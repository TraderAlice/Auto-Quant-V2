"""Human- and Agent-facing AutoQuant command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Sequence

from .capabilities import CLI_COMMANDS
from .cli_contract import (
    artifact,
    error_envelope,
    global_context,
    next_action,
    project_context,
    success_envelope,
    workspace_context,
)
from .workspace import (
    PROJECT_MANIFEST,
    WORKSPACE_MANIFEST,
    create_project,
    initialize_workspace,
    inspect_project,
    list_workspace_projects,
    load_project,
    load_workspace,
    resolve_project_directory,
    schema_for,
    set_default_project,
)


class CliUsageError(ValueError):
    pass


class RaisingArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


@dataclass
class CommandResult:
    command: str
    data: Any
    human: str
    context: dict[str, Any] = field(default_factory=global_context)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[dict[str, Any]] = field(default_factory=list)


def _json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit one versioned machine-readable JSON envelope",
    )


def build_parser() -> RaisingArgumentParser:
    parser = RaisingArgumentParser(
        prog="aq",
        description=(
            "AutoQuant V2 — one standardized quantitative workbench with "
            "many self-contained Projects."
        ),
    )
    parser.add_argument("--version", action="version", version="aq 0.1.0")
    subcommands = parser.add_subparsers(dest="command", required=True)

    capabilities = subcommands.add_parser(
        "capabilities",
        help="describe every public command for Agents",
    )
    capabilities.set_defaults(command_id="capabilities")
    _json_argument(capabilities)

    schema = subcommands.add_parser(
        "schema",
        help="list or emit canonical manifest JSON Schemas",
    )
    schema.add_argument("kind", nargs="?", choices=["workspace", "project"])
    schema.set_defaults(command_id="schema")
    _json_argument(schema)

    workspace = subcommands.add_parser("workspace", help="manage a Workspace")
    workspace_actions = workspace.add_subparsers(dest="workspace_action", required=True)
    workspace_init = workspace_actions.add_parser("init", help="initialize a Workspace")
    workspace_init.add_argument("directory")
    workspace_init.add_argument("--name")
    workspace_init.set_defaults(command_id="workspace.init")
    _json_argument(workspace_init)

    project = subcommands.add_parser("project", help="manage Projects")
    project_actions = project.add_subparsers(dest="project_action", required=True)
    project_create = project_actions.add_parser(
        "create",
        help="create a self-contained Project",
    )
    project_create.add_argument("workspace")
    project_create.add_argument("project_id")
    project_create.add_argument("--name")
    project_create.add_argument("--description", default="")
    project_create.set_defaults(command_id="project.create")
    _json_argument(project_create)

    project_list = project_actions.add_parser("list", help="list Workspace Projects")
    project_list.add_argument("workspace")
    project_list.set_defaults(command_id="project.list")
    _json_argument(project_list)

    project_default = project_actions.add_parser(
        "default",
        help="select the default Project",
    )
    project_default.add_argument("workspace")
    project_default.add_argument("project_id")
    project_default.set_defaults(command_id="project.default")
    _json_argument(project_default)

    for command in ("validate", "inspect"):
        command_parser = subcommands.add_parser(
            command,
            help=f"{command} one resolved Project",
        )
        command_parser.add_argument("path")
        command_parser.add_argument("--project")
        command_parser.set_defaults(command_id=command)
        _json_argument(command_parser)
    return parser


def _workspace_init(args: argparse.Namespace) -> CommandResult:
    workspace = initialize_workspace(args.directory, name=args.name)
    manifest_path = workspace.root_dir / WORKSPACE_MANIFEST
    return CommandResult(
        "workspace.init",
        {
            "workspaceDir": str(workspace.root_dir),
            "manifest": workspace.manifest.to_dict(),
        },
        f"Initialized AutoQuant Workspace at {workspace.root_dir}\n",
        workspace_context(workspace),
        [artifact("workspace", workspace.manifest.name, manifest_path, immutable=False)],
        [
            next_action(
                "project.create",
                "Create the first self-contained research Project.",
                [
                    "aq",
                    "project",
                    "create",
                    str(workspace.root_dir),
                    "research-project",
                    "--json",
                ],
                "creates-artifact",
            )
        ],
    )


def _project_create(args: argparse.Namespace) -> CommandResult:
    project = create_project(
        args.workspace,
        args.project_id,
        name=args.name,
        description=args.description,
    )
    return CommandResult(
        "project.create",
        {
            "projectDir": str(project.root_dir),
            "manifest": project.manifest.to_dict(),
        },
        f"Created AutoQuant Project '{project.manifest.id}' at {project.root_dir}\n",
        project_context(project),
        [
            artifact(
                "project",
                project.manifest.id,
                project.root_dir / PROJECT_MANIFEST,
                immutable=False,
            )
        ],
        [
            next_action(
                "validate",
                "Validate the newly created Project.",
                ["aq", "validate", str(project.root_dir), "--json"],
                "read-only",
            ),
            next_action(
                "inspect",
                "Inspect the Project construction surfaces.",
                ["aq", "inspect", str(project.root_dir), "--json"],
                "read-only",
            ),
        ],
    )


def _project_list(args: argparse.Namespace) -> CommandResult:
    workspace = load_workspace(args.workspace)
    projects = list_workspace_projects(workspace.root_dir)
    lines = [f"AutoQuant Workspace: {workspace.manifest.name}"]
    if projects:
        lines.extend(
            f"{'*' if item.is_default else ' '} {item.id}  {item.name}  {item.path}"
            for item in projects
        )
    else:
        lines.append("  No Projects")
    actions = [
        next_action(
            "project.create",
            "Create a self-contained research Project.",
            [
                "aq",
                "project",
                "create",
                str(workspace.root_dir),
                "research-project",
                "--json",
            ],
            "creates-artifact",
        )
    ]
    default = next((item for item in projects if item.is_default), None)
    if default:
        actions.append(
            next_action(
                "inspect",
                "Inspect the default Project.",
                ["aq", "inspect", str(workspace.root_dir), "--json"],
                "read-only",
            )
        )
    return CommandResult(
        "project.list",
        {"projects": [item.to_dict() for item in projects]},
        "\n".join(lines) + "\n",
        workspace_context(workspace),
        next_actions=actions,
    )


def _project_default(args: argparse.Namespace) -> CommandResult:
    workspace = set_default_project(args.workspace, args.project_id)
    return CommandResult(
        "project.default",
        {"defaultProject": workspace.manifest.default_project},
        f"Default AutoQuant Project: {workspace.manifest.default_project}\n",
        workspace_context(workspace),
        next_actions=[
            next_action(
                "inspect",
                "Inspect the selected default Project.",
                ["aq", "inspect", str(workspace.root_dir), "--json"],
                "read-only",
            )
        ],
    )


def _selected_project(args: argparse.Namespace):
    directory = resolve_project_directory(args.path, args.project)
    return load_project(directory)


def _validate(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    return CommandResult(
        "validate",
        {
            "valid": True,
            "project": {
                "id": project.manifest.id,
                "name": project.manifest.name,
                "rootDir": str(project.root_dir),
            },
        },
        f"Valid AutoQuant Project '{project.manifest.id}' at {project.root_dir}\n",
        project_context(project),
        [
            artifact(
                "project",
                project.manifest.id,
                project.root_dir / PROJECT_MANIFEST,
                immutable=False,
            )
        ],
        [
            next_action(
                "inspect",
                "Inspect the validated Project.",
                ["aq", "inspect", str(project.root_dir), "--json"],
                "read-only",
            )
        ],
    )


def _inspect(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    data = inspect_project(project)
    directory_lines = [
        f"  {key}: {value['entries']} entries ({value['relativePath']})"
        for key, value in data["directories"].items()
    ]
    human = (
        f"AutoQuant Project: {project.manifest.name} ({project.manifest.id})\n"
        f"Root: {project.root_dir}\n"
        f"Research: {project.manifest.research_program}\n"
        + "\n".join(directory_lines)
        + "\n"
    )
    return CommandResult(
        "inspect",
        data,
        human,
        project_context(project),
        [
            artifact(
                "project",
                project.manifest.id,
                project.root_dir / PROJECT_MANIFEST,
                immutable=False,
            )
        ],
        [
            next_action(
                "validate",
                "Revalidate Project structure after editing.",
                ["aq", "validate", str(project.root_dir), "--json"],
                "read-only",
            )
        ],
    )


def dispatch(args: argparse.Namespace) -> CommandResult:
    if args.command_id == "capabilities":
        human = "\n\n".join(
            f"{command['usage']}\n  {command['description']}\n"
            f"  effect: {command['effect']}"
            for command in CLI_COMMANDS
        )
        return CommandResult(
            "capabilities",
            {
                "name": "aq",
                "description": "AutoQuant V2 quantitative research workbench CLI",
                "commands": CLI_COMMANDS,
            },
            human + "\n",
        )
    if args.command_id == "schema":
        kinds = ["project", "workspace"]
        if args.kind is None:
            return CommandResult(
                "schema",
                {"kinds": kinds},
                "AutoQuant schema kinds:\n  project\n  workspace\n",
            )
        schema = schema_for(args.kind)
        return CommandResult(
            "schema",
            {"kind": args.kind, "schema": schema},
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
        )
    if args.command_id == "workspace.init":
        return _workspace_init(args)
    if args.command_id == "project.create":
        return _project_create(args)
    if args.command_id == "project.list":
        return _project_list(args)
    if args.command_id == "project.default":
        return _project_default(args)
    if args.command_id == "validate":
        return _validate(args)
    if args.command_id == "inspect":
        return _inspect(args)
    raise CliUsageError(f"Unknown command: {args.command_id}")


def _command_id(argv: Sequence[str]) -> str:
    if not argv:
        return "help"
    if argv[0] in {"workspace", "project"} and len(argv) > 1:
        return f"{argv[0]}.{argv[1]}"
    return argv[0]


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    wants_json = "--json" in arguments
    command = _command_id(arguments)
    try:
        parsed = build_parser().parse_args(arguments)
        command = parsed.command_id
        result = dispatch(parsed)
        if parsed.json:
            print(
                json.dumps(
                    success_envelope(
                        result.command,
                        result.data,
                        context=result.context,
                        artifacts=result.artifacts,
                        next_actions=result.next_actions,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            sys.stdout.write(result.human)
        return 0
    except CliUsageError as error:
        envelope = error_envelope(command, error, usage=True)
        if wants_json:
            print(json.dumps(envelope, indent=2, sort_keys=True))
        else:
            print(f"aq: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        envelope = error_envelope(command, error)
        if wants_json:
            print(json.dumps(envelope, indent=2, sort_keys=True))
        else:
            print(f"aq: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
