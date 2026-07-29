from __future__ import annotations

import json
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
from autoquant.sessions import evaluate_experiment, start_session
from autoquant.studies import create_study
from autoquant.studio import build_studio_snapshot
from autoquant.templates import OHLCV_STUDY_ID
from autoquant.workspace import create_project, initialize_workspace
from tests.intake_helpers import write_intake_inputs
from tests.study_helpers import make_project, study_definition


class AgentOrientationTests(unittest.TestCase):
    def test_fixed_template_surfaces_dependency_bound_project_request(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(
                Path(directory) / "workspace",
                name="Quant Desk",
            )
            project = create_project(
                workspace.root_dir,
                "allocation-lab",
                template="ohlcv-allocation-lab",
            )
            request_path = project.root_dir / "request.json"

            brief = build_agent_work_brief(project)

            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                brief["question"],
                {
                    "title": "Synthetic equal-risk-contribution allocation",
                    "text": (
                        "Does fixed ERC improve on a fixed 60/40 reference?"
                    ),
                    "origin": "project-request",
                    "sourcePath": str(request_path),
                    "requestPath": str(request_path),
                },
            )

    def test_every_fixed_request_template_surfaces_project_request(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(
                Path(directory) / "workspace",
                name="Quant Desk",
            )

            for template in (
                "ohlcv-allocation-lab",
                "ohlcv-book-risk-lab",
                "ohlcv-event-study-lab",
            ):
                with self.subTest(template=template):
                    project = create_project(
                        workspace.root_dir,
                        template.removeprefix("ohlcv-"),
                        template=template,
                    )
                    request_path = project.root_dir / "request.json"

                    question = build_agent_work_brief(project)["question"]

                    self.assertEqual(question["origin"], "project-request")
                    self.assertTrue(question["text"])
                    self.assertEqual(question["sourcePath"], str(request_path))
                    self.assertEqual(question["requestPath"], str(request_path))

    def test_unbound_tampered_invalid_and_symlink_requests_are_not_authority(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = initialize_workspace(root / "workspace", name="Quant Desk")
            project = create_project(
                workspace.root_dir,
                "allocation-lab",
                template="ohlcv-allocation-lab",
            )
            request_path = project.root_dir / "request.json"
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["question"] = "Tampered but schema-valid question"
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            research_path = project.root_dir / "research.md"
            research_path.write_text(
                "# Allocation Lab\n\n"
                "## Question\n\n"
                "Does the explicit Markdown fallback remain visible?\n",
                encoding="utf-8",
            )

            tampered = build_agent_work_brief(project)["question"]

            self.assertEqual(tampered["origin"], "project-research-brief")
            self.assertEqual(
                tampered["text"],
                "Does the explicit Markdown fallback remain visible?",
            )
            request_path.write_text("{}\n", encoding="utf-8")
            invalid = build_agent_work_brief(project)["question"]
            self.assertEqual(invalid["origin"], "project-research-brief")

            unbound = create_project(
                workspace.root_dir,
                "unbound-lab",
                description="Safe manifest fallback",
            )
            (unbound.root_dir / "request.json").write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (unbound.root_dir / "research.md").write_text(
                "# Unbound Lab\n\n## Purpose\n\nNo explicit question.\n",
                encoding="utf-8",
            )
            unbound_question = build_agent_work_brief(unbound)["question"]
            self.assertEqual(unbound_question["origin"], "local")
            self.assertEqual(
                unbound_question["text"],
                "Safe manifest fallback",
            )

            symlinked = create_project(
                workspace.root_dir,
                "symlinked-lab",
                description="Safe symlink fallback",
                template="ohlcv-allocation-lab",
            )
            symlink_request = symlinked.root_dir / "request.json"
            outside = root / "outside-request.json"
            outside.write_bytes(symlink_request.read_bytes())
            symlink_request.unlink()
            symlink_request.symlink_to(outside)
            symlink_question = build_agent_work_brief(symlinked)["question"]
            self.assertEqual(symlink_question["origin"], "local")

    def test_local_question_comes_from_explicit_research_brief_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(
                Path(directory) / "workspace",
                name="Quant Desk",
            )
            project = create_project(
                workspace.root_dir,
                "brief-lab",
                name="Brief Lab",
                description="Stale create-time description",
            )
            research_path = project.root_dir / "research.md"
            research_path.write_text(
                """# Brief Lab

## Context

Do not mistake this prose for the active question.

```markdown
## Research question

This fenced example is not authority.
```

### Research question and hypotheses

Does the maintained
multi-line question reach a replacement Agent?

#### Supporting detail

Preserve this deeper detail with the question.

### Constraints

Stop the extracted section here.
""",
                encoding="utf-8",
            )

            brief = build_agent_work_brief(project)

            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                brief["question"],
                {
                    "title": "Brief Lab",
                    "text": (
                        "Does the maintained\n"
                        "multi-line question reach a replacement Agent?\n\n"
                        "#### Supporting detail\n\n"
                        "Preserve this deeper detail with the question."
                    ),
                    "origin": "project-research-brief",
                    "sourcePath": str(research_path),
                    "requestPath": None,
                },
            )

    def test_research_brief_question_is_bounded_for_compact_orientation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(
                Path(directory) / "workspace",
                name="Quant Desk",
            )
            project = create_project(workspace.root_dir, "bounded-lab")
            (project.root_dir / "research.md").write_text(
                "# Bounded Lab\n\n## Research question\n\n"
                + "signal " * 1_000,
                encoding="utf-8",
            )

            question = build_agent_work_brief(project)["question"]

            self.assertEqual(question["origin"], "project-research-brief")
            self.assertLessEqual(len(question["text"]), 4_000)
            self.assertTrue(question["text"].endswith("…"))

    def test_local_question_falls_back_when_brief_has_no_question_heading(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(
                Path(directory) / "workspace",
                name="Quant Desk",
            )
            project = create_project(
                workspace.root_dir,
                "fallback-lab",
                name="Fallback Lab",
                description="Use the manifest fallback",
            )
            (project.root_dir / "research.md").write_text(
                "# Fallback Lab\n\n## Purpose\n\nArbitrary method prose.\n",
                encoding="utf-8",
            )

            brief = build_agent_work_brief(project)

            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                brief["question"],
                {
                    "title": "Fallback Lab",
                    "text": "Use the manifest fallback",
                    "origin": "local",
                    "sourcePath": None,
                    "requestPath": None,
                },
            )

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

    def test_settled_keep_routes_to_primary_promotion_before_another_edit(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            session = start_session(project, "factor-quality")
            candidate = (
                session.worktree_project.root_dir / "factors" / "candidate.py"
            )
            candidate.write_text("SCORE = 2.0\n", encoding="utf-8")
            experiment = evaluate_experiment(
                project,
                session.manifest["id"],
                "Raise the bounded synthetic score once.",
            )
            self.assertEqual(experiment.result["verdict"], "KEEP")

            settled = build_agent_work_brief(project)

            jsonschema.validate(settled, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                settled["method"],
                "verified-project-agent-orientation-v6",
            )
            self.assertEqual(
                [item["code"] for item in settled["reasons"]],
                ["promotion-ready"],
            )
            self.assertEqual(
                settled["primaryAction"]["id"],
                "session.promote",
            )
            self.assertEqual(settled["supportingActions"], [])
            self.assertEqual(settled["focus"]["operatingMode"], "promote")
            self.assertEqual(
                settled["review"]["next"],
                settled["primaryAction"]["description"],
            )
            snapshot = build_studio_snapshot(project.root_dir)
            self.assertEqual(
                snapshot["projects"][0]["agentWorkBrief"]["primaryAction"],
                settled["primaryAction"],
            )

            candidate.write_text("SCORE = 3.0\n", encoding="utf-8")
            newer_candidate = build_agent_work_brief(project)

            self.assertEqual(
                newer_candidate["primaryAction"]["id"],
                "experiment.evaluate",
            )
            self.assertEqual(
                [item["id"] for item in newer_candidate["supportingActions"]],
                ["session.promote"],
            )
            self.assertEqual(
                [item["code"] for item in newer_candidate["reasons"]],
                ["session-active", "promotion-ready"],
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
            (project.root_dir / "research.md").write_text(
                "# Conflicting local brief\n\n"
                "## Research question\n\n"
                "This local text must not replace delegated authority.\n",
                encoding="utf-8",
            )

            brief = build_agent_work_brief(project)
            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(brief["question"]["origin"], "delegated-request")
            self.assertEqual(
                brief["question"]["text"],
                prepared.request["question"],
            )
            self.assertEqual(
                brief["question"]["requestPath"],
                str(project.root_dir / "request.json"),
            )
            self.assertEqual(
                brief["question"]["sourcePath"],
                str(project.root_dir / "request.json"),
            )
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
