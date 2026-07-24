from __future__ import annotations

import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jsonschema

from autoquant.factor_explorer import (
    FACTOR_DIAGNOSTICS_JSON_SCHEMA,
    load_factor_diagnostics,
)
from autoquant.runs import execute_study
from autoquant.studio import build_studio_snapshot
from autoquant.studies import hash_file
from autoquant.templates import OHLCV_STUDY_ID, PORTFOLIO_STUDY_ID
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)


def make_lab(root: Path, *, template: str = "ohlcv-factor-lab"):
    workspace = initialize_workspace(root / "workspace")
    project = create_project(
        workspace.root_dir,
        "factor-evidence",
        template=template,
    )
    study_id = (
        OHLCV_STUDY_ID
        if template == "ohlcv-factor-lab"
        else PORTFOLIO_STUDY_ID
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


class FactorEvidenceExplorerTests(unittest.TestCase):
    def test_projection_reconciles_paths_horizons_and_stability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, run = make_lab(Path(directory))
            diagnostics = load_factor_diagnostics(
                project,
                run.result["id"],
                point_limit=64,
            )

            self.assertEqual(
                diagnostics["kind"],
                "autoquant-factor-diagnostics",
            )
            self.assertEqual(diagnostics["run"]["inputHash"], run.result["inputHash"])
            self.assertEqual(diagnostics["icPath"]["sampledRows"], 64)
            self.assertGreater(diagnostics["icPath"]["totalRows"], 64)
            self.assertEqual(
                diagnostics["summary"]["validation"]["meanRankIc"],
                run.result["metrics"]["validation"]["mean_ic"],
            )
            self.assertEqual(
                diagnostics["summary"]["testAudit"]["meanRankIc"],
                run.result["metrics"]["test"]["mean_ic"],
            )
            self.assertFalse(diagnostics["protocol"]["testEntersSelection"])
            self.assertEqual(
                [item["horizon"] for item in diagnostics["horizonProfile"]],
                [1, 5, 10],
            )
            self.assertEqual(len(diagnostics["quantileSummary"]), 9)
            self.assertEqual(len(diagnostics["stability"]["assets"]), 18)
            self.assertEqual(len(diagnostics["stability"]["styles"]), 12)
            self.assertEqual(len(diagnostics["coverage"]), 6)

            sampled_dates = {
                item["timestamp"] for item in diagnostics["icPath"]["points"]
            }
            daily_path = run.root_dir / "artifacts" / "daily-factor-evidence.csv"
            with daily_path.open(encoding="utf-8", newline="") as handle:
                daily = list(csv.DictReader(handle))
            self.assertIn(daily[0]["timestamp"], sampled_dates)
            self.assertIn(daily[-1]["timestamp"], sampled_dates)
            for split in ("train", "validation", "test"):
                contract = run.result["metrics"]["split_protocol"]["splits"][split]
                self.assertIn(contract["start"], sampled_dates)
            maximum = max(
                daily,
                key=lambda row: abs(float(row["rank_ic_h1"] or 0.0)),
            )
            self.assertIn(maximum["timestamp"], sampled_dates)

            validation_quantiles = [
                item
                for item in diagnostics["quantilePath"]["points"]
                if item["split"] == "validation" and item["horizon"] == 1
            ]
            self.assertTrue(validation_quantiles)
            self.assertTrue(
                all(
                    math.isclose(
                        item["high"] - item["low"],
                        item["highMinusLow"],
                        abs_tol=1e-10,
                    )
                    for item in validation_quantiles
                )
            )
            jsonschema.validate(
                diagnostics,
                FACTOR_DIAGNOSTICS_JSON_SCHEMA,
            )

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]
            self.assertEqual(
                observed["factorExplorer"]["run"]["id"],
                run.result["id"],
            )
            self.assertIn(
                "run.factor",
                [item["id"] for item in observed["commands"]],
            )

    def test_limits_and_non_factor_runs_fail_structurally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(Path(directory))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "point_limit must be 40..400",
            ):
                load_factor_diagnostics(
                    project,
                    run.result["id"],
                    point_limit=39,
                )
            with patch(
                "autoquant.factor_explorer.MAX_ARTIFACT_BYTES",
                1,
            ), self.assertRaisesRegex(
                AutoQuantValidationError,
                "exceeds 1 bytes",
            ):
                load_factor_diagnostics(project, run.result["id"])

        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(
                Path(directory),
                template="ohlcv-portfolio-lab",
            )
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "not a fixed Factor Lab",
            ):
                load_factor_diagnostics(project, run.result["id"])

    def test_rehashed_truncated_daily_artifact_remains_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, run = make_lab(Path(directory))
            daily_path = run.root_dir / "artifacts" / "daily-factor-evidence.csv"
            lines = daily_path.read_text(encoding="utf-8").splitlines()
            daily_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            rehash_run(run.root_dir)

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Daily rows do not reconcile test split size",
            ):
                load_factor_diagnostics(project, run.result["id"])

    def test_studio_drops_only_invalid_factor_explorer_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, run = make_lab(Path(directory))
            daily_path = run.root_dir / "artifacts" / "daily-factor-evidence.csv"
            lines = daily_path.read_text(encoding="utf-8").splitlines()
            daily_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            rehash_run(run.root_dir)

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]

            self.assertEqual(len(observed["runs"]), 1)
            self.assertIsNone(observed["factorExplorer"])
            self.assertFalse(observed["valid"])
            self.assertTrue(
                any(
                    item["category"].startswith("factor-explorer:")
                    for item in observed["diagnostics"]
                )
            )


if __name__ == "__main__":
    unittest.main()
