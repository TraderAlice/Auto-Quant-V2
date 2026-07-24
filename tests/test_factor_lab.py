from __future__ import annotations

import shlex
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from autoquant.research import run_campaign
from autoquant.runs import execute_study, load_run
from autoquant.sessions import (
    evaluate_experiment,
    load_session,
    session_snapshot,
    start_session,
)
from autoquant.studies import load_study
from autoquant.studio import build_studio_snapshot
from autoquant.templates import OHLCV_STUDY_ID
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)


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


def make_factor_lab(directory: str | Path):
    workspace = initialize_workspace(Path(directory) / "workspace", name="Factor Desk")
    project = create_project(
        workspace.root_dir,
        "factor-lab",
        name="Factor Lab",
        template="ohlcv-factor-lab",
    )
    return workspace, project


class OhlcvFactorLabTests(unittest.TestCase):
    def test_template_constructs_content_locked_project_and_fast_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = make_factor_lab(directory)
            study = load_study(project, OHLCV_STUDY_ID)

            self.assertEqual(study.definition.dataset.paths, ["ohlcv/**"])
            self.assertEqual(len(study.dataset_hashes), 7)
            self.assertIn("ohlcv/ALPHA.csv", study.dataset_hashes)
            self.assertTrue((project.root_dir / "factors" / "candidate.py").is_file())
            self.assertTrue((project.root_dir / "judges" / "ohlcv_factor.py").is_file())

            run = execute_study(project, OHLCV_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            self.assertGreater(run.result["metrics"]["ic_dates"], 250)
            self.assertEqual(
                run.result["objective"]["metric"],
                "validation_mean_ic",
            )
            self.assertGreater(
                run.result["metrics"]["validation_mean_ic"],
                -1.0,
            )
            self.assertLess(
                run.result["metrics"]["validation_mean_ic"],
                1.0,
            )
            self.assertFalse(
                run.result["metrics"]["research_integrity"][
                    "test_enters_selection"
                ]
            )
            self.assertEqual(
                run.result["dataset"]["sourceHashes"],
                study.dataset_hashes,
            )
            self.assertTrue(
                (run.root_dir / "inputs" / "dataset-files.json").is_file()
            )
            self.assertEqual(
                load_run(project, run.result["id"]).result["inputHash"],
                run.result["inputHash"],
            )
            snapshot = build_studio_snapshot(workspace.root_dir)
            self.assertEqual(snapshot["projects"][0]["counts"]["runs"], 1)
            self.assertEqual(
                snapshot["projects"][0]["runs"][0]["metricLayers"]["kind"],
                "factor",
            )

    def test_known_factor_is_keep_and_future_leak_is_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_factor_lab(directory)
            session = start_session(project, OHLCV_STUDY_ID)
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
            self.assertGreater(kept.result["improvement"], 0.5)
            integrity = session_snapshot(
                project,
                load_session(project, session.manifest["id"]),
            )["selectionIntegrity"]
            self.assertEqual(integrity["selectionSplit"], "validation")
            self.assertFalse(integrity["testEntersSelection"])
            self.assertEqual(integrity["candidateTrials"], 1)
            self.assertTrue(integrity["externalHoldoutRequired"])

            active = load_session(project, session.manifest["id"])
            candidate = active.worktree_project.root_dir / "factors" / "candidate.py"
            candidate.write_text(LOOKAHEAD_FACTOR, encoding="utf-8")
            crashed = evaluate_experiment(
                project,
                session.manifest["id"],
                "Negative shift should be rejected as future leakage.",
            )
            self.assertEqual(crashed.result["verdict"], "CRASH")
            self.assertEqual(crashed.result["errors"][0]["code"], "factor.lookahead")

    def test_test_only_bar_changes_do_not_change_selection_metric(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_factor_lab(directory)
            before = execute_study(project, OHLCV_STUDY_ID)
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

            after = execute_study(project, OHLCV_STUDY_ID)

            self.assertEqual(
                before.result["metrics"]["validation_mean_ic"],
                after.result["metrics"]["validation_mean_ic"],
            )
            self.assertNotEqual(
                before.result["metrics"]["test"]["mean_ic"],
                after.result["metrics"]["test"]["mean_ic"],
            )

    def test_dataset_change_stales_session_and_changes_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_factor_lab(directory)
            before = load_study(project, OHLCV_STUDY_ID)
            session = start_session(project, OHLCV_STUDY_ID)
            self.assertEqual(
                list(
                    (
                        session.worktree_project.root_dir
                        / session.worktree_project.manifest.directories["data"]
                    ).iterdir()
                ),
                [],
            )

            alpha = project.root_dir / "data" / "ohlcv" / "ALPHA.csv"
            alpha.write_text(
                alpha.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            after = load_study(project, OHLCV_STUDY_ID)
            self.assertNotEqual(before.dataset_hash, after.dataset_hash)
            self.assertNotEqual(before.input_hash, after.input_hash)
            snapshot = session_snapshot(
                project,
                load_session(project, session.manifest["id"]),
            )
            self.assertFalse(snapshot["authority"]["valid"])
            self.assertTrue(
                any(
                    issue["code"] == "session.lock-stale"
                    and "datasetHash" in issue["message"]
                    for issue in snapshot["authority"]["issues"]
                )
            )

    def test_dataset_closure_rejects_symlink(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside,
        ):
            _, project = make_factor_lab(directory)
            target = project.root_dir / "data" / "ohlcv" / "escape.csv"
            target.symlink_to(Path(outside) / "bars.csv")
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Dataset closure contains a symlink",
            ):
                load_study(project, OHLCV_STUDY_ID)

    def test_invalid_template_does_not_publish_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Unknown Project template",
            ):
                create_project(
                    workspace.root_dir,
                    "bad-template",
                    template="not-real",
                )
            self.assertFalse((workspace.projects_dir / "bad-template").exists())

    def test_bounded_researcher_keep_is_visible_in_studio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = make_factor_lab(directory)
            session = start_session(project, OHLCV_STUDY_ID)
            researcher = Path(directory) / "factor_researcher.py"
            researcher.write_text(
                """\
import json
import os
from pathlib import Path

candidate = Path(os.environ["AUTOQUANT_WORKTREE"]) / "factors/candidate.py"
candidate.write_text('''from __future__ import annotations
import pandas as pd

def compute_factor(frame: pd.DataFrame) -> pd.Series:
    return frame["volume"] / frame["volume"].rolling(20, min_periods=20).mean() - 1.0
''')
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "relative-volume",
    "hypothesis": "Current relative volume predicts the next cross-sectional return.",
    "expected_effect": "Improve held-out rank IC without future access.",
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
            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]
            self.assertEqual(observed["counts"]["campaigns"], 1)
            self.assertEqual(observed["counts"]["verdicts"]["KEEP"], 1)
            self.assertEqual(observed["counts"]["runs"], 2)
            self.assertTrue(
                any(item["kind"] == "experiment" for item in observed["timeline"])
            )


if __name__ == "__main__":
    unittest.main()
