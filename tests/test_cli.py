from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
            ],
        )
        for command in commands:
            self.assertTrue(command["supportsJson"])
            self.assertIn(
                command["effect"],
                {
                    "read-only",
                    "creates-artifact",
                    "mutates-workspace",
                },
            )
            self.assertEqual(command["exitCodes"]["success"], 0)
            self.assertEqual(command["exitCodes"]["usage"], 2)

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
                    "models",
                    "runs",
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


if __name__ == "__main__":
    unittest.main()
