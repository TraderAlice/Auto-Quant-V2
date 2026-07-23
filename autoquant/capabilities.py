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
        "aq schema [workspace|project] [--json]",
        "List or emit canonical Workspace and Project JSON Schemas.",
        "read-only",
        [
            argument(
                "kind",
                "positional",
                "string",
                False,
                "Schema kind; omit to list kinds.",
                choices=["workspace", "project"],
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
]
