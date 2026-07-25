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

import pandas as pd

from .mandates import (
    PORTFOLIO_MANDATE,
    validate_portfolio_mandate,
)
from .project_templates.ohlcv_portfolio_lab.portfolio_core import (
    GROSS_TARGET,
    LONG_ENTRY_PERCENTILE,
    LONG_EXIT_PERCENTILE,
    MAX_ABS_WEIGHT,
    NO_TRADE_ONE_WAY,
    POSITION_EPISODE_COLUMNS,
    PortfolioFailure,
    SHORT_ENTRY_PERCENTILE,
    SHORT_EXIT_PERCENTILE,
    VOLATILITY_WINDOW,
    build_position_episodes,
    performance_metrics,
    position_episode_metrics,
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
MAX_EPISODE_ROWS = 100_000
MAX_NEIGHBORHOOD_ROWS = 100_000
MAX_UNIVERSE = 256
MAX_RECENT_TRANSITIONS = 40
MECHANICAL_DECISION_METHOD = (
    "stateful-percentile-target-risk-execution-chain-v1"
)
PERCENTILE_DISTANCE_SEMANTICS = (
    "current-cross-sectional-percentile-points-with-peer-ranks-held-fixed"
)
EXPECTED_SIGNAL_PARAMETERS = {
    "long_entry_percentile": LONG_ENTRY_PERCENTILE,
    "long_exit_percentile": LONG_EXIT_PERCENTILE,
    "short_exit_percentile": SHORT_EXIT_PERCENTILE,
    "short_entry_percentile": SHORT_ENTRY_PERCENTILE,
    "volatility_window": VOLATILITY_WINDOW,
    "gross_target": GROSS_TARGET,
    "max_abs_weight": MAX_ABS_WEIGHT,
    "no_trade_one_way": NO_TRADE_ONE_WAY,
}
BASE_ARTIFACT_KINDS = {
    "portfolio-report",
    "portfolio-daily",
    "portfolio-targets",
    "portfolio-weights",
    "portfolio-decisions",
}
POSITION_EPISODE_ARTIFACT_KIND = "portfolio-position-episodes"
PARAMETER_NEIGHBORHOOD_ARTIFACT_KIND = (
    "portfolio-parameter-neighborhood"
)
EXPECTED_ARTIFACT_KINDS = BASE_ARTIFACT_KINDS | {
    POSITION_EPISODE_ARTIFACT_KIND,
    PARAMETER_NEIGHBORHOOD_ARTIFACT_KIND,
}
PARAMETER_NEIGHBORHOOD_METHOD = (
    "predeclared-signal-threshold-no-trade-neighborhood-v1"
)
PARAMETER_BASE_CONFIGURATION_ID = "base__band-005"
PARAMETER_SIGNAL_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "id": "broad-entry",
        "label": "Broad entry",
        "longEntry": 0.55,
        "longExit": 0.55,
        "shortExit": 0.45,
        "shortEntry": 0.45,
    },
    {
        "id": "base",
        "label": "Base",
        "longEntry": 0.75,
        "longExit": 0.55,
        "shortExit": 0.45,
        "shortEntry": 0.25,
    },
    {
        "id": "selective-entry",
        "label": "Selective entry",
        "longEntry": 0.95,
        "longExit": 0.55,
        "shortExit": 0.45,
        "shortEntry": 0.05,
    },
    {
        "id": "fast-exit",
        "label": "Fast exit",
        "longEntry": 0.75,
        "longExit": 0.75,
        "shortExit": 0.25,
        "shortEntry": 0.25,
    },
    {
        "id": "selective-fast-exit",
        "label": "Selective + fast exit",
        "longEntry": 0.95,
        "longExit": 0.75,
        "shortExit": 0.25,
        "shortEntry": 0.05,
    },
)
PARAMETER_NO_TRADE_BANDS = (0.0, 0.05, 0.10)
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
LIQUIDITY_REFERENCE_NAV = 1_000_000.0
LIQUIDITY_DECISION_COLUMNS = {
    "liquidity_capacity_status",
    "liquidity_adv_observations",
    "causal_adv_dollar_volume",
    "reference_nav_adv_participation",
    "asset_capacity_nav_1pct",
    "asset_capacity_nav_5pct",
    "portfolio_capacity_nav_1pct",
    "portfolio_capacity_nav_5pct",
    "capacity_binding_asset",
}
LIQUIDITY_DECISION_FLOATS = LIQUIDITY_DECISION_COLUMNS - {
    "liquidity_capacity_status",
    "capacity_binding_asset",
}
EXECUTION_RISK_DAILY_FLOATS = {
    "execution_risk_observations",
    "pretrade_risk_forecast_annualized",
    "proposed_risk_forecast_pre_annualized",
    "proposed_risk_forecast_post_annualized",
    "executed_risk_forecast_annualized",
    "execution_risk_ceiling_annualized",
    "proposed_runtime_risk_scale",
    "execution_risk_repair_scale",
    "proposed_one_way_turnover",
}
EXECUTION_RISK_DAILY_BOOLEANS = {
    "execution_risk_forecast_available",
    "ordinary_rebalance",
    "risk_rebalance_override",
}
EXECUTION_RISK_DAILY_STRINGS = {
    "execution_reason",
    "execution_risk_status",
}
EXECUTION_RISK_DAILY_COLUMNS = (
    EXECUTION_RISK_DAILY_FLOATS
    | EXECUTION_RISK_DAILY_BOOLEANS
    | EXECUTION_RISK_DAILY_STRINGS
)
EXECUTION_RISK_DECISION_COLUMNS = EXECUTION_RISK_DAILY_COLUMNS - {
    "execution_reason"
}
EXECUTION_RISK_DECISION_FLOATS = EXECUTION_RISK_DAILY_FLOATS


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
    missing = BASE_ARTIFACT_KINDS - paths.keys()
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
    has_execution_risk = EXECUTION_RISK_DAILY_COLUMNS.issubset(fields)
    if EXECUTION_RISK_DAILY_COLUMNS & set(fields) and not has_execution_risk:
        _fail(
            path,
            "portfolio.execution-risk-columns",
            "Daily evidence must contain the complete execution-risk column set",
        )
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
        if has_execution_risk:
            execution_numeric = {
                key: _finite(raw[key], f"{path}:{index}/{key}")
                for key in EXECUTION_RISK_DAILY_FLOATS
            }
            execution_boolean: dict[str, bool] = {}
            for key in EXECUTION_RISK_DAILY_BOOLEANS:
                if raw[key] not in {"True", "False"}:
                    _fail(
                        f"{path}:{index}/{key}",
                        "portfolio.boolean",
                        f"{key} must be True or False",
                    )
                execution_boolean[key] = raw[key] == "True"
            if any(not raw[key] for key in EXECUTION_RISK_DAILY_STRINGS):
                _fail(
                    f"{path}:{index}",
                    "portfolio.execution-risk-string",
                    "Execution-risk status and reason must be non-empty",
                )
            if (
                any(value < 0 for value in execution_numeric.values())
                or not 0
                <= execution_numeric["proposed_runtime_risk_scale"]
                <= 1
                or not 0
                <= execution_numeric["execution_risk_repair_scale"]
                <= 1
                or not math.isclose(
                    execution_numeric["execution_risk_observations"],
                    round(
                        execution_numeric["execution_risk_observations"]
                    ),
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                or (
                    execution_boolean[
                        "execution_risk_forecast_available"
                    ]
                    and execution_numeric[
                        "executed_risk_forecast_annualized"
                    ]
                    > execution_numeric[
                        "execution_risk_ceiling_annualized"
                    ]
                    + 1e-10
                )
                or (
                    execution_boolean["risk_rebalance_override"]
                    and (
                        execution_boolean["ordinary_rebalance"]
                        or raw["execution_reason"]
                        != "risk_ceiling_override"
                        or raw["rebalanced"] != "True"
                    )
                )
            ):
                _fail(
                    f"{path}:{index}",
                    "portfolio.execution-risk-value",
                    "Executed-book risk evidence is invalid",
                )
            execution_values: dict[str, Any] = {
                **execution_numeric,
                **execution_boolean,
                "execution_reason": raw["execution_reason"],
                "execution_risk_status": raw[
                    "execution_risk_status"
                ],
            }
        else:
            execution_values = {
                **{
                    key: 0.0
                    for key in EXECUTION_RISK_DAILY_FLOATS
                },
                **{
                    key: False
                    for key in EXECUTION_RISK_DAILY_BOOLEANS
                },
                "execution_reason": "legacy_unavailable",
                "execution_risk_status": "legacy_unavailable",
            }
        rows.append(
            {
                "timestamp": timestamp,
                **values,
                "cash_weight": cash_weight,
                "rebalanced": raw["rebalanced"] == "True",
                **execution_values,
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
    has_liquidity_columns = LIQUIDITY_DECISION_COLUMNS.issubset(fields)
    if LIQUIDITY_DECISION_COLUMNS & set(fields) and not has_liquidity_columns:
        _fail(
            path,
            "portfolio.liquidity-columns",
            "Decision ledger must contain the complete liquidity-capacity column set",
        )
    has_execution_risk_columns = EXECUTION_RISK_DECISION_COLUMNS.issubset(
        fields
    )
    if (
        EXECUTION_RISK_DECISION_COLUMNS & set(fields)
        and not has_execution_risk_columns
    ):
        _fail(
            path,
            "portfolio.execution-risk-columns",
            "Decision ledger must contain the complete execution-risk column set",
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
        liquidity_numeric = (
            {
                field: _finite(raw[field], f"{row_path}/{field}")
                for field in LIQUIDITY_DECISION_FLOATS
            }
            if has_liquidity_columns
            else {
                "liquidity_adv_observations": 0.0,
                "causal_adv_dollar_volume": 0.0,
                "reference_nav_adv_participation": 0.0,
                "asset_capacity_nav_1pct": 0.0,
                "asset_capacity_nav_5pct": 0.0,
                "portfolio_capacity_nav_1pct": 0.0,
                "portfolio_capacity_nav_5pct": 0.0,
            }
        )
        execution_risk_numeric = (
            {
                field: _finite(raw[field], f"{row_path}/{field}")
                for field in EXECUTION_RISK_DECISION_FLOATS
            }
            if has_execution_risk_columns
            else {
                field: 0.0 for field in EXECUTION_RISK_DECISION_FLOATS
            }
        )
        execution_risk_booleans: dict[str, bool] = {}
        if has_execution_risk_columns:
            for field in EXECUTION_RISK_DAILY_BOOLEANS:
                if raw[field] not in {"True", "False"}:
                    _fail(
                        f"{row_path}/{field}",
                        "portfolio.boolean",
                        f"{field} must be True or False",
                    )
                execution_risk_booleans[field] = raw[field] == "True"
            if not raw["execution_risk_status"]:
                _fail(
                    f"{row_path}/execution_risk_status",
                    "portfolio.execution-risk-status",
                    "Execution-risk status must be non-empty",
                )
        else:
            execution_risk_booleans = {
                field: False
                for field in EXECUTION_RISK_DAILY_BOOLEANS
            }
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
        if has_liquidity_columns and (
            raw["liquidity_capacity_status"]
            not in {
                "available",
                "no_trade",
                "insufficient_adv_history",
            }
            or raw["capacity_binding_asset"] not in {"True", "False"}
        ):
            _fail(
                row_path,
                "portfolio.liquidity-status",
                "Liquidity status or binding flag is invalid",
            )
        if has_execution_risk_columns and (
            any(value < 0 for value in execution_risk_numeric.values())
            or not 0
            <= execution_risk_numeric["proposed_runtime_risk_scale"]
            <= 1
            or not 0
            <= execution_risk_numeric["execution_risk_repair_scale"]
            <= 1
            or not math.isclose(
                execution_risk_numeric["execution_risk_observations"],
                round(
                    execution_risk_numeric[
                        "execution_risk_observations"
                    ]
                ),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or (
                execution_risk_booleans[
                    "execution_risk_forecast_available"
                ]
                and execution_risk_numeric[
                    "executed_risk_forecast_annualized"
                ]
                > execution_risk_numeric[
                    "execution_risk_ceiling_annualized"
                ]
                + 1e-10
            )
            or (
                execution_risk_booleans["risk_rebalance_override"]
                and (
                    execution_risk_booleans["ordinary_rebalance"]
                    or raw["execution_reason"] != "risk_ceiling_override"
                )
            )
        ):
            _fail(
                row_path,
                "portfolio.execution-risk-value",
                "Executed-book risk decision evidence is invalid",
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
        if (
            any(value < 0 for value in liquidity_numeric.values())
            or not math.isclose(
                liquidity_numeric["liquidity_adv_observations"],
                round(liquidity_numeric["liquidity_adv_observations"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            _fail(
                row_path,
                "portfolio.liquidity-value",
                "Liquidity-capacity numeric evidence is invalid",
            )
        if has_liquidity_columns:
            status = raw["liquidity_capacity_status"]
            trade = abs(numeric["trade_weight"])
            adv = liquidity_numeric["causal_adv_dollar_volume"]
            if status == "available" and trade > 1e-12:
                expected_participation = (
                    trade * LIQUIDITY_REFERENCE_NAV / adv
                    if adv > 0
                    else math.inf
                )
                expected_1pct = 0.01 * adv / trade
                if (
                    adv <= 0
                    or not math.isclose(
                        liquidity_numeric[
                            "reference_nav_adv_participation"
                        ],
                        expected_participation,
                        rel_tol=1e-10,
                        abs_tol=1e-8,
                    )
                    or not math.isclose(
                        liquidity_numeric["asset_capacity_nav_1pct"],
                        expected_1pct,
                        rel_tol=1e-10,
                        abs_tol=1e-6,
                    )
                    or not math.isclose(
                        liquidity_numeric["asset_capacity_nav_5pct"],
                        expected_1pct * 5.0,
                        rel_tol=1e-10,
                        abs_tol=1e-6,
                    )
                ):
                    _fail(
                        row_path,
                        "portfolio.liquidity-reconciliation",
                        "Asset liquidity-capacity evidence does not reconcile",
                    )
            elif any(
                liquidity_numeric[field] > 1e-12
                for field in (
                    "reference_nav_adv_participation",
                    "asset_capacity_nav_1pct",
                    "asset_capacity_nav_5pct",
                )
            ):
                _fail(
                    row_path,
                    "portfolio.liquidity-inactive",
                    "Unavailable or inactive asset capacity must be zero",
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
            **liquidity_numeric,
            **execution_risk_numeric,
            **execution_risk_booleans,
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
            "execution_risk_status": (
                raw["execution_risk_status"]
                if has_execution_risk_columns
                else "legacy_unavailable"
            ),
            "liquidity_capacity_status": (
                raw["liquidity_capacity_status"]
                if has_liquidity_columns
                else "legacy_unavailable"
            ),
            "capacity_binding_asset": (
                raw["capacity_binding_asset"] == "True"
                if has_liquidity_columns
                else False
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
        liquidity_signatures = {
            (
                item["liquidity_capacity_status"],
                item["portfolio_capacity_nav_1pct"],
                item["portfolio_capacity_nav_5pct"],
            )
            for item in rows
        }
        if len(liquidity_signatures) != 1:
            _fail(
                f"{path}/{timestamp}",
                "portfolio.liquidity-panel",
                "Liquidity-capacity evidence must be identical across one date",
            )
        execution_risk_signatures = {
            (
                item["execution_risk_status"],
                item["execution_risk_forecast_available"],
                item["execution_risk_observations"],
                item["pretrade_risk_forecast_annualized"],
                item["proposed_risk_forecast_pre_annualized"],
                item["proposed_risk_forecast_post_annualized"],
                item["executed_risk_forecast_annualized"],
                item["execution_risk_ceiling_annualized"],
                item["proposed_runtime_risk_scale"],
                item["execution_risk_repair_scale"],
                item["proposed_one_way_turnover"],
                item["ordinary_rebalance"],
                item["risk_rebalance_override"],
                item["execution_reason"],
            )
            for item in rows
        }
        if len(execution_risk_signatures) != 1:
            _fail(
                f"{path}/{timestamp}",
                "portfolio.execution-risk-panel",
                "Execution-risk evidence must be identical across one date",
            )
        execution_signature = next(iter(execution_risk_signatures))
        expected_execution_signature = (
            expected_daily["execution_risk_status"],
            expected_daily["execution_risk_forecast_available"],
            expected_daily["execution_risk_observations"],
            expected_daily["pretrade_risk_forecast_annualized"],
            expected_daily["proposed_risk_forecast_pre_annualized"],
            expected_daily["proposed_risk_forecast_post_annualized"],
            expected_daily["executed_risk_forecast_annualized"],
            expected_daily["execution_risk_ceiling_annualized"],
            expected_daily["proposed_runtime_risk_scale"],
            expected_daily["execution_risk_repair_scale"],
            expected_daily["proposed_one_way_turnover"],
            expected_daily["ordinary_rebalance"],
            expected_daily["risk_rebalance_override"],
            expected_daily["execution_reason"],
        )
        if execution_signature[0] != "legacy_unavailable":
            for actual, expected_value in zip(
                execution_signature,
                expected_execution_signature,
            ):
                if isinstance(actual, float):
                    matches = math.isclose(
                        actual,
                        float(expected_value),
                        rel_tol=1e-10,
                        abs_tol=1e-10,
                    )
                else:
                    matches = actual == expected_value
                if not matches:
                    _fail(
                        f"{path}/{timestamp}",
                        "portfolio.execution-risk-daily",
                        "Decision execution-risk evidence differs from daily evidence",
                    )
        status, capacity_1pct, capacity_5pct = next(
            iter(liquidity_signatures)
        )
        active_rows = [
            item for item in rows if abs(item["trade_weight"]) > 1e-12
        ]
        binding_rows = [
            item for item in rows if item["capacity_binding_asset"]
        ]
        if status == "available":
            if (
                not active_rows
                or len(binding_rows) != 1
                or capacity_1pct <= 0
                or not math.isclose(
                    capacity_5pct,
                    capacity_1pct * 5.0,
                    rel_tol=1e-10,
                    abs_tol=1e-6,
                )
                or not math.isclose(
                    binding_rows[0]["asset_capacity_nav_1pct"],
                    capacity_1pct,
                    rel_tol=1e-10,
                    abs_tol=1e-6,
                )
            ):
                _fail(
                    f"{path}/{timestamp}",
                    "portfolio.liquidity-binding",
                    "Available capacity must reconcile one binding active asset",
                )
        elif status == "no_trade":
            if active_rows or binding_rows or capacity_1pct or capacity_5pct:
                _fail(
                    f"{path}/{timestamp}",
                    "portfolio.liquidity-no-trade",
                    "No-trade capacity evidence is inconsistent",
                )
        elif status == "insufficient_adv_history":
            if (
                not active_rows
                or binding_rows
                or capacity_1pct
                or capacity_5pct
                or all(
                    item["causal_adv_dollar_volume"] > 0
                    for item in active_rows
                )
            ):
                _fail(
                    f"{path}/{timestamp}",
                    "portfolio.liquidity-unavailable",
                    "Incomplete active ADV must not publish capacity",
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
        has_trade = (
            sum(abs(item["trade_weight"]) for item in rows) > 1e-12
        )
        if has_trade != bool(expected_daily["rebalanced"]):
            _fail(
                f"{path}/{timestamp}",
                "portfolio.rebalance-reconciliation",
                "Daily rebalance flag differs from the exact trade vector",
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


def _parameter_configuration_id(profile_id: str, band: float) -> str:
    return f"{profile_id}__band-{int(round(band * 100)):03d}"


def _compare_parameter_value(
    actual: Any,
    expected: Any,
    path: str,
) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            _fail(
                path,
                "portfolio.parameter-neighborhood-metric",
                "Parameter-neighborhood metric keys do not reconcile",
            )
        for key, expected_value in expected.items():
            _compare_parameter_value(
                actual[key],
                expected_value,
                f"{path}/{key}",
            )
        return
    if isinstance(expected, bool):
        if actual is not expected:
            _fail(
                path,
                "portfolio.parameter-neighborhood-metric",
                "Parameter-neighborhood boolean does not reconcile",
            )
        return
    if isinstance(expected, (int, float)):
        if (
            not isinstance(actual, (int, float))
            or isinstance(actual, bool)
            or not math.isclose(
                float(actual),
                float(expected),
                rel_tol=1e-9,
                abs_tol=1e-11,
            )
        ):
            _fail(
                path,
                "portfolio.parameter-neighborhood-metric",
                "Parameter-neighborhood numeric value does not reconcile",
            )
        return
    if actual != expected:
        _fail(
            path,
            "portfolio.parameter-neighborhood-metric",
            "Parameter-neighborhood value does not reconcile",
        )


def _parameter_neighborhood_projection(
    result: dict[str, Any],
    artifact_path: Path | None,
    daily: ParsedDaily,
    splits: dict[str, Any],
) -> dict[str, Any]:
    metric = result["metrics"].get("parameter_neighborhood")
    if metric is None and artifact_path is None:
        return {
            "available": False,
            "policy": None,
            "validation": None,
            "test": None,
        }
    if not isinstance(metric, dict) or artifact_path is None:
        _fail(
            "RunResult/metrics/parameter_neighborhood",
            "portfolio.parameter-neighborhood-availability",
            "Parameter-neighborhood metric and artifact must appear together",
        )
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail(
            artifact_path,
            "portfolio.parameter-neighborhood-json",
            "Parameter-neighborhood artifact must be UTF-8 JSON",
        )
    if not isinstance(payload, dict) or set(payload) != {
        "schemaVersion",
        "inputHash",
        "method",
        "baseConfigurationId",
        "signalProfiles",
        "noTradeBands",
        "rows",
    }:
        _fail(
            artifact_path,
            "portfolio.parameter-neighborhood-shape",
            "Parameter-neighborhood artifact has an unexpected root shape",
        )
    if (
        payload["schemaVersion"] != 1
        or payload["inputHash"] != result["inputHash"]
        or payload["method"] != PARAMETER_NEIGHBORHOOD_METHOD
        or payload["baseConfigurationId"]
        != PARAMETER_BASE_CONFIGURATION_ID
        or payload["signalProfiles"] != list(PARAMETER_SIGNAL_PROFILES)
        or payload["noTradeBands"] != list(PARAMETER_NO_TRADE_BANDS)
    ):
        _fail(
            artifact_path,
            "portfolio.parameter-neighborhood-contract",
            "Parameter-neighborhood fixed contract does not reconcile",
        )
    raw_rows = payload["rows"]
    if (
        not isinstance(raw_rows, list)
        or len(raw_rows) > MAX_NEIGHBORHOOD_ROWS
    ):
        _fail(
            artifact_path,
            "portfolio.parameter-neighborhood-rows",
            "Parameter-neighborhood rows exceed the bounded JSON contract",
        )
    row_fields = {
        "configurationId",
        "signalProfile",
        "noTradeOneWay",
        "split",
        "role",
        "timestamp",
        "netReturn",
        "benchmarkReturn",
        "oneWayTurnover",
        "cost",
        "rebalanced",
        "signalDecisionRows",
        "signalTransitions",
        "entries",
        "exits",
        "reversals",
    }
    configuration_ids = [
        _parameter_configuration_id(profile["id"], band)
        for profile in PARAMETER_SIGNAL_PROFILES
        for band in PARAMETER_NO_TRADE_BANDS
    ]
    profile_by_configuration = {
        _parameter_configuration_id(profile["id"], band): (
            profile["id"],
            band,
        )
        for profile in PARAMETER_SIGNAL_PROFILES
        for band in PARAMETER_NO_TRADE_BANDS
    }
    daily_dates = set(daily.dates)
    expected_dates = {
        split: [
            timestamp
            for timestamp in daily.dates
            if (
                splits[split]["start"]
                <= timestamp
                <= splits[split]["signalEnd"]
            )
        ]
        for split in ("validation", "test")
    }
    expected_order = [
        (configuration_id, split, timestamp)
        for configuration_id in configuration_ids
        for split in ("validation", "test")
        for timestamp in expected_dates[split]
    ]
    if len(raw_rows) != len(expected_order):
        _fail(
            artifact_path,
            "portfolio.parameter-neighborhood-coverage",
            "Parameter-neighborhood rows do not cover every fixed cell/date",
        )
    parsed: dict[tuple[str, str], list[dict[str, Any]]] = {
        (configuration_id, split): []
        for configuration_id in configuration_ids
        for split in ("validation", "test")
    }
    observed_order: list[tuple[str, str, str]] = []
    for index, row in enumerate(raw_rows):
        path = f"{artifact_path}/rows/{index}"
        if not isinstance(row, dict) or set(row) != row_fields:
            _fail(
                path,
                "portfolio.parameter-neighborhood-row",
                "Parameter-neighborhood row has an unexpected shape",
            )
        configuration_id = row["configurationId"]
        split = row["split"]
        timestamp = _session_date(row["timestamp"], f"{path}/timestamp")
        if (
            configuration_id not in profile_by_configuration
            or split not in {"validation", "test"}
            or timestamp not in daily_dates
        ):
            _fail(
                path,
                "portfolio.parameter-neighborhood-identity",
                "Parameter-neighborhood row identity is outside the fixed panel",
            )
        profile_id, band = profile_by_configuration[configuration_id]
        expected_role = (
            "selection-context"
            if split == "validation"
            else "visible-audit"
        )
        if (
            row["signalProfile"] != profile_id
            or not isinstance(row["noTradeOneWay"], (int, float))
            or isinstance(row["noTradeOneWay"], bool)
            or not math.isclose(
                float(row["noTradeOneWay"]),
                float(band),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or row["role"] != expected_role
        ):
            _fail(
                path,
                "portfolio.parameter-neighborhood-identity",
                "Parameter-neighborhood row parameters do not reconcile",
            )
        numeric = {
            key: _finite(row[key], f"{path}/{key}")
            for key in (
                "netReturn",
                "benchmarkReturn",
                "oneWayTurnover",
                "cost",
            )
        }
        if numeric["oneWayTurnover"] < 0 or numeric["cost"] < 0:
            _fail(
                path,
                "portfolio.parameter-neighborhood-accounting",
                "Turnover and cost must be non-negative",
            )
        if type(row["rebalanced"]) is not bool:
            _fail(
                f"{path}/rebalanced",
                "portfolio.parameter-neighborhood-accounting",
                "Rebalanced must be boolean",
            )
        counts: dict[str, int] = {}
        for key in (
            "signalDecisionRows",
            "signalTransitions",
            "entries",
            "exits",
            "reversals",
        ):
            value = row[key]
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                _fail(
                    f"{path}/{key}",
                    "portfolio.parameter-neighborhood-signal",
                    "Signal counts must be non-negative integers",
                )
            counts[key] = value
        if (
            counts["signalTransitions"]
            > counts["signalDecisionRows"]
            or counts["entries"]
            + counts["exits"]
            + counts["reversals"]
            > counts["signalTransitions"]
        ):
            _fail(
                path,
                "portfolio.parameter-neighborhood-signal",
                "Signal transition counts are internally inconsistent",
            )
        observed_order.append((configuration_id, split, timestamp))
        parsed[(configuration_id, split)].append(
            {
                "timestamp": timestamp,
                **numeric,
                "rebalanced": row["rebalanced"],
                **counts,
            }
        )
    if observed_order != expected_order:
        _fail(
            artifact_path,
            "portfolio.parameter-neighborhood-order",
            "Parameter-neighborhood rows must follow the fixed deterministic order",
        )

    reconstructed: dict[str, dict[str, Any]] = {
        "validation": {},
        "test": {},
    }
    for configuration_id in configuration_ids:
        for split in ("validation", "test"):
            rows = parsed[(configuration_id, split)]
            frame = pd.DataFrame(rows).set_index("timestamp")
            performance = performance_metrics(
                frame["netReturn"],
                frame["benchmarkReturn"],
            )
            decision_rows = int(frame["signalDecisionRows"].sum())
            transitions = int(frame["signalTransitions"].sum())
            implementation = {
                "mean_one_way_turnover": float(
                    frame["oneWayTurnover"].mean()
                ),
                "annualized_one_way_turnover": float(
                    frame["oneWayTurnover"].mean() * 252
                ),
                "total_cost_drag": float(frame["cost"].sum()),
                "rebalance_rate": float(frame["rebalanced"].mean()),
                "no_trade_rate": float((~frame["rebalanced"]).mean()),
            }
            signal = {
                "decision_rows": decision_rows,
                "timestamps": int(len(frame)),
                "signal_transitions": transitions,
                "state_change_rate": (
                    float(transitions / decision_rows)
                    if decision_rows
                    else 0.0
                ),
                "entries": int(frame["entries"].sum()),
                "exits": int(frame["exits"].sum()),
                "reversals": int(frame["reversals"].sum()),
            }
            reconstructed[split][configuration_id] = {
                "performance": performance,
                "implementation": implementation,
                "signal": signal,
            }

    expected_metric: dict[str, Any] = {}
    for split in ("validation", "test"):
        base = reconstructed[split][PARAMETER_BASE_CONFIGURATION_ID]
        for configuration_id in configuration_ids:
            current = reconstructed[split][configuration_id]
            current["delta_vs_base"] = {
                "net_sharpe": (
                    current["performance"]["sharpe"]
                    - base["performance"]["sharpe"]
                ),
                "total_return": (
                    current["performance"]["total_return"]
                    - base["performance"]["total_return"]
                ),
                "annualized_one_way_turnover": (
                    current["implementation"][
                        "annualized_one_way_turnover"
                    ]
                    - base["implementation"][
                        "annualized_one_way_turnover"
                    ]
                ),
                "total_cost_drag": (
                    current["implementation"]["total_cost_drag"]
                    - base["implementation"]["total_cost_drag"]
                ),
                "signal_transitions": (
                    current["signal"]["signal_transitions"]
                    - base["signal"]["signal_transitions"]
                ),
            }
        sharpes = [
            reconstructed[split][configuration_id]["performance"]["sharpe"]
            for configuration_id in configuration_ids
        ]
        base_sharpe = base["performance"]["sharpe"]
        turnovers = [
            reconstructed[split][configuration_id]["implementation"][
                "annualized_one_way_turnover"
            ]
            for configuration_id in configuration_ids
        ]
        costs = [
            reconstructed[split][configuration_id]["implementation"][
                "total_cost_drag"
            ]
            for configuration_id in configuration_ids
        ]
        transitions = [
            reconstructed[split][configuration_id]["signal"][
                "signal_transitions"
            ]
            for configuration_id in configuration_ids
        ]
        base_sign = 1 if base_sharpe > 0 else -1 if base_sharpe < 0 else 0
        expected_metric[split] = {
            "configurations": reconstructed[split],
            "aggregate": {
                "configuration_count": len(configuration_ids),
                "base_net_sharpe": base_sharpe,
                "positive_net_sharpe_rate": float(
                    sum(value > 0 for value in sharpes) / len(sharpes)
                ),
                "sign_agreement_with_base_rate": float(
                    sum(
                        (
                            1
                            if value > 0
                            else -1
                            if value < 0
                            else 0
                        )
                        == base_sign
                        for value in sharpes
                    )
                    / len(sharpes)
                ),
                "minimum_net_sharpe": min(sharpes),
                "median_net_sharpe": float(pd.Series(sharpes).median()),
                "maximum_net_sharpe": max(sharpes),
                "net_sharpe_std": float(
                    pd.Series(sharpes).std(ddof=0)
                ),
                "worst_net_sharpe_delta": min(
                    value - base_sharpe for value in sharpes
                ),
                "best_net_sharpe_delta": max(
                    value - base_sharpe for value in sharpes
                ),
                "minimum_annualized_one_way_turnover": min(turnovers),
                "maximum_annualized_one_way_turnover": max(turnovers),
                "minimum_total_cost_drag": min(costs),
                "maximum_total_cost_drag": max(costs),
                "minimum_signal_transitions": min(transitions),
                "maximum_signal_transitions": max(transitions),
            },
        }
    expected_policy = {
        "method": PARAMETER_NEIGHBORHOOD_METHOD,
        "base_configuration_id": PARAMETER_BASE_CONFIGURATION_ID,
        "role": "robustness-only",
        "selection_authority": "context-only",
        "trading_authority": "none",
        "configuration_count": len(configuration_ids),
        "signal_profiles": [
            {
                "id": profile["id"],
                "label": profile["label"],
                "long_entry": profile["longEntry"],
                "long_exit": profile["longExit"],
                "short_exit": profile["shortExit"],
                "short_entry": profile["shortEntry"],
            }
            for profile in PARAMETER_SIGNAL_PROFILES
        ],
        "no_trade_bands": list(PARAMETER_NO_TRADE_BANDS),
    }
    _compare_parameter_value(
        metric,
        {
            "policy": expected_policy,
            "validation": expected_metric["validation"],
            "test": expected_metric["test"],
        },
        "RunResult/metrics/parameter_neighborhood",
    )
    for split in ("validation", "test"):
        base_reconciliation = {
            "performance": result["metrics"]["portfolio"][split]["net"],
            "implementation": {
                key: result["metrics"]["implementation"][split][key]
                for key in (
                    "mean_one_way_turnover",
                    "annualized_one_way_turnover",
                    "total_cost_drag",
                    "rebalance_rate",
                    "no_trade_rate",
                )
            },
            "signal": {
                key: result["metrics"]["signal_policy"][split][key]
                for key in (
                    "decision_rows",
                    "timestamps",
                    "signal_transitions",
                    "state_change_rate",
                    "entries",
                    "exits",
                    "reversals",
                )
            },
        }
        _compare_parameter_value(
            reconstructed[split][PARAMETER_BASE_CONFIGURATION_ID],
            {
                **base_reconciliation,
                "delta_vs_base": {
                    "net_sharpe": 0.0,
                    "total_return": 0.0,
                    "annualized_one_way_turnover": 0.0,
                    "total_cost_drag": 0.0,
                    "signal_transitions": 0,
                },
            },
            f"RunResult/metrics/parameter_neighborhood/base/{split}",
        )

    def split_projection(split: str) -> dict[str, Any]:
        aggregate = expected_metric[split]["aggregate"]
        return {
            "aggregate": {
                "configurationCount": aggregate["configuration_count"],
                "baseNetSharpe": aggregate["base_net_sharpe"],
                "positiveNetSharpeRate": aggregate[
                    "positive_net_sharpe_rate"
                ],
                "signAgreementWithBaseRate": aggregate[
                    "sign_agreement_with_base_rate"
                ],
                "minimumNetSharpe": aggregate["minimum_net_sharpe"],
                "medianNetSharpe": aggregate["median_net_sharpe"],
                "maximumNetSharpe": aggregate["maximum_net_sharpe"],
                "netSharpeStd": aggregate["net_sharpe_std"],
                "worstNetSharpeDelta": aggregate[
                    "worst_net_sharpe_delta"
                ],
                "bestNetSharpeDelta": aggregate[
                    "best_net_sharpe_delta"
                ],
                "minimumAnnualizedOneWayTurnover": aggregate[
                    "minimum_annualized_one_way_turnover"
                ],
                "maximumAnnualizedOneWayTurnover": aggregate[
                    "maximum_annualized_one_way_turnover"
                ],
                "minimumTotalCostDrag": aggregate[
                    "minimum_total_cost_drag"
                ],
                "maximumTotalCostDrag": aggregate[
                    "maximum_total_cost_drag"
                ],
                "minimumSignalTransitions": aggregate[
                    "minimum_signal_transitions"
                ],
                "maximumSignalTransitions": aggregate[
                    "maximum_signal_transitions"
                ],
            },
            "configurations": [
                {
                    "id": configuration_id,
                    "signalProfile": profile_by_configuration[
                        configuration_id
                    ][0],
                    "noTradeOneWay": profile_by_configuration[
                        configuration_id
                    ][1],
                    "isBase": (
                        configuration_id
                        == PARAMETER_BASE_CONFIGURATION_ID
                    ),
                    "netSharpe": reconstructed[split][configuration_id][
                        "performance"
                    ]["sharpe"],
                    "totalReturn": reconstructed[split][configuration_id][
                        "performance"
                    ]["total_return"],
                    "annualizedOneWayTurnover": reconstructed[split][
                        configuration_id
                    ]["implementation"]["annualized_one_way_turnover"],
                    "totalCostDrag": reconstructed[split][configuration_id][
                        "implementation"
                    ]["total_cost_drag"],
                    "rebalanceRate": reconstructed[split][configuration_id][
                        "implementation"
                    ]["rebalance_rate"],
                    "signalTransitions": reconstructed[split][
                        configuration_id
                    ]["signal"]["signal_transitions"],
                    "netSharpeDeltaVsBase": reconstructed[split][
                        configuration_id
                    ]["delta_vs_base"]["net_sharpe"],
                }
                for configuration_id in configuration_ids
            ],
        }

    return {
        "available": True,
        "policy": {
            "method": PARAMETER_NEIGHBORHOOD_METHOD,
            "baseConfigurationId": PARAMETER_BASE_CONFIGURATION_ID,
            "role": "robustness-only",
            "selectionAuthority": "context-only",
            "tradingAuthority": "none",
            "configurationCount": len(configuration_ids),
            "signalProfiles": list(PARAMETER_SIGNAL_PROFILES),
            "noTradeBands": list(PARAMETER_NO_TRADE_BANDS),
        },
        "validation": split_projection("validation"),
        "test": split_projection("test"),
    }


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
                "executedRiskForecastAnnualized": row[
                    "executed_risk_forecast_annualized"
                ],
                "executionRiskCeilingAnnualized": row[
                    "execution_risk_ceiling_annualized"
                ],
                "riskRebalanceOverride": row[
                    "risk_rebalance_override"
                ],
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


def _trigger_candidate(
    event: str,
    comparator: str,
    threshold: float,
    score: float | None,
) -> dict[str, Any]:
    if comparator not in {">=", ">", "<=", "<"}:
        raise ValueError("Unknown trigger comparator")
    if score is None:
        distance = None
    elif comparator in {">=", ">"}:
        distance = max(0.0, threshold - score)
    else:
        distance = max(0.0, score - threshold)
    return {
        "event": event,
        "comparator": comparator,
        "threshold": threshold,
        "distance": distance,
    }


def _next_signal_triggers(
    *,
    family: str,
    signal_state: int,
    score: float | None,
    parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    long_entry = parameters["long_entry_percentile"]
    long_exit = parameters["long_exit_percentile"]
    short_exit = parameters["short_exit_percentile"]
    short_entry = parameters["short_entry_percentile"]
    if family == "long-cash":
        if signal_state not in {0, 1}:
            _fail(
                "mechanicalDecision/signalState",
                "portfolio.mechanical-state",
                "Long/cash evidence cannot carry short signal intent",
            )
        return [
            _trigger_candidate(
                "exit_long" if signal_state == 1 else "enter_long",
                "<" if signal_state == 1 else ">=",
                long_exit if signal_state == 1 else long_entry,
                score,
            )
        ]
    if family == "short-cash":
        if signal_state not in {-1, 0}:
            _fail(
                "mechanicalDecision/signalState",
                "portfolio.mechanical-state",
                "Short/cash evidence cannot carry long signal intent",
            )
        return [
            _trigger_candidate(
                "exit_short" if signal_state == -1 else "enter_short",
                ">" if signal_state == -1 else "<=",
                short_exit if signal_state == -1 else short_entry,
                score,
            )
        ]
    if family != "dollar-neutral":
        _fail(
            "mechanicalDecision/family",
            "portfolio.mechanical-family",
            "Unknown mechanical construction family",
        )
    if signal_state == 1:
        return [
            _trigger_candidate("exit_long", "<", long_exit, score),
            _trigger_candidate(
                "reverse_long_to_short",
                "<=",
                short_entry,
                score,
            ),
        ]
    if signal_state == -1:
        return [
            _trigger_candidate("exit_short", ">", short_exit, score),
            _trigger_candidate(
                "reverse_short_to_long",
                ">=",
                long_entry,
                score,
            ),
        ]
    if signal_state == 0:
        return [
            _trigger_candidate("enter_long", ">=", long_entry, score),
            _trigger_candidate("enter_short", "<=", short_entry, score),
        ]
    _fail(
        "mechanicalDecision/signalState",
        "portfolio.mechanical-state",
        "Signal state must be -1, 0, or 1",
    )


def _mechanical_decision_projection(
    daily: ParsedDaily,
    universe: list[str],
    decisions: dict[tuple[str, str], dict[str, Any]],
    signal_policy: dict[str, Any],
    mandate: dict[str, Any],
) -> dict[str, Any]:
    """Build one research-only current decision chain from verified evidence."""

    parameters = signal_policy["parameters"]
    timestamp = daily.dates[-1]
    daily_row = daily.rows[-1]
    family = mandate["family"]
    positions: list[dict[str, Any]] = []
    pre_governor_gross = 0.0
    governed_target_gross = 0.0
    pretrade_gross = 0.0
    executed_gross = 0.0
    computed_proposed_one_way = 0.0
    state_changes = 0
    unavailable_scores = 0
    context_assets = 0
    position_execution_reasons: set[str] = set()
    inactive_events = {
        "hold_long",
        "hold_short",
        "stay_flat",
        "unavailable_flat",
        "unavailable_reset",
        "context_only",
    }
    for asset in universe:
        item = decisions[(timestamp, asset)]
        score = item["percentile_score"]
        if score is not None and not 0.0 <= score <= 1.0:
            _fail(
                f"mechanicalDecision/positions/{asset}/score",
                "portfolio.mechanical-score",
                "Current percentile score must be within [0, 1]",
            )
        if not item["tradable"]:
            context_assets += 1
            if item["signal_state"] != 0:
                _fail(
                    f"mechanicalDecision/positions/{asset}/signalState",
                    "portfolio.mechanical-context-state",
                    "Context-only assets must remain flat",
                )
            trigger_candidates: list[dict[str, Any]] = []
        else:
            trigger_candidates = _next_signal_triggers(
                family=family,
                signal_state=item["signal_state"],
                score=score,
                parameters=parameters,
            )
        available_candidates = [
            candidate
            for candidate in trigger_candidates
            if candidate["distance"] is not None
        ]
        nearest = (
            min(
                available_candidates,
                key=lambda candidate: (
                    candidate["distance"],
                    trigger_candidates.index(candidate),
                ),
            )
            if available_candidates
            else None
        )
        proposed_trade = (
            item["proposed_target_weight"] - item["pretrade_weight"]
        )
        pre_governor_gross += abs(item["pre_governor_target_weight"])
        governed_target_gross += abs(item["proposed_target_weight"])
        pretrade_gross += abs(item["pretrade_weight"])
        executed_gross += abs(item["executed_weight"])
        computed_proposed_one_way += 0.5 * abs(proposed_trade)
        position_execution_reasons.add(item["execution_reason"])
        state_changes += int(item["signal_event"] not in inactive_events)
        unavailable_scores += int(item["tradable"] and score is None)
        positions.append(
            {
                "asset": asset,
                "tradable": item["tradable"],
                "allocationStatus": item["allocation_status"],
                "score": score,
                "scoreAvailable": score is not None,
                "signalState": item["signal_state"],
                "signalEvent": item["signal_event"],
                "nextTriggers": trigger_candidates,
                "nearestTrigger": nearest,
                "preGovernorTargetWeight": item[
                    "pre_governor_target_weight"
                ],
                "targetWeight": item["proposed_target_weight"],
                "pretradeWeight": item["pretrade_weight"],
                "proposedTradeWeight": proposed_trade,
                "executedWeight": item["executed_weight"],
                "tradeWeight": item["trade_weight"],
                "executionAction": item["execution_action"],
                "executionReason": item["execution_reason"],
            }
        )
    execution_available = (
        daily_row["execution_risk_status"] != "legacy_unavailable"
    )
    if len(position_execution_reasons) != 1:
        _fail(
            "mechanicalDecision/executionGate/reason",
            "portfolio.mechanical-execution-reason",
            "Current asset execution reasons must agree",
        )
    position_execution_reason = next(iter(position_execution_reasons))
    if (
        execution_available
        and position_execution_reason != daily_row["execution_reason"]
    ):
        _fail(
            "mechanicalDecision/executionGate/reason",
            "portfolio.mechanical-execution-reason",
            "Current asset and portfolio execution reasons differ",
        )
    recorded_proposed_one_way = daily_row["proposed_one_way_turnover"]
    if execution_available and not math.isclose(
        computed_proposed_one_way,
        recorded_proposed_one_way,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        _fail(
            "mechanicalDecision/executionGate/proposedOneWayTurnover",
            "portfolio.mechanical-turnover",
            "Current target-to-pretrade turnover does not reconcile",
        )
    no_trade_one_way = parameters["no_trade_one_way"]
    proposed_one_way = (
        recorded_proposed_one_way
        if execution_available
        else computed_proposed_one_way
    )
    return {
        "method": MECHANICAL_DECISION_METHOD,
        "timestamp": timestamp,
        "authority": "quantitative-decision-support",
        "tradingAuthority": "none",
        "distanceSemantics": PERCENTILE_DISTANCE_SEMANTICS,
        "signalGate": {
            "family": family,
            "stateChanges": state_changes,
            "unavailableScores": unavailable_scores,
            "contextAssets": context_assets,
            "longEntryPercentile": parameters[
                "long_entry_percentile"
            ],
            "longExitPercentile": parameters[
                "long_exit_percentile"
            ],
            "shortExitPercentile": parameters[
                "short_exit_percentile"
            ],
            "shortEntryPercentile": parameters[
                "short_entry_percentile"
            ],
        },
        "targetGate": {
            "preGovernorGross": pre_governor_gross,
            "governedTargetGross": governed_target_gross,
            "pretradeGross": pretrade_gross,
            "riskGovernorStatus": decisions[
                (timestamp, universe[0])
            ]["risk_governor_status"],
            "riskGovernorScale": decisions[
                (timestamp, universe[0])
            ]["risk_governor_scale"],
            "riskLimited": decisions[
                (timestamp, universe[0])
            ]["risk_governor_scale"]
            < 1.0 - 1e-12,
        },
        "executionGate": {
            "available": execution_available,
            "noTradeOneWay": no_trade_one_way,
            "proposedOneWayTurnover": proposed_one_way,
            "bandShortfall": max(0.0, no_trade_one_way - proposed_one_way),
            "bandExcess": max(0.0, proposed_one_way - no_trade_one_way),
            "ordinaryRebalance": (
                daily_row["ordinary_rebalance"]
                if execution_available
                else None
            ),
            "riskOverride": (
                daily_row["risk_rebalance_override"]
                if execution_available
                else None
            ),
            "rebalanced": daily_row["rebalanced"],
            "finalOneWayTurnover": daily_row["one_way_turnover"],
            "executedGross": executed_gross,
            "reason": (
                daily_row["execution_reason"]
                if execution_available
                else position_execution_reason
            ),
            "status": daily_row["execution_risk_status"],
        },
        "positions": positions,
    }


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
        "executionRiskStatus": daily_row["execution_risk_status"],
        "executionRiskForecastAvailable": daily_row[
            "execution_risk_forecast_available"
        ],
        "pretradeRiskForecastAnnualized": daily_row[
            "pretrade_risk_forecast_annualized"
        ],
        "executedRiskForecastAnnualized": daily_row[
            "executed_risk_forecast_annualized"
        ],
        "executionRiskCeilingAnnualized": daily_row[
            "execution_risk_ceiling_annualized"
        ],
        "riskRebalanceOverride": daily_row[
            "risk_rebalance_override"
        ],
        "executionReason": daily_row["execution_reason"],
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
    required_parameters = set(EXPECTED_SIGNAL_PARAMETERS)
    if set(parameters) != required_parameters:
        _fail(
            "RunResult/metrics/signal_policy/parameters",
            "portfolio.signal-policy-parameters",
            "Signal-policy parameters differ from the fixed contract",
        )
    normalized_parameters = {
        key: _finite(
            parameters[key],
            f"RunResult/metrics/signal_policy/parameters/{key}",
        )
        for key in required_parameters
    }
    if (
        not 0.0
        <= normalized_parameters["short_entry_percentile"]
        <= normalized_parameters["short_exit_percentile"]
        < normalized_parameters["long_exit_percentile"]
        <= normalized_parameters["long_entry_percentile"]
        <= 1.0
        or normalized_parameters["volatility_window"] < 2
        or not math.isclose(
            normalized_parameters["volatility_window"],
            round(normalized_parameters["volatility_window"]),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        or not 0.0 < normalized_parameters["gross_target"] <= 2.0
        or not 0.0
        < normalized_parameters["max_abs_weight"]
        <= normalized_parameters["gross_target"]
        or not 0.0 <= normalized_parameters["no_trade_one_way"] <= 1.0
    ):
        _fail(
            "RunResult/metrics/signal_policy/parameters",
            "portfolio.signal-policy-parameters",
            "Signal-policy parameters are invalid",
        )
    normalized_parameters["volatility_window"] = int(
        normalized_parameters["volatility_window"]
    )
    if normalized_parameters != EXPECTED_SIGNAL_PARAMETERS:
        _fail(
            "RunResult/metrics/signal_policy/parameters",
            "portfolio.signal-policy-parameters",
            "Signal-policy parameters differ from the fixed contract",
        )
    output: dict[str, Any] = {"parameters": normalized_parameters}
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


def _executed_book_risk_projection(
    result: dict[str, Any],
    daily: ParsedDaily,
    splits: dict[str, Any],
    mandate: dict[str, Any],
) -> dict[str, Any]:
    raw = result["metrics"].get("execution_risk")
    has_daily = any(
        row["execution_risk_status"] != "legacy_unavailable"
        for row in daily.rows
    )
    if raw is None and not has_daily:
        return {
            "available": False,
            "policy": None,
            "selectionAuthority": "context-only",
            "validation": None,
            "test": None,
            "latest": None,
        }
    if not isinstance(raw, dict) or not has_daily:
        _fail(
            "RunResult/metrics/execution_risk",
            "portfolio.execution-risk",
            "Execution-risk metrics and daily evidence must exist together",
        )
    policy = raw.get("policy")
    expected_policy = {
        "method": (
            "post-drift-executed-book-volatility-compliance-v1"
        ),
        "risk_policy": mandate["riskPolicy"],
        "no_trade_priority": "risk-compliance-first",
        "repair": "minimum-proportional-scale-down",
        "selection_authority": "context-only",
        "trading_authority": "none",
    }
    if policy != expected_policy:
        _fail(
            "RunResult/metrics/execution_risk/policy",
            "portfolio.execution-risk-policy",
            "Executed-book risk policy differs from the fixed contract",
        )

    def derive(split_name: str) -> dict[str, Any]:
        split = splits[split_name]
        dated = [
            row
            for row in daily.rows
            if split["start"]
            <= row["timestamp"]
            <= split["signalEnd"]
        ]
        active = [
            row
            for row in dated
            if (
                abs(row["gross_exposure"]) > 1e-12
                or abs(row["proposed_one_way_turnover"]) > 1e-12
                or row["risk_rebalance_override"]
            )
        ]
        available = [
            row
            for row in active
            if row["execution_risk_forecast_available"]
        ]
        unavailable = [
            row
            for row in active
            if not row["execution_risk_forecast_available"]
        ]
        pretrade_breach = [
            row
            for row in available
            if row["pretrade_risk_forecast_annualized"]
            > row["execution_risk_ceiling_annualized"] + 1e-10
        ]
        executed_breach = [
            row
            for row in available
            if row["executed_risk_forecast_annualized"]
            > row["execution_risk_ceiling_annualized"] + 1e-10
        ]
        overrides = [
            row for row in active if row["risk_rebalance_override"]
        ]
        errors = [
            max(
                0.0,
                row["executed_risk_forecast_annualized"]
                - row["execution_risk_ceiling_annualized"],
            )
            for row in available
        ]
        status_counts: dict[str, int] = {}
        reason_counts: dict[str, int] = {}
        for row in dated:
            status = row["execution_risk_status"]
            reason = row["execution_reason"]
            status_counts[status] = status_counts.get(status, 0) + 1
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        return {
            "status": (
                "available"
                if available
                else "no_active_dates"
                if not active
                else "forecast_unavailable"
            ),
            "dates": len(dated),
            "active_dates": len(active),
            "forecast_available_dates": len(available),
            "forecast_unavailable_dates": len(unavailable),
            "forecast_coverage": (
                len(available) / len(active) if active else 0.0
            ),
            "pretrade_breach_dates": len(pretrade_breach),
            "pretrade_breach_rate": (
                len(pretrade_breach) / len(available)
                if available
                else 0.0
            ),
            "risk_rebalance_override_dates": len(overrides),
            "risk_rebalance_override_rate": (
                len(overrides) / len(active) if active else 0.0
            ),
            "executed_breach_dates": len(executed_breach),
            "executed_breach_rate": (
                len(executed_breach) / len(available)
                if available
                else 0.0
            ),
            "mean_executed_forecast_annualized": (
                sum(
                    row["executed_risk_forecast_annualized"]
                    for row in available
                )
                / len(available)
                if available
                else 0.0
            ),
            "maximum_executed_forecast_annualized": (
                max(
                    row["executed_risk_forecast_annualized"]
                    for row in available
                )
                if available
                else 0.0
            ),
            "maximum_ceiling_error": max(errors) if errors else 0.0,
            "status_counts": status_counts,
            "execution_reason_counts": reason_counts,
        }

    def compare(expected: Any, actual: Any, path: str) -> None:
        if isinstance(actual, dict):
            if not isinstance(expected, dict) or set(expected) != set(actual):
                _fail(
                    path,
                    "portfolio.execution-risk-metrics",
                    "Execution-risk metric shape differs from daily evidence",
                )
            for key, value in actual.items():
                compare(expected[key], value, f"{path}/{key}")
        elif isinstance(actual, float):
            if not math.isclose(
                _finite(expected, path),
                actual,
                rel_tol=1e-10,
                abs_tol=1e-10,
            ):
                _fail(
                    path,
                    "portfolio.execution-risk-metrics",
                    "Execution-risk metric differs from daily evidence",
                )
        elif expected != actual:
            _fail(
                path,
                "portfolio.execution-risk-metrics",
                "Execution-risk metric differs from daily evidence",
            )

    projection: dict[str, Any] = {
        "available": True,
        "policy": {
            "method": policy["method"],
            "riskPolicy": policy["risk_policy"],
            "noTradePriority": policy["no_trade_priority"],
            "repair": policy["repair"],
            "selectionAuthority": policy["selection_authority"],
            "tradingAuthority": policy["trading_authority"],
        },
        "selectionAuthority": "context-only",
    }
    fields = {
        "status": "status",
        "dates": "dates",
        "activeDates": "active_dates",
        "forecastAvailableDates": "forecast_available_dates",
        "forecastUnavailableDates": "forecast_unavailable_dates",
        "forecastCoverage": "forecast_coverage",
        "pretradeBreachDates": "pretrade_breach_dates",
        "pretradeBreachRate": "pretrade_breach_rate",
        "riskRebalanceOverrideDates": (
            "risk_rebalance_override_dates"
        ),
        "riskRebalanceOverrideRate": (
            "risk_rebalance_override_rate"
        ),
        "executedBreachDates": "executed_breach_dates",
        "executedBreachRate": "executed_breach_rate",
        "meanExecutedForecastAnnualized": (
            "mean_executed_forecast_annualized"
        ),
        "maximumExecutedForecastAnnualized": (
            "maximum_executed_forecast_annualized"
        ),
        "maximumCeilingError": "maximum_ceiling_error",
        "statusCounts": "status_counts",
        "executionReasonCounts": "execution_reason_counts",
    }
    for split_name in ("validation", "test"):
        derived = derive(split_name)
        compare(
            raw.get(split_name),
            derived,
            f"RunResult/metrics/execution_risk/{split_name}",
        )
        projection[split_name] = {
            output: derived[source]
            for output, source in fields.items()
        }
    latest = daily.rows[-1]
    projection["latest"] = {
        "timestamp": latest["timestamp"],
        "status": latest["execution_risk_status"],
        "forecastAvailable": latest[
            "execution_risk_forecast_available"
        ],
        "pretradeForecastAnnualized": latest[
            "pretrade_risk_forecast_annualized"
        ],
        "executedForecastAnnualized": latest[
            "executed_risk_forecast_annualized"
        ],
        "ceilingAnnualized": latest[
            "execution_risk_ceiling_annualized"
        ],
        "riskRebalanceOverride": latest[
            "risk_rebalance_override"
        ],
        "executionReason": latest["execution_reason"],
    }
    return projection


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _liquidity_capacity_projection(
    result: dict[str, Any],
    ordered_decisions: list[dict[str, Any]],
    splits: dict[str, Any],
) -> dict[str, Any]:
    raw = result["metrics"].get("liquidity_capacity")
    has_ledger = any(
        item["liquidity_capacity_status"] != "legacy_unavailable"
        for item in ordered_decisions
    )
    if raw is None and not has_ledger:
        return {
            "available": False,
            "policy": None,
            "selectionAuthority": "context-only",
            "validation": None,
            "test": None,
            "latestTrade": None,
        }
    if not isinstance(raw, dict) or not has_ledger:
        _fail(
            "RunResult/metrics/liquidity_capacity",
            "portfolio.liquidity-capacity",
            "Capacity metrics and ledger evidence must exist together",
        )
    policy = raw.get("policy")
    expected_policy = {
        "method": "trailing-average-dollar-volume-capacity-v1",
        "adv_window": 20,
        "participation_limits": [0.01, 0.05],
        "reference_nav": LIQUIDITY_REFERENCE_NAV,
        "selection_authority": "context-only",
        "trading_authority": "none",
    }
    if policy != expected_policy:
        _fail(
            "RunResult/metrics/liquidity_capacity/policy",
            "portfolio.liquidity-policy",
            "Liquidity-capacity policy differs from the fixed contract",
        )

    by_date: dict[str, list[dict[str, Any]]] = {}
    for item in ordered_decisions:
        by_date.setdefault(item["timestamp"], []).append(item)

    def derive(split_name: str) -> dict[str, Any]:
        split = splits[split_name]
        dated = [
            (timestamp, rows)
            for timestamp, rows in sorted(by_date.items())
            if split["start"] <= timestamp <= split["signalEnd"]
        ]
        trade_dates = [
            (timestamp, rows)
            for timestamp, rows in dated
            if rows[0]["liquidity_capacity_status"] != "no_trade"
        ]
        available = [
            (timestamp, rows)
            for timestamp, rows in trade_dates
            if rows[0]["liquidity_capacity_status"] == "available"
        ]
        unavailable = [
            (timestamp, rows)
            for timestamp, rows in trade_dates
            if rows[0]["liquidity_capacity_status"]
            == "insufficient_adv_history"
        ]
        capacities = {
            "capacity_1pct": [
                rows[0]["portfolio_capacity_nav_1pct"]
                for _, rows in available
            ],
            "capacity_5pct": [
                rows[0]["portfolio_capacity_nav_5pct"]
                for _, rows in available
            ],
        }
        binding_counts: dict[str, int] = {}
        for _, rows in available:
            binding = next(
                row["asset"]
                for row in rows
                if row["capacity_binding_asset"]
            )
            binding_counts[binding] = binding_counts.get(binding, 0) + 1

        def summary(key: str) -> dict[str, Any]:
            values = capacities[key]
            return {
                "status": "available" if values else "unavailable",
                "observations": len(values),
                "minimum_nav": min(values) if values else 0.0,
                "tenth_percentile_nav": _quantile(values, 0.10),
                "median_nav": _quantile(values, 0.50),
                "reference_nav_breach_rate": (
                    sum(
                        value + 1e-12 < LIQUIDITY_REFERENCE_NAV
                        for value in values
                    )
                    / len(values)
                    if values
                    else 0.0
                ),
            }

        return {
            "status": (
                "available"
                if available
                else "no_trades"
                if not trade_dates
                else "insufficient_adv_history"
            ),
            "trade_dates": len(trade_dates),
            "available_trade_dates": len(available),
            "unavailable_trade_dates": len(unavailable),
            "trade_date_coverage": (
                len(available) / len(trade_dates)
                if trade_dates
                else 0.0
            ),
            "binding_asset_counts_1pct": binding_counts,
            "capacity_1pct": summary("capacity_1pct"),
            "capacity_5pct": summary("capacity_5pct"),
        }

    def compare(expected: Any, actual: Any, path: str) -> None:
        if isinstance(actual, dict):
            if not isinstance(expected, dict) or set(expected) != set(actual):
                _fail(
                    path,
                    "portfolio.liquidity-metrics",
                    "Capacity metric shape differs from the ledger",
                )
            for key, value in actual.items():
                compare(expected[key], value, f"{path}/{key}")
        elif isinstance(actual, float):
            if not math.isclose(
                _finite(expected, path),
                actual,
                rel_tol=1e-10,
                abs_tol=1e-6,
            ):
                _fail(
                    path,
                    "portfolio.liquidity-metrics",
                    "Capacity metric differs from the ledger",
                )
        elif expected != actual:
            _fail(
                path,
                "portfolio.liquidity-metrics",
                "Capacity metric differs from the ledger",
            )

    projection: dict[str, Any] = {
        "available": True,
        "policy": {
            "method": policy["method"],
            "advWindow": policy["adv_window"],
            "participationLimits": policy["participation_limits"],
            "referenceNav": policy["reference_nav"],
            "selectionAuthority": policy["selection_authority"],
            "tradingAuthority": policy["trading_authority"],
        },
        "selectionAuthority": "context-only",
    }
    for split_name in ("validation", "test"):
        derived = derive(split_name)
        compare(
            raw.get(split_name),
            derived,
            f"RunResult/metrics/liquidity_capacity/{split_name}",
        )
        projection[split_name] = {
            "status": derived["status"],
            "tradeDates": derived["trade_dates"],
            "availableTradeDates": derived["available_trade_dates"],
            "unavailableTradeDates": derived[
                "unavailable_trade_dates"
            ],
            "tradeDateCoverage": derived["trade_date_coverage"],
            "bindingAssetCounts1Pct": derived[
                "binding_asset_counts_1pct"
            ],
            "capacity1Pct": {
                "status": derived["capacity_1pct"]["status"],
                "observations": derived["capacity_1pct"]["observations"],
                "minimumNav": derived["capacity_1pct"]["minimum_nav"],
                "tenthPercentileNav": derived["capacity_1pct"][
                    "tenth_percentile_nav"
                ],
                "medianNav": derived["capacity_1pct"]["median_nav"],
                "referenceNavBreachRate": derived["capacity_1pct"][
                    "reference_nav_breach_rate"
                ],
            },
            "capacity5Pct": {
                "status": derived["capacity_5pct"]["status"],
                "observations": derived["capacity_5pct"]["observations"],
                "minimumNav": derived["capacity_5pct"]["minimum_nav"],
                "tenthPercentileNav": derived["capacity_5pct"][
                    "tenth_percentile_nav"
                ],
                "medianNav": derived["capacity_5pct"]["median_nav"],
                "referenceNavBreachRate": derived["capacity_5pct"][
                    "reference_nav_breach_rate"
                ],
            },
        }
    trades = [
        (timestamp, rows)
        for timestamp, rows in sorted(by_date.items())
        if rows[0]["liquidity_capacity_status"]
        in {"available", "insufficient_adv_history"}
    ]
    if not trades:
        projection["latestTrade"] = None
    else:
        timestamp, rows = trades[-1]
        available = rows[0]["liquidity_capacity_status"] == "available"
        binding = next(
            (
                row["asset"]
                for row in rows
                if row["capacity_binding_asset"]
            ),
            None,
        )
        projection["latestTrade"] = {
            "timestamp": timestamp,
            "status": rows[0]["liquidity_capacity_status"],
            "capacity1Pct": (
                rows[0]["portfolio_capacity_nav_1pct"]
                if available
                else None
            ),
            "capacity5Pct": (
                rows[0]["portfolio_capacity_nav_5pct"]
                if available
                else None
            ),
            "bindingAsset": binding,
            "maximumReferenceNavParticipation": (
                max(
                    row["reference_nav_adv_participation"]
                    for row in rows
                )
                if available
                else None
            ),
        }
    return projection


EPISODE_BOOLEAN_COLUMNS = {
    "left_censored",
    "right_censored",
    "complete",
}
EPISODE_INTEGER_COLUMNS = {
    "episode_number",
    "decision_bars",
    "intent_mismatch_bars",
    "no_trade_bars",
    "risk_override_bars",
}
EPISODE_DATE_COLUMNS = {
    "entry_timestamp",
    "last_earning_timestamp",
    "exit_timestamp",
}
EPISODE_STRING_COLUMNS = {
    "episode_id",
    "split",
    "role",
    "asset",
    "side",
    "entry_action",
    "exit_action",
}
EPISODE_FLOAT_COLUMNS = (
    set(POSITION_EPISODE_COLUMNS)
    - EPISODE_BOOLEAN_COLUMNS
    - EPISODE_INTEGER_COLUMNS
    - EPISODE_DATE_COLUMNS
    - EPISODE_STRING_COLUMNS
)


def _parse_position_episodes(path: Path) -> pd.DataFrame:
    fields, raw_rows = _read_csv(
        path,
        required=set(POSITION_EPISODE_COLUMNS),
        maximum_rows=MAX_EPISODE_ROWS,
    )
    if fields != list(POSITION_EPISODE_COLUMNS):
        _fail(
            path,
            "portfolio.position-episode-columns",
            "Position-episode columns differ from the fixed contract",
        )
    parsed: list[dict[str, Any]] = []
    for row_number, raw in enumerate(raw_rows, start=2):
        row_path = f"{path}:{row_number}"
        row: dict[str, Any] = {}
        for field in EPISODE_STRING_COLUMNS:
            if not raw[field]:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.position-episode-string",
                    f"{field} must be non-empty",
                )
            row[field] = raw[field]
        for field in EPISODE_DATE_COLUMNS:
            row[field] = (
                pd.NaT
                if raw[field] == ""
                else pd.Timestamp(
                    _session_date(raw[field], f"{row_path}/{field}")
                )
            )
        for field in EPISODE_BOOLEAN_COLUMNS:
            if raw[field] not in {"True", "False"}:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.boolean",
                    f"{field} must be True or False",
                )
            row[field] = raw[field] == "True"
        for field in EPISODE_INTEGER_COLUMNS:
            try:
                value = int(raw[field])
            except ValueError:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.integer",
                    f"{field} must be a non-negative integer",
                )
            if str(value) != raw[field] or value < 0:
                _fail(
                    f"{row_path}/{field}",
                    "portfolio.integer",
                    f"{field} must be a non-negative integer",
                )
            row[field] = value
        for field in EPISODE_FLOAT_COLUMNS:
            row[field] = _finite(raw[field], f"{row_path}/{field}")
        if (
            row["split"] not in {"train", "validation", "test"}
            or row["role"]
            not in {"training", "selection", "visible-audit"}
            or row["side"] not in {"long", "short"}
            or row["episode_id"]
            != (
                f"{row['split']}:{row['asset']}:"
                f"{row['episode_number']:04d}"
            )
            or row["complete"]
            != (not (row["left_censored"] or row["right_censored"]))
            or (
                row["decision_bars"] == 0
                and not pd.isna(row["last_earning_timestamp"])
            )
            or (
                row["decision_bars"] > 0
                and pd.isna(row["last_earning_timestamp"])
            )
            or (
                row["right_censored"]
                != pd.isna(row["exit_timestamp"])
            )
            or row["intent_mismatch_bars"] > row["decision_bars"]
            or row["no_trade_bars"] > row["decision_bars"]
            or row["risk_override_bars"] > row["decision_bars"]
            or min(
                row["peak_abs_weight"],
                row["average_abs_weight"],
                row["entry_cost"],
                row["holding_cost"],
                row["exit_cost"],
                row["total_cost"],
                row["maximum_favorable_excursion"],
            )
            < -1e-12
            or row["maximum_adverse_excursion"] > 1e-12
            or not math.isclose(
                row["total_cost"],
                row["entry_cost"]
                + row["holding_cost"]
                + row["exit_cost"],
                rel_tol=0.0,
                abs_tol=1e-10,
            )
            or not math.isclose(
                row["net_contribution"],
                row["gross_contribution"] - row["total_cost"],
                rel_tol=0.0,
                abs_tol=1e-10,
            )
            or (
                row["side"] == "long"
                and row["entry_weight"] < -1e-12
            )
            or (
                row["side"] == "short"
                and row["entry_weight"] > 1e-12
            )
        ):
            _fail(
                row_path,
                "portfolio.position-episode-value",
                "Position-episode evidence is invalid",
            )
        parsed.append(row)
    if not parsed:
        return pd.DataFrame(columns=POSITION_EPISODE_COLUMNS)
    result = pd.DataFrame(parsed)
    return result.loc[:, POSITION_EPISODE_COLUMNS]


def _compare_position_episode_frames(
    actual: pd.DataFrame,
    expected: pd.DataFrame,
    path: Path,
) -> None:
    if len(actual) != len(expected):
        _fail(
            path,
            "portfolio.position-episode-coverage",
            "Position-episode artifact does not match reconstructed coverage",
        )
    for row_number, (actual_row, expected_row) in enumerate(
        zip(actual.to_dict("records"), expected.to_dict("records")),
        start=2,
    ):
        for field in POSITION_EPISODE_COLUMNS:
            actual_value = actual_row[field]
            expected_value = expected_row[field]
            if field in EPISODE_FLOAT_COLUMNS:
                matches = math.isclose(
                    float(actual_value),
                    float(expected_value),
                    rel_tol=1e-10,
                    abs_tol=1e-10,
                )
            elif field in EPISODE_DATE_COLUMNS:
                matches = (
                    pd.isna(actual_value) and pd.isna(expected_value)
                ) or (
                    not pd.isna(actual_value)
                    and not pd.isna(expected_value)
                    and pd.Timestamp(actual_value)
                    == pd.Timestamp(expected_value)
                )
            else:
                matches = actual_value == expected_value
            if not matches:
                _fail(
                    f"{path}:{row_number}/{field}",
                    "portfolio.position-episode-reconciliation",
                    "Position-episode artifact differs from the decision ledger",
                )


def _compare_position_metrics(
    actual: Any,
    expected: Any,
    path: str,
) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            _fail(
                path,
                "portfolio.position-lifecycle-metrics",
                "Position-lifecycle metric shape differs from reconstructed evidence",
            )
        for key, value in expected.items():
            _compare_position_metrics(
                actual[key],
                value,
                f"{path}/{key}",
            )
    elif isinstance(expected, bool):
        if actual is not expected:
            _fail(
                path,
                "portfolio.position-lifecycle-metrics",
                "Position-lifecycle metric differs from reconstructed evidence",
            )
    elif isinstance(expected, float):
        if not math.isclose(
            _finite(actual, path),
            expected,
            rel_tol=1e-10,
            abs_tol=1e-10,
        ):
            _fail(
                path,
                "portfolio.position-lifecycle-metrics",
                "Position-lifecycle metric differs from reconstructed evidence",
            )
    elif actual != expected:
        _fail(
            path,
            "portfolio.position-lifecycle-metrics",
            "Position-lifecycle metric differs from reconstructed evidence",
        )


def _position_lifecycle_projection(
    result: dict[str, Any],
    episode_path: Path | None,
    ordered_decisions: list[dict[str, Any]],
    daily: ParsedDaily,
    splits: dict[str, Any],
) -> dict[str, Any]:
    raw = result["metrics"].get("position_lifecycle")
    if raw is None and episode_path is None:
        return {
            "available": False,
            "policy": None,
            "selectionAuthority": "context-only",
            "validation": None,
            "test": None,
            "recentEpisodes": [],
        }
    if not isinstance(raw, dict) or episode_path is None:
        _fail(
            "RunResult/metrics/position_lifecycle",
            "portfolio.position-lifecycle",
            "Position-lifecycle metrics and artifact must exist together",
        )
    policy = {
        "method": "split-bounded-executed-position-episodes-v1",
        "state": "sign-of-executed-weight",
        "boundary": "split-clipped-left-right-censored",
        "pnl": (
            "additive-portfolio-return-contribution-after-"
            "proportional-trade-cost"
        ),
        "excursion": (
            "cumulative-net-contribution-from-split-segment-start"
        ),
        "selection_authority": "context-only",
        "trading_authority": "none",
    }
    if raw.get("policy") != policy or set(raw) != {
        "policy",
        "train",
        "validation",
        "test",
    }:
        _fail(
            "RunResult/metrics/position_lifecycle/policy",
            "portfolio.position-lifecycle-policy",
            "Position-lifecycle policy differs from the fixed contract",
        )
    ledger = pd.DataFrame(ordered_decisions)
    ledger["timestamp"] = pd.to_datetime(
        ledger["timestamp"],
        format="%Y-%m-%d",
    )
    roles = {
        "train": "training",
        "validation": "selection",
        "test": "visible-audit",
    }
    expected_frames: dict[str, pd.DataFrame] = {}
    expected_metrics: dict[str, dict[str, object]] = {}
    for split_name in ("train", "validation", "test"):
        split = splits[split_name]
        index = pd.DatetimeIndex(
            [
                timestamp
                for timestamp in pd.to_datetime(
                    daily.dates,
                    format="%Y-%m-%d",
                )
                if pd.Timestamp(split["start"])
                <= timestamp
                <= pd.Timestamp(split["signalEnd"])
            ]
        )
        try:
            frame = build_position_episodes(
                ledger,
                index,
                split=split_name,
                role=roles[split_name],
            )
            metrics = position_episode_metrics(
                frame,
                ledger,
                index,
            )
        except PortfolioFailure as error:
            _fail(
                episode_path,
                getattr(error, "code", "portfolio.position-lifecycle"),
                str(error),
            )
        expected_frames[split_name] = frame
        expected_metrics[split_name] = metrics
        _compare_position_metrics(
            raw[split_name],
            metrics,
            f"RunResult/metrics/position_lifecycle/{split_name}",
        )
    expected = pd.concat(
        expected_frames.values(),
        ignore_index=True,
    )
    actual = _parse_position_episodes(episode_path)
    _compare_position_episode_frames(actual, expected, episode_path)

    def split_projection(name: str) -> dict[str, Any]:
        value = expected_metrics[name]
        return {
            "status": value["status"],
            "segments": value["segments"],
            "activeSegments": value["active_segments"],
            "completeEpisodes": value["complete_episodes"],
            "leftCensoredSegments": value["left_censored_segments"],
            "rightCensoredSegments": value["right_censored_segments"],
            "longSegments": value["long_segments"],
            "shortSegments": value["short_segments"],
            "decisionBars": value["decision_bars"],
            "segmentPositiveRate": value["segment_positive_rate"],
            "completeEpisodeWinRate": value[
                "complete_episode_win_rate"
            ],
            "averageCompleteHoldingBars": value[
                "average_complete_holding_bars"
            ],
            "medianCompleteHoldingBars": value[
                "median_complete_holding_bars"
            ],
            "averageCompleteWinContribution": value[
                "average_complete_win_contribution"
            ],
            "averageCompleteLossContribution": value[
                "average_complete_loss_contribution"
            ],
            "completePayoffRatio": value["complete_payoff_ratio"],
            "completeProfitFactor": value["complete_profit_factor"],
            "averageSegmentMfe": value["average_segment_mfe"],
            "averageSegmentMae": value["average_segment_mae"],
            "intentMismatchBars": value["intent_mismatch_bars"],
            "intentMismatchRate": value["intent_mismatch_rate"],
            "noTradeBars": value["no_trade_bars"],
            "noTradeBarRate": value["no_trade_bar_rate"],
            "riskOverrideBars": value["risk_override_bars"],
            "totalGrossContribution": value[
                "total_gross_contribution"
            ],
            "totalCost": value["total_cost"],
            "totalNetContribution": value[
                "total_net_contribution"
            ],
            "byAsset": [
                {
                    "asset": asset,
                    "segments": metrics["segments"],
                    "activeSegments": metrics["active_segments"],
                    "completeEpisodes": metrics["complete_episodes"],
                    "decisionBars": metrics["decision_bars"],
                    "totalNetContribution": metrics[
                        "total_net_contribution"
                    ],
                    "totalCost": metrics["total_cost"],
                    "completeEpisodeWinRate": metrics[
                        "complete_episode_win_rate"
                    ],
                }
                for asset, metrics in value["by_asset"].items()
            ],
            "reconciliation": value["reconciliation"],
        }

    active_recent = expected[
        expected["split"].isin(["validation", "test"])
        & (expected["decision_bars"].astype(int) > 0)
    ]
    recent = pd.concat(
        [
            active_recent[active_recent["split"].eq(name)]
            .sort_values(
                ["entry_timestamp", "asset", "episode_number"],
            )
            .tail(12)
            for name in ("validation", "test")
        ],
        ignore_index=True,
    )
    return {
        "available": True,
        "policy": {
            "method": policy["method"],
            "state": policy["state"],
            "boundary": policy["boundary"],
            "pnl": policy["pnl"],
            "excursion": policy["excursion"],
            "selectionAuthority": policy["selection_authority"],
            "tradingAuthority": policy["trading_authority"],
        },
        "selectionAuthority": "context-only",
        "validation": split_projection("validation"),
        "test": split_projection("test"),
        "recentEpisodes": [
            {
                "id": row["episode_id"],
                "split": row["split"],
                "role": row["role"],
                "asset": row["asset"],
                "side": row["side"],
                "entryTimestamp": pd.Timestamp(
                    row["entry_timestamp"]
                ).date().isoformat(),
                "lastEarningTimestamp": (
                    None
                    if pd.isna(row["last_earning_timestamp"])
                    else pd.Timestamp(
                        row["last_earning_timestamp"]
                    ).date().isoformat()
                ),
                "exitTimestamp": (
                    None
                    if pd.isna(row["exit_timestamp"])
                    else pd.Timestamp(
                        row["exit_timestamp"]
                    ).date().isoformat()
                ),
                "entryAction": row["entry_action"],
                "exitAction": row["exit_action"],
                "leftCensored": bool(row["left_censored"]),
                "rightCensored": bool(row["right_censored"]),
                "complete": bool(row["complete"]),
                "decisionBars": int(row["decision_bars"]),
                "netContribution": float(row["net_contribution"]),
                "totalCost": float(row["total_cost"]),
                "maximumFavorableExcursion": float(
                    row["maximum_favorable_excursion"]
                ),
                "maximumAdverseExcursion": float(
                    row["maximum_adverse_excursion"]
                ),
                "intentMismatchBars": int(
                    row["intent_mismatch_bars"]
                ),
            }
            for row in recent.to_dict("records")
        ],
    }


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
    signal_policy = _signal_policy_projection(run.result)
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
        "mechanicalDecision": _mechanical_decision_projection(
            daily,
            universe,
            decisions,
            signal_policy,
            mandate,
        ),
        "recentTransitions": _recent_transitions(
            ordered_decisions,
            universe,
        ),
        "signalPolicy": signal_policy,
        "riskGovernor": _risk_governor_projection(run.result, mandate),
        "executedBookRisk": _executed_book_risk_projection(
            run.result,
            daily,
            splits,
            mandate,
        ),
        "liquidityCapacity": _liquidity_capacity_projection(
            run.result,
            ordered_decisions,
            splits,
        ),
        "positionLifecycle": _position_lifecycle_projection(
            run.result,
            paths.get(POSITION_EPISODE_ARTIFACT_KIND),
            ordered_decisions,
            daily,
            splits,
        ),
        "parameterNeighborhood": _parameter_neighborhood_projection(
            run.result,
            paths.get(PARAMETER_NEIGHBORHOOD_ARTIFACT_KIND),
            daily,
            splits,
        ),
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
                "executedRiskForecastAnnualized",
                "executionRiskCeilingAnnualized",
                "riskRebalanceOverride",
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
                "executedRiskForecastAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "executionRiskCeilingAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "riskRebalanceOverride": {"type": "boolean"},
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
        "mechanicalTrigger": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "event",
                "comparator",
                "threshold",
                "distance",
            ],
            "properties": {
                "event": {"type": "string", "minLength": 1},
                "comparator": {"enum": [">=", ">", "<=", "<"]},
                "threshold": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "distance": {
                    "anyOf": [
                        {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        {"type": "null"},
                    ]
                },
            },
        },
        "mechanicalPosition": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "asset",
                "tradable",
                "allocationStatus",
                "score",
                "scoreAvailable",
                "signalState",
                "signalEvent",
                "nextTriggers",
                "nearestTrigger",
                "preGovernorTargetWeight",
                "targetWeight",
                "pretradeWeight",
                "proposedTradeWeight",
                "executedWeight",
                "tradeWeight",
                "executionAction",
                "executionReason",
            ],
            "properties": {
                "asset": {"type": "string", "minLength": 1},
                "tradable": {"type": "boolean"},
                "allocationStatus": {"type": "string", "minLength": 1},
                "score": {
                    "anyOf": [
                        {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        {"type": "null"},
                    ]
                },
                "scoreAvailable": {"type": "boolean"},
                "signalState": {"enum": [-1, 0, 1]},
                "signalEvent": {"type": "string", "minLength": 1},
                "nextTriggers": {
                    "type": "array",
                    "maxItems": 2,
                    "items": {"$ref": "#/$defs/mechanicalTrigger"},
                },
                "nearestTrigger": {
                    "anyOf": [
                        {"$ref": "#/$defs/mechanicalTrigger"},
                        {"type": "null"},
                    ]
                },
                "preGovernorTargetWeight": {"type": "number"},
                "targetWeight": {"type": "number"},
                "pretradeWeight": {"type": "number"},
                "proposedTradeWeight": {"type": "number"},
                "executedWeight": {"type": "number"},
                "tradeWeight": {"type": "number"},
                "executionAction": {"type": "string", "minLength": 1},
                "executionReason": {"type": "string", "minLength": 1},
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
        "mechanicalDecision",
        "recentTransitions",
        "signalPolicy",
        "riskGovernor",
        "executedBookRisk",
        "liquidityCapacity",
        "positionLifecycle",
        "parameterNeighborhood",
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
            "required": sorted(BASE_ARTIFACT_KINDS),
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
                "executionRiskStatus",
                "executionRiskForecastAvailable",
                "pretradeRiskForecastAnnualized",
                "executedRiskForecastAnnualized",
                "executionRiskCeilingAnnualized",
                "riskRebalanceOverride",
                "executionReason",
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
                "executionRiskStatus": {
                    "type": "string",
                    "minLength": 1,
                },
                "executionRiskForecastAvailable": {
                    "type": "boolean"
                },
                "pretradeRiskForecastAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "executedRiskForecastAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "executionRiskCeilingAnnualized": {
                    "type": "number",
                    "minimum": 0,
                },
                "riskRebalanceOverride": {"type": "boolean"},
                "executionReason": {
                    "type": "string",
                    "minLength": 1,
                },
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
        "mechanicalDecision": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "method",
                "timestamp",
                "authority",
                "tradingAuthority",
                "distanceSemantics",
                "signalGate",
                "targetGate",
                "executionGate",
                "positions",
            ],
            "properties": {
                "method": {"const": MECHANICAL_DECISION_METHOD},
                "timestamp": {"type": "string", "format": "date"},
                "authority": {
                    "const": "quantitative-decision-support"
                },
                "tradingAuthority": {"const": "none"},
                "distanceSemantics": {
                    "const": PERCENTILE_DISTANCE_SEMANTICS
                },
                "signalGate": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "family",
                        "stateChanges",
                        "unavailableScores",
                        "contextAssets",
                        "longEntryPercentile",
                        "longExitPercentile",
                        "shortExitPercentile",
                        "shortEntryPercentile",
                    ],
                    "properties": {
                        "family": {
                            "enum": [
                                "dollar-neutral",
                                "long-cash",
                                "short-cash",
                            ]
                        },
                        "stateChanges": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "unavailableScores": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "contextAssets": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "longEntryPercentile": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "longExitPercentile": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "shortExitPercentile": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "shortEntryPercentile": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                    },
                },
                "targetGate": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "preGovernorGross",
                        "governedTargetGross",
                        "pretradeGross",
                        "riskGovernorStatus",
                        "riskGovernorScale",
                        "riskLimited",
                    ],
                    "properties": {
                        "preGovernorGross": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "governedTargetGross": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "pretradeGross": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "riskGovernorStatus": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "riskGovernorScale": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "riskLimited": {"type": "boolean"},
                    },
                },
                "executionGate": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "available",
                        "noTradeOneWay",
                        "proposedOneWayTurnover",
                        "bandShortfall",
                        "bandExcess",
                        "ordinaryRebalance",
                        "riskOverride",
                        "rebalanced",
                        "finalOneWayTurnover",
                        "executedGross",
                        "reason",
                        "status",
                    ],
                    "properties": {
                        "available": {"type": "boolean"},
                        "noTradeOneWay": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "proposedOneWayTurnover": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "bandShortfall": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "bandExcess": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "ordinaryRebalance": {
                            "type": ["boolean", "null"]
                        },
                        "riskOverride": {
                            "type": ["boolean", "null"]
                        },
                        "rebalanced": {"type": "boolean"},
                        "finalOneWayTurnover": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "executedGross": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "reason": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "status": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
                "positions": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_UNIVERSE,
                    "items": {"$ref": "#/$defs/mechanicalPosition"},
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
        "executedBookRisk": {"type": "object"},
        "liquidityCapacity": {"type": "object"},
        "positionLifecycle": {"type": "object"},
        "parameterNeighborhood": {"type": "object"},
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
