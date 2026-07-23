"""Asset-clock adjustments around Freqtrade's legacy report metrics."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from .data import candle_filename, normalize_ohlcv
from .profiles import AssetProfile


RISK_METRIC_KEYS = ("sharpe", "sortino", "calmar")


def session_risk_metric_scale(
    *,
    calendar_days: int,
    session_days: int,
    annualization_days: int,
) -> float:
    """Translate Freqtrade's 365-day denominator to a session-day clock."""

    if calendar_days <= 0 or session_days <= 0 or annualization_days <= 0:
        return 1.0
    return (
        calendar_days
        / session_days
        * math.sqrt(annualization_days / 365)
    )


def _read_daily_data(path: Path, data_format: str) -> pd.DataFrame:
    if data_format == "feather":
        return pd.read_feather(path)
    if data_format == "parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def normalize_session_risk_metrics(
    results: dict[str, Any],
    strategy_name: str,
    profile: AssetProfile,
    project_dir: Path,
) -> None:
    """Adjust in-place report ratios to the profile's observed session clock.

    Freqtrade computes trade-based Sharpe/Sortino/Calmar using elapsed calendar
    days and ``sqrt(365)``.  For a session market we retain its formula for
    backward comparability, but replace the time basis with actual observed
    trading days and the profile annualization constant.
    """

    if not profile.is_session_based:
        return
    strategy = results.get("strategy", {}).get(strategy_name, {})
    if not strategy:
        return

    start_ms = strategy.get("backtest_start_ts")
    end_ms = strategy.get("backtest_end_ts")
    calendar_days = int(strategy.get("backtest_days") or 0)
    if start_ms is None or end_ms is None or calendar_days <= 0:
        return

    first_pair = profile.pairs[0]
    path = profile.data_dir(project_dir) / candle_filename(
        first_pair,
        "1d",
        profile.data_format,
    )
    if not path.exists():
        return
    daily = normalize_ohlcv(_read_daily_data(path, profile.data_format), source=str(path))
    start = pd.Timestamp(int(start_ms), unit="ms", tz="UTC")
    end = pd.Timestamp(int(end_ms), unit="ms", tz="UTC")
    normalized_dates = daily["date"].dt.normalize()
    session_days = int(
        normalized_dates.loc[
            (normalized_dates >= start.normalize())
            & (normalized_dates <= end.normalize())
        ].nunique()
    )
    scale = session_risk_metric_scale(
        calendar_days=calendar_days,
        session_days=session_days,
        annualization_days=profile.annualization_days,
    )

    entries = [strategy, *(strategy.get("results_per_pair") or [])]
    for entry in entries:
        for key in RISK_METRIC_KEYS:
            value = entry.get(key)
            if value is None or value in (0, -100):
                continue
            entry[key] = float(value) * scale
