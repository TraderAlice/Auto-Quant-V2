from __future__ import annotations

import unittest

import pandas as pd

from autoquant.intervals import (
    AGGREGATION_METHOD,
    IntervalContractError,
    aggregate_completed_ohlcv,
    build_multi_interval_frame,
    interval_surface,
    normalize_feature_intervals,
)


def hourly_fixture(periods: int = 72) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-01T01:00:00Z",
        periods=periods,
        freq="1h",
    )
    sequence = pd.Series(range(periods), dtype=float)
    opens = 100.0 + sequence
    closes = opens + 0.5
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": opens,
            "high": closes + 1.0,
            "low": opens - 1.0,
            "close": closes,
            "volume": 1_000.0 + sequence,
        }
    )


class MultiIntervalCoreTests(unittest.TestCase):
    def test_interval_surface_is_canonical_and_strict(self) -> None:
        self.assertEqual(
            normalize_feature_intervals(["1d", "3h", "12h"]),
            ("3h", "12h", "1d"),
        )
        surface = interval_surface(["12h", "3h"]).to_dict()
        self.assertEqual(surface["baseInterval"], "1h")
        self.assertEqual(surface["featureIntervals"], ["3h", "12h"])
        self.assertEqual(surface["timestampSemantics"], "bar-close")
        self.assertEqual(surface["aggregationMethod"], AGGREGATION_METHOD)
        with self.assertRaisesRegex(IntervalContractError, "selected from"):
            normalize_feature_intervals(["2h"])
        with self.assertRaisesRegex(IntervalContractError, "unique"):
            normalize_feature_intervals(["3h", "3h"])

    def test_aggregation_reconciles_complete_utc_buckets(self) -> None:
        base = hourly_fixture()
        three_hour = aggregate_completed_ohlcv(base, "3h")
        first = three_hour.iloc[0]
        self.assertEqual(first["timestamp"], pd.Timestamp("2026-01-01T03:00:00Z"))
        self.assertEqual(first["open"], 100.0)
        self.assertEqual(first["high"], 103.5)
        self.assertEqual(first["low"], 99.0)
        self.assertEqual(first["close"], 102.5)
        self.assertEqual(first["volume"], 3_003.0)
        daily = aggregate_completed_ohlcv(base, "1d")
        self.assertEqual(len(daily), 3)
        self.assertEqual(
            daily.iloc[0]["timestamp"],
            pd.Timestamp("2026-01-02T00:00:00Z"),
        )
        self.assertEqual(daily.iloc[0]["volume"], sum(1_000.0 + i for i in range(24)))

    def test_forming_bars_are_invisible_and_completed_bars_carry_backward(self) -> None:
        joined = build_multi_interval_frame(hourly_fixture(30), ["3h", "1d"])
        at_two = joined.loc[
            joined["timestamp"] == pd.Timestamp("2026-01-01T02:00:00Z")
        ].iloc[0]
        self.assertTrue(pd.isna(at_two["bar_close__3h"]))
        at_three = joined.loc[
            joined["timestamp"] == pd.Timestamp("2026-01-01T03:00:00Z")
        ].iloc[0]
        self.assertEqual(
            at_three["bar_close__3h"],
            pd.Timestamp("2026-01-01T03:00:00Z"),
        )
        self.assertEqual(at_three["age_bars__3h"], 0)
        at_four = joined.loc[
            joined["timestamp"] == pd.Timestamp("2026-01-01T04:00:00Z")
        ].iloc[0]
        self.assertEqual(
            at_four["bar_close__3h"],
            pd.Timestamp("2026-01-01T03:00:00Z"),
        )
        self.assertEqual(at_four["age_bars__3h"], 1)
        before_daily_close = joined.iloc[22]
        self.assertTrue(pd.isna(before_daily_close["bar_close__1d"]))
        at_daily_close = joined.iloc[23]
        self.assertEqual(
            at_daily_close["bar_close__1d"],
            pd.Timestamp("2026-01-02T00:00:00Z"),
        )

    def test_future_withholding_cannot_change_already_aligned_rows(self) -> None:
        base = hourly_fixture()
        full = build_multi_interval_frame(base, ["3h", "4h", "6h", "12h", "1d"])
        for cut in (24, 37, 55):
            prefix = build_multi_interval_frame(
                base.iloc[:cut].copy(),
                ["3h", "4h", "6h", "12h", "1d"],
            )
            pd.testing.assert_frame_equal(
                full.iloc[:cut].reset_index(drop=True),
                prefix,
            )

    def test_gaps_naive_timestamps_and_bad_bar_geometry_are_rejected(self) -> None:
        gap = hourly_fixture().drop(index=10).reset_index(drop=True)
        with self.assertRaisesRegex(IntervalContractError, "without gaps"):
            build_multi_interval_frame(gap, ["3h"])
        naive = hourly_fixture()
        naive["timestamp"] = naive["timestamp"].dt.tz_localize(None)
        with self.assertRaisesRegex(IntervalContractError, "explicit UTC offset"):
            build_multi_interval_frame(naive, ["3h"])
        bad = hourly_fixture()
        bad.loc[0, "high"] = bad.loc[0, "open"] - 2.0
        with self.assertRaisesRegex(IntervalContractError, "bar geometry"):
            build_multi_interval_frame(bad, ["3h"])


if __name__ == "__main__":
    unittest.main()
