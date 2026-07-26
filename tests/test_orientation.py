from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import jsonschema

from autoquant.intake import prepare_project_intake
from autoquant.orientation import (
    AGENT_WORK_BRIEF_JSON_SCHEMA,
    build_agent_work_brief,
)
from autoquant.runs import execute_study
from autoquant.sessions import start_session
from autoquant.studies import create_study
from autoquant.templates import OHLCV_STUDY_ID
from autoquant.workspace import create_project, initialize_workspace
from tests.intake_helpers import write_intake_inputs
from tests.study_helpers import make_project, study_definition


class AgentOrientationTests(unittest.TestCase):
    def test_single_study_moves_from_baseline_to_session_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())

            initial = build_agent_work_brief(project)
            jsonschema.validate(initial, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                initial["primaryAction"]["id"],
                "run.execute",
            )
            self.assertFalse(initial["filesystem"]["writable"])
            self.assertEqual(initial["filesystem"]["editablePaths"], [])
            self.assertEqual(
                initial["filesystem"]["declaredEditablePaths"],
                ["factors/**"],
            )

            execute_study(project, "factor-quality")
            baseline = build_agent_work_brief(project)
            jsonschema.validate(baseline, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                baseline["researchAgenda"]["status"],
                "unsupported-study",
            )
            self.assertEqual(
                baseline["primaryAction"]["id"],
                "session.start",
            )
            self.assertFalse(baseline["filesystem"]["writable"])

            session = start_session(project, "factor-quality")
            active = build_agent_work_brief(project)
            jsonschema.validate(active, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                active["primaryAction"]["id"],
                "experiment.evaluate",
            )
            self.assertTrue(active["filesystem"]["writable"])
            self.assertEqual(
                active["filesystem"]["operatingRoot"],
                str(session.worktree_project.root_dir),
            )
            self.assertEqual(
                active["filesystem"]["editablePaths"],
                ["factors/**"],
            )
            self.assertEqual(
                active["authority"]["tradingAuthority"],
                "none",
            )

            (project.root_dir / "judges" / "evaluate.py").write_text(
                "raise SystemExit('changed fixed authority')\n",
                encoding="utf-8",
            )
            stale = build_agent_work_brief(project)
            jsonschema.validate(stale, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                stale["reasons"][0]["code"],
                "current-evidence-stale",
            )
            self.assertEqual(
                stale["primaryAction"]["id"],
                "session.show",
            )
            self.assertEqual(stale["review"]["status"], "blocked")
            self.assertFalse(stale["filesystem"]["writable"])
            self.assertEqual(
                stale["filesystem"]["operatingRoot"],
                str(project.root_dir),
            )

    def test_research_desk_orients_to_verified_factor_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(
                root / "workspace",
                name="Quant Desk",
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                workspace.root_dir,
                "agent-desk",
                name=prepared.request["title"],
                description=prepared.request["question"],
                template=prepared.template,
                template_intake=prepared,
            )

            brief = build_agent_work_brief(project)
            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(brief["question"]["origin"], "delegated-request")
            self.assertEqual(brief["focus"]["laneId"], "factor")
            self.assertEqual(brief["focus"]["studyId"], OHLCV_STUDY_ID)
            self.assertEqual(
                brief["focus"]["scientificStage"],
                "factor-evidence-required",
            )
            self.assertEqual(
                brief["reasons"][0]["code"],
                "baseline-evidence-missing",
            )
            self.assertEqual(brief["primaryAction"]["id"], "run.execute")
            self.assertEqual(
                brief["researchAgenda"]["status"],
                "waiting-evidence",
            )
            self.assertEqual(brief["researchAgenda"]["moves"], [])
            self.assertEqual(
                brief["authority"],
                {
                    "researchAuthority": "research-prioritization-only",
                    "selectionSplit": "validation",
                    "testRole": "visible-audit",
                    "testEntersSelection": False,
                    "tradingAuthority": "none",
                },
            )

    def test_blank_project_is_observable_but_not_writable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(
                Path(directory) / "workspace",
                name="Quant Desk",
            )
            project = create_project(
                workspace.root_dir,
                "blank-lab",
                name="Blank Lab",
            )
            brief = build_agent_work_brief(project)
            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(brief["reasons"][0]["code"], "study-required")
            self.assertIsNone(brief["primaryAction"])
            self.assertFalse(brief["filesystem"]["writable"])

    def test_uncoordinated_multi_study_project_is_not_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition(study_id="first-study"))
            create_study(project, study_definition(study_id="second-study"))

            brief = build_agent_work_brief(project)
            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                brief["reasons"][0]["code"],
                "study-selection-required",
            )
            self.assertIsNone(brief["primaryAction"])
            self.assertFalse(brief["filesystem"]["writable"])
            self.assertEqual(
                [item["id"] for item in brief["supportingActions"]],
                ["study.inspect", "study.inspect"],
            )
