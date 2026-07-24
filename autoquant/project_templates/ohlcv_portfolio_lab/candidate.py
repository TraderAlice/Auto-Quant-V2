"""Agent-editable baseline factor for the OHLCV Portfolio Lab."""

from __future__ import annotations

import pandas as pd


def compute_factor(frame: pd.DataFrame) -> pd.Series:
    """Return a causal medium-horizon momentum signal.

    The fixed Judge owns signal state/hysteresis, conviction/volatility sizing,
    target and executed weights, attribution, delay, drift, costs, benchmark,
    splits, metrics, and stress tests. Change only this factor while testing
    one falsifiable hypothesis at a time.
    """

    return frame["close"].pct_change(10)
