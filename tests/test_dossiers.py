from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

from autoquant.dossiers import (
    DOSSIER_ANALYSIS_JSON_SCHEMA,
    DOSSIER_RESULT_JSON_SCHEMA,
    DOSSIER_STATUS_JSON_SCHEMA,
    list_dossiers,
    load_dossier,
    load_dossier_status,
    publish_dossier,
)
from autoquant.intake import prepare_project_intake
from autoquant.reports import publish_report
from autoquant.research_program import load_research_program
from autoquant.runs import execute_study
from autoquant.sessions import complete_session, start_session
from autoquant.studio import build_studio_snapshot
from autoquant.templates import (
    OHLCV_STUDY_ID,
    PORTFOLIO_STUDY_ID,
    RL_STUDY_ID,
)
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)
from tests.intake_helpers import write_intake_inputs


PROJECT_DIR = Path(__file__).resolve().parents[1]


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "autoquant", *arguments],
        cwd=PROJECT_DIR,
        capture_output=True,
        check=False,
        text=True,
    )


def lane_analysis(lane_id: str, run_id: str) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-report-analysis",
        "title": f"{lane_id.title()} lane evidence",
        "executiveSummary": (
            f"The {lane_id} lane records bounded quantitative evidence for "
            "cross-lane synthesis."
        ),
        "findings": [
            {
                "id": f"{lane_id}-headline",
                "claim": f"The current {lane_id} leader is the verified lane evidence.",
                "confidence": "medium",
                "evidenceRefs": [
                    {
                        "kind": "run",
                        "id": run_id,
                        "artifactPath": None,
                    }
                ],
            }
        ],
        "recommendations": [],
        "limitations": ["This lane alone is not the Project conclusion."],
        "unresolvedQuestions": [],
    }


def dossier_analysis(reports: dict[str, str]) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-dossier-analysis",
        "title": "Cross-lane quantitative research dossier",
        "executiveSummary": (
            "Factor and implementation evidence are considered together; "
            "adaptive evidence is included only when current and compatible."
        ),
        "findings": [
            {
                "id": "factor-and-implementation",
                "claim": (
                    "The predictive and implementation lanes must be interpreted "
                    "as one evidence chain."
                ),
                "confidence": "medium",
                "evidenceRefs": [
                    {
                        "laneId": "factor",
                        "reportId": reports["factor"],
                        "findingId": "factor-headline",
                    },
                    {
                        "laneId": "portfolio",
                        "reportId": reports["portfolio"],
                        "findingId": "portfolio-headline",
                    },
                ],
            },
            *(
                [
                    {
                        "id": "adaptive-context",
                        "claim": "The governed RL lane is separate adaptive evidence.",
                        "confidence": "low",
                        "evidenceRefs": [
                            {
                                "laneId": "rl",
                                "reportId": reports["rl"],
                                "findingId": "rl-headline",
                            }
                        ],
                    }
                ]
                if "rl" in reports
                else []
            ),
        ],
        "recommendations": [
            {
                "action": "Use the dossier as decision support only.",
                "rationale": "Forward execution belongs to OpenAlice authority.",
                "conditions": ["Review every lane limitation."],
                "evidenceRefs": [
                    {
                        "laneId": "factor",
                        "reportId": reports["factor"],
                        "findingId": None,
                    },
                    {
                        "laneId": "portfolio",
                        "reportId": reports["portfolio"],
                        "findingId": None,
                    },
                ],
            }
        ],
        "limitations": ["The deterministic fixture is not live market evidence."],
        "unresolvedQuestions": ["What external holdout should be acquired next?"],
    }


class ProgramResearchDossierTests(unittest.TestCase):
    def _project(self, directory: str):
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
            "dossier-desk",
            name=prepared.request["title"],
            description=prepared.request["question"],
            template=prepared.template,
            template_intake=prepared,
        )
        for study_id in (OHLCV_STUDY_ID, PORTFOLIO_STUDY_ID, RL_STUDY_ID):
            execute_study(project, study_id)
        return project, prepared.request

    def _publish_lane(
        self,
        project,
        request: dict,
        lane_id: str,
        study_id: str,
    ):
        session = start_session(project, study_id, request=request)
        report = publish_report(
            project,
            session.manifest["id"],
            lane_analysis(lane_id, session.manifest["leader"]["runId"]),
        )
        return session, report

    def test_required_lane_reports_publish_immutable_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, request = self._project(directory)
            initial = load_dossier_status(project)
            assert initial is not None
            jsonschema.validate(initial, DOSSIER_STATUS_JSON_SCHEMA)
            self.assertFalse(initial["ready"])
            self.assertEqual(
                {blocker["code"] for blocker in initial["blockers"]},
                {"dossier.session-missing"},
            )

            factor_session, factor_report = self._publish_lane(
                project,
                request,
                "factor",
                OHLCV_STUDY_ID,
            )
            portfolio_session, portfolio_report = self._publish_lane(
                project,
                request,
                "portfolio",
                PORTFOLIO_STUDY_ID,
            )
            reports = {
                "factor": factor_report.report["id"],
                "portfolio": portfolio_report.report["id"],
            }
            portfolio_markdown = (
                portfolio_report.root_dir / "report.md"
            ).read_text(encoding="utf-8")
            self.assertIn("## Portfolio mandate", portfolio_markdown)
            self.assertIn("`long` / `long-cash`", portfolio_markdown)
            self.assertIn("`AAPL`, `MSFT`", portfolio_markdown)
            self.assertIn("`NVDA`, `QQQ`, `SPY`", portfolio_markdown)
            self.assertIn(
                "`trailing-covariance-volatility-ceiling-v1`",
                portfolio_markdown,
            )
            self.assertIn("Scale-up permitted: `False`", portfolio_markdown)
            self.assertIn(
                "`trailing-average-dollar-volume-capacity-v1`",
                portfolio_markdown,
            )
            self.assertIn(
                "Validation 1% participation capacity",
                portfolio_markdown,
            )
            active_program = load_research_program(project)
            assert active_program is not None
            self.assertEqual(
                active_program["recommendedLaneId"],
                "factor",
            )
            self.assertEqual(
                active_program["recommendedAction"]["id"],
                "session.complete",
            )
            complete_session(
                project,
                factor_session.manifest["id"],
                factor_report.report["id"],
            )
            complete_session(
                project,
                portfolio_session.manifest["id"],
                portfolio_report.report["id"],
            )
            completed_program = load_research_program(project)
            assert completed_program is not None
            self.assertEqual(
                completed_program["summary"]["activeSessions"],
                0,
            )
            self.assertEqual(completed_program["summary"]["conflicts"], 0)
            ready = load_dossier_status(project)
            assert ready is not None
            self.assertTrue(ready["ready"])
            self.assertEqual(ready["includedLaneIds"], ["factor", "portfolio"])
            self.assertEqual(
                ready["omittedOptionalLanes"][0]["id"],
                "rl",
            )
            self.assertEqual(ready["nextAction"]["id"], "dossier.publish")

            analysis = dossier_analysis(reports)
            jsonschema.validate(analysis, DOSSIER_ANALYSIS_JSON_SCHEMA)
            status_result = run_cli(
                "dossier",
                "status",
                str(project.root_dir),
                "--json",
            )
            self.assertEqual(status_result.returncode, 0, status_result.stderr)
            self.assertTrue(json.loads(status_result.stdout)["data"]["ready"])
            analysis_path = Path(directory) / "dossier-analysis.json"
            analysis_path.write_text(json.dumps(analysis), encoding="utf-8")
            published = run_cli(
                "dossier",
                "publish",
                str(project.root_dir),
                "--analysis",
                str(analysis_path),
                "--json",
            )
            self.assertEqual(published.returncode, 0, published.stderr)
            envelope = json.loads(published.stdout)
            self.assertEqual(envelope["command"], "dossier.publish")
            self.assertEqual(
                {item["kind"] for item in envelope["artifacts"]},
                {"research-dossier", "research-dossier-markdown"},
            )
            dossier = load_dossier(
                project,
                envelope["data"]["dossier"]["id"],
            )
            jsonschema.validate(dossier.dossier, DOSSIER_RESULT_JSON_SCHEMA)
            self.assertEqual(dossier.dossier["tradingAuthority"], "none")
            self.assertEqual(
                [lane["id"] for lane in dossier.dossier["evidence"]["lanes"]],
                ["factor", "portfolio"],
            )
            self.assertEqual(
                dossier.dossier["evidence"]["omittedOptionalLanes"][0]["id"],
                "rl",
            )
            markdown = (dossier.root_dir / "dossier.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Program evidence", markdown)
            self.assertIn("## Portfolio mandate", markdown)
            self.assertIn("`long` / `long-cash`", markdown)
            self.assertIn(
                "`trailing-covariance-volatility-ceiling-v1`",
                markdown,
            )
            self.assertIn("## Liquidity capacity", markdown)
            self.assertIn(
                "OHLCV participation envelope only",
                markdown,
            )
            self.assertIn("`AAPL`, `MSFT`", markdown)
            self.assertIn("`NVDA`, `QQQ`, `SPY`", markdown)
            self.assertIn("Omitted optional lanes", markdown)
            self.assertIn("Research family:", markdown)
            self.assertIn("Selection adjustment:", markdown)
            self.assertIn("Selection interpretation:", markdown)
            self.assertIn("OpenAlice Inbox", markdown)
            self.assertEqual(
                [item.id for item in list_dossiers(project)],
                [dossier.dossier["id"]],
            )
            listed = run_cli(
                "dossier",
                "list",
                str(project.root_dir),
                "--json",
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(
                json.loads(listed.stdout)["data"]["dossiers"][0]["id"],
                dossier.dossier["id"],
            )
            shown = run_cli(
                "dossier",
                "show",
                str(project.root_dir),
                "--dossier",
                dossier.dossier["id"],
                "--json",
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertEqual(
                json.loads(shown.stdout)["data"]["dossier"]["id"],
                dossier.dossier["id"],
            )

            after = load_dossier_status(project)
            assert after is not None
            self.assertTrue(after["latestDossier"]["current"])
            self.assertEqual(after["nextAction"]["id"], "dossier.show")

            completed_status = load_dossier_status(project)
            assert completed_status is not None
            self.assertTrue(completed_status["latestDossier"]["current"])

            studio = build_studio_snapshot(project.root_dir)["projects"][0]
            self.assertEqual(studio["counts"]["dossiers"], 1)
            self.assertEqual(
                studio["dossierStatus"]["latestDossier"]["id"],
                dossier.dossier["id"],
            )
            self.assertTrue(studio["dossierStatus"]["latestDossier"]["current"])
            self.assertEqual(studio["dossiers"][0]["id"], dossier.dossier["id"])
            self.assertIn(
                dossier.dossier["id"],
                {
                    event["id"]
                    for event in studio["timeline"]
                    if event["kind"] == "dossier"
                },
            )
            self.assertIn(
                "dossier.show",
                {command["id"] for command in studio["commands"]},
            )

    def test_rl_report_is_included_and_analysis_must_cover_every_lane(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, request = self._project(directory)
            reports: dict[str, str] = {}
            for lane_id, study_id in (
                ("factor", OHLCV_STUDY_ID),
                ("portfolio", PORTFOLIO_STUDY_ID),
                ("rl", RL_STUDY_ID),
            ):
                _, report = self._publish_lane(
                    project,
                    request,
                    lane_id,
                    study_id,
                )
                reports[lane_id] = report.report["id"]
            status = load_dossier_status(project)
            assert status is not None
            self.assertTrue(status["ready"])
            self.assertEqual(
                status["includedLaneIds"],
                ["factor", "portfolio", "rl"],
            )
            self.assertEqual(status["omittedOptionalLanes"], [])
            status_by_lane = {
                lane["id"]: lane for lane in status["lanes"]
            }
            self.assertEqual(
                status_by_lane["portfolio"]["leaderRun"][
                    "portfolioMandateId"
                ],
                status_by_lane["rl"]["leaderRun"]["portfolioMandateId"],
            )

            incomplete = dossier_analysis(reports)
            incomplete["findings"] = incomplete["findings"][:1]
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "must reference every included lane",
            ):
                publish_dossier(project, incomplete)

            wrong = dossier_analysis(reports)
            wrong["findings"][0]["evidenceRefs"][0]["findingId"] = "invented"
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Unknown finding",
            ):
                publish_dossier(project, wrong)

            dossier = publish_dossier(project, dossier_analysis(reports))
            loaded = load_dossier(project, dossier.dossier["id"])
            self.assertEqual(
                loaded.dossier["evidenceHash"],
                dossier.dossier["evidenceHash"],
            )
            markdown = (loaded.root_dir / "dossier.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(markdown.count("## Portfolio mandate"), 1)
            self.assertIn("`long` / `long-cash`", markdown)

            # A later lane Report does not rewrite or invalidate the point-in-time
            # Dossier evidence prefix.
            rl_session_id = dossier.dossier["evidence"]["lanes"][2]["report"][
                "sessionId"
            ]
            publish_report(
                project,
                rl_session_id,
                lane_analysis(
                    "rl",
                    dossier.dossier["evidence"]["lanes"][2]["leaderRun"]["id"],
                ),
            )
            self.assertEqual(
                load_dossier(project, dossier.dossier["id"]).dossier["id"],
                dossier.dossier["id"],
            )

            (dossier.root_dir / "dossier.md").write_text(
                "tampered\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "files changed",
            ):
                load_dossier(project, dossier.dossier["id"])


if __name__ == "__main__":
    unittest.main()
