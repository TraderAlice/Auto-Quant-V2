"""Fixed covariance audit for one reported book and supplied scenarios."""

from __future__ import annotations

import csv
import hashlib
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


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
REPORT_KIND = "autoquant-book-risk-report"
SCENARIO_KIND = "autoquant-book-risk-scenarios"


class JudgeFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()


def _write_output(value: dict[str, Any]) -> None:
    Path(os.environ["AUTOQUANT_RUN_OUTPUT"]).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise JudgeFailure(code, f"Cannot read fixed JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise JudgeFailure(code, f"Fixed JSON input must be an object: {path}")
    return value


def _load_scenarios(project_root: Path) -> dict[str, Any]:
    path = project_root / "strategies" / "book-risk-scenarios.json"
    value = _read_object(path, "book-risk.scenarios")
    if set(value) != {
        "schemaVersion",
        "kind",
        "lookbackBars",
        "primaryLookbackBars",
        "minimumObservations",
        "reductionWeight",
        "rollingStepBars",
    }:
        raise JudgeFailure(
            "book-risk.scenarios",
            "Book-risk scenario fields differ from the fixed contract",
        )
    lookbacks = value.get("lookbackBars")
    if (
        value.get("schemaVersion") != 1
        or value.get("kind") != SCENARIO_KIND
        or not isinstance(lookbacks, list)
        or not 1 <= len(lookbacks) <= 8
        or not all(
            isinstance(item, int)
            and not isinstance(item, bool)
            and 20 <= item <= 2520
            for item in lookbacks
        )
        or len(lookbacks) != len(set(lookbacks))
        or lookbacks != sorted(lookbacks)
        or value.get("primaryLookbackBars") not in lookbacks
        or not isinstance(value.get("minimumObservations"), int)
        or isinstance(value.get("minimumObservations"), bool)
        or not 20 <= value["minimumObservations"] <= min(lookbacks)
        or not isinstance(value.get("rollingStepBars"), int)
        or isinstance(value.get("rollingStepBars"), bool)
        or not 1 <= value["rollingStepBars"] <= 252
        or not isinstance(value.get("reductionWeight"), (int, float))
        or isinstance(value.get("reductionWeight"), bool)
        or not math.isfinite(float(value["reductionWeight"]))
        or not 0 < float(value["reductionWeight"]) <= 0.25
    ):
        raise JudgeFailure(
            "book-risk.scenarios",
            "Book-risk scenario values are outside the fixed bounded contract",
        )
    return {
        **value,
        "reductionWeight": float(value["reductionWeight"]),
    }


def _load_close(
    data_root: Path,
    asset: str,
    start: str,
    end: str,
) -> pd.Series:
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
        frame = multi_interval
    else:
        source = (data_root / "ohlcv" / f"{asset}.csv").resolve()
        if data_root not in source.parents or not source.is_file():
            raise JudgeFailure(
                "dataset.asset",
                f"Missing confined OHLCV file for {asset}",
            )
        frame = pd.read_csv(source)
        if tuple(frame.columns) != REQUIRED_COLUMNS:
            raise JudgeFailure(
                "dataset.columns",
                f"{asset} columns must be exactly {', '.join(REQUIRED_COLUMNS)}",
            )
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"],
            errors="raise",
        )
        for column in REQUIRED_COLUMNS[1:]:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        frame = frame[
            (frame["timestamp"] >= pd.Timestamp(start))
            & (frame["timestamp"] <= pd.Timestamp(end))
        ].copy()
    if (
        len(frame) < 40
        or frame["timestamp"].duplicated().any()
        or not frame["timestamp"].is_monotonic_increasing
        or not np.isfinite(frame["close"].to_numpy(dtype=float)).all()
        or (frame["close"] <= 0).any()
    ):
        raise JudgeFailure(
            "dataset.asset",
            f"{asset} has invalid or insufficient closed price observations",
        )
    return pd.Series(
        frame["close"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(frame["timestamp"]),
        name=asset,
    )


def _covariance_analysis(
    returns: pd.DataFrame,
    weights: pd.Series,
    annualization: int,
) -> dict[str, Any]:
    values = returns.to_numpy(dtype=float)
    covariance = np.atleast_2d(
        np.cov(values, rowvar=False, ddof=0)
    ) * annualization
    if (
        covariance.shape != (len(weights), len(weights))
        or not np.isfinite(covariance).all()
    ):
        raise JudgeFailure(
            "book-risk.covariance",
            "Covariance matrix is invalid",
        )
    weight_values = weights.to_numpy(dtype=float)
    variance = float(weight_values @ covariance @ weight_values)
    if not math.isfinite(variance) or variance <= 1e-18:
        raise JudgeFailure(
            "book-risk.zero-variance",
            "Reported book has no measurable covariance risk",
        )
    volatility = math.sqrt(max(variance, 0.0))
    marginal = covariance @ weight_values
    component_variance = weight_values * marginal
    signed_shares = component_variance / variance
    absolute = np.abs(component_variance)
    absolute_total = float(absolute.sum())
    absolute_shares = (
        absolute / absolute_total
        if absolute_total > 1e-18
        else np.zeros_like(absolute)
    )
    hhi = float(np.square(absolute_shares).sum())
    correlation = returns.corr().to_numpy(dtype=float)
    eigenvalues = np.linalg.eigvalsh(correlation)
    first_pc_share = float(
        max(float(eigenvalues[-1]), 0.0)
        / max(float(eigenvalues.sum()), 1e-18)
    )
    contributions = [
        {
            "asset": asset,
            "weight": float(weight_values[index]),
            "marginalVariance": float(marginal[index]),
            "componentVariance": float(component_variance[index]),
            "signedRiskShare": float(signed_shares[index]),
            "absoluteRiskShare": float(absolute_shares[index]),
        }
        for index, asset in enumerate(weights.index)
    ]
    return {
        "observations": int(len(returns)),
        "annualizedVolatility": volatility,
        "annualizedVariance": variance,
        "componentRiskHhi": hhi,
        "effectiveRiskBets": 1.0 / hhi if hhi > 1e-18 else 0.0,
        "firstPrincipalComponentVarianceShare": first_pc_share,
        "largestAbsoluteRiskContributorShare": float(
            absolute_shares.max(initial=0.0)
        ),
        "contributions": contributions,
        "correlation": correlation,
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _reduction_rows(
    returns: pd.DataFrame,
    weights: pd.Series,
    cash_weight: float,
    annualization: int,
    reduction_weight: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    baseline = _covariance_analysis(
        returns,
        weights,
        annualization,
    )
    for asset in weights.index:
        step = min(reduction_weight, abs(float(weights[asset])))
        candidate = weights.copy()
        candidate[asset] = float(candidate[asset]) - math.copysign(
            step,
            float(candidate[asset]),
        )
        analysis = _covariance_analysis(
            returns,
            candidate,
            annualization,
        )
        volatility_reduction = (
            float(baseline["annualizedVolatility"])
            - float(analysis["annualizedVolatility"])
        )
        rows.append(
            {
                "asset": str(asset),
                "startingWeight": float(weights[asset]),
                "weightReduction": step,
                "resultingWeight": float(candidate[asset]),
                "resultingCashWeight": (
                    cash_weight
                    + math.copysign(step, float(weights[asset]))
                ),
                "annualizedVolatility": float(
                    analysis["annualizedVolatility"]
                ),
                "volatilityReduction": volatility_reduction,
                "volatilityReductionPerWeight": (
                    volatility_reduction / step
                ),
                "componentRiskHhi": float(
                    analysis["componentRiskHhi"]
                ),
                "effectiveRiskBets": float(
                    analysis["effectiveRiskBets"]
                ),
            }
        )
    rows.sort(
        key=lambda item: item["volatilityReductionPerWeight"],
        reverse=True,
    )
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def main() -> None:
    try:
        project_root = Path(os.environ["AUTOQUANT_PROJECT_ROOT"]).resolve()
        data_root = Path(os.environ["AUTOQUANT_DATA_ROOT"]).resolve()
        artifacts = Path(os.environ["AUTOQUANT_ARTIFACTS_DIR"]).resolve()
        study = _read_object(
            Path(os.environ["AUTOQUANT_STUDY_PATH"]),
            "study.invalid",
        )
        snapshot = _read_object(
            project_root / "strategies" / "position-snapshot.json",
            "book-risk.position-snapshot",
        )
        weights_raw = snapshot.get("weights")
        if not isinstance(weights_raw, dict) or len(weights_raw) < 2:
            raise JudgeFailure(
                "book-risk.position-snapshot",
                "Book Risk Study requires at least two reported position weights",
            )
        weights = pd.Series(weights_raw, dtype=float)
        if (
            not np.isfinite(weights.to_numpy(dtype=float)).all()
            or (weights.abs() <= 1e-12).any()
        ):
            raise JudgeFailure(
                "book-risk.position-snapshot",
                "Reported position weights are invalid",
            )
        scenario_snapshots = snapshot.get("scenarios")
        if (
            not isinstance(scenario_snapshots, list)
            or len(scenario_snapshots) > 8
            or not all(isinstance(item, dict) for item in scenario_snapshots)
        ):
            raise JudgeFailure(
                "book-risk.position-scenarios",
                "Position scenarios differ from the bounded fixed contract",
            )
        scenario_weights: list[tuple[dict[str, Any], pd.Series]] = []
        scenario_ids: set[str] = set()
        for scenario in scenario_snapshots:
            raw = scenario.get("weights")
            identifier = scenario.get("id")
            if (
                not isinstance(identifier, str)
                or not identifier
                or identifier in scenario_ids
                or not isinstance(scenario.get("name"), str)
                or not scenario["name"]
                or scenario.get("snapshotKind") != "hypothetical-weights"
                or scenario.get("asOf") != snapshot.get("asOf")
                or scenario.get("baseCurrency") != snapshot.get("baseCurrency")
                or scenario.get("authority")
                != {
                    "positionTruth": "caller-hypothetical-not-authenticated",
                    "tradingAuthority": "none",
                }
                or not isinstance(raw, dict)
                or not raw
            ):
                raise JudgeFailure(
                    "book-risk.position-scenarios",
                    "One position scenario is invalid",
                )
            candidate = pd.Series(raw, dtype=float)
            if (
                not np.isfinite(candidate.to_numpy(dtype=float)).all()
                or (candidate.abs() <= 1e-12).any()
            ):
                raise JudgeFailure(
                    "book-risk.position-scenarios",
                    "Scenario position weights are invalid",
                )
            scenario_ids.add(identifier)
            scenario_weights.append((scenario, candidate))
        scenarios = _load_scenarios(project_root)
        dataset = study.get("dataset")
        if not isinstance(dataset, dict):
            raise JudgeFailure("study.dataset", "Study dataset is invalid")
        universe = dataset.get("universe")
        time_range = dataset.get("time_range")
        if (
            not isinstance(universe, list)
            or not set(weights.index).issubset(universe)
            or not isinstance(time_range, dict)
        ):
            raise JudgeFailure(
                "book-risk.universe",
                "Reported positions are outside the Study universe",
            )
        comparison_assets = list(weights.index)
        for _, candidate in scenario_weights:
            for asset in candidate.index:
                if asset not in comparison_assets:
                    comparison_assets.append(str(asset))
        if not set(comparison_assets).issubset(universe):
            raise JudgeFailure(
                "book-risk.universe",
                "Scenario positions are outside the Study universe",
            )
        closes = pd.concat(
            [
                _load_close(
                    data_root,
                    asset,
                    str(time_range["start"]),
                    str(time_range["end"]),
                )
                for asset in comparison_assets
            ],
            axis=1,
            join="inner",
        ).dropna()
        as_of = pd.Timestamp(snapshot.get("asOf"))
        comparable_as_of = (
            as_of.tz_localize(None)
            if closes.index.tz is None and as_of.tzinfo is not None
            else as_of
        )
        closes = closes.loc[closes.index <= comparable_as_of]
        returns = closes.pct_change(fill_method=None).dropna()
        baseline_returns = returns.loc[:, list(weights.index)]
        minimum = int(scenarios["minimumObservations"])
        if len(returns) < max(minimum, max(scenarios["lookbackBars"])):
            raise JudgeFailure(
                "book-risk.observations",
                "Insufficient common return observations for declared lookbacks",
            )
        annualization = annualization_periods(closes.index)
        lookback_results: list[dict[str, Any]] = []
        analyses: dict[int, dict[str, Any]] = {}
        for lookback in scenarios["lookbackBars"]:
            selected = baseline_returns.tail(lookback)
            analysis = _covariance_analysis(
                selected,
                weights,
                annualization,
            )
            analyses[lookback] = analysis
            window_reductions = _reduction_rows(
                selected,
                weights,
                float(snapshot["cashWeight"]),
                annualization,
                float(scenarios["reductionWeight"]),
            )
            largest = max(
                analysis["contributions"],
                key=lambda item: item["absoluteRiskShare"],
            )
            lookback_results.append(
                {
                    "lookbackBars": lookback,
                    **{
                        key: value
                        for key, value in analysis.items()
                        if key not in {"contributions", "correlation"}
                    },
                    "largestAbsoluteRiskContributor": largest["asset"],
                    "firstReductionAsset": window_reductions[0]["asset"],
                    "firstReductionVolatilityPerWeight": window_reductions[0][
                        "volatilityReductionPerWeight"
                    ],
                }
            )
        primary_lookback = int(scenarios["primaryLookbackBars"])
        primary = analyses[primary_lookback]
        primary_returns = baseline_returns.tail(primary_lookback)
        correlation = primary["correlation"]
        pairwise: list[dict[str, Any]] = []
        for left in range(len(weights)):
            for right in range(left + 1, len(weights)):
                pairwise.append(
                    {
                        "leftAsset": str(weights.index[left]),
                        "rightAsset": str(weights.index[right]),
                        "correlation": float(correlation[left, right]),
                    }
                )
        pairwise.sort(
            key=lambda item: abs(item["correlation"]),
            reverse=True,
        )
        reduction_weight = float(scenarios["reductionWeight"])
        reductions = _reduction_rows(
            primary_returns,
            weights,
            float(snapshot["cashWeight"]),
            annualization,
            reduction_weight,
        )
        comparison_weights = weights.reindex(
            comparison_assets,
            fill_value=0.0,
        )
        comparison_baselines: dict[int, dict[str, Any]] = {}
        scenario_results: list[dict[str, Any]] = []
        for scenario, candidate in scenario_weights:
            complete_candidate = candidate.reindex(
                comparison_assets,
                fill_value=0.0,
            )
            scenario_lookbacks: list[dict[str, Any]] = []
            for lookback in scenarios["lookbackBars"]:
                selected = returns.tail(lookback)
                if lookback not in comparison_baselines:
                    comparison_baselines[lookback] = _covariance_analysis(
                        selected,
                        comparison_weights,
                        annualization,
                    )
                comparison_baseline = comparison_baselines[lookback]
                analysis = _covariance_analysis(
                    selected,
                    complete_candidate,
                    annualization,
                )
                largest = max(
                    analysis["contributions"],
                    key=lambda item: item["absoluteRiskShare"],
                )
                scenario_lookbacks.append(
                    {
                        "lookbackBars": lookback,
                        "observations": int(analysis["observations"]),
                        "annualizedVolatility": float(
                            analysis["annualizedVolatility"]
                        ),
                        "annualizedVolatilityDelta": float(
                            analysis["annualizedVolatility"]
                            - comparison_baseline["annualizedVolatility"]
                        ),
                        "componentRiskHhi": float(
                            analysis["componentRiskHhi"]
                        ),
                        "componentRiskHhiDelta": float(
                            analysis["componentRiskHhi"]
                            - comparison_baseline["componentRiskHhi"]
                        ),
                        "effectiveRiskBets": float(
                            analysis["effectiveRiskBets"]
                        ),
                        "effectiveRiskBetsDelta": float(
                            analysis["effectiveRiskBets"]
                            - comparison_baseline["effectiveRiskBets"]
                        ),
                        "largestAbsoluteRiskContributor": largest["asset"],
                        "largestAbsoluteRiskContributorShare": float(
                            largest["absoluteRiskShare"]
                        ),
                    }
                )
            scenario_results.append(
                {
                    "id": scenario["id"],
                    "name": scenario["name"],
                    "weights": scenario["weights"],
                    "cashWeight": float(scenario["cashWeight"]),
                    "lookbacks": scenario_lookbacks,
                }
            )
        for lookback in scenarios["lookbackBars"]:
            ranked = sorted(
                scenario_results,
                key=lambda item: next(
                    row["annualizedVolatilityDelta"]
                    for row in item["lookbacks"]
                    if row["lookbackBars"] == lookback
                ),
            )
            for rank, scenario in enumerate(ranked, start=1):
                next(
                    row
                    for row in scenario["lookbacks"]
                    if row["lookbackBars"] == lookback
                )["volatilityRank"] = rank
        comparison_rows: list[dict[str, Any]] = []
        scenario_contribution_rows: list[dict[str, Any]] = []
        primary_comparison_baseline = comparison_baselines.get(
            primary_lookback
        )
        if scenario_results and primary_comparison_baseline is None:
            raise JudgeFailure(
                "book-risk.position-scenarios",
                "Primary scenario baseline is unavailable",
            )
        baseline_contributions = {
            row["asset"]: row
            for row in (
                primary_comparison_baseline["contributions"]
                if primary_comparison_baseline is not None
                else []
            )
        }
        for (scenario, candidate), result in zip(
            scenario_weights,
            scenario_results,
            strict=True,
        ):
            for row in result["lookbacks"]:
                comparison_rows.append(
                    {
                        "scenarioId": result["id"],
                        "scenarioName": result["name"],
                        **row,
                    }
                )
            primary_analysis = _covariance_analysis(
                returns.tail(primary_lookback),
                candidate.reindex(comparison_assets, fill_value=0.0),
                annualization,
            )
            scenario_contributions = {
                row["asset"]: row
                for row in primary_analysis["contributions"]
            }
            for asset in comparison_assets:
                baseline_row = baseline_contributions[asset]
                scenario_row = scenario_contributions[asset]
                baseline_weight = float(comparison_weights[asset])
                scenario_weight = float(
                    candidate.reindex(
                        comparison_assets,
                        fill_value=0.0,
                    )[asset]
                )
                scenario_contribution_rows.append(
                    {
                        "scenarioId": scenario["id"],
                        "asset": asset,
                        "baselineWeight": baseline_weight,
                        "scenarioWeight": scenario_weight,
                        "weightDelta": scenario_weight - baseline_weight,
                        "baselineComponentVariance": float(
                            baseline_row["componentVariance"]
                        ),
                        "scenarioComponentVariance": float(
                            scenario_row["componentVariance"]
                        ),
                        "componentVarianceDelta": float(
                            scenario_row["componentVariance"]
                            - baseline_row["componentVariance"]
                        ),
                        "baselineAbsoluteRiskShare": float(
                            baseline_row["absoluteRiskShare"]
                        ),
                        "scenarioAbsoluteRiskShare": float(
                            scenario_row["absoluteRiskShare"]
                        ),
                        "absoluteRiskShareDelta": float(
                            scenario_row["absoluteRiskShare"]
                            - baseline_row["absoluteRiskShare"]
                        ),
                    }
                )
        rolling: list[dict[str, Any]] = []
        step = int(scenarios["rollingStepBars"])
        positions = list(
            range(primary_lookback, len(baseline_returns) + 1, step)
        )
        if not positions or positions[-1] != len(baseline_returns):
            positions.append(len(baseline_returns))
        for stop in positions:
            selected = baseline_returns.iloc[
                max(0, stop - primary_lookback) : stop
            ]
            if len(selected) < minimum:
                continue
            analysis = _covariance_analysis(
                selected,
                weights,
                annualization,
            )
            rolling.append(
                {
                    "timestamp": timestamp_label(selected.index[-1]),
                    "observations": int(len(selected)),
                    "annualizedVolatility": float(
                        analysis["annualizedVolatility"]
                    ),
                    "componentRiskHhi": float(
                        analysis["componentRiskHhi"]
                    ),
                    "effectiveRiskBets": float(
                        analysis["effectiveRiskBets"]
                    ),
                    "firstPrincipalComponentVarianceShare": float(
                        analysis["firstPrincipalComponentVarianceShare"]
                    ),
                }
            )
        report = {
            "schemaVersion": 1,
            "kind": REPORT_KIND,
            "requestHash": snapshot["source"]["requestHash"],
            "positionSnapshot": snapshot,
            "authority": {
                "positionTruth": "external-reported-not-authenticated",
                "marketEvidence": "content-locked-closed-ohlcv",
                "tradingAuthority": "none",
                "reductionMeaning": "standardized-historical-sensitivity",
                "scenarioMeaning": "caller-specified-historical-comparison",
            },
            "method": scenarios,
            "dataset": {
                "id": dataset.get("id"),
                "version": dataset.get("version"),
                "assetClass": dataset.get("asset_class"),
                "universe": universe,
                "heldAssets": list(weights.index),
                "marketDataEnd": timestamp_label(closes.index[-1]),
                "annualizationPeriods": annualization,
            },
            "lookbacks": lookback_results,
            "current": {
                **{
                    key: value
                    for key, value in primary.items()
                    if key not in {"contributions", "correlation"}
                },
                "lookbackBars": primary_lookback,
                "grossExposure": float(weights.abs().sum()),
                "netExposure": float(weights.sum()),
                "cashWeight": float(snapshot["cashWeight"]),
            },
            "contributions": sorted(
                primary["contributions"],
                key=lambda item: item["absoluteRiskShare"],
                reverse=True,
            ),
            "pairwiseCorrelations": pairwise,
            "reductions": reductions,
            "scenarioComparison": {
                "comparisonUniverse": comparison_assets,
                "baselineLookbacks": [
                    {
                        "lookbackBars": lookback,
                        "observations": int(
                            comparison_baselines[lookback]["observations"]
                        ),
                        "annualizedVolatility": float(
                            comparison_baselines[lookback][
                                "annualizedVolatility"
                            ]
                        ),
                        "componentRiskHhi": float(
                            comparison_baselines[lookback][
                                "componentRiskHhi"
                            ]
                        ),
                        "effectiveRiskBets": float(
                            comparison_baselines[lookback][
                                "effectiveRiskBets"
                            ]
                        ),
                    }
                    for lookback in scenarios["lookbackBars"]
                    if lookback in comparison_baselines
                ],
                "scenarios": scenario_results,
                "ranking": {
                    "metric": "annualizedVolatilityDelta",
                    "direction": "minimize",
                    "selectionAuthority": "none",
                },
            },
            "rollingSummary": {
                "observations": len(rolling),
                "start": rolling[0]["timestamp"],
                "end": rolling[-1]["timestamp"],
                "minimumEffectiveRiskBets": min(
                    row["effectiveRiskBets"] for row in rolling
                ),
                "maximumComponentRiskHhi": max(
                    row["componentRiskHhi"] for row in rolling
                ),
            },
        }
        (artifacts / "book-risk-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_csv(
            artifacts / "book-risk-contributions.csv",
            [
                "asset",
                "weight",
                "marginalVariance",
                "componentVariance",
                "signedRiskShare",
                "absoluteRiskShare",
            ],
            report["contributions"],
        )
        _write_csv(
            artifacts / "book-risk-reductions.csv",
            [
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
            ],
            reductions,
        )
        _write_csv(
            artifacts / "book-risk-correlations.csv",
            ["leftAsset", "rightAsset", "correlation"],
            pairwise,
        )
        _write_csv(
            artifacts / "book-risk-path.csv",
            [
                "timestamp",
                "observations",
                "annualizedVolatility",
                "componentRiskHhi",
                "effectiveRiskBets",
                "firstPrincipalComponentVarianceShare",
            ],
            rolling,
        )
        _write_csv(
            artifacts / "book-risk-scenario-comparisons.csv",
            [
                "scenarioId",
                "scenarioName",
                "volatilityRank",
                "lookbackBars",
                "observations",
                "annualizedVolatility",
                "annualizedVolatilityDelta",
                "componentRiskHhi",
                "componentRiskHhiDelta",
                "effectiveRiskBets",
                "effectiveRiskBetsDelta",
                "largestAbsoluteRiskContributor",
                "largestAbsoluteRiskContributorShare",
            ],
            comparison_rows,
        )
        _write_csv(
            artifacts / "book-risk-scenario-contributions.csv",
            [
                "scenarioId",
                "asset",
                "baselineWeight",
                "scenarioWeight",
                "weightDelta",
                "baselineComponentVariance",
                "scenarioComponentVariance",
                "componentVarianceDelta",
                "baselineAbsoluteRiskShare",
                "scenarioAbsoluteRiskShare",
                "absoluteRiskShareDelta",
            ],
            scenario_contribution_rows,
        )
        metrics = {
            "current_component_risk_hhi": float(
                primary["componentRiskHhi"]
            ),
            "current_effective_risk_bets": float(
                primary["effectiveRiskBets"]
            ),
            "current_annualized_volatility": float(
                primary["annualizedVolatility"]
            ),
            "current_first_pc_variance_share": float(
                primary["firstPrincipalComponentVarianceShare"]
            ),
            "largest_risk_contributor_share": float(
                primary["largestAbsoluteRiskContributorShare"]
            ),
            "primary_lookback_bars": primary_lookback,
            "held_assets": len(weights),
            "scenario_count": len(scenario_results),
        }
        primary_scenario_order = sorted(
            scenario_results,
            key=lambda item: next(
                row["volatilityRank"]
                for row in item["lookbacks"]
                if row["lookbackBars"] == primary_lookback
            ),
        )
        _write_output(
            {
                "schema_version": 1,
                "status": "succeeded",
                "summary": (
                    "Reported book covariance audit; effective risk bets="
                    f"{metrics['current_effective_risk_bets']:.3f}; "
                    f"first standardized reduction={reductions[0]['asset']}; "
                    f"supplied scenarios={len(scenario_results)}"
                    + (
                        "; lowest primary-window volatility scenario="
                        f"{primary_scenario_order[0]['id']}"
                        if primary_scenario_order
                        else ""
                    )
                ),
                "metrics": metrics,
                "artifacts": [
                    {
                        "kind": "book-risk-report",
                        "path": "book-risk-report.json",
                        "description": (
                            "Verified reported-book covariance, crowding, "
                            "contribution, and reduction evidence"
                        ),
                    },
                    {
                        "kind": "book-risk-contributions",
                        "path": "book-risk-contributions.csv",
                        "description": "Per-asset component-risk ledger",
                    },
                    {
                        "kind": "book-risk-reductions",
                        "path": "book-risk-reductions.csv",
                        "description": (
                            "Standardized cash-funded reduction sensitivities"
                        ),
                    },
                    {
                        "kind": "book-risk-correlations",
                        "path": "book-risk-correlations.csv",
                        "description": "Primary-window held-asset correlations",
                    },
                    {
                        "kind": "book-risk-path",
                        "path": "book-risk-path.csv",
                        "description": "Sampled rolling primary-window risk path",
                    },
                    {
                        "kind": "book-risk-scenario-comparisons",
                        "path": "book-risk-scenario-comparisons.csv",
                        "description": (
                            "Caller-specified funded-book lookback comparisons"
                        ),
                    },
                    {
                        "kind": "book-risk-scenario-contributions",
                        "path": "book-risk-scenario-contributions.csv",
                        "description": (
                            "Primary-window per-asset scenario contribution "
                            "changes"
                        ),
                    },
                ],
                "errors": [],
            }
        )
    except JudgeFailure as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": str(error),
                "metrics": {},
                "artifacts": [],
                "errors": [{"code": error.code, "message": str(error)}],
            }
        )
    except Exception as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": f"Book-risk evaluation raised {type(error).__name__}",
                "metrics": {},
                "artifacts": [],
                "errors": [
                    {
                        "code": "book-risk.exception",
                        "message": f"{type(error).__name__}: {error}",
                    }
                ],
            }
        )


if __name__ == "__main__":
    main()
