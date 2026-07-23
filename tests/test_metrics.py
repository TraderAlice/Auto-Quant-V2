from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from autoquant.metrics import (
    normalize_session_risk_metrics,
    session_risk_metric_scale,
)
from autoquant.profiles import load_manifest


PROJECT_DIR = Path(__file__).resolve().parents[1]


class SessionMetricsTests(unittest.TestCase):
    def test_session_scale_replaces_calendar_clock_and_sqrt_365(self) -> None:
        scale = session_risk_metric_scale(
            calendar_days=365,
            session_days=252,
            annualization_days=252,
        )

        self.assertAlmostEqual(scale, math.sqrt(365 / 252))

    def test_invalid_session_count_is_neutral(self) -> None:
        self.assertEqual(
            session_risk_metric_scale(
                calendar_days=365,
                session_days=0,
                annualization_days=252,
            ),
            1.0,
        )

    def test_normalization_updates_aggregate_and_pair_metrics(self) -> None:
        base_profile = load_manifest(PROJECT_DIR / "harness.json").profile(
            "us-equities"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            profile = replace(
                base_profile,
                pairs=("AAPL/USD",),
                data_directory="data/us-equities",
            )
            data_dir = profile.data_dir(project)
            data_dir.mkdir(parents=True)
            dates = pd.bdate_range("2025-01-01", "2025-12-31", tz="UTC")
            pd.DataFrame(
                {
                    "date": dates,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 1_000.0,
                }
            ).to_feather(data_dir / "AAPL_USD-1d.feather")
            results = {
                "strategy": {
                    "Example": {
                        "backtest_start_ts": int(dates[0].timestamp() * 1_000),
                        "backtest_end_ts": int(dates[-1].timestamp() * 1_000),
                        "backtest_days": 364,
                        "sharpe": 1.0,
                        "sortino": 2.0,
                        "calmar": -100,
                        "results_per_pair": [
                            {
                                "key": "AAPL/USD",
                                "sharpe": 1.0,
                                "sortino": 2.0,
                                "calmar": -100,
                            }
                        ],
                    }
                }
            }

            normalize_session_risk_metrics(
                results,
                "Example",
                profile,
                project,
            )

        expected = session_risk_metric_scale(
            calendar_days=364,
            session_days=len(dates),
            annualization_days=252,
        )
        strategy = results["strategy"]["Example"]
        self.assertAlmostEqual(strategy["sharpe"], expected)
        self.assertAlmostEqual(
            strategy["results_per_pair"][0]["sortino"],
            2 * expected,
        )
        self.assertEqual(strategy["calmar"], -100)


if __name__ == "__main__":
    unittest.main()
