from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from autoquant.data import (
    DataValidationError,
    import_profile_data,
    normalize_ohlcv,
)
from autoquant.profiles import load_manifest


PROJECT_DIR = Path(__file__).resolve().parents[1]


def candles(dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": [100.0 + index for index in range(len(dates))],
            "high": [101.0 + index for index in range(len(dates))],
            "low": [99.0 + index for index in range(len(dates))],
            "close": [100.5 + index for index in range(len(dates))],
            "volume": [1_000 + index for index in range(len(dates))],
            "ignored_vendor_column": ["x"] * len(dates),
        }
    )


class DataContractTests(unittest.TestCase):
    def test_normalize_accepts_conventional_timestamp_alias(self) -> None:
        frame = normalize_ohlcv(candles(["2026-01-02T15:30:00Z"]))

        self.assertEqual(
            list(frame.columns),
            ["date", "open", "high", "low", "close", "volume"],
        )
        self.assertEqual(str(frame["date"].dt.tz), "UTC")

    def test_import_rejects_weekend_candles_for_session_profile(self) -> None:
        profile = load_manifest(PROJECT_DIR / "harness.json").profile("us-equities")
        weekend_frame = candles(
            ["2026-01-02T20:00:00Z", "2026-01-03T20:00:00Z"]
        )

        with (
            tempfile.TemporaryDirectory() as source_directory,
            tempfile.TemporaryDirectory() as project_directory,
        ):
            source = Path(source_directory)
            for pair in profile.pairs:
                for timeframe in profile.timeframes:
                    weekend_frame.to_csv(
                        source / f"{pair.replace('/', '_')}-{timeframe}.csv",
                        index=False,
                    )

            with self.assertRaisesRegex(DataValidationError, "weekend candles"):
                import_profile_data(source, Path(project_directory), profile)


if __name__ == "__main__":
    unittest.main()
