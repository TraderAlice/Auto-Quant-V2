from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from autoquant.freqtrade_adapter import (
    gap_aware_stop_price,
    preserve_session_gaps,
    retain_session_warmup,
    session_startup_candles,
)
from freqtrade.data import history
from freqtrade.enums import CandleType


class SessionAdapterTests(unittest.TestCase):
    def test_session_warmup_expands_intraday_and_daily_history(self) -> None:
        self.assertEqual(session_startup_candles("1h", 250), 1_500)
        self.assertEqual(session_startup_candles("1d", 250), 500)

    def test_session_warmup_lands_on_requested_start_after_row_trim(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.bdate_range("2025-01-01", periods=20, tz="UTC"),
                "close": range(20),
            }
        )
        start = frame["date"].iloc[12]

        retained = retain_session_warmup(frame, start=start, requested=5)

        self.assertEqual(len(retained.loc[retained["date"] < start]), 5)
        self.assertEqual(retained.iloc[5]["date"], start)

    def test_stop_crossed_at_open_fills_at_open(self) -> None:
        self.assertEqual(
            gap_aware_stop_price(open_price=90.0, stop_price=100.0, is_short=False),
            90.0,
        )
        self.assertEqual(
            gap_aware_stop_price(open_price=110.0, stop_price=100.0, is_short=True),
            110.0,
        )
        self.assertIsNone(
            gap_aware_stop_price(open_price=101.0, stop_price=100.0, is_short=False)
        )

    def test_session_policy_preserves_weekend_gap(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2026-01-02T00:00:00Z", "2026-01-05T00:00:00Z"],
                    utc=True,
                ),
                "open": [100.0, 90.0],
                "high": [101.0, 95.0],
                "low": [99.0, 85.0],
                "close": [100.0, 92.0],
                "volume": [1_000.0, 1_500.0],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            frame.to_feather(data_dir / "AAPL_USD-1d.feather")

            default = history.load_data(
                datadir=data_dir,
                timeframe="1d",
                pairs=["AAPL/USD"],
                data_format="feather",
                candle_type=CandleType.SPOT,
            )
            with preserve_session_gaps():
                session = history.load_data(
                    datadir=data_dir,
                    timeframe="1d",
                    pairs=["AAPL/USD"],
                    data_format="feather",
                    candle_type=CandleType.SPOT,
                )

        self.assertEqual(len(default["AAPL/USD"]), 4)
        self.assertEqual(len(session["AAPL/USD"]), 2)


if __name__ == "__main__":
    unittest.main()
