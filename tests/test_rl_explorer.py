from __future__ import annotations

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
                ["factors/**"],
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
