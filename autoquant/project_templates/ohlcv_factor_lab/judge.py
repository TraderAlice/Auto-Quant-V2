"""Fixed no-lookahead Judge for the OHLCV Factor Lab reference Project."""

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
    load_multi_interval_asset,
    timestamp_label,
)
from judges.factor_diagnostics import (
    HORIZONS,
    REGIME_NAMES,
    STYLE_NAMES,
    causal_regime_labels,
    chronological_fold_masks,
    cross_sectional_rank_residual,
    daily_pearson_correlation,
    daily_quantile_returns,
    daily_rank_correlation,
    descriptive_ic,
    equal_rank_blend,
    forward_return_panels,
    per_asset_rank_correlation,
    purged_split_masks,
    quantile_summary,
    style_proxy_panels,
)


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
MIN_ASSETS_PER_DATE = 4
MIN_IC_DATES_PER_SPLIT = 20


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
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
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


def _split_metrics(values: pd.Series) -> dict[str, Any]:
    if len(values) < MIN_IC_DATES_PER_SPLIT:
        raise JudgeFailure(
            "judge.population",
            f"Chronological split has only {len(values)} valid IC dates",
        )
    return descriptive_ic(
        values,
        minimum_observations=MIN_IC_DATES_PER_SPLIT,
    )


def _masked(values: pd.Series, mask: pd.Series) -> pd.Series:
    return values.reindex(mask.index[mask]).dropna()


def _style_summary(values: pd.Series) -> dict[str, float | int | None]:
    clean = values.dropna().astype(float)
    if len(clean) < 3:
        return {
            "mean_rank_correlation": None,
            "mean_absolute_rank_correlation": None,
            "observations": int(len(clean)),
        }
    return {
        "mean_rank_correlation": float(clean.mean()),
        "mean_absolute_rank_correlation": float(clean.abs().mean()),
        "observations": int(len(clean)),
    }


def _decay_summary(
    horizon_metrics: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for split in ("train", "validation", "test"):
        means = {
            horizon: horizon_metrics[horizon][split]["mean_ic"]
            for horizon in (str(item) for item in HORIZONS)
        }
        one_bar = means["1"]
        ratios: dict[str, float | None] = {}
        for horizon in ("5", "10"):
            value = means[horizon]
            ratios[f"horizon_{horizon}_to_1"] = (
                float(value) / float(one_bar)
                if value is not None
                and one_bar is not None
                and abs(float(one_bar)) > 1e-12
                else None
            )
        result[split] = {
            "mean_ic_by_horizon": means,
            **ratios,
        }
    return result


def _factor_qualification(
    factor_panel: pd.DataFrame,
    styles: dict[str, pd.DataFrame],
    forward_panels: dict[int, pd.DataFrame],
    split_masks: dict[int, dict[str, pd.Series]],
    fold_masks: dict[str, pd.Series],
    split_labels: pd.Series,
    style_correlations: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Build train-selected style-neutral and blend evidence."""

    candidates = {
        name: {
            "mean_rank_correlation": style_correlations["train"][name][
                "mean_rank_correlation"
            ],
            "mean_absolute_rank_correlation": style_correlations["train"][
                name
            ]["mean_absolute_rank_correlation"],
            "observations": style_correlations["train"][name][
                "observations"
            ],
        }
        for name in STYLE_NAMES
    }
    finite = [
        (name, value["mean_rank_correlation"])
        for name, value in candidates.items()
        if value["mean_rank_correlation"] is not None
    ]
    if not finite:
        raise JudgeFailure(
            "factor.qualification-style",
            "No finite train-only style overlap is available",
        )
    dominant_style = min(
        finite,
        key=lambda item: (-abs(float(item[1])), item[0]),
    )[0]
    style_panel = styles[dominant_style].reindex_like(factor_panel)
    residual_panel = cross_sectional_rank_residual(
        factor_panel,
        style_panel,
        minimum_assets=MIN_ASSETS_PER_DATE,
    )
    blend_panel = equal_rank_blend(factor_panel, style_panel)
    panels = {
        "candidate": factor_panel,
        "dominant_style": style_panel,
        "style_neutral_candidate": residual_panel,
        "equal_rank_blend": blend_panel,
    }
    daily = {
        signal: {
            horizon: daily_rank_correlation(
                panel,
                forward_panels[horizon],
                minimum_assets=MIN_ASSETS_PER_DATE,
                constant_left_value=(
                    0.0
                    if signal == "style_neutral_candidate"
                    else None
                ),
            )
            for horizon in HORIZONS
        }
        for signal, panel in panels.items()
    }
    horizon_quality = {
        str(horizon): {
            split: {
                signal: _split_metrics(
                    _masked(
                        daily[signal][horizon],
                        split_masks[horizon][split],
                    )
                )
                for signal in panels
            }
            for split in ("train", "validation", "test")
        }
        for horizon in HORIZONS
    }
    residual_folds = {
        name: descriptive_ic(
            _masked(daily["style_neutral_candidate"][1], mask)
        )
        for name, mask in fold_masks.items()
    }
    evidence = pd.DataFrame(
        {
            "split": split_labels,
            "dominant_style": dominant_style,
        },
        index=factor_panel.index,
    )
    for horizon in HORIZONS:
        eligible = (
            split_masks[horizon]["train"]
            | split_masks[horizon]["validation"]
            | split_masks[horizon]["test"]
        )
        for signal in panels:
            evidence[f"{signal}_rank_ic_h{horizon}"] = (
                daily[signal][horizon]
                .reindex(factor_panel.index)
                .where(eligible)
            )
    evidence.index.name = "timestamp"
    return {
        "method": "train-selected-one-style-rank-neutralization-v1",
        "selection": {
            "split": "train",
            "criterion": "maximum-absolute-mean-daily-rank-overlap",
            "dominant_style": dominant_style,
            "candidates": candidates,
            "validation_enters_selection": False,
            "test_enters_selection": False,
        },
        "semantics": {
            "neutralization": (
                "same-timestamp-cross-sectional-centered-rank-ols"
            ),
            "blend": "equal-weight-cross-sectional-percentile-ranks",
            "target_enters_neutralization": False,
            "selection_authority": "research-context-only",
            "trading_authority": "none",
        },
        "horizon_quality": horizon_quality,
        "stability": {
            "style_neutral_chronological_folds": residual_folds,
        },
    }, evidence


def _evaluate() -> tuple[
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
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

    factor_by_asset: dict[str, pd.Series] = {}
    close_by_asset: dict[str, pd.Series] = {}
    volume_by_asset: dict[str, pd.Series] = {}
    audited: dict[str, list[int]] = {}
    coverage: dict[str, float] = {}
    for asset in universe:
        frame = _load_asset(
            data_root,
            asset,
            time_range["start"],
            time_range["end"],
        )
        factor = _factor_series(module, frame, asset)
        audited[asset] = _audit_causality(module, frame, factor, asset)
        timestamp = pd.DatetimeIndex(frame["timestamp"])
        factor.index = timestamp
        close = frame["close"].copy()
        close.index = timestamp
        volume = frame["volume"].copy()
        volume.index = timestamp
        factor_by_asset[asset] = factor
        close_by_asset[asset] = close
        volume_by_asset[asset] = volume
        coverage[asset] = float(factor.notna().mean())

    factor_panel = pd.DataFrame(factor_by_asset).sort_index()
    close_panel = pd.DataFrame(close_by_asset).reindex(factor_panel.index)
    volume_panel = pd.DataFrame(volume_by_asset).reindex(factor_panel.index)
    timeline = pd.DatetimeIndex(factor_panel.index)
    split_masks, split_protocol, base_split_labels = purged_split_masks(timeline)
    fold_masks, fold_protocol = chronological_fold_masks(timeline)
    forward_panels = forward_return_panels(close_panel)
    daily_ic_by_horizon = {
        horizon: daily_rank_correlation(
            factor_panel,
            forward_panels[horizon],
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        for horizon in HORIZONS
    }
    daily_pearson_by_horizon = {
        horizon: daily_pearson_correlation(
            factor_panel,
            forward_panels[horizon],
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        for horizon in HORIZONS
    }
    horizon_metrics = {
        str(horizon): {
            split: {
                **_split_metrics(
                    _masked(
                        daily_ic_by_horizon[horizon],
                        split_masks[horizon][split],
                    )
                ),
                "pearson_ic": _split_metrics(
                    _masked(
                        daily_pearson_by_horizon[horizon],
                        split_masks[horizon][split],
                    )
                ),
            }
            for split in ("train", "validation", "test")
        }
        for horizon in HORIZONS
    }
    splits = horizon_metrics["1"]
    validation_mean_ic = float(splits["validation"]["mean_ic"])

    quantile_daily = {
        horizon: daily_quantile_returns(
            factor_panel,
            forward_panels[horizon],
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        for horizon in HORIZONS
    }
    quantile_analysis = {
        str(horizon): {
            split: quantile_summary(
                quantile_daily[horizon].reindex(
                    split_masks[horizon][split].index[
                        split_masks[horizon][split]
                    ]
                )
            )
            for split in ("train", "validation", "test")
        }
        for horizon in HORIZONS
    }

    one_bar_ic = daily_ic_by_horizon[1]
    chronological_folds = {
        name: descriptive_ic(_masked(one_bar_ic, mask))
        for name, mask in fold_masks.items()
    }
    regimes = causal_regime_labels(close_panel)
    regime_stability = {
        split: {
            regime: descriptive_ic(
                _masked(
                    one_bar_ic,
                    split_masks[1][split]
                    & regimes.eq(regime).fillna(False),
                )
            )
            for regime in REGIME_NAMES
        }
        for split in ("train", "validation", "test")
    }
    styles = style_proxy_panels(close_panel, volume_panel)
    style_correlations: dict[str, dict[str, Any]] = {
        split: {}
        for split in ("train", "validation", "test")
    }
    for style in STYLE_NAMES:
        daily_style = daily_rank_correlation(
            factor_panel,
            styles[style],
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        for split in style_correlations:
            style_correlations[split][style] = _style_summary(
                _masked(daily_style, split_masks[1][split])
            )
    factor_qualification, qualification_evidence = _factor_qualification(
        factor_panel,
        styles,
        forward_panels,
        split_masks,
        fold_masks,
        base_split_labels,
        style_correlations,
    )
    per_asset_stability = {
        split: per_asset_rank_correlation(
            factor_panel,
            forward_panels[1],
            split_masks[1][split],
        )
        for split in ("train", "validation", "test")
    }

    ranked = factor_panel.rank(axis=1, pct=True)
    turnover = float(ranked.diff().abs().mean(axis=1).dropna().mean())
    metrics = {
        "validation_mean_ic": validation_mean_ic,
        "train": splits["train"],
        "validation": splits["validation"],
        "test": splits["test"],
        "horizon_quality": horizon_metrics,
        "factor_decay": _decay_summary(horizon_metrics),
        "quantile_analysis": quantile_analysis,
        "stability": {
            "chronological_folds": chronological_folds,
            "causal_regimes": regime_stability,
            "per_asset": per_asset_stability,
        },
        "style_correlations": style_correlations,
        "factor_qualification": factor_qualification,
        "split_protocol": {
            **split_protocol,
            "folds": fold_protocol,
        },
        "mean_coverage": float(sum(coverage.values()) / len(coverage)),
        "mean_rank_turnover": turnover,
        "assets": int(len(universe)),
        "ic_dates": int(len(one_bar_ic)),
        "research_integrity": {
            "selection_split": "validation",
            "test_role": "visible-diagnostic",
            "test_enters_selection": False,
            "external_holdout_rule": (
                "required-after-test-guided-iteration"
            ),
        },
    }
    if not all(
        math.isfinite(float(value))
        for value in (
            validation_mean_ic,
            metrics["mean_coverage"],
            metrics["mean_rank_turnover"],
        )
    ):
        raise JudgeFailure("judge.non-finite", "Judge produced non-finite metrics")
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
            "target": "next-bar close-to-close return",
            "measure": (
                "per-date cross-sectional Spearman rank IC and Pearson IC"
            ),
            "horizons": list(HORIZONS),
            "split": (
                "dataset-fixed chronological 60/20/20 with horizon-specific "
                "boundary purge"
            ),
            "score": "validation one-bar mean rank IC only",
            "inference": (
                "Newey-West/Bartlett HAC mean t-statistic with maximum lag 5 "
                "and two-sided normal-approximation p-value"
            ),
            "quantiles": "fixed low/middle/high cross-sectional groups",
            "regimes": (
                "causal trailing market direction and volatility versus "
                "lagged rolling threshold"
            ),
            "styles": list(STYLE_NAMES),
            "qualification": {
                "method": factor_qualification["method"],
                "styleSelection": "train-only",
                "neutralization": factor_qualification["semantics"][
                    "neutralization"
                ],
                "blend": factor_qualification["semantics"]["blend"],
                "testRole": "visible audit only",
                "tradingAuthority": "none",
            },
            "testRole": (
                "visible diagnostic evidence; never enters candidate selection"
            ),
        },
        "causalityAuditCuts": audited,
        "coverageByAsset": coverage,
        "splitProtocol": split_protocol,
        "foldProtocol": fold_protocol,
        "metrics": metrics,
    }
    daily_evidence = pd.DataFrame(
        {
            "split": base_split_labels,
            "regime": regimes.fillna("unavailable"),
        },
        index=timeline,
    )
    for horizon in HORIZONS:
        eligible = (
            split_masks[horizon]["train"]
            | split_masks[horizon]["validation"]
            | split_masks[horizon]["test"]
        )
        daily_evidence[f"rank_ic_h{horizon}"] = (
            daily_ic_by_horizon[horizon].reindex(timeline).where(eligible)
        )
        daily_evidence[f"pearson_ic_h{horizon}"] = (
            daily_pearson_by_horizon[horizon].reindex(timeline).where(eligible)
        )
    daily_evidence.index.name = "timestamp"

    quantile_rows: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        for split in ("train", "validation", "test"):
            selected = quantile_daily[horizon].reindex(
                split_masks[horizon][split].index[
                    split_masks[horizon][split]
                ]
            ).dropna()
            for timestamp, row in selected.iterrows():
                quantile_rows.append(
                    {
                        "timestamp": timestamp,
                        "split": split,
                        "horizon": horizon,
                        "low": float(row["low"]),
                        "middle": float(row["middle"]),
                        "high": float(row["high"]),
                        "high_minus_low": float(row["high_minus_low"]),
                    }
                )
    quantile_evidence = pd.DataFrame(quantile_rows)
    return (
        metrics,
        report,
        daily_evidence,
        quantile_evidence,
        qualification_evidence,
    )


def main() -> None:
    try:
        (
            metrics,
            report,
            daily_evidence,
            quantile_evidence,
            qualification_evidence,
        ) = _evaluate()
        artifacts = Path(os.environ["AUTOQUANT_ARTIFACTS_DIR"])
        report_path = artifacts / "factor-report.json"
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        daily_artifact = daily_evidence.copy()
        daily_artifact.index = [
            timestamp_label(value) for value in daily_artifact.index
        ]
        daily_artifact.index.name = "timestamp"
        quantile_artifact = quantile_evidence.copy()
        quantile_artifact["timestamp"] = quantile_artifact["timestamp"].map(
            timestamp_label
        )
        qualification_artifact = qualification_evidence.copy()
        qualification_artifact.index = [
            timestamp_label(value) for value in qualification_artifact.index
        ]
        qualification_artifact.index.name = "timestamp"
        daily_artifact.to_csv(
            artifacts / "daily-factor-evidence.csv",
            float_format="%.17g",
        )
        quantile_artifact.to_csv(
            artifacts / "factor-quantiles.csv",
            index=False,
            float_format="%.17g",
        )
        qualification_artifact.to_csv(
            artifacts / "factor-qualification.csv",
            float_format="%.17g",
        )
        _write_output(
            {
                "schema_version": 1,
                "status": "succeeded",
                "summary": (
                    "Causal purge-aware factor tear sheet completed; "
                    "validation one-bar mean rank IC="
                    f"{metrics['validation_mean_ic']:.6f}"
                ),
                "metrics": metrics,
                "artifacts": [
                    {
                        "kind": "factor-report",
                        "path": "factor-report.json",
                        "description": (
                            "Factor semantics, purged split protocol, complete "
                            "tear sheet, coverage, and causality audit"
                        ),
                    },
                    {
                        "kind": "factor-daily",
                        "path": "daily-factor-evidence.csv",
                        "description": (
                            "Timestamped split, causal regime, and purge-aware "
                            "1/5/10-bar rank and Pearson IC"
                        ),
                    },
                    {
                        "kind": "factor-quantiles",
                        "path": "factor-quantiles.csv",
                        "description": (
                            "Timestamped fixed-tertile forward returns and "
                            "high-minus-low spread by split and horizon"
                        ),
                    },
                    {
                        "kind": "factor-qualification",
                        "path": "factor-qualification.csv",
                        "description": (
                            "Train-selected style, candidate/style/residual/"
                            "blend daily rank IC, and visible-test audit"
                        ),
                    }
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
    except Exception as error:  # Preserve candidate/Judge diagnostics as evidence.
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": f"Factor evaluation raised {type(error).__name__}",
                "metrics": {},
                "artifacts": [],
                "errors": [
                    {
                        "code": "factor.exception",
                        "message": f"{type(error).__name__}: {error}",
                    }
                ],
            }
        )


if __name__ == "__main__":
    main()
