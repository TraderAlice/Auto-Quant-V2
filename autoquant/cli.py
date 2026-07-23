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
from .runs import (
    JUDGE_OUTPUT_JSON_SCHEMA,
    RUN_RESULT_JSON_SCHEMA,
    execute_study,
    list_runs,
    load_run,
)
from .sessions import (
    EXPERIMENT_JSON_SCHEMA,
    SESSION_JSON_SCHEMA,
    evaluate_experiment,
    list_experiments,
    list_sessions,
    load_experiment,
    load_session,
    promote_session,
    session_snapshot,
    start_session,
)
from .studies import (
    STUDY_JSON_SCHEMA,
    StudyDataset,
    StudyDefinition,
    StudyJudge,
    StudyObjective,
    StudySubject,
    StudyTimeRange,
    create_study,
    list_studies,
    load_study,
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
    schema_for as workspace_schema_for,
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
    schema.add_argument(
        "kind",
        nargs="?",
        choices=[
            "workspace",
            "project",
            "study",
            "judge-output",
            "run-result",
            "session",
            "experiment",
        ],
    )
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

    study = subcommands.add_parser("study", help="manage fixed quantitative Studies")
    study_actions = study.add_subparsers(dest="study_action", required=True)
    study_create = study_actions.add_parser(
        "create",
        help="create one fixed Project-local Study",
    )
    study_create.add_argument("path")
    study_create.add_argument("study_id")
    study_create.add_argument("--project")
    study_create.add_argument("--name")
    study_create.add_argument("--description", default="")
    study_create.add_argument(
        "--subject-kind",
        choices=["strategy", "factor", "model", "research"],
        required=True,
    )
    study_create.add_argument("--subject-name")
    study_create.add_argument("--subject-version", default="working")
    study_create.add_argument("--judge", required=True)
    study_create.add_argument("--judge-path", action="append")
    study_create.add_argument("--judge-arg", action="append", default=[])
    study_create.add_argument("--editable", action="append", required=True)
    study_create.add_argument("--metric", default="score")
    study_create.add_argument(
        "--direction",
        choices=["maximize", "minimize"],
        default="maximize",
    )
    study_create.add_argument("--minimum-improvement", type=float, default=0.0)
    study_create.add_argument("--dataset-id", required=True)
    study_create.add_argument("--dataset-version", default="working")
    study_create.add_argument("--asset-class", required=True)
    study_create.add_argument("--asset", action="append", required=True)
    study_create.add_argument("--start", required=True)
    study_create.add_argument("--end", required=True)
    study_create.add_argument("--timeout", type=int, default=60)
    study_create.set_defaults(command_id="study.create")
    _json_argument(study_create)

    study_list = study_actions.add_parser("list", help="list Project Studies")
    study_list.add_argument("path")
    study_list.add_argument("--project")
    study_list.set_defaults(command_id="study.list")
    _json_argument(study_list)

    study_inspect = study_actions.add_parser("inspect", help="inspect one Study")
    study_inspect.add_argument("path")
    study_inspect.add_argument("--project")
    study_inspect.add_argument("--study", required=True)
    study_inspect.set_defaults(command_id="study.inspect")
    _json_argument(study_inspect)

    run = subcommands.add_parser("run", help="execute and inspect immutable Runs")
    run_actions = run.add_subparsers(dest="run_action", required=True)
    run_execute = run_actions.add_parser(
        "execute",
        help="execute one Study through its fixed Judge",
    )
    run_execute.add_argument("path")
    run_execute.add_argument("--project")
    run_execute.add_argument("--study", required=True)
    run_execute.set_defaults(command_id="run.execute")
    _json_argument(run_execute)

    run_list = run_actions.add_parser("list", help="list immutable Runs")
    run_list.add_argument("path")
    run_list.add_argument("--project")
    run_list.add_argument("--study")
    run_list.set_defaults(command_id="run.list")
    _json_argument(run_list)

    run_show = run_actions.add_parser("show", help="verify and show one Run")
    run_show.add_argument("path")
    run_show.add_argument("--project")
    run_show.add_argument("--run", required=True)
    run_show.set_defaults(command_id="run.show")
    _json_argument(run_show)

    session = subcommands.add_parser(
        "session",
        help="manage governed research Sessions",
    )
    session_actions = session.add_subparsers(dest="session_action", required=True)
    session_start = session_actions.add_parser(
        "start",
        help="start a resumable Session from a fresh successful baseline",
    )
    session_start.add_argument("path")
    session_start.add_argument("--project")
    session_start.add_argument("--study", required=True)
    session_start.set_defaults(command_id="session.start")
    _json_argument(session_start)

    session_list = session_actions.add_parser("list", help="list research Sessions")
    session_list.add_argument("path")
    session_list.add_argument("--project")
    session_list.set_defaults(command_id="session.list")
    _json_argument(session_list)

    session_show = session_actions.add_parser("show", help="inspect one Session")
    session_show.add_argument("path")
    session_show.add_argument("--project")
    session_show.add_argument("--session", required=True)
    session_show.set_defaults(command_id="session.show")
    _json_argument(session_show)

    session_promote = session_actions.add_parser(
        "promote",
        help="promote the exact current KEEP into the owning Project",
    )
    session_promote.add_argument("path")
    session_promote.add_argument("--project")
    session_promote.add_argument("--session", required=True)
    session_promote.set_defaults(command_id="session.promote")
    _json_argument(session_promote)

    experiment = subcommands.add_parser(
        "experiment",
        help="evaluate and inspect immutable candidate Experiments",
    )
    experiment_actions = experiment.add_subparsers(
        dest="experiment_action",
        required=True,
    )
    experiment_evaluate = experiment_actions.add_parser(
        "evaluate",
        help="judge the current Session candidate and apply its verdict",
    )
    experiment_evaluate.add_argument("path")
    experiment_evaluate.add_argument("--project")
    experiment_evaluate.add_argument("--session", required=True)
    experiment_evaluate.add_argument("--hypothesis", required=True)
    experiment_evaluate.set_defaults(command_id="experiment.evaluate")
    _json_argument(experiment_evaluate)

    experiment_list = experiment_actions.add_parser(
        "list",
        help="list immutable Experiments in one Session",
    )
    experiment_list.add_argument("path")
    experiment_list.add_argument("--project")
    experiment_list.add_argument("--session", required=True)
    experiment_list.set_defaults(command_id="experiment.list")
    _json_argument(experiment_list)

    experiment_show = experiment_actions.add_parser(
        "show",
        help="verify and inspect one immutable Experiment",
    )
    experiment_show.add_argument("path")
    experiment_show.add_argument("--project")
    experiment_show.add_argument("--session", required=True)
    experiment_show.add_argument("--experiment", required=True)
    experiment_show.set_defaults(command_id="experiment.show")
    _json_argument(experiment_show)
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


def _study_create(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    definition = StudyDefinition(
        schema_version=1,
        id=args.study_id,
        name=(args.name or args.study_id),
        description=args.description,
        program="program.md",
        subject=StudySubject(
            args.subject_kind,
            args.subject_name or args.study_id,
            args.subject_version,
        ),
        editable={"paths": args.editable},
        judge=StudyJudge(
            "python",
            args.judge,
            args.judge_path or [args.judge],
            args.judge_arg,
            args.timeout,
        ),
        objective=StudyObjective(
            args.metric,
            args.direction,
            args.minimum_improvement,
        ),
        dataset=StudyDataset(
            args.dataset_id,
            args.dataset_version,
            args.asset_class,
            args.asset,
            StudyTimeRange(args.start, args.end),
        ),
    )
    study = create_study(project, definition)
    return CommandResult(
        "study.create",
        _study_data(study),
        f"Created AutoQuant Study '{study.definition.id}' at {study.root_dir}\n",
        project_context(project),
        [
            artifact(
                "study",
                study.definition.id,
                study.manifest_path,
                immutable=False,
            )
        ],
        [
            next_action(
                "run.execute",
                "Execute the fixed Study through its bounded Python Judge.",
                [
                    "aq",
                    "run",
                    "execute",
                    str(project.root_dir),
                    "--study",
                    study.definition.id,
                    "--json",
                ],
                "creates-artifact",
            )
        ],
    )


def _study_data(study) -> dict[str, Any]:
    return {
        "definition": study.definition.to_dict(),
        "path": str(study.root_dir),
        "programPath": str(study.program_path),
        "identity": {
            "studyHash": study.study_hash,
            "programHash": study.program_hash,
            "judgeHash": study.judge_hash,
            "judgeSourceHashes": study.judge_hashes,
            "sourceHash": study.source_hash,
            "sourceHashes": study.editable_hashes,
            "datasetHash": study.dataset_hash,
            "inputHash": study.input_hash,
        },
    }


def _study_list(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    studies = list_studies(project)
    lines = [f"AutoQuant Studies in {project.manifest.name}:"]
    lines.extend(
        f"  {item.id}  {item.subject_kind}  "
        f"{item.primary_metric}:{item.direction}  {item.name}"
        for item in studies
    )
    if not studies:
        lines.append("  No Studies")
    return CommandResult(
        "study.list",
        {"studies": [item.to_dict() for item in studies]},
        "\n".join(lines) + "\n",
        project_context(project),
    )


def _study_inspect(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    study = load_study(project, args.study)
    data = _study_data(study)
    return CommandResult(
        "study.inspect",
        data,
        (
            f"AutoQuant Study: {study.definition.name} ({study.definition.id})\n"
            f"Subject: {study.definition.subject.kind} "
            f"{study.definition.subject.name}@{study.definition.subject.version}\n"
            f"Primary: {study.definition.objective.metric} "
            f"({study.definition.objective.direction})\n"
            f"Dataset: {study.definition.dataset.id}@"
            f"{study.definition.dataset.version} · "
            f"{len(study.definition.dataset.universe)} assets · "
            f"{study.definition.dataset.time_range.start}.."
            f"{study.definition.dataset.time_range.end}\n"
            f"Input hash: {study.input_hash}\n"
        ),
        project_context(project),
        [
            artifact(
                "study",
                study.definition.id,
                study.manifest_path,
                immutable=False,
            )
        ],
        [
            next_action(
                "run.execute",
                "Execute the Study through its fixed Judge.",
                [
                    "aq",
                    "run",
                    "execute",
                    str(project.root_dir),
                    "--study",
                    study.definition.id,
                    "--json",
                ],
                "creates-artifact",
            )
        ],
    )


def _run_artifacts(run) -> list[dict[str, Any]]:
    items = [artifact("run", run.result["id"], run.root_dir, immutable=True)]
    items.extend(
        artifact(
            item["kind"],
            f"{run.result['id']}:{item['path']}",
            run.root_dir / item["path"],
            immutable=True,
        )
        for item in run.result["artifacts"]
    )
    return items


def _run_execute(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    run = execute_study(project, args.study)
    metric = run.result["objective"]["metric"]
    value = run.result["metrics"].get(metric)
    return CommandResult(
        "run.execute",
        run.result,
        (
            f"Run {run.result['id']}: {run.result['status']}\n"
            f"Study: {run.result['study']['id']}\n"
            f"{metric}: {value if value is not None else 'unavailable'}\n"
            f"{run.result['summary']}\n"
        ),
        project_context(project),
        _run_artifacts(run),
        [
            next_action(
                "run.show",
                "Verify and inspect the immutable RunResult.",
                [
                    "aq",
                    "run",
                    "show",
                    str(project.root_dir),
                    "--run",
                    run.result["id"],
                    "--json",
                ],
                "read-only",
            ),
            next_action(
                "run.list",
                "List immutable Runs for this Study.",
                [
                    "aq",
                    "run",
                    "list",
                    str(project.root_dir),
                    "--study",
                    run.result["study"]["id"],
                    "--json",
                ],
                "read-only",
            ),
        ],
    )


def _run_list(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    if args.study:
        load_study(project, args.study)
    runs = list_runs(project, args.study)
    lines = [f"AutoQuant Runs in {project.manifest.name}:"]
    lines.extend(
        f"  {item.id}  {item.status}  {item.study_id}  "
        f"{item.primary_metric}="
        f"{item.primary_value if item.primary_value is not None else 'unavailable'}"
        for item in runs
    )
    if not runs:
        lines.append("  No Runs")
    actions = []
    if runs:
        actions.append(
            next_action(
                "run.show",
                "Inspect the latest listed immutable Run.",
                [
                    "aq",
                    "run",
                    "show",
                    str(project.root_dir),
                    "--run",
                    runs[-1].id,
                    "--json",
                ],
                "read-only",
            )
        )
    return CommandResult(
        "run.list",
        {"runs": [item.to_dict() for item in runs]},
        "\n".join(lines) + "\n",
        project_context(project),
        next_actions=actions,
    )


def _run_show(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    run = load_run(project, args.run)
    metric = run.result["objective"]["metric"]
    value = run.result["metrics"].get(metric)
    return CommandResult(
        "run.show",
        {"manifest": run.manifest, "result": run.result},
        (
            f"Immutable Run: {run.result['id']}\n"
            f"Status: {run.result['status']}\n"
            f"Study: {run.result['study']['id']}\n"
            f"{metric}: {value if value is not None else 'unavailable'}\n"
            f"Input hash: {run.result['inputHash']}\n"
        ),
        project_context(project),
        _run_artifacts(run),
    )


def _session_next_actions(project, session) -> list[dict[str, Any]]:
    actions = [
        next_action(
            "session.show",
            "Refresh the Session brief, candidate state, and Experiment history.",
            [
                "aq",
                "session",
                "show",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--json",
            ],
            "read-only",
        )
    ]
    if session.manifest["status"] == "active":
        actions.append(
            next_action(
                "experiment.evaluate",
                "After editing only the declared worktree closure, evaluate one hypothesis.",
                [
                    "aq",
                    "experiment",
                    "evaluate",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--hypothesis",
                    "Describe the candidate change",
                    "--json",
                ],
                "creates-artifact",
            )
        )
        if (
            session.manifest["leader"]["runId"]
            != session.manifest["baseline"]["runId"]
        ):
            actions.append(
                next_action(
                    "session.promote",
                    "Promote the exact current KEEP if the Project base is unchanged.",
                    [
                        "aq",
                        "session",
                        "promote",
                        str(project.root_dir),
                        "--session",
                        session.manifest["id"],
                        "--json",
                    ],
                    "mutates-project",
                )
            )
    return actions


def _session_start(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = start_session(project, args.study)
    data = session_snapshot(project, session)
    return CommandResult(
        "session.start",
        data,
        (
            f"Research Session: {session.manifest['id']}\n"
            f"Study: {session.manifest['studyId']}\n"
            f"Leader: {session.manifest['leader']['metric']}="
            f"{session.manifest['leader']['value']}\n"
            f"Worktree: {session.worktree_project.root_dir}\n"
            f"Editable: {', '.join(session.manifest['editablePaths'])}\n"
        ),
        project_context(project),
        [
            artifact(
                "session",
                session.manifest["id"],
                session.manifest_path,
                immutable=False,
            ),
            *_run_artifacts(session.baseline_run),
        ],
        _session_next_actions(project, session),
    )


def _session_list(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    sessions = list_sessions(project)
    lines = [f"AutoQuant Research Sessions in {project.manifest.name}:"]
    lines.extend(
        f"  {item.id}  {item.status}  {item.study_id}  "
        f"leader={item.leader_value}  experiments={item.experiments}"
        for item in sessions
    )
    if not sessions:
        lines.append("  No Sessions")
    actions = []
    if sessions:
        actions.append(
            next_action(
                "session.show",
                "Inspect the latest listed Session.",
                [
                    "aq",
                    "session",
                    "show",
                    str(project.root_dir),
                    "--session",
                    sessions[-1].id,
                    "--json",
                ],
                "read-only",
            )
        )
    return CommandResult(
        "session.list",
        {"sessions": [item.to_dict() for item in sessions]},
        "\n".join(lines) + "\n",
        project_context(project),
        next_actions=actions,
    )


def _session_show(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    data = session_snapshot(project, session)
    candidate = data["candidate"]
    return CommandResult(
        "session.show",
        data,
        (
            f"Research Session: {session.manifest['id']}\n"
            f"Status: {session.manifest['status']}\n"
            f"Study: {session.manifest['studyId']}\n"
            f"Leader: {session.manifest['leader']['metric']}="
            f"{session.manifest['leader']['value']}\n"
            f"Experiments: {len(data['experiments'])}\n"
            f"Authority: {'valid' if data['authority']['valid'] else 'stale'}\n"
            f"Candidate changed: "
            f"{candidate['differsFromLeader'] if candidate else 'invalid'}\n"
            f"Worktree: {session.worktree_project.root_dir}\n"
        ),
        project_context(project),
        [
            artifact(
                "session",
                session.manifest["id"],
                session.manifest_path,
                immutable=False,
            )
        ],
        _session_next_actions(project, session),
    )


def _session_promote(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    receipt = promote_session(project, args.session)
    session = load_session(project, args.session)
    receipt_path = session.root_dir / "promotion.json"
    return CommandResult(
        "session.promote",
        {"receipt": receipt, "session": session.manifest},
        (
            f"Promoted Session {session.manifest['id']}\n"
            f"Study: {session.manifest['studyId']}\n"
            f"Source: {receipt['beforeSourceHash']} -> "
            f"{receipt['afterSourceHash']}\n"
        ),
        project_context(project),
        [
            artifact(
                "promotion",
                receipt["id"],
                receipt_path,
                immutable=True,
            )
        ],
        [
            next_action(
                "run.execute",
                "Execute the promoted Project source through the fixed Study.",
                [
                    "aq",
                    "run",
                    "execute",
                    str(project.root_dir),
                    "--study",
                    session.manifest["studyId"],
                    "--json",
                ],
                "creates-artifact",
            )
        ],
    )


def _experiment_artifacts(project, experiment) -> list[dict[str, Any]]:
    run = load_run(project, experiment.result["candidate"]["runId"])
    return [
        artifact(
            "experiment",
            experiment.result["id"],
            experiment.root_dir,
            immutable=True,
        ),
        *_run_artifacts(run),
    ]


def _experiment_evaluate(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    experiment = evaluate_experiment(project, args.session, args.hypothesis)
    session = load_session(project, args.session)
    candidate = experiment.result["candidate"]
    return CommandResult(
        "experiment.evaluate",
        {
            "experiment": experiment.result,
            "changes": experiment.changes,
            "session": session_snapshot(project, session),
        },
        (
            f"Experiment {experiment.result['id']}: "
            f"{experiment.result['verdict']}\n"
            f"Hypothesis: {experiment.result['hypothesis']}\n"
            f"Leader: {experiment.result['leader']['value']}\n"
            f"Candidate: "
            f"{candidate['value'] if candidate['value'] is not None else 'failed'}\n"
            f"Improvement: "
            f"{experiment.result['improvement'] if experiment.result['improvement'] is not None else 'unavailable'}\n"
        ),
        project_context(project),
        _experiment_artifacts(project, experiment),
        _session_next_actions(project, session),
    )


def _experiment_list(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    experiments = list_experiments(project, session)
    lines = [f"Experiments in {session.manifest['id']}:"]
    lines.extend(
        f"  {item.id}  {item.verdict}  leader={item.leader_value}  "
        f"candidate={item.candidate_value if item.candidate_value is not None else 'failed'}"
        for item in experiments
    )
    if not experiments:
        lines.append("  No Experiments")
    actions = []
    if experiments:
        actions.append(
            next_action(
                "experiment.show",
                "Inspect the latest immutable Experiment.",
                [
                    "aq",
                    "experiment",
                    "show",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--experiment",
                    experiments[-1].id,
                    "--json",
                ],
                "read-only",
            )
        )
    return CommandResult(
        "experiment.list",
        {"experiments": [item.to_dict() for item in experiments]},
        "\n".join(lines) + "\n",
        project_context(project),
        next_actions=actions,
    )


def _experiment_show(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    experiment = load_experiment(project, session, args.experiment)
    return CommandResult(
        "experiment.show",
        {
            "manifest": experiment.manifest,
            "result": experiment.result,
            "changes": experiment.changes,
            "diffPath": str(experiment.root_dir / "diff.patch"),
        },
        (
            f"Immutable Experiment: {experiment.result['id']}\n"
            f"Verdict: {experiment.result['verdict']}\n"
            f"Hypothesis: {experiment.result['hypothesis']}\n"
            f"Candidate Run: {experiment.result['candidate']['runId']}\n"
        ),
        project_context(project),
        _experiment_artifacts(project, experiment),
        _session_next_actions(project, session),
    )


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
        kinds = [
            "experiment",
            "judge-output",
            "project",
            "run-result",
            "session",
            "study",
            "workspace",
        ]
        if args.kind is None:
            return CommandResult(
                "schema",
                {"kinds": kinds},
                "AutoQuant schema kinds:\n"
                + "".join(f"  {kind}\n" for kind in kinds),
            )
        schemas = {
            "study": STUDY_JSON_SCHEMA,
            "judge-output": JUDGE_OUTPUT_JSON_SCHEMA,
            "run-result": RUN_RESULT_JSON_SCHEMA,
            "session": SESSION_JSON_SCHEMA,
            "experiment": EXPERIMENT_JSON_SCHEMA,
        }
        schema = schemas.get(args.kind) or workspace_schema_for(args.kind)
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
    if args.command_id == "study.create":
        return _study_create(args)
    if args.command_id == "study.list":
        return _study_list(args)
    if args.command_id == "study.inspect":
        return _study_inspect(args)
    if args.command_id == "run.execute":
        return _run_execute(args)
    if args.command_id == "run.list":
        return _run_list(args)
    if args.command_id == "run.show":
        return _run_show(args)
    if args.command_id == "session.start":
        return _session_start(args)
    if args.command_id == "session.list":
        return _session_list(args)
    if args.command_id == "session.show":
        return _session_show(args)
    if args.command_id == "session.promote":
        return _session_promote(args)
    if args.command_id == "experiment.evaluate":
        return _experiment_evaluate(args)
    if args.command_id == "experiment.list":
        return _experiment_list(args)
    if args.command_id == "experiment.show":
        return _experiment_show(args)
    raise CliUsageError(f"Unknown command: {args.command_id}")


def _command_id(argv: Sequence[str]) -> str:
    if not argv:
        return "help"
    if argv[0] in {
        "workspace",
        "project",
        "study",
        "run",
        "session",
        "experiment",
    } and len(argv) > 1:
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
