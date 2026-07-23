"""Agent-editable baseline factor for the OHLCV Factor Lab."""

from __future__ import annotations

import pandas as pd


def compute_factor(frame: pd.DataFrame) -> pd.Series:
    """Return a simple causal price-momentum baseline.

    The fixed Judge owns targets, chronological splits, and evaluation. Change
    only this function while testing one falsifiable factor hypothesis at a
    time.
    """

    return frame["close"].pct_change(10)
