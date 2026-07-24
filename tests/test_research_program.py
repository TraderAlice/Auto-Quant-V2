from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import jsonschema

from autoquant.intake import prepare_project_intake
from autoquant.research_program import (
    RESEARCH_PROGRAM_STATUS_JSON_SCHEMA,
    load_research_program,
)
from autoquant.runs import execute_study
from autoquant.sessions import start_session
from autoquant.studio import build_studio_snapshot
from autoquant.studies import load_study
from autoquant.templates import (
    OHLCV_STUDY_ID,
    PORTFOLIO_STUDY_ID,
    RL_STUDY_ID,
)
from autoquant.workspace import create_project, initialize_workspace
from tests.intake_helpers import write_intake_inputs


class MultiStudyResearchProgramTests(unittest.TestCase):
    def test_one_intake_coordinates_factor_portfolio_and_rl_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(root / "workspace", name="Quant Desk")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                workspace.root_dir,
                "leadership-desk",
                name=prepared.request["title"],
                description=prepared.request["question"],
                template=prepared.template,
                template_intake=prepared,
            )

            initial = load_research_program(project)
            assert initial is not None
            jsonschema.validate(initial, RESEARCH_PROGRAM_STATUS_JSON_SCHEMA)
            self.assertEqual(
                [lane["id"] for lane in initial["lanes"]],
                ["factor", "portfolio", "rl"],
            )
            self.assertEqual(
                [lane["phase"] for lane in initial["lanes"]],
                ["not-started", "not-started", "not-started"],
            )
            self.assertEqual(initial["recommendedLaneId"], "factor")
            self.assertEqual(initial["recommendedAction"]["id"], "run.execute")
            self.assertEqual(
                {lane["study"]["datasetHash"] for lane in initial["lanes"]},
                {initial["datasetHash"]},
            )
            self.assertEqual(
                initial["lanes"][0]["study"]["sourceHash"],
                initial["lanes"][1]["study"]["sourceHash"],
            )
            self.assertNotEqual(
                initial["lanes"][1]["study"]["sourceHash"],
                initial["lanes"][2]["study"]["sourceHash"],
            )

            runs = {
                study_id: execute_study(project, study_id)
                for study_id in (
                    OHLCV_STUDY_ID,
                    PORTFOLIO_STUDY_ID,
                    RL_STUDY_ID,
                )
            }
            self.assertTrue(
                all(run.result["status"] == "succeeded" for run in runs.values())
            )

            baseline = load_research_program(project)
            assert baseline is not None
            self.assertEqual(
                [lane["phase"] for lane in baseline["lanes"]],
                ["baseline-ready", "baseline-ready", "baseline-ready"],
            )
            self.assertTrue(
                all(lane["latestRun"]["value"] is not None for lane in baseline["lanes"])
            )
            self.assertEqual(baseline["recommendedAction"]["id"], "session.start")

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]["researchProgramStatus"]
            self.assertEqual(observed["datasetHash"], baseline["datasetHash"])
            self.assertEqual(observed["summary"]["lanes"], 3)

            start_session(project, OHLCV_STUDY_ID)
            start_session(project, PORTFOLIO_STUDY_ID)
            conflicted = load_research_program(project)
            assert conflicted is not None
            self.assertEqual(conflicted["summary"]["activeSessions"], 2)
            self.assertEqual(conflicted["summary"]["conflicts"], 1)
            self.assertEqual(conflicted["conflicts"][0]["editablePath"], "factors/**")

            candidate_path = project.root_dir / "factors" / "candidate.py"
            candidate_path.write_text(
                candidate_path.read_text(encoding="utf-8")
                + "\n# evidence staleness probe\n",
                encoding="utf-8",
            )
            stale = load_research_program(project)
            assert stale is not None
            self.assertFalse(stale["lanes"][0]["currentRun"])
            self.assertFalse(stale["lanes"][1]["currentRun"])
            self.assertTrue(stale["lanes"][2]["currentRun"])
            self.assertEqual(
                [lane["phase"] for lane in stale["lanes"]],
                ["stale", "stale", "baseline-ready"],
            )
            self.assertEqual(stale["recommendedAction"]["id"], "run.execute")

            self.assertEqual(
                load_study(project, OHLCV_STUDY_ID).dataset_hash,
                load_study(project, RL_STUDY_ID).dataset_hash,
            )
            manifest = json.loads(
                (project.root_dir / "research-program.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["template"], "ohlcv-research-desk")
