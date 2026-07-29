from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from autoquant.research import run_campaign
from autoquant.sessions import evaluate_experiment, start_session
from autoquant.studies import create_study, hash_json
from autoquant.studio import build_studio_snapshot, create_studio_server
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)
from tests.study_helpers import make_project, study_definition


SLOW_RESEARCHER = """\
import json
import os
import time
from pathlib import Path

brief = json.loads(input())
Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text("SCORE = 3.0\\n")
time.sleep(1)
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "slow-bounded-proposal",
    "hypothesis": "Expose one bounded in-progress turn.",
    "expected_effect": "Improve the synthetic score.",
}))
"""


class StudioObservationTests(unittest.TestCase):
    def _setup(self, directory: str):
        workspace, project = make_project(directory)
        create_study(project, study_definition())
        session = start_session(project, "factor-quality")
        candidate = session.worktree_project.root_dir / "factors/candidate.py"
        candidate.write_text("SCORE = 2.0\n")
        evaluate_experiment(project, session.manifest["id"], "Improve the factor")
        return workspace, project, session

    def _script(self, directory: str, source: str) -> str:
        path = Path(directory) / "studio-researcher.py"
        path.write_text(source, encoding="utf-8")
        return f"{shlex.quote(sys.executable)} {shlex.quote(str(path))}"

    def test_workspace_and_project_snapshots_share_verified_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, session = self._setup(directory)
            create_project(
                workspace.root_dir,
                "empty-lab",
                name="Empty Lab",
                description="A second bounded research Project",
            )

            snapshot = build_studio_snapshot(workspace.root_dir)
            self.assertEqual(snapshot["kind"], "autoquant-studio-snapshot")
            self.assertEqual(snapshot["source"]["scope"], "workspace")
            self.assertEqual(
                snapshot["source"]["workspace"]["projectsDir"],
                str(workspace.projects_dir),
            )
            self.assertEqual(
                snapshot["source"]["workspace"]["configurationSource"],
                "workspace-manifest",
            )
            self.assertEqual(
                snapshot["source"]["workspace"]["configurationPath"],
                str(workspace.root_dir / "autoquant-workspace.json"),
            )
            self.assertEqual(
                [item["id"] for item in snapshot["projects"]],
                ["empty-lab", "factor-project"],
            )
            observed = next(
                item for item in snapshot["projects"] if item["id"] == "factor-project"
            )
            self.assertTrue(observed["valid"])
            self.assertEqual(observed["counts"]["studies"], 1)
            self.assertEqual(observed["counts"]["runs"], 2)
            self.assertEqual(
                observed["agentWorkBrief"]["kind"],
                "autoquant-agent-work-brief",
            )
            self.assertEqual(
                len(observed["agentWorkBriefHash"]),
                64,
            )
            self.assertEqual(
                observed["agentWorkBriefHash"],
                hash_json(observed["agentWorkBrief"]),
            )
            self.assertEqual(
                observed["agentWorkBrief"]["filesystem"]["operatingRoot"],
                str(session.worktree_project.root_dir),
            )
            self.assertEqual(
                observed["agentWorkBrief"]["researchAgenda"]["status"],
                "unsupported-study",
            )
            self.assertEqual(
                observed["agentWorkBrief"]["researchAgenda"]["moves"],
                [],
            )
            self.assertEqual(observed["counts"]["activeSessions"], 1)
            self.assertEqual(observed["counts"]["dossiers"], 0)
            self.assertEqual(observed["counts"]["verdicts"]["KEEP"], 1)
            self.assertIsNone(observed["dossierStatus"])
            self.assertEqual(observed["dossiers"], [])
            self.assertEqual(observed["sessions"][0]["session"]["id"], session.manifest["id"])
            self.assertTrue(observed["sessions"][0]["authority"]["valid"])
            self.assertEqual(
                observed["sessions"][0]["selectionIntegrity"][
                    "selectionSplit"
                ],
                "unspecified",
            )
            self.assertIsNone(
                observed["sessions"][0]["selectionIntegrity"][
                    "externalHoldoutRequired"
                ]
            )
            self.assertEqual(
                observed["sessions"][0]["selectionIntegrity"][
                    "researchFamily"
                ]["uniqueSourceTrials"],
                2,
            )
            self.assertEqual(
                observed["sessions"][0]["selectionIntegrity"][
                    "selectionAdjustment"
                ]["status"],
                "unsupported",
            )
            self.assertEqual(
                observed["sessions"][0]["selectionIntegrity"][
                    "verdictAuthority"
                ],
                "diagnostic-only",
            )
            self.assertTrue(
                any(item["kind"] == "experiment" for item in observed["timeline"])
            )
            json.dumps(snapshot)

            direct = build_studio_snapshot(project.root_dir)
            self.assertEqual(direct["source"]["scope"], "project")
            self.assertIsNone(direct["source"]["workspace"])
            self.assertEqual([item["id"] for item in direct["projects"]], ["factor-project"])

            selected = build_studio_snapshot(
                workspace.root_dir,
                project_id="empty-lab",
            )
            self.assertEqual([item["id"] for item in selected["projects"]], ["empty-lab"])
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "cannot select inside a direct Project",
            ):
                build_studio_snapshot(project.root_dir, project_id="factor-project")

    def test_empty_and_partially_invalid_workspaces_remain_observable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "empty")
            empty = build_studio_snapshot(workspace.root_dir)
            self.assertTrue(empty["valid"])
            self.assertEqual(empty["projects"], [])

            (workspace.projects_dir / "broken-project").mkdir()
            partial = build_studio_snapshot(workspace.root_dir)
            self.assertFalse(partial["valid"])
            self.assertEqual(partial["projects"], [])
            self.assertEqual(
                partial["diagnostics"][0]["category"],
                "workspace",
            )

    def test_invalid_run_category_does_not_become_unverified_display_data(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project, _ = self._setup(directory)
            runs = sorted((project.root_dir / "runs").iterdir())
            result_path = runs[0] / "result.json"
            value = json.loads(result_path.read_text())
            value["summary"] = "tampered"
            result_path.write_text(json.dumps(value))

            snapshot = build_studio_snapshot(project.root_dir)
            observed = snapshot["projects"][0]
            self.assertFalse(snapshot["valid"])
            self.assertFalse(observed["valid"])
            self.assertEqual(observed["runs"], [])
            self.assertEqual(observed["sessions"], [])
            self.assertEqual(len(observed["studies"]), 1)
            self.assertIn(
                "runs",
                {item["category"] for item in observed["diagnostics"]},
            )

    def test_running_progress_is_mutable_then_replaced_by_terminal_campaign(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project, session = self._setup(directory)
            command = self._script(directory, SLOW_RESEARCHER)
            outcome: list[object] = []

            def execute() -> None:
                try:
                    outcome.append(
                        run_campaign(
                            project,
                            session.manifest["id"],
                            command,
                            max_turns=1,
                            max_wall_seconds=30,
                            turn_timeout_seconds=5,
                        )
                    )
                except Exception as error:
                    outcome.append(error)

            thread = threading.Thread(target=execute)
            thread.start()
            deadline = time.monotonic() + 5
            running = None
            while time.monotonic() < deadline:
                snapshot = build_studio_snapshot(workspace.root_dir)
                observed = next(
                    item
                    for item in snapshot["projects"]
                    if item["id"] == project.manifest.id
                )
                if observed["counts"]["runningCampaigns"] == 1:
                    candidate = observed["sessions"][0]["progress"][0]
                    if candidate["phase"] == "researcher":
                        running = candidate
                        break
                time.sleep(0.02)

            self.assertIsNotNone(running)
            self.assertTrue(running["mutable"])
            self.assertEqual(running["status"], "running")
            self.assertEqual(running["phase"], "researcher")
            self.assertEqual(running["turn"], 1)
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(outcome), 1)
            self.assertFalse(isinstance(outcome[0], Exception), outcome[0])

            terminal = build_studio_snapshot(workspace.root_dir)
            observed = next(
                item
                for item in terminal["projects"]
                if item["id"] == project.manifest.id
            )
            self.assertEqual(observed["counts"]["runningCampaigns"], 0)
            self.assertEqual(observed["counts"]["campaigns"], 1)
            self.assertEqual(
                observed["sessions"][0]["campaigns"][0]["status"],
                "budget_exhausted",
            )

    def test_http_server_exposes_only_fixed_read_only_routes_and_headers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, _, _ = self._setup(directory)
            server = create_studio_server(workspace.root_dir, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(f"{base}/api/v1/health", timeout=3) as response:
                    health = json.loads(response.read())
                    self.assertTrue(health["ok"])
                    self.assertEqual(health["mode"], "read-only")
                    self.assertEqual(response.headers["X-Frame-Options"], "DENY")
                    self.assertIn(
                        "default-src 'none'",
                        response.headers["Content-Security-Policy"],
                    )
                    self.assertIsNone(response.headers["Access-Control-Allow-Origin"])

                with urlopen(f"{base}/api/v1/snapshot", timeout=3) as response:
                    snapshot = json.loads(response.read())
                    self.assertEqual(snapshot["kind"], "autoquant-studio-snapshot")
                    self.assertEqual(response.headers["Cache-Control"], "no-store")

                with urlopen(f"{base}/", timeout=3) as response:
                    html = response.read().decode()
                    self.assertIn("Quant research desk", html)
                    self.assertIn("Research cockpit", html)
                    self.assertIn("Current research decision brief", html)
                    self.assertIn('id="decision-brief"', html)
                    self.assertIn('id="rail-workspace"', html)
                    self.assertIn('id="desk-nav"', html)
                    self.assertIn("Research handoff", html)
                    self.assertIn('id="handoff-board"', html)
                    self.assertIn('id="evidence-workbench"', html)
                    self.assertIn('id="evidence-lane-tabs"', html)
                    self.assertIn(
                        'id="portfolio-mechanical-decision"',
                        html,
                    )
                    self.assertIn(
                        'id="portfolio-sizing-anatomy"',
                        html,
                    )
                    self.assertIn(
                        'id="portfolio-diversification-stress"',
                        html,
                    )
                    self.assertIn(
                        'id="portfolio-strategy-viability"',
                        html,
                    )
                    self.assertIn(
                        'id="portfolio-signal-monetization"',
                        html,
                    )
                    self.assertIn(
                        'id="factor-qualification"',
                        html,
                    )
                    self.assertIn('id="factor-components"', html)
                    self.assertIn('id="research-agenda"', html)
                    self.assertIn('id="research-agenda-board"', html)
                    self.assertIn('id="external-holdout"', html)
                    self.assertIn('id="external-holdout-board"', html)
                    self.assertIn(
                        "Current mechanical decision",
                        html,
                    )
                    self.assertIn('id="inspector-toggle"', html)
                    self.assertIn('id="rl-opportunity"', html)
                    self.assertIn(
                        'id="rl-fusion-diagnosis"',
                        html,
                    )
                    self.assertIn('href="/assets/studio.css"', html)
                    self.assertNotIn("<script>", html)

                with urlopen(f"{base}/assets/studio.css", timeout=3) as response:
                    css = response.read().decode()
                    self.assertIn(".handoff-board", css)
                    self.assertIn(".decision-brief", css)
                    self.assertIn(".workspace-context", css)
                    self.assertIn(".desk-nav-button", css)
                    self.assertIn('[data-lane-count="1"]', css)
                    self.assertIn(".program-assessment", css)
                    self.assertIn(".admission-chip", css)
                    self.assertIn(".program-lane.admission-locked", css)
                    self.assertIn(".evidence-lane-tabs", css)
                    self.assertIn(".mandate-strip", css)
                    self.assertIn(".mechanical-chain", css)
                    self.assertIn(".mechanical-table", css)
                    self.assertIn(".trigger-condition", css)
                    self.assertIn(".report-decision-proof", css)
                    self.assertIn(".sizing-summary", css)
                    self.assertIn(".sizing-table", css)
                    self.assertIn(".diversification-summary", css)
                    self.assertIn(".diversification-ladder", css)
                    self.assertIn(".diversification-table", css)
                    self.assertIn(".viability-diagnosis", css)
                    self.assertIn(".viability-chain", css)
                    self.assertIn(".monetization-chain", css)
                    self.assertIn(".monetization-deltas", css)
                    self.assertIn(".factor-qualification-chain", css)
                    self.assertIn(
                        ".factor-qualification-diagnosis",
                        css,
                    )
                    self.assertIn(".factor-component-diagnosis", css)
                    self.assertIn(".factor-component-table", css)
                    self.assertIn(".factor-table-wrap", css)
                    self.assertIn("overflow-x: auto", css)
                    self.assertIn(".research-agenda-board", css)
                    self.assertIn(".holdout-board", css)
                    self.assertIn(".holdout-lane", css)
                    self.assertIn(".research-move-evidence", css)
                    self.assertIn(
                        "content: attr(data-label)",
                        css,
                    )
                    self.assertIn(
                        ".book-risk-scenario-table .factor-table td::before",
                        css,
                    )
                    self.assertIn(
                        ".book-risk-scenario-contribution-table .factor-table td::before",
                        css,
                    )
                    self.assertIn(".inspector-lane", css)
                    self.assertIn(".inspector-collapsed", css)
                    self.assertIn(".rl-opportunity-panel", css)
                    self.assertIn(".rl-incremental-panel", css)
                    self.assertIn(".rl-fusion-diagnosis", css)
                    self.assertIn(".rl-fusion-chain", css)
                    self.assertIn(".selection-risk", css)
                    self.assertIn(".command-button", css)
                    self.assertIn("@media (max-width: 680px)", css)
                    self.assertIn(":focus-visible", css)

                with urlopen(f"{base}/assets/studio.js", timeout=3) as response:
                    javascript = response.read().decode()
                    self.assertIn("programAssessment", javascript)
                    self.assertIn("laneAdmission", javascript)
                    self.assertIn("progressionGate", javascript)
                    self.assertIn("REQUIRED RESEARCH COMPLETE", javascript)
                    self.assertIn("researchDecisionBrief", javascript)
                    self.assertIn("project.agentWorkBrief", javascript)
                    self.assertIn("project.agentWorkBriefHash", javascript)
                    self.assertIn("ORIENTATION UNAVAILABLE", javascript)
                    self.assertNotIn("DO NOT PROMOTE ADAPTIVITY", javascript)
                    self.assertIn("projectFocusStudy", javascript)
                    self.assertIn("fixed event policy", javascript)
                    self.assertIn("DESCRIPTIVE EVIDENCE READY", javascript)
                    self.assertIn("renderDeskContext", javascript)
                    self.assertIn("updateDeskNavActive", javascript)
                    self.assertIn("validationBaselineAdvantage", javascript)
                    self.assertIn("renderFactorComponents", javascript)
                    self.assertIn("renderResearchAgenda", javascript)
                    self.assertIn(
                        "project.agentWorkBrief?.researchAgenda",
                        javascript,
                    )
                    self.assertIn(
                        "project.externalHoldout",
                        javascript,
                    )
                    self.assertIn(
                        "renderExternalHoldout(project)",
                        javascript,
                    )
                    self.assertIn(
                        "Sessions are disabled in this frozen external-audit Project.",
                        javascript,
                    )
                    self.assertIn(
                        "FROZEN SOURCE → LATER DATA → EXTERNAL AUDIT",
                        javascript,
                    )
                    self.assertIn(
                        "REQUEST → DATASET → FIXED RUN → REVIEW",
                        javascript,
                    )
                    self.assertIn(
                        "Copy Book Risk Explorer CLI",
                        javascript,
                    )
                    self.assertIn(
                        "no Session, optimization, order, or trading authority",
                        javascript,
                    )
                    self.assertIn(
                        'data-label="Validation raw IC"',
                        javascript,
                    )
                    self.assertIn("data-evidence-lane", javascript)
                    self.assertIn("mandateMarkup", javascript)
                    self.assertIn(
                        "renderPortfolioMechanicalDecision",
                        javascript,
                    )
                    self.assertIn(
                        "renderPortfolioSizingAnatomy",
                        javascript,
                    )
                    self.assertIn(
                        "renderPortfolioDiversificationStress",
                        javascript,
                    )
                    self.assertIn(
                        "25% / 50% / 100% ceiling-breach rate",
                        javascript,
                    )
                    self.assertIn(
                        "renderPortfolioStrategyViability",
                        javascript,
                    )
                    self.assertIn(
                        "renderPortfolioSignalMonetization",
                        javascript,
                    )
                    self.assertIn(
                        "renderFactorQualification",
                        javascript,
                    )
                    self.assertIn(
                        "First missing qualification layer",
                        javascript,
                    )
                    self.assertIn(
                        "Core could not verify the Agent Work Brief",
                        javascript,
                    )
                    self.assertIn(
                        "Frozen factor qualification",
                        javascript,
                    )
                    self.assertIn(
                        "TEST · VISIBLE AUDIT ONLY",
                        javascript,
                    )
                    self.assertIn(
                        "Diagonal risk is a sizing heuristic",
                        javascript,
                    )
                    self.assertIn(
                        "reportDecisionProof",
                        javascript,
                    )
                    self.assertIn(
                        "Frozen leader decision",
                        javascript,
                    )
                    self.assertIn(
                        "Current cross-sectional percentile buffers",
                        javascript,
                    )
                    self.assertIn("NO-TRADE HOLD", javascript)
                    self.assertIn("Authorized positions", javascript)
                    self.assertIn("syncEvidenceSelection", javascript)
                    self.assertIn("dossierState", javascript)
                    self.assertIn("PROJECT DOSSIER", javascript)
                    self.assertIn("OpenAlice return artifact", javascript)
                    self.assertIn("Copy completion CLI", javascript)
                    self.assertIn("no trading authority", javascript)
                    self.assertIn("browser-authored verdict", javascript)
                    self.assertIn("selectionRiskSection", javascript)
                    self.assertIn("renderRlOpportunity", javascript)
                    self.assertIn("renderRlIncremental", javascript)
                    self.assertIn(
                        "renderRlFusionDiagnosis",
                        javascript,
                    )
                    self.assertIn(
                        "Where adaptive value stops",
                        javascript,
                    )
                    self.assertIn(
                        "Frozen RL factor-fusion diagnosis",
                        javascript,
                    )
                    self.assertIn("Gross selection edge", javascript)
                    self.assertIn("factorOpportunity", javascript)
                    self.assertIn("contextualBaselines", javascript)
                    self.assertIn("train-only frozen learner", javascript)
                    self.assertIn("learningContract", javascript)
                    self.assertIn("SAME-PRETRADE · TRAIN ONLY", javascript)
                    self.assertIn("Family trials", javascript)
                    self.assertIn("Project-family trials", javascript)
                    self.assertIn("diagnostic only", javascript)
                    self.assertNotIn("RESEARCH CHAIN PASSES", javascript)

                request = Request(
                    f"{base}/api/v1/snapshot",
                    method="POST",
                    data=b"{}",
                )
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=3)
                self.assertEqual(raised.exception.code, 405)
                self.assertEqual(
                    json.loads(raised.exception.read())["error"]["code"],
                    "studio.read-only",
                )

                with self.assertRaises(HTTPError) as raised:
                    urlopen(f"{base}/files/research.md", timeout=3)
                self.assertEqual(raised.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_invalid_port_and_workspace_manifest_remain_core_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, _, _ = self._setup(directory)
            with self.assertRaisesRegex(AutoQuantValidationError, "port"):
                create_studio_server(workspace.root_dir, port=70000)

            manifest_path = workspace.root_dir / "autoquant-workspace.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["unknown"] = True
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AutoQuantValidationError, "Unknown field"):
                build_studio_snapshot(workspace.root_dir)

    def test_cli_serve_announces_a_live_local_read_only_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, _, _ = self._setup(directory)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "autoquant",
                    "studio",
                    "serve",
                    str(workspace.root_dir),
                    "--port",
                    "0",
                    "--no-open",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                announcement = process.stdout.readline().strip()
                self.assertTrue(
                    announcement.startswith("AutoQuant Studio: http://127.0.0.1:"),
                    process.stderr.read() if process.poll() is not None else announcement,
                )
                url = announcement.removeprefix("AutoQuant Studio: ")
                with urlopen(f"{url}/api/v1/health", timeout=3) as response:
                    self.assertEqual(json.loads(response.read())["mode"], "read-only")
            finally:
                process.terminate()
                process.wait(timeout=5)
                process.stdout.close()
                process.stderr.close()


if __name__ == "__main__":
    unittest.main()
