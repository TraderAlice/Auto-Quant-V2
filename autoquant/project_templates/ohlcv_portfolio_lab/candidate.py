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
    frame: pd.DataFrame,
    interval: str,
    periods: int,
) -> pd.Series:
    close_column = f"close__{interval}"
    bar_column = f"bar_close__{interval}"
    if close_column not in frame or bar_column not in frame:
        return pd.Series(float("nan"), index=frame.index, dtype=float)
    completed = (
        frame.loc[frame[bar_column].notna(), [bar_column, close_column]]
        .drop_duplicates(bar_column, keep="first")
        .set_index(bar_column)[close_column]
    )
    values = completed.pct_change(periods)
    return frame[bar_column].map(values).astype(float)


def compute_factor_components(frame: pd.DataFrame) -> pd.DataFrame:
    """Declare causal components without changing downstream factor authority."""

    components = {
        "base_momentum_10": frame["close"].pct_change(10),
    }
    for name, interval, periods in (
        ("momentum_3h_4", "3h", 4),
        ("momentum_12h_2", "12h", 2),
        ("momentum_1d_3", "1d", 3),
    ):
        if f"close__{interval}" in frame:
            components[name] = _completed_bar_return(
                frame,
                interval,
                periods,
            )
    return pd.DataFrame(components, index=frame.index)


def compute_factor(frame: pd.DataFrame) -> pd.Series:
    """Return causal multi-horizon momentum for mechanical construction.

    The fixed Judge owns signal state/hysteresis, conviction/volatility sizing,
    target and executed weights, attribution, delay, drift, costs, benchmark,
    splits, metrics, and stress tests. Change only this factor while testing
    one falsifiable hypothesis at a time.
    """

    components = compute_factor_components(frame)
    return components.mean(axis=1, skipna=True)
