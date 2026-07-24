"""Bounded, verified decision diagnostics for immutable Portfolio Runs."""

from __future__ import annotations

import csv
import json
import math
from bisect import bisect_right
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .mandates import (
    PORTFOLIO_MANDATE,
    validate_portfolio_mandate,
)
from .runs import RunContext, load_run
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


PORTFOLIO_DIAGNOSTICS_KIND = "autoquant-portfolio-diagnostics"
DEFAULT_PORTFOLIO_POINTS = 180
MIN_PORTFOLIO_POINTS = 40
MAX_PORTFOLIO_POINTS = 400
MAX_ARTIFACT_BYTES = 32 * 1024 * 1024
MAX_DAILY_ROWS = 100_000
MAX_DECISION_ROWS = 1_000_000
MAX_UNIVERSE = 256
MAX_RECENT_TRANSITIONS = 40
EXPECTED_ARTIFACT_KINDS = {
    "portfolio-report",
    "portfolio-daily",
    "portfolio-targets",
    "portfolio-weights",
    "portfolio-decisions",
}
DAILY_NUMERIC_COLUMNS = (
    "gross_return",
    "net_return",
    "benchmark_return",
    "one_way_turnover",
    "traded_notional",
    "cost",
    "gross_exposure",
    "net_exposure",
    "max_abs_weight",
    "concentration_hhi",
    "max_participation",
    "mean_participation",
)
DECISION_REQUIRED_COLUMNS = {
    "factor",
    "percentile_score",
    "prior_signal_state",
    "signal_state",
    "signal_event",
    "conviction",
    "trailing_volatility",
    "risk_strength",
    "allocation_status",
    "prior_target_weight",
    "proposed_target_weight",
    "target_delta",
    "target_action",
    "diagonal_risk_budget_share",
    "timestamp",
    "asset",
    "regime",
    "pretrade_weight",
    "executed_weight",
    "executed_state",
    "trade_weight",
    "execution_action",
    "execution_reason",
    "asset_forward_return",
    "gross_return_contribution",
    "cost_contribution",
    "net_return_contribution",
    "one_way_turnover_contribution",
    "component_variance",
    "variance_contribution_share",
    "portfolio_variance",
    "portfolio_gross_return",
    "portfolio_cost",
    "portfolio_net_return",
    "portfolio_traded_notional",
}
DECISION_OPTIONAL_FLOATS = {
    "factor",
    "percentile_score",
    "trailing_volatility",
}
DECISION_FLOATS = {
    "conviction",
    "risk_strength",
    "prior_target_weight",
    "proposed_target_weight",
    "target_delta",
    "diagonal_risk_budget_share",
    "pretrade_weight",
    "executed_weight",
    "trade_weight",
    "asset_forward_return",
    "gross_return_contribution",
    "cost_contribution",
    "net_return_contribution",
    "one_way_turnover_contribution",
    "component_variance",
    "variance_contribution_share",
    "portfolio_variance",
    "portfolio_gross_return",
    "portfolio_cost",
    "portfolio_net_return",
    "portfolio_traded_notional",
}
RISK_DECISION_COLUMNS = {
    "pre_governor_target_weight",
    "risk_governor_status",
    "risk_estimation_observations",
    "risk_forecast_pre_annualized",
    "risk_forecast_post_annualized",
    "risk_volatility_ceiling_annualized",
    "risk_governor_scale",
}
RISK_DECISION_FLOATS = RISK_DECISION_COLUMNS - {"risk_governor_status"}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _fail(path: Path | str, code: str, message: str) -> None:
    raise AutoQuantValidationError([_issue(path, code, message)])


def _finite(value: Any, path: Path | str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        _fail(path, "portfolio.number", "Expected a finite numeric value")
    if not math.isfinite(number):
        _fail(path, "portfolio.number", "Expected a finite numeric value")
    return number


def _optional_finite(value: Any, path: Path | str) -> float | None:
    if value is None or value == "":
        return None
    return _finite(value, path)


def _session_date(value: Any, path: Path | str) -> str:
    if not isinstance(value, str):
        _fail(path, "portfolio.timestamp", "Timestamp must be an ISO session date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        _fail(path, "portfolio.timestamp", "Timestamp must be an ISO session date")
    if parsed.isoformat() != value:
        _fail(path, "portfolio.timestamp", "Timestamp must be an ISO session date")
    return value


def _artifact_paths(
    run: RunContext,
) -> tuple[dict[str, Path], dict[str, dict[str, str]]]:
    if run.result["status"] != "succeeded":
        _fail(
            run.root_dir,
            "portfolio.run-status",
            "Portfolio diagnostics require a successful immutable Run",
        )
    artifacts = run.result.get("artifacts")
    if not isinstance(artifacts, list):
        _fail(run.root_dir, "portfolio.artifacts", "Run artifacts must be an array")
    paths: dict[str, Path] = {}
    identities: dict[str, dict[str, str]] = {}
    for index, artifact in enumerate(artifacts):
        artifact_path = f"{run.root_dir}/result.json/artifacts/{index}"
        if not isinstance(artifact, dict):
            _fail(artifact_path, "portfolio.artifact", "Artifact must be an object")
        kind = artifact.get("kind")
        relative = artifact.get("path")
        if kind not in EXPECTED_ARTIFACT_KINDS:
            continue
        if kind in paths:
            _fail(
                artifact_path,
                "portfolio.duplicate-artifact",
                f"Portfolio artifact kind must be unique: {kind}",
            )
        if not isinstance(relative, str):
            _fail(
                artifact_path,
                "portfolio.artifact-path",
                "Portfolio artifact path must be a string",
            )
        path = confined_path(run.root_dir, relative, artifact_path)
        if not path.is_file():
            _fail(path, "portfolio.artifact-missing", f"Missing artifact: {kind}")
        size = path.stat().st_size
        if size > MAX_ARTIFACT_BYTES:
            _fail(
                path,
                "portfolio.artifact-size",
                f"Portfolio artifact exceeds {MAX_ARTIFACT_BYTES} bytes",
            )
        content_hash = run.manifest["files"].get(relative)
        if not isinstance(content_hash, str):
            _fail(
                path,
                "portfolio.artifact-identity",
                "Artifact is absent from immutable Run identity",
            )
        paths[kind] = path
        identities[kind] = {
            "path": relative,
            "sha256": content_hash,
        }
    missing = EXPECTED_ARTIFACT_KINDS - paths.keys()
    if missing:
        _fail(
            run.root_dir,
            "portfolio.artifacts",
            "Run does not declare the fixed Portfolio artifact set: "
            + ", ".join(sorted(missing)),
        )
    return paths, identities


def _read_csv(
    path: Path,
    *,
    required: set[str],
    maximum_rows: int,
) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            if (
                fields is None
                or len(fields) != len(set(fields))
                or any(not field for field in fields)
            ):
                _fail(
                    path,
                    "portfolio.csv-header",
                    "CSV must have unique non-empty headers",
                )
            missing = required - set(fields)
            if missing:
                _fail(
                    path,
                    "portfolio.csv-columns",
                    "CSV is missing columns: " + ", ".join(sorted(missing)),
                )
            rows: list[dict[str, str]] = []
            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    _fail(
                        f"{path}:{row_number}",
                        "portfolio.csv-width",
                        "CSV row has more values than headers",
                    )
                if any(value is None for value in row.values()):
                    _fail(
                        f"{path}:{row_number}",
                        "portfolio.csv-width",
                        "CSV row has fewer values than headers",
                    )
                rows.append(row)
                if len(rows) > maximum_rows:
                    _fail(
                        path,
                        "portfolio.row-limit",
                        f"CSV exceeds the {maximum_rows}-row diagnostics limit",
                    )
    except UnicodeDecodeError:
        _fail(path, "portfolio.csv-encoding", "CSV must be UTF-8")
    if not rows:
        _fail(path, "portfolio.csv-empty", "CSV must contain data rows")
    return fields, rows


def _strict_dates(rows: list[dict[str, str]], path: Path) -> list[str]:
    dates = [
        _session_date(row.get("timestamp"), f"{path}:{index}/timestamp")
        for index, row in enumerate(rows, start=2)
    ]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        _fail(
            path,
            "portfolio.timestamp-order",
            "Timestamps must be unique and strictly increasing",
        )
    return dates


@dataclass(frozen=True)
class ParsedDaily:
    dates: list[str]
    rows: list[dict[str, Any]]


def _parse_daily(path: Path) -> ParsedDaily:
    required = {"timestamp", "rebalanced", *DAILY_NUMERIC_COLUMNS}
    fields, raw_rows = _read_csv(
        path,
        required=required,
        maximum_rows=MAX_DAILY_ROWS,
    )
    dates = _strict_dates(raw_rows, path)
    rows: list[dict[str, Any]] = []
    for index, (timestamp, raw) in enumerate(zip(dates, raw_rows), start=2):
        values = {
            key: _finite(raw[key], f"{path}:{index}/{key}")
            for key in DAILY_NUMERIC_COLUMNS
        }
        cash_weight = (
            _finite(raw["cash_weight"], f"{path}:{index}/cash_weight")
            if "cash_weight" in fields
            else 1.0 - values["gross_exposure"]
        )
        if not math.isclose(
            cash_weight,
            1.0 - values["gross_exposure"],
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            _fail(
                f"{path}:{index}/cash_weight",
                "portfolio.cash-reconciliation",
                "Cash weight must equal one minus gross exposure",
            )
        if (
            values["gross_return"] <= -1.0
            or values["net_return"] <= -1.0
            or values["benchmark_return"] <= -1.0
        ):
            _fail(
                f"{path}:{index}",
                "portfolio.return",
                "Daily compounded returns must be greater than -1",
            )
        for key in (
            "one_way_turnover",
            "traded_notional",
            "cost",
            "gross_exposure",
            "max_abs_weight",
            "concentration_hhi",
            "max_participation",
            "mean_participation",
        ):
            if values[key] < 0:
                _fail(
                    f"{path}:{index}/{key}",
                    "portfolio.non-negative",
                    f"{key} must be non-negative",
                )
        if raw["rebalanced"] not in {"True", "False"}:
            _fail(
                f"{path}:{index}/rebalanced",
                "portfolio.boolean",
                "rebalanced must be True or False",
            )
        rows.append(
            {
                "timestamp": timestamp,
                **values,
                "cash_weight": cash_weight,
                "rebalanced": raw["rebalanced"] == "True",
            }
        )
    return ParsedDaily(dates, rows)


def _parse_weight_panel(
    path: Path,
    universe: list[str],
) -> tuple[list[str], dict[str, dict[str, float]]]:
    fields, raw_rows = _read_csv(
        path,
        required={"timestamp", *universe},
        maximum_rows=MAX_DAILY_ROWS + 1,
    )
    if fields != ["timestamp", *universe]:
        _fail(
            path,
            "portfolio.weight-universe",
            "Weight columns must exactly match Study universe order",
        )
    dates = _strict_dates(raw_rows, path)
    panel: dict[str, dict[str, float]] = {}
    for row_number, (timestamp, raw) in enumerate(
        zip(dates, raw_rows),
        start=2,
    ):
        weights = {
            asset: _finite(raw[asset], f"{path}:{row_number}/{asset}")
            for asset in universe
        }
        if any(abs(value) > 1.0 + 1e-12 for value in weights.values()):
            _fail(
                f"{path}:{row_number}",
                "portfolio.weight-bound",
                "Research weight magnitude cannot exceed 1",
            )
        panel[timestamp] = weights
    return dates, panel


def _parse_decisions(
    path: Path,
    daily: ParsedDaily,
    universe: list[str],
    targets: dict[str, dict[str, float]],
    weights: dict[str, dict[str, float]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    fields, raw_rows = _read_csv(
        path,
        required=DECISION_REQUIRED_COLUMNS,
        maximum_rows=MAX_DECISION_ROWS,
    )
    expected = {
        (timestamp, asset)
        for timestamp in daily.dates
        for asset in universe
    }
    decisions: dict[tuple[str, str], dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    mandate_columns = {"tradable", "permitted_direction", "mandate_id"}
    has_mandate_columns = mandate_columns.issubset(fields)
    if mandate_columns & set(fields) and not has_mandate_columns:
        _fail(
            path,
            "portfolio.mandate-columns",
            "Decision ledger must contain the complete mandate column set",
        )
    has_risk_columns = RISK_DECISION_COLUMNS.issubset(fields)
    if RISK_DECISION_COLUMNS & set(fields) and not has_risk_columns:
        _fail(
            path,
            "portfolio.risk-governor-columns",
            "Decision ledger must contain the complete risk-governor column set",
        )
    for row_number, raw in enumerate(raw_rows, start=2):
        row_path = f"{path}:{row_number}"
        timestamp = _session_date(raw["timestamp"], f"{row_path}/timestamp")
        asset = raw["asset"]
        key = (timestamp, asset)
        if key not in expected:
            _fail(
                row_path,
                "portfolio.decision-identity",
                "Decision timestamp/asset is outside the daily Study panel",
            )
        if key in decisions:
            _fail(
                row_path,
                "portfolio.duplicate-decision",
                "Decision timestamp/asset must be unique",
            )
        states: dict[str, int] = {}
        for field in ("prior_signal_state", "signal_state", "executed_state"):
            try:
                state = int(raw[field])
            except ValueError:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.signal-state",
                    "Signal states must be -1, 0, or 1",
                )
            if str(state) != raw[field] or state not in {-1, 0, 1}:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.signal-state",
                    "Signal states must be -1, 0, or 1",
                )
            states[field] = state
        optional = {
            field: _optional_finite(raw[field], f"{row_path}/{field}")
            for field in DECISION_OPTIONAL_FLOATS
        }
        numeric = {
            field: _finite(raw[field], f"{row_path}/{field}")
            for field in DECISION_FLOATS
        }
        risk_numeric = (
            {
                field: _finite(raw[field], f"{row_path}/{field}")
                for field in RISK_DECISION_FLOATS
            }
            if has_risk_columns
            else {
                "pre_governor_target_weight": numeric[
                    "proposed_target_weight"
                ],
                "risk_estimation_observations": 0.0,
                "risk_forecast_pre_annualized": 0.0,
                "risk_forecast_post_annualized": 0.0,
                "risk_volatility_ceiling_annualized": 0.0,
                "risk_governor_scale": 1.0,
            }
        )
        for field in (
            "signal_event",
            "allocation_status",
            "target_action",
            "regime",
            "execution_action",
            "execution_reason",
        ):
            if not raw[field]:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.decision-string",
                    f"{field} must be non-empty",
                )
        if has_risk_columns and not raw["risk_governor_status"]:
            _fail(
                f"{row_path}/risk_governor_status",
                "portfolio.risk-governor-status",
                "Risk-governor status must be non-empty",
            )
        if (
            not 0.0 <= risk_numeric["risk_governor_scale"] <= 1.0
            or risk_numeric["risk_estimation_observations"] < 0
            or not math.isclose(
                risk_numeric["risk_estimation_observations"],
                round(risk_numeric["risk_estimation_observations"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            _fail(
                row_path,
                "portfolio.risk-governor-value",
                "Risk scale and estimation observations are invalid",
            )
        if has_risk_columns and (
            not math.isclose(
                numeric["proposed_target_weight"],
                risk_numeric["pre_governor_target_weight"]
                * risk_numeric["risk_governor_scale"],
                rel_tol=0.0,
                abs_tol=1e-10,
            )
            or not math.isclose(
                risk_numeric["risk_forecast_post_annualized"],
                risk_numeric["risk_forecast_pre_annualized"]
                * risk_numeric["risk_governor_scale"],
                rel_tol=0.0,
                abs_tol=1e-10,
            )
            or (
                risk_numeric["risk_volatility_ceiling_annualized"] > 0
                and risk_numeric["risk_forecast_post_annualized"]
                > risk_numeric["risk_volatility_ceiling_annualized"] + 1e-10
            )
        ):
            _fail(
                row_path,
                "portfolio.risk-governor-reconciliation",
                "Risk-governor weights or volatility forecasts do not reconcile",
            )
        if has_mandate_columns:
            if raw["tradable"] not in {"True", "False"}:
                _fail(
                    f"{row_path}/tradable",
                    "portfolio.boolean",
                    "tradable must be True or False",
                )
            if not raw["permitted_direction"] or not raw["mandate_id"]:
                _fail(
                    row_path,
                    "portfolio.mandate-decision",
                    "Mandate decision fields must be non-empty",
                )
        if not math.isclose(
            numeric["proposed_target_weight"],
            targets[timestamp][asset],
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            _fail(
                row_path,
                "portfolio.target-alignment",
                "Decision target differs from target-weight artifact",
            )
        if not math.isclose(
            numeric["executed_weight"],
            weights[timestamp][asset],
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            _fail(
                row_path,
                "portfolio.weight-alignment",
                "Decision executed weight differs from weight artifact",
            )
        parsed = {
            "timestamp": timestamp,
            "asset": asset,
            **states,
            **optional,
            **numeric,
            **risk_numeric,
            "signal_event": raw["signal_event"],
            "allocation_status": raw["allocation_status"],
            "target_action": raw["target_action"],
            "regime": raw["regime"],
            "execution_action": raw["execution_action"],
            "execution_reason": raw["execution_reason"],
            "risk_governor_status": (
                raw["risk_governor_status"]
                if has_risk_columns
                else "legacy_none"
            ),
            "tradable": (
                raw["tradable"] == "True"
                if has_mandate_columns
                else True
            ),
            "permitted_direction": (
                raw["permitted_direction"]
                if has_mandate_columns
                else "dollar-neutral"
            ),
            "mandate_id": (
                raw["mandate_id"]
                if has_mandate_columns
                else "legacy-dollar-neutral"
            ),
        }
        decisions[key] = parsed
        ordered.append(parsed)
    missing = expected - decisions.keys()
    if missing:
        timestamp, asset = min(missing)
        _fail(
            path,
            "portfolio.decision-panel",
            f"Missing decision row for {timestamp}/{asset}",
        )
    if len(decisions) != len(expected):
        _fail(
            path,
            "portfolio.decision-panel",
            "Decision ledger must contain exactly one row per date and asset",
        )

    daily_by_date = {row["timestamp"]: row for row in daily.rows}
    for timestamp in daily.dates:
        rows = [decisions[(timestamp, asset)] for asset in universe]
        expected_daily = daily_by_date[timestamp]
        risk_signatures = {
            (
                item["risk_governor_status"],
                item["risk_estimation_observations"],
                item["risk_forecast_pre_annualized"],
                item["risk_forecast_post_annualized"],
                item["risk_volatility_ceiling_annualized"],
                item["risk_governor_scale"],
            )
            for item in rows
        }
        if len(risk_signatures) != 1:
            _fail(
                f"{path}/{timestamp}",
                "portfolio.risk-governor-panel",
                "Risk-governor evidence must be identical across one decision date",
            )
        reconciliations = (
            (
                sum(item["gross_return_contribution"] for item in rows),
                expected_daily["gross_return"],
                "gross return",
            ),
            (
                sum(item["cost_contribution"] for item in rows),
                expected_daily["cost"],
                "cost",
            ),
            (
                sum(item["net_return_contribution"] for item in rows),
                expected_daily["net_return"],
                "net return",
            ),
            (
                sum(abs(item["trade_weight"]) for item in rows),
                expected_daily["traded_notional"],
                "traded notional",
            ),
        )
        for actual, expected_value, label in reconciliations:
            if not math.isclose(
                actual,
                expected_value,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                _fail(
                    f"{path}/{timestamp}",
                    "portfolio.reconciliation",
                    f"Decision ledger does not reconcile daily {label}",
                )
    return ordered, decisions


def _split_contract(result: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    metrics = result.get("metrics", {})
    protocol = metrics.get("split_protocol")
    if not isinstance(protocol, dict):
        _fail(
            "RunResult/metrics/split_protocol",
            "portfolio.split-protocol",
            "Portfolio Run is missing fixed split protocol",
        )
    splits = protocol.get("splits")
    if not isinstance(splits, dict) or set(splits) != {
        "train",
        "validation",
        "test",
    }:
        _fail(
            "RunResult/metrics/split_protocol/splits",
            "portfolio.split-protocol",
            "Expected train, validation, and test splits",
        )
    normalized: dict[str, Any] = {}
    ordered_names = ["train", "validation", "test"]
    prior_end: str | None = None
    for name in ordered_names:
        split = splits[name]
        if not isinstance(split, dict):
            _fail(
                f"RunResult/metrics/split_protocol/splits/{name}",
                "portfolio.split-protocol",
                "Split must be an object",
            )
        start = _session_date(
            split.get("start"),
            f"RunResult/metrics/split_protocol/splits/{name}/start",
        )
        end = _session_date(
            split.get("end"),
            f"RunResult/metrics/split_protocol/splits/{name}/end",
        )
        signal_end = _session_date(
            split.get("signalEnd"),
            f"RunResult/metrics/split_protocol/splits/{name}/signalEnd",
        )
        if not start <= signal_end <= end or (
            prior_end is not None and start <= prior_end
        ):
            _fail(
                f"RunResult/metrics/split_protocol/splits/{name}",
                "portfolio.split-order",
                "Splits must be chronological and signalEnd must be bounded",
            )
        normalized[name] = {
            "start": start,
            "end": end,
            "signalEnd": signal_end,
            "role": "selection" if name == "validation" else (
                "visible-audit" if name == "test" else "training"
            ),
        }
        prior_end = end
    return normalized, ordered_names


def _split_for(timestamp: str, splits: dict[str, Any], names: list[str]) -> str:
    for name in names:
        if splits[name]["start"] <= timestamp <= splits[name]["end"]:
            return name
    _fail(
        timestamp,
        "portfolio.split-membership",
        "Daily timestamp does not belong to exactly one fixed split",
    )


def _sample_indices(
    total: int,
    limit: int,
    anchors: set[int],
) -> list[int]:
    if total <= limit:
        return list(range(total))
    fixed = sorted(index for index in anchors if 0 <= index < total)
    if len(fixed) > limit:
        _fail(
            "portfolio sampling",
            "portfolio.sample-limit",
            "Point limit is smaller than required accounting anchors",
        )
    candidates = [index for index in range(total) if index not in anchors]
    slots = limit - len(fixed)
    selected: set[int] = set(fixed)
    if slots >= len(candidates):
        selected.update(candidates)
    elif slots == 1:
        selected.add(candidates[len(candidates) // 2])
    elif slots > 1:
        positions = {
            round(position * (len(candidates) - 1) / (slots - 1))
            for position in range(slots)
        }
        selected.update(candidates[position] for position in positions)
        if len(selected) < limit:
            selected.update(
                candidate
                for candidate in candidates
                if candidate not in selected
                for _ in [None]
                if len(selected) < limit
            )
    return sorted(selected)


def _path_projection(
    daily: ParsedDaily,
    weights: dict[str, dict[str, float]],
    splits: dict[str, Any],
    split_names: list[str],
    point_limit: int,
) -> dict[str, Any]:
    net_growth = 1.0
    gross_growth = 1.0
    benchmark_growth = 1.0
    peak = 1.0
    full: list[dict[str, Any]] = []
    maximum_drawdown = 0.0
    maximum_drawdown_index = 0
    maximum_turnover_index = 0
    total_cost = 0.0
    total_turnover = 0.0
    rebalances = 0
    for index, row in enumerate(daily.rows):
        gross_growth *= 1.0 + row["gross_return"]
        net_growth *= 1.0 + row["net_return"]
        benchmark_growth *= 1.0 + row["benchmark_return"]
        peak = max(peak, net_growth)
        drawdown = net_growth / peak - 1.0
        total_cost += row["cost"]
        total_turnover += row["one_way_turnover"]
        rebalances += int(row["rebalanced"])
        if drawdown < maximum_drawdown:
            maximum_drawdown = drawdown
            maximum_drawdown_index = index
        if (
            row["one_way_turnover"]
            > daily.rows[maximum_turnover_index]["one_way_turnover"]
        ):
            maximum_turnover_index = index
        full.append(
            {
                "timestamp": row["timestamp"],
                "split": _split_for(row["timestamp"], splits, split_names),
                "netGrowth": net_growth,
                "grossGrowth": gross_growth,
                "benchmarkGrowth": benchmark_growth,
                "drawdown": drawdown,
                "grossExposure": row["gross_exposure"],
                "netExposure": row["net_exposure"],
                "cashWeight": row["cash_weight"],
                "oneWayTurnover": row["one_way_turnover"],
                "cost": row["cost"],
                "rebalanced": row["rebalanced"],
                "weights": weights[row["timestamp"]],
            }
        )
    anchors = {
        0,
        len(full) - 1,
        maximum_drawdown_index,
        maximum_turnover_index,
    }
    for split in splits.values():
        for boundary in ("start", "signalEnd", "end"):
            position = bisect_right(daily.dates, split[boundary]) - 1
            if position >= 0:
                anchors.add(position)
            next_position = position + 1
            if next_position < len(daily.dates):
                anchors.add(next_position)
    selected = _sample_indices(len(full), point_limit, anchors)
    return {
        "totalRows": len(full),
        "sampledRows": len(selected),
        "pointLimit": point_limit,
        "sampling": "deterministic-even-with-accounting-anchors",
        "summary": {
            "netTotalReturn": net_growth - 1.0,
            "grossTotalReturn": gross_growth - 1.0,
            "benchmarkTotalReturn": benchmark_growth - 1.0,
            "maximumDrawdown": maximum_drawdown,
            "maximumDrawdownAt": full[maximum_drawdown_index]["timestamp"],
            "maximumOneWayTurnover": daily.rows[maximum_turnover_index][
                "one_way_turnover"
            ],
            "maximumOneWayTurnoverAt": full[maximum_turnover_index]["timestamp"],
            "totalOneWayTurnover": total_turnover,
            "totalCost": total_cost,
            "rebalanceDays": rebalances,
        },
        "points": [full[index] for index in selected],
    }


def _attribution_projection(
    result: dict[str, Any],
    universe: list[str],
) -> dict[str, list[dict[str, Any]]]:
    attribution = result["metrics"].get("attribution")
    if not isinstance(attribution, dict):
        _fail(
            "RunResult/metrics/attribution",
            "portfolio.attribution",
            "Portfolio Run is missing attribution evidence",
        )
    output: dict[str, list[dict[str, Any]]] = {}
    fields = {
        "annualizedNetContribution": "annualized_net_contribution",
        "averageAbsoluteWeight": "average_absolute_executed_weight",
        "meanVarianceContributionShare": "mean_variance_contribution_share",
        "totalCostContribution": "total_cost_contribution",
        "totalOneWayTurnoverContribution": (
            "total_one_way_turnover_contribution"
        ),
    }
    for split_name in ("validation", "test"):
        split = attribution.get(split_name)
        by_asset = split.get("by_asset") if isinstance(split, dict) else None
        if not isinstance(by_asset, dict) or set(by_asset) != set(universe):
            _fail(
                f"RunResult/metrics/attribution/{split_name}/by_asset",
                "portfolio.attribution-universe",
                "Attribution assets must exactly match Study universe",
            )
        projected: list[dict[str, Any]] = []
        for asset in universe:
            values = by_asset[asset]
            if not isinstance(values, dict):
                _fail(
                    f"RunResult/metrics/attribution/{split_name}/by_asset/{asset}",
                    "portfolio.attribution",
                    "Per-asset attribution must be an object",
                )
            projected.append(
                {
                    "asset": asset,
                    **{
                        output_name: _finite(
                            values.get(source_name),
                            "RunResult/metrics/attribution/"
                            f"{split_name}/by_asset/{asset}/{source_name}",
                        )
                        for output_name, source_name in fields.items()
                    },
                }
            )
        output[split_name] = projected
    return output


def _current_book(
    daily: ParsedDaily,
    universe: list[str],
    decisions: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    timestamp = daily.dates[-1]
    positions = []
    for asset in universe:
        item = decisions[(timestamp, asset)]
        positions.append(
            {
                "asset": asset,
                "signalState": item["signal_state"],
                "signalEvent": item["signal_event"],
                "tradable": item["tradable"],
                "permittedDirection": item["permitted_direction"],
                "allocationStatus": item["allocation_status"],
                "conviction": item["conviction"],
                "riskStrength": item["risk_strength"],
                "preGovernorTargetWeight": item[
                    "pre_governor_target_weight"
                ],
                "targetWeight": item["proposed_target_weight"],
                "pretradeWeight": item["pretrade_weight"],
                "executedWeight": item["executed_weight"],
                "tradeWeight": item["trade_weight"],
                "targetAction": item["target_action"],
                "executionAction": item["execution_action"],
                "executionReason": item["execution_reason"],
                "regime": item["regime"],
                "netReturnContribution": item["net_return_contribution"],
                "varianceContributionShare": item[
                    "variance_contribution_share"
                ],
            }
        )
    daily_row = daily.rows[-1]
    return {
        "timestamp": timestamp,
        "historicalResearchWeights": True,
        "grossExposure": daily_row["gross_exposure"],
        "netExposure": daily_row["net_exposure"],
        "cashWeight": daily_row["cash_weight"],
        "oneWayTurnover": daily_row["one_way_turnover"],
        "cost": daily_row["cost"],
        "rebalanced": daily_row["rebalanced"],
        "riskGovernorStatus": decisions[
            (timestamp, universe[0])
        ]["risk_governor_status"],
        "riskGovernorScale": decisions[
            (timestamp, universe[0])
        ]["risk_governor_scale"],
        "riskForecastPreAnnualized": decisions[
            (timestamp, universe[0])
        ]["risk_forecast_pre_annualized"],
        "riskForecastPostAnnualized": decisions[
            (timestamp, universe[0])
        ]["risk_forecast_post_annualized"],
        "riskVolatilityCeilingAnnualized": decisions[
            (timestamp, universe[0])
        ]["risk_volatility_ceiling_annualized"],
        "riskEstimationObservations": int(
            decisions[(timestamp, universe[0])][
                "risk_estimation_observations"
            ]
        ),
        "positions": positions,
    }


def _recent_transitions(
    ordered: list[dict[str, Any]],
    universe: list[str],
) -> list[dict[str, Any]]:
    universe_order = {asset: index for index, asset in enumerate(universe)}
    transitions = [
        item
        for item in ordered
        if item["signal_event"]
        not in {
            "hold_long",
            "hold_short",
            "stay_flat",
            "unavailable_flat",
            "context_only",
        }
        or item["execution_action"]
        in {
            "open_long",
            "open_short",
            "close_long",
            "close_short",
            "reverse_long_to_short",
            "reverse_short_to_long",
        }
    ]
    transitions.sort(
        key=lambda item: (item["timestamp"], universe_order[item["asset"]])
    )
    return [
        {
            "timestamp": item["timestamp"],
            "asset": item["asset"],
            "signalEvent": item["signal_event"],
            "tradable": item["tradable"],
            "permittedDirection": item["permitted_direction"],
            "allocationStatus": item["allocation_status"],
            "riskGovernorStatus": item["risk_governor_status"],
            "riskGovernorScale": item["risk_governor_scale"],
            "preGovernorTargetWeight": item[
                "pre_governor_target_weight"
            ],
            "priorSignalState": item["prior_signal_state"],
            "signalState": item["signal_state"],
            "targetWeight": item["proposed_target_weight"],
            "executedWeight": item["executed_weight"],
            "tradeWeight": item["trade_weight"],
            "executionAction": item["execution_action"],
            "executionReason": item["execution_reason"],
            "regime": item["regime"],
        }
        for item in transitions[-MAX_RECENT_TRANSITIONS:]
    ]


def _signal_policy_projection(result: dict[str, Any]) -> dict[str, Any]:
    policy = result["metrics"].get("signal_policy")
    if not isinstance(policy, dict):
        _fail(
            "RunResult/metrics/signal_policy",
            "portfolio.signal-policy",
            "Portfolio Run is missing mechanical signal-policy evidence",
        )
    parameters = policy.get("parameters")
    if not isinstance(parameters, dict):
        _fail(
            "RunResult/metrics/signal_policy/parameters",
            "portfolio.signal-policy",
            "Signal-policy parameters must be an object",
        )
    output: dict[str, Any] = {"parameters": parameters}
    for split_name in ("validation", "test"):
        split = policy.get(split_name)
        if not isinstance(split, dict):
            _fail(
                f"RunResult/metrics/signal_policy/{split_name}",
                "portfolio.signal-policy",
                "Signal-policy split evidence must be an object",
            )
        output[split_name] = {
            "entries": split.get("entries"),
            "exits": split.get("exits"),
            "reversals": split.get("reversals"),
            "stateChangeRate": split.get("state_change_rate"),
            "annualizedTargetOneWayTurnover": split.get(
                "annualized_target_one_way_turnover"
            ),
            "signalEventCounts": split.get("signal_event_counts"),
            "targetActionCounts": split.get("target_action_counts"),
            "riskGovernorStatusCounts": split.get(
                "risk_governor_status_counts"
            ),
            "riskLimitedDates": split.get("risk_limited_dates"),
            "riskLimitedRate": split.get("risk_limited_rate"),
            "riskUnavailableDates": split.get("risk_unavailable_dates"),
            "averageActiveRiskScale": split.get(
                "average_active_risk_scale"
            ),
            "maximumPreGovernorAnnualizedVolatility": split.get(
                "maximum_pre_governor_annualized_volatility"
            ),
            "maximumPostGovernorAnnualizedVolatility": split.get(
                "maximum_post_governor_annualized_volatility"
            ),
        }
    return output


def _mandate_projection(
    run: RunContext,
    report: dict[str, Any],
    universe: list[str],
) -> dict[str, Any]:
    raw = run.result["metrics"].get("portfolio_mandate")
    report_raw = report.get("portfolioMandate")
    if raw is None and report_raw is None:
        return {
            "available": False,
            "id": None,
            "sha256": None,
            "sourceKind": "legacy-implicit",
            "requestHash": None,
            "direction": "research-only",
            "family": "dollar-neutral",
            "researchUniverse": universe,
            "tradableAssets": universe,
            "contextAssets": [],
            "grossLimit": 1.0,
            "maxAbsWeight": 0.30,
            "cashAllowed": True,
            "shortAllowed": True,
            "benchmark": "equal-weight-long-research-universe",
            "riskPolicy": None,
        }
    if not isinstance(raw, dict) or not isinstance(report_raw, dict):
        _fail(
            "RunResult/metrics/portfolio_mandate",
            "portfolio.mandate",
            "Portfolio Mandate must exist in both Run metrics and report",
        )
    try:
        mandate = validate_portfolio_mandate(
            raw,
            "RunResult/metrics/portfolio_mandate",
        )
    except AutoQuantValidationError as error:
        raise error
    if report_raw != mandate:
        _fail(
            "portfolio-report.json/portfolioMandate",
            "portfolio.mandate-report",
            "Portfolio report Mandate differs from Run metrics",
        )
    if mandate["researchUniverse"] != universe:
        _fail(
            "RunResult/metrics/portfolio_mandate/researchUniverse",
            "portfolio.mandate-universe",
            "Portfolio Mandate differs from the Run universe",
        )
    dependencies = run.result.get("dependencies")
    source_hashes = (
        dependencies.get("sourceHashes")
        if isinstance(dependencies, dict)
        else None
    )
    mandate_hash = (
        source_hashes.get(PORTFOLIO_MANDATE)
        if isinstance(source_hashes, dict)
        else None
    )
    if not isinstance(mandate_hash, str):
        _fail(
            "RunResult/dependencies/sourceHashes",
            "portfolio.mandate-dependency",
            "Portfolio Mandate is absent from fixed Run dependencies",
        )
    source = mandate["source"]
    construction = mandate["construction"]
    return {
        "available": True,
        "id": mandate["id"],
        "sha256": mandate_hash,
        "sourceKind": source["kind"],
        "requestHash": source["requestHash"],
        "direction": source["direction"],
        "family": construction["family"],
        "researchUniverse": mandate["researchUniverse"],
        "tradableAssets": mandate["tradableAssets"],
        "contextAssets": mandate["contextAssets"],
        "grossLimit": construction["grossLimit"],
        "maxAbsWeight": construction["maxAbsWeight"],
        "cashAllowed": construction["cashAllowed"],
        "shortAllowed": construction["shortAllowed"],
        "benchmark": construction["benchmark"],
        "riskPolicy": construction["riskPolicy"],
    }


def _risk_governor_projection(
    result: dict[str, Any],
    mandate: dict[str, Any],
) -> dict[str, Any]:
    raw = result["metrics"].get("robustness", {}).get("risk_governor")
    if raw is None and mandate["riskPolicy"] is None:
        return {
            "available": False,
            "policy": None,
            "selectionAuthority": "diagnostic-only",
            "validation": None,
            "test": None,
        }
    if (
        not isinstance(raw, dict)
        or raw.get("policy") != mandate["riskPolicy"]
        or raw.get("selectionAuthority") != "diagnostic-only"
    ):
        _fail(
            "RunResult/metrics/robustness/risk_governor",
            "portfolio.risk-governor",
            "Risk-governor robustness evidence differs from the fixed Mandate",
        )
    projected: dict[str, Any] = {
        "available": True,
        "policy": raw["policy"],
        "selectionAuthority": "diagnostic-only",
    }
    for split_name in ("validation", "test"):
        split = raw.get(split_name)
        governed = split.get("governed") if isinstance(split, dict) else None
        ungoverned = (
            split.get("ungoverned_diagnostic")
            if isinstance(split, dict)
            else None
        )
        if not isinstance(governed, dict) or not isinstance(ungoverned, dict):
            _fail(
                f"RunResult/metrics/robustness/risk_governor/{split_name}",
                "portfolio.risk-governor",
                "Risk-governor split must contain governed and diagnostic evidence",
            )
        projected[split_name] = {
            "governed": {
                key: _finite(
                    governed.get(source),
                    "RunResult/metrics/robustness/risk_governor/"
                    f"{split_name}/governed/{source}",
                )
                for key, source in {
                    "netSharpe": "net_sharpe",
                    "annualVolatility": "annual_volatility",
                    "maximumDrawdown": "maximum_drawdown",
                    "averageGrossExposure": "average_gross_exposure",
                    "riskLimitedDates": "risk_limited_dates",
                    "riskLimitedRate": "risk_limited_rate",
                    "averageActiveRiskScale": "average_active_risk_scale",
                    "maximumPreGovernorAnnualizedVolatility": (
                        "maximum_pre_governor_annualized_volatility"
                    ),
                    "maximumPostGovernorAnnualizedVolatility": (
                        "maximum_post_governor_annualized_volatility"
                    ),
                }.items()
            },
            "ungovernedDiagnostic": {
                key: _finite(
                    ungoverned.get(source),
                    "RunResult/metrics/robustness/risk_governor/"
                    f"{split_name}/ungoverned_diagnostic/{source}",
                )
                for key, source in {
                    "netSharpe": "net_sharpe",
                    "annualVolatility": "annual_volatility",
                    "maximumDrawdown": "maximum_drawdown",
                    "averageGrossExposure": "average_gross_exposure",
                }.items()
            },
            "netSharpeDelta": _finite(
                split.get("net_sharpe_delta"),
                "RunResult/metrics/robustness/risk_governor/"
                f"{split_name}/net_sharpe_delta",
            ),
            "annualVolatilityDelta": _finite(
                split.get("annual_volatility_delta"),
                "RunResult/metrics/robustness/risk_governor/"
                f"{split_name}/annual_volatility_delta",
            ),
        }
    return projected


def load_portfolio_diagnostics(
    project: ProjectContext,
    run_id: str,
    *,
    point_limit: int = DEFAULT_PORTFOLIO_POINTS,
) -> dict[str, Any]:
    """Verify and project one immutable Portfolio Run into a bounded read model."""

    if (
        not isinstance(point_limit, int)
        or isinstance(point_limit, bool)
        or not MIN_PORTFOLIO_POINTS <= point_limit <= MAX_PORTFOLIO_POINTS
    ):
        _fail(
            point_limit,
            "portfolio.point-limit",
            f"point_limit must be {MIN_PORTFOLIO_POINTS}..{MAX_PORTFOLIO_POINTS}",
        )
    run = load_run(project, run_id)
    if run.result["objective"]["metric"] != "validation_net_sharpe":
        _fail(
            run.root_dir,
            "portfolio.run-kind",
            "Run is not a fixed Portfolio Lab evaluation",
        )
    universe = run.result["dataset"].get("universe")
    if (
        not isinstance(universe, list)
        or not universe
        or len(universe) > MAX_UNIVERSE
        or not all(isinstance(asset, str) and asset for asset in universe)
        or len(universe) != len(set(universe))
    ):
        _fail(
            run.root_dir,
            "portfolio.universe",
            f"Portfolio universe must contain 1..{MAX_UNIVERSE} unique assets",
        )
    paths, artifact_identities = _artifact_paths(run)
    try:
        report = json.loads(paths["portfolio-report"].read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail(
            paths["portfolio-report"],
            "portfolio.report-json",
            "Portfolio report must be a UTF-8 JSON object",
        )
    if not isinstance(report, dict):
        _fail(
            paths["portfolio-report"],
            "portfolio.report-json",
            "Portfolio report must be a UTF-8 JSON object",
        )

    daily = _parse_daily(paths["portfolio-daily"])
    target_dates, targets = _parse_weight_panel(
        paths["portfolio-targets"],
        universe,
    )
    weight_dates, weights = _parse_weight_panel(
        paths["portfolio-weights"],
        universe,
    )
    if weight_dates != daily.dates:
        _fail(
            paths["portfolio-weights"],
            "portfolio.weight-panel",
            "Executed weights must exactly match daily timestamp panel",
        )
    if (
        target_dates[: len(daily.dates)] != daily.dates
        or len(target_dates) not in {len(daily.dates), len(daily.dates) + 1}
    ):
        _fail(
            paths["portfolio-targets"],
            "portfolio.target-panel",
            "Targets must cover the daily panel with at most one pending row",
        )
    ordered_decisions, decisions = _parse_decisions(
        paths["portfolio-decisions"],
        daily,
        universe,
        targets,
        weights,
    )
    splits, split_names = _split_contract(run.result)
    research_integrity = run.result["metrics"].get("research_integrity")
    if not isinstance(research_integrity, dict):
        _fail(
            "RunResult/metrics/research_integrity",
            "portfolio.selection",
            "Portfolio Run must disclose selection integrity",
        )
    mandate = _mandate_projection(run, report, universe)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": PORTFOLIO_DIAGNOSTICS_KIND,
        "run": {
            "id": run.result["id"],
            "studyId": run.result["study"]["id"],
            "status": run.result["status"],
            "startedAt": run.result["startedAt"],
            "inputHash": run.result["inputHash"],
            "datasetHash": run.result["dataset"]["hash"],
            "primaryMetric": run.result["objective"]["metric"],
            "primaryValue": run.result["metrics"][
                run.result["objective"]["metric"]
            ],
        },
        "universe": universe,
        "mandate": mandate,
        "selection": {
            "selectionSplit": research_integrity.get("selection_split"),
            "testRole": research_integrity.get("test_role"),
            "testEntersSelection": research_integrity.get(
                "test_enters_selection"
            ),
            "externalHoldoutRule": research_integrity.get(
                "external_holdout_rule"
            ),
            "splits": splits,
        },
        "artifacts": artifact_identities,
        "path": _path_projection(
            daily,
            weights,
            splits,
            split_names,
            point_limit,
        ),
        "currentBook": _current_book(
            daily,
            universe,
            decisions,
        ),
        "recentTransitions": _recent_transitions(
            ordered_decisions,
            universe,
        ),
        "signalPolicy": _signal_policy_projection(run.result),
        "riskGovernor": _risk_governor_projection(run.result, mandate),
        "attribution": _attribution_projection(run.result, universe),
    }


PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant bounded Portfolio Run diagnostics",
    "$defs": {
        "artifact": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "sha256"],
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        },
        "split": {
            "type": "object",
            "additionalProperties": False,
            "required": ["start", "end", "signalEnd", "role"],
            "properties": {
                "start": {"type": "string", "format": "date"},
                "end": {"type": "string", "format": "date"},
                "signalEnd": {"type": "string", "format": "date"},
                "role": {"type": "string", "minLength": 1},
            },
        },
        "pathPoint": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "timestamp",
                "split",
                "netGrowth",
                "grossGrowth",
                "benchmarkGrowth",
                "drawdown",
                "grossExposure",
                "netExposure",
                "cashWeight",
                "oneWayTurnover",
                "cost",
                "rebalanced",
                "weights",
            ],
            "properties": {
                "timestamp": {"type": "string", "format": "date"},
                "split": {"enum": ["train", "validation", "test"]},
                "netGrowth": {"type": "number"},
                "grossGrowth": {"type": "number"},
                "benchmarkGrowth": {"type": "number"},
                "drawdown": {"type": "number"},
                "grossExposure": {"type": "number"},
                "netExposure": {"type": "number"},
                "cashWeight": {"type": "number"},
                "oneWayTurnover": {"type": "number", "minimum": 0},
                "cost": {"type": "number", "minimum": 0},
                "rebalanced": {"type": "boolean"},
                "weights": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                },
            },
        },
        "position": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "asset",
                "signalState",
                "signalEvent",
                "tradable",
                "permittedDirection",
                "allocationStatus",
                "conviction",
                "preGovernorTargetWeight",
                "targetWeight",
                "targetAction",
                "pretradeWeight",
                "executedWeight",
                "tradeWeight",
                "executionAction",
                "executionReason",
                "netReturnContribution",
                "regime",
                "riskStrength",
                "varianceContributionShare",
            ],
            "properties": {
                "asset": {"type": "string", "minLength": 1},
                "signalState": {"enum": [-1, 0, 1]},
                "signalEvent": {"type": "string", "minLength": 1},
                "tradable": {"type": "boolean"},
                "permittedDirection": {
                    "enum": [
                        "dollar-neutral",
                        "long-cash",
                        "short-cash",
                    ]
                },
                "allocationStatus": {"type": "string", "minLength": 1},
                "conviction": {"type": "number"},
                "preGovernorTargetWeight": {"type": "number"},
                "targetWeight": {"type": "number"},
                "targetAction": {"type": "string", "minLength": 1},
                "pretradeWeight": {"type": "number"},
                "executedWeight": {"type": "number"},
                "tradeWeight": {"type": "number"},
                "executionAction": {"type": "string", "minLength": 1},
                "executionReason": {"type": "string", "minLength": 1},
                "netReturnContribution": {"type": "number"},
                "regime": {"type": "string", "minLength": 1},
                "riskStrength": {"type": "number"},
                "varianceContributionShare": {"type": "number"},
            },
        },
        "transition": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "timestamp",
                "asset",
                "priorSignalState",
                "signalState",
                "signalEvent",
                "tradable",
                "permittedDirection",
                "allocationStatus",
                "riskGovernorStatus",
                "riskGovernorScale",
                "preGovernorTargetWeight",
                "targetWeight",
                "executedWeight",
                "tradeWeight",
                "executionAction",
                "executionReason",
                "regime",
            ],
            "properties": {
                "timestamp": {"type": "string", "format": "date"},
                "asset": {"type": "string", "minLength": 1},
                "priorSignalState": {"enum": [-1, 0, 1]},
                "signalState": {"enum": [-1, 0, 1]},
                "signalEvent": {"type": "string", "minLength": 1},
                "tradable": {"type": "boolean"},
                "permittedDirection": {
                    "enum": [
                        "dollar-neutral",
                        "long-cash",
                        "short-cash",
                    ]
                },
                "allocationStatus": {"type": "string", "minLength": 1},
                "riskGovernorStatus": {"type": "string", "minLength": 1},
                "riskGovernorScale": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "preGovernorTargetWeight": {"type": "number"},
                "targetWeight": {"type": "number"},
                "executedWeight": {"type": "number"},
                "tradeWeight": {"type": "number"},
                "executionAction": {"type": "string", "minLength": 1},
                "executionReason": {"type": "string", "minLength": 1},
                "regime": {"type": "string", "minLength": 1},
            },
        },
        "attributionRow": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "asset",
                "annualizedNetContribution",
                "averageAbsoluteWeight",
                "meanVarianceContributionShare",
                "totalCostContribution",
                "totalOneWayTurnoverContribution",
            ],
            "properties": {
                "asset": {"type": "string", "minLength": 1},
                "annualizedNetContribution": {"type": "number"},
                "averageAbsoluteWeight": {"type": "number", "minimum": 0},
                "meanVarianceContributionShare": {"type": "number"},
                "totalCostContribution": {"type": "number", "minimum": 0},
                "totalOneWayTurnoverContribution": {
                    "type": "number",
                    "minimum": 0,
                },
            },
        },
    },
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "run",
        "universe",
        "mandate",
        "selection",
        "artifacts",
        "path",
        "currentBook",
        "recentTransitions",
        "signalPolicy",
        "riskGovernor",
        "attribution",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": PORTFOLIO_DIAGNOSTICS_KIND},
        "run": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "id",
                "studyId",
                "status",
                "startedAt",
                "inputHash",
                "datasetHash",
                "primaryMetric",
                "primaryValue",
            ],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "studyId": {"type": "string", "minLength": 1},
                "status": {"const": "succeeded"},
                "startedAt": {"type": "string", "format": "date-time"},
                "inputHash": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "datasetHash": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "primaryMetric": {"type": "string", "minLength": 1},
                "primaryValue": {"type": "number"},
            },
        },
        "universe": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_UNIVERSE,
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
        "mandate": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "available",
                "id",
                "sha256",
                "sourceKind",
                "requestHash",
                "direction",
                "family",
                "researchUniverse",
                "tradableAssets",
                "contextAssets",
                "grossLimit",
                "maxAbsWeight",
                "cashAllowed",
                "shortAllowed",
                "benchmark",
                "riskPolicy",
            ],
            "properties": {
                "available": {"type": "boolean"},
                "id": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "string",
                            "pattern": "^mandate-[0-9a-f]{16}$",
                        },
                    ]
                },
                "sha256": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "string",
                            "pattern": "^[0-9a-f]{64}$",
                        },
                    ]
                },
                "sourceKind": {
                    "enum": [
                        "legacy-implicit",
                        "research-request",
                        "template-default",
                    ]
                },
                "requestHash": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "string",
                            "pattern": "^[0-9a-f]{64}$",
                        },
                    ]
                },
                "direction": {
                    "enum": [
                        "long",
                        "short",
                        "long-short",
                        "relative-value",
                        "research-only",
                    ]
                },
                "family": {
                    "enum": [
                        "dollar-neutral",
                        "long-cash",
                        "short-cash",
                    ]
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
                "grossLimit": {"type": "number", "exclusiveMinimum": 0},
                "maxAbsWeight": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                },
                "cashAllowed": {"type": "boolean"},
                "shortAllowed": {"type": "boolean"},
                "benchmark": {"type": "string", "minLength": 1},
                "riskPolicy": {
                    "anyOf": [
                        {"type": "null"},
                        {
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
                                "method": {"type": "string", "minLength": 1},
                                "annualizedVolatilityCeiling": {
                                    "type": "number",
                                    "exclusiveMinimum": 0,
                                },
                                "covarianceWindow": {
                                    "type": "integer",
                                    "minimum": 2,
                                },
                                "minimumObservations": {
                                    "type": "integer",
                                    "minimum": 2,
                                },
                                "annualizationPeriods": {
                                    "type": "integer",
                                    "minimum": 1,
                                },
                                "scaleUp": {"const": False},
                            },
                        },
                    ]
                },
            },
        },
        "selection": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "selectionSplit",
                "testRole",
                "testEntersSelection",
                "externalHoldoutRule",
                "splits",
            ],
            "properties": {
                "selectionSplit": {"const": "validation"},
                "testRole": {"type": "string", "minLength": 1},
                "testEntersSelection": {"const": False},
                "externalHoldoutRule": {"type": "string", "minLength": 1},
                "splits": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["train", "validation", "test"],
                    "properties": {
                        "train": {"$ref": "#/$defs/split"},
                        "validation": {"$ref": "#/$defs/split"},
                        "test": {"$ref": "#/$defs/split"},
                    },
                },
            },
        },
        "artifacts": {
            "type": "object",
            "additionalProperties": False,
            "required": sorted(EXPECTED_ARTIFACT_KINDS),
            "properties": {
                kind: {"$ref": "#/$defs/artifact"}
                for kind in sorted(EXPECTED_ARTIFACT_KINDS)
            },
        },
        "path": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "totalRows",
                "sampledRows",
                "pointLimit",
                "sampling",
                "summary",
                "points",
            ],
            "properties": {
                "totalRows": {"type": "integer", "minimum": 1},
                "sampledRows": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_PORTFOLIO_POINTS,
                },
                "pointLimit": {
                    "type": "integer",
                    "minimum": MIN_PORTFOLIO_POINTS,
                    "maximum": MAX_PORTFOLIO_POINTS,
                },
                "sampling": {
                    "const": "deterministic-even-with-accounting-anchors"
                },
                "summary": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "netTotalReturn",
                        "grossTotalReturn",
                        "benchmarkTotalReturn",
                        "maximumDrawdown",
                        "maximumDrawdownAt",
                        "totalOneWayTurnover",
                        "maximumOneWayTurnover",
                        "maximumOneWayTurnoverAt",
                        "totalCost",
                        "rebalanceDays",
                    ],
                    "properties": {
                        "netTotalReturn": {"type": "number"},
                        "grossTotalReturn": {"type": "number"},
                        "benchmarkTotalReturn": {"type": "number"},
                        "maximumDrawdown": {"type": "number"},
                        "maximumDrawdownAt": {
                            "type": "string",
                            "format": "date",
                        },
                        "totalOneWayTurnover": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "maximumOneWayTurnover": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "maximumOneWayTurnoverAt": {
                            "type": "string",
                            "format": "date",
                        },
                        "totalCost": {"type": "number", "minimum": 0},
                        "rebalanceDays": {"type": "integer", "minimum": 0},
                    },
                },
                "points": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_PORTFOLIO_POINTS,
                    "items": {"$ref": "#/$defs/pathPoint"},
                },
            },
        },
        "currentBook": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "timestamp",
                "historicalResearchWeights",
                "grossExposure",
                "netExposure",
                "cashWeight",
                "oneWayTurnover",
                "cost",
                "rebalanced",
                "riskGovernorStatus",
                "riskGovernorScale",
                "riskForecastPreAnnualized",
                "riskForecastPostAnnualized",
                "riskVolatilityCeilingAnnualized",
                "riskEstimationObservations",
                "positions",
            ],
            "properties": {
                "timestamp": {"type": "string", "format": "date"},
                "historicalResearchWeights": {"const": True},
                "grossExposure": {"type": "number", "minimum": 0},
                "netExposure": {"type": "number"},
                "cashWeight": {"type": "number"},
                "oneWayTurnover": {"type": "number", "minimum": 0},
                "cost": {"type": "number", "minimum": 0},
                "rebalanced": {"type": "boolean"},
                "riskGovernorStatus": {
                    "type": "string",
                    "minLength": 1,
                },
                "riskGovernorScale": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "riskForecastPreAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "riskForecastPostAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "riskVolatilityCeilingAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "riskEstimationObservations": {
                    "type": "integer",
                    "minimum": 0,
                },
                "positions": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_UNIVERSE,
                    "items": {"$ref": "#/$defs/position"},
                },
            },
        },
        "recentTransitions": {
            "type": "array",
            "maxItems": MAX_RECENT_TRANSITIONS,
            "items": {"$ref": "#/$defs/transition"},
        },
        "signalPolicy": {
            "type": "object",
            "required": ["parameters", "validation", "test"],
            "properties": {
                "parameters": {"type": "object"},
                "validation": {"type": "object"},
                "test": {"type": "object"},
            },
        },
        "riskGovernor": {"type": "object"},
        "attribution": {
            "type": "object",
            "additionalProperties": False,
            "required": ["validation", "test"],
            "properties": {
                "validation": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_UNIVERSE,
                    "items": {"$ref": "#/$defs/attributionRow"},
                },
                "test": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_UNIVERSE,
                    "items": {"$ref": "#/$defs/attributionRow"},
                },
            },
        },
    },
}
