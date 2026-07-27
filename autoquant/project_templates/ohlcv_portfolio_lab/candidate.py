"""Agent-editable baseline factor for the OHLCV Portfolio Lab."""

from __future__ import annotations

import pandas as pd


FACTOR_COMPONENTS = {
    "base_momentum_10": {
        "label": "10-base-bar momentum",
        "intervals": ["base"],
        "hypothesis": (
            "Recent relative strength persists over the next base bar."
        ),
    },
    "momentum_3h_4": {
        "label": "Four completed 3-hour bars momentum",
        "intervals": ["3h"],
        "hypothesis": (
            "Short intraday trend persists beyond the latest completed "
            "3-hour bar."
        ),
    },
    "momentum_12h_2": {
        "label": "Two completed 12-hour bars momentum",
        "intervals": ["12h"],
        "hypothesis": (
            "Half-day trend filters noisy base-bar momentum."
        ),
    },
    "momentum_1d_3": {
        "label": "Three completed daily bars momentum",
        "intervals": ["1d"],
        "hypothesis": (
            "Multi-day relative strength persists at the next base close."
        ),
    },
}


def _completed_bar_return(
    panel: pd.DataFrame,
    interval: str,
    periods: int,
) -> pd.Series:
    close_column = f"close__{interval}"
    bar_column = f"bar_close__{interval}"
    if close_column not in panel or bar_column not in panel:
        return pd.Series(float("nan"), index=panel.index, dtype=float)
    completed = panel.loc[
        panel[bar_column].notna(),
        ["asset", bar_column, close_column],
    ].drop_duplicates(["asset", bar_column], keep="first")
    completed["return"] = completed.groupby(
        "asset",
        sort=False,
    )[close_column].pct_change(periods, fill_method=None)
    lookup = completed.set_index(
        ["asset", bar_column],
    )["return"]
    keys = pd.MultiIndex.from_frame(
        panel.loc[:, ["asset", bar_column]],
    )
    return pd.Series(
        lookup.reindex(keys).to_numpy(dtype=float),
        index=panel.index,
        dtype=float,
    )


def compute_factor_components(panel: pd.DataFrame) -> pd.DataFrame:
    """Declare causal components without changing downstream factor authority."""

    components = {
        "base_momentum_10": panel.groupby(
            "asset",
            sort=False,
        )["close"].pct_change(10, fill_method=None),
    }
    for name, interval, periods in (
        ("momentum_3h_4", "3h", 4),
        ("momentum_12h_2", "12h", 2),
        ("momentum_1d_3", "1d", 3),
    ):
        if f"close__{interval}" in panel:
            components[name] = _completed_bar_return(
                panel,
                interval,
                periods,
            )
    return pd.DataFrame(components, index=panel.index)


def compute_factor(panel: pd.DataFrame) -> pd.Series:
    """Return causal relative multi-horizon momentum for construction.

    The fixed Judge owns signal state/hysteresis, conviction/volatility sizing,
    target and executed weights, attribution, delay, drift, costs, benchmark,
    splits, metrics, and stress tests. Change only this factor while testing
    one falsifiable hypothesis at a time.
    """

    components = compute_factor_components(panel)
    raw = components.mean(axis=1, skipna=True)
    market_center = raw.groupby(panel["timestamp"], sort=False).transform("mean")
    return (raw - market_center).rename("relative_multi_horizon_momentum")
