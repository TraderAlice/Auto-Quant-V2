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

from judges.portfolio_core import (
    BASE_COST_BPS,
    GROSS_TARGET,
    LONG_ENTRY_PERCENTILE,
    LONG_EXIT_PERCENTILE,
    MAX_ABS_WEIGHT,
    NO_TRADE_ONE_WAY,
    REFERENCE_NAV,
    RISK_COVARIANCE_MINIMUM,
    RISK_COVARIANCE_WINDOW,
    SHORT_ENTRY_PERCENTILE,
    SHORT_EXIT_PERCENTILE,
    VOLATILITY_WINDOW,
    PortfolioFailure,
    attribution_metrics,
    build_decision_ledger,
    constraint_audit,
    construct_signal_policy,
    implementation_metrics,
    performance_metrics,
    signal_policy_metrics,
    simulate_targets,
)


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
MIN_ASSETS_PER_DATE = 4
MIN_SPLIT_OBSERVATIONS = 20


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


def _load_asset(data_root: Path, asset: str, start: str, end: str) -> pd.DataFrame:
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
            "start": index[start].date().isoformat(),
            "end": index[stop - 1].date().isoformat(),
            "signalEnd": index[stop - 2].date().isoformat(),
            "targetEnd": index[stop - 1].date().isoformat(),
            "eligibleSignalRows": len(eligible),
            "purgedBoundaryRows": 1,
        }
    return splits, protocol


def _evaluate() -> tuple[
    dict[str, Any],
    dict[str, Any],
    Any,
    Any,
    pd.DataFrame,
]:
    study, data_root = _load_contract()
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
    factor_evidence = _daily_factor_evidence(factor_panel, forward_returns)
    construction = construct_signal_policy(factor_panel, close_panel)
    targets = construction.targets
    audit = constraint_audit(targets)
    if not audit["passed"]:
        raise JudgeFailure(
            "portfolio.constraints",
            "Fixed target construction violated its declared constraints",
        )
    base = simulate_targets(targets, close_panel, volume_panel)
    decision_ledger = build_decision_ledger(
        construction,
        base,
        close_panel,
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

    validation_net_sharpe = float(
        portfolio_metrics["validation"]["net"]["sharpe"]
    )
    cost_stress: dict[str, Any] = {}
    for cost_bps in (0.0, BASE_COST_BPS, 25.0):
        simulation = simulate_targets(
            targets,
            close_panel,
            volume_panel,
            cost_bps=cost_bps,
        )
        key = f"{int(cost_bps)}bps"
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
    )
    no_hysteresis_simulation = simulate_targets(
        no_hysteresis.targets,
        close_panel,
        volume_panel,
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
    test_index = splits["test"]
    contribution = (
        base.weights.loc[test_index]
        * forward_returns.loc[test_index]
    ).mean() * 252
    per_asset_contribution = {
        asset: float(value)
        for asset, value in contribution.items()
    }
    metrics = {
        "validation_net_sharpe": validation_net_sharpe,
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
                "gross_target": GROSS_TARGET,
                "max_abs_weight": MAX_ABS_WEIGHT,
                "no_trade_one_way": NO_TRADE_ONE_WAY,
            },
            "train": policy_metrics["train"],
            "validation": policy_metrics["validation"],
            "test": policy_metrics["test"],
            "hysteresis_comparison": hysteresis_comparison,
        },
        "attribution": attribution,
        "split_protocol": split_protocol,
        "robustness": {
            "cost_stress": cost_stress,
            "extra_delay": delay_stress,
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
        "semantics": {
            "simulation": "bar-target-weight",
            "decision": "OHLCV and factor known through close t",
            "return": "close t to close t+1",
            "factorTransform": (
                "cross-sectional percentile state machine with inverse-volatility "
                "conviction sizing"
            ),
            "signalState": (
                "long entry/exit 0.75/0.55; short entry/exit 0.25/0.45; "
                "direct reversal at opposite entry"
            ),
            "portfolio": "gross 1.0, long +0.5, short -0.5, max abs weight 0.30",
            "noTrade": "retain drifted book below 0.05 one-way turnover",
            "turnover": "0.5 * sum(abs(trade weight))",
            "cost": "sum(abs(trade weight)) * 10bps",
            "benchmark": "equal-weight long-only next-bar return",
            "split": (
                "dataset-fixed chronological 60/20/20 with one-bar "
                "boundary purge"
            ),
            "score": "validation net Sharpe at 10bps only",
            "testRole": (
                "visible diagnostic evidence; never enters candidate selection"
            ),
            "tradingAuthority": "none",
        },
        "fixedParameters": {
            "volatilityWindow": VOLATILITY_WINDOW,
            "grossTarget": GROSS_TARGET,
            "maxAbsWeight": MAX_ABS_WEIGHT,
            "noTradeOneWay": NO_TRADE_ONE_WAY,
            "baseCostBps": BASE_COST_BPS,
            "referenceNav": REFERENCE_NAV,
            "longEntryPercentile": LONG_ENTRY_PERCENTILE,
            "longExitPercentile": LONG_EXIT_PERCENTILE,
            "shortExitPercentile": SHORT_EXIT_PERCENTILE,
            "shortEntryPercentile": SHORT_ENTRY_PERCENTILE,
            "riskCovarianceWindow": RISK_COVARIANCE_WINDOW,
            "riskCovarianceMinimum": RISK_COVARIANCE_MINIMUM,
        },
        "causalityAuditCuts": causality_cuts,
        "splitProtocol": split_protocol,
        "metrics": metrics,
    }
    return metrics, report, base, construction, decision_ledger


def main() -> None:
    try:
        (
            metrics,
            report,
            simulation,
            construction,
            decision_ledger,
        ) = _evaluate()
        artifacts = Path(os.environ["AUTOQUANT_ARTIFACTS_DIR"])
        report_path = artifacts / "portfolio-report.json"
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        daily = simulation.daily.copy()
        daily.index.name = "timestamp"
        daily.to_csv(artifacts / "daily-portfolio.csv", float_format="%.12g")
        proposed_targets = construction.targets.copy()
        proposed_targets.index.name = "timestamp"
        proposed_targets.to_csv(
            artifacts / "proposed-target-weights.csv",
            float_format="%.12g",
        )
        executed_weights = simulation.weights.copy()
        executed_weights.index.name = "timestamp"
        executed_weights.to_csv(
            artifacts / "executed-weights.csv",
            float_format="%.12g",
        )
        decision_ledger.to_csv(
            artifacts / "portfolio-decisions.csv",
            index=False,
            date_format="%Y-%m-%d",
            float_format="%.12g",
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
                            "trade, contribution, cost, regime, and variance "
                            "attribution ledger"
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
