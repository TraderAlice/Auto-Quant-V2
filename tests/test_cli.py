from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autoquant.sessions import list_experiments, start_session
from autoquant.studies import create_study
from tests.intake_helpers import write_intake_inputs
from tests.study_helpers import SUCCESS_JUDGE, make_project, study_definition


PROJECT_DIR = Path(__file__).resolve().parents[1]


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "autoquant", *arguments],
        cwd=PROJECT_DIR,
        capture_output=True,
        check=False,
        text=True,
    )


def json_output(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


class AgentCliTests(unittest.TestCase):
    def test_cli_orients_fixed_template_from_bound_project_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "allocation-lab",
                "--template",
                "ohlcv-allocation-lab",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            project = Path(json_output(created)["data"]["projectDir"])

            oriented = run_cli("orient", str(project), "--json")

            self.assertEqual(oriented.returncode, 0, oriented.stderr)
            question = json_output(oriented)["data"]["question"]
            self.assertEqual(question["origin"], "project-request")
            self.assertEqual(
                question["text"],
                "Does fixed ERC improve on a fixed 60/40 reference?",
            )
            self.assertEqual(
                question["sourcePath"],
                str(project / "request.json"),
            )

    def test_cli_constructs_and_runs_ohlcv_factor_lab_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "ohlcv-lab",
                "--template",
                "ohlcv-factor-lab",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json_output(created)
            self.assertEqual(envelope["data"]["template"], "ohlcv-factor-lab")
            self.assertEqual(
                envelope["data"]["researchBriefPath"],
                str(Path(envelope["data"]["projectDir"]) / "research.md"),
            )
            self.assertEqual(
                [item["kind"] for item in envelope["artifacts"][:2]],
                ["project", "research-brief"],
            )
            self.assertEqual(
                envelope["data"]["frameworkNeedsPath"],
                str(
                    Path(envelope["data"]["projectDir"])
                    / "framework-needs.md"
                ),
            )
            self.assertEqual(
                [action["id"] for action in envelope["nextActions"]],
                ["study.inspect", "run.execute"],
            )
            project = Path(envelope["data"]["projectDir"])
            research_path = project / "research.md"
            research_path.write_text(
                "# OHLCV Lab\n\n"
                "## Research question\n\n"
                "Does the shipped factor survive the fixed validation Study?\n",
                encoding="utf-8",
            )
            study = json.loads(
                (
                    project
                    / "studies"
                    / "ohlcv-factor-quality"
                    / "study.json"
                ).read_text()
            )
            self.assertEqual(study["dataset"]["paths"], ["ohlcv/**"])

            oriented = run_cli(
                "orient",
                str(project),
                "--json",
            )
            self.assertEqual(oriented.returncode, 0, oriented.stderr)
            orientation = json_output(oriented)
            self.assertEqual(orientation["command"], "orient")
            self.assertEqual(
                orientation["data"]["kind"],
                "autoquant-agent-work-brief",
            )
            self.assertEqual(
                orientation["data"]["question"],
                {
                    "title": "ohlcv-lab",
                    "text": (
                        "Does the shipped factor survive the fixed validation "
                        "Study?"
                    ),
                    "origin": "project-research-brief",
                    "sourcePath": str(research_path),
                    "requestPath": None,
                },
            )
            self.assertEqual(
                orientation["data"]["primaryAction"]["id"],
                "run.execute",
            )
            self.assertFalse(
                orientation["data"]["filesystem"]["writable"]
            )
            self.assertEqual(
                [item["id"] for item in orientation["nextActions"]],
                ["run.execute"],
            )

            executed = run_cli(
                "run",
                "execute",
                str(project),
                "--study",
                "ohlcv-factor-quality",
                "--json",
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            execution = json_output(executed)
            result = execution["data"]
            self.assertEqual(result["status"], "succeeded")
            self.assertIn("sourceHashes", result["dataset"])

            oriented_with_evidence = run_cli(
                "orient",
                str(project),
                "--json",
            )
            self.assertEqual(
                oriented_with_evidence.returncode,
                0,
                oriented_with_evidence.stderr,
            )
            evidence_brief = json_output(oriented_with_evidence)["data"]
            self.assertEqual(
                evidence_brief["researchAgenda"]["laneId"],
                "factor",
            )
            self.assertIn(
                evidence_brief["researchAgenda"]["status"],
                {"available", "no-further-in-sample-tuning"},
            )
            self.assertGreaterEqual(
                len(evidence_brief["researchAgenda"]["moves"]),
                1,
            )

            human_orientation = run_cli("orient", str(project))
            self.assertEqual(
                human_orientation.returncode,
                0,
                human_orientation.stderr,
            )
            self.assertIn(
                "Research agenda:",
                human_orientation.stdout,
            )
            self.assertIn("Experiment 1:", human_orientation.stdout)
            self.assertIn("Hypothesis:", human_orientation.stdout)
            self.assertIn(
                "run.factor",
                [item["id"] for item in execution["nextActions"]],
            )
            diagnostics = run_cli(
                "run",
                "factor",
                str(project),
                "--run",
                result["id"],
                "--points",
                "48",
                "--json",
            )
            self.assertEqual(diagnostics.returncode, 0, diagnostics.stderr)
            projected = json_output(diagnostics)
            self.assertEqual(projected["command"], "run.factor")
            self.assertEqual(
                projected["data"]["kind"],
                "autoquant-factor-diagnostics",
            )
            self.assertEqual(projected["data"]["icPath"]["sampledRows"], 48)
            self.assertEqual(
                {item["kind"] for item in projected["artifacts"]},
                {
                    "factor-report",
                    "factor-daily",
                    "factor-quantiles",
                    "factor-availability",
                    "factor-qualification",
                    "factor-components",
                },
            )
            self.assertTrue(
                projected["data"]["factorComponents"]["available"]
            )

    def test_orient_reenters_exact_session_worktree_without_copying_data(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "worktree-reentry",
                "--template",
                "ohlcv-factor-lab",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            project = Path(json_output(created)["data"]["projectDir"])
            baseline = run_cli(
                "run",
                "execute",
                str(project),
                "--study",
                "ohlcv-factor-quality",
                "--json",
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            started = run_cli(
                "session",
                "start",
                str(project),
                "--study",
                "ohlcv-factor-quality",
                "--json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            worktree = Path(json_output(started)["data"]["worktree"])
            self.assertFalse((worktree / "data" / "ohlcv").exists())

            canonical = run_cli("orient", str(project), "--json")
            reentered = run_cli("orient", str(worktree), "--json")

            self.assertEqual(canonical.returncode, 0, canonical.stderr)
            self.assertEqual(reentered.returncode, 0, reentered.stderr)
            canonical_json = json_output(canonical)
            reentered_json = json_output(reentered)
            self.assertEqual(reentered_json["data"], canonical_json["data"])
            self.assertEqual(
                reentered_json["context"],
                canonical_json["context"],
            )
            self.assertEqual(
                reentered_json["nextActions"],
                canonical_json["nextActions"],
            )
            canonical_human = run_cli("orient", str(project))
            reentered_human = run_cli("orient", str(worktree))
            self.assertEqual(
                reentered_human.stdout,
                canonical_human.stdout,
            )
            self.assertIn(
                f"Project root: {project.resolve()}",
                reentered_human.stdout,
            )
            self.assertIn(
                f"Operating root: {worktree.resolve()}",
                reentered_human.stdout,
            )
            studio = run_cli(
                "studio",
                "snapshot",
                str(project),
                "--json",
            )
            self.assertEqual(studio.returncode, 0, studio.stderr)
            self.assertEqual(
                json_output(studio)["data"]["projects"][0]["agentWorkBrief"],
                canonical_json["data"],
            )

            direct_mutation = run_cli(
                "run",
                "execute",
                str(worktree),
                "--study",
                "ohlcv-factor-quality",
                "--json",
            )
            self.assertNotEqual(direct_mutation.returncode, 0)
            self.assertEqual(
                json_output(direct_mutation)["error"]["issues"][0]["code"],
                "dataset.directory",
            )

    def test_cli_constructs_portfolio_lab_with_correct_next_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "portfolio-lab",
                "--template",
                "ohlcv-portfolio-lab",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json_output(created)
            self.assertEqual(envelope["data"]["template"], "ohlcv-portfolio-lab")
            self.assertTrue(
                all(
                    "ohlcv-portfolio-quality" in action["argv"]
                    for action in envelope["nextActions"]
                )
            )
            project = Path(envelope["data"]["projectDir"])
            executed = run_cli(
                "run",
                "execute",
                str(project),
                "--study",
                "ohlcv-portfolio-quality",
                "--json",
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            run_id = json_output(executed)["data"]["id"]
            diagnostics = run_cli(
                "run",
                "portfolio",
                str(project),
                "--run",
                run_id,
                "--points",
                "48",
                "--json",
            )
            self.assertEqual(diagnostics.returncode, 0, diagnostics.stderr)
            projected = json_output(diagnostics)
            self.assertEqual(projected["command"], "run.portfolio")
            self.assertEqual(
                projected["data"]["kind"],
                "autoquant-portfolio-diagnostics",
            )
            self.assertEqual(projected["data"]["path"]["sampledRows"], 48)
            self.assertEqual(
                projected["data"]["mechanicalDecision"][
                    "tradingAuthority"
                ],
                "none",
            )
            self.assertEqual(
                projected["data"]["mechanicalDecision"]["timestamp"],
                projected["data"]["currentBook"]["timestamp"],
            )
            self.assertEqual(
                len(
                    projected["data"]["mechanicalDecision"][
                        "positions"
                    ]
                ),
                len(projected["data"]["universe"]),
            )
            self.assertTrue(projected["data"]["riskGovernor"]["available"])
            self.assertTrue(
                projected["data"]["executedBookRisk"]["available"]
            )
            self.assertEqual(
                projected["data"]["diversificationStress"]["authority"],
                "context-only",
            )
            self.assertEqual(
                projected["data"]["diversificationStress"]["shock"][
                    "method"
                ],
                (
                    "observed-to-perfect-position-aligned-"
                    "covariance-blend-ladder"
                ),
            )
            self.assertEqual(
                projected["data"]["executedBookRisk"]["validation"][
                    "executedBreachDates"
                ],
                0,
            )
            self.assertTrue(
                projected["data"]["liquidityCapacity"]["available"]
            )
            self.assertEqual(
                projected["data"]["liquidityCapacity"][
                    "selectionAuthority"
                ],
                "context-only",
            )
            self.assertEqual(
                projected["data"]["mandate"]["riskPolicy"]["method"],
                "trailing-covariance-volatility-ceiling-v1",
            )
            self.assertTrue(
                projected["data"]["positionLifecycle"]["available"]
            )
            self.assertTrue(
                projected["data"]["positionLifecycle"]["validation"][
                    "reconciliation"
                ]["passed"]
            )
            self.assertTrue(
                projected["data"]["parameterNeighborhood"]["available"]
            )
            self.assertEqual(
                {item["kind"] for item in projected["artifacts"]},
                {
                    "portfolio-report",
                    "portfolio-daily",
                    "portfolio-targets",
                    "portfolio-weights",
                    "portfolio-decisions",
                    "portfolio-position-episodes",
                    "portfolio-parameter-neighborhood",
                },
            )
            human = run_cli(
                "run",
                "portfolio",
                str(project),
                "--run",
                run_id,
                "--points",
                "48",
            )
            self.assertEqual(human.returncode, 0, human.stderr)
            self.assertIn(
                "Validation 1% participation capacity p10",
                human.stdout,
            )
            self.assertIn("Validation executed-book risk", human.stdout)
            self.assertIn("Validation position lifecycle", human.stdout)
            self.assertIn(
                "Validation parameter neighborhood",
                human.stdout,
            )
            self.assertIn("Executed book:", human.stdout)
            self.assertIn("contextual only", human.stdout)

    def test_cli_constructs_rl_factor_lab_with_correct_next_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "rl-factor-lab",
                "--template",
                "ohlcv-rl-factor-lab",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json_output(created)
            self.assertEqual(envelope["data"]["template"], "ohlcv-rl-factor-lab")
            self.assertTrue(
                all(
                    "ohlcv-rl-factor-policy" in action["argv"]
                    for action in envelope["nextActions"]
                )
            )

    def test_cli_constructs_and_projects_multi_study_research_desk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "research-desk",
                "--template",
                "ohlcv-research-desk",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json_output(created)
            self.assertEqual(
                [item["kind"] for item in envelope["artifacts"]],
                [
                    "project",
                    "research-brief",
                    "framework-needs",
                    "research-program",
                ],
            )
            self.assertEqual(
                [action["id"] for action in envelope["nextActions"]],
                ["project.program", "run.execute"],
            )
            projected = run_cli(
                "project",
                "program",
                envelope["data"]["projectDir"],
                "--json",
            )
            self.assertEqual(projected.returncode, 0, projected.stderr)
            status = json_output(projected)
            self.assertEqual(status["command"], "project.program")
            self.assertEqual(
                status["data"]["kind"],
                "autoquant-research-program-status",
            )
            self.assertEqual(
                [lane["id"] for lane in status["data"]["lanes"]],
                ["factor", "portfolio", "rl"],
            )
            self.assertEqual(
                status["data"]["progression"]["stage"],
                "factor-evidence-required",
            )
            self.assertEqual(
                [
                    gate["status"]
                    for gate in status["data"]["progression"]["gates"]
                ],
                ["waiting-current-evidence", "blocked-prerequisite"],
            )
            self.assertEqual(status["nextActions"][0]["id"], "run.execute")

    def test_capabilities_describe_every_public_command(self) -> None:
        result = run_cli("capabilities", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json_output(result)

        self.assertEqual(envelope["schemaVersion"], 1)
        self.assertTrue(envelope["ok"])
        commands = envelope["data"]["commands"]
        self.assertEqual(
            [command["id"] for command in commands],
            [
                "capabilities",
                "schema",
                "orient",
                "workspace.init",
                "project.create",
                "project.intake",
                "project.list",
                "project.default",
                "project.program",
                "validate",
                "inspect",
                "study.create",
                "study.list",
                "study.inspect",
                "run.execute",
                "run.list",
                "run.show",
                "run.factor",
                "run.portfolio",
                "run.book-risk",
                "run.event-study",
                "run.allocation",
                "run.rl",
                "session.start",
                "session.list",
                "session.show",
                "session.check",
                "session.compare",
                "session.promote",
                "session.complete",
                "experiment.evaluate",
                "experiment.list",
                "experiment.show",
                "research.run",
                "research.list",
                "research.show",
                "report.publish",
                "report.list",
                "report.show",
                "dossier.status",
                "dossier.publish",
                "dossier.list",
                "dossier.show",
                "holdout.bind",
                "holdout.status",
                "holdout.run",
                "holdout.show",
                "studio.snapshot",
                "studio.serve",
            ],
        )
        for command in commands:
            self.assertEqual(
                command["supportsJson"],
                command["id"] != "studio.serve",
            )
            self.assertIn(
                command["effect"],
                {
                    "read-only",
                    "creates-artifact",
                    "mutates-workspace",
                    "mutates-project",
                    "long-running-server",
                },
            )
            self.assertEqual(command["exitCodes"]["success"], 0)
            self.assertEqual(command["exitCodes"]["usage"], 2)
        project_create = next(
            command for command in commands if command["id"] == "project.create"
        )
        template_argument = next(
            argument
            for argument in project_create["arguments"]
            if argument["name"] == "template"
        )
        self.assertEqual(
            template_argument["choices"],
            [
                "blank",
                "ohlcv-factor-lab",
                "ohlcv-portfolio-lab",
                "ohlcv-rl-factor-lab",
                "ohlcv-book-risk-lab",
                "ohlcv-event-study-lab",
                "ohlcv-allocation-lab",
                "ohlcv-research-desk",
            ],
        )
        project_intake = next(
            command for command in commands if command["id"] == "project.intake"
        )
        self.assertEqual(project_intake["effect"], "creates-artifact")
        self.assertEqual(
            next(
                argument
                for argument in project_intake["arguments"]
                if argument["name"] == "template"
            )["choices"],
            [
                "ohlcv-factor-lab",
                "ohlcv-portfolio-lab",
                "ohlcv-rl-factor-lab",
                "ohlcv-book-risk-lab",
                "ohlcv-event-study-lab",
                "ohlcv-allocation-lab",
                "ohlcv-research-desk",
            ],
        )
        schema = next(command for command in commands if command["id"] == "schema")
        self.assertEqual(
            schema["arguments"][0]["choices"],
            [
                "workspace",
                "project",
                "agent-work-brief",
                "research-agenda",
                "holdout-binding",
                "holdout-result",
                "holdout-status",
                "study",
                "judge-output",
                "run-result",
                "factor-diagnostics",
                "factor-claim",
                "event-study-policy",
                "event-study-diagnostics",
                "allocation-policy",
                "allocation-diagnostics",
                "book-risk-diagnostics",
                "portfolio-diagnostics",
                "research-program-status",
                "rl-policy-diagnostics",
                "session-decision-matrix",
                "session",
                "session-completion",
                "candidate-preflight",
                "candidate-check-output",
                "candidate-check-result",
                "portfolio-mandate",
                "research-horizon",
                "experiment",
                "researcher-response",
                "campaign-result",
                "campaign-progress",
                "research-request",
                "ohlcv-dataset-package",
                "report-analysis",
                "dossier-analysis",
                "dossier-result",
                "dossier-status",
                "studio-snapshot",
            ],
        )
        agenda_schema = run_cli("schema", "research-agenda", "--json")
        self.assertEqual(agenda_schema.returncode, 0, agenda_schema.stderr)
        self.assertEqual(
            json_output(agenda_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-evidence-driven-research-agenda",
        )
        holdout_schema = run_cli("schema", "holdout-result", "--json")
        self.assertEqual(holdout_schema.returncode, 0, holdout_schema.stderr)
        self.assertEqual(
            json_output(holdout_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-frozen-holdout-result",
        )
        response_schema = run_cli("schema", "researcher-response", "--json")
        self.assertEqual(response_schema.returncode, 0, response_schema.stderr)
        self.assertEqual(
            json_output(response_schema)["data"]["schema"]["oneOf"][0][
                "properties"
            ]["action"]["const"],
            "propose",
        )
        campaign_schema = run_cli("schema", "campaign-result", "--json")
        self.assertEqual(campaign_schema.returncode, 0, campaign_schema.stderr)
        self.assertIn(
            "budget",
            json_output(campaign_schema)["data"]["schema"]["properties"],
        )
        progress_schema = run_cli("schema", "campaign-progress", "--json")
        self.assertEqual(progress_schema.returncode, 0, progress_schema.stderr)
        self.assertEqual(
            json_output(progress_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "campaign-progress",
        )
        request_schema = run_cli("schema", "research-request", "--json")
        self.assertEqual(request_schema.returncode, 0, request_schema.stderr)
        self.assertEqual(
            json_output(request_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-research-request",
        )
        report_schema = run_cli("schema", "report-analysis", "--json")
        self.assertEqual(report_schema.returncode, 0, report_schema.stderr)
        self.assertEqual(
            json_output(report_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-research-report-analysis",
        )
        dossier_schema = run_cli("schema", "dossier-analysis", "--json")
        self.assertEqual(dossier_schema.returncode, 0, dossier_schema.stderr)
        self.assertEqual(
            json_output(dossier_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-research-dossier-analysis",
        )
        studio_schema = run_cli("schema", "studio-snapshot", "--json")
        self.assertEqual(studio_schema.returncode, 0, studio_schema.stderr)
        self.assertEqual(
            json_output(studio_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-studio-snapshot",
        )
        dataset_schema = run_cli("schema", "ohlcv-dataset-package", "--json")
        self.assertEqual(dataset_schema.returncode, 0, dataset_schema.stderr)
        self.assertEqual(
            json_output(dataset_schema)["data"]["schema"]["properties"][
                "frequency"
            ]["const"],
            "1d",
        )
        self.assertEqual(
            json_output(dataset_schema)["data"]["schema"]["properties"][
                "schemaVersion"
            ]["enum"],
            [1, 2, 3, 4, 5],
        )
        portfolio_schema = run_cli(
            "schema",
            "portfolio-diagnostics",
            "--json",
        )
        self.assertEqual(
            portfolio_schema.returncode,
            0,
            portfolio_schema.stderr,
        )
        self.assertEqual(
            json_output(
                run_cli("schema", "factor-diagnostics", "--json")
            )["data"]["schema"]["properties"]["kind"]["const"],
            "autoquant-factor-diagnostics",
        )
        self.assertEqual(
            json_output(portfolio_schema)["data"]["schema"]["properties"][
                "kind"
            ]["const"],
            "autoquant-portfolio-diagnostics",
        )
        self.assertEqual(
            json_output(
                run_cli("schema", "rl-policy-diagnostics", "--json")
            )["data"]["schema"]["properties"]["kind"]["const"],
            "autoquant-rl-policy-diagnostics",
        )
        comparison_schema = run_cli(
            "schema",
            "session-decision-matrix",
            "--json",
        )
        self.assertEqual(
            comparison_schema.returncode,
            0,
            comparison_schema.stderr,
        )
        self.assertEqual(
            json_output(comparison_schema)["data"]["schema"]["properties"][
                "kind"
            ]["const"],
            "autoquant-session-decision-matrix",
        )
        completion_schema = run_cli(
            "schema",
            "session-completion",
            "--json",
        )
        self.assertEqual(
            completion_schema.returncode,
            0,
            completion_schema.stderr,
        )
        self.assertEqual(
            json_output(completion_schema)["data"]["schema"]["properties"][
                "kind"
            ]["const"],
            "autoquant-session-completion",
        )
        mandate_schema = run_cli(
            "schema",
            "portfolio-mandate",
            "--json",
        )
        self.assertEqual(
            mandate_schema.returncode,
            0,
            mandate_schema.stderr,
        )
        self.assertEqual(
            json_output(mandate_schema)["data"]["schema"]["properties"][
                "kind"
            ]["const"],
            "autoquant-portfolio-mandate",
        )
        horizon_schema = run_cli(
            "schema",
            "research-horizon",
            "--json",
        )
        self.assertEqual(
            horizon_schema.returncode,
            0,
            horizon_schema.stderr,
        )
        self.assertEqual(
            json_output(horizon_schema)["data"]["schema"]["properties"][
                "kind"
            ]["const"],
            "autoquant-research-horizon",
        )

    def test_cli_intakes_request_and_dataset_into_ready_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = root / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )

            created = run_cli(
                "project",
                "intake",
                str(workspace),
                "real-portfolio",
                "--request",
                str(request_path),
                "--dataset",
                str(package_path),
                "--template",
                "ohlcv-portfolio-lab",
                "--json",
            )

            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json_output(created)
            self.assertEqual(envelope["command"], "project.intake")
            self.assertEqual(
                envelope["data"]["intake"]["manifest"]["status"],
                "ready-for-session",
            )
            self.assertEqual(
                envelope["data"]["intake"]["dataset"]["requestedAssets"],
                ["AAPL", "MSFT"],
            )
            self.assertEqual(
                [item["kind"] for item in envelope["artifacts"]],
                [
                    "project",
                    "research-brief",
                    "framework-needs",
                    "research-request",
                    "dataset-snapshot",
                    "project-intake",
                ],
            )
            self.assertEqual(
                [item["id"] for item in envelope["nextActions"]],
                ["study.inspect", "run.execute", "session.start"],
            )
            self.assertIn(
                str(Path(envelope["data"]["projectDir"]) / "request.json"),
                envelope["nextActions"][-1]["argv"],
            )

    def test_cli_intake_defaults_to_multi_study_research_desk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = root / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "intake",
                str(workspace),
                "delegated-desk",
                "--request",
                str(request_path),
                "--dataset",
                str(package_path),
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json_output(created)
            self.assertEqual(
                envelope["data"]["intake"]["manifest"]["template"],
                "ohlcv-research-desk",
            )
            self.assertEqual(
                [item["kind"] for item in envelope["artifacts"]],
                [
                    "project",
                    "research-brief",
                    "framework-needs",
                    "research-request",
                    "dataset-snapshot",
                    "project-intake",
                    "research-program",
                ],
            )
            self.assertEqual(
                [action["id"] for action in envelope["nextActions"]],
                ["project.program", "run.execute"],
            )

    def test_json_cli_completes_a_two_project_workspace_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            initialized = run_cli(
                "workspace",
                "init",
                str(workspace),
                "--name",
                "Quant Desk",
                "--json",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            initialized_json = json_output(initialized)
            self.assertEqual(initialized_json["context"]["scope"], "workspace")
            self.assertEqual(initialized_json["artifacts"][0]["kind"], "workspace")
            self.assertEqual(
                initialized_json["nextActions"][0]["id"],
                "project.create",
            )

            for project_id in ("factor-lab", "ml-lab"):
                created = run_cli(
                    "project",
                    "create",
                    str(workspace),
                    project_id,
                    "--name",
                    project_id.replace("-", " ").title(),
                    "--json",
                )
                self.assertEqual(created.returncode, 0, created.stderr)
                created_json = json_output(created)
                self.assertEqual(created_json["context"]["scope"], "project")
                self.assertEqual(
                    created_json["context"]["project"]["id"],
                    project_id,
                )
                self.assertEqual(created_json["artifacts"][0]["kind"], "project")
                self.assertEqual(
                    created_json["artifacts"][1]["kind"],
                    "research-brief",
                )
                self.assertEqual(
                    created_json["artifacts"][2]["kind"],
                    "framework-needs",
                )
                self.assertEqual(
                    created_json["data"]["researchBriefPath"],
                    str(
                        Path(created_json["data"]["projectDir"])
                        / "research.md"
                    ),
                )
                self.assertEqual(
                    created_json["data"]["frameworkNeedsPath"],
                    str(
                        Path(created_json["data"]["projectDir"])
                        / "framework-needs.md"
                    ),
                )
                self.assertEqual(
                    [action["id"] for action in created_json["nextActions"]],
                    ["validate", "inspect"],
                )

            listed = run_cli("project", "list", str(workspace), "--json")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            projects = json_output(listed)["data"]["projects"]
            self.assertEqual(
                [project["id"] for project in projects],
                ["factor-lab", "ml-lab"],
            )
            self.assertTrue(projects[0]["isDefault"])

            selected = run_cli(
                "project",
                "default",
                str(workspace),
                "ml-lab",
                "--json",
            )
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertEqual(
                json_output(selected)["data"]["defaultProject"],
                "ml-lab",
            )

            validated = run_cli("validate", str(workspace), "--json")
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(
                json_output(validated)["context"]["project"]["id"],
                "ml-lab",
            )

            inspected = run_cli(
                "inspect",
                str(workspace),
                "--project",
                "factor-lab",
                "--json",
            )
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            inspected_json = json_output(inspected)
            self.assertEqual(
                inspected_json["context"]["project"]["id"],
                "factor-lab",
            )
            self.assertEqual(
                sorted(inspected_json["data"]["directories"]),
                [
                    "cache",
                    "data",
                    "factors",
                    "judges",
                    "models",
                    "runs",
                    "sessions",
                    "strategies",
                    "studies",
                ],
            )

    def test_project_list_discloses_effective_local_projects_configuration(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            external = root / "external"
            self.assertEqual(
                run_cli("workspace", "init", str(repository)).returncode,
                0,
            )
            self.assertEqual(
                run_cli("workspace", "init", str(external)).returncode,
                0,
            )
            self.assertEqual(
                run_cli(
                    "project",
                    "create",
                    str(external),
                    "external-project",
                ).returncode,
                0,
            )
            local_path = repository / "autoquant-workspace.local.json"
            local_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "Local Development Desk",
                        "projects_directory": "../external/projects",
                        "default_project": "external-project",
                    }
                ),
                encoding="utf-8",
            )

            result = run_cli("project", "list", str(repository), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            envelope = json_output(result)
            workspace = envelope["context"]["workspace"]
            self.assertEqual(
                workspace["projectsDir"],
                str((external / "projects").resolve()),
            )
            self.assertEqual(workspace["configurationSource"], "local-override")
            self.assertEqual(
                workspace["configurationPath"],
                str(local_path.resolve()),
            )
            self.assertEqual(
                [item["id"] for item in envelope["data"]["projects"]],
                ["external-project"],
            )

            human = run_cli("project", "list", str(repository))
            self.assertEqual(human.returncode, 0, human.stderr)
            self.assertIn(str((external / "projects").resolve()), human.stdout)
            self.assertIn("(local-override)", human.stdout)

    def test_validation_and_usage_failures_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            invalid = run_cli(
                "project",
                "create",
                str(workspace),
                "Bad_ID",
                "--json",
            )
            self.assertEqual(invalid.returncode, 1)
            invalid_json = json_output(invalid)
            self.assertFalse(invalid_json["ok"])
            self.assertEqual(
                invalid_json["error"]["code"],
                "validation.failed",
            )
            self.assertEqual(
                invalid_json["error"]["issues"][0]["code"],
                "schema.id",
            )

            usage = run_cli(
                "project",
                "create",
                str(workspace),
                "--json",
            )
            self.assertEqual(usage.returncode, 2)
            usage_json = json_output(usage)
            self.assertFalse(usage_json["ok"])
            self.assertEqual(usage_json["command"], "project.create")
            self.assertEqual(usage_json["error"]["code"], "cli.usage")

    def test_json_cli_creates_study_and_publishes_immutable_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "factor-project",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            project = Path(json_output(created)["data"]["projectDir"])
            (project / "factors" / "candidate.py").write_text("SCORE = 3.5\n")
            (project / "judges" / "evaluate.py").write_text(SUCCESS_JUDGE)

            study_created = run_cli(
                "study",
                "create",
                str(workspace),
                "factor-quality",
                "--subject-kind",
                "factor",
                "--subject-name",
                "candidate-factor",
                "--judge",
                "judges/evaluate.py",
                "--judge-path",
                "judges/**",
                "--editable",
                "factors/**",
                "--metric",
                "score",
                "--dataset-id",
                "synthetic-bars",
                "--dataset-version",
                "v1",
                "--asset-class",
                "equity",
                "--asset",
                "AAA/USD",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-31",
                "--json",
            )
            self.assertEqual(study_created.returncode, 0, study_created.stderr)
            study_json = json_output(study_created)
            self.assertEqual(study_json["command"], "study.create")
            self.assertEqual(study_json["artifacts"][0]["kind"], "study")
            self.assertEqual(
                study_json["nextActions"][0]["id"],
                "run.execute",
            )

            studies = run_cli("study", "list", str(workspace), "--json")
            self.assertEqual(studies.returncode, 0, studies.stderr)
            self.assertEqual(
                json_output(studies)["data"]["studies"][0]["id"],
                "factor-quality",
            )
            inspected = run_cli(
                "study",
                "inspect",
                str(workspace),
                "--study",
                "factor-quality",
                "--json",
            )
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            study_input_hash = json_output(inspected)["data"]["identity"]["inputHash"]

            executed = run_cli(
                "run",
                "execute",
                str(workspace),
                "--study",
                "factor-quality",
                "--json",
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            executed_json = json_output(executed)
            self.assertEqual(executed_json["data"]["status"], "succeeded")
            self.assertEqual(executed_json["data"]["metrics"]["score"], 3.5)
            self.assertEqual(
                executed_json["data"]["studyInputHash"],
                study_input_hash,
            )
            self.assertNotEqual(
                executed_json["data"]["inputHash"],
                study_input_hash,
            )
            self.assertTrue(executed_json["artifacts"][0]["immutable"])
            run_id = executed_json["data"]["id"]

            listed = run_cli(
                "run",
                "list",
                str(workspace),
                "--study",
                "factor-quality",
                "--json",
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(json_output(listed)["data"]["runs"][0]["id"], run_id)

            shown = run_cli(
                "run",
                "show",
                str(workspace),
                "--run",
                run_id,
                "--json",
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            shown_json = json_output(shown)
            self.assertEqual(shown_json["data"]["manifest"]["id"], run_id)
            self.assertEqual(shown_json["data"]["result"]["metrics"]["score"], 3.5)

    def test_json_cli_drives_keep_history_and_guarded_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            self.assertEqual(
                run_cli("workspace", "init", str(workspace), "--json").returncode,
                0,
            )
            created = run_cli(
                "project",
                "create",
                str(workspace),
                "factor-project",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            project = Path(json_output(created)["data"]["projectDir"])
            (project / "factors/candidate.py").write_text("SCORE = 1.0\n")
            (project / "judges/evaluate.py").write_text(SUCCESS_JUDGE)
            study = run_cli(
                "study",
                "create",
                str(workspace),
                "factor-quality",
                "--subject-kind",
                "factor",
                "--judge",
                "judges/evaluate.py",
                "--editable",
                "factors/**",
                "--dataset-id",
                "synthetic-bars",
                "--asset-class",
                "equity",
                "--asset",
                "AAA/USD",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-31",
                "--json",
            )
            self.assertEqual(study.returncode, 0, study.stderr)

            started = run_cli(
                "session",
                "start",
                str(workspace),
                "--study",
                "factor-quality",
                "--json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            started_json = json_output(started)
            session_id = started_json["data"]["session"]["id"]
            worktree = Path(started_json["data"]["worktree"])
            self.assertEqual(started_json["data"]["session"]["leader"]["value"], 1.0)
            self.assertEqual(
                [action["id"] for action in started_json["nextActions"]],
                ["session.show", "session.compare", "experiment.evaluate"],
            )
            (worktree / "factors/candidate.py").write_text("SCORE = 2.0\n")

            evaluated = run_cli(
                "experiment",
                "evaluate",
                str(workspace),
                "--session",
                session_id,
                "--hypothesis",
                "Raise the bounded synthetic score.",
                "--json",
            )
            self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
            evaluated_json = json_output(evaluated)
            self.assertEqual(
                evaluated_json["data"]["experiment"]["verdict"],
                "KEEP",
            )
            self.assertEqual(
                evaluated_json["data"]["verdictAuthority"],
                {
                    "scope": "session-objective-only",
                    "scientificQualification": False,
                    "downstreamAdmission": False,
                    "tradingAuthority": "none",
                },
            )
            experiment_id = evaluated_json["data"]["experiment"]["id"]
            self.assertIn(
                "session.promote",
                [action["id"] for action in evaluated_json["nextActions"]],
            )
            oriented = run_cli("orient", str(workspace), "--json")
            self.assertEqual(oriented.returncode, 0, oriented.stderr)
            oriented_json = json_output(oriented)
            self.assertEqual(
                oriented_json["data"]["primaryAction"]["id"],
                "session.promote",
            )
            self.assertEqual(
                [item["code"] for item in oriented_json["data"]["reasons"]],
                ["promotion-ready"],
            )
            self.assertEqual(
                [item["id"] for item in oriented_json["nextActions"]],
                ["session.promote"],
            )
            human_oriented = run_cli("orient", str(workspace))
            self.assertEqual(
                human_oriented.returncode,
                0,
                human_oriented.stderr,
            )
            self.assertIn(
                "Reason: promotion-ready",
                human_oriented.stdout,
            )
            self.assertIn(
                "Next: aq session promote",
                human_oriented.stdout,
            )
            compared = run_cli(
                "session",
                "compare",
                str(workspace),
                "--session",
                session_id,
                "--trials",
                "1",
                "--json",
            )
            self.assertEqual(compared.returncode, 0, compared.stderr)
            comparison = json_output(compared)
            self.assertEqual(comparison["command"], "session.compare")
            self.assertEqual(
                comparison["data"]["kind"],
                "autoquant-session-decision-matrix",
            )
            self.assertEqual(comparison["data"]["metricFamily"], "generic")
            self.assertEqual(
                [trial["verdict"] for trial in comparison["data"]["trials"]],
                ["BASELINE", "KEEP"],
            )

            history = run_cli(
                "experiment",
                "list",
                str(workspace),
                "--session",
                session_id,
                "--json",
            )
            self.assertEqual(history.returncode, 0, history.stderr)
            self.assertEqual(
                json_output(history)["data"]["experiments"][0]["id"],
                experiment_id,
            )
            shown = run_cli(
                "experiment",
                "show",
                str(workspace),
                "--session",
                session_id,
                "--experiment",
                experiment_id,
                "--json",
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertEqual(
                json_output(shown)["data"]["result"]["verdict"],
                "KEEP",
            )
            self.assertEqual(
                json_output(shown)["data"]["verdictAuthority"],
                evaluated_json["data"]["verdictAuthority"],
            )

            promoted = run_cli(
                "session",
                "promote",
                str(workspace),
                "--session",
                session_id,
                "--json",
            )
            self.assertEqual(promoted.returncode, 0, promoted.stderr)
            promoted_json = json_output(promoted)
            self.assertEqual(
                promoted_json["data"]["session"]["status"],
                "promoted",
            )
            self.assertEqual(
                (project / "factors/candidate.py").read_text(),
                "SCORE = 2.0\n",
            )
            post_promotion = run_cli(
                "orient",
                str(workspace),
                "--json",
            )
            self.assertEqual(
                post_promotion.returncode,
                0,
                post_promotion.stderr,
            )
            self.assertEqual(
                promoted_json["nextActions"],
                json_output(post_promotion)["nextActions"],
            )
            self.assertEqual(
                promoted_json["data"]["agentWorkBrief"],
                json_output(post_promotion)["data"],
            )
            self.assertEqual(
                [item["id"] for item in promoted_json["nextActions"]],
                ["session.start"],
            )

    def test_human_experiment_and_promotion_disclose_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            session = start_session(project, "factor-quality")
            (
                session.worktree_project.root_dir / "factors/candidate.py"
            ).write_text("SCORE = 2.0\n", encoding="utf-8")

            evaluated = run_cli(
                "experiment",
                "evaluate",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--hypothesis",
                "Raise the bounded synthetic score.",
            )

            self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
            self.assertIn("Experiment exp-0001", evaluated.stdout)
            self.assertIn(
                "Authority: Session objective only; this verdict is not "
                "scientific qualification, downstream admission, or trading "
                "authority.",
                evaluated.stdout,
            )
            shown = run_cli(
                "experiment",
                "show",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--experiment",
                list_experiments(project, session)[0].id,
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertIn(
                "Authority: Session objective only; this verdict is not "
                "scientific qualification, downstream admission, or trading "
                "authority.",
                shown.stdout,
            )

            promoted = run_cli(
                "session",
                "promote",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
            )

            self.assertEqual(promoted.returncode, 0, promoted.stderr)
            self.assertIn("Post-promotion: session-required", promoted.stdout)

    def test_json_cli_runs_and_inspects_a_bounded_external_campaign(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            session = start_session(project, "factor-quality")
            researcher = Path(directory) / "researcher.py"
            researcher.write_text(
                """\
import json
import os
from pathlib import Path

Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text("SCORE = 2.0\\n")
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "bounded-cli-smoke",
    "hypothesis": "Raise the synthetic score once.",
    "expected_effect": "Beat the baseline.",
}))
""",
                encoding="utf-8",
            )
            command = (
                f"{shlex.quote(sys.executable)} {shlex.quote(str(researcher))}"
            )

            executed = run_cli(
                "research",
                "run",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--agent-command",
                command,
                "--max-turns",
                "1",
                "--max-wall-seconds",
                "30",
                "--turn-timeout-seconds",
                "5",
                "--json",
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            envelope = json_output(executed)
            self.assertEqual(envelope["command"], "research.run")
            self.assertEqual(
                envelope["data"]["result"]["status"],
                "budget_exhausted",
            )
            self.assertEqual(
                envelope["data"]["result"]["verdicts"]["KEEP"],
                1,
            )
            self.assertEqual(envelope["artifacts"][0]["kind"], "campaign")
            campaign_id = envelope["data"]["result"]["id"]

            listed = run_cli(
                "research",
                "list",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--json",
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(
                json_output(listed)["data"]["campaigns"][0]["id"],
                campaign_id,
            )

            shown = run_cli(
                "research",
                "show",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--campaign",
                campaign_id,
                "--json",
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertEqual(
                json_output(shown)["data"]["result"]["id"],
                campaign_id,
            )

            studio = run_cli(
                "studio",
                "snapshot",
                str(project.root_dir),
                "--json",
            )
            self.assertEqual(studio.returncode, 0, studio.stderr)
            studio_json = json_output(studio)
            self.assertEqual(studio_json["command"], "studio.snapshot")
            self.assertEqual(
                studio_json["data"]["projects"][0]["counts"]["campaigns"],
                1,
            )
            self.assertEqual(
                studio_json["nextActions"][0]["id"],
                "studio.serve",
            )

    def test_json_cli_binds_request_and_publishes_verified_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            request = {
                "schemaVersion": 1,
                "kind": "autoquant-research-request",
                "title": "AAA support request",
                "question": "Does AAA have positive factor support?",
                "decisionContext": "OpenAlice is gathering decision support.",
                "assets": [
                    {
                        "symbol": "AAA/USD",
                        "assetClass": "equity",
                        "venue": "TEST",
                    }
                ],
                "direction": "long",
                "horizon": "one month",
                "hypotheses": ["The factor remains positive."],
                "constraints": ["Use the locked Study."],
                "deliverables": ["factor evidence"],
                "source": {
                    "system": "openalice",
                    "workspaceId": "equity-desk",
                    "sessionId": "resume-cli-origin",
                    "artifactPath": "requests/aaa.md",
                    "artifactRevision": "sha256:cli-request",
                },
            }
            request_path = Path(directory) / "request.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            started = run_cli(
                "session",
                "start",
                str(project.root_dir),
                "--study",
                "factor-quality",
                "--request",
                str(request_path),
                "--json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            started_json = json_output(started)
            session_id = started_json["data"]["session"]["id"]
            baseline_id = started_json["data"]["session"]["baseline"]["runId"]
            self.assertEqual(
                started_json["data"]["delegation"]["request"]["title"],
                "AAA support request",
            )
            self.assertEqual(
                [item["kind"] for item in started_json["artifacts"][-2:]],
                ["research-request", "research-brief"],
            )
            self.assertEqual(
                started_json["nextActions"][-1]["id"],
                "report.publish",
            )

            evidence = {
                "kind": "run",
                "id": baseline_id,
                "artifactPath": "artifacts/report.json",
            }
            analysis = {
                "schemaVersion": 1,
                "kind": "autoquant-research-report-analysis",
                "title": "AAA evidence report",
                "executiveSummary": "The fixed baseline is positive.",
                "findings": [
                    {
                        "id": "positive-baseline",
                        "claim": "The fixed baseline score is positive.",
                        "confidence": "medium",
                        "evidenceRefs": [evidence],
                    }
                ],
                "recommendations": [],
                "limitations": ["Synthetic fixture only."],
                "unresolvedQuestions": ["Does it survive realistic costs?"],
            }
            analysis_path = Path(directory) / "analysis.json"
            analysis_path.write_text(json.dumps(analysis), encoding="utf-8")
            published = run_cli(
                "report",
                "publish",
                str(project.root_dir),
                "--session",
                session_id,
                "--analysis",
                str(analysis_path),
                "--json",
            )
            self.assertEqual(published.returncode, 0, published.stderr)
            published_json = json_output(published)
            report_id = published_json["data"]["report"]["id"]
            self.assertEqual(
                published_json["data"]["report"]["tradingAuthority"],
                "none",
            )
            self.assertEqual(
                [item["kind"] for item in published_json["artifacts"]],
                ["research-report", "research-report-markdown"],
            )
            self.assertEqual(
                [item["id"] for item in published_json["nextActions"]],
                ["report.show", "session.complete"],
            )

            listed = run_cli(
                "report",
                "list",
                str(project.root_dir),
                "--session",
                session_id,
                "--json",
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(
                json_output(listed)["data"]["reports"][0]["id"],
                report_id,
            )
            shown = run_cli(
                "report",
                "show",
                str(project.root_dir),
                "--session",
                session_id,
                "--report",
                report_id,
                "--json",
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertEqual(
                json_output(shown)["data"]["report"]["analysisHash"],
                published_json["data"]["report"]["analysisHash"],
            )

            completed = run_cli(
                "session",
                "complete",
                str(project.root_dir),
                "--session",
                session_id,
                "--report",
                report_id,
                "--json",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            completed_json = json_output(completed)
            self.assertEqual(
                completed_json["data"]["session"]["status"],
                "completed",
            )
            self.assertEqual(
                completed_json["data"]["receipt"]["report"]["id"],
                report_id,
            )
            self.assertEqual(
                [item["kind"] for item in completed_json["artifacts"]],
                ["session-completion", "research-report"],
            )
            self.assertNotIn(
                "experiment.evaluate",
                {
                    action["id"]
                    for action in completed_json["nextActions"]
                },
            )


if __name__ == "__main__":
    unittest.main()
