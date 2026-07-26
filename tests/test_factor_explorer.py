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
            qualification = diagnostics["factorQualification"]
            self.assertTrue(qualification["available"])
            self.assertEqual(
                qualification["selection"]["split"],
                "train",
            )
            self.assertFalse(
                qualification["selection"]["validationEntersSelection"]
            )
            self.assertFalse(
                qualification["semantics"]["testEntersDiagnosis"]
            )
            self.assertEqual(
                qualification["validation"]["role"],
                "selection",
            )
            self.assertEqual(
                qualification["testAudit"]["role"],
                "visible-audit",
            )
            self.assertEqual(
                qualification["diagnosis"]["stage"],
                "raw-statistical-evidence-weak",
            )
            self.assertAlmostEqual(
                qualification["validation"]["candidate"]["meanRankIc"],
                diagnostics["summary"]["validation"]["meanRankIc"],
            )
            self.assertAlmostEqual(
                qualification["validation"]["styleNeutralCandidate"][
                    "meanRankIc"
                ]
                - qualification["validation"]["candidate"]["meanRankIc"],
                qualification["validation"]["incremental"][
                    "styleNeutralIcDelta"
                ],
            )
            self.assertEqual(
                len(
                    qualification["validation"][
                        "styleNeutralChronologicalFolds"
                    ]
                ),
                2,
            )
            components = diagnostics["factorComponents"]
            self.assertTrue(components["available"])
            self.assertEqual(
                components["trialDisclosure"],
                {
                    "materializedComponents": 1,
                    "pairwiseComparisons": 0,
                    "entersPromotionScore": False,
                },
            )
            self.assertEqual(
                components["validationDiagnosis"][
                    "strongestRawComponent"
                ],
                "base_momentum_10",
            )
            self.assertIsNone(
                components["components"][0]["nearestPeer"]["id"]
            )
            self.assertFalse(
                components["declaration"]["sourceInference"]
            )

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

            qualification_path = (
                run.root_dir / "artifacts" / "factor-qualification.csv"
            )
            original_qualification = qualification_path.read_text(
                encoding="utf-8"
            )
            qualification_rows = original_qualification.splitlines()
            cells = qualification_rows[1].split(",")
            header = qualification_rows[0].split(",")
            candidate_index = header.index("candidate_rank_ic_h1")
            cells[candidate_index] = "0.999"
            qualification_rows[1] = ",".join(cells)
            qualification_path.write_text(
                "\n".join(qualification_rows) + "\n",
                encoding="utf-8",
            )
            rehash_run(run.root_dir)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "candidate daily rank IC",
            ):
                load_factor_diagnostics(project, run.result["id"])

            qualification_path.write_text(
                original_qualification,
                encoding="utf-8",
            )
            component_path = (
                run.root_dir / "artifacts" / "factor-components.json"
            )
            original_components = component_path.read_text(
                encoding="utf-8"
            )
            tampered_components = json.loads(original_components)
            tampered_components["evidence"]["components"][0][
                "mean_coverage"
            ] = 0.123
            component_path.write_text(
                json.dumps(tampered_components, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            rehash_run(run.root_dir)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "does not reconcile immutable Run",
            ):
                load_factor_diagnostics(project, run.result["id"])

            component_path.write_text(
                original_components,
                encoding="utf-8",
            )
            result_path = run.root_dir / "result.json"
            report_path = run.root_dir / "artifacts" / "factor-report.json"
            legacy_result = json.loads(
                result_path.read_text(encoding="utf-8")
            )
            legacy_report = json.loads(
                report_path.read_text(encoding="utf-8")
            )
            legacy_result["metrics"].pop("factor_qualification")
            legacy_result["metrics"].pop("factor_components")
            legacy_result["artifacts"] = [
                item
                for item in legacy_result["artifacts"]
                if item["kind"]
                not in {"factor-qualification", "factor-components"}
            ]
            legacy_report["metrics"].pop("factor_qualification")
            legacy_report["metrics"].pop("factor_components")
            legacy_report["semantics"].pop("qualification")
            legacy_report["semantics"]["components"] = None
            result_path.write_text(
                json.dumps(legacy_result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            report_path.write_text(
                json.dumps(legacy_report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            qualification_path.unlink()
            component_path.unlink()
            rehash_run(run.root_dir)
            legacy = load_factor_diagnostics(project, run.result["id"])
            self.assertFalse(legacy["factorQualification"]["available"])
            self.assertFalse(legacy["factorComponents"]["available"])
            jsonschema.validate(
                legacy,
                FACTOR_DIAGNOSTICS_JSON_SCHEMA,
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
