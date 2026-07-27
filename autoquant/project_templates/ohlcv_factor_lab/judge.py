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

from autoquant.factor_runtime import (
    FactorRuntimeError,
    build_factor_panel,
    evaluate_factor,
    factor_contract,
    values_to_wide,
)
from autoquant.intervals import (
    IntervalContractError,
    load_multi_interval_asset,
    timestamp_label,
)
from autoquant.horizons import (
    RESEARCH_HORIZON,
    load_research_horizon,
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
PRIMARY_HORIZON = 1


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


def _load_horizon() -> dict[str, Any]:
    path = Path(os.environ["AUTOQUANT_PROJECT_ROOT"]) / RESEARCH_HORIZON
    try:
        return load_research_horizon(path)
    except Exception as error:
        raise JudgeFailure(
            "horizon.contract",
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


def _component_split_metrics(values: pd.Series) -> dict[str, Any]:
    """Disclose sparse component evidence without failing a valid final factor."""

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


def _equal_rank_component_blend(
    panels: dict[str, pd.DataFrame],
    *,
    common_available: pd.DataFrame | None = None,
) -> pd.DataFrame:
    names = list(panels)
    first = panels[names[0]]
    if common_available is None:
        common_available = pd.DataFrame(
            True,
            index=first.index,
            columns=first.columns,
        )
        for panel in panels.values():
            common_available &= panel.notna()
    ranks = [
        panel.rank(axis=1, method="average", pct=True)
        for panel in panels.values()
    ]
    return (sum(ranks) / float(len(ranks))).where(common_available)


def _component_evidence(
    declarations: list[dict[str, Any]],
    component_panels: dict[str, pd.DataFrame],
    factor_panel: pd.DataFrame,
    forward_panels: dict[int, pd.DataFrame],
    split_masks: dict[int, dict[str, pd.Series]],
    coverage: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Build target-fixed diagnostics for candidate-declared components."""

    names = list(component_panels)
    raw_daily = {
        name: {
            horizon: daily_rank_correlation(
                component_panels[name],
                forward_panels[horizon],
                minimum_assets=MIN_ASSETS_PER_DATE,
            )
            for horizon in HORIZONS
        }
        for name in names
    }
    raw_quality = {
        name: {
            str(horizon): {
                split: _component_split_metrics(
                    _masked(
                        raw_daily[name][horizon],
                        split_masks[horizon][split],
                    )
                )
                for split in ("train", "validation", "test")
            }
            for horizon in HORIZONS
        }
        for name in names
    }
    composite_association_daily = {
        name: daily_rank_correlation(
            component_panels[name],
            factor_panel,
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        for name in names
    }
    composite_association = {
        name: {
            split: _style_summary(
                _masked(
                    composite_association_daily[name],
                    split_masks[PRIMARY_HORIZON][split],
                )
            )
            for split in ("train", "validation", "test")
        }
        for name in names
    }

    pair_daily: dict[frozenset[str], pd.Series] = {}
    pairwise: list[dict[str, Any]] = []
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            daily = daily_rank_correlation(
                component_panels[left],
                component_panels[right],
                minimum_assets=MIN_ASSETS_PER_DATE,
            )
            pair_daily[frozenset((left, right))] = daily
            pairwise.append(
                {
                    "left": left,
                    "right": right,
                    "splits": {
                        split: _style_summary(
                            _masked(
                                daily,
                                split_masks[PRIMARY_HORIZON][split],
                            )
                        )
                        for split in ("train", "validation", "test")
                    },
                }
            )

    nearest_peers: dict[str, str | None] = {}
    for name in names:
        candidates: list[tuple[str, float]] = []
        for pair, daily in pair_daily.items():
            if name not in pair:
                continue
            peer = next(item for item in pair if item != name)
            summary = _style_summary(
                _masked(
                    daily,
                    split_masks[PRIMARY_HORIZON]["train"],
                )
            )
            absolute = summary["mean_absolute_rank_correlation"]
            if absolute is not None:
                candidates.append((peer, float(absolute)))
        nearest_peers[name] = (
            min(candidates, key=lambda item: (-item[1], item[0]))[0]
            if candidates
            else None
        )

    residual_quality: dict[str, Any] = {}
    for name in names:
        peer = nearest_peers[name]
        if peer is None:
            residual_quality[name] = {
                "peer": None,
                "selection": (
                    "unavailable-single-component"
                    if len(names) == 1
                    else "unavailable-no-finite-train-peer"
                ),
                "horizon_quality": None,
            }
            continue
        residual = cross_sectional_rank_residual(
            component_panels[name],
            component_panels[peer],
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        residual_daily = {
            horizon: daily_rank_correlation(
                residual,
                forward_panels[horizon],
                minimum_assets=MIN_ASSETS_PER_DATE,
                constant_left_value=0.0,
            )
            for horizon in HORIZONS
        }
        residual_quality[name] = {
            "peer": peer,
            "selection": (
                "maximum-absolute-mean-train-daily-rank-association"
            ),
            "horizon_quality": {
                str(horizon): {
                    split: _component_split_metrics(
                        _masked(
                            residual_daily[horizon],
                            split_masks[horizon][split],
                        )
                    )
                    for split in ("train", "validation", "test")
                }
                for horizon in HORIZONS
            },
        }

    first = component_panels[names[0]]
    common_available = pd.DataFrame(
        True,
        index=first.index,
        columns=first.columns,
    )
    for panel in component_panels.values():
        common_available &= panel.notna()
    full_blend = _equal_rank_component_blend(
        component_panels,
        common_available=common_available,
    )
    full_blend_daily = {
        horizon: daily_rank_correlation(
            full_blend,
            forward_panels[horizon],
            minimum_assets=MIN_ASSETS_PER_DATE,
        )
        for horizon in HORIZONS
    }
    full_blend_quality = {
        str(horizon): {
            split: _component_split_metrics(
                _masked(
                    full_blend_daily[horizon],
                    split_masks[horizon][split],
                )
            )
            for split in ("train", "validation", "test")
        }
        for horizon in HORIZONS
    }
    ablations: dict[str, Any] = {}
    for name in names:
        remaining = {
            candidate: panel
            for candidate, panel in component_panels.items()
            if candidate != name
        }
        if not remaining:
            ablations[name] = {
                "available": False,
                "reason": "single-component",
                "horizon_quality": None,
                "removal_delta_mean_ic": None,
            }
            continue
        leave_one_out = _equal_rank_component_blend(
            remaining,
            common_available=common_available,
        )
        leave_daily = {
            horizon: daily_rank_correlation(
                leave_one_out,
                forward_panels[horizon],
                minimum_assets=MIN_ASSETS_PER_DATE,
            )
            for horizon in HORIZONS
        }
        quality = {
            str(horizon): {
                split: _component_split_metrics(
                    _masked(
                        leave_daily[horizon],
                        split_masks[horizon][split],
                    )
                )
                for split in ("train", "validation", "test")
            }
            for horizon in HORIZONS
        }
        removal_delta: dict[str, float | None] = {}
        for split in ("train", "validation", "test"):
            primary = str(PRIMARY_HORIZON)
            leave_mean = quality[primary][split]["mean_ic"]
            full_mean = full_blend_quality[primary][split]["mean_ic"]
            removal_delta[split] = (
                float(leave_mean) - float(full_mean)
                if leave_mean is not None and full_mean is not None
                else None
            )
        ablations[name] = {
            "available": True,
            "reason": None,
            "horizon_quality": quality,
            "removal_delta_mean_ic": removal_delta,
        }

    component_rows: list[dict[str, Any]] = []
    metadata_by_name = {item["id"]: item for item in declarations}
    for name in names:
        primary = str(PRIMARY_HORIZON)
        raw_validation = raw_quality[name][primary]["validation"]["mean_ic"]
        residual = residual_quality[name]
        residual_validation = (
            residual["horizon_quality"][primary]["validation"]["mean_ic"]
            if residual["horizon_quality"] is not None
            else None
        )
        removal_delta = (
            ablations[name]["removal_delta_mean_ic"]["validation"]
            if ablations[name]["available"]
            else None
        )
        peer = nearest_peers[name]
        train_redundancy = None
        if peer is not None:
            train_redundancy = _style_summary(
                _masked(
                    pair_daily[frozenset((name, peer))],
                    split_masks[PRIMARY_HORIZON]["train"],
                )
            )["mean_absolute_rank_correlation"]
        component_rows.append(
            {
                **metadata_by_name[name],
                "coverage_by_asset": coverage[name],
                "mean_coverage": float(
                    sum(coverage[name].values()) / len(coverage[name])
                ),
                "raw_horizon_quality": raw_quality[name],
                "composite_association": composite_association[name],
                "nearest_peer": {
                    "id": peer,
                    "train_mean_absolute_rank_association": train_redundancy,
                },
                "nearest_peer_residual": residual,
                "fixed_blend_ablation": ablations[name],
                "validation_priority_inputs": {
                    "raw_mean_ic": raw_validation,
                    "nearest_peer_residual_mean_ic": residual_validation,
                    "removal_delta_mean_ic": removal_delta,
                },
            }
        )

    raw_candidates = [
        row
        for row in component_rows
        if row["validation_priority_inputs"]["raw_mean_ic"] is not None
    ]
    strongest_raw = (
        max(
            raw_candidates,
            key=lambda row: (
                float(row["validation_priority_inputs"]["raw_mean_ic"]),
                row["id"],
            ),
        )
        if raw_candidates
        else None
    )
    residual_candidates = [
        row
        for row in component_rows
        if row["validation_priority_inputs"][
            "nearest_peer_residual_mean_ic"
        ] is not None
    ]
    strongest_residual = (
        max(
            residual_candidates,
            key=lambda row: (
                float(
                    row["validation_priority_inputs"][
                        "nearest_peer_residual_mean_ic"
                    ]
                ),
                row["id"],
            ),
        )
        if residual_candidates
        else None
    )
    removable = [
        row
        for row in component_rows
        if row["validation_priority_inputs"]["removal_delta_mean_ic"]
        is not None
    ]
    best_removal = (
        max(
            removable,
            key=lambda row: (
                float(
                    row["validation_priority_inputs"][
                        "removal_delta_mean_ic"
                    ]
                ),
                row["id"],
            ),
        )
        if removable
        else None
    )
    finite_pairs = [
        row
        for row in pairwise
        if row["splits"]["train"]["mean_absolute_rank_correlation"]
        is not None
    ]
    most_redundant = (
        max(
            finite_pairs,
            key=lambda row: (
                float(
                    row["splits"]["train"][
                        "mean_absolute_rank_correlation"
                    ]
                    or -1.0
                ),
                row["left"],
                row["right"],
            ),
        )
        if finite_pairs
        else None
    )
    return {
        "method": "candidate-declared-components-v1",
        "declaration": {
            "exhaustive_composition_claim": False,
            "source_inference": False,
            "components": declarations,
        },
        "semantics": {
            "prediction_target": "fixed-purged-forward-base-bar-return",
            "nearest_peer_selection": "train-only-target-free",
            "residualization": (
                "same-timestamp-cross-sectional-centered-rank-ols"
            ),
            "diagnostic_blend": (
                "equal-weight-cross-sectional-percentile-ranks-with-"
                "common-component-availability"
            ),
            "ablation_target": "fixed-diagnostic-blend-not-candidate-factor",
            "selection_authority": "research-prioritization-only",
            "test_role": "visible-audit",
            "promotion_authority": "none",
            "portfolio_authority": "none",
            "rl_action_authority": "none",
            "trading_authority": "none",
        },
        "trial_disclosure": {
            "materialized_components": len(names),
            "pairwise_comparisons": len(pairwise),
            "component_diagnostics_enter_promotion_score": False,
        },
        "components": component_rows,
        "pairwise": pairwise,
        "fixed_blend": {
            "horizon_quality": full_blend_quality,
        },
        "validation_diagnosis": {
            "strongest_raw_component": (
                strongest_raw["id"] if strongest_raw is not None else None
            ),
            "strongest_raw_mean_ic": (
                strongest_raw["validation_priority_inputs"]["raw_mean_ic"]
                if strongest_raw is not None
                else None
            ),
            "strongest_residual_component": (
                strongest_residual["id"]
                if strongest_residual is not None
                else None
            ),
            "strongest_residual_mean_ic": (
                strongest_residual["validation_priority_inputs"][
                    "nearest_peer_residual_mean_ic"
                ]
                if strongest_residual is not None
                else None
            ),
            "removal_most_improves_fixed_blend": (
                best_removal["id"] if best_removal is not None else None
            ),
            "best_removal_delta_mean_ic": (
                best_removal["validation_priority_inputs"][
                    "removal_delta_mean_ic"
                ]
                if best_removal is not None
                else None
            ),
            "most_redundant_pair": (
                {
                    "left": most_redundant["left"],
                    "right": most_redundant["right"],
                    "train_mean_absolute_rank_association": (
                        most_redundant["splits"]["train"][
                            "mean_absolute_rank_correlation"
                        ]
                    ),
                }
                if most_redundant is not None
                else None
            ),
            "authority": "research-prioritization-only",
            "test_enters_diagnosis": False,
        },
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
        primary = means[str(PRIMARY_HORIZON)]
        ratios: dict[str, float | None] = {}
        for horizon in (str(item) for item in HORIZONS):
            if horizon == str(PRIMARY_HORIZON):
                continue
            value = means[horizon]
            ratios[
                f"horizon_{horizon}_to_{PRIMARY_HORIZON}"
            ] = (
                float(value) / float(primary)
                if value is not None
                and primary is not None
                and abs(float(primary)) > 1e-12
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
            _masked(
                daily["style_neutral_candidate"][PRIMARY_HORIZON],
                mask,
            )
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
    dict[str, Any] | None,
]:
    global HORIZONS, PRIMARY_HORIZON
    study, data_root = _load_contract()
    research_horizon = _load_horizon()
    HORIZONS = tuple(research_horizon["diagnosticForwardBars"])
    PRIMARY_HORIZON = int(research_horizon["primaryForwardBars"])
    dataset = study["dataset"]
    universe = dataset["universe"]
    time_range = dataset["time_range"]
    module = importlib.import_module("factors.candidate")
    frames: dict[str, pd.DataFrame] = {}
    close_by_asset: dict[str, pd.Series] = {}
    volume_by_asset: dict[str, pd.Series] = {}
    for asset in universe:
        frame = _load_asset(
            data_root,
            asset,
            time_range["start"],
            time_range["end"],
        )
        frames[asset] = frame
        timestamp = pd.DatetimeIndex(frame["timestamp"])
        close = frame["close"].copy()
        close.index = timestamp
        volume = frame["volume"].copy()
        volume.index = timestamp
        close_by_asset[asset] = close
        volume_by_asset[asset] = volume

    try:
        panel = build_factor_panel(frames, universe=universe)
        factor_evaluation = evaluate_factor(module, panel)
        factor_panel = values_to_wide(
            panel,
            factor_evaluation.values,
            universe=universe,
        )
    except FactorRuntimeError as error:
        raise JudgeFailure(error.code, str(error)) from error
    coverage = {
        asset: float(
            factor_evaluation.values.loc[panel["asset"] == asset].notna().mean()
        )
        for asset in universe
    }
    close_panel = pd.DataFrame(close_by_asset).reindex(factor_panel.index)
    volume_panel = pd.DataFrame(volume_by_asset).reindex(factor_panel.index)
    timeline = pd.DatetimeIndex(factor_panel.index)
    split_masks, split_protocol, base_split_labels = purged_split_masks(
        timeline,
        HORIZONS,
    )
    fold_masks, fold_protocol = chronological_fold_masks(
        timeline,
        PRIMARY_HORIZON,
    )
    forward_panels = forward_return_panels(close_panel, HORIZONS)
    components = factor_evaluation.components
    component_declarations = (
        components.declaration() if components is not None else None
    )
    component_panels = (
        {
            name: values_to_wide(
                panel,
                components.values[name],
                universe=universe,
            )
            for name in components.values.columns
        }
        if components is not None
        else {}
    )
    component_coverage = (
        {
            name: {
                asset: float(
                    components.values.loc[
                        panel["asset"] == asset,
                        name,
                    ].notna().mean()
                )
                for asset in universe
            }
            for name in components.values.columns
        }
        if components is not None
        else {}
    )
    component_evidence = (
        _component_evidence(
            component_declarations,
            component_panels,
            factor_panel,
            forward_panels,
            split_masks,
            component_coverage,
        )
        if component_declarations is not None
        else None
    )
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
    splits = horizon_metrics[str(PRIMARY_HORIZON)]
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

    primary_ic = daily_ic_by_horizon[PRIMARY_HORIZON]
    chronological_folds = {
        name: descriptive_ic(_masked(primary_ic, mask))
        for name, mask in fold_masks.items()
    }
    regimes = causal_regime_labels(close_panel)
    regime_stability = {
        split: {
            regime: descriptive_ic(
                _masked(
                    primary_ic,
                    split_masks[PRIMARY_HORIZON][split]
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
                _masked(
                    daily_style,
                    split_masks[PRIMARY_HORIZON][split],
                )
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
            forward_panels[PRIMARY_HORIZON],
            split_masks[PRIMARY_HORIZON][split],
        )
        for split in ("train", "validation", "test")
    }

    ranked = factor_panel.rank(axis=1, pct=True)
    turnover = float(ranked.diff().abs().mean(axis=1).dropna().mean())
    metrics = {
        "validation_mean_ic": validation_mean_ic,
        "factor_api": factor_contract(factor_evaluation),
        "research_horizon": research_horizon,
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
        "ic_dates": int(len(primary_ic)),
        "research_integrity": {
            "selection_split": "validation",
            "test_role": "visible-diagnostic",
            "test_enters_selection": False,
            "external_holdout_rule": (
                "required-after-test-guided-iteration"
            ),
        },
    }
    if component_evidence is not None:
        metrics["factor_components"] = component_evidence
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
        "researchHorizon": research_horizon,
        "semantics": {
            "target": research_horizon["targetSemantics"],
            "measure": (
                "per-date cross-sectional Spearman rank IC and Pearson IC"
            ),
            "horizons": list(HORIZONS),
            "primaryHorizon": PRIMARY_HORIZON,
            "split": (
                "dataset-fixed chronological 60/20/20 with horizon-specific "
                "boundary purge"
            ),
            "score": (
                "validation mean rank IC at the fixed primary "
                f"{PRIMARY_HORIZON}-bar horizon only"
            ),
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
            "components": (
                {
                    "method": component_evidence["method"],
                    "declaration": "candidate-explicit-not-source-inferred",
                    "exhaustiveCompositionClaim": False,
                    "nearestPeerSelection": "train-only-target-free",
                    "ablationTarget": (
                        "fixed-diagnostic-blend-not-candidate-factor"
                    ),
                    "testRole": "visible audit only",
                    "portfolioAuthority": "none",
                    "rlActionAuthority": "none",
                    "tradingAuthority": "none",
                }
                if component_evidence is not None
                else None
            ),
            "testRole": (
                "visible diagnostic evidence; never enters candidate selection"
            ),
        },
        "causalityAuditCuts": list(factor_evaluation.causality_cuts),
        "componentCausalityAuditCuts": (
            list(factor_evaluation.causality_cuts)
            if components is not None
            else []
        ),
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
        (
            {
                "schemaVersion": 1,
                "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
                "evidence": component_evidence,
            }
            if component_evidence is not None
            else None
        ),
    )


def main() -> None:
    try:
        (
            metrics,
            report,
            daily_evidence,
            quantile_evidence,
            qualification_evidence,
            component_evidence,
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
        if component_evidence is not None:
            (artifacts / "factor-components.json").write_text(
                json.dumps(component_evidence, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        output_artifacts = [
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
                    "request-bound forward-bar rank and Pearson IC"
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
            },
        ]
        if component_evidence is not None:
            output_artifacts.append(
                {
                    "kind": "factor-components",
                    "path": "factor-components.json",
                    "description": (
                        "Candidate-declared component quality, redundancy, "
                        "nearest-peer residual, and fixed-blend ablation evidence"
                    ),
                }
            )
        _write_output(
            {
                "schema_version": 1,
                "status": "succeeded",
                "summary": (
                    "Causal purge-aware factor tear sheet completed; "
                    f"validation {PRIMARY_HORIZON}-bar mean rank IC="
                    f"{metrics['validation_mean_ic']:.6f}"
                ),
                "metrics": metrics,
                "artifacts": output_artifacts,
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
