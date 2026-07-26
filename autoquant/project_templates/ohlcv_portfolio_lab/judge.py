"""Fixed causal signal-to-portfolio Judge for the reference laboratory."""

from __future__ import annotations

import importlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autoquant.intervals import (
    IntervalContractError,
    annualization_periods,
    load_multi_interval_asset,
    timestamp_label,
)
from autoquant.horizons import (
    RESEARCH_HORIZON,
    load_research_horizon,
)
from autoquant.mandates import (
    PORTFOLIO_MANDATE,
    load_portfolio_mandate,
)
from judges.portfolio_core import (
    LONG_ENTRY_PERCENTILE,
    LONG_EXIT_PERCENTILE,
    LIQUIDITY_ADV_WINDOW,
    LIQUIDITY_PARTICIPATION_LIMITS,
    RISK_COVARIANCE_MINIMUM,
    RISK_COVARIANCE_WINDOW,
    SHORT_ENTRY_PERCENTILE,
    SHORT_EXIT_PERCENTILE,
    VOLATILITY_WINDOW,
    PortfolioFailure,
    attribution_metrics,
    build_decision_ledger,
    build_position_episodes,
    build_risk_covariance_cache,
    constraint_audit,
    construct_signal_policy,
    execution_risk_metrics,
    implementation_metrics,
    liquidity_capacity_metrics,
    performance_metrics,
    resolve_implementation_policy,
    position_episode_metrics,
    signal_policy_metrics,
    simulate_targets,
)


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
MIN_ASSETS_PER_DATE = 4
MIN_SPLIT_OBSERVATIONS = 20
PARAMETER_NEIGHBORHOOD_METHOD = (
    "predeclared-signal-threshold-no-trade-neighborhood-v1"
)
PARAMETER_SIGNAL_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "id": "broad-entry",
        "label": "Broad entry",
        "long_entry": 0.55,
        "long_exit": 0.55,
        "short_exit": 0.45,
        "short_entry": 0.45,
    },
    {
        "id": "base",
        "label": "Base",
        "long_entry": LONG_ENTRY_PERCENTILE,
        "long_exit": LONG_EXIT_PERCENTILE,
        "short_exit": SHORT_EXIT_PERCENTILE,
        "short_entry": SHORT_ENTRY_PERCENTILE,
    },
    {
        "id": "selective-entry",
        "label": "Selective entry",
        "long_entry": 0.95,
        "long_exit": 0.55,
        "short_exit": 0.45,
        "short_entry": 0.05,
    },
    {
        "id": "fast-exit",
        "label": "Fast exit",
        "long_entry": 0.75,
        "long_exit": 0.75,
        "short_exit": 0.25,
        "short_entry": 0.25,
    },
    {
        "id": "selective-fast-exit",
        "label": "Selective + fast exit",
        "long_entry": 0.95,
        "long_exit": 0.75,
        "short_exit": 0.25,
        "short_entry": 0.05,
    },
)


class JudgeFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _write_output(value: dict[str, Any]) -> None:
    Path(os.environ["AUTOQUANT_RUN_OUTPUT"]).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_contract() -> tuple[dict[str, Any], Path]:
    study = json.loads(
        Path(os.environ["AUTOQUANT_STUDY_PATH"]).read_text(encoding="utf-8")
    )
    data_root = Path(os.environ["AUTOQUANT_DATA_ROOT"]).resolve()
    if not data_root.is_dir():
        raise JudgeFailure("dataset.root", "AUTOQUANT_DATA_ROOT is not a directory")
    return study, data_root


def _load_mandate() -> dict[str, Any]:
    path = Path(os.environ["AUTOQUANT_PROJECT_ROOT"]) / PORTFOLIO_MANDATE
    try:
        return load_portfolio_mandate(path)
    except Exception as error:
        raise JudgeFailure(
            "mandate.invalid",
            f"Invalid fixed Portfolio Mandate: {error}",
        ) from error


def _load_horizon() -> dict[str, Any]:
    path = Path(os.environ["AUTOQUANT_PROJECT_ROOT"]) / RESEARCH_HORIZON
    try:
        return load_research_horizon(path)
    except Exception as error:
        raise JudgeFailure(
            "horizon.invalid",
            f"Invalid fixed Horizon Mandate: {error}",
        ) from error


def _load_asset(data_root: Path, asset: str, start: str, end: str) -> pd.DataFrame:
    try:
        multi_interval = load_multi_interval_asset(
            data_root,
            asset,
            start=start,
            end=end,
        )
    except IntervalContractError as error:
        raise JudgeFailure(error.code, str(error)) from error
    if multi_interval is not None:
        if len(multi_interval) < 120:
            raise JudgeFailure(
                "dataset.observations",
                f"{asset} has fewer than 120 base observations in the Study range",
            )
        return multi_interval
    source = (data_root / "ohlcv" / f"{asset}.csv").resolve()
    if data_root not in source.parents or not source.is_file():
        raise JudgeFailure("dataset.asset", f"Missing confined OHLCV file for {asset}")
    frame = pd.read_csv(source)
    if tuple(frame.columns) != REQUIRED_COLUMNS:
        raise JudgeFailure(
            "dataset.columns",
            f"{asset} columns must be exactly {', '.join(REQUIRED_COLUMNS)}",
        )
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        format="%Y-%m-%d",
        errors="raise",
    )
    if (
        frame["timestamp"].duplicated().any()
        or not frame["timestamp"].is_monotonic_increasing
    ):
        raise JudgeFailure(
            "dataset.time-order",
            f"{asset} timestamps must be unique and chronological",
        )
    for column in REQUIRED_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    numeric = frame[list(REQUIRED_COLUMNS[1:])].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise JudgeFailure("dataset.non-finite", f"{asset} contains non-finite OHLCV")
    if (frame[["open", "high", "low", "close", "volume"]] <= 0).any().any():
        raise JudgeFailure("dataset.non-positive", f"{asset} contains non-positive OHLCV")
    if (
        (frame["high"] < frame[["open", "close"]].max(axis=1)).any()
        or (frame["low"] > frame[["open", "close"]].min(axis=1)).any()
    ):
        raise JudgeFailure("dataset.bar-shape", f"{asset} contains invalid bars")
    selected = frame[
        (frame["timestamp"] >= pd.Timestamp(start))
        & (frame["timestamp"] <= pd.Timestamp(end))
    ].copy()
    if len(selected) < 120:
        raise JudgeFailure(
            "dataset.observations",
            f"{asset} has fewer than 120 observations in the Study range",
        )
    return selected.reset_index(drop=True)


def _factor_series(module: Any, frame: pd.DataFrame, asset: str) -> pd.Series:
    before = frame.copy(deep=True)
    result = module.compute_factor(frame)
    if not frame.equals(before):
        raise JudgeFailure("factor.mutation", f"compute_factor mutated {asset} input")
    if not isinstance(result, pd.Series):
        raise JudgeFailure("factor.type", "compute_factor must return pandas.Series")
    if len(result) != len(frame) or not result.index.equals(frame.index):
        raise JudgeFailure(
            "factor.alignment",
            "Factor Series must preserve the input length and index",
        )
    try:
        numeric = pd.to_numeric(result, errors="raise").astype(float)
    except (TypeError, ValueError) as error:
        raise JudgeFailure("factor.numeric", f"Factor must be numeric: {error}") from error
    if np.isinf(numeric.to_numpy()).any():
        raise JudgeFailure("factor.non-finite", "Factor cannot contain infinity")
    return numeric


def _audit_causality(
    module: Any,
    frame: pd.DataFrame,
    full: pd.Series,
    asset: str,
) -> list[int]:
    cuts = sorted({len(frame) // 2, (len(frame) * 3) // 4, len(frame) - 2})
    for cut in cuts:
        prefix_frame = frame.iloc[: cut + 1].copy()
        prefix = _factor_series(module, prefix_frame, asset)
        start = max(0, cut - 4)
        expected = full.iloc[start : cut + 1].to_numpy(dtype=float)
        actual = prefix.iloc[start : cut + 1].to_numpy(dtype=float)
        if not np.isclose(
            expected,
            actual,
            rtol=1e-10,
            atol=1e-12,
            equal_nan=True,
        ).all():
            raise JudgeFailure(
                "factor.lookahead",
                f"{asset} past factor values change when future rows are withheld",
            )
    return cuts


def _daily_factor_evidence(
    factors: pd.DataFrame,
    forward_returns: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for timestamp in factors.index.intersection(forward_returns.index):
        pair = pd.DataFrame(
            {
                "factor": factors.loc[timestamp],
                "forward_return": forward_returns.loc[timestamp],
            }
        ).dropna()
        if (
            len(pair) < MIN_ASSETS_PER_DATE
            or pair["factor"].nunique() < 2
            or pair["forward_return"].nunique() < 2
        ):
            continue
        factor_rank = pair["factor"].rank(method="average")
        return_rank = pair["forward_return"].rank(method="average")
        rank_ic = factor_rank.corr(return_rank)
        ordered = pair.sort_values("factor")
        breadth = max(1, len(ordered) // 3)
        spread = float(
            ordered["forward_return"].iloc[-breadth:].mean()
            - ordered["forward_return"].iloc[:breadth].mean()
        )
        if rank_ic is not None and math.isfinite(float(rank_ic)):
            rows.append(
                {
                    "timestamp": timestamp,
                    "rank_ic": float(rank_ic),
                    "top_bottom_spread": spread,
                }
            )
    if not rows:
        raise JudgeFailure("factor.population", "No valid factor evidence dates")
    return pd.DataFrame(rows).set_index("timestamp").sort_index()


def _factor_metrics(
    evidence: pd.DataFrame,
    index: pd.Index,
    factors: pd.DataFrame,
) -> dict[str, float | int]:
    selected = evidence.reindex(index).dropna()
    if len(selected) < MIN_SPLIT_OBSERVATIONS:
        raise JudgeFailure(
            "factor.population",
            f"Chronological split has only {len(selected)} factor dates",
        )
    ic = selected["rank_ic"]
    mean_ic = float(ic.mean())
    std_ic = float(ic.std(ddof=0))
    coverage = float(factors.loc[index].notna().mean().mean())
    result: dict[str, float | int] = {
        "observations": int(len(selected)),
        "mean_rank_ic": mean_ic,
        "rank_icir": mean_ic / std_ic if std_ic > 1e-12 else 0.0,
        "rank_ic_hit_rate": float((ic > 0).mean()),
        "mean_top_bottom_spread": float(
            selected["top_bottom_spread"].mean()
        ),
        "mean_coverage": coverage,
    }
    if not all(math.isfinite(float(value)) for value in result.values()):
        raise JudgeFailure("factor.non-finite", "Factor metrics are non-finite")
    return result


def _split_indices(
    index: pd.DatetimeIndex,
) -> tuple[dict[str, pd.DatetimeIndex], dict[str, Any]]:
    if len(index) < 3 * (MIN_SPLIT_OBSERVATIONS + 1):
        raise JudgeFailure(
            "portfolio.population",
            "Too few dataset dates for fixed purged chronological evaluation",
        )
    train_end = int(len(index) * 0.60)
    validation_end = int(len(index) * 0.80)
    ranges = {
        "train": (0, train_end),
        "validation": (train_end, validation_end),
        "test": (validation_end, len(index)),
    }
    splits: dict[str, pd.DatetimeIndex] = {}
    protocol: dict[str, Any] = {
        "method": "dataset-fixed-chronological-60-20-20",
        "candidateDependent": False,
        "forwardHorizonBars": 1,
        "targetCrossesBoundary": False,
        "splits": {},
    }
    for name, (start, stop) in ranges.items():
        eligible = index[start : stop - 1]
        if len(eligible) < MIN_SPLIT_OBSERVATIONS:
            raise JudgeFailure(
                "portfolio.population",
                f"Fixed split {name} has only {len(eligible)} signal dates",
            )
        splits[name] = pd.DatetimeIndex(eligible)
        protocol["splits"][name] = {
            "start": timestamp_label(index[start]),
            "end": timestamp_label(index[stop - 1]),
            "signalEnd": timestamp_label(index[stop - 2]),
            "targetEnd": timestamp_label(index[stop - 1]),
            "eligibleSignalRows": len(eligible),
            "purgedBoundaryRows": 1,
        }
    return splits, protocol


def _parameter_configuration_id(profile_id: str, band: float) -> str:
    return f"{profile_id}__band-{int(round(band * 100)):03d}"


def _parameter_signal_daily(
    construction: Any,
    index: pd.DatetimeIndex,
) -> pd.DataFrame:
    selected = construction.ledger[
        construction.ledger["timestamp"].isin(index)
    ].copy()
    selected["signal_transition"] = selected[
        "prior_signal_state"
    ].ne(selected["signal_state"])
    selected["entry"] = selected["signal_event"].isin(
        {"enter_long", "enter_short"}
    )
    selected["exit"] = selected["signal_event"].isin(
        {"exit_long", "exit_short"}
    )
    selected["reversal"] = selected["signal_event"].isin(
        {"reverse_long_to_short", "reverse_short_to_long"}
    )
    return (
        selected.groupby("timestamp", sort=True)
        .agg(
            decision_rows=("asset", "size"),
            signal_transitions=("signal_transition", "sum"),
            entries=("entry", "sum"),
            exits=("exit", "sum"),
            reversals=("reversal", "sum"),
        )
        .reindex(index, fill_value=0)
        .astype(int)
    )


def _parameter_neighborhood(
    factor_panel: pd.DataFrame,
    close_panel: pd.DataFrame,
    volume_panel: pd.DataFrame,
    splits: dict[str, pd.DatetimeIndex],
    mandate: dict[str, Any],
    *,
    base_construction: Any,
    base_simulation: Any,
    risk_covariance_cache: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    implementation_policy = resolve_implementation_policy(mandate)
    base_band = implementation_policy["no_trade_one_way"]
    adverse_band = min(1.0, max(0.10, 2.0 * base_band))
    bands = tuple(dict.fromkeys((0.0, base_band, adverse_band)))
    base_configuration_id = _parameter_configuration_id("base", base_band)
    roles = {
        "validation": "selection-context",
        "test": "visible-audit",
    }
    configurations: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for profile in PARAMETER_SIGNAL_PROFILES:
        construction = (
            base_construction
            if profile["id"] == "base"
            else construct_signal_policy(
                factor_panel,
                close_panel,
                long_entry=float(profile["long_entry"]),
                long_exit=float(profile["long_exit"]),
                short_exit=float(profile["short_exit"]),
                short_entry=float(profile["short_entry"]),
                mandate=mandate,
                risk_covariance_cache=risk_covariance_cache,
            )
        )
        for band in bands:
            configuration_id = _parameter_configuration_id(
                str(profile["id"]),
                band,
            )
            is_base = configuration_id == base_configuration_id
            simulation = (
                base_simulation
                if is_base
                else simulate_targets(
                    construction.targets,
                    close_panel,
                    volume_panel,
                    no_trade_one_way=band,
                    mandate=mandate,
                    risk_covariance_cache=risk_covariance_cache,
                )
            )
            split_metrics: dict[str, Any] = {}
            for split in ("validation", "test"):
                index = splits[split]
                performance = performance_metrics(
                    simulation.daily.loc[index, "net_return"],
                    simulation.daily.loc[index, "benchmark_return"],
                )
                implementation = implementation_metrics(simulation, index)
                signal = signal_policy_metrics(construction, index)
                split_metrics[split] = {
                    "performance": performance,
                    "implementation": {
                        "mean_one_way_turnover": implementation[
                            "mean_one_way_turnover"
                        ],
                        "annualized_one_way_turnover": implementation[
                            "annualized_one_way_turnover"
                        ],
                        "total_cost_drag": implementation["total_cost_drag"],
                        "rebalance_rate": implementation["rebalance_rate"],
                        "no_trade_rate": implementation["no_trade_rate"],
                    },
                    "signal": {
                        "decision_rows": signal["decision_rows"],
                        "timestamps": signal["timestamps"],
                        "signal_transitions": signal["signal_transitions"],
                        "state_change_rate": signal["state_change_rate"],
                        "entries": signal["entries"],
                        "exits": signal["exits"],
                        "reversals": signal["reversals"],
                    },
                }
                daily_signal = _parameter_signal_daily(construction, index)
                daily = simulation.daily.loc[index]
                for timestamp in index:
                    rows.append(
                        {
                            "configurationId": configuration_id,
                            "signalProfile": profile["id"],
                            "noTradeOneWay": band,
                            "split": split,
                            "role": roles[split],
                            "timestamp": timestamp_label(timestamp),
                            "netReturn": float(
                                daily.loc[timestamp, "net_return"]
                            ),
                            "benchmarkReturn": float(
                                daily.loc[timestamp, "benchmark_return"]
                            ),
                            "oneWayTurnover": float(
                                daily.loc[timestamp, "one_way_turnover"]
                            ),
                            "cost": float(daily.loc[timestamp, "cost"]),
                            "rebalanced": bool(
                                daily.loc[timestamp, "rebalanced"]
                            ),
                            "signalDecisionRows": int(
                                daily_signal.loc[
                                    timestamp,
                                    "decision_rows",
                                ]
                            ),
                            "signalTransitions": int(
                                daily_signal.loc[
                                    timestamp,
                                    "signal_transitions",
                                ]
                            ),
                            "entries": int(
                                daily_signal.loc[timestamp, "entries"]
                            ),
                            "exits": int(
                                daily_signal.loc[timestamp, "exits"]
                            ),
                            "reversals": int(
                                daily_signal.loc[timestamp, "reversals"]
                            ),
                        }
                    )
            configurations[configuration_id] = {
                "signal_profile": profile["id"],
                "no_trade_one_way": band,
                "is_base": is_base,
                "validation": split_metrics["validation"],
                "test": split_metrics["test"],
            }

    for split in ("validation", "test"):
        base = configurations[base_configuration_id][split]
        for configuration in configurations.values():
            current = configuration[split]
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

    split_output: dict[str, Any] = {}
    for split in ("validation", "test"):
        values = [
            configuration[split]
            for configuration in configurations.values()
        ]
        sharpes = np.asarray(
            [value["performance"]["sharpe"] for value in values],
            dtype=float,
        )
        base_sharpe = float(
            configurations[base_configuration_id][split][
                "performance"
            ]["sharpe"]
        )
        deltas = sharpes - base_sharpe
        turnovers = [
            value["implementation"]["annualized_one_way_turnover"]
            for value in values
        ]
        costs = [
            value["implementation"]["total_cost_drag"]
            for value in values
        ]
        transitions = [
            value["signal"]["signal_transitions"] for value in values
        ]
        base_sign = 1 if base_sharpe > 0 else -1 if base_sharpe < 0 else 0
        signs = np.sign(sharpes)
        split_output[split] = {
            "configurations": {
                configuration_id: configuration[split]
                for configuration_id, configuration in configurations.items()
            },
            "aggregate": {
                "configuration_count": len(values),
                "base_net_sharpe": base_sharpe,
                "positive_net_sharpe_rate": float(
                    np.mean(sharpes > 0)
                ),
                "sign_agreement_with_base_rate": float(
                    np.mean(signs == base_sign)
                ),
                "minimum_net_sharpe": float(np.min(sharpes)),
                "median_net_sharpe": float(np.median(sharpes)),
                "maximum_net_sharpe": float(np.max(sharpes)),
                "net_sharpe_std": float(np.std(sharpes, ddof=0)),
                "worst_net_sharpe_delta": float(np.min(deltas)),
                "best_net_sharpe_delta": float(np.max(deltas)),
                "minimum_annualized_one_way_turnover": float(
                    min(turnovers)
                ),
                "maximum_annualized_one_way_turnover": float(
                    max(turnovers)
                ),
                "minimum_total_cost_drag": float(min(costs)),
                "maximum_total_cost_drag": float(max(costs)),
                "minimum_signal_transitions": int(min(transitions)),
                "maximum_signal_transitions": int(max(transitions)),
            },
        }

    policy = {
        "method": PARAMETER_NEIGHBORHOOD_METHOD,
        "base_configuration_id": base_configuration_id,
        "role": "robustness-only",
        "selection_authority": "context-only",
        "trading_authority": "none",
        "configuration_count": len(configurations),
        "signal_profiles": [
            {
                "id": profile["id"],
                "label": profile["label"],
                "long_entry": profile["long_entry"],
                "long_exit": profile["long_exit"],
                "short_exit": profile["short_exit"],
                "short_entry": profile["short_entry"],
            }
            for profile in PARAMETER_SIGNAL_PROFILES
        ],
        "no_trade_bands": list(bands),
    }
    metrics = {
        "policy": policy,
        "validation": split_output["validation"],
        "test": split_output["test"],
    }
    artifact = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "method": PARAMETER_NEIGHBORHOOD_METHOD,
        "baseConfigurationId": base_configuration_id,
        "signalProfiles": [
            {
                "id": profile["id"],
                "label": profile["label"],
                "longEntry": profile["long_entry"],
                "longExit": profile["long_exit"],
                "shortExit": profile["short_exit"],
                "shortEntry": profile["short_entry"],
            }
            for profile in PARAMETER_SIGNAL_PROFILES
        ],
        "noTradeBands": list(bands),
        "rows": rows,
    }
    return metrics, artifact


def _evaluate() -> tuple[
    dict[str, Any],
    dict[str, Any],
    Any,
    Any,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    study, data_root = _load_contract()
    mandate = _load_mandate()
    research_horizon = _load_horizon()
    implementation_policy = resolve_implementation_policy(mandate)
    dataset = study["dataset"]
    universe = dataset["universe"]
    time_range = dataset["time_range"]
    module = importlib.import_module("factors.candidate")
    if not callable(getattr(module, "compute_factor", None)):
        raise JudgeFailure(
            "factor.api",
            "factors.candidate must export callable compute_factor(frame)",
        )

    factors: dict[str, pd.Series] = {}
    closes: dict[str, pd.Series] = {}
    volumes: dict[str, pd.Series] = {}
    causality_cuts: dict[str, list[int]] = {}
    for asset in universe:
        frame = _load_asset(
            data_root,
            asset,
            time_range["start"],
            time_range["end"],
        )
        factor = _factor_series(module, frame, asset)
        causality_cuts[asset] = _audit_causality(module, frame, factor, asset)
        timestamp = pd.DatetimeIndex(frame["timestamp"])
        factor.index = timestamp
        close = frame["close"].astype(float)
        close.index = timestamp
        volume = frame["volume"].astype(float)
        volume.index = timestamp
        factors[asset] = factor
        closes[asset] = close
        volumes[asset] = volume

    factor_panel = pd.DataFrame(factors)
    close_panel = pd.DataFrame(closes)
    volume_panel = pd.DataFrame(volumes)
    forward_returns = close_panel.shift(-1) / close_panel - 1.0
    risk_covariance_cache = build_risk_covariance_cache(
        close_panel,
        mandate=mandate,
    )
    factor_evidence = _daily_factor_evidence(factor_panel, forward_returns)
    construction = construct_signal_policy(
        factor_panel,
        close_panel,
        mandate=mandate,
        risk_covariance_cache=risk_covariance_cache,
    )
    targets = construction.targets
    audit = constraint_audit(targets, mandate=mandate)
    if not audit["passed"]:
        raise JudgeFailure(
            "portfolio.constraints",
            "Fixed target construction violated its declared constraints",
        )
    base = simulate_targets(
        targets,
        close_panel,
        volume_panel,
        mandate=mandate,
        risk_covariance_cache=risk_covariance_cache,
    )
    decision_ledger = build_decision_ledger(
        construction,
        base,
        close_panel,
        volume_panel,
        mandate=mandate,
    )
    splits, split_protocol = _split_indices(
        pd.DatetimeIndex(factor_panel.index)
    )

    factor_metrics: dict[str, Any] = {}
    portfolio_metrics: dict[str, Any] = {}
    implementation: dict[str, Any] = {}
    for name, index in splits.items():
        factor_metrics[name] = _factor_metrics(
            factor_evidence,
            index,
            factor_panel,
        )
        portfolio_metrics[name] = {
            "gross": performance_metrics(
                base.daily.loc[index, "gross_return"],
                base.daily.loc[index, "benchmark_return"],
            ),
            "net": performance_metrics(
                base.daily.loc[index, "net_return"],
                base.daily.loc[index, "benchmark_return"],
            ),
        }
        implementation[name] = implementation_metrics(base, index)

    policy_metrics = {
        name: signal_policy_metrics(construction, index)
        for name, index in splits.items()
    }
    attribution = {
        name: attribution_metrics(decision_ledger, base, index)
        for name, index in splits.items()
    }
    liquidity_capacity = {
        "policy": {
            "method": "trailing-average-dollar-volume-capacity-v1",
            "adv_window": LIQUIDITY_ADV_WINDOW,
            "participation_limits": list(
                LIQUIDITY_PARTICIPATION_LIMITS
            ),
            "reference_nav": implementation_policy["reference_nav"],
            "selection_authority": "context-only",
            "trading_authority": "none",
        },
        **{
            name: liquidity_capacity_metrics(
                decision_ledger,
                index,
                reference_nav=implementation_policy["reference_nav"],
            )
            for name, index in splits.items()
        },
    }
    execution_risk = {
        "policy": {
            "method": (
                "post-drift-executed-book-volatility-compliance-v1"
            ),
            "risk_policy": mandate["construction"]["riskPolicy"],
            "no_trade_priority": "risk-compliance-first",
            "repair": "minimum-proportional-scale-down",
            "selection_authority": "context-only",
            "trading_authority": "none",
        },
        **{
            name: execution_risk_metrics(base, index)
            for name, index in splits.items()
        },
    }
    episode_roles = {
        "train": "training",
        "validation": "selection",
        "test": "visible-audit",
    }
    episode_frames = {
        name: build_position_episodes(
            decision_ledger,
            index,
            split=name,
            role=episode_roles[name],
        )
        for name, index in splits.items()
    }
    position_episodes = pd.concat(
        episode_frames.values(),
        ignore_index=True,
    )
    position_lifecycle = {
        "policy": {
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
        },
        **{
            name: position_episode_metrics(
                episode_frames[name],
                decision_ledger,
                index,
            )
            for name, index in splits.items()
        },
    }
    parameter_neighborhood, parameter_neighborhood_artifact = (
        _parameter_neighborhood(
            factor_panel,
            close_panel,
            volume_panel,
            splits,
            mandate,
            base_construction=construction,
            base_simulation=base,
            risk_covariance_cache=risk_covariance_cache,
        )
    )

    validation_net_sharpe = float(
        portfolio_metrics["validation"]["net"]["sharpe"]
    )
    cost_stress: dict[str, Any] = {}
    base_cost_bps = implementation_policy["base_cost_bps"]
    adverse_cost_bps = max(25.0, 2.0 * base_cost_bps)
    for cost_bps in dict.fromkeys(
        (0.0, base_cost_bps, adverse_cost_bps)
    ):
        simulation = simulate_targets(
            targets,
            close_panel,
            volume_panel,
            cost_bps=cost_bps,
            mandate=mandate,
            risk_covariance_cache=risk_covariance_cache,
        )
        key = f"{cost_bps:g}bps"
        cost_stress[key] = {
            split: performance_metrics(
                simulation.daily.loc[index, "net_return"],
                simulation.daily.loc[index, "benchmark_return"],
            )
            for split, index in (
                ("validation", splits["validation"]),
                ("test", splits["test"]),
            )
        }
    delayed = simulate_targets(
        targets,
        close_panel,
        volume_panel,
        extra_delay=1,
        mandate=mandate,
        risk_covariance_cache=risk_covariance_cache,
    )
    delay_stress = {
        split: performance_metrics(
            delayed.daily.loc[index, "net_return"],
            delayed.daily.loc[index, "benchmark_return"],
        )
        for split, index in (
            ("validation", splits["validation"]),
            ("test", splits["test"]),
        )
    }
    no_hysteresis = construct_signal_policy(
        factor_panel,
        close_panel,
        long_exit=LONG_ENTRY_PERCENTILE,
        short_exit=SHORT_ENTRY_PERCENTILE,
        mandate=mandate,
        risk_covariance_cache=risk_covariance_cache,
    )
    no_hysteresis_simulation = simulate_targets(
        no_hysteresis.targets,
        close_panel,
        volume_panel,
        mandate=mandate,
        risk_covariance_cache=risk_covariance_cache,
    )
    hysteresis_comparison: dict[str, Any] = {}
    for split in ("validation", "test"):
        index = splits[split]
        governed_policy = policy_metrics[split]
        baseline_policy = signal_policy_metrics(no_hysteresis, index)
        governed_implementation = implementation[split]
        baseline_implementation = implementation_metrics(
            no_hysteresis_simulation,
            index,
        )
        governed_net = portfolio_metrics[split]["net"]
        baseline_net = performance_metrics(
            no_hysteresis_simulation.daily.loc[index, "net_return"],
            no_hysteresis_simulation.daily.loc[index, "benchmark_return"],
        )
        baseline_transitions = int(baseline_policy["signal_transitions"])
        transition_reduction = (
            baseline_transitions
            - int(governed_policy["signal_transitions"])
        )
        hysteresis_comparison[split] = {
            "governed": {
                "signal_transitions": governed_policy["signal_transitions"],
                "state_change_rate": governed_policy["state_change_rate"],
                "annualized_target_one_way_turnover": governed_policy[
                    "annualized_target_one_way_turnover"
                ],
                "annualized_implementation_one_way_turnover": (
                    governed_implementation["annualized_one_way_turnover"]
                ),
                "net_sharpe": governed_net["sharpe"],
            },
            "no_hysteresis": {
                "signal_transitions": baseline_transitions,
                "state_change_rate": baseline_policy["state_change_rate"],
                "annualized_target_one_way_turnover": baseline_policy[
                    "annualized_target_one_way_turnover"
                ],
                "annualized_implementation_one_way_turnover": (
                    baseline_implementation["annualized_one_way_turnover"]
                ),
                "net_sharpe": baseline_net["sharpe"],
            },
            "transition_reduction": transition_reduction,
            "transition_reduction_rate": (
                transition_reduction / baseline_transitions
                if baseline_transitions > 0
                else 0.0
            ),
            "implementation_turnover_reduction": (
                baseline_implementation["annualized_one_way_turnover"]
                - governed_implementation["annualized_one_way_turnover"]
            ),
        }
    ungoverned = construct_signal_policy(
        factor_panel,
        close_panel,
        mandate=mandate,
        apply_risk_governor=False,
        risk_covariance_cache=risk_covariance_cache,
    )
    ungoverned_simulation = simulate_targets(
        ungoverned.targets,
        close_panel,
        volume_panel,
        mandate=mandate,
        risk_covariance_cache=risk_covariance_cache,
    )
    risk_governor_comparison: dict[str, Any] = {}
    for split in ("validation", "test"):
        index = splits[split]
        governed_net = portfolio_metrics[split]["net"]
        ungoverned_net = performance_metrics(
            ungoverned_simulation.daily.loc[index, "net_return"],
            ungoverned_simulation.daily.loc[index, "benchmark_return"],
        )
        governed_implementation = implementation[split]
        ungoverned_implementation = implementation_metrics(
            ungoverned_simulation,
            index,
        )
        risk_governor_comparison[split] = {
            "governed": {
                "net_sharpe": governed_net["sharpe"],
                "annual_volatility": governed_net["annual_volatility"],
                "maximum_drawdown": governed_net["maximum_drawdown"],
                "average_gross_exposure": governed_implementation[
                    "average_gross_exposure"
                ],
                "risk_limited_dates": policy_metrics[split][
                    "risk_limited_dates"
                ],
                "risk_limited_rate": policy_metrics[split][
                    "risk_limited_rate"
                ],
                "average_active_risk_scale": policy_metrics[split][
                    "average_active_risk_scale"
                ],
                "maximum_pre_governor_annualized_volatility": policy_metrics[
                    split
                ]["maximum_pre_governor_annualized_volatility"],
                "maximum_post_governor_annualized_volatility": policy_metrics[
                    split
                ]["maximum_post_governor_annualized_volatility"],
            },
            "ungoverned_diagnostic": {
                "net_sharpe": ungoverned_net["sharpe"],
                "annual_volatility": ungoverned_net["annual_volatility"],
                "maximum_drawdown": ungoverned_net["maximum_drawdown"],
                "average_gross_exposure": ungoverned_implementation[
                    "average_gross_exposure"
                ],
            },
            "net_sharpe_delta": (
                governed_net["sharpe"] - ungoverned_net["sharpe"]
            ),
            "annual_volatility_delta": (
                governed_net["annual_volatility"]
                - ungoverned_net["annual_volatility"]
            ),
        }
    test_index = splits["test"]
    contribution = (
        base.weights.loc[test_index]
        * forward_returns.loc[test_index]
    ).mean() * annualization_periods(test_index)
    per_asset_contribution = {
        asset: float(value)
        for asset, value in contribution.items()
    }
    metrics = {
        "validation_net_sharpe": validation_net_sharpe,
        "portfolio_mandate": mandate,
        "research_horizon": research_horizon,
        "factor": factor_metrics,
        "portfolio": portfolio_metrics,
        "implementation": implementation,
        "signal_policy": {
            "parameters": {
                "long_entry_percentile": LONG_ENTRY_PERCENTILE,
                "long_exit_percentile": LONG_EXIT_PERCENTILE,
                "short_exit_percentile": SHORT_EXIT_PERCENTILE,
                "short_entry_percentile": SHORT_ENTRY_PERCENTILE,
                "volatility_window": VOLATILITY_WINDOW,
                "gross_target": mandate["construction"]["grossLimit"],
                "max_abs_weight": mandate["construction"]["maxAbsWeight"],
                "no_trade_one_way": implementation_policy[
                    "no_trade_one_way"
                ],
            },
            "train": policy_metrics["train"],
            "validation": policy_metrics["validation"],
            "test": policy_metrics["test"],
            "hysteresis_comparison": hysteresis_comparison,
        },
        "attribution": attribution,
        "liquidity_capacity": liquidity_capacity,
        "execution_risk": execution_risk,
        "position_lifecycle": position_lifecycle,
        "parameter_neighborhood": parameter_neighborhood,
        "split_protocol": split_protocol,
        "robustness": {
            "cost_stress": cost_stress,
            "extra_delay": delay_stress,
            "risk_governor": {
                "policy": mandate["construction"]["riskPolicy"],
                "selectionAuthority": "diagnostic-only",
                "validation": risk_governor_comparison["validation"],
                "test": risk_governor_comparison["test"],
            },
            "test_annualized_gross_contribution": per_asset_contribution,
        },
        "constraint_audit": audit,
        "research_integrity": {
            "selection_split": "validation",
            "test_role": "visible-diagnostic",
            "test_enters_selection": False,
            "external_holdout_rule": (
                "required-after-test-guided-iteration"
            ),
        },
    }
    if not math.isfinite(validation_net_sharpe):
        raise JudgeFailure("portfolio.non-finite", "Primary score is non-finite")
    report = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "dataset": {
            "id": dataset["id"],
            "version": dataset["version"],
            "universe": universe,
            "timeRange": time_range,
        },
        "portfolioMandate": mandate,
        "researchHorizon": research_horizon,
        "semantics": {
            "simulation": "bar-target-weight",
            "decision": "OHLCV and factor known through close t",
            "return": "close t to close t+1",
            "researchHorizonRole": (
                "fixed question identity and disclosure; sequential one-bar "
                "accounting is not a direct multi-bar forecast"
            ),
            "factorTransform": (
                "cross-sectional percentile state machine with inverse-volatility "
                "conviction sizing followed by a causal one-sided portfolio "
                "volatility ceiling"
            ),
            "signalState": (
                "long entry/exit 0.75/0.55; short entry/exit 0.25/0.45; "
                "direct reversal at opposite entry"
            ),
            "portfolio": (
                f"{mandate['construction']['family']} over authorized tradable "
                "assets; gross limit "
                f"{mandate['construction']['grossLimit']}; max abs weight "
                f"{mandate['construction']['maxAbsWeight']}; unused "
                "directional budget and risk-governor reductions remain cash"
            ),
            "riskGovernor": (
                "60-bar trailing covariance through close t; minimum 20 "
                "observations; annualized volatility ceiling "
                f"{mandate['construction']['riskPolicy']['annualizedVolatilityCeiling']}; "
                "scale-down only"
            ),
            "executionRisk": (
                "the final post-drift book is rechecked through close t; "
                "risk compliance bypasses the no-trade band with minimum "
                "proportional scale-down"
            ),
            "positionLifecycle": (
                "contiguous executed-weight signs clipped to fixed splits; "
                "linear close/open cost allocated exactly; MFE/MAE is "
                "daily cumulative additive return contribution"
            ),
            "noTrade": (
                "retain drifted book below "
                f"{implementation_policy['no_trade_one_way']} one-way turnover"
            ),
            "turnover": "0.5 * sum(abs(trade weight))",
            "cost": (
                "sum(abs(trade weight)) * "
                f"{base_cost_bps:g}bps"
            ),
            "liquidityCapacity": (
                "20-observation trailing average close-times-volume through "
                "decision close; exact executed trade weights inverted at "
                "1% and 5% participation; contextual only"
            ),
            "benchmark": mandate["construction"]["benchmark"],
            "split": (
                "dataset-fixed chronological 60/20/20 with one-bar "
                "boundary purge"
            ),
            "score": (
                "validation net Sharpe at "
                f"{base_cost_bps:g}bps only"
            ),
            "testRole": (
                "visible diagnostic evidence; never enters candidate selection"
            ),
            "tradingAuthority": "none",
        },
        "fixedParameters": {
            "volatilityWindow": VOLATILITY_WINDOW,
            "grossTarget": mandate["construction"]["grossLimit"],
            "maxAbsWeight": mandate["construction"]["maxAbsWeight"],
            "noTradeOneWay": implementation_policy["no_trade_one_way"],
            "baseCostBps": base_cost_bps,
            "referenceNav": implementation_policy["reference_nav"],
            "longEntryPercentile": LONG_ENTRY_PERCENTILE,
            "longExitPercentile": LONG_EXIT_PERCENTILE,
            "shortExitPercentile": SHORT_EXIT_PERCENTILE,
            "shortEntryPercentile": SHORT_ENTRY_PERCENTILE,
            "riskCovarianceWindow": RISK_COVARIANCE_WINDOW,
            "riskCovarianceMinimum": RISK_COVARIANCE_MINIMUM,
            "riskPolicy": mandate["construction"]["riskPolicy"],
            "executionRiskMethod": (
                "post-drift-executed-book-volatility-compliance-v1"
            ),
            "liquidityAdvWindow": LIQUIDITY_ADV_WINDOW,
            "liquidityParticipationLimits": list(
                LIQUIDITY_PARTICIPATION_LIMITS
            ),
        },
        "causalityAuditCuts": causality_cuts,
        "splitProtocol": split_protocol,
        "metrics": metrics,
    }
    return (
        metrics,
        report,
        base,
        construction,
        decision_ledger,
        position_episodes,
        parameter_neighborhood_artifact,
    )


def main() -> None:
    try:
        (
            metrics,
            report,
            simulation,
            construction,
            decision_ledger,
            position_episodes,
            parameter_neighborhood,
        ) = _evaluate()
        artifacts = Path(os.environ["AUTOQUANT_ARTIFACTS_DIR"])
        report_path = artifacts / "portfolio-report.json"
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        daily = simulation.daily.copy()
        daily.index = [timestamp_label(value) for value in daily.index]
        daily.index.name = "timestamp"
        daily.to_csv(artifacts / "daily-portfolio.csv", float_format="%.17g")
        proposed_targets = construction.targets.copy()
        proposed_targets.index = [
            timestamp_label(value) for value in proposed_targets.index
        ]
        proposed_targets.index.name = "timestamp"
        proposed_targets.to_csv(
            artifacts / "proposed-target-weights.csv",
            float_format="%.17g",
        )
        executed_weights = simulation.weights.copy()
        executed_weights.index = [
            timestamp_label(value) for value in executed_weights.index
        ]
        executed_weights.index.name = "timestamp"
        executed_weights.to_csv(
            artifacts / "executed-weights.csv",
            float_format="%.17g",
        )
        decision_artifact = decision_ledger.copy()
        decision_artifact["timestamp"] = decision_artifact["timestamp"].map(
            timestamp_label
        )
        decision_artifact.to_csv(
            artifacts / "portfolio-decisions.csv",
            index=False,
            float_format="%.17g",
        )
        episode_artifact = position_episodes.copy()
        for column in (
            "entry_timestamp",
            "last_earning_timestamp",
            "exit_timestamp",
        ):
            episode_artifact[column] = episode_artifact[column].map(
                lambda value: (
                    value if pd.isna(value) else timestamp_label(value)
                )
            )
        episode_artifact.to_csv(
            artifacts / "position-episodes.csv",
            index=False,
            float_format="%.17g",
        )
        (artifacts / "portfolio-parameter-neighborhood.json").write_text(
            json.dumps(
                parameter_neighborhood,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_output(
            {
                "schema_version": 1,
                "status": "succeeded",
                "summary": (
                    "Causal factor translated into constrained next-bar targets; "
                    "validation net Sharpe="
                    f"{metrics['validation_net_sharpe']:.6f}"
                ),
                "metrics": metrics,
                "artifacts": [
                    {
                        "kind": "portfolio-report",
                        "path": "portfolio-report.json",
                        "description": (
                            "Timing, construction, split, cost, risk, stress, "
                            "constraint, and causality evidence"
                        ),
                    },
                    {
                        "kind": "portfolio-daily",
                        "path": "daily-portfolio.csv",
                        "description": (
                            "Daily gross/net/benchmark returns, turnover, costs, "
                            "exposures, rebalance state, and participation"
                        ),
                    },
                    {
                        "kind": "portfolio-targets",
                        "path": "proposed-target-weights.csv",
                        "description": (
                            "Exact per-date signal-policy proposed target weights"
                        ),
                    },
                    {
                        "kind": "portfolio-weights",
                        "path": "executed-weights.csv",
                        "description": (
                            "Exact post-drift and no-trade-band executed weights"
                        ),
                    },
                    {
                        "kind": "portfolio-decisions",
                        "path": "portfolio-decisions.csv",
                        "description": (
                            "Per-asset signal state, sizing, execution reason, "
                            "trade, contribution, cost, regime, variance, "
                            "executed-book risk compliance, and causal "
                            "liquidity-capacity ledger"
                        ),
                    },
                    {
                        "kind": "portfolio-position-episodes",
                        "path": "position-episodes.csv",
                        "description": (
                            "Split-bounded executed-position episodes with "
                            "holding, contribution, cost, excursion, censoring, "
                            "and signal/execution mismatch evidence"
                        ),
                    },
                    {
                        "kind": "portfolio-parameter-neighborhood",
                        "path": "portfolio-parameter-neighborhood.json",
                        "description": (
                            "Exact predeclared local signal-threshold and "
                            "no-trade-band validation/test paths"
                        ),
                    },
                ],
                "errors": [],
            }
        )
    except (JudgeFailure, PortfolioFailure) as error:
        code = getattr(error, "code", "portfolio.failure")
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": str(error),
                "metrics": {},
                "artifacts": [],
                "errors": [{"code": code, "message": str(error)}],
            }
        )
    except Exception as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": f"Portfolio evaluation raised {type(error).__name__}",
                "metrics": {},
                "artifacts": [],
                "errors": [
                    {
                        "code": "portfolio.exception",
                        "message": f"{type(error).__name__}: {error}",
                    }
                ],
            }
        )


if __name__ == "__main__":
    main()
