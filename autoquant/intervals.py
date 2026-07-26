"""Causal completed-bar aggregation and multi-interval pandas alignment."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


OHLCV_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
BASE_INTERVAL = "1h"
FEATURE_INTERVAL_HOURS = {
    "3h": 3,
    "4h": 4,
    "6h": 6,
    "12h": 12,
    "1d": 24,
}
SUPPORTED_FEATURE_INTERVALS = tuple(FEATURE_INTERVAL_HOURS)
AGGREGATION_METHOD = "complete-utc-midnight-bar-close-v1"
INTERVAL_ID = re.compile(r"^(?:[1-9][0-9]*h|1d)$")


class IntervalContractError(ValueError):
    """Raised when a multi-interval input violates fixed time authority."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class IntervalSurface:
    base_interval: str
    feature_intervals: tuple[str, ...]
    timestamp_semantics: str = "bar-close"
    market_clock: str = "continuous"
    timezone: str = "UTC"
    anchor: str = "00:00"
    aggregation_method: str = AGGREGATION_METHOD

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseInterval": self.base_interval,
            "featureIntervals": list(self.feature_intervals),
            "timestampSemantics": self.timestamp_semantics,
            "marketClock": self.market_clock,
            "timezone": self.timezone,
            "anchor": self.anchor,
            "aggregationMethod": self.aggregation_method,
        }


def normalize_feature_intervals(values: Iterable[str]) -> tuple[str, ...]:
    """Return a unique canonical interval sequence in increasing duration."""

    raw = list(values)
    if (
        not all(isinstance(value, str) and INTERVAL_ID.fullmatch(value) for value in raw)
        or any(value not in FEATURE_INTERVAL_HOURS for value in raw)
    ):
        raise IntervalContractError(
            "interval.unsupported",
            "Feature intervals must be selected from: "
            + ", ".join(SUPPORTED_FEATURE_INTERVALS),
        )
    if len(raw) != len(set(raw)):
        raise IntervalContractError(
            "interval.duplicate",
            "Feature intervals must be unique",
        )
    return tuple(sorted(raw, key=FEATURE_INTERVAL_HOURS.__getitem__))


def interval_surface(feature_intervals: Iterable[str]) -> IntervalSurface:
    return IntervalSurface(
        base_interval=BASE_INTERVAL,
        feature_intervals=normalize_feature_intervals(feature_intervals),
    )


def timestamp_label(value: Any) -> str:
    """Preserve V1 session dates and identify V2 intraday UTC closes exactly."""

    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.date().isoformat()
    return timestamp.tz_convert("UTC").isoformat().replace("+00:00", "Z")


def annualization_periods(index: Iterable[Any]) -> int:
    """Return fixed period units for supported V1 daily or V2 hourly clocks."""

    timestamps = pd.DatetimeIndex(index)
    if len(timestamps) > 1 and timestamps.tz is not None:
        deltas = timestamps.to_series().diff().dropna()
        if deltas.eq(pd.Timedelta(hours=1)).all():
            return 24 * 365
    return 252


def validate_continuous_hourly_ohlcv(
    frame: pd.DataFrame,
    *,
    label: str = "base OHLCV",
) -> pd.DataFrame:
    """Normalize one strict UTC 1h bar-close frame without filling gaps."""

    if tuple(frame.columns) != OHLCV_COLUMNS:
        raise IntervalContractError(
            "interval.columns",
            f"{label} columns must be exactly {', '.join(OHLCV_COLUMNS)}",
        )
    result = frame.copy(deep=True)
    try:
        timestamps = pd.to_datetime(result["timestamp"], utc=True, errors="raise")
    except (TypeError, ValueError) as error:
        raise IntervalContractError(
            "interval.timestamp",
            f"{label} timestamps must be timezone-aware UTC bar closes: {error}",
        ) from error
    # pd.to_datetime(..., utc=True) would silently localize naive values. Reject
    # those before accepting the normalized UTC index.
    naive = pd.to_datetime(result["timestamp"], errors="raise")
    if getattr(naive.dt, "tz", None) is None:
        raise IntervalContractError(
            "interval.timezone",
            f"{label} timestamps must include an explicit UTC offset",
        )
    if not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
        raise IntervalContractError(
            "interval.order",
            f"{label} timestamps must be unique and chronological",
        )
    if len(timestamps) > 1:
        deltas = timestamps.diff().iloc[1:]
        if not deltas.eq(pd.Timedelta(hours=1)).all():
            raise IntervalContractError(
                "interval.gap",
                f"{label} must contain consecutive 1h bar closes without gaps",
            )
    if not timestamps.dt.minute.eq(0).all() or not timestamps.dt.second.eq(0).all():
        raise IntervalContractError(
            "interval.boundary",
            f"{label} bar closes must land on exact UTC hours",
        )
    numeric_columns = list(OHLCV_COLUMNS[1:])
    try:
        result[numeric_columns] = result[numeric_columns].apply(
            pd.to_numeric,
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise IntervalContractError(
            "interval.numeric",
            f"{label} OHLCV values must be numeric: {error}",
        ) from error
    numeric = result[numeric_columns].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise IntervalContractError(
            "interval.non-finite",
            f"{label} contains non-finite OHLCV",
        )
    if (numeric <= 0).any():
        raise IntervalContractError(
            "interval.non-positive",
            f"{label} OHLCV must be strictly positive",
        )
    if (
        (result["high"] < result[["open", "close"]].max(axis=1)).any()
        or (result["low"] > result[["open", "close"]].min(axis=1)).any()
        or (result["high"] < result["low"]).any()
    ):
        raise IntervalContractError(
            "interval.bar-shape",
            f"{label} contains invalid OHLCV bar geometry",
        )
    result["timestamp"] = timestamps
    return result.reset_index(drop=True)


def aggregate_completed_ohlcv(
    base_frame: pd.DataFrame,
    interval: str,
) -> pd.DataFrame:
    """Aggregate exact complete UTC-midnight buckets from strict 1h bars."""

    normalized_interval = normalize_feature_intervals([interval])[0]
    hours = FEATURE_INTERVAL_HOURS[normalized_interval]
    base = validate_continuous_hourly_ohlcv(base_frame)
    indexed = base.set_index("timestamp", drop=False)
    frequency = pd.Timedelta(hours=hours)
    rows: list[dict[str, Any]] = []
    for bucket_close, group in indexed.groupby(
        pd.Grouper(
            freq=frequency,
            origin="start_day",
            closed="right",
            label="right",
        ),
        sort=True,
    ):
        if len(group) != hours:
            continue
        expected = pd.date_range(
            end=bucket_close,
            periods=hours,
            freq="1h",
            tz="UTC",
        )
        if not pd.DatetimeIndex(group.index).equals(expected):
            continue
        rows.append(
            {
                "timestamp": bucket_close,
                "open": float(group["open"].iloc[0]),
                "high": float(group["high"].max()),
                "low": float(group["low"].min()),
                "close": float(group["close"].iloc[-1]),
                "volume": float(group["volume"].sum()),
            }
        )
    return pd.DataFrame(rows, columns=OHLCV_COLUMNS)


def align_completed_intervals(
    base_frame: pd.DataFrame,
    derived: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Backward-align only already closed higher-period bars to 1h rows."""

    intervals = normalize_feature_intervals(derived.keys())
    if set(intervals) != set(derived):
        raise IntervalContractError(
            "interval.inventory",
            "Derived interval inventory is inconsistent",
        )
    result = validate_continuous_hourly_ohlcv(base_frame)
    for interval in intervals:
        high = derived[interval].copy(deep=True)
        if tuple(high.columns) != OHLCV_COLUMNS:
            raise IntervalContractError(
                "interval.columns",
                f"{interval} columns must be exactly {', '.join(OHLCV_COLUMNS)}",
            )
        high["timestamp"] = pd.to_datetime(
            high["timestamp"],
            utc=True,
            errors="raise",
        )
        if high["timestamp"].duplicated().any() or not high[
            "timestamp"
        ].is_monotonic_increasing:
            raise IntervalContractError(
                "interval.order",
                f"{interval} bar closes must be unique and chronological",
            )
        suffix = f"__{interval}"
        renamed = high.rename(
            columns={
                "timestamp": f"bar_close{suffix}",
                **{
                    column: f"{column}{suffix}"
                    for column in OHLCV_COLUMNS[1:]
                },
            }
        )
        result = pd.merge_asof(
            result.sort_values("timestamp"),
            renamed.sort_values(f"bar_close{suffix}"),
            left_on="timestamp",
            right_on=f"bar_close{suffix}",
            direction="backward",
            allow_exact_matches=True,
        )
        visible = result[f"bar_close{suffix}"].dropna()
        decisions = result.loc[visible.index, "timestamp"]
        if (visible > decisions).any():
            raise IntervalContractError(
                "interval.lookahead",
                f"{interval} alignment exposed a bar before its close",
            )
        age = (
            result["timestamp"] - result[f"bar_close{suffix}"]
        ) / pd.Timedelta(hours=1)
        result[f"age_bars{suffix}"] = age.astype("Int64")
    return result.reset_index(drop=True)


def build_multi_interval_frame(
    base_frame: pd.DataFrame,
    feature_intervals: Iterable[str],
) -> pd.DataFrame:
    """Build the shared ordinary pandas surface from one locked 1h frame."""

    intervals = normalize_feature_intervals(feature_intervals)
    base = validate_continuous_hourly_ohlcv(base_frame)
    derived = {
        interval: aggregate_completed_ohlcv(base, interval)
        for interval in intervals
    }
    return align_completed_intervals(base, derived)


def load_multi_interval_asset(
    data_root: str | Path,
    asset: str,
    *,
    start: str,
    end: str,
) -> pd.DataFrame | None:
    """Load and verify one materialized V2 asset, or return None for V1 data."""

    root = Path(data_root).resolve()
    ohlcv = (root / "ohlcv").resolve()
    snapshot_path = ohlcv / "snapshot.json"
    if not snapshot_path.is_file():
        return None
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise IntervalContractError(
            "interval.snapshot",
            f"Invalid interval snapshot JSON: {error}",
        ) from error
    if snapshot.get("schemaVersion") != 2:
        return None
    surface = snapshot.get("intervalSurface")
    if not isinstance(surface, dict):
        raise IntervalContractError(
            "interval.snapshot",
            "V2 snapshot is missing intervalSurface",
        )
    try:
        expected_surface = interval_surface(
            surface.get("featureIntervals", [])
        ).to_dict()
    except IntervalContractError:
        raise
    if surface != expected_surface:
        raise IntervalContractError(
            "interval.snapshot",
            "V2 snapshot intervalSurface differs from fixed authority",
        )
    if not isinstance(asset, str) or not asset or "/" in asset or "\\" in asset:
        raise IntervalContractError("interval.asset", "Invalid confined asset id")
    intervals = [BASE_INTERVAL, *expected_surface["featureIntervals"]]
    frames: dict[str, pd.DataFrame] = {}
    for interval in intervals:
        source = (ohlcv / interval / f"{asset}.csv").resolve()
        if ohlcv not in source.parents or not source.is_file() or source.is_symlink():
            raise IntervalContractError(
                "interval.asset",
                f"Missing confined {interval} OHLCV for {asset}",
            )
        frame = pd.read_csv(source)
        if interval == BASE_INTERVAL:
            frames[interval] = validate_continuous_hourly_ohlcv(
                frame,
                label=f"{asset} {interval}",
            )
        else:
            if tuple(frame.columns) != OHLCV_COLUMNS:
                raise IntervalContractError(
                    "interval.columns",
                    f"{asset} {interval} columns must be exactly "
                    + ", ".join(OHLCV_COLUMNS),
                )
            frame["timestamp"] = pd.to_datetime(
                frame["timestamp"],
                utc=True,
                errors="raise",
            )
            for column in OHLCV_COLUMNS[1:]:
                frame[column] = pd.to_numeric(frame[column], errors="raise")
            frames[interval] = frame
    base = frames[BASE_INTERVAL]
    for interval in expected_surface["featureIntervals"]:
        expected = aggregate_completed_ohlcv(base, interval)
        actual = frames[interval]
        if not pd.DatetimeIndex(actual["timestamp"]).equals(
            pd.DatetimeIndex(expected["timestamp"])
        ):
            raise IntervalContractError(
                "interval.reconciliation",
                f"{asset} {interval} timestamps do not reconcile to 1h bars",
            )
        if actual.shape != expected.shape or not np.isclose(
            actual[list(OHLCV_COLUMNS[1:])].to_numpy(dtype=float),
            expected[list(OHLCV_COLUMNS[1:])].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-9,
        ).all():
            raise IntervalContractError(
                "interval.reconciliation",
                f"{asset} {interval} OHLCV does not reconcile to 1h bars",
            )
    aligned = align_completed_intervals(
        base,
        {
            interval: frames[interval]
            for interval in expected_surface["featureIntervals"]
        },
    )
    start_at = pd.Timestamp(start)
    end_at = pd.Timestamp(end)
    if start_at.tzinfo is None:
        start_at = start_at.tz_localize("UTC")
    else:
        start_at = start_at.tz_convert("UTC")
    if end_at.tzinfo is None:
        end_at = end_at.tz_localize("UTC")
    else:
        end_at = end_at.tz_convert("UTC")
    return aligned[
        (aligned["timestamp"] >= start_at)
        & (aligned["timestamp"] <= end_at)
    ].reset_index(drop=True)
