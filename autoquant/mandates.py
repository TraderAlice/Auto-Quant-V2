"""Strict request-bound portfolio mandate contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .studies import hash_json
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ValidationIssue,
)


PORTFOLIO_MANDATE = "strategies/portfolio-mandate.json"
PORTFOLIO_MANDATE_KIND = "autoquant-portfolio-mandate"
PORTFOLIO_MANDATE_AUTHORITY = "quantitative-decision-support"
PORTFOLIO_MANDATE_DIRECTIONS = {
    "long",
    "short",
    "long-short",
    "relative-value",
    "research-only",
}
PORTFOLIO_FAMILIES = {
    "long": "long-cash",
    "short": "short-cash",
    "long-short": "dollar-neutral",
    "relative-value": "dollar-neutral",
    "research-only": "dollar-neutral",
}
PORTFOLIO_NET_RULES = {
    "long": "long-only",
    "short": "short-only",
    "long-short": "zero",
    "relative-value": "zero",
    "research-only": "zero",
}
PORTFOLIO_BENCHMARKS = {
    "long": "equal-weight-long-tradable",
    "short": "equal-weight-short-tradable",
    "long-short": "cash",
    "relative-value": "cash",
    "research-only": "equal-weight-long-research-universe",
}
PORTFOLIO_RISK_POLICY = {
    "method": "trailing-covariance-volatility-ceiling-v1",
    "annualizedVolatilityCeiling": 0.15,
    "covarianceWindow": 60,
    "minimumObservations": 20,
    "annualizationPeriods": 252,
    "scaleUp": False,
}
DEFAULT_PORTFOLIO_POLICY = {
    "grossLimit": 1.0,
    "maxAbsWeight": 0.30,
    "annualizedVolatilityCeiling": 0.15,
    "baseCostBps": 10.0,
    "noTradeOneWay": 0.05,
    "referenceNav": 1_000_000.0,
}
IMPLEMENTATION_COST_MODEL = "linear-traded-notional-v1"
IMPLEMENTATION_CAPACITY_MODEL = "trailing-dollar-volume-participation-v1"
MIN_ANNUALIZATION_PERIODS = 1
MAX_ANNUALIZATION_PERIODS = 365 * 24 * 60
SHA256 = "^[0-9a-f]{64}$"


def _valid_annualization_periods(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and MIN_ANNUALIZATION_PERIODS
        <= value
        <= MAX_ANNUALIZATION_PERIODS
    )


def _valid_portfolio_policy(
    value: dict[str, Any],
    direction: str,
) -> bool:
    required = set(DEFAULT_PORTFOLIO_POLICY)
    if set(value) != required:
        return False
    if any(
        not isinstance(value[key], (int, float))
        or isinstance(value[key], bool)
        for key in required
    ):
        return False
    gross = float(value["grossLimit"])
    cap = float(value["maxAbsWeight"])
    ceiling = float(value["annualizedVolatilityCeiling"])
    cost = float(value["baseCostBps"])
    no_trade = float(value["noTradeOneWay"])
    nav = float(value["referenceNav"])
    maximum_cap = (
        gross / 2.0
        if direction
        in {"long-short", "relative-value", "research-only"}
        else gross
    )
    return (
        0 < gross <= 2
        and 0 < cap <= maximum_cap
        and 0 < ceiling <= 1
        and 0 <= cost <= 1000
        and 0 <= no_trade <= 1
        and 0 < nav <= 1e12
    )


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


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _symbol_list(
    value: Any,
    path: Path | str,
    *,
    allow_empty: bool,
) -> tuple[list[str], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or not all(isinstance(item, str) and item for item in value)
    ):
        issues.append(
            _issue(
                path,
                "mandate.assets",
                "Must be a list of unique non-empty asset symbols",
            )
        )
        return [], issues
    if len(value) != len(set(value)):
        issues.append(
            _issue(path, "mandate.duplicate-asset", "Asset symbols must be unique")
        )
    return list(value), issues


def _canonical_payload(
    *,
    source_kind: str,
    request_hash: str | None,
    direction: str,
    research_universe: list[str],
    tradable_assets: list[str],
    annualization_periods: int,
    portfolio_policy: dict[str, Any],
    policy_source: str,
) -> dict[str, Any]:
    context_assets = [
        asset for asset in research_universe if asset not in set(tradable_assets)
    ]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": PORTFOLIO_MANDATE_KIND,
        "source": {
            "kind": source_kind,
            "requestHash": request_hash,
            "direction": direction,
            "portfolioPolicy": policy_source,
        },
        "researchUniverse": list(research_universe),
        "tradableAssets": list(tradable_assets),
        "contextAssets": context_assets,
        "construction": {
            "family": PORTFOLIO_FAMILIES[direction],
            "grossLimit": portfolio_policy["grossLimit"],
            "netRule": PORTFOLIO_NET_RULES[direction],
            "maxAbsWeight": portfolio_policy["maxAbsWeight"],
            "cashAllowed": True,
            "shortAllowed": direction
            in {"short", "long-short", "relative-value", "research-only"},
            "benchmark": PORTFOLIO_BENCHMARKS[direction],
            "riskPolicy": {
                **PORTFOLIO_RISK_POLICY,
                "annualizedVolatilityCeiling": portfolio_policy[
                    "annualizedVolatilityCeiling"
                ],
                "annualizationPeriods": annualization_periods,
            },
        },
        "implementationPolicy": {
            "baseCostBps": portfolio_policy["baseCostBps"],
            "noTradeOneWay": portfolio_policy["noTradeOneWay"],
            "referenceNav": portfolio_policy["referenceNav"],
            "costModel": IMPLEMENTATION_COST_MODEL,
            "capacityModel": IMPLEMENTATION_CAPACITY_MODEL,
        },
        "authority": PORTFOLIO_MANDATE_AUTHORITY,
        "tradingAuthority": "none",
    }


def build_portfolio_mandate(
    request: dict[str, Any] | None,
    research_universe: list[str],
    *,
    annualization_periods: int = 252,
) -> dict[str, Any]:
    """Derive one fixed mandate from a normalized request or template default."""

    if not research_universe or len(research_universe) != len(set(research_universe)):
        raise ValueError("research_universe must contain unique assets")
    if not _valid_annualization_periods(annualization_periods):
        raise ValueError("unsupported annualization_periods")
    if request is None:
        policy = dict(DEFAULT_PORTFOLIO_POLICY)
        payload = _canonical_payload(
            source_kind="template-default",
            request_hash=None,
            direction="research-only",
            research_universe=research_universe,
            tradable_assets=research_universe,
            annualization_periods=annualization_periods,
            portfolio_policy=policy,
            policy_source="reference-default",
        )
    else:
        direction = request.get("direction")
        if direction not in PORTFOLIO_MANDATE_DIRECTIONS:
            raise ValueError("request has an invalid portfolio direction")
        requested = [item["symbol"] for item in request["assets"]]
        missing = sorted(set(requested) - set(research_universe))
        if missing:
            raise ValueError(
                "requested assets are outside the research universe: "
                + ", ".join(missing)
            )
        supplied_policy = request.get("portfolioPolicy")
        policy = (
            dict(DEFAULT_PORTFOLIO_POLICY)
            if supplied_policy is None
            else dict(supplied_policy)
        )
        if not _valid_portfolio_policy(policy, direction):
            raise ValueError("request has an invalid portfolio policy")
        payload = _canonical_payload(
            source_kind="research-request",
            request_hash=hash_json(request),
            direction=direction,
            research_universe=research_universe,
            tradable_assets=(
                research_universe if direction == "research-only" else requested
            ),
            annualization_periods=annualization_periods,
            portfolio_policy=policy,
            policy_source=(
                "reference-default"
                if supplied_policy is None
                else "caller-supplied"
            ),
        )
    return {
        **payload,
        "id": f"mandate-{hash_json(payload)[:16]}",
    }


def validate_portfolio_mandate(
    value: dict[str, Any],
    path: Path | str = PORTFOLIO_MANDATE,
) -> dict[str, Any]:
    """Validate one mandate and return its canonical representation."""

    required = {
        "schemaVersion",
        "kind",
        "id",
        "source",
        "researchUniverse",
        "tradableAssets",
        "contextAssets",
        "construction",
        "implementationPolicy",
        "authority",
        "tradingAuthority",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected V1"))
    if value.get("kind") != PORTFOLIO_MANDATE_KIND:
        issues.append(
            _issue(
                f"{path}/kind",
                "mandate.kind",
                f"Expected {PORTFOLIO_MANDATE_KIND}",
            )
        )
    if value.get("authority") != PORTFOLIO_MANDATE_AUTHORITY:
        issues.append(
            _issue(f"{path}/authority", "mandate.authority", "Invalid authority")
        )
    if value.get("tradingAuthority") != "none":
        issues.append(
            _issue(
                f"{path}/tradingAuthority",
                "mandate.trading-authority",
                "Portfolio Mandate cannot grant trading authority",
            )
        )

    source = value.get("source")
    direction: Any = None
    source_kind: Any = None
    request_hash: Any = None
    policy_source: Any = None
    if not isinstance(source, dict):
        issues.append(_issue(f"{path}/source", "schema.type", "Source must be an object"))
    else:
        issues.extend(
            _strict_keys(
                source,
                {
                    "kind",
                    "requestHash",
                    "direction",
                    "portfolioPolicy",
                },
                f"{path}/source",
            )
        )
        source_kind = source.get("kind")
        request_hash = source.get("requestHash")
        direction = source.get("direction")
        policy_source = source.get("portfolioPolicy")
        if source_kind not in {"research-request", "template-default"}:
            issues.append(
                _issue(
                    f"{path}/source/kind",
                    "mandate.source-kind",
                    "Invalid mandate source kind",
                )
            )
        if direction not in PORTFOLIO_MANDATE_DIRECTIONS:
            issues.append(
                _issue(
                    f"{path}/source/direction",
                    "mandate.direction",
                    "Invalid mandate direction",
                )
            )
        if policy_source not in {"caller-supplied", "reference-default"}:
            issues.append(
                _issue(
                    f"{path}/source/portfolioPolicy",
                    "mandate.policy-source",
                    "Invalid Portfolio policy source",
                )
            )
        if source_kind == "research-request" and not _valid_hash(request_hash):
            issues.append(
                _issue(
                    f"{path}/source/requestHash",
                    "mandate.request-hash",
                    "Request-derived mandate requires a SHA-256 request hash",
                )
            )
        if source_kind == "template-default" and (
            request_hash is not None
            or direction != "research-only"
            or policy_source != "reference-default"
        ):
            issues.append(
                _issue(
                    f"{path}/source",
                    "mandate.template-default",
                    "Template default must be request-free research-only",
                )
            )

    research, research_issues = _symbol_list(
        value.get("researchUniverse"),
        f"{path}/researchUniverse",
        allow_empty=False,
    )
    tradable, tradable_issues = _symbol_list(
        value.get("tradableAssets"),
        f"{path}/tradableAssets",
        allow_empty=False,
    )
    context, context_issues = _symbol_list(
        value.get("contextAssets"),
        f"{path}/contextAssets",
        allow_empty=True,
    )
    issues.extend(research_issues)
    issues.extend(tradable_issues)
    issues.extend(context_issues)
    if not set(tradable).issubset(research):
        issues.append(
            _issue(
                f"{path}/tradableAssets",
                "mandate.tradable-universe",
                "Tradable assets must be a subset of the research universe",
            )
        )
    expected_context = [asset for asset in research if asset not in set(tradable)]
    if context != expected_context:
        issues.append(
            _issue(
                f"{path}/contextAssets",
                "mandate.context-assets",
                "Context assets must exactly complement tradable assets",
            )
        )

    construction = value.get("construction")
    implementation = value.get("implementationPolicy")
    normalized_policy: dict[str, Any] | None = None
    if not isinstance(implementation, dict):
        issues.append(
            _issue(
                f"{path}/implementationPolicy",
                "schema.type",
                "Implementation policy must be an object",
            )
        )
    else:
        issues.extend(
            _strict_keys(
                implementation,
                {
                    "baseCostBps",
                    "noTradeOneWay",
                    "referenceNav",
                    "costModel",
                    "capacityModel",
                },
                f"{path}/implementationPolicy",
            )
        )
    if not isinstance(construction, dict):
        issues.append(
            _issue(
                f"{path}/construction",
                "schema.type",
                "Construction must be an object",
            )
        )
    else:
        issues.extend(
            _strict_keys(
                construction,
                {
                    "family",
                    "grossLimit",
                    "netRule",
                    "maxAbsWeight",
                    "cashAllowed",
                    "shortAllowed",
                    "benchmark",
                    "riskPolicy",
                },
                f"{path}/construction",
            )
        )
        if direction in PORTFOLIO_MANDATE_DIRECTIONS:
            risk_policy = construction.get("riskPolicy")
            annualization_periods = (
                risk_policy.get("annualizationPeriods")
                if isinstance(risk_policy, dict)
                else None
            )
            if not _valid_annualization_periods(annualization_periods):
                issues.append(
                    _issue(
                        f"{path}/construction/riskPolicy/annualizationPeriods",
                        "mandate.annualization",
                        "Annualization periods must match a supported market clock",
                    )
                )
                annualization_periods = 252
            if isinstance(implementation, dict):
                normalized_policy = {
                    "grossLimit": construction.get("grossLimit"),
                    "maxAbsWeight": construction.get("maxAbsWeight"),
                    "annualizedVolatilityCeiling": (
                        risk_policy.get("annualizedVolatilityCeiling")
                        if isinstance(risk_policy, dict)
                        else None
                    ),
                    "baseCostBps": implementation.get("baseCostBps"),
                    "noTradeOneWay": implementation.get("noTradeOneWay"),
                    "referenceNav": implementation.get("referenceNav"),
                }
                if not _valid_portfolio_policy(
                    normalized_policy,
                    direction,
                ):
                    issues.append(
                        _issue(
                            path,
                            "mandate.portfolio-policy",
                            "Portfolio policy contains unsupported values",
                        )
                    )
            expected = _canonical_payload(
                source_kind=(
                    source_kind
                    if source_kind in {"research-request", "template-default"}
                    else "research-request"
                ),
                request_hash=(
                    request_hash
                    if isinstance(request_hash, str)
                    else None
                ),
                direction=direction,
                research_universe=research,
                tradable_assets=tradable,
                annualization_periods=annualization_periods,
                portfolio_policy=(
                    normalized_policy
                    if normalized_policy is not None
                    else DEFAULT_PORTFOLIO_POLICY
                ),
                policy_source=(
                    policy_source
                    if policy_source
                    in {"caller-supplied", "reference-default"}
                    else "reference-default"
                ),
            )
            if (
                construction != expected["construction"]
                or implementation != expected["implementationPolicy"]
            ):
                issues.append(
                    _issue(
                        path,
                        "mandate.construction",
                        "Portfolio policy differs from the fixed request contract",
                    )
                )
        if direction == "research-only" and tradable != research:
            issues.append(
                _issue(
                    f"{path}/tradableAssets",
                    "mandate.research-universe",
                    "Research-only mandate must use the complete research universe",
                )
            )

    payload = {
        key: value.get(key)
        for key in (
            "schemaVersion",
            "kind",
            "source",
            "researchUniverse",
            "tradableAssets",
            "contextAssets",
            "construction",
            "implementationPolicy",
            "authority",
            "tradingAuthority",
        )
    }
    expected_id = f"mandate-{hash_json(payload)[:16]}"
    if value.get("id") != expected_id:
        issues.append(
            _issue(
                f"{path}/id",
                "mandate.derived-id",
                "Mandate id is not derived from its complete content",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return {**payload, "id": expected_id}


def load_portfolio_mandate(path: str | Path) -> dict[str, Any]:
    mandate_path = Path(path).expanduser().absolute()
    try:
        value = json.loads(mandate_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [
                _issue(
                    mandate_path,
                    "mandate.missing",
                    f"Missing Portfolio Mandate: {mandate_path}",
                )
            ]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    mandate_path,
                    "mandate.json",
                    f"Invalid JSON at line {error.lineno}, column "
                    f"{error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(mandate_path, "mandate.type", "Mandate must be an object")]
        )
    return validate_portfolio_mandate(value, mandate_path)


PORTFOLIO_MANDATE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant request-bound Portfolio Mandate",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "id",
        "source",
        "researchUniverse",
        "tradableAssets",
        "contextAssets",
        "construction",
        "implementationPolicy",
        "authority",
        "tradingAuthority",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": PORTFOLIO_MANDATE_KIND},
        "id": {"type": "string", "pattern": "^mandate-[0-9a-f]{16}$"},
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "kind",
                "requestHash",
                "direction",
                "portfolioPolicy",
            ],
            "properties": {
                "kind": {"enum": ["research-request", "template-default"]},
                "requestHash": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "pattern": SHA256},
                    ]
                },
                "direction": {"enum": sorted(PORTFOLIO_MANDATE_DIRECTIONS)},
                "portfolioPolicy": {
                    "enum": ["caller-supplied", "reference-default"]
                },
            },
        },
        "researchUniverse": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "tradableAssets": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "contextAssets": {
            "type": "array",
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "construction": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "family",
                "grossLimit",
                "netRule",
                "maxAbsWeight",
                "cashAllowed",
                "shortAllowed",
                "benchmark",
                "riskPolicy",
            ],
            "properties": {
                "family": {
                    "enum": ["long-cash", "short-cash", "dollar-neutral"]
                },
                "grossLimit": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 2,
                },
                "netRule": {"enum": ["long-only", "short-only", "zero"]},
                "maxAbsWeight": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 2,
                },
                "cashAllowed": {"const": True},
                "shortAllowed": {"type": "boolean"},
                "benchmark": {
                    "enum": [
                        "cash",
                        "equal-weight-long-research-universe",
                        "equal-weight-long-tradable",
                        "equal-weight-short-tradable",
                    ]
                },
                "riskPolicy": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "method",
                        "annualizedVolatilityCeiling",
                        "covarianceWindow",
                        "minimumObservations",
                        "annualizationPeriods",
                        "scaleUp",
                    ],
                    "properties": {
                        "method": {
                            "const": "trailing-covariance-volatility-ceiling-v1"
                        },
                        "annualizedVolatilityCeiling": {
                            "type": "number",
                            "exclusiveMinimum": 0,
                            "maximum": 1,
                        },
                        "covarianceWindow": {"const": 60},
                        "minimumObservations": {"const": 20},
                        "annualizationPeriods": {
                            "type": "integer",
                            "minimum": MIN_ANNUALIZATION_PERIODS,
                            "maximum": MAX_ANNUALIZATION_PERIODS,
                        },
                        "scaleUp": {"const": False},
                    },
                },
            },
        },
        "implementationPolicy": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "baseCostBps",
                "noTradeOneWay",
                "referenceNav",
                "costModel",
                "capacityModel",
            ],
            "properties": {
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
                "costModel": {"const": IMPLEMENTATION_COST_MODEL},
                "capacityModel": {
                    "const": IMPLEMENTATION_CAPACITY_MODEL
                },
            },
        },
        "authority": {"const": PORTFOLIO_MANDATE_AUTHORITY},
        "tradingAuthority": {"const": "none"},
    },
}
