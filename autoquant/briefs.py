"""Strict delegated research requests and Session-bound Research Briefs."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .horizons import (
    MAX_DIAGNOSTIC_HORIZONS,
    MAX_FORWARD_BARS,
    MIN_DIAGNOSTIC_HORIZONS,
    MIN_FORWARD_BARS,
)
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
ASSET_POSITION_ROLES = {
    "long-only",
    "short-only",
    "two-sided",
    "context-only",
}
PORTFOLIO_POLICY_NUMERIC_FIELDS = {
    "grossLimit",
    "maxAbsWeight",
    "annualizedVolatilityCeiling",
    "baseCostBps",
    "noTradeOneWay",
    "referenceNav",
}
PORTFOLIO_POLICY_INTEGER_FIELDS = {
    "decisionEveryBars",
}
PORTFOLIO_POLICY_FIELDS = {
    *PORTFOLIO_POLICY_NUMERIC_FIELDS,
    *PORTFOLIO_POLICY_INTEGER_FIELDS,
    "assetMaxAbsWeights",
    "decisionAnchor",
}
DECISION_ANCHORS = {"dataset-start", "session-start"}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _strict_keys(
    value: dict[str, Any],
    required: set[str],
    path: Path | str,
    *,
    optional: set[str] | None = None,
) -> list[ValidationIssue]:
    allowed = required | (optional or set())
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - allowed)
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
    issues = _strict_keys(
        value,
        required,
        path,
        optional={
            "portfolioPolicy",
            "benchmarkPolicy",
            "horizonPolicy",
        },
    )
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
    benchmark_policy = value.get("benchmarkPolicy")
    normalized_benchmark_policy: dict[str, Any] | None = None
    if "benchmarkPolicy" in value:
        benchmark_path = f"{path}/benchmarkPolicy"
        if not isinstance(benchmark_policy, dict):
            issues.append(
                _issue(
                    benchmark_path,
                    "schema.type",
                    "benchmarkPolicy must be an object",
                )
            )
        else:
            issues.extend(
                _strict_keys(
                    benchmark_policy,
                    {"kind", "symbol"},
                    benchmark_path,
                )
            )
            benchmark_kind = benchmark_policy.get("kind")
            benchmark_symbol = benchmark_policy.get("symbol")
            if benchmark_kind not in {"cash", "asset"}:
                issues.append(
                    _issue(
                        f"{benchmark_path}/kind",
                        "request.benchmark-kind",
                        "Benchmark kind must be cash or asset",
                    )
                )
            elif benchmark_kind == "cash":
                if benchmark_symbol is not None:
                    issues.append(
                        _issue(
                            f"{benchmark_path}/symbol",
                            "request.cash-benchmark-symbol",
                            "Cash benchmark symbol must be null",
                        )
                    )
                else:
                    normalized_benchmark_policy = {
                        "kind": "cash",
                        "symbol": None,
                    }
            elif (
                not isinstance(benchmark_symbol, str)
                or not benchmark_symbol.strip()
            ):
                issues.append(
                    _issue(
                        f"{benchmark_path}/symbol",
                        "request.asset-benchmark-symbol",
                        "Asset benchmark symbol must be non-empty",
                    )
                )
            else:
                normalized_benchmark_policy = {
                    "kind": "asset",
                    "symbol": benchmark_symbol.strip(),
                }
    policy = value.get("portfolioPolicy")
    normalized_policy: dict[str, Any] | None = None
    if policy is not None:
        if not isinstance(policy, dict):
            issues.append(
                _issue(
                    f"{path}/portfolioPolicy",
                    "schema.type",
                    "portfolioPolicy must be an object or null",
                )
            )
        else:
            issues.extend(
                _strict_keys(
                    policy,
                    PORTFOLIO_POLICY_FIELDS,
                    f"{path}/portfolioPolicy",
                )
            )
            numeric: dict[str, float] = {}
            for key in sorted(PORTFOLIO_POLICY_NUMERIC_FIELDS):
                item = policy.get(key)
                if (
                    not isinstance(item, (int, float))
                    or isinstance(item, bool)
                    or not math.isfinite(float(item))
                ):
                    issues.append(
                        _issue(
                            f"{path}/portfolioPolicy/{key}",
                            "request.portfolio-policy-number",
                            f"{key} must be a finite number",
                        )
                    )
                else:
                    numeric[key] = float(item)
            raw_asset_caps = policy.get("assetMaxAbsWeights")
            asset_caps: dict[str, float] | None = None
            if not isinstance(raw_asset_caps, dict):
                issues.append(
                    _issue(
                        f"{path}/portfolioPolicy/assetMaxAbsWeights",
                        "request.asset-cap-map",
                        "assetMaxAbsWeights must be an object",
                    )
                )
            else:
                asset_caps = {}
                if len(raw_asset_caps) > 256:
                    issues.append(
                        _issue(
                            f"{path}/portfolioPolicy/assetMaxAbsWeights",
                            "request.asset-cap-count",
                            "assetMaxAbsWeights may contain at most 256 assets",
                        )
                    )
                for symbol, item in raw_asset_caps.items():
                    cap_path = (
                        f"{path}/portfolioPolicy/"
                        f"assetMaxAbsWeights/{symbol}"
                    )
                    if not isinstance(symbol, str) or not symbol.strip():
                        issues.append(
                            _issue(
                                cap_path,
                                "request.asset-cap-symbol",
                                "Asset cap symbols must be non-empty strings",
                            )
                        )
                    elif (
                        not isinstance(item, (int, float))
                        or isinstance(item, bool)
                        or not math.isfinite(float(item))
                    ):
                        issues.append(
                            _issue(
                                cap_path,
                                "request.asset-cap-number",
                                "Asset caps must be finite numbers",
                            )
                        )
                    else:
                        normalized_symbol = symbol.strip()
                        if normalized_symbol in asset_caps:
                            issues.append(
                                _issue(
                                    cap_path,
                                    "request.duplicate-asset-cap",
                                    "Asset cap symbols must be unique after "
                                    "whitespace normalization",
                                )
                            )
                        else:
                            asset_caps[normalized_symbol] = float(item)
            decision_every_bars = policy.get("decisionEveryBars")
            valid_decision_every_bars = (
                isinstance(decision_every_bars, int)
                and not isinstance(decision_every_bars, bool)
                and 1 <= decision_every_bars <= 252
            )
            if not valid_decision_every_bars:
                issues.append(
                    _issue(
                        f"{path}/portfolioPolicy/decisionEveryBars",
                        "request.decision-cadence",
                        "decisionEveryBars must be an integer from 1 to 252",
                    )
                )
            decision_anchor = policy.get("decisionAnchor")
            valid_decision_anchor = (
                isinstance(decision_anchor, str)
                and decision_anchor in DECISION_ANCHORS
            )
            if not valid_decision_anchor:
                issues.append(
                    _issue(
                        f"{path}/portfolioPolicy/decisionAnchor",
                        "request.decision-anchor",
                        "decisionAnchor must be dataset-start or session-start",
                    )
                )
            if (
                len(numeric) == len(PORTFOLIO_POLICY_NUMERIC_FIELDS)
                and asset_caps is not None
                and valid_decision_every_bars
                and valid_decision_anchor
            ):
                bounds = (
                    ("grossLimit", 0.0, 2.0, False),
                    ("maxAbsWeight", 0.0, 2.0, False),
                    (
                        "annualizedVolatilityCeiling",
                        0.0,
                        1.0,
                        False,
                    ),
                    ("baseCostBps", 0.0, 1000.0, True),
                    ("noTradeOneWay", 0.0, 1.0, True),
                    ("referenceNav", 0.0, 1e12, False),
                )
                for key, lower, upper, inclusive_lower in bounds:
                    item = numeric[key]
                    lower_ok = (
                        item >= lower if inclusive_lower else item > lower
                    )
                    if not lower_ok or item > upper:
                        issues.append(
                            _issue(
                                f"{path}/portfolioPolicy/{key}",
                                "request.portfolio-policy-bound",
                                f"{key} is outside its supported bound",
                            )
                        )
                gross = numeric["grossLimit"]
                cap = numeric["maxAbsWeight"]
                direction = value.get("direction")
                raw_assets = value.get("assets")
                explicit_roles = (
                    [item.get("positionRole") for item in raw_assets]
                    if isinstance(raw_assets, list)
                    and raw_assets
                    and all(isinstance(item, dict) for item in raw_assets)
                    and all("positionRole" in item for item in raw_assets)
                    else []
                )
                has_long = any(
                    role in {"long-only", "two-sided"}
                    for role in explicit_roles
                )
                has_short = any(
                    role in {"short-only", "two-sided"}
                    for role in explicit_roles
                )
                maximum_cap = (
                    gross / 2.0
                    if (
                        has_long
                        and has_short
                        or (
                            not explicit_roles
                            and direction
                            in {
                                "long-short",
                                "relative-value",
                                "research-only",
                            }
                        )
                    )
                    else gross
                )
                if cap > maximum_cap:
                    issues.append(
                        _issue(
                            f"{path}/portfolioPolicy/maxAbsWeight",
                            "request.portfolio-policy-cap",
                            "maxAbsWeight exceeds the permitted directional "
                            "side budget",
                        )
                    )
                normalized_policy = {
                    **numeric,
                    "decisionEveryBars": decision_every_bars,
                    "decisionAnchor": decision_anchor,
                    "assetMaxAbsWeights": {
                        symbol: asset_caps[symbol]
                        for symbol in sorted(asset_caps)
                    },
                }
    horizon_policy = value.get("horizonPolicy")
    normalized_horizon_policy: dict[str, Any] | None = None
    if horizon_policy is not None:
        horizon_path = f"{path}/horizonPolicy"
        if not isinstance(horizon_policy, dict):
            issues.append(
                _issue(
                    horizon_path,
                    "schema.type",
                    "horizonPolicy must be an object or null",
                )
            )
        else:
            issues.extend(
                _strict_keys(
                    horizon_policy,
                    {"primaryForwardBars", "diagnosticForwardBars"},
                    horizon_path,
                )
            )
            primary = horizon_policy.get("primaryForwardBars")
            diagnostics = horizon_policy.get("diagnosticForwardBars")
            if (
                not isinstance(primary, int)
                or isinstance(primary, bool)
                or not MIN_FORWARD_BARS
                <= primary
                <= MAX_FORWARD_BARS
            ):
                issues.append(
                    _issue(
                        f"{horizon_path}/primaryForwardBars",
                        "request.horizon-primary",
                        "primaryForwardBars must be a supported positive "
                        "integer",
                    )
                )
            if (
                not isinstance(diagnostics, list)
                or not MIN_DIAGNOSTIC_HORIZONS
                <= len(diagnostics)
                <= MAX_DIAGNOSTIC_HORIZONS
            ):
                issues.append(
                    _issue(
                        f"{horizon_path}/diagnosticForwardBars",
                        "request.horizon-diagnostics",
                        "diagnosticForwardBars must contain one to five bars",
                    )
                )
            elif any(
                not isinstance(item, int)
                or isinstance(item, bool)
                or not MIN_FORWARD_BARS
                <= item
                <= MAX_FORWARD_BARS
                for item in diagnostics
            ):
                issues.append(
                    _issue(
                        f"{horizon_path}/diagnosticForwardBars",
                        "request.horizon-diagnostic",
                        "Every diagnostic forward bar must be a supported "
                        "positive integer",
                    )
                )
            elif diagnostics != sorted(set(diagnostics)):
                issues.append(
                    _issue(
                        f"{horizon_path}/diagnosticForwardBars",
                        "request.horizon-order",
                        "Diagnostic forward bars must be sorted and unique",
                    )
                )
            elif isinstance(primary, int) and primary not in diagnostics:
                issues.append(
                    _issue(
                        f"{horizon_path}/primaryForwardBars",
                        "request.horizon-primary-missing",
                        "Primary forward bars must appear in diagnostics",
                    )
                )
            else:
                normalized_horizon_policy = {
                    "primaryForwardBars": primary,
                    "diagnosticForwardBars": list(diagnostics),
                }
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
    declared_position_roles = 0
    position_capable_roles = 0
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
                optional={"positionRole"},
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
        if "positionRole" in asset:
            declared_position_roles += 1
            role = asset.get("positionRole")
            if role not in ASSET_POSITION_ROLES:
                issues.append(
                    _issue(
                        f"{asset_path}/positionRole",
                        "request.asset-position-role",
                        "positionRole must be long-only, short-only, "
                        "two-sided, or context-only",
                    )
                )
            elif role != "context-only":
                position_capable_roles += 1
        asset_identities.append(
            (asset.get("assetClass"), asset.get("symbol"), venue)
        )
    if len(asset_identities) != len(set(asset_identities)):
        issues.append(
            _issue(f"{path}/assets", "request.duplicate-asset", "Assets must be unique")
        )
    if declared_position_roles not in {0, len(assets)}:
        issues.append(
            _issue(
                f"{path}/assets",
                "request.partial-asset-position-roles",
                "If one requested asset declares positionRole, every "
                "requested asset must declare one",
            )
        )
    if declared_position_roles == len(assets) and position_capable_roles == 0:
        issues.append(
            _issue(
                f"{path}/assets",
                "request.no-position-capable-asset",
                "An explicit role contract requires at least one "
                "position-capable asset",
            )
        )
    if declared_position_roles == len(assets):
        valid_roles = {
            asset.get("positionRole")
            for asset in assets
            if isinstance(asset, dict)
        }
        has_long_role = bool(
            valid_roles & {"long-only", "two-sided"}
        )
        has_short_role = bool(
            valid_roles & {"short-only", "two-sided"}
        )
        direction = value.get("direction")
        if direction == "long" and not has_long_role:
            issues.append(
                _issue(
                    f"{path}/assets",
                    "request.direction-role-conflict",
                    "A long request requires at least one long-capable asset",
                )
            )
        if direction == "short" and not has_short_role:
            issues.append(
                _issue(
                    f"{path}/assets",
                    "request.direction-role-conflict",
                    "A short request requires at least one short-capable asset",
                )
            )
        if (
            direction in {"long-short", "relative-value"}
            and not (has_long_role and has_short_role)
        ):
            issues.append(
                _issue(
                    f"{path}/assets",
                    "request.direction-role-conflict",
                    "A two-sided request requires both long-capable and "
                    "short-capable assets",
                )
            )
    if normalized_policy is not None:
        requested_symbols = {
            identity[1]
            for identity in asset_identities
            if isinstance(identity[1], str)
        }
        requested_roles = {
            asset.get("symbol"): asset.get("positionRole")
            for asset in assets
            if isinstance(asset, dict)
            and isinstance(asset.get("symbol"), str)
        }
        global_cap = normalized_policy["maxAbsWeight"]
        for symbol, asset_cap in normalized_policy[
            "assetMaxAbsWeights"
        ].items():
            cap_path = (
                f"{path}/portfolioPolicy/assetMaxAbsWeights/{symbol}"
            )
            if symbol not in requested_symbols:
                issues.append(
                    _issue(
                        cap_path,
                        "request.asset-cap-unrequested",
                        "Per-asset caps may name requested assets only",
                    )
                )
            elif requested_roles.get(symbol) == "context-only":
                issues.append(
                    _issue(
                        cap_path,
                        "request.asset-cap-context-only",
                        "A context-only asset cannot receive a position cap",
                    )
                )
            if not 0 < asset_cap <= global_cap:
                issues.append(
                    _issue(
                        cap_path,
                        "request.asset-cap-bound",
                        "Per-asset caps must be positive and no greater "
                        "than maxAbsWeight",
                    )
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
                **(
                    {"positionRole": asset["positionRole"]}
                    if "positionRole" in asset
                    else {}
                ),
            }
            for asset in value["assets"]
        ],
        "direction": value["direction"],
        **(
            {"benchmarkPolicy": normalized_benchmark_policy}
            if "benchmarkPolicy" in value
            else {}
        ),
        **(
            {"portfolioPolicy": normalized_policy}
            if "portfolioPolicy" in value
            else {}
        ),
        **(
            {"horizonPolicy": normalized_horizon_policy}
            if "horizonPolicy" in value
            else {}
        ),
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
            **(
                {
                    "dependencyHash": session_manifest["locks"][
                        "dependencyHash"
                    ]
                }
                if "dependencyHash" in session_manifest["locks"]
                else {}
            ),
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
                    "positionRole": {
                        "enum": sorted(ASSET_POSITION_ROLES),
                    },
                },
            },
        },
        "direction": {"enum": sorted(REQUEST_DIRECTIONS)},
        "benchmarkPolicy": {
            "oneOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["kind", "symbol"],
                    "properties": {
                        "kind": {"const": "cash"},
                        "symbol": {"type": "null"},
                    },
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["kind", "symbol"],
                    "properties": {
                        "kind": {"const": "asset"},
                        "symbol": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            ]
        },
        "portfolioPolicy": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": sorted(PORTFOLIO_POLICY_FIELDS),
                    "properties": {
                        "grossLimit": {
                            "type": "number",
                            "exclusiveMinimum": 0,
                            "maximum": 2,
                        },
                        "maxAbsWeight": {
                            "type": "number",
                            "exclusiveMinimum": 0,
                            "maximum": 2,
                        },
                        "assetMaxAbsWeights": {
                            "type": "object",
                            "maxProperties": 256,
                            "additionalProperties": {
                                "type": "number",
                                "exclusiveMinimum": 0,
                                "maximum": 2,
                            },
                        },
                        "annualizedVolatilityCeiling": {
                            "type": "number",
                            "exclusiveMinimum": 0,
                            "maximum": 1,
                        },
                        "baseCostBps": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1000,
                        },
                        "noTradeOneWay": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "referenceNav": {
                            "type": "number",
                            "exclusiveMinimum": 0,
                            "maximum": 1e12,
                        },
                        "decisionEveryBars": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 252,
                        },
                        "decisionAnchor": {
                            "enum": sorted(DECISION_ANCHORS),
                        },
                    },
                },
            ]
        },
        "horizonPolicy": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "primaryForwardBars",
                        "diagnosticForwardBars",
                    ],
                    "properties": {
                        "primaryForwardBars": {
                            "type": "integer",
                            "minimum": MIN_FORWARD_BARS,
                            "maximum": MAX_FORWARD_BARS,
                        },
                        "diagnosticForwardBars": {
                            "type": "array",
                            "minItems": MIN_DIAGNOSTIC_HORIZONS,
                            "maxItems": MAX_DIAGNOSTIC_HORIZONS,
                            "uniqueItems": True,
                            "items": {
                                "type": "integer",
                                "minimum": MIN_FORWARD_BARS,
                                "maximum": MAX_FORWARD_BARS,
                            },
                        },
                    },
                },
            ]
        },
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
