from __future__ import annotations

import math
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from autoquant.project_templates.ohlcv_portfolio_lab.portfolio_core import (
    constraint_audit,
    construct_targets,
    drift_weights,
    simulate_targets,
)
from autoquant.research import run_campaign
from autoquant.runs import execute_study
from autoquant.sessions import evaluate_experiment, start_session
from autoquant.studio import build_studio_snapshot
from autoquant.studies import load_study
from autoquant.templates import PORTFOLIO_STUDY_ID
from autoquant.workspace import create_project, initialize_workspace


IMPROVED_FACTOR = """\
from __future__ import annotations

import pandas as pd


def compute_factor(frame: pd.DataFrame) -> pd.Series:
    return frame["volume"] / frame["volume"].rolling(20, min_periods=20).mean() - 1.0
"""


LOOKAHEAD_FACTOR = """\
from __future__ import annotations

import pandas as pd


def compute_factor(frame: pd.DataFrame) -> pd.Series:
    return frame["close"].shift(-1) / frame["close"] - 1.0
"""


def make_portfolio_lab(directory: str | Path):
    workspace = initialize_workspace(
        Path(directory) / "workspace",
        name="Portfolio Desk",
    )
    project = create_project(
        workspace.root_dir,
        "portfolio-lab",
        name="Portfolio Lab",
        template="ohlcv-portfolio-lab",
    )
    return workspace, project


class PortfolioAccountingTests(unittest.TestCase):
    def test_constructed_targets_obey_gross_net_and_asset_caps(self) -> None:
        index = pd.bdate_range("2026-01-01", periods=50)
        assets = list("ABCDEF")
        factors = pd.DataFrame(
            np.tile(np.arange(6, dtype=float), (len(index), 1)),
            index=index,
            columns=assets,
        )
        closes = pd.DataFrame(
            {
                asset: 100.0
                * np.exp(
                    np.cumsum(
                        0.001 * (column + 1)
                        + 0.002
                        * np.sin(np.arange(len(index)) / (4.0 + column))
                    )
                )
                for column, asset in enumerate(assets)
            },
            index=index,
        )

        targets = construct_targets(factors, closes)
        audit = constraint_audit(targets)

        self.assertTrue(audit["passed"])
        self.assertGreater(audit["active_dates"], 20)
        self.assertLessEqual(audit["maximum_gross_error"], 1e-8)
        self.assertLessEqual(audit["maximum_abs_net_target"], 1e-8)
        self.assertLessEqual(audit["maximum_abs_target_weight"], 0.30 + 1e-8)

    def test_target_earns_only_the_return_after_its_decision_bar(self) -> None:
        index = pd.bdate_range("2026-01-01", periods=4)
        targets = pd.DataFrame(
            [[0.0, 0.0], [0.5, -0.5], [0.5, -0.5], [0.5, -0.5]],
            index=index,
            columns=["A", "B"],
        )
        closes = pd.DataFrame(
            {
                "A": [100.0, 200.0, 200.0, 220.0],
                "B": [100.0, 100.0, 100.0, 100.0],
            },
            index=index,
        )
        volumes = pd.DataFrame(
            1_000_000.0,
            index=index,
            columns=targets.columns,
        )

        simulation = simulate_targets(
            targets,
            closes,
            volumes,
            cost_bps=0.0,
            no_trade_one_way=0.0,
        )

        self.assertEqual(simulation.daily.loc[index[1], "gross_return"], 0.0)
        self.assertAlmostEqual(
            simulation.daily.loc[index[2], "gross_return"],
            0.05,
        )

    def test_extra_delay_moves_target_to_the_following_decision_bar(self) -> None:
        index = pd.bdate_range("2026-01-01", periods=4)
        targets = pd.DataFrame(
            [[0.0, 0.0], [0.5, -0.5], [0.0, 0.0], [0.0, 0.0]],
            index=index,
            columns=["A", "B"],
        )
        closes = pd.DataFrame(
            {
                "A": [100.0, 100.0, 110.0, 132.0],
                "B": [100.0, 100.0, 100.0, 100.0],
            },
            index=index,
        )
        volumes = pd.DataFrame(
            1_000_000.0,
            index=index,
            columns=targets.columns,
        )

        base = simulate_targets(
            targets,
            closes,
            volumes,
            cost_bps=0.0,
            no_trade_one_way=0.0,
        )
        delayed = simulate_targets(
            targets,
            closes,
            volumes,
            cost_bps=0.0,
            no_trade_one_way=0.0,
            extra_delay=1,
        )

        self.assertAlmostEqual(base.daily.loc[index[1], "gross_return"], 0.05)
        self.assertEqual(delayed.daily.loc[index[1], "gross_return"], 0.0)
        self.assertAlmostEqual(delayed.daily.loc[index[2], "gross_return"], 0.10)

    def test_drift_turnover_and_cost_conventions_are_explicit(self) -> None:
        previous = pd.Series({"A": 0.5, "B": -0.5})
        realized = pd.Series({"A": 0.10, "B": 0.0})
        drifted = drift_weights(previous, realized)
        expected = pd.Series({"A": 0.55 / 1.05, "B": -0.5 / 1.05})
        pd.testing.assert_series_equal(drifted, expected)

        index = pd.bdate_range("2026-01-01", periods=3)
        targets = pd.DataFrame(
            [[0.5, -0.5]] * 3,
            index=index,
            columns=["A", "B"],
        )
        closes = pd.DataFrame(
            {"A": [100.0, 110.0, 110.0], "B": [100.0, 100.0, 100.0]},
            index=index,
        )
        volumes = pd.DataFrame(
            1_000_000.0,
            index=index,
            columns=targets.columns,
        )
        simulation = simulate_targets(targets, closes, volumes)

        first = simulation.daily.loc[index[0]]
        self.assertAlmostEqual(first["traded_notional"], 1.0)
        self.assertAlmostEqual(first["one_way_turnover"], 0.5)
        self.assertAlmostEqual(first["cost"], 0.001)
        self.assertFalse(bool(simulation.daily.loc[index[1], "rebalanced"]))
        self.assertAlmostEqual(
            float(simulation.trades.loc[index[1]].abs().sum()),
            0.0,
        )


class OhlcvPortfolioLabTests(unittest.TestCase):
    def test_template_runs_fast_and_emits_layered_portfolio_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = make_portfolio_lab(directory)
            study = load_study(project, PORTFOLIO_STUDY_ID)
            self.assertEqual(study.definition.editable["paths"], ["factors/**"])
            self.assertEqual(study.definition.judge.paths, ["judges/**"])
            self.assertEqual(len(study.dataset_hashes), 7)

            run = execute_study(project, PORTFOLIO_STUDY_ID)

            self.assertEqual(run.result["status"], "succeeded")
            metrics = run.result["metrics"]
            self.assertEqual(
                run.result["objective"]["metric"],
                "validation_net_sharpe",
            )
            self.assertTrue(math.isfinite(metrics["validation_net_sharpe"]))
            self.assertIn("factor", metrics)
            self.assertIn("portfolio", metrics)
            self.assertIn("implementation", metrics)
            self.assertIn("robustness", metrics)
            self.assertTrue(metrics["constraint_audit"]["passed"])
            self.assertFalse(
                metrics["research_integrity"]["test_enters_selection"]
            )
            self.assertEqual(
                {item["kind"] for item in run.result["artifacts"]},
                {"portfolio-report", "portfolio-daily", "portfolio-weights"},
            )
            snapshot = build_studio_snapshot(workspace.root_dir)
            self.assertEqual(snapshot["projects"][0]["counts"]["runs"], 1)
            layers = snapshot["projects"][0]["runs"][0]["metricLayers"]
            self.assertEqual(layers["kind"], "portfolio")
            self.assertTrue(layers["constraintsPassed"])
            self.assertTrue(
                math.isfinite(layers["portfolio"]["testNetSharpe"])
            )

    def test_test_only_bar_changes_do_not_change_selection_metric(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_portfolio_lab(directory)
            before = execute_study(project, PORTFOLIO_STUDY_ID)
            for asset_number, source in enumerate(
                sorted((project.root_dir / "data" / "ohlcv").glob("*.csv"))
            ):
                frame = pd.read_csv(source)
                rows = frame.index[-40:]
                direction = 1.0 if asset_number % 2 else -1.0
                scale = 1.0 + direction * np.linspace(0.0, 0.30, len(rows))
                frame.loc[rows, ["open", "high", "low", "close"]] = (
                    frame.loc[rows, ["open", "high", "low", "close"]]
                    .mul(scale, axis=0)
                )
                frame.to_csv(source, index=False)

            after = execute_study(project, PORTFOLIO_STUDY_ID)

            self.assertEqual(
                before.result["metrics"]["validation_net_sharpe"],
                after.result["metrics"]["validation_net_sharpe"],
            )
            self.assertNotEqual(
                before.result["metrics"]["portfolio"]["test"]["net"]["sharpe"],
                after.result["metrics"]["portfolio"]["test"]["net"]["sharpe"],
            )

    def test_known_factor_is_keep_and_future_leak_is_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_portfolio_lab(directory)
            session = start_session(project, PORTFOLIO_STUDY_ID)
            candidate = (
                session.worktree_project.root_dir / "factors" / "candidate.py"
            )
            candidate.write_text(IMPROVED_FACTOR, encoding="utf-8")
            kept = evaluate_experiment(
                project,
                session.manifest["id"],
                "Current relative volume predicts the next cross-sectional return.",
            )
            self.assertEqual(kept.result["verdict"], "KEEP")
            self.assertGreater(kept.result["improvement"], 10.0)

            candidate.write_text(LOOKAHEAD_FACTOR, encoding="utf-8")
            crashed = evaluate_experiment(
                project,
                session.manifest["id"],
                "Negative shift should be rejected as future leakage.",
            )
            self.assertEqual(crashed.result["verdict"], "CRASH")
            self.assertEqual(crashed.result["errors"][0]["code"], "factor.lookahead")

    def test_external_campaign_and_studio_share_portfolio_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = make_portfolio_lab(directory)
            session = start_session(project, PORTFOLIO_STUDY_ID)
            researcher = Path(directory) / "portfolio_researcher.py"
            researcher.write_text(
                """\
import json
import os
from pathlib import Path

Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text(
    '''from __future__ import annotations
import pandas as pd

def compute_factor(frame: pd.DataFrame) -> pd.Series:
    return frame["volume"] / frame["volume"].rolling(20, min_periods=20).mean() - 1.0
'''
)
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "relative-volume-portfolio",
    "hypothesis": "Relative volume survives fixed portfolio costs.",
    "expected_effect": "Improve robust held-out net Sharpe.",
}))
""",
                encoding="utf-8",
            )
            campaign = run_campaign(
                project,
                session.manifest["id"],
                f"{shlex.quote(sys.executable)} {shlex.quote(str(researcher))}",
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )

            self.assertEqual(campaign.result["verdicts"]["KEEP"], 1)
            observed = build_studio_snapshot(workspace.root_dir)["projects"][0]
            self.assertEqual(observed["counts"]["campaigns"], 1)
            self.assertTrue(
                all("metricLayers" in run for run in observed["runs"])
            )


if __name__ == "__main__":
    unittest.main()
