"""Closed provider-neutral Operator Port and ResearchLedger projection."""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .research import (
    list_campaign_progress,
    list_campaigns,
    load_campaign,
    request_campaign_stop,
)
from .research_artifacts import (
    load_artifact_decision,
    load_reproduction_receipt,
    list_artifact_decisions,
    list_reproduction_receipts,
    publish_artifact_decision,
    publish_reproduction_receipt,
    validate_artifact_review,
    validate_reproduction_request,
)
from .research_definitions import (
    create_experiment_definition_version,
    create_factor_definition_version,
    create_strategy_definition_version,
    load_experiment_definition,
    load_factor_definition,
    list_experiment_definitions,
    list_factor_definitions,
    list_strategy_definitions,
    load_strategy_definition,
    semantic_definition_diff,
    validate_experiment_definition,
    validate_factor_definition,
    validate_strategy_definition,
)
from .sessions import list_experiments, load_session, session_snapshot
from .studies import hash_file, hash_json
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


OPERATOR_SCHEMA_VERSION = 1
OPERATOR_REQUEST = "request.json"
OPERATOR_RECEIPT = "receipt.json"
OPERATOR_MANIFEST = "manifest.json"
REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
TERMINAL_STATUSES = {
    "completed",
    "stopped",
    "failed",
    "unavailable",
    "stale",
    "confirmation-required",
}
READ_ONLY_INTENTS = {
    "research.inspect",
    "research.explain",
    "research.compare",
    "research.reproduction-readiness",
}
CONFIRMATION_INTENTS = {
    "definition.factor.create",
    "definition.strategy.create",
    "definition.experiment.create",
    "artifact.decide",
    "reproduction.start",
}
CONFIRMATION_DECISION_INTENTS = {"confirmation.accept"}
IMMEDIATE_INTENTS = {"campaign.stop"}
CAMPAIGN_EXECUTOR_INTENTS = {"campaign.start", "campaign.pause", "campaign.resume"}
INTENTS = (
    READ_ONLY_INTENTS
    | CONFIRMATION_INTENTS
    | CONFIRMATION_DECISION_INTENTS
    | IMMEDIATE_INTENTS
    | CAMPAIGN_EXECUTOR_INTENTS
)
FORBIDDEN_KEYS = {
    "command",
    "shell",
    "argv",
    "providercommand",
    "apikey",
    "api_key",
    "password",
    "secret",
    "credential",
    "credentials",
    "token",
    "path",
    "filepath",
    "directory",
}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.missing", f"Missing {label}")]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.json", f"Invalid JSON: {error.msg}")]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.type", f"{label} must be an object")]
        )
    return value


def _strict_keys(
    value: Any,
    required: set[str],
    path: Path | str,
    *,
    optional: set[str] = frozenset(),
) -> list[ValidationIssue]:
    if not isinstance(value, dict):
        return [_issue(path, "schema.type", "Expected an object")]
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - required - optional)
    )
    return issues


def _walk_forbidden(value: Any, path: str = "request") -> list[ValidationIssue]:
    issues = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower().replace("-", "").replace("_", "")
            blocked = {item.replace("_", "") for item in FORBIDDEN_KEYS}
            if key.lower() in FORBIDDEN_KEYS or any(
                normalized == item or normalized.endswith(item) for item in blocked
            ):
                issues.append(
                    _issue(
                        f"{path}/{key}",
                        "operator.forbidden-field",
                        "Operator requests cannot carry commands or credentials",
                    )
                )
            issues.extend(_walk_forbidden(item, f"{path}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(_walk_forbidden(item, f"{path}/{index}"))
    return issues


def validate_operator_request(value: dict[str, Any], path: str = "request") -> None:
    required = {
        "schemaVersion",
        "kind",
        "requestId",
        "actor",
        "workspaceRef",
        "projectId",
        "sessionId",
        "intent",
        "objectRefs",
        "authority",
        "budget",
        "confirmationRef",
        "expectedState",
        "input",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != OPERATOR_SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected Operator request V1"))
    if value.get("kind") != "autoquant-operator-request":
        issues.append(_issue(f"{path}/kind", "operator.kind", "Invalid Operator request kind"))
    if not isinstance(value.get("requestId"), str) or not REQUEST_ID.fullmatch(value["requestId"]):
        issues.append(_issue(f"{path}/requestId", "operator.request-id", "Invalid request identity"))
    for key in ("workspaceRef", "projectId", "sessionId", "intent"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            issues.append(_issue(f"{path}/{key}", "schema.string", f"{key} must be non-empty"))
    intent = value.get("intent")
    input_fields = {
        "research.inspect": set(),
        "research.explain": set(),
        "research.compare": set(),
        "research.reproduction-readiness": set(),
        "definition.factor.create": {"definition"},
        "definition.strategy.create": {"definition"},
        "definition.experiment.create": {"definition"},
        "artifact.decide": {"review"},
        "reproduction.start": {"reproduction"},
        "confirmation.accept": {"executionActor"},
        "campaign.stop": set(),
        "campaign.start": {"experimentDefinitionRef"},
        "campaign.pause": set(),
        "campaign.resume": set(),
    }
    if intent in input_fields:
        issues.extend(_strict_keys(value.get("input"), input_fields[intent], f"{path}/input"))
    input_value = value.get("input")
    domain_validators = {
        "definition.factor.create": ("definition", validate_factor_definition),
        "definition.strategy.create": ("definition", validate_strategy_definition),
        "definition.experiment.create": ("definition", validate_experiment_definition),
        "artifact.decide": ("review", validate_artifact_review),
        "reproduction.start": ("reproduction", validate_reproduction_request),
    }
    if intent in domain_validators and isinstance(input_value, dict):
        field, validator = domain_validators[intent]
        domain_value = input_value.get(field)
        if not isinstance(domain_value, dict):
            issues.append(_issue(f"{path}/input/{field}", "schema.type", "Expected an object"))
        else:
            try:
                validator(domain_value)
            except AutoQuantValidationError as error:
                issues.extend(error.issues)
    actor = value.get("actor")
    issues.extend(_strict_keys(actor, {"id", "kind"}, f"{path}/actor"))
    if isinstance(actor, dict):
        if actor.get("kind") not in {"user", "studio", "embedded-agent", "openalice", "hermes", "codex"}:
            issues.append(_issue(f"{path}/actor/kind", "operator.actor", "Invalid actor kind"))
        if not isinstance(actor.get("id"), str) or not actor["id"].strip():
            issues.append(_issue(f"{path}/actor/id", "schema.string", "Actor id must be non-empty"))
    object_refs = value.get("objectRefs")
    if not isinstance(object_refs, list):
        issues.append(_issue(f"{path}/objectRefs", "schema.list", "objectRefs must be a list"))
    else:
        for index, reference in enumerate(object_refs):
            ref_path = f"{path}/objectRefs/{index}"
            issues.extend(_strict_keys(reference, {"kind", "id", "version"}, ref_path))
            if isinstance(reference, dict):
                if reference.get("kind") not in {"session", "factor-definition", "strategy-definition", "experiment-definition", "campaign", "artifact-approval", "reproduction-receipt"}:
                    issues.append(_issue(f"{ref_path}/kind", "operator.object-ref", "Invalid object reference kind"))
                if not isinstance(reference.get("id"), str) or not reference["id"].strip():
                    issues.append(_issue(f"{ref_path}/id", "schema.string", "Object id must be non-empty"))
                version = reference.get("version")
                if version is not None and (
                    not isinstance(version, int) or isinstance(version, bool) or version < 1
                ):
                    issues.append(_issue(f"{ref_path}/version", "definition.version", "Object version must be positive or null"))
    authority = value.get("authority")
    issues.extend(_strict_keys(authority, {"mode"}, f"{path}/authority"))
    if isinstance(authority, dict) and authority.get("mode") not in {"read-only", "approved-envelope", "confirmation-bound"}:
        issues.append(_issue(f"{path}/authority/mode", "operator.authority", "Invalid authority mode"))
    budget = value.get("budget")
    issues.extend(
        _strict_keys(
            budget,
            {"candidateLimit", "wallTimeSeconds", "cpuSeconds", "gpuSeconds", "cost"},
            f"{path}/budget",
        )
    )
    if isinstance(budget, dict):
        for key in ("candidateLimit", "wallTimeSeconds", "cpuSeconds", "gpuSeconds"):
            item = budget.get(key)
            if not isinstance(item, int) or isinstance(item, bool) or item < 0:
                issues.append(_issue(f"{path}/budget/{key}", "schema.range", f"{key} must be non-negative"))
        cost = budget.get("cost")
        if cost is not None:
            issues.extend(_strict_keys(cost, {"currency", "amount"}, f"{path}/budget/cost"))
            if isinstance(cost, dict):
                if not isinstance(cost.get("currency"), str) or not cost["currency"].strip():
                    issues.append(_issue(f"{path}/budget/cost/currency", "schema.string", "Currency must be non-empty"))
                if not isinstance(cost.get("amount"), (int, float)) or isinstance(cost.get("amount"), bool) or cost.get("amount", -1) < 0:
                    issues.append(_issue(f"{path}/budget/cost/amount", "schema.range", "Cost must be non-negative"))
    confirmation = value.get("confirmationRef")
    if confirmation is not None and (
        not isinstance(confirmation, str) or not REQUEST_ID.fullmatch(confirmation)
    ):
        issues.append(_issue(f"{path}/confirmationRef", "operator.confirmation", "Invalid confirmation reference"))
    expected = value.get("expectedState")
    issues.extend(_strict_keys(expected, {"sessionStatus", "objectHashes"}, f"{path}/expectedState"))
    if isinstance(expected, dict):
        if expected.get("sessionStatus") not in {"active", "promoted", "completed"}:
            issues.append(_issue(f"{path}/expectedState/sessionStatus", "operator.expected-state", "Invalid expected Session state"))
        hashes = expected.get("objectHashes")
        if not isinstance(hashes, dict) or any(
            not isinstance(key, str)
            or not key
            or not isinstance(item, str)
            or not HASH.fullmatch(item)
            for key, item in (hashes.items() if isinstance(hashes, dict) else [])
        ):
            issues.append(_issue(f"{path}/expectedState/objectHashes", "operator.expected-state", "Object hashes must be a string-to-sha256 map"))
    if not isinstance(value.get("input"), dict):
        issues.append(_issue(f"{path}/input", "schema.type", "input must be an object"))
    issues.extend(_walk_forbidden(value, path))
    if issues:
        raise AutoQuantValidationError(issues)


def _receipts_root(project: ProjectContext, session_id: str, *, create: bool = False) -> Path:
    session = load_session(project, session_id)
    root = confined_path(session.root_dir, "operator-receipts", "session/operatorReceipts")
    if create:
        root.mkdir(exist_ok=True)
    return root


@contextmanager
def _operator_lock(project: ProjectContext, session_id: str):
    root = _receipts_root(project, session_id, create=True)
    path = root / ".operator.lock"
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        # ponytail: one Session-wide lock; split by request only if Operator throughput matters.
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _pending_root(project: ProjectContext, session_id: str, request_id: str) -> Path:
    return confined_path(
        _receipts_root(project, session_id, create=True),
        f".{request_id}.pending",
        "session/operatorReceipts/pending",
    )


def _receipt_root(project: ProjectContext, session_id: str, request_id: str) -> Path:
    if not REQUEST_ID.fullmatch(request_id):
        raise AutoQuantValidationError([_issue("requestId", "operator.request-id", "Invalid request identity")])
    return confined_path(
        _receipts_root(project, session_id),
        request_id,
        "session/operatorReceipts/requestId",
    )


def _load_receipt(root: Path) -> dict[str, Any]:
    manifest_path = root / OPERATOR_MANIFEST
    request_path = root / OPERATOR_REQUEST
    receipt_path = root / OPERATOR_RECEIPT
    manifest = _read_json(manifest_path, "Operator manifest")
    required = {
        "schemaVersion", "kind", "requestId", "requestHash", "receiptHash", "completed", "files"
    }
    issues = _strict_keys(manifest, required, manifest_path)
    request_hash = hash_file(request_path) if request_path.is_file() else None
    receipt_hash = hash_file(receipt_path) if receipt_path.is_file() else None
    if manifest.get("schemaVersion") != 1 or manifest.get("kind") != "autoquant-agent-operation-manifest":
        issues.append(_issue(manifest_path, "operator.manifest", "Invalid Operator manifest"))
    if manifest.get("requestHash") != request_hash or manifest.get("receiptHash") != receipt_hash:
        issues.append(_issue(root, "operator.hash", "Operator receipt hash mismatch"))
    if manifest.get("files") != {OPERATOR_REQUEST: request_hash, OPERATOR_RECEIPT: receipt_hash}:
        issues.append(_issue(root, "operator.files", "Operator receipt file manifest mismatch"))
    if issues:
        raise AutoQuantValidationError(issues)
    receipt = _read_json(receipt_path, "Operator receipt")
    validate_operator_receipt(receipt, str(receipt_path))
    if receipt["requestId"] != manifest["requestId"] or receipt["acceptedRequestHash"] != hash_json(_read_json(request_path, "Operator request")):
        raise AutoQuantValidationError([_issue(root, "operator.identity", "Operator receipt identity mismatch")])
    return receipt


def validate_operator_receipt(value: dict[str, Any], path: str = "receipt") -> None:
    required = {
        "schemaVersion", "kind", "requestId", "acceptedRequestHash", "actor", "intent",
        "status", "operations", "artifacts", "evidence", "budgetSpent", "warnings",
        "failedGates", "errors", "nextValidActions", "reproductionLineage", "completedAt",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "autoquant-agent-operation-receipt":
        issues.append(_issue(path, "operator.receipt", "Invalid Operator receipt kind or version"))
    if value.get("status") not in TERMINAL_STATUSES:
        issues.append(_issue(f"{path}/status", "operator.status", "Invalid terminal status"))
    if not isinstance(value.get("acceptedRequestHash"), str) or not HASH.fullmatch(value.get("acceptedRequestHash", "")):
        issues.append(_issue(f"{path}/acceptedRequestHash", "schema.hash", "Invalid accepted request hash"))
    for key in ("operations", "artifacts", "evidence", "warnings", "failedGates", "errors", "nextValidActions", "reproductionLineage"):
        if not isinstance(value.get(key), list):
            issues.append(_issue(f"{path}/{key}", "schema.list", f"{key} must be a list"))
    if not isinstance(value.get("budgetSpent"), dict):
        issues.append(_issue(f"{path}/budgetSpent", "schema.type", "budgetSpent must be an object"))
    if issues:
        raise AutoQuantValidationError(issues)


def _publish_receipt(
    project: ProjectContext,
    request: dict[str, Any],
    *,
    status: str,
    operations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    failed_gates: list[str] | None = None,
    errors: list[dict[str, str]] | None = None,
    next_actions: list[str] | None = None,
) -> dict[str, Any]:
    root = _receipt_root(project, request["sessionId"], request["requestId"])
    pending = _pending_root(project, request["sessionId"], request["requestId"])
    if root.exists():
        prior_request = _read_json(root / OPERATOR_REQUEST, "Operator request")
        if hash_json(prior_request) == hash_json(request):
            if pending.exists():
                shutil.rmtree(pending)
            return _load_receipt(root)
        raise AutoQuantValidationError(
            [_issue(root, "operator.collision", "Operator receipt already exists")]
        )
    parent = _receipts_root(project, request["sessionId"], create=True)
    temporary = parent / f".{request['requestId']}.{uuid.uuid4().hex}.creating"
    request_hash = hash_json(request)
    receipt = {
        "schemaVersion": 1,
        "kind": "autoquant-agent-operation-receipt",
        "requestId": request["requestId"],
        "acceptedRequestHash": request_hash,
        "actor": request["actor"],
        "intent": request["intent"],
        "status": status,
        "operations": operations,
        "artifacts": artifacts or [],
        "evidence": evidence or [],
        "budgetSpent": {
            "candidates": 0,
            "wallTimeSeconds": 0,
            "cpuSeconds": 0,
            "gpuSeconds": 0,
            "cost": {"known": True, "currency": None, "amount": 0},
        },
        "warnings": warnings or [],
        "failedGates": failed_gates or [],
        "errors": errors or [],
        "nextValidActions": next_actions or [],
        "reproductionLineage": [],
        "completedAt": datetime.now(timezone.utc).isoformat(),
    }
    validate_operator_receipt(receipt)
    try:
        temporary.mkdir()
        _write_json(temporary / OPERATOR_REQUEST, request)
        _write_json(temporary / OPERATOR_RECEIPT, receipt)
        files = {
            OPERATOR_REQUEST: hash_file(temporary / OPERATOR_REQUEST),
            OPERATOR_RECEIPT: hash_file(temporary / OPERATOR_RECEIPT),
        }
        manifest = {
            "schemaVersion": 1,
            "kind": "autoquant-agent-operation-manifest",
            "requestId": request["requestId"],
            "requestHash": files[OPERATOR_REQUEST],
            "receiptHash": files[OPERATOR_RECEIPT],
            "completed": True,
            "files": files,
        }
        _write_json(temporary / OPERATOR_MANIFEST, manifest)
        os.replace(temporary, root)
        if pending.exists():
            shutil.rmtree(pending)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        if root.exists():
            prior_request = _read_json(root / OPERATOR_REQUEST, "Operator request")
            if hash_json(prior_request) == hash_json(request):
                if pending.exists():
                    shutil.rmtree(pending)
                return _load_receipt(root)
        raise
    return _load_receipt(root)


def list_operator_receipts(project: ProjectContext, session_id: str) -> list[dict[str, Any]]:
    root = _receipts_root(project, session_id)
    if not root.exists():
        return []
    receipts = []
    for path in sorted(root.iterdir()):
        if path.is_dir() and not path.name.startswith("."):
            receipts.append(_load_receipt(path))
    return receipts


def build_research_ledger(project: ProjectContext, session_id: str) -> dict[str, Any]:
    session = load_session(project, session_id)
    snapshot = session_snapshot(project, session)
    factors = [item.definition for item in list_factor_definitions(project)]
    strategies = [item.definition for item in list_strategy_definitions(project)]
    experiment_definitions = [
        item.definition for item in list_experiment_definitions(project, session_id)
    ]
    campaigns = [item.to_dict() for item in list_campaigns(project, session)]
    campaign_progress = list_campaign_progress(session)
    experiments = [item.to_dict() for item in list_experiments(project, session)]
    receipts = list_operator_receipts(project, session_id)
    artifact_decisions = list_artifact_decisions(project, session_id)
    reproductions = list_reproduction_receipts(project, session_id)
    stages = [
        {
            "id": "data",
            "label": "Data",
            "state": "available",
            "objects": [{"kind": "study", "id": session.manifest["studyId"], "version": None}],
            "blockers": [],
            "nextValidActions": ["research.inspect"],
        },
        {
            "id": "question",
            "label": "Question",
            "state": "available" if session.manifest.get("brief") else "partial",
            "objects": ([{"kind": "research-brief", "id": session.manifest["brief"]["id"], "version": None}] if session.manifest.get("brief") else []),
            "blockers": ([] if session.manifest.get("brief") else ["No request-bound ResearchBrief is attached to this legacy Session."]),
            "nextValidActions": ["research.explain"],
        },
        {
            "id": "factor",
            "label": "Factor",
            "state": "available" if factors or strategies else "empty",
            "objects": (
                [{"kind": "factor-definition", "id": item["id"], "version": item["version"]} for item in factors]
                + [{"kind": "strategy-definition", "id": item["id"], "version": item["version"]} for item in strategies]
            ),
            "blockers": [] if factors or strategies else ["No FactorDefinition or StrategyDefinition version has been published."],
            "nextValidActions": ["research.inspect"],
        },
        {
            "id": "experiment",
            "label": "Experiment",
            "state": "available" if experiment_definitions or experiments else "empty",
            "objects": [
                {"kind": "experiment-definition", "id": item["id"], "version": item["version"]}
                for item in experiment_definitions
            ],
            "blockers": [] if experiment_definitions else ["No frozen ExperimentDefinition is connected."],
            "nextValidActions": ["research.compare"],
        },
        {
            "id": "campaign",
            "label": "Campaign",
            "state": "partial" if campaign_progress else ("available" if campaigns else "empty"),
            "objects": [
                {
                    "kind": "campaign",
                    "id": item.get("id", item.get("campaignId")),
                    "version": None,
                }
                for item in [*campaigns, *campaign_progress]
            ],
            "blockers": [],
            "nextValidActions": ["campaign.stop"] if campaign_progress else ["research.inspect"],
        },
        {
            "id": "evidence",
            "label": "Evidence",
            "state": "partial" if experiments else "empty",
            "objects": [{"kind": "experiment", "id": item["id"], "version": None} for item in experiments],
            "blockers": ["ReplayBundle, verified market clock, and entity mapping are unavailable for this connected projection."],
            "nextValidActions": ["research.reproduction-readiness"],
            "widgets": {
                "runs": {"state": "available" if experiments else "empty"},
                "replay": {"state": "unavailable", "reason": "ReplayBundle contract is not connected."},
            },
        },
        {
            "id": "approval",
            "label": "Approval",
            "state": "available" if artifact_decisions else "unavailable",
            "objects": [
                {"kind": "artifact-approval", "id": item["decision"]["id"], "version": None}
                for item in artifact_decisions
            ],
            "blockers": [] if artifact_decisions else ["No exact-version artifact approval is published; approval remains unavailable until Core verifies an EvidenceAssessment."],
            "nextValidActions": ["research.reproduction-readiness"] if artifact_decisions else [],
        },
        {
            "id": "reproduction",
            "label": "Reproduction",
            "state": "available" if reproductions else "unavailable",
            "objects": [
                {"kind": "reproduction-receipt", "id": item["receipt"]["id"], "version": None}
                for item in reproductions
            ],
            "blockers": [] if reproductions else ["Reproduction requires an approved artifact manifest and a Core-controlled executor."],
            "nextValidActions": [],
        },
    ]
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-ledger",
        "sessionId": session_id,
        "sessionStatus": session.manifest["status"],
        "authority": snapshot["authority"],
        "stages": stages,
        "receipts": receipts,
    }


def _current_object_hashes(
    project: ProjectContext, session_id: str, refs: list[dict[str, Any]]
) -> dict[str, str]:
    hashes = {}
    session = load_session(project, session_id)
    for reference in refs:
        key = f"{reference['kind']}:{reference['id']}:{reference['version']}"
        if reference["kind"] == "session":
            hashes[key] = hash_file(session.manifest_path)
        elif reference["kind"] == "factor-definition" and reference["version"] is not None:
            item = load_factor_definition(project, reference["id"], reference["version"])
            hashes[key] = item.manifest["contentHash"]
        elif reference["kind"] == "experiment-definition" and reference["version"] is not None:
            item = load_experiment_definition(project, session_id, reference["id"], reference["version"])
            hashes[key] = item.manifest["contentHash"]
        elif reference["kind"] == "strategy-definition" and reference["version"] is not None:
            item = load_strategy_definition(project, reference["id"], reference["version"])
            hashes[key] = item.manifest["contentHash"]
    return hashes


def _compare(project: ProjectContext, request: dict[str, Any]) -> dict[str, Any]:
    refs = request["objectRefs"]
    if len(refs) != 2 or refs[0]["kind"] != refs[1]["kind"] or refs[0]["id"] != refs[1]["id"]:
        raise AutoQuantValidationError([_issue("objectRefs", "operator.compare", "Compare requires two versions of the same definition")])
    if refs[0]["kind"] == "factor-definition":
        before = load_factor_definition(project, refs[0]["id"], refs[0]["version"]).definition
        after = load_factor_definition(project, refs[1]["id"], refs[1]["version"]).definition
    elif refs[0]["kind"] == "experiment-definition":
        before = load_experiment_definition(project, request["sessionId"], refs[0]["id"], refs[0]["version"]).definition
        after = load_experiment_definition(project, request["sessionId"], refs[1]["id"], refs[1]["version"]).definition
    elif refs[0]["kind"] == "strategy-definition":
        before = load_strategy_definition(project, refs[0]["id"], refs[0]["version"]).definition
        after = load_strategy_definition(project, refs[1]["id"], refs[1]["version"]).definition
    else:
        raise AutoQuantValidationError([_issue("objectRefs", "operator.compare", "Only definition versions support semantic comparison")])
    return semantic_definition_diff(before, after)


def _is_collision(error: AutoQuantValidationError) -> bool:
    return any(item.code in {"definition.collision", "artifact.collision"} for item in error.issues)


def execute_operator_request(
    project: ProjectContext, request: dict[str, Any]
) -> dict[str, Any]:
    validate_operator_request(request)
    with _operator_lock(project, request["sessionId"]):
        return _execute_operator_request_locked(project, request)


def _execute_operator_request_locked(
    project: ProjectContext, request: dict[str, Any]
) -> dict[str, Any]:
    session = load_session(project, request["sessionId"])
    if request["projectId"] != project.manifest.id:
        raise AutoQuantValidationError([_issue("projectId", "operator.project", "Operator Project id mismatch")])
    root = _receipt_root(project, request["sessionId"], request["requestId"])
    if root.exists():
        prior_request = _read_json(root / OPERATOR_REQUEST, "Operator request")
        if hash_json(prior_request) != hash_json(request):
            raise AutoQuantValidationError([_issue("requestId", "operator.idempotency-conflict", "Request identity was already used for different bytes")])
        return _load_receipt(root)
    pending = _pending_root(project, request["sessionId"], request["requestId"])
    recovering = pending.exists()
    if recovering:
        pending_request_path = pending / OPERATOR_REQUEST
        if not pending_request_path.is_file():
            shutil.rmtree(pending)
            recovering = False
        else:
            pending_request = _read_json(pending_request_path, "Pending Operator request")
            if hash_json(pending_request) != hash_json(request):
                raise AutoQuantValidationError(
                    [
                        _issue(
                            request["requestId"],
                            "operator.idempotency-conflict",
                            "Request identity is reserved for different bytes",
                        )
                    ]
                )
    if not recovering:
        pending.mkdir()
        _write_json(pending / OPERATOR_REQUEST, request)
    if request["intent"] not in INTENTS:
        return _publish_receipt(
            project,
            request,
            status="failed",
            operations=[],
            errors=[{"code": "operator.unknown-intent", "message": "Unknown closed Operator intent"}],
            next_actions=["aq capabilities --json"],
        )
    if request["intent"] in CONFIRMATION_DECISION_INTENTS:
        if (
            request["authority"]["mode"] != "approved-envelope"
            or request["actor"]["kind"] != "user"
            or request["confirmationRef"] is None
        ):
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[
                    {
                        "code": "operator.confirmation-authority",
                        "message": "Semantic confirmation requires an authorized user and an exact proposal receipt",
                    }
                ],
                next_actions=["research.inspect"],
            )
        issues = _strict_keys(
            request["input"],
            {"executionActor"},
            "request/input",
        )
        execution_actor = request["input"].get("executionActor")
        issues.extend(
            _strict_keys(execution_actor, {"id", "kind"}, "request/input/executionActor")
        )
        if issues:
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[{"code": item.code, "message": item.message} for item in issues],
                next_actions=["research.inspect"],
            )
        proposal_root = _receipt_root(
            project,
            request["sessionId"],
            request["confirmationRef"],
        )
        try:
            proposal_receipt = _load_receipt(proposal_root)
            proposal_request = _read_json(
                proposal_root / OPERATOR_REQUEST,
                "Operator proposal request",
            )
        except AutoQuantValidationError as error:
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[{"code": item.code, "message": item.message} for item in error.issues],
                next_actions=["research.inspect"],
            )
        if (
            proposal_receipt["status"] != "confirmation-required"
            or proposal_request["actor"] != execution_actor
            or proposal_request["projectId"] != request["projectId"]
            or proposal_request["sessionId"] != request["sessionId"]
            or proposal_request["expectedState"] != request["expectedState"]
        ):
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                failed_gates=["semantic-confirmation"],
                errors=[
                    {
                        "code": "operator.confirmation-mismatch",
                        "message": "Confirmation decision does not match the proposed actor and prior state",
                    }
                ],
                next_actions=["research.inspect"],
            )
        return _publish_receipt(
            project,
            request,
            status="completed",
            operations=[{"intent": request["intent"], "completed": True}],
            evidence=[
                {
                    "kind": "autoquant-semantic-confirmation-decision",
                    "proposalRequestId": proposal_request["requestId"],
                    "proposalRequestHash": hash_json(proposal_request),
                    "executionActor": execution_actor,
                    "confirmedBy": request["actor"],
                }
            ],
            next_actions=[proposal_request["intent"]],
        )
    expected = request["expectedState"]
    current_hashes = _current_object_hashes(project, request["sessionId"], request["objectRefs"])
    if (
        expected["sessionStatus"] != session.manifest["status"]
        or expected["objectHashes"] != current_hashes
    ):
        return _publish_receipt(
            project,
            request,
            status="stale",
            operations=[],
            evidence=[{"kind": "current-state", "sessionStatus": session.manifest["status"], "objectHashes": current_hashes}],
            failed_gates=["expected-prior-state"],
            next_actions=["research.inspect"],
        )
    if request["intent"] in CONFIRMATION_INTENTS:
        if request["authority"]["mode"] != "confirmation-bound":
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[{"code": "operator.authority", "message": "Mutation intents require confirmation-bound authority"}],
                next_actions=["research.inspect"],
            )
        if request["confirmationRef"] is None:
            return _publish_receipt(
                project,
                request,
                status="confirmation-required",
                operations=[{"intent": request["intent"], "completed": False}],
                evidence=[{
                    "kind": "autoquant-semantic-confirmation",
                    "intent": request["intent"],
                    "objectRefs": request["objectRefs"],
                    "budget": request["budget"],
                    "proposedInputHash": hash_json(request["input"]),
                }],
                next_actions=[request["intent"]],
            )
        confirmation_root = _receipt_root(
            project,
            request["sessionId"],
            request["confirmationRef"],
        )
        try:
            confirmation_decision = _load_receipt(confirmation_root)
            confirmation_decision_request = _read_json(
                confirmation_root / OPERATOR_REQUEST,
                "Operator confirmation decision request",
            )
        except AutoQuantValidationError:
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                failed_gates=["semantic-confirmation"],
                errors=[{"code": "operator.confirmation-missing", "message": "Confirmation receipt is missing or invalid"}],
                next_actions=["research.inspect"],
            )
        decision = next(
            (
                item
                for item in confirmation_decision.get("evidence", [])
                if item.get("kind") == "autoquant-semantic-confirmation-decision"
            ),
            None,
        )
        proposal_root = (
            _receipt_root(
                project,
                request["sessionId"],
                decision["proposalRequestId"],
            )
            if isinstance(decision, dict) and isinstance(decision.get("proposalRequestId"), str)
            else None
        )
        try:
            proposal_receipt = _load_receipt(proposal_root) if proposal_root else None
            proposal_request = (
                _read_json(proposal_root / OPERATOR_REQUEST, "Operator proposal request")
                if proposal_root
                else None
            )
        except AutoQuantValidationError:
            proposal_receipt = None
            proposal_request = None
        if (
            confirmation_decision["status"] != "completed"
            or confirmation_decision["intent"] != "confirmation.accept"
            or confirmation_decision_request["actor"].get("kind") != "user"
            or not isinstance(decision, dict)
            or decision.get("executionActor") != request["actor"]
            or proposal_receipt is None
            or proposal_receipt["status"] != "confirmation-required"
            or proposal_request is None
            or proposal_receipt["intent"] != request["intent"]
            or decision.get("proposalRequestHash") != hash_json(proposal_request)
            or proposal_request["actor"] != request["actor"]
            or proposal_request["workspaceRef"] != request["workspaceRef"]
            or proposal_request["projectId"] != request["projectId"]
            or proposal_request["sessionId"] != request["sessionId"]
            or proposal_request["expectedState"] != request["expectedState"]
            or hash_json(proposal_request["input"]) != hash_json(request["input"])
            or proposal_request["objectRefs"] != request["objectRefs"]
            or proposal_request["budget"] != request["budget"]
        ):
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                failed_gates=["semantic-confirmation"],
                errors=[{"code": "operator.confirmation-mismatch", "message": "Confirmation does not match the proposed semantic input, object references, and budget"}],
                next_actions=["research.inspect"],
            )
        try:
            if request["intent"] == "definition.factor.create":
                definition_input = request["input"]["definition"]
                try:
                    created = create_factor_definition_version(project, definition_input)
                except AutoQuantValidationError as error:
                    if not recovering or not _is_collision(error):
                        raise
                    created = load_factor_definition(
                        project,
                        definition_input["id"],
                        definition_input["version"],
                    )
                    if created.definition != definition_input:
                        raise error
                artifact_refs = [{"kind": "factor-definition", "id": created.definition["id"], "version": created.definition["version"], "hash": created.manifest["contentHash"]}]
                result = created.definition
            elif request["intent"] == "definition.strategy.create":
                definition_input = request["input"]["definition"]
                try:
                    created = create_strategy_definition_version(project, definition_input)
                except AutoQuantValidationError as error:
                    if not recovering or not _is_collision(error):
                        raise
                    created = load_strategy_definition(
                        project,
                        definition_input["id"],
                        definition_input["version"],
                    )
                    if created.definition != definition_input:
                        raise error
                artifact_refs = [{"kind": "strategy-definition", "id": created.definition["id"], "version": created.definition["version"], "hash": created.manifest["contentHash"]}]
                result = created.definition
            elif request["intent"] == "definition.experiment.create":
                definition_input = request["input"]["definition"]
                try:
                    created = create_experiment_definition_version(
                        project,
                        request["sessionId"],
                        definition_input,
                    )
                except AutoQuantValidationError as error:
                    if not recovering or not _is_collision(error):
                        raise
                    created = load_experiment_definition(
                        project,
                        request["sessionId"],
                        definition_input["id"],
                        definition_input["version"],
                    )
                    if created.definition != definition_input:
                        raise error
                artifact_refs = [{"kind": "experiment-definition", "id": created.definition["id"], "version": created.definition["version"], "hash": created.manifest["contentHash"]}]
                result = created.definition
            elif request["intent"] == "artifact.decide":
                review_input = request["input"]["review"]
                try:
                    created = publish_artifact_decision(
                        project,
                        request["sessionId"],
                        review_input,
                    )
                except AutoQuantValidationError as error:
                    if not recovering or not _is_collision(error):
                        raise
                    created = load_artifact_decision(
                        project,
                        request["sessionId"],
                        review_input["id"],
                    )
                    if created["review"] != review_input:
                        raise error
                artifact_refs = [{"kind": "artifact-approval", "id": created["decision"]["id"], "version": None, "hash": created["manifest"]["files"]["decision.json"]}]
                result = created["decision"]
            else:
                reproduction_input = request["input"]["reproduction"]
                try:
                    created = publish_reproduction_receipt(
                        project,
                        request["sessionId"],
                        reproduction_input,
                    )
                except AutoQuantValidationError as error:
                    if not recovering or not _is_collision(error):
                        raise
                    created = load_reproduction_receipt(
                        project,
                        request["sessionId"],
                        reproduction_input["id"],
                    )
                    if created["request"] != reproduction_input:
                        raise error
                artifact_refs = [{"kind": "reproduction-receipt", "id": created["receipt"]["id"], "version": None, "hash": created["manifest"]["files"]["receipt.json"]}]
                result = created["receipt"]
        except (AutoQuantValidationError, KeyError) as error:
            issues = (
                error.issues
                if isinstance(error, AutoQuantValidationError)
                else [_issue("input", "schema.missing", f"Missing mutation input field: {error.args[0]}")]
            )
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[{"intent": request["intent"], "completed": False}],
                errors=[{"code": item.code, "message": item.message} for item in issues],
                next_actions=["research.inspect"],
            )
        return _publish_receipt(
            project,
            request,
            status="completed",
            operations=[{"intent": request["intent"], "completed": True}],
            artifacts=artifact_refs,
            evidence=[result],
        )
    if request["intent"] in IMMEDIATE_INTENTS:
        if request["authority"]["mode"] != "approved-envelope":
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[{"code": "operator.authority", "message": "Immediate Campaign stop requires approved-envelope authority"}],
                next_actions=["research.inspect"],
            )
        references = request["objectRefs"]
        if len(references) != 1 or references[0]["kind"] != "campaign" or references[0]["version"] is not None:
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[{"code": "operator.campaign-ref", "message": "Campaign stop requires one exact unversioned Campaign reference"}],
                next_actions=["research.inspect"],
            )
        session = load_session(project, request["sessionId"])
        active = next(
            (
                item
                for item in list_campaign_progress(session)
                if item["campaignId"] == references[0]["id"]
            ),
            None,
        )
        try:
            stop = request_campaign_stop(
                project,
                request["sessionId"],
                references[0]["id"],
                request["actor"],
            )
        except AutoQuantValidationError as error:
            return _publish_receipt(
                project,
                request,
                status="unavailable",
                operations=[{"intent": request["intent"], "completed": False}],
                errors=[{"code": item.code, "message": item.message} for item in error.issues],
                next_actions=["research.inspect"],
            )
        remaining = (
            active.get("budget", {}).get("remaining", {}).get("wallSeconds", 0)
            if active is not None
            else 0
        )
        deadline = time.monotonic() + min(30, max(1, remaining + 1))
        terminal = None
        while time.monotonic() < deadline:
            session = load_session(project, request["sessionId"])
            if not any(
                item["campaignId"] == references[0]["id"]
                for item in list_campaign_progress(session)
            ):
                terminal = load_campaign(
                    project,
                    session,
                    references[0]["id"],
                ).result
                break
            time.sleep(0.05)
        if terminal is None:
            return _publish_receipt(
                project,
                request,
                status="unavailable",
                operations=[{"intent": request["intent"], "completed": False}],
                evidence=[stop],
                warnings=["Campaign stop was persisted but terminal publication is still pending"],
                next_actions=["research.inspect"],
            )
        return _publish_receipt(
            project,
            request,
            status="stopped",
            operations=[{"intent": request["intent"], "completed": True}],
            evidence=[stop, terminal],
            next_actions=["research.inspect"],
        )
    approved = [
        item
        for item in list_artifact_decisions(project, request["sessionId"])
        if item["decision"]["decision"] == "approve"
    ]
    if request["intent"] in CAMPAIGN_EXECUTOR_INTENTS:
        if request["authority"]["mode"] != "approved-envelope":
            return _publish_receipt(
                project,
                request,
                status="failed",
                operations=[],
                errors=[{"code": "operator.authority", "message": "Campaign executor intents require approved-envelope authority"}],
                next_actions=["research.inspect"],
            )
        references = request["objectRefs"]
        if request["intent"] == "campaign.start":
            session = load_session(project, request["sessionId"])
            active_progress = list_campaign_progress(session)
            if active_progress:
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "campaign.already-running", "message": "Session already has an active Campaign"}],
                    next_actions=["campaign.stop", "research.inspect"],
                )
            definition_ref = request["input"].get("experimentDefinitionRef")
            if not isinstance(definition_ref, dict) or set(definition_ref) != {"id", "version", "contentHash"} or not isinstance(definition_ref.get("id"), str) or not definition_ref["id"].strip() or not isinstance(definition_ref.get("version"), int) or isinstance(definition_ref.get("version"), bool) or definition_ref["version"] < 1 or not isinstance(definition_ref.get("contentHash"), str) or not HASH.fullmatch(definition_ref.get("contentHash", "")):
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "campaign.definition-ref", "message": "campaign.start requires an exact experimentDefinitionRef with id, version, and contentHash"}],
                    next_actions=["research.inspect"],
                )
            try:
                experiment_def = load_experiment_definition(
                    project,
                    request["sessionId"],
                    definition_ref["id"],
                    definition_ref["version"],
                )
            except AutoQuantValidationError as error:
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": item.code, "message": item.message} for item in error.issues],
                    next_actions=["research.inspect"],
                )
            if experiment_def.definition["status"] != "frozen":
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "campaign.definition-status", "message": "ExperimentDefinition must be frozen before Campaign execution"}],
                    next_actions=["research.inspect"],
                )
            if experiment_def.manifest["contentHash"] != definition_ref["contentHash"]:
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "campaign.definition-hash", "message": "experimentDefinitionRef contentHash does not match the frozen ExperimentDefinition contentHash"}],
                    next_actions=["research.inspect"],
                )
            budget = request["budget"]
            if not isinstance(budget.get("candidateLimit"), int) or budget["candidateLimit"] < 1:
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "campaign.budget", "message": "campaign.start requires a positive candidateLimit in the request budget"}],
                    next_actions=["research.inspect"],
                )
        if request["intent"] in {"campaign.pause", "campaign.resume"}:
            if len(references) != 1 or references[0]["kind"] != "campaign" or references[0]["version"] is not None:
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "operator.campaign-ref", "message": "Campaign pause/resume requires one exact unversioned Campaign reference"}],
                    next_actions=["research.inspect"],
                )
            session = load_session(project, request["sessionId"])
            progress = next(
                (
                    item
                    for item in list_campaign_progress(session)
                    if item["campaignId"] == references[0]["id"]
                ),
                None,
            )
            if progress is None:
                return _publish_receipt(
                    project,
                    request,
                    status="failed",
                    operations=[],
                    errors=[{"code": "campaign.not-running", "message": "No active Campaign is running"}],
                    next_actions=["research.inspect"],
                )
        return _publish_receipt(
            project,
            request,
            status="unavailable",
            operations=[{"intent": request["intent"], "completed": False}],
            evidence=[
                {
                    "kind": "autoquant-campaign-preflight",
                    "intent": request["intent"],
                    "validated": True,
                    "executor": None,
                    "message": "Preflight validation passed; execution is deferred to a structured executor.",
                }
            ],
            errors=[{"code": "campaign.structured-executor-unavailable", "message": "A structured Campaign executor is not available in this build; the validated preflight is preserved for future execution."}],
            next_actions=["research.inspect"],
        )
    handlers: dict[str, Callable[[], dict[str, Any]]] = {
        "research.inspect": lambda: build_research_ledger(project, request["sessionId"]),
        "research.explain": lambda: {
            "kind": "autoquant-research-explanation",
            "blockers": [
                {"stage": stage["id"], "items": stage["blockers"]}
                for stage in build_research_ledger(project, request["sessionId"])["stages"]
                if stage["blockers"]
            ],
        },
        "research.compare": lambda: _compare(project, request),
        "research.reproduction-readiness": lambda: {
            "kind": "autoquant-reproduction-readiness",
            "ready": bool(approved),
            "unresolved": [] if approved else ["approved-artifact-manifest"],
            "approvals": [
                {
                    "id": item["decision"]["id"],
                    "artifactId": item["decision"]["artifactId"],
                    "definitionRef": item["decision"]["definitionRef"],
                }
                for item in approved
            ],
        },
    }
    try:
        result = handlers[request["intent"]]()
    except AutoQuantValidationError as error:
        return _publish_receipt(
            project,
            request,
            status="failed",
            operations=[{"intent": request["intent"], "completed": False}],
            errors=[{"code": item.code, "message": item.message} for item in error.issues],
            next_actions=["research.inspect"],
        )
    status = (
        "unavailable"
        if request["intent"] == "research.reproduction-readiness" and not result["ready"]
        else "completed"
    )
    return _publish_receipt(
        project,
        request,
        status=status,
        operations=[{"intent": request["intent"], "completed": True}],
        evidence=[result],
        next_actions=["research.inspect"] if status == "unavailable" else [],
    )


OPERATOR_REQUEST_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant Operator request V1",
    "type": "object",
    "required": [
        "schemaVersion", "kind", "requestId", "actor", "workspaceRef", "projectId",
        "sessionId", "intent", "objectRefs", "authority", "budget", "confirmationRef",
        "expectedState", "input",
    ],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-operator-request"},
        "requestId": {"type": "string", "pattern": REQUEST_ID.pattern},
        "actor": {"type": "object"},
        "workspaceRef": {"type": "string", "minLength": 1},
        "projectId": {"type": "string", "minLength": 1},
        "sessionId": {"type": "string", "minLength": 1},
        "intent": {"type": "string", "enum": sorted(INTENTS)},
        "objectRefs": {"type": "array"},
        "authority": {"type": "object"},
        "budget": {"type": "object"},
        "confirmationRef": {"type": ["string", "null"]},
        "expectedState": {"type": "object"},
        "input": {"type": "object"},
    },
}


OPERATOR_RECEIPT_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant AgentOperationReceipt V1",
    "type": "object",
    "required": [
        "schemaVersion", "kind", "requestId", "acceptedRequestHash", "actor", "intent",
        "status", "operations", "artifacts", "evidence", "budgetSpent", "warnings",
        "failedGates", "errors", "nextValidActions", "reproductionLineage", "completedAt",
    ],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-agent-operation-receipt"},
        "requestId": {"type": "string"},
        "acceptedRequestHash": {"type": "string", "pattern": HASH.pattern},
        "actor": {"type": "object"},
        "intent": {"type": "string"},
        "status": {"enum": sorted(TERMINAL_STATUSES)},
        "operations": {"type": "array"},
        "artifacts": {"type": "array"},
        "evidence": {"type": "array"},
        "budgetSpent": {"type": "object"},
        "warnings": {"type": "array"},
        "failedGates": {"type": "array"},
        "errors": {"type": "array"},
        "nextValidActions": {"type": "array"},
        "reproductionLineage": {"type": "array"},
        "completedAt": {"type": "string"},
    },
}


RESEARCH_LEDGER_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant ResearchLedger V1",
    "type": "object",
    "required": ["schemaVersion", "kind", "sessionId", "sessionStatus", "authority", "stages", "receipts"],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-research-ledger"},
        "sessionId": {"type": "string"},
        "sessionStatus": {"type": "string"},
        "authority": {"type": "object"},
        "stages": {"type": "array", "minItems": 8, "maxItems": 8},
        "receipts": {"type": "array"},
    },
}
