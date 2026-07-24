from __future__ import annotations

import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autoquant.portfolio_explorer import load_portfolio_diagnostics
from autoquant.runs import execute_study
from autoquant.studio import build_studio_snapshot
from autoquant.studies import hash_file
from autoquant.templates import OHLCV_STUDY_ID, PORTFOLIO_STUDY_ID
from autoquant.workspace import AutoQuantValidationError, create_project, initialize_workspace


def make_lab(root: Path, *, template: str = "ohlcv-portfolio-lab"):
    workspace = initialize_workspace(root / "workspace")
    project = create_project(
        workspace.root_dir,
        "decision-lab",
        template=template,
    )
    study_id = (
        PORTFOLIO_STUDY_ID
        if template == "ohlcv-portfolio-lab"
        else OHLCV_STUDY_ID
    )
    return workspace, project, execute_study(project, study_id)


def rehash_run(run_root: Path) -> None:
    manifest_path = run_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = {
        path.relative_to(run_root).as_posix(): hash_file(path)
        for path in sorted(run_root.rglob("*"))
        if path.is_file() and path != manifest_path
    }
    manifest["resultHash"] = manifest["files"]["result.json"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class PortfolioDecisionExplorerTests(unittest.TestCase):
    def test_projection_preserves_full_path_anchors_book_and_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(Path(directory))

            diagnostics = load_portfolio_diagnostics(
                project,
                run.result["id"],
                point_limit=64,
            )

            self.assertEqual(
                diagnostics["kind"],
                "autoquant-portfolio-diagnostics",
            )
            self.assertEqual(diagnostics["run"]["inputHash"], run.result["inputHash"])
            self.assertEqual(diagnostics["path"]["sampledRows"], 64)
            self.assertGreater(diagnostics["path"]["totalRows"], 64)
            sampled_dates = {
                point["timestamp"] for point in diagnostics["path"]["points"]
            }
            self.assertIn(
                diagnostics["path"]["summary"]["maximumDrawdownAt"],
                sampled_dates,
            )
            self.assertIn(
                diagnostics["path"]["summary"]["maximumOneWayTurnoverAt"],
                sampled_dates,
            )
            self.assertEqual(
                diagnostics["path"]["points"][0]["timestamp"],
                run.result["metrics"]["split_protocol"]["splits"]["train"]["start"],
            )
            for split in ("train", "validation", "test"):
                contract = run.result["metrics"]["split_protocol"]["splits"][split]
                self.assertIn(contract["start"], sampled_dates)
                self.assertIn(contract["signalEnd"], sampled_dates)

            daily_path = run.root_dir / "artifacts" / "daily-portfolio.csv"
            with daily_path.open(encoding="utf-8", newline="") as handle:
                daily = list(csv.DictReader(handle))
            expected_net = math.prod(1.0 + float(row["net_return"]) for row in daily) - 1.0
            self.assertAlmostEqual(
                diagnostics["path"]["summary"]["netTotalReturn"],
                expected_net,
                places=12,
            )
            latest = diagnostics["currentBook"]
            self.assertEqual(latest["timestamp"], daily[-1]["timestamp"])
            self.assertEqual(len(latest["positions"]), 6)
            self.assertAlmostEqual(
                sum(abs(item["executedWeight"]) for item in latest["positions"]),
                latest["grossExposure"],
                places=9,
            )

            first_asset = diagnostics["universe"][0]
            expected = run.result["metrics"]["attribution"]["validation"]["by_asset"][
                first_asset
            ]
            observed = diagnostics["attribution"]["validation"][0]
            self.assertEqual(observed["asset"], first_asset)
            self.assertEqual(
                observed["annualizedNetContribution"],
                expected["annualized_net_contribution"],
            )
            self.assertLessEqual(len(diagnostics["recentTransitions"]), 40)
            transition_order = [
                (item["timestamp"], diagnostics["universe"].index(item["asset"]))
                for item in diagnostics["recentTransitions"]
            ]
            self.assertEqual(transition_order, sorted(transition_order))

    def test_point_and_artifact_size_limits_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(Path(directory))

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "point_limit must be 40..400",
            ):
                load_portfolio_diagnostics(
                    project,
                    run.result["id"],
                    point_limit=39,
                )
            with patch(
                "autoquant.portfolio_explorer.MAX_ARTIFACT_BYTES",
                1,
            ), self.assertRaisesRegex(
                AutoQuantValidationError,
                "exceeds 1 bytes",
            ):
                load_portfolio_diagnostics(project, run.result["id"])

    def test_non_portfolio_run_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(
                Path(directory),
                template="ohlcv-factor-lab",
            )

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "not a fixed Portfolio Lab",
            ):
                load_portfolio_diagnostics(project, run.result["id"])

    def test_rehashed_misaligned_artifacts_remain_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(Path(directory))
            daily_path = run.root_dir / "artifacts" / "daily-portfolio.csv"
            lines = daily_path.read_text(encoding="utf-8").splitlines()
            daily_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            rehash_run(run.root_dir)

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Executed weights must exactly match",
            ):
                load_portfolio_diagnostics(project, run.result["id"])

    def test_studio_drops_only_invalid_explorer_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, run = make_lab(Path(directory))
            daily_path = run.root_dir / "artifacts" / "daily-portfolio.csv"
            lines = daily_path.read_text(encoding="utf-8").splitlines()
            daily_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            rehash_run(run.root_dir)

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]

            self.assertEqual(len(observed["runs"]), 1)
            self.assertIsNone(observed["portfolioExplorer"])
            self.assertFalse(observed["valid"])
            self.assertTrue(
                any(
                    item["category"].startswith("portfolio-explorer:")
                    for item in observed["diagnostics"]
                )
            )


if __name__ == "__main__":
    unittest.main()
