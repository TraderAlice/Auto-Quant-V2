from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoquant.dossiers import load_dossier, load_dossier_status, publish_dossier
from autoquant.intake import load_project_intake, prepare_project_intake
from autoquant.reports import REPORT_MARKDOWN
from autoquant.research_program import load_research_program
from autoquant.run_reports import (
    list_run_reports,
    load_run_report,
    publish_run_report,
)
from autoquant.runs import execute_study
from autoquant.sessions import list_sessions, start_session
from autoquant.studio import build_studio_snapshot
from autoquant.workspace import (
    AutoQuantValidationError,
    create_or_intake_project,
    create_project,
    initialize_workspace,
)
from tests.intake_helpers import write_intake_inputs
from tests.test_cli import json_output, run_cli


def analysis(run_id: str, artifact_path: str = "artifacts/factor-report.json") -> dict:
    reference = {
        "kind": "run",
        "id": run_id,
        "artifactPath": artifact_path,
    }
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-report-analysis",
        "title": "Frozen baseline evidence",
        "executiveSummary": (
            "The current immutable Run provides bounded evidence without a "
            "candidate-edit investigation."
        ),
        "findings": [
            {
                "id": "frozen-current-run",
                "claim": "The Report is anchored to the exact current Study Run.",
                "confidence": "high",
                "evidenceRefs": [reference],
            }
        ],
        "recommendations": [],
        "limitations": ["This evidence grants no trading authority."],
        "unresolvedQuestions": [],
    }


class RunBoundResearchReportTests(unittest.TestCase):
    def _request_project(self, root: Path):
        workspace = initialize_workspace(root / "workspace")
        request, dataset = write_intake_inputs(root)
        prepared = prepare_project_intake(
            request,
            dataset,
            "ohlcv-research-desk",
        )
        project = create_or_intake_project(
            workspace.root_dir,
            "run-report-desk",
            name="Run Report Desk",
            description="Frozen baseline handoff",
            template="ohlcv-research-desk",
            template_intake=prepared,
        )
        return workspace, project

    def test_current_run_report_needs_no_session_and_projects_everywhere(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = self._request_project(Path(directory))
            run = execute_study(project, "ohlcv-factor-quality")
            self.assertEqual(run.result["status"], "succeeded")
            self.assertEqual(list_sessions(project), [])
            before_report = load_dossier_status(project)
            self.assertEqual(before_report["nextAction"]["id"], "report.publish")
            self.assertIn("--study", before_report["nextAction"]["argv"])
            self.assertIn("--run", before_report["nextAction"]["argv"])
            self.assertNotIn("--session", before_report["nextAction"]["argv"])

            report = publish_run_report(
                project,
                "ohlcv-factor-quality",
                run.result["id"],
                analysis(run.result["id"]),
            )

            self.assertEqual(report.report["anchor"]["kind"], "run")
            self.assertIsNone(report.report["anchor"]["sessionId"])
            self.assertEqual(report.report["anchor"]["runId"], run.result["id"])
            self.assertEqual(report.report["evidence"]["anchor"]["kind"], "run")
            self.assertNotIn("session", report.report["evidence"])
            self.assertEqual(list_sessions(project), [])
            self.assertEqual(
                report.root_dir.parent,
                project.root_dir / "reports",
            )
            self.assertIn(
                "no Session, Check, Experiment, or candidate-edit authority",
                (report.root_dir / REPORT_MARKDOWN).read_text(encoding="utf-8"),
            )
            self.assertEqual(
                load_run_report(project, report.report["id"]).report,
                report.report,
            )
            summary = list_run_reports(project, "ohlcv-factor-quality")[0]
            self.assertEqual(summary.anchor_kind, "run")
            self.assertIsNone(summary.session_id)

            program = load_research_program(project)
            factor = program["lanes"][0]
            self.assertEqual(factor["phase"], "reported")
            self.assertEqual(factor["reports"][0]["anchor"]["kind"], "run")
            self.assertIsNone(factor["latestSession"])

            dossier_status = load_dossier_status(project)
            self.assertTrue(dossier_status["ready"])
            self.assertEqual(dossier_status["includedLaneIds"], ["factor"])
            self.assertIsNone(dossier_status["lanes"][0]["session"])
            self.assertEqual(
                dossier_status["lanes"][0]["report"]["anchor"]["kind"],
                "run",
            )
            dossier = publish_dossier(
                project,
                {
                    "schemaVersion": 1,
                    "kind": "autoquant-research-dossier-analysis",
                    "title": "Frozen factor conclusion",
                    "executiveSummary": "The fixed Factor lane is reported.",
                    "findings": [
                        {
                            "id": "factor-reported",
                            "claim": "The Factor conclusion is immutable.",
                            "confidence": "high",
                            "evidenceRefs": [
                                {
                                    "laneId": "factor",
                                    "reportId": report.report["id"],
                                    "findingId": "frozen-current-run",
                                }
                            ],
                        }
                    ],
                    "recommendations": [],
                    "limitations": [],
                    "unresolvedQuestions": [],
                },
            )
            loaded_dossier = load_dossier(project, dossier.dossier["id"])
            frozen_report = loaded_dossier.dossier["evidence"]["lanes"][0]["report"]
            self.assertEqual(frozen_report["anchor"]["kind"], "run")
            self.assertIsNone(frozen_report["sessionId"])

            snapshot = build_studio_snapshot(workspace.root_dir)
            projected = snapshot["projects"][0]
            self.assertTrue(snapshot["valid"])
            self.assertEqual(projected["counts"]["sessions"], 0)
            self.assertEqual(projected["counts"]["reports"], 1)
            self.assertEqual(projected["runReports"][0]["anchor"]["kind"], "run")
            self.assertIn(
                report.report["id"],
                [item["id"] for item in projected["timeline"]],
            )

            markdown = report.root_dir / REPORT_MARKDOWN
            markdown.write_text(markdown.read_text() + "tampered\n", encoding="utf-8")
            with self.assertRaises(AutoQuantValidationError) as tampered:
                load_run_report(project, report.report["id"])
            self.assertIn(
                "report.tampered",
                {item.code for item in tampered.exception.issues},
            )

    def test_cli_publishes_lists_and_shows_run_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _workspace, project = self._request_project(root)
            run = execute_study(project, "ohlcv-factor-quality")
            analysis_path = root / "analysis.json"
            analysis_path.write_text(
                json.dumps(analysis(run.result["id"]), indent=2) + "\n",
                encoding="utf-8",
            )

            published = run_cli(
                "report",
                "publish",
                str(project.root_dir),
                "--study",
                "ohlcv-factor-quality",
                "--run",
                run.result["id"],
                "--analysis",
                str(analysis_path),
                "--json",
            )
            self.assertEqual(published.returncode, 0, published.stderr)
            envelope = json_output(published)
            report_id = envelope["data"]["report"]["id"]
            self.assertEqual(envelope["data"]["report"]["anchor"]["kind"], "run")
            self.assertEqual(envelope["data"]["anchor"]["kind"], "run")
            self.assertEqual(
                [item["id"] for item in envelope["nextActions"]],
                ["report.show"],
            )
            self.assertNotIn("--session", envelope["nextActions"][0]["argv"])

            listed = run_cli(
                "report",
                "list",
                str(project.root_dir),
                "--study",
                "ohlcv-factor-quality",
                "--json",
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(
                json_output(listed)["data"]["reports"][0]["anchor"]["kind"],
                "run",
            )
            shown = run_cli(
                "report",
                "show",
                str(project.root_dir),
                "--report",
                report_id,
                "--json",
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertEqual(json_output(shown)["data"]["report"]["id"], report_id)
            self.assertEqual(json_output(shown)["data"]["anchor"]["kind"], "run")

            mixed = run_cli(
                "report",
                "publish",
                str(project.root_dir),
                "--session",
                "session-invalid",
                "--study",
                "ohlcv-factor-quality",
                "--run",
                run.result["id"],
                "--analysis",
                str(analysis_path),
                "--json",
            )
            self.assertEqual(mixed.returncode, 2)
            self.assertIn("exactly one anchor", json_output(mixed)["error"]["message"])

    def test_run_report_cannot_bypass_a_later_editable_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _workspace, project = self._request_project(Path(directory))
            run = execute_study(project, "ohlcv-factor-quality")
            publish_run_report(
                project,
                "ohlcv-factor-quality",
                run.result["id"],
                analysis(run.result["id"]),
            )
            intake = load_project_intake(project)
            assert intake is not None
            session = start_session(
                project,
                "ohlcv-factor-quality",
                request=intake["request"],
            )
            with self.assertRaises(AutoQuantValidationError) as history:
                publish_run_report(
                    project,
                    "ohlcv-factor-quality",
                    run.result["id"],
                    analysis(run.result["id"]),
                )
            self.assertIn(
                "report.session-history",
                {item.code for item in history.exception.issues},
            )

            program = load_research_program(project)
            factor = program["lanes"][0]
            self.assertEqual(factor["latestSession"]["id"], session.manifest["id"])
            self.assertEqual(factor["reports"], [])
            self.assertEqual(factor["phase"], "researching")
            status = load_dossier_status(project)
            self.assertFalse(status["ready"])
            self.assertEqual(status["lanes"][0]["session"]["id"], session.manifest["id"])
            self.assertIsNone(status["lanes"][0]["report"])
            self.assertIn(
                "dossier.report-missing",
                {item["code"] for item in status["blockers"]},
            )

    def test_older_run_report_does_not_report_a_newer_current_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _workspace, project = self._request_project(Path(directory))
            first = execute_study(project, "ohlcv-factor-quality")
            publish_run_report(
                project,
                "ohlcv-factor-quality",
                first.result["id"],
                analysis(first.result["id"]),
            )
            second = execute_study(project, "ohlcv-factor-quality")
            self.assertNotEqual(first.result["id"], second.result["id"])
            with self.assertRaises(AutoQuantValidationError) as superseded:
                publish_run_report(
                    project,
                    "ohlcv-factor-quality",
                    first.result["id"],
                    analysis(first.result["id"]),
                )
            self.assertIn(
                "report.run-superseded",
                {item.code for item in superseded.exception.issues},
            )

            factor = load_research_program(project)["lanes"][0]
            self.assertEqual(factor["latestRun"]["id"], second.result["id"])
            self.assertEqual(factor["phase"], "baseline-ready")
            self.assertEqual(factor["reports"][0]["leaderRunId"], first.result["id"])
            self.assertIn(
                "report.publish",
                {item["id"] for item in factor["commands"]},
            )
            status = load_dossier_status(project)
            self.assertFalse(status["ready"])
            self.assertEqual(
                status["nextAction"]["id"],
                "report.publish",
            )
            self.assertIn(second.result["id"], status["nextAction"]["argv"])

    def test_run_report_rejects_wrong_stale_unbound_and_non_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, project = self._request_project(root)
            run = execute_study(project, "ohlcv-factor-quality")

            with self.assertRaises(AutoQuantValidationError) as wrong_study:
                publish_run_report(
                    project,
                    "ohlcv-portfolio-quality",
                    run.result["id"],
                    analysis(run.result["id"]),
                )
            self.assertIn(
                "report.study-run",
                {item.code for item in wrong_study.exception.issues},
            )

            invalid_analysis = analysis(run.result["id"])
            invalid_analysis["findings"][0]["evidenceRefs"] = [
                {"kind": "experiment", "id": "exp-0001-unavailable", "artifactPath": None}
            ]
            with self.assertRaises(AutoQuantValidationError) as unknown:
                publish_run_report(
                    project,
                    "ohlcv-factor-quality",
                    run.result["id"],
                    invalid_analysis,
                )
            self.assertIn(
                "report.unknown-evidence",
                {item.code for item in unknown.exception.issues},
            )

            candidate = project.root_dir / "factors" / "candidate.py"
            candidate.write_text(candidate.read_text() + "\n# changed\n", encoding="utf-8")
            with self.assertRaises(AutoQuantValidationError) as stale:
                publish_run_report(
                    project,
                    "ohlcv-factor-quality",
                    run.result["id"],
                    analysis(run.result["id"]),
                )
            self.assertIn("report.run-stale", {item.code for item in stale.exception.issues})

            unbound = create_project(
                workspace.root_dir,
                "unbound-factor",
                template="ohlcv-factor-lab",
            )
            unbound_run = execute_study(unbound, "ohlcv-factor-quality")
            with self.assertRaises(AutoQuantValidationError) as no_request:
                publish_run_report(
                    unbound,
                    "ohlcv-factor-quality",
                    unbound_run.result["id"],
                    analysis(unbound_run.result["id"]),
                )
            self.assertIn(
                "report.request-required",
                {item.code for item in no_request.exception.issues},
            )

            outside = root / "outside-reports"
            outside.mkdir()
            (unbound.root_dir / "reports").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(AutoQuantValidationError) as symlinked:
                list_run_reports(unbound)
            self.assertIn(
                "path.symlink",
                {item.code for item in symlinked.exception.issues},
            )

    def test_template_route_catalog_prevents_single_lane_composition_guess(self) -> None:
        machine = run_cli("project", "templates", "--json")
        self.assertEqual(machine.returncode, 0, machine.stderr)
        data = json_output(machine)["data"]
        self.assertEqual(data["default"], "blank")
        self.assertEqual(
            data["recommendationRules"][1],
            {
                "when": "factor-to-portfolio-or-rl",
                "template": "ohlcv-research-desk",
                "reason": "Cross-lane admission and Dossier evidence require the coordinated desk.",
            },
        )
        routes = {item["id"]: item for item in data["routes"]}
        self.assertEqual(routes["ohlcv-research-desk"]["lanes"], ["factor", "portfolio", "rl"])
        self.assertIn(
            "Factor evidence must be established",
            routes["ohlcv-portfolio-lab"]["doesNotFit"][0],
        )
        human = run_cli("project", "templates")
        self.assertIn(
            "if Factor evidence must feed Portfolio or RL",
            human.stdout,
        )


if __name__ == "__main__":
    unittest.main()
