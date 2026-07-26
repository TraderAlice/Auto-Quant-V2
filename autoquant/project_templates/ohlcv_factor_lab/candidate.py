"""Agent-editable baseline factor for the OHLCV Factor Lab."""

from __future__ import annotations

import pandas as pd


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


def compute_factor(frame: pd.DataFrame) -> pd.Series:
    """Return causal multi-horizon momentum when completed bars are available.

    The fixed Judge owns targets, chronological splits, and evaluation. Change
    only this function while testing one falsifiable factor hypothesis at a
    time.
    """

    base = frame["close"].pct_change(10)
    if "close__1d" not in frame:
        return base
    components = pd.concat(
        [
            base.rename("base_10"),
            _completed_bar_return(frame, "3h", 4).rename("three_hour_4"),
            _completed_bar_return(frame, "12h", 2).rename("twelve_hour_2"),
            _completed_bar_return(frame, "1d", 3).rename("daily_3"),
        ],
        axis=1,
    )
    return components.mean(axis=1, skipna=True)
