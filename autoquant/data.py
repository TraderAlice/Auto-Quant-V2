"""Project-local OHLCV storage and ingestion helpers."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .profiles import AssetProfile


OHLCV_COLUMNS = ("date", "open", "high", "low", "close", "volume")
SUPPORTED_SOURCE_SUFFIXES = (".feather", ".parquet", ".csv")


class DataValidationError(ValueError):
    """Raised when imported OHLCV violates the Harness data contract."""


@dataclass(frozen=True)
class DataCoverage:
    pair: str
    timeframe: str
    path: Path
    rows: int
    start: pd.Timestamp
    end: pd.Timestamp


def pair_stem(pair: str) -> str:
    return pair.replace("/", "_").replace(":", "_")


def candle_filename(pair: str, timeframe: str, data_format: str = "feather") -> str:
    return f"{pair_stem(pair)}-{timeframe}.{data_format}"


def expected_candle_paths(project_dir: Path, profile: AssetProfile) -> list[Path]:
    data_dir = profile.data_dir(project_dir)
    return [
        data_dir / candle_filename(pair, timeframe, profile.data_format)
        for pair in profile.pairs
        for timeframe in profile.timeframes
    ]


def _read_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".feather":
        return pd.read_feather(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise DataValidationError(f"unsupported OHLCV source format: {path}")


def normalize_ohlcv(frame: pd.DataFrame, *, source: str = "<dataframe>") -> pd.DataFrame:
    """Normalize a conventional OHLCV table to Freqtrade's disk schema."""

    frame = frame.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    if "date" not in frame.columns:
        for alias in ("datetime", "timestamp", "time"):
            if alias in frame.columns:
                frame.rename(columns={alias: "date"}, inplace=True)
                break

    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise DataValidationError(f"{source}: missing OHLCV columns {missing}")

    raw_date = frame["date"]
    if pd.api.types.is_numeric_dtype(raw_date):
        non_null = raw_date.dropna()
        sample = float(non_null.iloc[0]) if not non_null.empty else 0.0
        unit = "ms" if abs(sample) >= 100_000_000_000 else "s"
        frame["date"] = pd.to_datetime(raw_date, unit=unit, utc=True, errors="coerce")
    else:
        frame["date"] = pd.to_datetime(raw_date, utc=True, errors="coerce")

    for column in OHLCV_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.loc[:, list(OHLCV_COLUMNS)].sort_values("date").reset_index(drop=True)
    if frame.empty:
        raise DataValidationError(f"{source}: OHLCV table is empty")
    if frame.isna().any().any():
        bad = [column for column in OHLCV_COLUMNS if frame[column].isna().any()]
        raise DataValidationError(f"{source}: null or unparsable values in {bad}")
    if frame["date"].duplicated().any():
        raise DataValidationError(f"{source}: duplicate candle timestamps")
    if (frame["volume"] < 0).any():
        raise DataValidationError(f"{source}: volume must be non-negative")

    invalid_high = frame["high"] < frame[["open", "low", "close"]].max(axis=1)
    invalid_low = frame["low"] > frame[["open", "high", "close"]].min(axis=1)
    if invalid_high.any() or invalid_low.any():
        raise DataValidationError(f"{source}: OHLC price bounds are inconsistent")
    return frame


def validate_candle_file(
    path: Path,
    pair: str,
    timeframe: str,
    *,
    session_based: bool,
) -> DataCoverage:
    frame = normalize_ohlcv(_read_frame(path), source=str(path))
    if session_based and (frame["date"].dt.weekday >= 5).any():
        raise DataValidationError(
            f"{path}: session-based data contains weekend candles; "
            "market-closure gaps must remain absent"
        )
    return DataCoverage(
        pair=pair,
        timeframe=timeframe,
        path=path,
        rows=len(frame),
        start=pd.Timestamp(frame["date"].iloc[0]),
        end=pd.Timestamp(frame["date"].iloc[-1]),
    )


def inspect_profile_data(project_dir: Path, profile: AssetProfile) -> list[DataCoverage]:
    """Validate all expected files and return their coverage."""

    coverages: list[DataCoverage] = []
    data_dir = profile.data_dir(project_dir)
    for pair in profile.pairs:
        for timeframe in profile.timeframes:
            path = data_dir / candle_filename(pair, timeframe, profile.data_format)
            if not path.exists():
                raise DataValidationError(f"missing candle file: {path}")
            coverages.append(
                validate_candle_file(
                    path,
                    pair,
                    timeframe,
                    session_based=profile.is_session_based,
                )
            )
    return coverages


def import_profile_data(
    source_dir: Path,
    project_dir: Path,
    profile: AssetProfile,
) -> list[DataCoverage]:
    """Import matching CSV/Parquet/Feather files into the profile data directory."""

    source_dir = source_dir.resolve()
    destination = profile.data_dir(project_dir)
    destination.mkdir(parents=True, exist_ok=True)

    for pair in profile.pairs:
        for timeframe in profile.timeframes:
            stem = f"{pair_stem(pair)}-{timeframe}"
            candidates = [
                source_dir / f"{stem}{suffix}" for suffix in SUPPORTED_SOURCE_SUFFIXES
            ]
            source = next((path for path in candidates if path.exists()), None)
            if source is None:
                names = ", ".join(path.name for path in candidates)
                raise DataValidationError(
                    f"no source file for {pair} {timeframe}; expected one of: {names}"
                )

            frame = normalize_ohlcv(_read_frame(source), source=str(source))
            target = destination / candle_filename(pair, timeframe, profile.data_format)
            if profile.data_format == "feather":
                frame.to_feather(target)
            elif profile.data_format == "parquet":
                frame.to_parquet(target, index=False)
            else:
                frame.to_csv(target, index=False)

    return inspect_profile_data(project_dir, profile)


def migrate_legacy_crypto_data(
    project_dir: Path,
    profile: AssetProfile,
    *,
    move: bool = True,
) -> int:
    """Move/copy the old ``user_data/data`` layout into a profile directory."""

    legacy = project_dir / "user_data" / "data"
    destination = profile.data_dir(project_dir)
    if not legacy.exists() or legacy.resolve() == destination.resolve():
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    migrated = 0
    for source in legacy.iterdir():
        if not source.is_file():
            continue
        target = destination / source.name
        if target.exists():
            continue
        if move:
            shutil.move(str(source), str(target))
        else:
            shutil.copy2(source, target)
        migrated += 1

    if move:
        try:
            legacy.rmdir()
        except OSError:
            pass
    return migrated
