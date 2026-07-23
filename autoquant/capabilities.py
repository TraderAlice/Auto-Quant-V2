"""Machine-discoverable public CLI capabilities."""

from __future__ import annotations

from typing import Any


EXIT_CODES = {"success": 0, "failure": [1], "usage": 2}


def argument(
    name: str,
    form: str,
    value: str,
    required: bool,
    description: str,
    *,
    default: Any | None = None,
    choices: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "form": form,
        "value": value,
        "required": required,
        "description": description,
    }
    if default is not None:
        result["default"] = default
    if choices is not None:
        result["choices"] = choices
    return result


JSON_ARGUMENT = argument(
    "json",
    "option",
    "boolean",
    False,
    "Emit one versioned machine-readable JSON envelope.",
    default=False,
)
PROJECT_ARGUMENT = argument(
    "project",
    "option",
    "string",
    False,
    "Project id inside a Workspace.",
    default="Workspace default",
)
PATH_ARGUMENT = argument(
    "path",
    "positional",
    "string",
    True,
    "Direct Project or Workspace directory.",
)
STUDY_ARGUMENT = argument(
    "study",
    "option",
    "string",
    True,
    "Project-local Study id.",
)
RUN_ARGUMENT = argument(
    "run",
    "option",
    "string",
    True,
    "Immutable Run id.",
)


def descriptor(
    command_id: str,
    usage: str,
    description: str,
    effect: str,
    arguments: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": command_id,
        "usage": usage,
        "description": description,
        "effect": effect,
        "supportsJson": True,
        "exitCodes": EXIT_CODES,
        "arguments": arguments,
        "outputSections": [],
    }


CLI_COMMANDS = [
    descriptor(
        "capabilities",
        "aq capabilities [--json]",
        "Describe every public command, argument, effect, and exit behavior.",
        "read-only",
        [JSON_ARGUMENT],
    ),
    descriptor(
        "schema",
        "aq schema [workspace|project|study|judge-output|run-result] [--json]",
        "List or emit canonical AutoQuant JSON Schemas.",
        "read-only",
        [
            argument(
                "kind",
                "positional",
                "string",
                False,
                "Schema kind; omit to list kinds.",
                choices=[
                    "workspace",
                    "project",
                    "study",
                    "judge-output",
                    "run-result",
                ],
            ),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "workspace.init",
        "aq workspace init <workspace-dir> [--name NAME] [--json]",
        "Create an empty multi-Project AutoQuant Workspace.",
        "creates-artifact",
        [
            argument(
                "workspace-dir",
                "positional",
                "string",
                True,
                "New empty Workspace directory.",
            ),
            argument(
                "name",
                "option",
                "string",
                False,
                "Workspace display name.",
                default="Directory name",
            ),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "project.create",
        "aq project create <workspace-dir> <project-id> [options]",
        "Create one complete self-contained quantitative research Project.",
        "creates-artifact",
        [
            argument(
                "workspace-dir",
                "positional",
                "string",
                True,
                "Existing AutoQuant Workspace directory.",
            ),
            argument(
                "project-id",
                "positional",
                "string",
                True,
                "Lowercase kebab-case Project id.",
            ),
            argument(
                "name",
                "option",
                "string",
                False,
                "Project display name.",
                default="Project id",
            ),
            argument(
                "description",
                "option",
                "string",
                False,
                "Initial quantitative research question.",
                default="Empty",
            ),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "project.list",
        "aq project list <workspace-dir> [--json]",
        "List immediate self-contained Workspace Projects.",
        "read-only",
        [
            argument(
                "workspace-dir",
                "positional",
                "string",
                True,
                "Existing AutoQuant Workspace directory.",
            ),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "project.default",
        "aq project default <workspace-dir> <project-id> [--json]",
        "Select the Workspace default Project.",
        "mutates-workspace",
        [
            argument(
                "workspace-dir",
                "positional",
                "string",
                True,
                "Existing AutoQuant Workspace directory.",
            ),
            argument(
                "project-id",
                "positional",
                "string",
                True,
                "Existing Project id.",
            ),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "validate",
        "aq validate <project-or-workspace-dir> [--project ID] [--json]",
        "Strictly validate and resolve one AutoQuant Project.",
        "read-only",
        [
            argument(
                "path",
                "positional",
                "string",
                True,
                "Direct Project or Workspace directory.",
            ),
            PROJECT_ARGUMENT,
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "inspect",
        "aq inspect <project-or-workspace-dir> [--project ID] [--json]",
        "Inspect one Project's research program and owned construction surfaces.",
        "read-only",
        [
            argument(
                "path",
                "positional",
                "string",
                True,
                "Direct Project or Workspace directory.",
            ),
            PROJECT_ARGUMENT,
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "study.create",
        "aq study create <path> <study-id> [contract options] [--json]",
        "Create and validate one fixed Project-local quantitative Study.",
        "creates-artifact",
        [
            PATH_ARGUMENT,
            argument(
                "study-id",
                "positional",
                "string",
                True,
                "Lowercase kebab-case Study id.",
            ),
            PROJECT_ARGUMENT,
            argument("name", "option", "string", False, "Study display name.", default="Study id"),
            argument("description", "option", "string", False, "Bounded research question.", default="Empty"),
            argument(
                "subject-kind",
                "option",
                "string",
                True,
                "Research subject kind.",
                choices=["strategy", "factor", "model", "research"],
            ),
            argument("subject-name", "option", "string", False, "Research subject name.", default="Study id"),
            argument("subject-version", "option", "string", False, "Mutable subject version label.", default="working"),
            argument("judge", "option", "string", True, "Project-relative Python Judge entrypoint."),
            argument("judge-path", "option", "string", False, "Repeatable fixed Judge file or trailing /** closure.", default="Judge entrypoint"),
            argument("judge-arg", "option", "string", False, "Repeatable fixed Judge argument.", default="None"),
            argument("editable", "option", "string", True, "Repeatable Agent-editable file or trailing /** closure."),
            argument("metric", "option", "string", False, "Primary metric name.", default="score"),
            argument(
                "direction",
                "option",
                "string",
                False,
                "Primary metric direction.",
                default="maximize",
                choices=["maximize", "minimize"],
            ),
            argument("minimum-improvement", "option", "number", False, "Minimum comparable improvement.", default=0),
            argument("dataset-id", "option", "string", True, "Dataset identity."),
            argument("dataset-version", "option", "string", False, "Dataset version.", default="working"),
            argument("asset-class", "option", "string", True, "Dataset asset class."),
            argument("asset", "option", "string", True, "Repeatable asset universe member."),
            argument("start", "option", "string", True, "Dataset start date YYYY-MM-DD."),
            argument("end", "option", "string", True, "Dataset end date YYYY-MM-DD."),
            argument("timeout", "option", "integer", False, "Judge timeout in seconds.", default=60),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "study.list",
        "aq study list <path> [--project ID] [--json]",
        "List strict Project-local Studies.",
        "read-only",
        [PATH_ARGUMENT, PROJECT_ARGUMENT, JSON_ARGUMENT],
    ),
    descriptor(
        "study.inspect",
        "aq study inspect <path> --study ID [--project ID] [--json]",
        "Inspect one fixed Study, source closure, Judge, dataset, and input identity.",
        "read-only",
        [PATH_ARGUMENT, PROJECT_ARGUMENT, STUDY_ARGUMENT, JSON_ARGUMENT],
    ),
    descriptor(
        "run.execute",
        "aq run execute <path> --study ID [--project ID] [--json]",
        "Execute one bounded Python Judge and publish an immutable RunResult.",
        "creates-artifact",
        [PATH_ARGUMENT, PROJECT_ARGUMENT, STUDY_ARGUMENT, JSON_ARGUMENT],
    ),
    descriptor(
        "run.list",
        "aq run list <path> [--study ID] [--project ID] [--json]",
        "List verified immutable Runs, optionally filtered by Study.",
        "read-only",
        [
            PATH_ARGUMENT,
            PROJECT_ARGUMENT,
            argument("study", "option", "string", False, "Optional Study id filter."),
            JSON_ARGUMENT,
        ],
    ),
    descriptor(
        "run.show",
        "aq run show <path> --run ID [--project ID] [--json]",
        "Verify and inspect one immutable RunResult.",
        "read-only",
        [PATH_ARGUMENT, PROJECT_ARGUMENT, RUN_ARGUMENT, JSON_ARGUMENT],
    ),
]
