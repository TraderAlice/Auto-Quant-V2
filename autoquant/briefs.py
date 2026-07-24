"""Strict delegated research requests and Session-bound Research Briefs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .studies import hash_json
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
)


RESEARCH_REQUEST = "request.json"
RESEARCH_BRIEF = "brief.json"
REQUEST_KIND = "autoquant-research-request"
BRIEF_KIND = "autoquant-research-brief"
REQUEST_DIRECTIONS = {
    "long",
    "short",
    "long-short",
    "relative-value",
    "research-only",
}
SOURCE_SYSTEMS = {"openalice", "external", "local"}
ASSET_CLASSES = {"equity", "fund", "future", "forex", "crypto", "index", "other"}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _strict_keys(
    value: dict[str, Any],
    required: set[str],
    path: Path | str,
) -> list[ValidationIssue]:
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - required)
    )
    return issues


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
                    f"Invalid JSON at line {error.lineno}, column "
                    f"{error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.type", f"{label} must be a JSON object")]
        )
    return value


def _non_empty(value: Any, path: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.strip():
        return [_issue(path, "schema.string", "Must be a non-empty string")]
    return []


def _string_list(
    value: Any,
    path: str,
    *,
    allow_empty: bool,
) -> list[ValidationIssue]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        qualifier = "non-empty " if not allow_empty else ""
        return [
            _issue(
                path,
                "schema.array",
                f"Must be a {qualifier}array of non-empty strings",
            )
        ]
    return []


def validate_research_request(
    value: dict[str, Any],
    path: Path | str = "research-request",
) -> dict[str, Any]:
    """Validate and return one canonical caller-supplied request object."""

    required = {
        "schemaVersion",
        "kind",
        "title",
        "question",
        "decisionContext",
        "assets",
        "direction",
        "horizon",
        "hypotheses",
        "constraints",
        "deliverables",
        "source",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected V1"))
    if value.get("kind") != REQUEST_KIND:
        issues.append(_issue(f"{path}/kind", "request.kind", f"Expected {REQUEST_KIND}"))
    for key in ("title", "question", "decisionContext", "horizon"):
        issues.extend(_non_empty(value.get(key), f"{path}/{key}"))
    if value.get("direction") not in REQUEST_DIRECTIONS:
        issues.append(
            _issue(
                f"{path}/direction",
                "schema.choice",
                "Invalid requested direction",
            )
        )
    for key, allow_empty in (
        ("hypotheses", True),
        ("constraints", True),
        ("deliverables", False),
    ):
        issues.extend(
            _string_list(value.get(key), f"{path}/{key}", allow_empty=allow_empty)
        )

    assets = value.get("assets")
    if not isinstance(assets, list) or not assets:
        issues.append(
            _issue(
                f"{path}/assets",
                "schema.array",
                "Assets must be a non-empty array",
            )
        )
        assets = []
    asset_identities: list[tuple[Any, Any, Any]] = []
    for index, asset in enumerate(assets):
        asset_path = f"{path}/assets/{index}"
        if not isinstance(asset, dict):
            issues.append(_issue(asset_path, "schema.type", "Asset must be an object"))
            continue
        issues.extend(
            _strict_keys(
                asset,
                {"symbol", "assetClass", "venue"},
                asset_path,
            )
        )
        issues.extend(_non_empty(asset.get("symbol"), f"{asset_path}/symbol"))
        if asset.get("assetClass") not in ASSET_CLASSES:
            issues.append(
                _issue(
                    f"{asset_path}/assetClass",
                    "schema.choice",
                    "Invalid asset class",
                )
            )
        venue = asset.get("venue")
        if venue is not None:
            issues.extend(_non_empty(venue, f"{asset_path}/venue"))
        asset_identities.append(
            (asset.get("assetClass"), asset.get("symbol"), venue)
        )
    if len(asset_identities) != len(set(asset_identities)):
        issues.append(
            _issue(f"{path}/assets", "request.duplicate-asset", "Assets must be unique")
        )

    source = value.get("source")
    if not isinstance(source, dict):
        issues.append(_issue(f"{path}/source", "schema.type", "Source must be an object"))
    else:
        issues.extend(
            _strict_keys(
                source,
                {
                    "system",
                    "workspaceId",
                    "sessionId",
                    "artifactPath",
                    "artifactRevision",
                },
                f"{path}/source",
            )
        )
        if source.get("system") not in SOURCE_SYSTEMS:
            issues.append(
                _issue(
                    f"{path}/source/system",
                    "schema.choice",
                    "Invalid source system",
                )
            )
        for key in ("workspaceId", "sessionId", "artifactPath", "artifactRevision"):
            item = source.get(key)
            if item is not None:
                issues.extend(_non_empty(item, f"{path}/source/{key}"))
        has_artifact = source.get("artifactPath") is not None
        has_revision = source.get("artifactRevision") is not None
        if has_artifact != has_revision:
            issues.append(
                _issue(
                    f"{path}/source",
                    "request.source-revision",
                    "artifactPath and artifactRevision must be provided together",
                )
            )
    if issues:
        raise AutoQuantValidationError(issues)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": REQUEST_KIND,
        "title": value["title"].strip(),
        "question": value["question"].strip(),
        "decisionContext": value["decisionContext"].strip(),
        "assets": [
            {
                "symbol": asset["symbol"].strip(),
                "assetClass": asset["assetClass"],
                "venue": (
                    asset["venue"].strip()
                    if isinstance(asset["venue"], str)
                    else None
                ),
            }
            for asset in value["assets"]
        ],
        "direction": value["direction"],
        "horizon": value["horizon"].strip(),
        "hypotheses": [item.strip() for item in value["hypotheses"]],
        "constraints": [item.strip() for item in value["constraints"]],
        "deliverables": [item.strip() for item in value["deliverables"]],
        "source": {
            "system": value["source"]["system"],
            **{
                key: (
                    value["source"][key].strip()
                    if isinstance(value["source"][key], str)
                    else None
                )
                for key in (
                    "workspaceId",
                    "sessionId",
                    "artifactPath",
                    "artifactRevision",
                )
            },
        },
    }


def load_research_request(path: str | Path) -> dict[str, Any]:
    request_path = Path(path).expanduser().absolute()
    return validate_research_request(
        _read_json(request_path, "research request"),
        request_path,
    )


def build_research_brief(
    request: dict[str, Any],
    project: ProjectContext,
    session_manifest: dict[str, Any],
    baseline_result: dict[str, Any],
    *,
    created_at: str,
) -> dict[str, Any]:
    """Derive one exact brief from normalized request and fixed Session inputs."""

    request_hash = hash_json(request)
    identity = {
        "requestHash": request_hash,
        "projectId": project.manifest.id,
        "sessionId": session_manifest["id"],
        "studyId": session_manifest["studyId"],
        "baselineRunId": session_manifest["baseline"]["runId"],
        "locks": {
            key: value
            for key, value in session_manifest["locks"].items()
            if key != "fixedHashes"
        },
        "createdAt": created_at,
    }
    brief_id = f"brief-{hash_json(identity)[:16]}"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": BRIEF_KIND,
        "id": brief_id,
        "authority": "derived-research-handoff",
        "claimKind": "research-prioritization",
        "createdAt": created_at,
        "requestHash": request_hash,
        "project": {
            "id": project.manifest.id,
            "name": project.manifest.name,
        },
        "sessionId": session_manifest["id"],
        "study": {
            "id": baseline_result["study"]["id"],
            "name": baseline_result["study"]["name"],
            "hash": session_manifest["locks"]["studyHash"],
            "programHash": session_manifest["locks"]["programHash"],
            "judgeHash": session_manifest["locks"]["judgeHash"],
            "datasetHash": session_manifest["locks"]["datasetHash"],
            "objective": baseline_result["objective"],
            "dataset": baseline_result["dataset"],
        },
        "baseline": session_manifest["baseline"],
        "harness": session_manifest["locks"]["harness"],
        "authorityBoundary": {
            "requestContext": "caller-supplied-content-locked",
            "fixedEvaluation": "locked-study-and-judge",
            "candidateEdits": "study-editable-closure-only",
            "verdict": "locked-judge-only",
            "trading": "none",
            "openAliceProvenance": "authenticated-on-openalice-inbox-publication",
        },
    }


def validate_session_brief(
    project: ProjectContext,
    session_root: Path,
    session_manifest: dict[str, Any],
    baseline_result: dict[str, Any],
) -> dict[str, Any] | None:
    """Verify optional request/brief bytes against the mutable Session pointer."""

    request_path = session_root / RESEARCH_REQUEST
    brief_path = session_root / RESEARCH_BRIEF
    pointer = session_manifest.get("brief")
    if pointer is None:
        if (
            request_path.exists()
            or request_path.is_symlink()
            or brief_path.exists()
            or brief_path.is_symlink()
        ):
            raise AutoQuantValidationError(
                [
                    _issue(
                        session_root,
                        "brief.untracked",
                        "Session has untracked request or brief files",
                    )
                ]
            )
        return None
    issues: list[ValidationIssue] = []
    if not isinstance(pointer, dict):
        raise AutoQuantValidationError(
            [_issue(f"{session_root}/brief", "schema.type", "Brief pointer must be an object")]
        )
    issues.extend(
        _strict_keys(
            pointer,
            {"id", "requestHash", "briefHash"},
            f"{session_root}/session.json/brief",
        )
    )
    for key in ("requestHash", "briefHash"):
        if (
            not isinstance(pointer.get(key), str)
            or len(pointer.get(key, "")) != 64
            or any(character not in "0123456789abcdef" for character in pointer.get(key, ""))
        ):
            issues.append(
                _issue(
                    f"{session_root}/session.json/brief/{key}",
                    "schema.hash",
                    f"Invalid {key}",
                )
            )
    request = validate_research_request(
        _read_json(request_path, "research request"),
        request_path,
    )
    brief = _read_json(brief_path, "research brief")
    brief_required = {
        "schemaVersion",
        "kind",
        "id",
        "authority",
        "claimKind",
        "createdAt",
        "requestHash",
        "project",
        "sessionId",
        "study",
        "baseline",
        "harness",
        "authorityBoundary",
    }
    issues.extend(_strict_keys(brief, brief_required, brief_path))
    if brief.get("schemaVersion") != SCHEMA_VERSION or brief.get("kind") != BRIEF_KIND:
        issues.append(_issue(brief_path, "brief.schema", "Invalid Research Brief schema"))
    if not isinstance(brief.get("createdAt"), str) or not brief["createdAt"]:
        issues.append(_issue(f"{brief_path}/createdAt", "schema.string", "Invalid createdAt"))
    if issues:
        raise AutoQuantValidationError(issues)
    expected = build_research_brief(
        request,
        project,
        session_manifest,
        baseline_result,
        created_at=brief["createdAt"],
    )
    request_hash = hash_json(request)
    brief_hash = hash_json(brief)
    if request_hash != pointer.get("requestHash"):
        issues.append(_issue(request_path, "brief.request-hash", "Request hash mismatch"))
    if brief != expected:
        issues.append(
            _issue(brief_path, "brief.derived", "Research Brief differs from fixed inputs")
        )
    if brief.get("id") != pointer.get("id"):
        issues.append(_issue(brief_path, "brief.id", "Research Brief id mismatch"))
    if brief_hash != pointer.get("briefHash"):
        issues.append(_issue(brief_path, "brief.hash", "Research Brief hash mismatch"))
    if issues:
        raise AutoQuantValidationError(issues)
    return {"request": request, "brief": brief}


RESEARCH_REQUEST_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant delegated research request",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "title",
        "question",
        "decisionContext",
        "assets",
        "direction",
        "horizon",
        "hypotheses",
        "constraints",
        "deliverables",
        "source",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": REQUEST_KIND},
        "title": {"type": "string", "minLength": 1},
        "question": {"type": "string", "minLength": 1},
        "decisionContext": {"type": "string", "minLength": 1},
        "assets": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["symbol", "assetClass", "venue"],
                "properties": {
                    "symbol": {"type": "string", "minLength": 1},
                    "assetClass": {"enum": sorted(ASSET_CLASSES)},
                    "venue": {
                        "anyOf": [
                            {"type": "null"},
                            {"type": "string", "minLength": 1},
                        ]
                    },
                },
            },
        },
        "direction": {"enum": sorted(REQUEST_DIRECTIONS)},
        "horizon": {"type": "string", "minLength": 1},
        "hypotheses": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "constraints": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "deliverables": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "system",
                "workspaceId",
                "sessionId",
                "artifactPath",
                "artifactRevision",
            ],
            "properties": {
                "system": {"enum": sorted(SOURCE_SYSTEMS)},
                "workspaceId": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "minLength": 1},
                    ]
                },
                "sessionId": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "minLength": 1},
                    ]
                },
                "artifactPath": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "minLength": 1},
                    ]
                },
                "artifactRevision": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "minLength": 1},
                    ]
                },
            },
        },
    },
}
