"""Request-bound reported-position snapshot authority."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .studies import hash_json
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ValidationIssue,
)


POSITION_SNAPSHOT = "strategies/position-snapshot.json"
POSITION_SNAPSHOT_KIND = "autoquant-position-snapshot"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def build_position_snapshot(request: dict[str, Any]) -> dict[str, Any]:
    source = request.get("positionSnapshot")
    if not isinstance(source, dict):
        raise AutoQuantValidationError(
            [
                _issue(
                    "request/positionSnapshot",
                    "request.position-snapshot-required",
                    "Book Risk requires one normalized positionSnapshot",
                )
            ]
        )
    request_hash = hash_json(request)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": POSITION_SNAPSHOT_KIND,
        "id": f"position-{request_hash[:16]}",
        "source": {
            "requestHash": request_hash,
            "requestSystem": request["source"]["system"],
            "requestArtifactPath": request["source"]["artifactPath"],
            "requestArtifactRevision": request["source"][
                "artifactRevision"
            ],
        },
        "snapshotKind": source["kind"],
        "asOf": source["asOf"],
        "baseCurrency": source["baseCurrency"],
        "weights": dict(source["weights"]),
        "cashWeight": float(source["cashWeight"]),
        "authority": {
            "positionTruth": "external-reported-not-authenticated",
            "tradingAuthority": "none",
        },
    }


def validate_position_snapshot(
    value: dict[str, Any],
    path: Path | str = POSITION_SNAPSHOT,
) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "source",
        "snapshotKind",
        "asOf",
        "baseCurrency",
        "weights",
        "cashWeight",
        "authority",
    }
    issues = [
        *(
            _issue(f"{path}/{key}", "schema.missing", f"Missing field '{key}'")
            for key in sorted(required - value.keys())
        ),
        *(
            _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
            for key in sorted(value.keys() - required)
        ),
    ]
    if (
        value.get("schemaVersion") != SCHEMA_VERSION
        or value.get("kind") != POSITION_SNAPSHOT_KIND
    ):
        issues.append(
            _issue(path, "position-snapshot.schema", "Invalid position snapshot")
        )
    identifier = value.get("id")
    if (
        not isinstance(identifier, str)
        or not re.fullmatch(r"position-[0-9a-f]{16}", identifier)
    ):
        issues.append(
            _issue(f"{path}/id", "position-snapshot.id", "Invalid snapshot id")
        )
    source = value.get("source")
    if not isinstance(source, dict) or set(source) != {
        "requestHash",
        "requestSystem",
        "requestArtifactPath",
        "requestArtifactRevision",
    }:
        issues.append(
            _issue(
                f"{path}/source",
                "position-snapshot.source",
                "Invalid request provenance",
            )
        )
    elif (
        not isinstance(source.get("requestHash"), str)
        or not SHA256.fullmatch(source["requestHash"])
        or source.get("requestSystem") not in {"openalice", "external", "local"}
        or (
            source.get("requestArtifactPath") is None
            and source.get("requestArtifactRevision") is not None
        )
        or (
            source.get("requestArtifactPath") is not None
            and source.get("requestArtifactRevision") is None
        )
    ):
        issues.append(
            _issue(
                f"{path}/source",
                "position-snapshot.source",
                "Invalid request provenance values",
            )
        )
    weights = value.get("weights")
    cash = value.get("cashWeight")
    if (
        not isinstance(weights, dict)
        or not weights
        or len(weights) > 256
        or not all(
            isinstance(symbol, str)
            and symbol == symbol.strip()
            and bool(symbol)
            and isinstance(weight, (int, float))
            and not isinstance(weight, bool)
            and math.isfinite(float(weight))
            and 1e-12 < abs(float(weight)) <= 2
            for symbol, weight in weights.items()
        )
        or not isinstance(cash, (int, float))
        or isinstance(cash, bool)
        or not math.isfinite(float(cash))
        or not -3 <= float(cash) <= 3
        or sum(abs(float(weight)) for weight in weights.values())
        > 4 + 1e-12
        or not math.isclose(
            sum(float(weight) for weight in weights.values()) + float(cash),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
    ):
        issues.append(
            _issue(
                path,
                "position-snapshot.weights",
                "Invalid funded position weights",
            )
        )
    if value.get("snapshotKind") not in {
        "reported-weights",
        "hypothetical-weights",
    }:
        issues.append(
            _issue(
                f"{path}/snapshotKind",
                "position-snapshot.snapshot-kind",
                "Invalid snapshot kind",
            )
        )
    as_of = value.get("asOf")
    try:
        parsed_as_of = (
            datetime.fromisoformat(as_of.replace("Z", "+00:00"))
            if isinstance(as_of, str)
            else None
        )
    except ValueError:
        parsed_as_of = None
    base_currency = value.get("baseCurrency")
    if (
        parsed_as_of is None
        or parsed_as_of.tzinfo is None
        or not isinstance(base_currency, str)
        or not base_currency
        or base_currency != base_currency.strip().upper()
        or len(base_currency) > 16
    ):
        issues.append(
            _issue(path, "position-snapshot.identity", "Invalid snapshot identity")
        )
    if value.get("authority") != {
        "positionTruth": "external-reported-not-authenticated",
        "tradingAuthority": "none",
    }:
        issues.append(
            _issue(
                f"{path}/authority",
                "position-snapshot.authority",
                "Position snapshot authority differs from the fixed boundary",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return value


def load_position_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "position-snapshot.json",
                    f"Cannot read position snapshot: {error}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "position-snapshot.type", "Must be an object")]
        )
    return validate_position_snapshot(value, path)
