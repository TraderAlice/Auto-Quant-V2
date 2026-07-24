from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autoquant.sessions import start_session
from autoquant.studies import create_study
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
                [action["id"] for action in envelope["nextActions"]],
                ["study.inspect", "run.execute"],
            )
            project = Path(envelope["data"]["projectDir"])
            study = json.loads(
                (
                    project
                    / "studies"
                    / "ohlcv-factor-quality"
                    / "study.json"
                ).read_text()
            )
            self.assertEqual(study["dataset"]["paths"], ["ohlcv/**"])

            executed = run_cli(
                "run",
                "execute",
                str(project),
                "--study",
                "ohlcv-factor-quality",
                "--json",
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            result = json_output(executed)["data"]
            self.assertEqual(result["status"], "succeeded")
            self.assertIn("sourceHashes", result["dataset"])

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
                "workspace.init",
                "project.create",
                "project.list",
                "project.default",
                "validate",
                "inspect",
                "study.create",
                "study.list",
                "study.inspect",
                "run.execute",
                "run.list",
                "run.show",
                "session.start",
                "session.list",
                "session.show",
                "session.promote",
                "experiment.evaluate",
                "experiment.list",
                "experiment.show",
                "research.run",
                "research.list",
                "research.show",
                "report.publish",
                "report.list",
                "report.show",
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
            ["blank", "ohlcv-factor-lab", "ohlcv-portfolio-lab"],
        )
        schema = next(command for command in commands if command["id"] == "schema")
        self.assertEqual(
            schema["arguments"][0]["choices"],
            [
                "workspace",
                "project",
                "study",
                "judge-output",
                "run-result",
                "session",
                "experiment",
                "researcher-response",
                "campaign-result",
                "campaign-progress",
                "research-request",
                "report-analysis",
                "studio-snapshot",
            ],
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
        studio_schema = run_cli("schema", "studio-snapshot", "--json")
        self.assertEqual(studio_schema.returncode, 0, studio_schema.stderr)
        self.assertEqual(
            json_output(studio_schema)["data"]["schema"]["properties"]["kind"][
                "const"
            ],
            "autoquant-studio-snapshot",
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
                ["session.show", "experiment.evaluate"],
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
            experiment_id = evaluated_json["data"]["experiment"]["id"]
            self.assertIn(
                "session.promote",
                [action["id"] for action in evaluated_json["nextActions"]],
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


if __name__ == "__main__":
    unittest.main()
