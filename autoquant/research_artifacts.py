"""Exact-version research artifact decisions and reproduction receipts."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_definitions import (
    load_experiment_definition,
    load_factor_definition,
    load_strategy_definition,
)
from .runs import load_run
from .sessions import load_session
from .studies import hash_file, hash_json
from .verification import (
    load_verification_assessment,
    validate_verification_assessment,
)
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


SCHEMA_VERSION = 1
ARTIFACT_REVIEW = "review.json"
ARTIFACT_DECISION = "decision.json"
REPRODUCTION_REQUEST = "request.json"
REPRODUCTION_RECEIPT = "receipt.json"
MANIFEST = "manifest.json"
OBJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
DECISIONS = {"approve", "return-for-revision", "retain-as-draft"}
REPRODUCTION_OUTCOMES = {
    "exact-match",
    "within-tolerance",
    "drift",
    "unavailable",
    "failed",
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
        raise AutoQuantValidationError([_issue(path, f"{label}.missing", f"Missing {label}")]) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError([_issue(path, f"{label}.json", f"Invalid JSON: {error.msg}")]) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError([_issue(path, f"{label}.type", f"{label} must be an object")])
    return value


def _strict_keys(value: Any, required: set[str], path: Path | str) -> list[ValidationIssue]:
    if not isinstance(value, dict):
        return [_issue(path, "schema.type", "Expected an object")]
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - required)
    )
    return issues


def validate_artifact_review(value: dict[str, Any], path: str = "artifactReview") -> None:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "decision",
        "actor",
        "definitionRef",
        "definitionHash",
        "evidenceManifest",
        "reason",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "autoquant-artifact-review":
        issues.append(_issue(path, "artifact.review", "Invalid artifact review kind or version"))
    if not isinstance(value.get("id"), str) or not OBJECT_ID.fullmatch(value["id"]):
        issues.append(_issue(f"{path}/id", "artifact.id", "Invalid artifact review id"))
    if value.get("decision") not in DECISIONS:
        issues.append(_issue(f"{path}/decision", "artifact.decision", "Invalid artifact decision"))
    if not isinstance(value.get("actor"), dict) or set(value["actor"]) != {"id", "kind"}:
        issues.append(_issue(f"{path}/actor", "artifact.actor", "Actor must contain exactly id and kind"))
    reference = value.get("definitionRef")
    issues.extend(_strict_keys(reference, {"kind", "id", "version"}, f"{path}/definitionRef"))
    if isinstance(reference, dict):
        if reference.get("kind") not in {"factor", "strategy"}:
            issues.append(_issue(f"{path}/definitionRef/kind", "artifact.definition", "Definition kind must be factor or strategy"))
        if not isinstance(reference.get("id"), str) or not reference["id"].strip():
            issues.append(_issue(f"{path}/definitionRef/id", "artifact.definition", "Definition id must be non-empty"))
        if not isinstance(reference.get("version"), int) or isinstance(reference.get("version"), bool) or reference.get("version", 0) < 1:
            issues.append(_issue(f"{path}/definitionRef/version", "artifact.definition", "Definition version must be positive"))
    if not isinstance(value.get("definitionHash"), str) or not HASH.fullmatch(value.get("definitionHash", "")):
        issues.append(_issue(f"{path}/definitionHash", "schema.hash", "Invalid definition hash"))
    evidence = value.get("evidenceManifest")
    evidence_keys = {
        "data",
        "experimentDefinition",
        "runs",
        "assessment",
        "costs",
        "holdout",
        "limitations",
        "diagnostics",
        "artifactHashes",
        "metrics",
        "environment",
        "cpuEquivalentAllowed",
    }
    issues.extend(_strict_keys(evidence, evidence_keys, f"{path}/evidenceManifest"))
    if isinstance(evidence, dict):
        if not isinstance(evidence.get("runs"), list) or not evidence["runs"]:
            issues.append(_issue(f"{path}/evidenceManifest/runs", "artifact.closure", "At least one immutable Run reference is required"))
        for key in ("limitations", "diagnostics"):
            if not isinstance(evidence.get(key), list):
                issues.append(_issue(f"{path}/evidenceManifest/{key}", "schema.list", f"{key} must be a list"))
        hashes = evidence.get("artifactHashes")
        if not isinstance(hashes, dict) or any(
            not isinstance(key, str) or not key or not isinstance(item, str) or not HASH.fullmatch(item)
            for key, item in (hashes.items() if isinstance(hashes, dict) else [])
        ):
            issues.append(_issue(f"{path}/evidenceManifest/artifactHashes", "artifact.hashes", "artifactHashes must be a string-to-sha256 map"))
        metrics = evidence.get("metrics")
        if not isinstance(metrics, dict) or any(
            not isinstance(key, str)
            or not key
            or not isinstance(item, (int, float))
            or isinstance(item, bool)
            or not math.isfinite(float(item))
            for key, item in (metrics.items() if isinstance(metrics, dict) else [])
        ):
            issues.append(_issue(f"{path}/evidenceManifest/metrics", "artifact.metrics", "metrics must be finite numbers"))
        if not isinstance(evidence.get("environment"), dict) or not evidence["environment"]:
            issues.append(_issue(f"{path}/evidenceManifest/environment", "artifact.environment", "Exact environment is required"))
        if not isinstance(evidence.get("cpuEquivalentAllowed"), bool):
            issues.append(_issue(f"{path}/evidenceManifest/cpuEquivalentAllowed", "schema.boolean", "cpuEquivalentAllowed must be boolean"))
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        issues.append(_issue(f"{path}/reason", "schema.string", "Decision reason must be non-empty"))
    if issues:
        raise AutoQuantValidationError(issues)


def artifact_review_readiness(value: dict[str, Any]) -> dict[str, Any]:
    validate_artifact_review(value)
    evidence = value["evidenceManifest"]
    unresolved: list[str] = []
    for key in ("data", "experimentDefinition", "assessment", "costs", "holdout"):
        if evidence[key] is None:
            unresolved.append(key)
    if evidence.get("assessment") is not None:
        try:
            validate_verification_assessment(evidence["assessment"])
        except AutoQuantValidationError:
            if "coreEvidenceAssessment" not in unresolved:
                unresolved.append("coreEvidenceAssessment")
    if not evidence["runs"]:
        unresolved.append("runs")
    if evidence["diagnostics"]:
        unresolved.append("diagnostics")
    return {"ready": not unresolved, "unresolved": unresolved}


def _session_child_root(
    project: ProjectContext, session_id: str, name: str, *, create: bool = False
) -> Path:
    session = load_session(project, session_id)
    root = confined_path(session.root_dir, name, f"session/{name}")
    if create:
        root.mkdir(exist_ok=True)
    return root


def _object_root(parent: Path, object_id: str, issue_path: str) -> Path:
    if not OBJECT_ID.fullmatch(object_id):
        raise AutoQuantValidationError([_issue(issue_path, "artifact.id", "Invalid object id")])
    return confined_path(parent, object_id, issue_path)


def _publish_bundle(parent: Path, object_id: str, files: dict[str, dict[str, Any]], kind: str) -> Path:
    target = _object_root(parent, object_id, kind)
    if target.exists():
        raise AutoQuantValidationError([_issue(target, "artifact.collision", "Immutable object already exists")])
    temporary = parent / f".{object_id}.{uuid.uuid4().hex}.creating"
    try:
        temporary.mkdir()
        for name, value in files.items():
            _write_json(temporary / name, value)
        hashes = {name: hash_file(temporary / name) for name in sorted(files)}
        manifest = {
            "schemaVersion": 1,
            "kind": kind,
            "id": object_id,
            "completed": True,
            "files": hashes,
        }
        _write_json(temporary / MANIFEST, manifest)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return target


def _load_bundle(root: Path, kind: str, files: tuple[str, ...]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = _read_json(root / MANIFEST, "manifest")
    issues = _strict_keys(manifest, {"schemaVersion", "kind", "id", "completed", "files"}, root / MANIFEST)
    if manifest.get("schemaVersion") != 1 or manifest.get("kind") != kind or manifest.get("completed") is not True:
        issues.append(_issue(root / MANIFEST, "artifact.manifest", "Invalid immutable manifest"))
    expected = {}
    values = {}
    for name in files:
        path = root / name
        expected[name] = hash_file(path) if path.is_file() else None
        if path.is_file():
            values[name] = _read_json(path, name)
    if manifest.get("files") != expected:
        issues.append(_issue(root, "artifact.hash", "Immutable artifact hash mismatch"))
    if issues:
        raise AutoQuantValidationError(issues)
    return manifest, values


def publish_artifact_decision(
    project: ProjectContext, session_id: str, review: dict[str, Any]
) -> dict[str, Any]:
    validate_artifact_review(review)
    reference = review["definitionRef"]
    definition = (
        load_factor_definition(project, reference["id"], reference["version"])
        if reference["kind"] == "factor"
        else load_strategy_definition(project, reference["id"], reference["version"])
    )
    if definition.manifest["contentHash"] != review["definitionHash"]:
        raise AutoQuantValidationError([_issue("definitionHash", "artifact.stale-review", "Definition bytes changed or the review targets a different version")])
    readiness = artifact_review_readiness(review)
    if review["decision"] == "approve" and not readiness["ready"]:
        raise AutoQuantValidationError([_issue("evidenceManifest", "artifact.incomplete-closure", "Approval requires complete evidence closure: " + ", ".join(readiness["unresolved"]))])
    if review["decision"] == "approve":
        if definition.definition.get("status") != "approved":
            raise AutoQuantValidationError(
                [_issue("definitionRef", "artifact.definition-gate",
                        "Definition status must be 'approved' for artifact approval")])
        evidence = review["evidenceManifest"]
        experiment_ref = evidence.get("experimentDefinition")
        if not isinstance(experiment_ref, dict) or set(experiment_ref.keys()) != {"id", "version", "contentHash"}:
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition", "artifact.experiment-gate",
                        "experimentDefinition must contain exactly id, version, contentHash")])
        if not isinstance(experiment_ref["id"], str) or not experiment_ref["id"].strip():
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition/id", "artifact.experiment-gate",
                        "experimentDefinition id must be a non-empty string")])
        if not isinstance(experiment_ref["version"], int) or isinstance(experiment_ref["version"], bool) or experiment_ref["version"] < 1:
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition/version", "artifact.experiment-gate",
                        "experimentDefinition version must be a positive integer")])
        if not isinstance(experiment_ref["contentHash"], str) or not HASH.fullmatch(experiment_ref["contentHash"]):
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition/contentHash", "artifact.experiment-gate",
                        "experimentDefinition contentHash must be a valid sha256 hex string")])
        experiment = load_experiment_definition(project, session_id, experiment_ref["id"], experiment_ref["version"])
        if experiment.definition.get("status") != "frozen":
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition", "artifact.experiment-gate",
                        "Experiment definition status must be 'frozen'")])
        if experiment.manifest.get("contentHash") != experiment_ref["contentHash"]:
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition/contentHash", "artifact.experiment-gate",
                        "Experiment contentHash does not match evidence manifest")])
        if experiment.definition.get("definitionRef") != review["definitionRef"]:
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/experimentDefinition", "artifact.experiment-gate",
                        "Experiment definitionRef does not match review definitionRef")])
        if experiment.definition.get("data") != evidence.get("data"):
            raise AutoQuantValidationError(
                [_issue("evidenceManifest/data", "artifact.data-gate",
                        "Experiment data does not match evidence data")])
        # ── Run gate ─────────────────────────────────────────────
        reviewed_pairs: set[tuple[str, str]] = set()
        run_refs = evidence["runs"]
        for i, run_ref in enumerate(run_refs):
            if not isinstance(run_ref, dict):
                raise AutoQuantValidationError([_issue(
                    f"evidenceManifest/runs/{i}", "artifact.run-ref",
                    f"Run reference at index {i} must be a dict")])
            run_id = run_ref.get("id")
            if not isinstance(run_id, str) or not run_id.strip():
                raise AutoQuantValidationError([_issue(
                    f"evidenceManifest/runs/{i}/id", "artifact.run-ref",
                    f"Run reference id must be a non-empty string at index {i}")])
            run_hash = run_ref.get("hash")
            if not isinstance(run_hash, str) or not HASH.fullmatch(run_hash):
                raise AutoQuantValidationError([_issue(
                    f"evidenceManifest/runs/{i}/hash", "artifact.run-hash",
                    f"Run reference hash must be a valid sha256 hex string at index {i}")])
            run = load_run(project, run_id)
            if run.manifest["resultHash"] != run_hash:
                raise AutoQuantValidationError([_issue(
                    f"evidenceManifest/runs/{i}/hash", "artifact.run-hash",
                    f"Run hash does not match immutable Run result hash at index {i}")])
            pair = (run_id, run_hash)
            if pair in reviewed_pairs:
                raise AutoQuantValidationError([_issue(
                    f"evidenceManifest/runs/{i}", "artifact.run-ref",
                    f"Run ({run_id}) is cited more than once in evidence")])
            reviewed_pairs.add(pair)
        # validate researchBinding on every reviewed Run
        expected_binding: dict[str, Any] = {
            "definitionRef": {
                "kind": reference["kind"],
                "id": reference["id"],
                "version": reference["version"],
                "contentHash": review["definitionHash"],
            },
            "experimentDefinitionRef": {
                "kind": "experiment",
                "sessionId": session_id,
                "id": experiment_ref["id"],
                "version": experiment_ref["version"],
                "contentHash": experiment_ref["contentHash"],
            },
        }
        for i, run_ref in enumerate(run_refs):
            run_id = run_ref["id"]
            run = load_run(project, run_id)
            if run.result.get("researchBinding") != expected_binding:
                raise AutoQuantValidationError([_issue(
                    f"evidenceManifest/runs/{i}", "artifact.run-binding",
                    f"Run researchBinding does not match the review definition and experiment")])
        # ── end Run gate ─────────────────────────────────────────────
        # ── Assessment gate ─────────────────────────────────────────
        assessment = evidence["assessment"]
        validated_assessment = validate_verification_assessment(assessment)
        published = load_verification_assessment(project, validated_assessment["id"])["assessment"]
        if published != assessment:
            raise AutoQuantValidationError([_issue(
                "evidenceManifest/assessment", "artifact.assessment",
                "Published verification assessment does not match evidence manifest assessment")])
        run_refs_from_assessment = [ref for ref in published["evidenceRefs"] if ref["kind"] == "run"]
        assessment_run_pairs = {(ref["id"], ref["sha256"]) for ref in run_refs_from_assessment}
        if len(run_refs_from_assessment) != len(assessment_run_pairs):
            raise AutoQuantValidationError([_issue(
                "evidenceManifest/assessment/evidenceRefs", "artifact.assessment-runs",
                "Duplicate run references in assessment evidenceRefs")])
        if assessment_run_pairs != reviewed_pairs:
            raise AutoQuantValidationError([_issue(
                "evidenceManifest/assessment/evidenceRefs", "artifact.assessment-runs",
                "Assessment run references do not match evidence runs")])
        # ── end Assessment gate ─────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    artifact_id = (
        "artifact-" + hash_json({"definition": reference, "evidence": review["evidenceManifest"]})[:20]
        if review["decision"] == "approve"
        else None
    )
    decision = {
        "schemaVersion": 1,
        "kind": "autoquant-artifact-decision-receipt",
        "id": review["id"],
        "sessionId": session_id,
        "decision": review["decision"],
        "definitionRef": reference,
        "definitionHash": review["definitionHash"],
        "evidenceManifestHash": hash_json(review["evidenceManifest"]),
        "artifactId": artifact_id,
        "reason": review["reason"],
        "completedAt": now,
        "nextValidActions": (
            ["reproduction.start"]
            if artifact_id is not None
            else ["definition.create-draft", "research.inspect"]
        ),
    }
    root = _publish_bundle(
        _session_child_root(project, session_id, "artifact-decisions", create=True),
        review["id"],
        {ARTIFACT_REVIEW: review, ARTIFACT_DECISION: decision},
        "autoquant-artifact-decision-manifest",
    )
    return load_artifact_decision(project, session_id, root.name)


def load_artifact_decision(
    project: ProjectContext, session_id: str, decision_id: str
) -> dict[str, Any]:
    root = _object_root(
        _session_child_root(project, session_id, "artifact-decisions"),
        decision_id,
        "artifactDecision",
    )
    manifest, values = _load_bundle(
        root,
        "autoquant-artifact-decision-manifest",
        (ARTIFACT_DECISION, ARTIFACT_REVIEW),
    )
    validate_artifact_review(values[ARTIFACT_REVIEW], str(root / ARTIFACT_REVIEW))
    decision = values[ARTIFACT_DECISION]
    if decision.get("id") != decision_id or decision.get("sessionId") != session_id:
        raise AutoQuantValidationError([_issue(root, "artifact.identity", "Artifact decision identity mismatch")])
    return {"path": str(root), "manifest": manifest, "review": values[ARTIFACT_REVIEW], "decision": decision}


def list_artifact_decisions(project: ProjectContext, session_id: str) -> list[dict[str, Any]]:
    root = _session_child_root(project, session_id, "artifact-decisions")
    if not root.exists():
        return []
    return [
        load_artifact_decision(project, session_id, item.name)
        for item in sorted(root.iterdir())
        if item.is_dir() and not item.name.startswith(".")
    ]


def validate_reproduction_request(value: dict[str, Any], path: str = "reproductionRequest") -> None:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "approvalId",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "autoquant-reproduction-request":
        issues.append(_issue(path, "reproduction.request", "Invalid reproduction request kind or version"))
    for key in ("id", "approvalId"):
        if not isinstance(value.get(key), str) or not OBJECT_ID.fullmatch(value[key]):
            issues.append(_issue(f"{path}/{key}", "artifact.id", f"Invalid {key}"))
    if issues:
        raise AutoQuantValidationError(issues)


def publish_reproduction_receipt(
    project: ProjectContext, session_id: str, request: dict[str, Any]
) -> dict[str, Any]:
    validate_reproduction_request(request)
    approval = load_artifact_decision(project, session_id, request["approvalId"])
    if approval["decision"]["decision"] != "approve":
        raise AutoQuantValidationError([_issue("approvalId", "reproduction.unapproved", "Reproduction requires an approved artifact decision")])
    baseline = approval["review"]["evidenceManifest"]
    receipt = {
        "schemaVersion": 1,
        "kind": "autoquant-reproduction-receipt",
        "id": request["id"],
        "sessionId": session_id,
        "approvalId": request["approvalId"],
        "artifactId": approval["decision"]["artifactId"],
        "outcome": "unavailable",
        "environment": baseline["environment"],
        "inputsHash": hash_json({"approval": approval["manifest"], "request": request}),
        "differences": [
            {
                "field": "executor",
                "expected": "Core-controlled reproduction executor",
                "actual": "unavailable",
            }
        ],
        "originalEvidenceHash": approval["decision"]["evidenceManifestHash"],
        "completedAt": datetime.now(timezone.utc).isoformat(),
    }
    root = _publish_bundle(
        _session_child_root(project, session_id, "reproductions", create=True),
        request["id"],
        {REPRODUCTION_REQUEST: request, REPRODUCTION_RECEIPT: receipt},
        "autoquant-reproduction-manifest",
    )
    return load_reproduction_receipt(project, session_id, root.name)


def load_reproduction_receipt(
    project: ProjectContext, session_id: str, reproduction_id: str
) -> dict[str, Any]:
    root = _object_root(
        _session_child_root(project, session_id, "reproductions"),
        reproduction_id,
        "reproduction",
    )
    manifest, values = _load_bundle(
        root,
        "autoquant-reproduction-manifest",
        (REPRODUCTION_RECEIPT, REPRODUCTION_REQUEST),
    )
    validate_reproduction_request(values[REPRODUCTION_REQUEST], str(root / REPRODUCTION_REQUEST))
    receipt = values[REPRODUCTION_RECEIPT]
    if receipt.get("id") != reproduction_id or receipt.get("sessionId") != session_id or receipt.get("outcome") not in REPRODUCTION_OUTCOMES:
        raise AutoQuantValidationError([_issue(root, "reproduction.identity", "Invalid reproduction receipt")])
    return {"path": str(root), "manifest": manifest, "request": values[REPRODUCTION_REQUEST], "receipt": receipt}


def list_reproduction_receipts(project: ProjectContext, session_id: str) -> list[dict[str, Any]]:
    root = _session_child_root(project, session_id, "reproductions")
    if not root.exists():
        return []
    return [
        load_reproduction_receipt(project, session_id, item.name)
        for item in sorted(root.iterdir())
        if item.is_dir() and not item.name.startswith(".")
    ]


ARTIFACT_REVIEW_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant exact-version artifact review V1",
    "type": "object",
    "additionalProperties": False,
    "required": ["schemaVersion", "kind", "id", "decision", "actor", "definitionRef", "definitionHash", "evidenceManifest", "reason"],
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-artifact-review"},
        "id": {"type": "string", "pattern": OBJECT_ID.pattern},
        "decision": {"enum": sorted(DECISIONS)},
        "actor": {"type": "object"},
        "definitionRef": {"type": "object"},
        "definitionHash": {"type": "string", "pattern": HASH.pattern},
        "evidenceManifest": {"type": "object"},
        "reason": {"type": "string", "minLength": 1},
    },
}


REPRODUCTION_REQUEST_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant reproduction request V1",
    "type": "object",
    "additionalProperties": False,
    "required": ["schemaVersion", "kind", "id", "approvalId"],
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-reproduction-request"},
        "id": {"type": "string", "pattern": OBJECT_ID.pattern},
        "approvalId": {"type": "string", "pattern": OBJECT_ID.pattern},
    },
}
