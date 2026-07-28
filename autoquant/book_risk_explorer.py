"""Strict bounded read model for immutable reported-book risk Runs."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from .position_snapshots import validate_position_snapshot
from .runs import load_run
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
)


BOOK_RISK_DIAGNOSTICS_KIND = "autoquant-book-risk-diagnostics"
DEFAULT_BOOK_RISK_POINTS = 80
MIN_BOOK_RISK_POINTS = 20
MAX_BOOK_RISK_POINTS = 400
ARTIFACTS = {
    "book-risk-report": "book-risk-report.json",
    "book-risk-contributions": "book-risk-contributions.csv",
    "book-risk-reductions": "book-risk-reductions.csv",
    "book-risk-correlations": "book-risk-correlations.csv",
    "book-risk-path": "book-risk-path.csv",
}
CONTRIBUTION_COLUMNS = (
    "asset",
    "weight",
    "marginalVariance",
    "componentVariance",
    "signedRiskShare",
    "absoluteRiskShare",
)
REDUCTION_COLUMNS = (
    "rank",
    "asset",
    "startingWeight",
    "weightReduction",
    "resultingWeight",
    "resultingCashWeight",
    "annualizedVolatility",
    "volatilityReduction",
    "volatilityReductionPerWeight",
    "componentRiskHhi",
    "effectiveRiskBets",
)
CORRELATION_COLUMNS = ("leftAsset", "rightAsset", "correlation")
PATH_COLUMNS = (
    "timestamp",
    "observations",
    "annualizedVolatility",
    "componentRiskHhi",
    "effectiveRiskBets",
    "firstPrincipalComponentVarianceShare",
)


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _fail(path: Path | str, code: str, message: str) -> None:
    raise AutoQuantValidationError([_issue(path, code, message)])


def _strict(
    value: Any,
    keys: set[str],
    path: Path | str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        _fail(path, "book-risk.schema", "Object fields differ from the fixed contract")
    return value


def _finite(value: Any, path: Path | str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        _fail(path, "book-risk.number", "Expected one finite number")
    return float(value)


def _csv_finite(value: str, path: Path | str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        _fail(path, "book-risk.number", "Expected one finite CSV number")
    if not math.isfinite(result):
        _fail(path, "book-risk.number", "Expected one finite CSV number")
    return result


def _close(left: float, right: float, path: Path | str) -> None:
    if not math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-12):
        _fail(path, "book-risk.reconcile", "Derived evidence does not reconcile")


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(path, "book-risk.json", f"Cannot read JSON evidence: {error}")
    if not isinstance(value, dict):
        _fail(path, "book-risk.type", "JSON evidence must be an object")
    return value


def _csv_rows(
    path: Path,
    columns: tuple[str, ...],
) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != columns:
                _fail(
                    path,
                    "book-risk.csv-columns",
                    "CSV columns differ from the fixed contract",
                )
            rows = list(reader)
    except OSError as error:
        _fail(path, "book-risk.csv", f"Cannot read CSV evidence: {error}")
    if not rows or any(
        None in row or any(value is None for value in row.values())
        for row in rows
    ):
        _fail(path, "book-risk.csv-width", "CSV evidence is empty or malformed")
    return rows


def _artifact_paths(run) -> dict[str, Path]:
    declared = {
        item["kind"]: item["path"]
        for item in run.result["artifacts"]
    }
    if set(declared) != set(ARTIFACTS):
        _fail(
            run.root_dir,
            "book-risk.artifacts",
            "Book Risk Run artifacts differ from the fixed inventory",
        )
    result: dict[str, Path] = {}
    for kind, filename in ARTIFACTS.items():
        relative = declared[kind]
        if relative != f"artifacts/{filename}":
            _fail(
                run.root_dir / relative,
                "book-risk.artifact-path",
                "Book Risk artifact path differs from the fixed contract",
            )
        result[kind] = run.root_dir / relative
    return result


def _sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(rows) <= limit:
        return rows
    indices = {
        round(index * (len(rows) - 1) / (limit - 1))
        for index in range(limit)
    }
    return [rows[index] for index in sorted(indices)]


def load_book_risk_diagnostics(
    project: ProjectContext,
    run_id: str,
    *,
    point_limit: int = DEFAULT_BOOK_RISK_POINTS,
) -> dict[str, Any]:
    """Verify and project one immutable Book Risk Run."""

    if (
        not isinstance(point_limit, int)
        or isinstance(point_limit, bool)
        or not MIN_BOOK_RISK_POINTS <= point_limit <= MAX_BOOK_RISK_POINTS
    ):
        _fail(
            point_limit,
            "book-risk.point-limit",
            f"point_limit must be {MIN_BOOK_RISK_POINTS}..{MAX_BOOK_RISK_POINTS}",
        )
    run = load_run(project, run_id)
    if run.result["objective"]["metric"] != "current_component_risk_hhi":
        _fail(
            run.root_dir,
            "book-risk.run-kind",
            "Run is not a fixed Book Risk evaluation",
        )
    paths = _artifact_paths(run)
    report = _strict(
        _read_object(paths["book-risk-report"]),
        {
            "schemaVersion",
            "kind",
            "requestHash",
            "positionSnapshot",
            "authority",
            "method",
            "dataset",
            "lookbacks",
            "current",
            "contributions",
            "pairwiseCorrelations",
            "reductions",
            "rollingSummary",
        },
        paths["book-risk-report"],
    )
    if (
        report["schemaVersion"] != SCHEMA_VERSION
        or report["kind"] != "autoquant-book-risk-report"
    ):
        _fail(
            paths["book-risk-report"],
            "book-risk.report-kind",
            "Invalid Book Risk report identity",
        )
    frozen_snapshot_path = (
        run.root_dir
        / "inputs"
        / "dependency-sources"
        / "strategies"
        / "position-snapshot.json"
    )
    frozen_snapshot = _read_object(frozen_snapshot_path)
    validate_position_snapshot(frozen_snapshot, frozen_snapshot_path)
    if report["positionSnapshot"] != frozen_snapshot:
        _fail(
            paths["book-risk-report"],
            "book-risk.position-snapshot",
            "Report position snapshot differs from the frozen dependency",
        )
    if report["requestHash"] != frozen_snapshot.get("source", {}).get(
        "requestHash"
    ):
        _fail(
            paths["book-risk-report"],
            "book-risk.request-hash",
            "Report request hash differs from the frozen position snapshot",
        )
    authority = {
        "positionTruth": "external-reported-not-authenticated",
        "marketEvidence": "content-locked-closed-ohlcv",
        "tradingAuthority": "none",
        "reductionMeaning": "standardized-historical-sensitivity",
    }
    if report["authority"] != authority:
        _fail(
            paths["book-risk-report"],
            "book-risk.authority",
            "Book Risk authority boundary differs from the fixed contract",
        )
    current = _strict(
        report["current"],
        {
            "observations",
            "annualizedVolatility",
            "annualizedVariance",
            "componentRiskHhi",
            "effectiveRiskBets",
            "firstPrincipalComponentVarianceShare",
            "largestAbsoluteRiskContributorShare",
            "lookbackBars",
            "grossExposure",
            "netExposure",
            "cashWeight",
        },
        f"{paths['book-risk-report']}/current",
    )
    current_numeric = {
        key: _finite(value, f"{paths['book-risk-report']}/current/{key}")
        for key, value in current.items()
    }
    if (
        current_numeric["observations"] < 20
        or current_numeric["annualizedVolatility"] <= 0
        or not 0 < current_numeric["componentRiskHhi"] <= 1
        or current_numeric["effectiveRiskBets"] < 1
        or not 0
        <= current_numeric["firstPrincipalComponentVarianceShare"]
        <= 1
        or not 0
        <= current_numeric["largestAbsoluteRiskContributorShare"]
        <= 1
    ):
        _fail(
            f"{paths['book-risk-report']}/current",
            "book-risk.current",
            "Current Book Risk evidence is outside valid bounds",
        )
    _close(
        current_numeric["annualizedVolatility"] ** 2,
        current_numeric["annualizedVariance"],
        f"{paths['book-risk-report']}/current/annualizedVariance",
    )
    _close(
        1.0 / current_numeric["componentRiskHhi"],
        current_numeric["effectiveRiskBets"],
        f"{paths['book-risk-report']}/current/effectiveRiskBets",
    )
    metric_map = {
        "current_component_risk_hhi": "componentRiskHhi",
        "current_effective_risk_bets": "effectiveRiskBets",
        "current_annualized_volatility": "annualizedVolatility",
        "current_first_pc_variance_share": (
            "firstPrincipalComponentVarianceShare"
        ),
        "largest_risk_contributor_share": (
            "largestAbsoluteRiskContributorShare"
        ),
        "primary_lookback_bars": "lookbackBars",
    }
    for metric, field in metric_map.items():
        _close(
            _finite(run.result["metrics"].get(metric), f"metrics/{metric}"),
            current_numeric[field],
            f"metrics/{metric}",
        )
    method = _strict(
        report["method"],
        {
            "schemaVersion",
            "kind",
            "lookbackBars",
            "primaryLookbackBars",
            "minimumObservations",
            "reductionWeight",
            "rollingStepBars",
        },
        f"{paths['book-risk-report']}/method",
    )
    if (
        method["schemaVersion"] != SCHEMA_VERSION
        or method["kind"] != "autoquant-book-risk-scenarios"
        or not isinstance(method["lookbackBars"], list)
        or not method["lookbackBars"]
        or not all(
            isinstance(item, int)
            and not isinstance(item, bool)
            and 20 <= item <= 2520
            for item in method["lookbackBars"]
        )
        or method["lookbackBars"] != sorted(set(method["lookbackBars"]))
        or method["primaryLookbackBars"] not in method["lookbackBars"]
        or not isinstance(method["minimumObservations"], int)
        or isinstance(method["minimumObservations"], bool)
        or not isinstance(method["rollingStepBars"], int)
        or isinstance(method["rollingStepBars"], bool)
        or not 20 <= method["minimumObservations"] <= min(method["lookbackBars"])
        or not 1 <= method["rollingStepBars"] <= 252
        or not 0 < _finite(
            method["reductionWeight"],
            f"{paths['book-risk-report']}/method/reductionWeight",
        ) <= 0.25
    ):
        _fail(
            f"{paths['book-risk-report']}/method",
            "book-risk.method",
            "Book Risk method differs from the bounded contract",
        )
    dataset = _strict(
        report["dataset"],
        {
            "id",
            "version",
            "assetClass",
            "universe",
            "heldAssets",
            "marketDataEnd",
            "annualizationPeriods",
        },
        f"{paths['book-risk-report']}/dataset",
    )
    if (
        not isinstance(dataset["id"], str)
        or not dataset["id"]
        or not isinstance(dataset["version"], str)
        or not dataset["version"]
        or not isinstance(dataset["assetClass"], str)
        or not dataset["assetClass"]
        or not isinstance(dataset["universe"], list)
        or not isinstance(dataset["heldAssets"], list)
        or not all(
            isinstance(item, str) and item
            for item in dataset["universe"] + dataset["heldAssets"]
        )
        or len(dataset["universe"]) != len(set(dataset["universe"]))
        or len(dataset["heldAssets"]) != len(set(dataset["heldAssets"]))
        or dataset["heldAssets"] != list(frozen_snapshot["weights"])
        or not set(dataset["heldAssets"]).issubset(dataset["universe"])
        or not isinstance(dataset["marketDataEnd"], str)
        or not dataset["marketDataEnd"]
        or not isinstance(dataset["annualizationPeriods"], int)
        or isinstance(dataset["annualizationPeriods"], bool)
        or dataset["annualizationPeriods"] <= 0
    ):
        _fail(
            f"{paths['book-risk-report']}/dataset",
            "book-risk.dataset",
            "Book Risk dataset description is invalid",
        )
    raw_lookbacks = report["lookbacks"]
    if (
        not isinstance(raw_lookbacks, list)
        or not raw_lookbacks
        or not all(isinstance(item, dict) for item in raw_lookbacks)
        or [item.get("lookbackBars") for item in raw_lookbacks]
        != method.get("lookbackBars")
    ):
        _fail(
            f"{paths['book-risk-report']}/lookbacks",
            "book-risk.lookbacks",
            "Lookback evidence differs from the declared method",
        )
    lookbacks: list[dict[str, Any]] = []
    lookback_keys = {
        "lookbackBars",
        "observations",
        "annualizedVolatility",
        "annualizedVariance",
        "componentRiskHhi",
        "effectiveRiskBets",
        "firstPrincipalComponentVarianceShare",
        "largestAbsoluteRiskContributorShare",
        "largestAbsoluteRiskContributor",
        "firstReductionAsset",
        "firstReductionVolatilityPerWeight",
    }
    for index, raw in enumerate(raw_lookbacks):
        item = _strict(
            raw,
            lookback_keys,
            f"{paths['book-risk-report']}/lookbacks/{index}",
        )
        parsed = {
            key: (
                item[key]
                if key
                in {
                    "largestAbsoluteRiskContributor",
                    "firstReductionAsset",
                }
                else _finite(
                    item[key],
                    f"{paths['book-risk-report']}/lookbacks/{index}/{key}",
                )
            )
            for key in lookback_keys
        }
        if (
            parsed["observations"] != parsed["lookbackBars"]
            or parsed["annualizedVolatility"] <= 0
            or not 0 < parsed["componentRiskHhi"] <= 1
            or parsed["effectiveRiskBets"] < 1
            or not 0
            <= parsed["firstPrincipalComponentVarianceShare"]
            <= 1
            or not 0
            <= parsed["largestAbsoluteRiskContributorShare"]
            <= 1
            or not isinstance(
                parsed["largestAbsoluteRiskContributor"],
                str,
            )
            or not isinstance(parsed["firstReductionAsset"], str)
        ):
            _fail(
                f"{paths['book-risk-report']}/lookbacks/{index}",
                "book-risk.lookback",
                "Lookback evidence is outside valid bounds",
            )
        _close(
            parsed["annualizedVolatility"] ** 2,
            parsed["annualizedVariance"],
            f"{paths['book-risk-report']}/lookbacks/{index}",
        )
        _close(
            1.0 / parsed["componentRiskHhi"],
            parsed["effectiveRiskBets"],
            f"{paths['book-risk-report']}/lookbacks/{index}",
        )
        lookbacks.append(parsed)
    contribution_rows = _csv_rows(
        paths["book-risk-contributions"],
        CONTRIBUTION_COLUMNS,
    )
    contributions: list[dict[str, Any]] = []
    for index, row in enumerate(contribution_rows):
        parsed = {
            "asset": row["asset"],
            **{
                key: _csv_finite(
                    row[key],
                    f"{paths['book-risk-contributions']}:{index + 2}/{key}",
                )
                for key in CONTRIBUTION_COLUMNS[1:]
            },
        }
        contributions.append(parsed)
    if contributions != report["contributions"]:
        _fail(
            paths["book-risk-contributions"],
            "book-risk.contributions",
            "Contribution CSV differs from the report",
        )
    if len({row["asset"] for row in contributions}) != len(contributions):
        _fail(
            paths["book-risk-contributions"],
            "book-risk.contribution-assets",
            "Contribution assets must be unique",
        )
    _close(
        sum(row["absoluteRiskShare"] for row in contributions),
        1.0,
        paths["book-risk-contributions"],
    )
    _close(
        sum(row["signedRiskShare"] for row in contributions),
        1.0,
        paths["book-risk-contributions"],
    )
    reduction_rows = _csv_rows(
        paths["book-risk-reductions"],
        REDUCTION_COLUMNS,
    )
    reductions: list[dict[str, Any]] = []
    for index, row in enumerate(reduction_rows):
        reductions.append(
            {
                "rank": int(row["rank"]),
                "asset": row["asset"],
                **{
                    key: _csv_finite(
                        row[key],
                        f"{paths['book-risk-reductions']}:{index + 2}/{key}",
                    )
                    for key in REDUCTION_COLUMNS[2:]
                },
            }
        )
    if reductions != report["reductions"]:
        _fail(
            paths["book-risk-reductions"],
            "book-risk.reductions",
            "Reduction CSV differs from the report",
        )
    if (
        [row["rank"] for row in reductions]
        != list(range(1, len(reductions) + 1))
        or [row["asset"] for row in reductions]
        != [row["asset"] for row in contributions]
        and set(row["asset"] for row in reductions)
        != set(row["asset"] for row in contributions)
        or any(
            reductions[index]["volatilityReductionPerWeight"]
            < reductions[index + 1]["volatilityReductionPerWeight"] - 1e-12
            for index in range(len(reductions) - 1)
        )
    ):
        _fail(
            paths["book-risk-reductions"],
            "book-risk.reduction-order",
            "Reduction ranking is invalid",
        )
    correlation_rows = _csv_rows(
        paths["book-risk-correlations"],
        CORRELATION_COLUMNS,
    )
    correlations = [
        {
            "leftAsset": row["leftAsset"],
            "rightAsset": row["rightAsset"],
            "correlation": _csv_finite(
                row["correlation"],
                f"{paths['book-risk-correlations']}:{index + 2}/correlation",
            ),
        }
        for index, row in enumerate(correlation_rows)
    ]
    if (
        correlations != report["pairwiseCorrelations"]
        or len(correlations)
        != len(contributions) * (len(contributions) - 1) // 2
        or any(abs(row["correlation"]) > 1 + 1e-12 for row in correlations)
    ):
        _fail(
            paths["book-risk-correlations"],
            "book-risk.correlations",
            "Correlation evidence is invalid",
        )
    path_rows_raw = _csv_rows(paths["book-risk-path"], PATH_COLUMNS)
    path_rows: list[dict[str, Any]] = []
    previous = ""
    for index, row in enumerate(path_rows_raw):
        timestamp = row["timestamp"]
        if not timestamp or timestamp <= previous:
            _fail(
                f"{paths['book-risk-path']}:{index + 2}/timestamp",
                "book-risk.path-order",
                "Book Risk path timestamps must be ordered and unique",
            )
        previous = timestamp
        path_rows.append(
            {
                "timestamp": timestamp,
                **{
                    key: (
                        int(row[key])
                        if key == "observations"
                        else _csv_finite(
                            row[key],
                            f"{paths['book-risk-path']}:{index + 2}/{key}",
                        )
                    )
                    for key in PATH_COLUMNS[1:]
                },
            }
        )
    rolling = _strict(
        report["rollingSummary"],
        {
            "observations",
            "start",
            "end",
            "minimumEffectiveRiskBets",
            "maximumComponentRiskHhi",
        },
        f"{paths['book-risk-report']}/rollingSummary",
    )
    if (
        rolling["observations"] != len(path_rows)
        or rolling["start"] != path_rows[0]["timestamp"]
        or rolling["end"] != path_rows[-1]["timestamp"]
    ):
        _fail(
            paths["book-risk-path"],
            "book-risk.path-summary",
            "Rolling path summary does not reconcile",
        )
    _close(
        _finite(
            rolling["minimumEffectiveRiskBets"],
            "rollingSummary/minimumEffectiveRiskBets",
        ),
        min(row["effectiveRiskBets"] for row in path_rows),
        paths["book-risk-path"],
    )
    _close(
        _finite(
            rolling["maximumComponentRiskHhi"],
            "rollingSummary/maximumComponentRiskHhi",
        ),
        max(row["componentRiskHhi"] for row in path_rows),
        paths["book-risk-path"],
    )
    held_assets = set(frozen_snapshot["weights"])
    if (
        set(row["asset"] for row in contributions) != held_assets
        or set(row["asset"] for row in reductions) != held_assets
    ):
        _fail(
            paths["book-risk-report"],
            "book-risk.held-assets",
            "Book Risk evidence differs from reported held assets",
        )
    if any(
        row["largestAbsoluteRiskContributor"] not in held_assets
        or row["firstReductionAsset"] not in held_assets
        for row in lookbacks
    ):
        _fail(
            paths["book-risk-report"],
            "book-risk.lookback-assets",
            "Lookback priority evidence names an unreported asset",
        )
    primary_lookback = next(
        (
            row
            for row in lookbacks
            if row["lookbackBars"] == current_numeric["lookbackBars"]
        ),
        None,
    )
    if (
        primary_lookback is None
        or primary_lookback["largestAbsoluteRiskContributor"]
        != contributions[0]["asset"]
        or primary_lookback["firstReductionAsset"]
        != reductions[0]["asset"]
    ):
        _fail(
            paths["book-risk-report"],
            "book-risk.primary-lookback",
            "Primary lookback priority does not reconcile",
        )
    sampled = _sample(path_rows, point_limit)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": BOOK_RISK_DIAGNOSTICS_KIND,
        "run": {
            "id": run.result["id"],
            "status": run.result["status"],
            "harness": run.result["harness"],
            "primaryMetric": run.result["objective"]["metric"],
            "primaryValue": run.result["metrics"][
                run.result["objective"]["metric"]
            ],
        },
        "positionSnapshot": frozen_snapshot,
        "authority": authority,
        "current": current,
        "lookbacks": lookbacks,
        "riskContributions": contributions,
        "reductionPriority": reductions,
        "pairwiseCorrelations": correlations,
        "rollingPath": {
            "totalRows": len(path_rows),
            "sampledRows": len(sampled),
            "points": sampled,
            "summary": rolling,
        },
        "artifacts": {
            kind: {
                "path": f"artifacts/{filename}",
                "immutable": True,
            }
            for kind, filename in ARTIFACTS.items()
        },
    }


BOOK_RISK_DIAGNOSTICS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant Book Risk diagnostics",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "run",
        "positionSnapshot",
        "authority",
        "current",
        "lookbacks",
        "riskContributions",
        "reductionPriority",
        "pairwiseCorrelations",
        "rollingPath",
        "artifacts",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": BOOK_RISK_DIAGNOSTICS_KIND},
        "run": {"type": "object"},
        "positionSnapshot": {"type": "object"},
        "authority": {"type": "object"},
        "current": {"type": "object"},
        "lookbacks": {"type": "array"},
        "riskContributions": {"type": "array"},
        "reductionPriority": {"type": "array"},
        "pairwiseCorrelations": {"type": "array"},
        "rollingPath": {"type": "object"},
        "artifacts": {"type": "object"},
    },
}
