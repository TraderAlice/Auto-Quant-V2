from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jsonschema

from autoquant.rl_explorer import (
    RL_DIAGNOSTICS_JSON_SCHEMA,
    load_rl_diagnostics,
)
from autoquant.runs import execute_study
from autoquant.studio import build_studio_snapshot
from autoquant.studies import hash_file
from autoquant.templates import RL_STUDY_ID
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)


def make_lab(root: Path):
    workspace = initialize_workspace(root / "workspace")
    project = create_project(
        workspace.root_dir,
        "rl-evidence",
        template="ohlcv-rl-factor-lab",
    )
    return workspace, project, execute_study(project, RL_STUDY_ID)


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


class RlPolicyEvidenceExplorerTests(unittest.TestCase):
    def test_projection_reconciles_trials_baselines_training_and_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, run = make_lab(Path(directory))
            diagnostics = load_rl_diagnostics(
                project,
                run.result["id"],
                point_limit=64,
            )

            self.assertEqual(
                diagnostics["kind"],
                "autoquant-rl-policy-diagnostics",
            )
            self.assertEqual(diagnostics["run"]["inputHash"], run.result["inputHash"])
            self.assertEqual(len(diagnostics["trials"]), 6)
            self.assertEqual(len(diagnostics["baselines"]), 14)
            self.assertEqual(len(diagnostics["models"]), 6)
            self.assertEqual(len(diagnostics["training"]), 24)
            self.assertEqual(len(diagnostics["actionSummaries"]), 12)
            self.assertEqual(diagnostics["actionPath"]["sampledRows"], 64)
            self.assertEqual(diagnostics["actionPath"]["totalRows"], 780)
            self.assertFalse(diagnostics["protocol"]["testEntersSelection"])
            self.assertEqual(
                diagnostics["factorFusion"]["dependency"]["paths"],
                [
                    "factors/**",
                    "strategies/portfolio-mandate.json",
                ],
            )
            self.assertTrue(diagnostics["portfolioMandate"]["available"])
            self.assertEqual(
                diagnostics["portfolioMandate"]["family"],
                "dollar-neutral",
            )
            self.assertEqual(
                diagnostics["portfolioMandate"]["id"],
                run.result["metrics"]["portfolio_mandate"]["id"],
            )
            self.assertTrue(diagnostics["executedBookRisk"]["available"])
            self.assertEqual(
                diagnostics["executedBookRisk"]["selectionAuthority"],
                "context-only",
            )
            self.assertEqual(
                diagnostics["executedBookRisk"]["validation"][
                    "executedBreachDates"
                ],
                0,
            )
            self.assertEqual(
                diagnostics["executedBookRisk"]["validation"][
                    "trialPaths"
                ],
                6,
            )
            self.assertTrue(diagnostics["factorFusion"]["available"])
            self.assertEqual(
                diagnostics["factorFusion"][
                    "meanValidationAdvantageVsCandidateFactor"
                ],
                run.result["metrics"]["comparison"][
                    "mean_validation_advantage_vs_candidate_factor"
                ],
            )
            self.assertEqual(
                diagnostics["summary"]["validation"]["mean"],
                run.result["metrics"]["validation_mean_net_sharpe"],
            )
            self.assertEqual(
                diagnostics["summary"]["meanValidationAdvantageVsBestBaseline"],
                run.result["metrics"]["comparison"][
                    "mean_validation_advantage_vs_best_baseline"
                ],
            )
            behavior = diagnostics["policyBehavior"]
            self.assertTrue(behavior["available"])
            self.assertEqual(
                behavior["policy"]["qScale"],
                "uncalibrated-linear-model-score",
            )
            self.assertEqual(
                behavior["policy"]["selectionAuthority"],
                "context-only",
            )
            self.assertEqual(behavior["validation"]["decisions"], 360)
            self.assertEqual(behavior["validation"]["trialPaths"], 6)
            self.assertEqual(len(behavior["validation"]["byAction"]), 5)
            self.assertEqual(
                {
                    item["feature"]
                    for item in behavior["validation"]["byFeature"]
                },
                set(diagnostics["protocol"]["featureNames"]),
            )
            self.assertTrue(
                behavior["validation"]["reconciliation"]["passed"]
            )
            self.assertEqual(
                {
                    item["split"]
                    for item in behavior["representativeDecisions"]
                },
                {"validation", "test"},
            )
            opportunity = diagnostics["factorOpportunity"]
            self.assertTrue(opportunity["available"])
            self.assertEqual(
                opportunity["policy"]["method"],
                "actual-pretrade-one-step-governed-action-audit-v1",
            )
            self.assertEqual(
                opportunity["selectionAuthority"],
                "context-only",
            )
            self.assertEqual(opportunity["validation"]["decisions"], 360)
            self.assertEqual(opportunity["validation"]["trialPaths"], 6)
            self.assertEqual(
                opportunity["validation"]["reconciliation"][
                    "action_evaluations"
                ],
                1800,
            )
            self.assertTrue(
                opportunity["validation"]["reconciliation"]["passed"]
            )
            self.assertEqual(
                {
                    item["split"]
                    for item in opportunity["representativeDecisions"]
                },
                {"validation", "test"},
            )
            self.assertTrue(
                all(
                    item["selectedBaseline"] == "contextual-ridge"
                    for item in diagnostics["trials"]
                )
            )
            self.assertTrue(
                all(
                    sum(item["actionCounts"].values())
                    == diagnostics["protocol"]["ranges"][item["fold"]]["train"][
                        "observations"
                    ]
                    for item in diagnostics["training"]
                )
            )
            jsonschema.validate(diagnostics, RL_DIAGNOSTICS_JSON_SCHEMA)

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]
            self.assertEqual(
                observed["rlExplorer"]["run"]["id"],
                run.result["id"],
            )
            self.assertIn(
                "run.rl",
                [item["id"] for item in observed["commands"]],
            )

            result_path = run.root_dir / "result.json"
            report_path = run.root_dir / "artifacts" / "rl-report.json"
            rationale_path = (
                run.root_dir / "artifacts" / "policy-rationales.json"
            )
            opportunity_path = (
                run.root_dir / "artifacts" / "policy-opportunities.json"
            )
            legacy_result = json.loads(result_path.read_text(encoding="utf-8"))
            legacy_report = json.loads(report_path.read_text(encoding="utf-8"))
            legacy_result["metrics"].pop("policy_rationale")
            legacy_result["metrics"].pop("factor_opportunity")
            legacy_result["artifacts"] = [
                item
                for item in legacy_result["artifacts"]
                if item["kind"]
                not in {"policy-rationales", "policy-opportunities"}
            ]
            legacy_report["metrics"].pop("policy_rationale")
            legacy_report["metrics"].pop("factor_opportunity")
            result_path.write_text(
                json.dumps(legacy_result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            report_path.write_text(
                json.dumps(legacy_report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rationale_path.unlink()
            opportunity_path.unlink()
            rehash_run(run.root_dir)
            legacy = load_rl_diagnostics(project, run.result["id"])
            self.assertFalse(legacy["policyBehavior"]["available"])
            self.assertFalse(legacy["factorOpportunity"]["available"])

    def test_limits_and_rehashed_action_corruption_fail_structurally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, run = make_lab(Path(directory))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "point_limit must be 40..400",
            ):
                load_rl_diagnostics(project, run.result["id"], point_limit=39)
            with patch(
                "autoquant.rl_explorer.MAX_ARTIFACT_BYTES",
                1,
            ), self.assertRaisesRegex(
                AutoQuantValidationError,
                "exceeds 1 bytes",
            ):
                load_rl_diagnostics(project, run.result["id"])

            actions_path = run.root_dir / "artifacts" / "policy-actions.csv"
            rationale_path = (
                run.root_dir / "artifacts" / "policy-rationales.json"
            )
            original_rationale = rationale_path.read_text(encoding="utf-8")
            rationale = json.loads(original_rationale)
            rationale["rows"][0]["qValues"][
                rationale["actions"][0]
            ] += 0.125
            rationale_path.write_text(
                json.dumps(rationale, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rehash_run(run.root_dir)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "does not reconcile action Q value",
            ):
                load_rl_diagnostics(project, run.result["id"])
            rationale_path.write_text(original_rationale, encoding="utf-8")
            rehash_run(run.root_dir)

            opportunities_path = (
                run.root_dir / "artifacts" / "policy-opportunities.json"
            )
            original_opportunities = opportunities_path.read_text(
                encoding="utf-8"
            )
            opportunities = json.loads(original_opportunities)
            first_row = opportunities["rows"][0]
            selected = first_row["selectedAction"]
            first_asset = opportunities["assets"][0]
            first_row["actions"][selected]["executedWeights"][
                first_asset
            ] += 0.01
            opportunities_path.write_text(
                json.dumps(opportunities, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rehash_run(run.root_dir)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "executed minus pretrade weight",
            ):
                load_rl_diagnostics(project, run.result["id"])
            opportunities_path.write_text(
                original_opportunities,
                encoding="utf-8",
            )
            rehash_run(run.root_dir)

            original_actions = actions_path.read_text(encoding="utf-8")
            with actions_path.open(
                encoding="utf-8",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
                fields = list(rows[0])
            active = next(
                row
                for row in rows
                if row["execution_risk_forecast_available"] == "True"
            )
            active["executed_risk_forecast_annualized"] = str(
                float(active["execution_risk_ceiling_annualized"]) + 0.01
            )
            with actions_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            rehash_run(run.root_dir)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Action executed-book risk evidence is invalid",
            ):
                load_rl_diagnostics(project, run.result["id"])

            actions_path.write_text(original_actions, encoding="utf-8")
            rehash_run(run.root_dir)
            with actions_path.open(
                encoding="utf-8",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
                fields = list(rows[0])
            rows[0]["execution_risk_observations"] = "2.5"
            with actions_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            rehash_run(run.root_dir)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Expected a non-negative integer",
            ):
                load_rl_diagnostics(project, run.result["id"])

            actions_path.write_text(original_actions, encoding="utf-8")
            rehash_run(run.root_dir)
            lines = actions_path.read_text(encoding="utf-8").splitlines()
            actions_path.write_text(
                "\n".join(lines[:-1]) + "\n",
                encoding="utf-8",
            )
            rehash_run(run.root_dir)

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Action rows do not match declared split observations",
            ):
                load_rl_diagnostics(project, run.result["id"])

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]
            self.assertIsNone(observed["rlExplorer"])
            self.assertFalse(observed["valid"])
            self.assertTrue(
                any(
                    item["category"].startswith("rl-explorer:")
                    for item in observed["diagnostics"]
                )
            )


if __name__ == "__main__":
    unittest.main()
