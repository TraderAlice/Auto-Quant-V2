"""Strict immutable FactorDefinition and ExperimentDefinition versions."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .sessions import load_session
from .studies import hash_file
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


DEFINITION_SCHEMA_VERSION = 1
DEFINITION_FILE = "definition.json"
DEFINITION_MANIFEST = "manifest.json"
DEFINITION_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HASH = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class DefinitionContext:
    root_dir: Path
    manifest: dict[str, Any]
    definition: dict[str, Any]


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.missing", f"Missing {label}: {path}")]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    f"{label}.json",
                    f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.type", f"{label} must be an object")]
        )
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def _nonempty(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(_issue(path, "schema.string", "Expected a non-empty string"))


def _string_list(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        issues.append(_issue(path, "schema.list", "Expected a non-empty string list"))


def _validate_identity(value: dict[str, Any], path: str, kind: str) -> list[ValidationIssue]:
    issues = _strict_keys(
        value,
        {
            "schemaVersion",
            "kind",
            "id",
            "version",
            "status",
            "createdAt",
            "lineage",
        },
        path,
        optional=set(value) - {
            "schemaVersion",
            "kind",
            "id",
            "version",
            "status",
            "createdAt",
            "lineage",
        },
    )
    if value.get("schemaVersion") != DEFINITION_SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected V1"))
    if value.get("kind") != kind:
        issues.append(_issue(f"{path}/kind", "definition.kind", f"Expected {kind}"))
    if not isinstance(value.get("id"), str) or not DEFINITION_ID.fullmatch(value["id"]):
        issues.append(_issue(f"{path}/id", "definition.id", "Invalid definition id"))
    version = value.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        issues.append(_issue(f"{path}/version", "definition.version", "Version must be positive"))
    _nonempty(value.get("createdAt"), f"{path}/createdAt", issues)
    lineage = value.get("lineage")
    issues.extend(_strict_keys(lineage, {"parentVersion"}, f"{path}/lineage"))
    if isinstance(lineage, dict):
        parent = lineage.get("parentVersion")
        if parent is not None and (
            not isinstance(parent, int)
            or isinstance(parent, bool)
            or parent < 1
            or (isinstance(version, int) and parent >= version)
        ):
            issues.append(
                _issue(
                    f"{path}/lineage/parentVersion",
                    "definition.lineage",
                    "parentVersion must be null or an earlier positive version",
                )
            )
    return issues


def validate_factor_definition(value: dict[str, Any], path: str = "factorDefinition") -> None:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "status",
        "createdAt",
        "lineage",
        "hypothesis",
        "calculation",
        "parameters",
        "output",
        "dataDependencies",
        "missingDataPolicy",
        "cohort",
        "expectedHorizon",
        "requiredTests",
        "failureGates",
    }
    issues = _strict_keys(value, required, path)
    issues.extend(_validate_identity(value, path, "autoquant-factor-definition"))
    if value.get("status") not in {"draft", "approved", "retired"}:
        issues.append(_issue(f"{path}/status", "definition.status", "Invalid factor status"))
    _nonempty(value.get("hypothesis"), f"{path}/hypothesis", issues)
    calculation = value.get("calculation")
    issues.extend(
        _strict_keys(calculation, {"kind", "identity", "sourceHash"}, f"{path}/calculation")
    )
    if isinstance(calculation, dict):
        if calculation.get("kind") not in {"source", "expression"}:
            issues.append(_issue(f"{path}/calculation/kind", "definition.calculation", "Invalid calculation kind"))
        _nonempty(calculation.get("identity"), f"{path}/calculation/identity", issues)
        identity = calculation.get("identity")
        if calculation.get("kind") == "source" and isinstance(identity, str):
            source_path, separator, symbol = identity.partition(":")
            candidate = PurePosixPath(source_path)
            if (
                not separator
                or not symbol
                or "\\" in source_path
                or candidate.is_absolute()
                or ".." in candidate.parts
                or candidate.suffix != ".py"
                or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol)
            ):
                issues.append(
                    _issue(
                        f"{path}/calculation/identity",
                        "definition.source-identity",
                        "Source identity must be a confined .py path and symbol",
                    )
                )
        if not isinstance(calculation.get("sourceHash"), str) or not HASH.fullmatch(calculation["sourceHash"]):
            issues.append(_issue(f"{path}/calculation/sourceHash", "schema.hash", "Invalid source hash"))
    parameters = value.get("parameters")
    if not isinstance(parameters, dict):
        issues.append(_issue(f"{path}/parameters", "schema.type", "parameters must be an object"))
    else:
        for name, parameter in parameters.items():
            parameter_path = f"{path}/parameters/{name}"
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,63}", name):
                issues.append(_issue(parameter_path, "definition.parameter-name", "Parameter names must be bounded identifiers"))
            if isinstance(parameter, bool):
                continue
            if not isinstance(parameter, (int, float)) or not math.isfinite(parameter):
                issues.append(_issue(parameter_path, "definition.parameter-value", "Parameters accept only finite numbers or booleans; credentials and opaque objects belong in Core-managed configuration"))
    output = value.get("output")
    issues.extend(_strict_keys(output, {"direction", "unit"}, f"{path}/output"))
    if isinstance(output, dict):
        if output.get("direction") not in {"higher", "lower", "bidirectional"}:
            issues.append(_issue(f"{path}/output/direction", "definition.direction", "Invalid output direction"))
        _nonempty(output.get("unit"), f"{path}/output/unit", issues)
    dependencies = value.get("dataDependencies")
    if not isinstance(dependencies, list) or not dependencies:
        issues.append(_issue(f"{path}/dataDependencies", "schema.list", "At least one data dependency is required"))
    else:
        for index, dependency in enumerate(dependencies):
            dep_path = f"{path}/dataDependencies/{index}"
            issues.extend(
                _strict_keys(
                    dependency,
                    {"packageId", "version", "fields", "availability"},
                    dep_path,
                )
            )
            if isinstance(dependency, dict):
                _nonempty(dependency.get("packageId"), f"{dep_path}/packageId", issues)
                _nonempty(dependency.get("version"), f"{dep_path}/version", issues)
                _string_list(dependency.get("fields"), f"{dep_path}/fields", issues)
                availability = dependency.get("availability")
                issues.extend(
                    _strict_keys(
                        availability,
                        {"pointInTime", "marketClock"},
                        f"{dep_path}/availability",
                    )
                )
                if isinstance(availability, dict):
                    if not isinstance(availability.get("pointInTime"), bool):
                        issues.append(_issue(f"{dep_path}/availability/pointInTime", "schema.boolean", "pointInTime must be boolean"))
                    clock = availability.get("marketClock")
                    if clock is not None:
                        issues.extend(
                            _strict_keys(clock, {"id", "version"}, f"{dep_path}/availability/marketClock")
                        )
                        if isinstance(clock, dict):
                            _nonempty(clock.get("id"), f"{dep_path}/availability/marketClock/id", issues)
                            _nonempty(clock.get("version"), f"{dep_path}/availability/marketClock/version", issues)
    for key in ("missingDataPolicy", "expectedHorizon"):
        _nonempty(value.get(key), f"{path}/{key}", issues)
    cohort = value.get("cohort")
    issues.extend(_strict_keys(cohort, {"kind", "identity"}, f"{path}/cohort"))
    if isinstance(cohort, dict):
        _nonempty(cohort.get("kind"), f"{path}/cohort/kind", issues)
        _nonempty(cohort.get("identity"), f"{path}/cohort/identity", issues)
    _string_list(value.get("requiredTests"), f"{path}/requiredTests", issues)
    _string_list(value.get("failureGates"), f"{path}/failureGates", issues)
    if issues:
        raise AutoQuantValidationError(issues)


def factor_readiness(value: dict[str, Any]) -> dict[str, Any]:
    validate_factor_definition(value)
    unresolved = []
    for dependency in value["dataDependencies"]:
        availability = dependency["availability"]
        if not availability["pointInTime"]:
            unresolved.append(f"data:{dependency['packageId']}:{dependency['version']}:point-in-time")
        if availability["marketClock"] is None:
            unresolved.append(f"data:{dependency['packageId']}:{dependency['version']}:market-clock")
    return {"ready": not unresolved, "unresolved": unresolved}


def validate_experiment_definition(
    value: dict[str, Any], path: str = "experimentDefinition"
) -> None:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "status",
        "createdAt",
        "lineage",
        "definitionRef",
        "data",
        "subject",
        "outcome",
        "benchmark",
        "costPolicy",
        "splitPolicy",
        "robustness",
        "selectionAdjustment",
        "holdoutPolicy",
        "executorPolicy",
        "budget",
        "stopConditions",
    }
    issues = _strict_keys(value, required, path)
    issues.extend(_validate_identity(value, path, "autoquant-experiment-definition"))
    if value.get("status") not in {"draft", "frozen"}:
        issues.append(_issue(f"{path}/status", "definition.status", "Invalid experiment status"))
    reference = value.get("definitionRef")
    issues.extend(_strict_keys(reference, {"kind", "id", "version"}, f"{path}/definitionRef"))
    if isinstance(reference, dict):
        if reference.get("kind") not in {"factor", "strategy"}:
            issues.append(_issue(f"{path}/definitionRef/kind", "definition.reference", "Reference kind must be factor or strategy"))
        if not isinstance(reference.get("id"), str) or not DEFINITION_ID.fullmatch(reference["id"]):
            issues.append(_issue(f"{path}/definitionRef/id", "definition.id", "Invalid referenced definition id"))
        if not isinstance(reference.get("version"), int) or isinstance(reference.get("version"), bool) or reference.get("version", 0) < 1:
            issues.append(_issue(f"{path}/definitionRef/version", "definition.version", "Invalid referenced version"))
    for key in ("data", "subject", "outcome", "benchmark"):
        item = value.get(key)
        item_keys = {
            "data": {"packageId", "version"},
            "subject": {"kind", "id", "version"},
            "outcome": {"name", "horizon"},
            "benchmark": {"id", "version"},
        }[key]
        issues.extend(_strict_keys(item, item_keys, f"{path}/{key}"))
        if isinstance(item, dict):
            for child in item_keys:
                if child == "version" and isinstance(item.get(child), int) and not isinstance(item.get(child), bool):
                    if item[child] < 1:
                        issues.append(_issue(f"{path}/{key}/{child}", "definition.version", "Version must be positive"))
                else:
                    _nonempty(item.get(child), f"{path}/{key}/{child}", issues)
    for key in (
        "costPolicy",
        "splitPolicy",
        "robustness",
        "selectionAdjustment",
        "holdoutPolicy",
        "executorPolicy",
    ):
        if not isinstance(value.get(key), dict) or not value[key]:
            issues.append(_issue(f"{path}/{key}", "schema.object", f"{key} must be a non-empty object"))
    budget = value.get("budget")
    issues.extend(
        _strict_keys(
            budget,
            {"candidateLimit", "wallTimeSeconds", "cpuSeconds", "gpuSeconds", "cost"},
            f"{path}/budget",
        )
    )
    if isinstance(budget, dict):
        for key in ("candidateLimit", "wallTimeSeconds", "cpuSeconds"):
            item = budget.get(key)
            if not isinstance(item, int) or isinstance(item, bool) or item < 1:
                issues.append(_issue(f"{path}/budget/{key}", "schema.range", f"{key} must be positive"))
        gpu = budget.get("gpuSeconds")
        if not isinstance(gpu, int) or isinstance(gpu, bool) or gpu < 0:
            issues.append(_issue(f"{path}/budget/gpuSeconds", "schema.range", "gpuSeconds must be non-negative"))
        cost = budget.get("cost")
        if cost is not None:
            issues.extend(_strict_keys(cost, {"currency", "amount"}, f"{path}/budget/cost"))
            if isinstance(cost, dict):
                _nonempty(cost.get("currency"), f"{path}/budget/cost/currency", issues)
                amount = cost.get("amount")
                if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
                    issues.append(_issue(f"{path}/budget/cost/amount", "schema.range", "Cost amount must be positive"))
    _string_list(value.get("stopConditions"), f"{path}/stopConditions", issues)
    if issues:
        raise AutoQuantValidationError(issues)


def validate_strategy_definition(
    value: dict[str, Any], path: str = "strategyDefinition"
) -> None:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "status",
        "createdAt",
        "lineage",
        "factorRefs",
        "composition",
        "portfolioValidation",
        "mlValidation",
        "rlValidation",
        "costPolicy",
        "riskAssumptions",
        "holdoutPolicy",
        "artifactClosure",
    }
    issues = _strict_keys(value, required, path)
    issues.extend(_validate_identity(value, path, "autoquant-strategy-definition"))
    if value.get("status") not in {"draft", "approved", "retired"}:
        issues.append(_issue(f"{path}/status", "definition.status", "Invalid strategy status"))
    references = value.get("factorRefs")
    if not isinstance(references, list) or not references:
        issues.append(_issue(f"{path}/factorRefs", "schema.list", "At least one exact FactorDefinition reference is required"))
    else:
        for index, reference in enumerate(references):
            ref_path = f"{path}/factorRefs/{index}"
            issues.extend(_strict_keys(reference, {"id", "version"}, ref_path))
            if isinstance(reference, dict):
                if not isinstance(reference.get("id"), str) or not DEFINITION_ID.fullmatch(reference["id"]):
                    issues.append(_issue(f"{ref_path}/id", "definition.id", "Invalid FactorDefinition id"))
                if not isinstance(reference.get("version"), int) or isinstance(reference.get("version"), bool) or reference.get("version", 0) < 1:
                    issues.append(_issue(f"{ref_path}/version", "definition.version", "Invalid FactorDefinition version"))
    for key in (
        "composition",
        "portfolioValidation",
        "costPolicy",
        "riskAssumptions",
        "holdoutPolicy",
        "artifactClosure",
    ):
        if not isinstance(value.get(key), dict) or not value[key]:
            issues.append(_issue(f"{path}/{key}", "schema.object", f"{key} must be a non-empty object"))
    for key in ("mlValidation", "rlValidation"):
        if value.get(key) is not None and (
            not isinstance(value[key], dict) or not value[key]
        ):
            issues.append(_issue(f"{path}/{key}", "schema.object", f"{key} must be null or a non-empty object"))
    if issues:
        raise AutoQuantValidationError(issues)


def experiment_readiness(value: dict[str, Any]) -> dict[str, Any]:
    try:
        validate_experiment_definition(value)
    except AutoQuantValidationError as error:
        missing = [issue.path for issue in error.issues if issue.code == "schema.missing"]
        return {
            "ready": False,
            "unresolved": missing,
            "diagnostics": [str(issue.message) if hasattr(issue, 'message') else issue.code for issue in error.issues],
        }
    unresolved = []
    if value["status"] != "frozen":
        unresolved.append("status:frozen")
    budget = value["budget"]
    if not isinstance(budget.get("cost"), dict) and not budget.get("candidateLimit"):
        unresolved.append("budget:candidate-limit-or-cost-required")
    cost_policy = value.get("costPolicy", {})
    if not cost_policy:
        unresolved.append("cost-policy:required")
    holdout = value.get("holdoutPolicy", {})
    if not holdout:
        unresolved.append("holdout-policy:required")
    executor = value.get("executorPolicy", {})
    if not executor:
        unresolved.append("executor-policy:required")
    stop = value.get("stopConditions", [])
    if not stop:
        unresolved.append("stop-conditions:required")
    return {"ready": not unresolved, "unresolved": unresolved}


def _factor_versions_root(project: ProjectContext, definition_id: str) -> Path:
    if not DEFINITION_ID.fullmatch(definition_id):
        raise AutoQuantValidationError([_issue("definition_id", "definition.id", "Invalid definition id")])
    factors_relative = project.manifest.directories["factors"]
    relative = f"{factors_relative}/definitions/{definition_id}/versions"
    return confined_path(project.root_dir, relative, "project/factorDefinitions")


def _experiment_versions_root(
    project: ProjectContext, session_id: str, definition_id: str
) -> Path:
    if not DEFINITION_ID.fullmatch(definition_id):
        raise AutoQuantValidationError([_issue("definition_id", "definition.id", "Invalid definition id")])
    session = load_session(project, session_id)
    return confined_path(
        session.root_dir,
        f"experiment-definitions/{definition_id}/versions",
        "session/experimentDefinitions",
    )


def _strategy_versions_root(project: ProjectContext, definition_id: str) -> Path:
    if not DEFINITION_ID.fullmatch(definition_id):
        raise AutoQuantValidationError([_issue("definition_id", "definition.id", "Invalid definition id")])
    strategies_relative = project.manifest.directories["strategies"]
    relative = f"{strategies_relative}/definitions/{definition_id}/versions"
    return confined_path(project.root_dir, relative, "project/strategyDefinitions")


def _validate_transition(
    kind: str, parent_status: str, child_status: str, definition_id: str
) -> None:
    """Validate kind-specific definition lifecycle transitions.

    Factor/Strategy: draft → approved → retired; edits from approved fork a new draft.
    Experiment: draft → frozen; edits from frozen fork a new draft.
    """
    legal: set[tuple[str, str]]
    if kind in ("autoquant-factor-definition", "autoquant-strategy-definition"):
        legal = {
            ("draft", "draft"),
            ("draft", "approved"),
            ("approved", "draft"),
            ("approved", "retired"),
        }
    elif kind == "autoquant-experiment-definition":
        legal = {
            ("draft", "draft"),
            ("draft", "frozen"),
            ("frozen", "draft"),
        }
    else:
        raise AutoQuantValidationError(
            [_issue("kind", "definition.kind", f"Unknown definition kind: {kind}")]
        )
    if (parent_status, child_status) not in legal:
        raise AutoQuantValidationError(
            [
                _issue(
                    "status",
                    "definition.lifecycle",
                    f"Illegal transition: {parent_status} → {child_status} for {kind}",
                )
            ]
        )


def _publish(root: Path, value: dict[str, Any]) -> DefinitionContext:
    version = value["version"]
    kind = value["kind"]
    definition_id = value["id"]
    status = value["status"]
    parent_version = value["lineage"]["parentVersion"]
    if version == 1:
        if parent_version is not None:
            raise AutoQuantValidationError(
                [_issue("lineage/parentVersion", "definition.lineage", "Version 1 cannot have a parent")]
            )
        if status != "draft":
            raise AutoQuantValidationError(
                [
                    _issue(
                        "status",
                        "definition.lifecycle",
                        "Version 1 must be created as draft; use an explicit transition function to advance status",
                    )
                ]
            )
    else:
        if parent_version != version - 1:
            raise AutoQuantValidationError(
                [
                    _issue(
                        "lineage/parentVersion",
                        "definition.lineage",
                        "Definition versions must reference the immediately preceding version",
                    )
                ]
            )
        parent = _load(
            root / str(parent_version),
            kind,
            definition_id,
            parent_version,
        )
        if parent.definition["status"] == "retired":
            raise AutoQuantValidationError(
                [_issue("lineage", "definition.retired", "Retired definitions cannot be extended")]
            )
        _validate_transition(kind, parent.definition["status"], status, definition_id)
    root.mkdir(parents=True, exist_ok=True)
    target = root / str(version)
    temporary = root / f".{version}.{uuid.uuid4().hex}.creating"
    if target.exists():
        raise AutoQuantValidationError([_issue(target, "definition.collision", "Definition version already exists")])
    try:
        temporary.mkdir()
        _write_json(temporary / DEFINITION_FILE, value)
        content_hash = hash_file(temporary / DEFINITION_FILE)
        manifest = {
            "schemaVersion": DEFINITION_SCHEMA_VERSION,
            "kind": "autoquant-definition-version-manifest",
            "definitionKind": value["kind"],
            "id": value["id"],
            "version": version,
            "status": value["status"],
            "completed": True,
            "contentHash": content_hash,
            "files": {DEFINITION_FILE: content_hash},
        }
        _write_json(temporary / DEFINITION_MANIFEST, manifest)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return _load(target, value["kind"], value["id"], version)


def _load(root: Path, kind: str, definition_id: str, version: int) -> DefinitionContext:
    manifest_path = root / DEFINITION_MANIFEST
    definition_path = root / DEFINITION_FILE
    manifest = _read_json(manifest_path, "Definition manifest")
    required = {
        "schemaVersion",
        "kind",
        "definitionKind",
        "id",
        "version",
        "status",
        "completed",
        "contentHash",
        "files",
    }
    issues = _strict_keys(manifest, required, manifest_path)
    if manifest.get("schemaVersion") != DEFINITION_SCHEMA_VERSION:
        issues.append(_issue(manifest_path, "schema.version", "Expected definition manifest V1"))
    if manifest.get("kind") != "autoquant-definition-version-manifest":
        issues.append(_issue(manifest_path, "definition.manifest-kind", "Invalid manifest kind"))
    if manifest.get("definitionKind") != kind or manifest.get("id") != definition_id or manifest.get("version") != version:
        issues.append(_issue(manifest_path, "definition.identity", "Definition manifest identity mismatch"))
    expected_hash = hash_file(definition_path) if definition_path.is_file() else None
    if expected_hash is None or manifest.get("contentHash") != expected_hash or manifest.get("files") != {DEFINITION_FILE: expected_hash}:
        issues.append(_issue(definition_path, "definition.hash", "Definition content hash mismatch"))
    if issues:
        raise AutoQuantValidationError(issues)
    definition = _read_json(definition_path, "Definition")
    if kind == "autoquant-factor-definition":
        validate_factor_definition(definition, str(definition_path))
    elif kind == "autoquant-experiment-definition":
        validate_experiment_definition(definition, str(definition_path))
    else:
        validate_strategy_definition(definition, str(definition_path))
    if definition["id"] != definition_id or definition["version"] != version or definition["status"] != manifest["status"]:
        raise AutoQuantValidationError([_issue(definition_path, "definition.identity", "Definition content identity mismatch")])
    return DefinitionContext(root, manifest, definition)


def create_factor_definition_version(
    project: ProjectContext, value: dict[str, Any]
) -> DefinitionContext:
    validate_factor_definition(value)
    if value.get("status") != "draft":
        raise AutoQuantValidationError(
            [
                _issue(
                    "status",
                    "definition.lifecycle",
                    "create_factor_definition_version only accepts draft status; use approve_factor_definition or retire_factor_definition to transition",
                )
            ]
        )
    return _publish(_factor_versions_root(project, value["id"]), deepcopy(value))


def load_factor_definition(
    project: ProjectContext, definition_id: str, version: int
) -> DefinitionContext:
    root = _factor_versions_root(project, definition_id) / str(version)
    return _load(root, "autoquant-factor-definition", definition_id, version)


def list_factor_definitions(project: ProjectContext) -> list[DefinitionContext]:
    factors = confined_path(
        project.root_dir,
        f"{project.manifest.directories['factors']}/definitions",
        "project/factorDefinitions",
    )
    if not factors.exists():
        return []
    result = []
    for definition_root in sorted(factors.iterdir()):
        versions = definition_root / "versions"
        if definition_root.is_dir() and versions.is_dir():
            version_roots = [item for item in versions.iterdir() if item.name.isdigit()]
            for version_root in sorted(version_roots, key=lambda item: int(item.name)):
                result.append(load_factor_definition(project, definition_root.name, int(version_root.name)))
    return result


def create_strategy_definition_version(
    project: ProjectContext, value: dict[str, Any]
) -> DefinitionContext:
    validate_strategy_definition(value)
    if value.get("status") != "draft":
        raise AutoQuantValidationError(
            [
                _issue(
                    "status",
                    "definition.lifecycle",
                    "create_strategy_definition_version only accepts draft status; use approve_strategy_definition or retire_strategy_definition to transition",
                )
            ]
        )
    for reference in value["factorRefs"]:
        factor = load_factor_definition(project, reference["id"], reference["version"])
        if factor.definition["status"] != "approved":
            raise AutoQuantValidationError([_issue("factorRefs", "definition.unapproved", "StrategyDefinition requires approved FactorDefinition versions")])
    return _publish(_strategy_versions_root(project, value["id"]), deepcopy(value))


def load_strategy_definition(
    project: ProjectContext, definition_id: str, version: int
) -> DefinitionContext:
    root = _strategy_versions_root(project, definition_id) / str(version)
    return _load(root, "autoquant-strategy-definition", definition_id, version)


def list_strategy_definitions(project: ProjectContext) -> list[DefinitionContext]:
    strategies = confined_path(
        project.root_dir,
        f"{project.manifest.directories['strategies']}/definitions",
        "project/strategyDefinitions",
    )
    if not strategies.exists():
        return []
    result = []
    for definition_root in sorted(strategies.iterdir()):
        versions = definition_root / "versions"
        if definition_root.is_dir() and versions.is_dir():
            version_roots = [item for item in versions.iterdir() if item.name.isdigit()]
            for version_root in sorted(version_roots, key=lambda item: int(item.name)):
                result.append(load_strategy_definition(project, definition_root.name, int(version_root.name)))
    return result


def _validate_experiment_reference(
    project: ProjectContext, reference: dict[str, Any]
) -> None:
    """Re-load and re-validate the definitionRef at gate time.

    Every gate (create, freeze) re-verifies that the referenced
    FactorDefinition or StrategyDefinition version still exists on disk,
    passes tamper (hash) checks, is still approved, and — for factors —
    still passes factor_readiness with all data-availability clocks resolved.
    """
    if reference["kind"] == "factor":
        factor = load_factor_definition(project, reference["id"], reference["version"])
        if factor.definition["status"] != "approved":
            raise AutoQuantValidationError(
                [_issue("definitionRef", "definition.unapproved",
                        "ExperimentDefinition requires an approved FactorDefinition version")]
            )
        readiness = factor_readiness(factor.definition)
        if not readiness["ready"]:
            raise AutoQuantValidationError(
                [_issue("definitionRef", "definition.unready",
                        f"FactorDefinition is not validation-ready: {', '.join(readiness['unresolved'])}")]
            )
    else:
        strategy = load_strategy_definition(project, reference["id"], reference["version"])
        if strategy.definition["status"] != "approved":
            raise AutoQuantValidationError(
                [_issue("definitionRef", "definition.unapproved",
                        "ExperimentDefinition requires an approved StrategyDefinition version")]
            )


def create_experiment_definition_version(
    project: ProjectContext, session_id: str, value: dict[str, Any]
) -> DefinitionContext:
    validate_experiment_definition(value)
    if value.get("status") != "draft":
        raise AutoQuantValidationError(
            [
                _issue(
                    "status",
                    "definition.lifecycle",
                    "create_experiment_definition_version only accepts draft status; use freeze_experiment_definition to transition",
                )
            ]
        )
    _validate_experiment_reference(project, value["definitionRef"])
    return _publish(
        _experiment_versions_root(project, session_id, value["id"]),
        deepcopy(value),
    )


def load_experiment_definition(
    project: ProjectContext, session_id: str, definition_id: str, version: int
) -> DefinitionContext:
    root = _experiment_versions_root(project, session_id, definition_id) / str(version)
    return _load(root, "autoquant-experiment-definition", definition_id, version)


def list_experiment_definitions(
    project: ProjectContext, session_id: str
) -> list[DefinitionContext]:
    session = load_session(project, session_id)
    root = confined_path(session.root_dir, "experiment-definitions", "session/experimentDefinitions")
    if not root.exists():
        return []
    result = []
    for definition_root in sorted(root.iterdir()):
        versions = definition_root / "versions"
        if definition_root.is_dir() and versions.is_dir():
            version_roots = [item for item in versions.iterdir() if item.name.isdigit()]
            for version_root in sorted(version_roots, key=lambda item: int(item.name)):
                result.append(load_experiment_definition(project, session_id, definition_root.name, int(version_root.name)))
    return result


def new_definition_version(
    current: dict[str, Any], changes: dict[str, Any], *, status: str = "draft"
) -> dict[str, Any]:
    immutable = {"schemaVersion", "kind", "id", "version", "createdAt", "lineage"}
    forbidden = immutable.intersection(changes)
    if forbidden:
        raise AutoQuantValidationError([_issue("changes", "definition.identity", f"Cannot edit identity fields: {', '.join(sorted(forbidden))}")])
    result = deepcopy(current)
    result.update(deepcopy(changes))
    result["version"] = current["version"] + 1
    result["status"] = status
    result["createdAt"] = datetime.now(timezone.utc).isoformat()
    result["lineage"] = {"parentVersion": current["version"]}
    return result


def approve_factor_definition(
    project: ProjectContext, definition_id: str, version: int
) -> DefinitionContext:
    """Approve a draft FactorDefinition version.

    An approved version is immutable and cannot be edited in place.
    Edits to an approved version fork a new draft with lineage.
    """
    current = load_factor_definition(project, definition_id, version)
    if current.definition["status"] != "draft":
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.status", "Only draft definitions can be approved")]
        )
    readiness = factor_readiness(current.definition)
    if not readiness["ready"]:
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.not-ready", f"Definition is not validation-ready: {', '.join(readiness['unresolved'])}")]
        )
    next_def = new_definition_version(current.definition, {}, status="approved")
    return _publish(_factor_versions_root(project, definition_id), next_def)


def retire_factor_definition(
    project: ProjectContext, definition_id: str, version: int
) -> DefinitionContext:
    """Retire an approved FactorDefinition version.

    Retired versions cannot be extended. Existing Runs remain bound.
    """
    current = load_factor_definition(project, definition_id, version)
    if current.definition["status"] != "approved":
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.status", "Only approved definitions can be retired")]
        )
    next_def = new_definition_version(current.definition, {}, status="retired")
    return _publish(_factor_versions_root(project, definition_id), next_def)


def approve_strategy_definition(
    project: ProjectContext, definition_id: str, version: int
) -> DefinitionContext:
    """Approve a draft StrategyDefinition version."""
    current = load_strategy_definition(project, definition_id, version)
    if current.definition["status"] != "draft":
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.status", "Only draft definitions can be approved")]
        )
    for reference in current.definition["factorRefs"]:
        factor = load_factor_definition(project, reference["id"], reference["version"])
        if factor.definition["status"] != "approved":
            raise AutoQuantValidationError(
                [_issue(f"{definition_id} v{version}", "definition.unapproved-factor", f"Factor {reference['id']} v{reference['version']} is not approved")]
            )
    next_def = new_definition_version(current.definition, {}, status="approved")
    return _publish(_strategy_versions_root(project, definition_id), next_def)


def retire_strategy_definition(
    project: ProjectContext, definition_id: str, version: int
) -> DefinitionContext:
    """Retire an approved StrategyDefinition version."""
    current = load_strategy_definition(project, definition_id, version)
    if current.definition["status"] != "approved":
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.status", "Only approved definitions can be retired")]
        )
    next_def = new_definition_version(current.definition, {}, status="retired")
    return _publish(_strategy_versions_root(project, definition_id), next_def)


def freeze_experiment_definition(
    project: ProjectContext, session_id: str, definition_id: str, version: int
) -> DefinitionContext:
    """Freeze a draft ExperimentDefinition.

    Freezing requires all PIT, clock, cost, stop, and holdout fields to be
    resolved. A frozen experiment is immutable and becomes the plan that
    ExperimentRuns reference.

    The referenced FactorDefinition or StrategyDefinition is re-loaded and
    re-validated at freeze time: it must still exist on disk, pass tamper
    (hash) checks, be approved, and for factors — still satisfy
    factor_readiness with all data-availability clocks resolved.
    """
    current = load_experiment_definition(project, session_id, definition_id, version)
    if current.definition["status"] != "draft":
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.status", "Only draft experiment definitions can be frozen")]
        )
    # Re-load and re-validate the referenced definition at freeze time
    _validate_experiment_reference(project, current.definition["definitionRef"])
    # Check structural readiness: all required fields must be non-empty
    # (costPolicy, splitPolicy, robustness, holdoutPolicy, executorPolicy)
    for key in ("costPolicy", "splitPolicy", "robustness", "holdoutPolicy", "executorPolicy"):
        if not isinstance(current.definition.get(key), dict) or not current.definition[key]:
            raise AutoQuantValidationError(
                [_issue(f"{definition_id} v{version}", "definition.not-ready", f"ExperimentDefinition is missing required field: {key}")]
            )
    if not isinstance(current.definition.get("stopConditions"), list) or not current.definition["stopConditions"]:
        raise AutoQuantValidationError(
            [_issue(f"{definition_id} v{version}", "definition.not-ready", "ExperimentDefinition is missing required field: stopConditions")]
        )
    next_def = new_definition_version(current.definition, {}, status="frozen")
    return _publish(_experiment_versions_root(project, session_id, definition_id), next_def)


def semantic_definition_diff(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    if before.get("kind") != after.get("kind") or before.get("id") != after.get("id"):
        raise AutoQuantValidationError([_issue("definitions", "definition.identity", "Semantic diff requires the same definition identity")])
    ignored = {"createdAt", "lineage", "status", "version"}
    changes = []
    for key in sorted((set(before) | set(after)) - ignored):
        if before.get(key) != after.get(key):
            changes.append({"field": key, "before": before.get(key), "after": after.get(key)})
    evidence_fields = {
        "calculation",
        "parameters",
        "dataDependencies",
        "cohort",
        "expectedHorizon",
        "definitionRef",
        "data",
        "subject",
        "outcome",
        "benchmark",
        "costPolicy",
        "splitPolicy",
        "holdoutPolicy",
        "executorPolicy",
        "factorRefs",
        "composition",
        "portfolioValidation",
        "mlValidation",
        "rlValidation",
        "riskAssumptions",
        "artifactClosure",
    }
    invalidated = [item["field"] for item in changes if item["field"] in evidence_fields]
    return {
        "kind": "autoquant-semantic-definition-diff",
        "definition": {"kind": before["kind"], "id": before["id"]},
        "fromVersion": before["version"],
        "toVersion": after["version"],
        "changes": changes,
        "affectedEvidence": invalidated,
        "invalidatedAssumptions": invalidated,
    }


FACTOR_DEFINITION_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant FactorDefinition V1",
    "type": "object",
    "required": [
        "schemaVersion", "kind", "id", "version", "status", "createdAt", "lineage",
        "hypothesis", "calculation", "parameters", "output", "dataDependencies",
        "missingDataPolicy", "cohort", "expectedHorizon", "requiredTests", "failureGates",
    ],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-factor-definition"},
        "id": {"type": "string", "pattern": DEFINITION_ID.pattern},
        "version": {"type": "integer", "minimum": 1},
        "status": {"enum": ["draft", "approved", "retired"]},
        "createdAt": {"type": "string", "minLength": 1},
        "lineage": {"type": "object"},
        "hypothesis": {"type": "string", "minLength": 1},
        "calculation": {"type": "object"},
        "parameters": {"type": "object"},
        "output": {"type": "object"},
        "dataDependencies": {"type": "array", "minItems": 1},
        "missingDataPolicy": {"type": "string", "minLength": 1},
        "cohort": {"type": "object"},
        "expectedHorizon": {"type": "string", "minLength": 1},
        "requiredTests": {"type": "array", "minItems": 1},
        "failureGates": {"type": "array", "minItems": 1},
    },
}


EXPERIMENT_DEFINITION_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant ExperimentDefinition V1",
    "type": "object",
    "required": [
        "schemaVersion", "kind", "id", "version", "status", "createdAt", "lineage",
        "definitionRef", "data", "subject", "outcome", "benchmark", "costPolicy",
        "splitPolicy", "robustness", "selectionAdjustment", "holdoutPolicy",
        "executorPolicy", "budget", "stopConditions",
    ],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-experiment-definition"},
        "id": {"type": "string", "pattern": DEFINITION_ID.pattern},
        "version": {"type": "integer", "minimum": 1},
        "status": {"enum": ["draft", "frozen"]},
        "createdAt": {"type": "string", "minLength": 1},
        "lineage": {"type": "object"},
        "definitionRef": {"type": "object"},
        "data": {"type": "object"},
        "subject": {"type": "object"},
        "outcome": {"type": "object"},
        "benchmark": {"type": "object"},
        "costPolicy": {"type": "object", "minProperties": 1},
        "splitPolicy": {"type": "object", "minProperties": 1},
        "robustness": {"type": "object", "minProperties": 1},
        "selectionAdjustment": {"type": "object", "minProperties": 1},
        "holdoutPolicy": {"type": "object", "minProperties": 1},
        "executorPolicy": {"type": "object", "minProperties": 1},
        "budget": {"type": "object"},
        "stopConditions": {"type": "array", "minItems": 1},
    },
}


STRATEGY_DEFINITION_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant StrategyDefinition V1",
    "type": "object",
    "required": [
        "schemaVersion", "kind", "id", "version", "status", "createdAt", "lineage",
        "factorRefs", "composition", "portfolioValidation", "mlValidation", "rlValidation",
        "costPolicy", "riskAssumptions", "holdoutPolicy", "artifactClosure",
    ],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": "autoquant-strategy-definition"},
        "id": {"type": "string", "pattern": DEFINITION_ID.pattern},
        "version": {"type": "integer", "minimum": 1},
        "status": {"enum": ["draft", "approved", "retired"]},
        "createdAt": {"type": "string", "minLength": 1},
        "lineage": {"type": "object"},
        "factorRefs": {"type": "array", "minItems": 1},
        "composition": {"type": "object", "minProperties": 1},
        "portfolioValidation": {"type": "object", "minProperties": 1},
        "mlValidation": {"type": ["object", "null"]},
        "rlValidation": {"type": ["object", "null"]},
        "costPolicy": {"type": "object", "minProperties": 1},
        "riskAssumptions": {"type": "object", "minProperties": 1},
        "holdoutPolicy": {"type": "object", "minProperties": 1},
        "artifactClosure": {"type": "object", "minProperties": 1},
    },
}
