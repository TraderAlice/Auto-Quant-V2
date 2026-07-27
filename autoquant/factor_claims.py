"""Strict request-bound Factor research-claim contracts."""

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


FACTOR_CLAIM = "strategies/factor-claim.json"
FACTOR_CLAIM_KIND = "autoquant-factor-claim"
FACTOR_CLAIMS = {
    "novel-factor",
    "known-style-validation",
}
KNOWN_FACTOR_STYLES = {
    "momentum_20",
    "reversal_5",
    "realized_volatility_20",
    "relative_volume_20",
}
DEFAULT_FACTOR_POLICY = {
    "claim": "novel-factor",
    "knownStyle": None,
}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def normalize_factor_policy(value: Any) -> dict[str, Any]:
    """Return one strict caller policy or the novel-factor default."""

    if value is None:
        return dict(DEFAULT_FACTOR_POLICY)
    if not isinstance(value, dict) or set(value) != {
        "claim",
        "knownStyle",
    }:
        raise AutoQuantValidationError(
            [
                _issue(
                    "factorPolicy",
                    "factor-claim.policy",
                    "factorPolicy must contain exactly claim and knownStyle",
                )
            ]
        )
    claim = value.get("claim")
    known_style = value.get("knownStyle")
    if claim not in FACTOR_CLAIMS:
        raise AutoQuantValidationError(
            [
                _issue(
                    "factorPolicy/claim",
                    "factor-claim.claim",
                    "Unknown Factor research claim",
                )
            ]
        )
    if (
        claim == "novel-factor"
        and known_style is not None
    ) or (
        claim == "known-style-validation"
        and known_style not in KNOWN_FACTOR_STYLES
    ):
        raise AutoQuantValidationError(
            [
                _issue(
                    "factorPolicy/knownStyle",
                    "factor-claim.known-style",
                    "knownStyle must be null for novel-factor and one supported "
                    "style for known-style-validation",
                )
            ]
        )
    return {
        "claim": claim,
        "knownStyle": known_style,
    }


def build_factor_claim(request: dict[str, Any] | None) -> dict[str, Any]:
    """Derive one content-addressed Factor claim from request authority."""

    supplied = (
        request.get("factorPolicy")
        if isinstance(request, dict)
        else None
    )
    policy = normalize_factor_policy(supplied)
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": FACTOR_CLAIM_KIND,
        "source": {
            "kind": (
                "research-request"
                if request is not None
                else "template-default"
            ),
            "requestHash": (
                hash_json(request) if request is not None else None
            ),
            "factorPolicy": (
                "caller-supplied"
                if supplied is not None
                else "reference-default"
            ),
        },
        **policy,
        "selectionAuthority": "validation-only",
        "testRole": "visible-audit",
        "authority": "quantitative-decision-support",
        "tradingAuthority": "none",
    }
    return {
        **payload,
        "id": f"factor-claim-{hash_json(payload)[:16]}",
    }


def validate_factor_claim(
    value: Any,
    path: Path | str = FACTOR_CLAIM,
) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "source",
        "claim",
        "knownStyle",
        "selectionAuthority",
        "testRole",
        "authority",
        "tradingAuthority",
    }
    issues: list[ValidationIssue] = []
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "factor-claim.type", "Factor claim must be an object")]
        )
    for key in sorted(required - value.keys()):
        issues.append(
            _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        )
    for key in sorted(value.keys() - required):
        issues.append(
            _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        )
    source = value.get("source")
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected V1"))
    if value.get("kind") != FACTOR_CLAIM_KIND:
        issues.append(_issue(f"{path}/kind", "factor-claim.kind", "Invalid Factor claim kind"))
    if (
        not isinstance(source, dict)
        or set(source) != {"kind", "requestHash", "factorPolicy"}
        or source.get("kind") not in {"research-request", "template-default"}
        or source.get("factorPolicy")
        not in {"caller-supplied", "reference-default"}
        or (
            source.get("kind") == "research-request"
            and (
                not isinstance(source.get("requestHash"), str)
                or len(source["requestHash"]) != 64
            )
        )
        or (
            source.get("kind") == "template-default"
            and source.get("requestHash") is not None
        )
    ):
        issues.append(
            _issue(f"{path}/source", "factor-claim.source", "Invalid Factor claim source")
        )
    try:
        policy = normalize_factor_policy(
            {
                "claim": value.get("claim"),
                "knownStyle": value.get("knownStyle"),
            }
        )
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
        policy = {
            "claim": value.get("claim"),
            "knownStyle": value.get("knownStyle"),
        }
    if (
        value.get("selectionAuthority") != "validation-only"
        or value.get("testRole") != "visible-audit"
        or value.get("authority") != "quantitative-decision-support"
        or value.get("tradingAuthority") != "none"
    ):
        issues.append(
            _issue(
                path,
                "factor-claim.authority",
                "Factor claim cannot alter selection or trading authority",
            )
        )
    payload = {key: value.get(key) for key in required - {"id"}}
    expected_id = f"factor-claim-{hash_json(payload)[:16]}"
    if value.get("id") != expected_id:
        issues.append(
            _issue(
                f"{path}/id",
                "factor-claim.derived-id",
                "Factor claim id is not derived from its complete content",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return {
        **payload,
        **policy,
        "id": expected_id,
    }


def load_factor_claim(path: str | Path) -> dict[str, Any]:
    claim_path = Path(path).expanduser().absolute()
    try:
        value = json.loads(claim_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [
                _issue(
                    claim_path,
                    "factor-claim.missing",
                    f"Missing Factor claim: {claim_path}",
                )
            ]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    claim_path,
                    "factor-claim.json",
                    f"Invalid JSON at line {error.lineno}, column "
                    f"{error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(claim_path, "factor-claim.type", "Factor claim must be an object")]
        )
    return validate_factor_claim(value, claim_path)


FACTOR_CLAIM_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant request-bound Factor research claim",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "id",
        "source",
        "claim",
        "knownStyle",
        "selectionAuthority",
        "testRole",
        "authority",
        "tradingAuthority",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": FACTOR_CLAIM_KIND},
        "id": {
            "type": "string",
            "pattern": "^factor-claim-[0-9a-f]{16}$",
        },
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "requestHash", "factorPolicy"],
            "properties": {
                "kind": {
                    "enum": ["research-request", "template-default"],
                },
                "requestHash": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    ]
                },
                "factorPolicy": {
                    "enum": ["caller-supplied", "reference-default"],
                },
            },
        },
        "claim": {"enum": sorted(FACTOR_CLAIMS)},
        "knownStyle": {
            "anyOf": [
                {"type": "null"},
                {"enum": sorted(KNOWN_FACTOR_STYLES)},
            ]
        },
        "selectionAuthority": {"const": "validation-only"},
        "testRole": {"const": "visible-audit"},
        "authority": {"const": "quantitative-decision-support"},
        "tradingAuthority": {"const": "none"},
    },
    "allOf": [
        {
            "if": {
                "properties": {
                    "claim": {"const": "novel-factor"},
                }
            },
            "then": {
                "properties": {
                    "knownStyle": {"type": "null"},
                }
            },
        },
        {
            "if": {
                "properties": {
                    "claim": {"const": "known-style-validation"},
                }
            },
            "then": {
                "properties": {
                    "knownStyle": {"enum": sorted(KNOWN_FACTOR_STYLES)},
                }
            },
        },
    ],
}
