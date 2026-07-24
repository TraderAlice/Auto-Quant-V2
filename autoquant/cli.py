"""Human- and Agent-facing AutoQuant command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Sequence

from .briefs import RESEARCH_REQUEST_JSON_SCHEMA, load_research_request
from .capabilities import CLI_COMMANDS
from .decision_matrix import (
    DEFAULT_COMPARISON_TRIALS,
    MAX_COMPARISON_TRIALS,
    MIN_COMPARISON_TRIALS,
    SESSION_DECISION_MATRIX_JSON_SCHEMA,
    load_session_decision_matrix,
)
from .factor_explorer import (
    DEFAULT_FACTOR_POINTS,
    FACTOR_DIAGNOSTICS_JSON_SCHEMA,
    MAX_FACTOR_POINTS,
    MIN_FACTOR_POINTS,
    load_factor_diagnostics,
)
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
from .research import (
    CAMPAIGN_PROGRESS_JSON_SCHEMA,
    CAMPAIGN_RESULT_JSON_SCHEMA,
    RESEARCHER_RESPONSE_JSON_SCHEMA,
    list_campaigns,
    load_campaign,
    run_campaign,
)
from .reports import (
    REPORT_ANALYSIS_JSON_SCHEMA,
    list_reports,
    load_report,
    load_report_analysis,
    publish_report,
)
from .intake import (
    INTAKE_TEMPLATE_REQUIREMENTS,
    OHLCV_DATASET_PACKAGE_JSON_SCHEMA,
    PROJECT_INTAKE,
    PROJECT_REQUEST,
    DATASET_SNAPSHOT,
    load_project_intake,
    prepare_project_intake,
)
from .portfolio_explorer import (
    DEFAULT_PORTFOLIO_POINTS,
    MAX_PORTFOLIO_POINTS,
    MIN_PORTFOLIO_POINTS,
    PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA,
    load_portfolio_diagnostics,
)
from .rl_explorer import (
    DEFAULT_RL_POINTS,
    MAX_RL_POINTS,
    MIN_RL_POINTS,
    RL_DIAGNOSTICS_JSON_SCHEMA,
    load_rl_diagnostics,
)
from .research_program import (
    RESEARCH_PROGRAM_MANIFEST,
    RESEARCH_PROGRAM_STATUS_JSON_SCHEMA,
    RESEARCH_DESK_TEMPLATE,
    load_research_program,
)
from .studio import STUDIO_SNAPSHOT_JSON_SCHEMA, build_studio_snapshot, serve_studio
from .templates import (
    PROJECT_TEMPLATE_IDS,
    TEMPLATE_STUDY_IDS,
    TEMPLATE_STUDY_SEQUENCES,
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
            "factor-diagnostics",
            "portfolio-diagnostics",
            "research-program-status",
            "rl-policy-diagnostics",
            "session-decision-matrix",
            "session",
            "experiment",
            "researcher-response",
            "campaign-result",
            "campaign-progress",
            "research-request",
            "ohlcv-dataset-package",
            "report-analysis",
            "studio-snapshot",
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
    project_create.add_argument(
        "--template",
        choices=PROJECT_TEMPLATE_IDS,
        default="blank",
    )
    project_create.set_defaults(command_id="project.create")
    _json_argument(project_create)

    project_intake = project_actions.add_parser(
        "intake",
        help="create a Project from a research request and OHLCV package",
    )
    project_intake.add_argument("workspace")
    project_intake.add_argument("project_id")
    project_intake.add_argument("--request", required=True)
    project_intake.add_argument("--dataset", required=True)
    project_intake.add_argument(
        "--template",
        choices=tuple(INTAKE_TEMPLATE_REQUIREMENTS),
        default=RESEARCH_DESK_TEMPLATE,
    )
    project_intake.add_argument("--name")
    project_intake.set_defaults(command_id="project.intake")
    _json_argument(project_intake)

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

    project_program = project_actions.add_parser(
        "program",
        help="inspect one verified multi-Study research program",
    )
    project_program.add_argument("path")
    project_program.add_argument("--project")
    project_program.set_defaults(command_id="project.program")
    _json_argument(project_program)

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
    study_create.add_argument(
        "--dataset-path",
        action="append",
        help="repeatable Project-data-relative file or trailing /** closure",
    )
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

    run_factor = run_actions.add_parser(
        "factor",
        help="inspect bounded Factor Run professional diagnostics",
    )
    run_factor.add_argument("path")
    run_factor.add_argument("--project")
    run_factor.add_argument("--run", required=True)
    run_factor.add_argument(
        "--points",
        type=int,
        choices=range(MIN_FACTOR_POINTS, MAX_FACTOR_POINTS + 1),
        default=DEFAULT_FACTOR_POINTS,
        metavar=f"{MIN_FACTOR_POINTS}..{MAX_FACTOR_POINTS}",
    )
    run_factor.set_defaults(command_id="run.factor")
    _json_argument(run_factor)

    run_portfolio = run_actions.add_parser(
        "portfolio",
        help="inspect bounded Portfolio Run decision diagnostics",
    )
    run_portfolio.add_argument("path")
    run_portfolio.add_argument("--project")
    run_portfolio.add_argument("--run", required=True)
    run_portfolio.add_argument(
        "--points",
        type=int,
        choices=range(MIN_PORTFOLIO_POINTS, MAX_PORTFOLIO_POINTS + 1),
        default=DEFAULT_PORTFOLIO_POINTS,
        metavar=f"{MIN_PORTFOLIO_POINTS}..{MAX_PORTFOLIO_POINTS}",
    )
    run_portfolio.set_defaults(command_id="run.portfolio")
    _json_argument(run_portfolio)

    run_rl = run_actions.add_parser(
        "rl",
        help="inspect bounded governed RL policy evidence",
    )
    run_rl.add_argument("path")
    run_rl.add_argument("--project")
    run_rl.add_argument("--run", required=True)
    run_rl.add_argument(
        "--points",
        type=int,
        choices=range(MIN_RL_POINTS, MAX_RL_POINTS + 1),
        default=DEFAULT_RL_POINTS,
        metavar=f"{MIN_RL_POINTS}..{MAX_RL_POINTS}",
    )
    run_rl.set_defaults(command_id="run.rl")
    _json_argument(run_rl)

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
    session_start.add_argument(
        "--request",
        help="strict delegated research-request JSON to bind into the Session",
    )
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

    session_compare = session_actions.add_parser(
        "compare",
        help="compare bounded verified Session trials across metric layers",
    )
    session_compare.add_argument("path")
    session_compare.add_argument("--project")
    session_compare.add_argument("--session", required=True)
    session_compare.add_argument(
        "--trials",
        type=int,
        choices=range(
            MIN_COMPARISON_TRIALS,
            MAX_COMPARISON_TRIALS + 1,
        ),
        default=DEFAULT_COMPARISON_TRIALS,
        metavar=f"{MIN_COMPARISON_TRIALS}..{MAX_COMPARISON_TRIALS}",
    )
    session_compare.set_defaults(command_id="session.compare")
    _json_argument(session_compare)

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

    research = subcommands.add_parser(
        "research",
        help="drive and inspect bounded external Researcher Campaigns",
    )
    research_actions = research.add_subparsers(
        dest="research_action",
        required=True,
    )
    research_run = research_actions.add_parser(
        "run",
        help="run one bounded provider-neutral Researcher Campaign",
    )
    research_run.add_argument("path")
    research_run.add_argument("--project")
    research_run.add_argument("--session", required=True)
    research_run.add_argument("--agent-command", required=True)
    research_run.add_argument("--max-turns", type=int, default=5)
    research_run.add_argument("--max-wall-seconds", type=int, default=900)
    research_run.add_argument("--turn-timeout-seconds", type=int, default=300)
    research_run.set_defaults(command_id="research.run")
    _json_argument(research_run)

    research_list = research_actions.add_parser(
        "list",
        help="list immutable Campaigns in one Session",
    )
    research_list.add_argument("path")
    research_list.add_argument("--project")
    research_list.add_argument("--session", required=True)
    research_list.set_defaults(command_id="research.list")
    _json_argument(research_list)

    research_show = research_actions.add_parser(
        "show",
        help="verify and inspect one immutable Campaign",
    )
    research_show.add_argument("path")
    research_show.add_argument("--project")
    research_show.add_argument("--session", required=True)
    research_show.add_argument("--campaign", required=True)
    research_show.set_defaults(command_id="research.show")
    _json_argument(research_show)

    report = subcommands.add_parser(
        "report",
        help="publish and inspect immutable evidence-bound Research Reports",
    )
    report_actions = report.add_subparsers(dest="report_action", required=True)
    report_publish = report_actions.add_parser(
        "publish",
        help="publish Agent-authored analysis over verified Session evidence",
    )
    report_publish.add_argument("path")
    report_publish.add_argument("--project")
    report_publish.add_argument("--session", required=True)
    report_publish.add_argument("--analysis", required=True)
    report_publish.set_defaults(command_id="report.publish")
    _json_argument(report_publish)

    report_list = report_actions.add_parser(
        "list",
        help="list immutable Research Reports in one Session",
    )
    report_list.add_argument("path")
    report_list.add_argument("--project")
    report_list.add_argument("--session", required=True)
    report_list.set_defaults(command_id="report.list")
    _json_argument(report_list)

    report_show = report_actions.add_parser(
        "show",
        help="verify and inspect one immutable Research Report",
    )
    report_show.add_argument("path")
    report_show.add_argument("--project")
    report_show.add_argument("--session", required=True)
    report_show.add_argument("--report", required=True)
    report_show.set_defaults(command_id="report.show")
    _json_argument(report_show)

    studio = subcommands.add_parser(
        "studio",
        help="observe verified Workspace research in CLI JSON or a local web UI",
    )
    studio_actions = studio.add_subparsers(dest="studio_action", required=True)
    studio_snapshot = studio_actions.add_parser(
        "snapshot",
        help="emit one verified read-only Studio snapshot",
    )
    studio_snapshot.add_argument("path")
    studio_snapshot.add_argument("--project")
    studio_snapshot.set_defaults(command_id="studio.snapshot")
    _json_argument(studio_snapshot)

    studio_serve = studio_actions.add_parser(
        "serve",
        help="serve the local read-only AutoQuant Studio",
    )
    studio_serve.add_argument("path")
    studio_serve.add_argument("--project")
    studio_serve.add_argument("--host", default="127.0.0.1")
    studio_serve.add_argument("--port", type=int, default=8765)
    studio_serve.add_argument("--no-open", action="store_true")
    studio_serve.set_defaults(command_id="studio.serve")
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
        template=args.template,
    )
    program = None
    if args.template == RESEARCH_DESK_TEMPLATE:
        program = load_research_program(project)
        assert program is not None
        next_actions = [
            next_action(
                "project.program",
                "Inspect the coordinated Factor, Portfolio, and RL lanes.",
                [
                    "aq",
                    "project",
                    "program",
                    str(project.root_dir),
                    "--json",
                ],
                "read-only",
            ),
        ]
        if program["recommendedAction"] is not None:
            action = program["recommendedAction"]
            next_actions.append(
                next_action(
                    action["id"],
                    action["description"],
                    action["argv"],
                    action["effect"],
                )
            )
    elif args.template != "blank":
        study_id = TEMPLATE_STUDY_IDS[args.template]
        next_actions = [
            next_action(
                "study.inspect",
                "Inspect the fixed reference Study and content identity.",
                [
                    "aq",
                    "study",
                    "inspect",
                    str(project.root_dir),
                    "--study",
                    study_id,
                    "--json",
                ],
                "read-only",
            ),
            next_action(
                "run.execute",
                "Execute the bounded reference baseline.",
                [
                    "aq",
                    "run",
                    "execute",
                    str(project.root_dir),
                    "--study",
                    study_id,
                    "--json",
                ],
                "creates-artifact",
            ),
        ]
    else:
        next_actions = [
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
        ]
    artifacts = [
        artifact(
            "project",
            project.manifest.id,
            project.root_dir / PROJECT_MANIFEST,
            immutable=False,
        )
    ]
    if program is not None:
        artifacts.append(
            artifact(
                "research-program",
                program["manifest"]["id"],
                project.root_dir / RESEARCH_PROGRAM_MANIFEST,
                immutable=False,
            )
        )
    return CommandResult(
        "project.create",
        {
            "projectDir": str(project.root_dir),
            "manifest": project.manifest.to_dict(),
            "template": args.template,
        },
        f"Created AutoQuant Project '{project.manifest.id}' at {project.root_dir}\n",
        project_context(project),
        artifacts,
        next_actions,
    )


def _project_intake(args: argparse.Namespace) -> CommandResult:
    prepared = prepare_project_intake(
        args.request,
        args.dataset,
        args.template,
    )
    project = create_project(
        args.workspace,
        args.project_id,
        name=args.name or prepared.request["title"],
        description=prepared.request["question"],
        template=args.template,
        template_intake=prepared,
    )
    intake = load_project_intake(project)
    assert intake is not None
    study_id = intake["study"]["id"]
    request_path = project.root_dir / PROJECT_REQUEST
    program = load_research_program(project, optional=True)
    if program is not None:
        next_actions = [
            next_action(
                "project.program",
                "Inspect the coordinated Factor, Portfolio, and RL research lanes.",
                [
                    "aq",
                    "project",
                    "program",
                    str(project.root_dir),
                    "--json",
                ],
                "read-only",
            ),
        ]
        if program["recommendedAction"] is not None:
            action = program["recommendedAction"]
            next_actions.append(
                next_action(
                    action["id"],
                    action["description"],
                    action["argv"],
                    action["effect"],
                )
            )
    else:
        next_actions = [
            next_action(
                "study.inspect",
                "Inspect the fixed Study and content-locked market snapshot.",
                [
                    "aq",
                    "study",
                    "inspect",
                    str(project.root_dir),
                    "--study",
                    study_id,
                    "--json",
                ],
                "read-only",
            ),
            next_action(
                "run.execute",
                "Execute the bounded real-data baseline.",
                [
                    "aq",
                    "run",
                    "execute",
                    str(project.root_dir),
                    "--study",
                    study_id,
                    "--json",
                ],
                "creates-artifact",
            ),
            next_action(
                "session.start",
                "Start delegated research with the preserved request.",
                [
                    "aq",
                    "session",
                    "start",
                    str(project.root_dir),
                    "--study",
                    study_id,
                    "--request",
                    str(request_path),
                    "--json",
                ],
                "creates-artifact",
            ),
        ]
    artifacts = [
        artifact(
            "project",
            project.manifest.id,
            project.root_dir / PROJECT_MANIFEST,
            immutable=False,
        ),
        artifact(
            "research-request",
            prepared.request_hash,
            request_path,
            immutable=False,
        ),
        artifact(
            "dataset-snapshot",
            intake["manifest"]["datasetSnapshotHash"],
            project.root_dir / DATASET_SNAPSHOT,
            immutable=False,
        ),
        artifact(
            "project-intake",
            project.manifest.id,
            project.root_dir / PROJECT_INTAKE,
            immutable=False,
        ),
    ]
    if program is not None:
        artifacts.append(
            artifact(
                "research-program",
                program["manifest"]["id"],
                project.root_dir / RESEARCH_PROGRAM_MANIFEST,
                immutable=False,
            )
        )
    return CommandResult(
        "project.intake",
        {
            "projectDir": str(project.root_dir),
            "manifest": project.manifest.to_dict(),
            "intake": intake,
        },
        (
            f"Created request-driven Project '{project.manifest.id}'\n"
            f"Request: {prepared.request['title']}\n"
            f"Dataset: {prepared.package['id']}@{prepared.package['version']} · "
            f"{len(prepared.assets)} assets · {prepared.start}..{prepared.end}\n"
            f"Studies: {len(TEMPLATE_STUDY_SEQUENCES[args.template])} · "
            f"primary {study_id}\n"
        ),
        project_context(project),
        artifacts,
        next_actions,
    )


def _project_program(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    program = load_research_program(project)
    assert program is not None
    lane_lines = [
        f"  {lane['id']}: {lane['phase']} · "
        f"{lane['study']['objective']['metric']}"
        for lane in program["lanes"]
    ]
    actions = []
    if program["recommendedAction"] is not None:
        action = program["recommendedAction"]
        actions.append(
            next_action(
                action["id"],
                action["description"],
                action["argv"],
                action["effect"],
            )
        )
    return CommandResult(
        "project.program",
        program,
        (
            f"Research program: {program['project']['name']}\n"
            + "\n".join(lane_lines)
            + "\n"
            + (
                f"Recommended: {program['recommendedAction']['display']}\n"
                if program["recommendedAction"] is not None
                else "Recommended: no pending lane action\n"
            )
        ),
        project_context(project),
        [
            artifact(
                "research-program",
                program["manifest"]["id"],
                project.root_dir / RESEARCH_PROGRAM_MANIFEST,
                immutable=False,
            )
        ],
        actions,
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
            args.dataset_path,
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
            "datasetSourceHashes": study.dataset_hashes,
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
    actions = [
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
    ]
    if (
        run.result["status"] == "succeeded"
        and metric == "validation_mean_ic"
    ):
        actions.append(
            next_action(
                "run.factor",
                "Inspect the verified professional Factor tear sheet.",
                [
                    "aq",
                    "run",
                    "factor",
                    str(project.root_dir),
                    "--run",
                    run.result["id"],
                    "--json",
                ],
                "read-only",
            )
        )
    if (
        run.result["status"] == "succeeded"
        and metric == "validation_mean_net_sharpe"
    ):
        actions.append(
            next_action(
                "run.rl",
                "Inspect the verified governed RL policy evidence.",
                [
                    "aq",
                    "run",
                    "rl",
                    str(project.root_dir),
                    "--run",
                    run.result["id"],
                    "--json",
                ],
                "read-only",
            )
        )
    actions.append(
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
        )
    )
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
        actions,
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


def _run_factor(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    diagnostics = load_factor_diagnostics(
        project,
        args.run,
        point_limit=args.points,
    )
    summary = diagnostics["summary"]
    validation = summary["validation"]
    return CommandResult(
        "run.factor",
        diagnostics,
        (
            f"Factor Run: {diagnostics['run']['id']}\n"
            f"Selection mean rank IC: {validation['meanRankIc']}\n"
            f"HAC t / p: {validation['hacTStatistic']} / "
            f"{validation['hacNormalPValue']}\n"
            f"IC path: {diagnostics['icPath']['totalRows']} rows → "
            f"{diagnostics['icPath']['sampledRows']} points\n"
            f"Mean coverage / rank turnover: {summary['meanCoverage']} / "
            f"{summary['meanRankTurnover']}\n"
            "Test and longer-horizon evidence are diagnostic only.\n"
        ),
        project_context(project),
        [
            artifact(
                kind,
                f"{diagnostics['run']['id']}:{kind}",
                project.root_dir
                / project.manifest.directories["runs"]
                / diagnostics["run"]["id"]
                / item["path"],
                immutable=True,
            )
            for kind, item in diagnostics["artifacts"].items()
        ],
    )


def _run_portfolio(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    diagnostics = load_portfolio_diagnostics(
        project,
        args.run,
        point_limit=args.points,
    )
    summary = diagnostics["path"]["summary"]
    book = diagnostics["currentBook"]
    return CommandResult(
        "run.portfolio",
        diagnostics,
        (
            f"Portfolio Run: {diagnostics['run']['id']}\n"
            f"Selection: {diagnostics['run']['primaryMetric']}="
            f"{diagnostics['run']['primaryValue']}\n"
            f"Path: {diagnostics['path']['totalRows']} rows → "
            f"{diagnostics['path']['sampledRows']} points\n"
            f"Net total return: {summary['netTotalReturn']}\n"
            f"Maximum drawdown: {summary['maximumDrawdown']} at "
            f"{summary['maximumDrawdownAt']}\n"
            f"Latest historical book: {book['timestamp']} · "
            f"gross {book['grossExposure']} · net {book['netExposure']}\n"
        ),
        project_context(project),
        [
            artifact(
                kind,
                f"{diagnostics['run']['id']}:{kind}",
                project.root_dir
                / project.manifest.directories["runs"]
                / diagnostics["run"]["id"]
                / item["path"],
                immutable=True,
            )
            for kind, item in diagnostics["artifacts"].items()
        ],
    )


def _run_rl(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    diagnostics = load_rl_diagnostics(
        project,
        args.run,
        point_limit=args.points,
    )
    summary = diagnostics["summary"]
    return CommandResult(
        "run.rl",
        diagnostics,
        (
            f"RL policy Run: {diagnostics['run']['id']}\n"
            f"Validation mean / minimum net Sharpe: "
            f"{summary['validation']['mean']} / "
            f"{summary['validation']['minimum']}\n"
            f"Validation advantage versus best baseline: "
            f"{summary['meanValidationAdvantageVsBestBaseline']}\n"
            f"Trials / failure rate: {summary['trialCount']} / "
            f"{summary['failureRate']}\n"
            f"Action path: {diagnostics['actionPath']['totalRows']} rows → "
            f"{diagnostics['actionPath']['sampledRows']} points\n"
            "Test evidence is visible audit only; actions have no trading authority.\n"
        ),
        project_context(project),
        [
            artifact(
                kind,
                f"{diagnostics['run']['id']}:{kind}",
                project.root_dir
                / project.manifest.directories["runs"]
                / diagnostics["run"]["id"]
                / item["path"],
                immutable=True,
            )
            for kind, item in diagnostics["artifacts"].items()
        ],
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
        ),
        next_action(
            "session.compare",
            "Compare baseline, candidates, and leader across verified metric layers.",
            [
                "aq",
                "session",
                "compare",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--json",
            ],
            "read-only",
        ),
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
    if session.delegation is not None:
        actions.append(
            next_action(
                "report.publish",
                "Publish strict analysis over the current verified Session evidence.",
                [
                    "aq",
                    "report",
                    "publish",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--analysis",
                    "report-analysis.json",
                    "--json",
                ],
                "creates-artifact",
            )
        )
    return actions


def _session_start(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    request = load_research_request(args.request) if args.request else None
    session = start_session(project, args.study, request=request)
    data = session_snapshot(project, session)
    delegation_line = (
        f"Request: {session.delegation['request']['title']}\n"
        if session.delegation is not None
        else ""
    )
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
            f"{delegation_line}"
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
            *(
                [
                    artifact(
                        "research-request",
                        session.manifest["brief"]["requestHash"],
                        session.root_dir / "request.json",
                        immutable=True,
                    ),
                    artifact(
                        "research-brief",
                        session.manifest["brief"]["id"],
                        session.root_dir / "brief.json",
                        immutable=True,
                    ),
                ]
                if session.delegation is not None
                else []
            ),
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


def _session_compare(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    matrix = load_session_decision_matrix(
        project,
        args.session,
        trial_limit=args.trials,
    )
    tradeoffs = matrix["tradeoffs"]
    return CommandResult(
        "session.compare",
        matrix,
        (
            f"Session decision matrix: {matrix['session']['id']}\n"
            f"Family: {matrix['metricFamily']} · "
            f"{len(matrix['metrics'])} metrics\n"
            f"Trials: {matrix['scope']['displayedCandidateTrials']}/"
            f"{matrix['scope']['totalCandidateTrials']} candidates "
            f"+ baseline\n"
            f"Leader: {matrix['session']['leaderRunId']}\n"
            f"Leader vs baseline: {len(tradeoffs['leaderVsBaseline']['improved'])} "
            f"better · {len(tradeoffs['leaderVsBaseline']['regressed'])} worse\n"
            f"Displayed non-dominated Runs: "
            f"{', '.join(tradeoffs['nonDominatedRunIds'])}\n"
        ),
        project_context(project),
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


def _campaign_artifact(campaign) -> dict[str, Any]:
    return artifact(
        "campaign",
        campaign.result["id"],
        campaign.root_dir,
        immutable=True,
    )


def _research_run(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    campaign = run_campaign(
        project,
        args.session,
        args.agent_command,
        max_turns=args.max_turns,
        max_wall_seconds=args.max_wall_seconds,
        turn_timeout_seconds=args.turn_timeout_seconds,
    )
    session = load_session(project, args.session)
    return CommandResult(
        "research.run",
        {
            "manifest": campaign.manifest,
            "result": campaign.result,
            "session": session_snapshot(project, session),
        },
        (
            f"Research Campaign: {campaign.result['id']}\n"
            f"Status: {campaign.result['status']}\n"
            f"Reason: {campaign.result['reason']}\n"
            f"Turns: {campaign.result['turnsCompleted']}/"
            f"{campaign.result['budget']['maxTurns']}\n"
            f"Experiments: {len(campaign.result['experiments'])}\n"
            f"Verdicts: "
            f"KEEP={campaign.result['verdicts']['KEEP']} "
            f"REVERT={campaign.result['verdicts']['REVERT']} "
            f"CRASH={campaign.result['verdicts']['CRASH']}\n"
        ),
        project_context(project),
        [_campaign_artifact(campaign)],
        [
            next_action(
                "research.show",
                "Verify and inspect this immutable Campaign.",
                [
                    "aq",
                    "research",
                    "show",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--campaign",
                    campaign.result["id"],
                    "--json",
                ],
                "read-only",
            )
        ],
    )


def _research_list(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    campaigns = list_campaigns(project, session)
    lines = [f"Research Campaigns in {session.manifest['id']}:"]
    lines.extend(
        f"  {item.id}  {item.status}  turns={item.turns_completed}  "
        f"experiments={item.experiments}"
        for item in campaigns
    )
    if not campaigns:
        lines.append("  No Campaigns")
    actions = []
    if campaigns:
        actions.append(
            next_action(
                "research.show",
                "Verify and inspect the latest immutable Campaign.",
                [
                    "aq",
                    "research",
                    "show",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--campaign",
                    campaigns[-1].id,
                    "--json",
                ],
                "read-only",
            )
        )
    return CommandResult(
        "research.list",
        {"campaigns": [item.to_dict() for item in campaigns]},
        "\n".join(lines) + "\n",
        project_context(project),
        next_actions=actions,
    )


def _research_show(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    campaign = load_campaign(project, session, args.campaign)
    turns = sorted(
        str(path)
        for path in (campaign.root_dir / "turns").iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )
    return CommandResult(
        "research.show",
        {
            "manifest": campaign.manifest,
            "result": campaign.result,
            "turnPaths": turns,
        },
        (
            f"Immutable Research Campaign: {campaign.result['id']}\n"
            f"Status: {campaign.result['status']}\n"
            f"Reason: {campaign.result['reason']}\n"
            f"Turns: {campaign.result['turnsCompleted']}\n"
            f"Experiments: {len(campaign.result['experiments'])}\n"
        ),
        project_context(project),
        [_campaign_artifact(campaign)],
    )


def _report_artifacts(report) -> list[dict[str, Any]]:
    return [
        artifact(
            "research-report",
            report.report["id"],
            report.root_dir / "report.json",
            immutable=True,
        ),
        artifact(
            "research-report-markdown",
            report.report["id"],
            report.root_dir / "report.md",
            immutable=True,
        ),
    ]


def _report_publish(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    analysis = load_report_analysis(args.analysis)
    report = publish_report(project, args.session, analysis)
    return CommandResult(
        "report.publish",
        {
            "manifest": report.manifest,
            "report": report.report,
            "markdownPath": str(report.root_dir / "report.md"),
        },
        (
            f"Research Report: {report.report['id']}\n"
            f"Title: {report.analysis['title']}\n"
            f"Session: {report.report['sessionId']}\n"
            f"Leader: {report.report['evidence']['session']['leader']['runId']}\n"
            f"Markdown: {report.root_dir / 'report.md'}\n"
            "Authority: quantitative decision support; trading authority: none\n"
        ),
        project_context(project),
        _report_artifacts(report),
        [
            next_action(
                "report.show",
                "Verify the immutable report before OpenAlice Inbox publication.",
                [
                    "aq",
                    "report",
                    "show",
                    str(project.root_dir),
                    "--session",
                    report.report["sessionId"],
                    "--report",
                    report.report["id"],
                    "--json",
                ],
                "read-only",
            )
        ],
    )


def _report_list(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    reports = list_reports(project, session)
    lines = [f"Research Reports in {session.manifest['id']}:"]
    lines.extend(
        f"  {item.id}  {item.title}  findings={item.findings}  "
        f"recommendations={item.recommendations}"
        for item in reports
    )
    if not reports:
        lines.append("  No Research Reports")
    actions = []
    if reports:
        actions.append(
            next_action(
                "report.show",
                "Verify and inspect the latest immutable Research Report.",
                [
                    "aq",
                    "report",
                    "show",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--report",
                    reports[-1].id,
                    "--json",
                ],
                "read-only",
            )
        )
    return CommandResult(
        "report.list",
        {"reports": [item.to_dict() for item in reports]},
        "\n".join(lines) + "\n",
        project_context(project),
        next_actions=actions,
    )


def _report_show(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    session = load_session(project, args.session)
    report = load_report(project, session, args.report)
    return CommandResult(
        "report.show",
        {
            "manifest": report.manifest,
            "report": report.report,
            "markdownPath": str(report.root_dir / "report.md"),
        },
        (
            f"Immutable Research Report: {report.report['id']}\n"
            f"Title: {report.analysis['title']}\n"
            f"Session: {report.report['sessionId']}\n"
            f"Findings: {len(report.analysis['findings'])}\n"
            f"Markdown: {report.root_dir / 'report.md'}\n"
        ),
        project_context(project),
        _report_artifacts(report),
    )


def _studio_snapshot(args: argparse.Namespace) -> CommandResult:
    snapshot = build_studio_snapshot(args.path, project_id=args.project)
    source = snapshot["source"]
    context = (
        workspace_context(load_workspace(source["rootDir"]))
        if source["scope"] == "workspace"
        else project_context(load_project(source["rootDir"]))
    )
    lines = [
        f"AutoQuant Studio snapshot: {source['scope']}",
        f"Projects: {len(snapshot['projects'])}",
        f"Evidence: {'valid' if snapshot['valid'] else 'attention required'}",
    ]
    lines.extend(
        f"  {project['id']}  studies={project['counts']['studies']}  "
        f"runs={project['counts']['runs']}  "
        f"active={project['counts']['activeSessions']}  "
        f"running={project['counts']['runningCampaigns']}"
        for project in snapshot["projects"]
    )
    return CommandResult(
        "studio.snapshot",
        snapshot,
        "\n".join(lines) + "\n",
        context,
        next_actions=[
            next_action(
                "studio.serve",
                "Open the same verified snapshot in the local read-only Studio.",
                [
                    "aq",
                    "studio",
                    "serve",
                    source["rootDir"],
                    *(
                        ["--project", args.project]
                        if args.project is not None
                        else []
                    ),
                ],
                "long-running-server",
            )
        ],
    )


def _studio_serve(args: argparse.Namespace) -> CommandResult:
    serve_studio(
        args.path,
        project_id=args.project,
        host=args.host,
        port=args.port,
        open_browser=not args.no_open,
    )
    return CommandResult(
        "studio.serve",
        {"stopped": True},
        "AutoQuant Studio stopped.\n",
    )


def _validate(args: argparse.Namespace) -> CommandResult:
    project = _selected_project(args)
    intake = load_project_intake(project)
    return CommandResult(
        "validate",
        {
            "valid": True,
            "project": {
                "id": project.manifest.id,
                "name": project.manifest.name,
                "rootDir": str(project.root_dir),
            },
            "intake": intake,
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
    data["intake"] = load_project_intake(project)
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
            "campaign-progress",
            "campaign-result",
            "experiment",
            "factor-diagnostics",
            "judge-output",
            "ohlcv-dataset-package",
            "portfolio-diagnostics",
            "research-program-status",
            "rl-policy-diagnostics",
            "session-decision-matrix",
            "project",
            "report-analysis",
            "research-request",
            "researcher-response",
            "run-result",
            "session",
            "study",
            "studio-snapshot",
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
            "factor-diagnostics": FACTOR_DIAGNOSTICS_JSON_SCHEMA,
            "portfolio-diagnostics": PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA,
            "research-program-status": RESEARCH_PROGRAM_STATUS_JSON_SCHEMA,
            "rl-policy-diagnostics": RL_DIAGNOSTICS_JSON_SCHEMA,
            "session-decision-matrix": SESSION_DECISION_MATRIX_JSON_SCHEMA,
            "session": SESSION_JSON_SCHEMA,
            "experiment": EXPERIMENT_JSON_SCHEMA,
            "researcher-response": RESEARCHER_RESPONSE_JSON_SCHEMA,
            "campaign-result": CAMPAIGN_RESULT_JSON_SCHEMA,
            "campaign-progress": CAMPAIGN_PROGRESS_JSON_SCHEMA,
            "research-request": RESEARCH_REQUEST_JSON_SCHEMA,
            "ohlcv-dataset-package": OHLCV_DATASET_PACKAGE_JSON_SCHEMA,
            "report-analysis": REPORT_ANALYSIS_JSON_SCHEMA,
            "studio-snapshot": STUDIO_SNAPSHOT_JSON_SCHEMA,
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
    if args.command_id == "project.intake":
        return _project_intake(args)
    if args.command_id == "project.list":
        return _project_list(args)
    if args.command_id == "project.default":
        return _project_default(args)
    if args.command_id == "project.program":
        return _project_program(args)
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
    if args.command_id == "run.factor":
        return _run_factor(args)
    if args.command_id == "run.portfolio":
        return _run_portfolio(args)
    if args.command_id == "run.rl":
        return _run_rl(args)
    if args.command_id == "session.start":
        return _session_start(args)
    if args.command_id == "session.list":
        return _session_list(args)
    if args.command_id == "session.show":
        return _session_show(args)
    if args.command_id == "session.compare":
        return _session_compare(args)
    if args.command_id == "session.promote":
        return _session_promote(args)
    if args.command_id == "experiment.evaluate":
        return _experiment_evaluate(args)
    if args.command_id == "experiment.list":
        return _experiment_list(args)
    if args.command_id == "experiment.show":
        return _experiment_show(args)
    if args.command_id == "research.run":
        return _research_run(args)
    if args.command_id == "research.list":
        return _research_list(args)
    if args.command_id == "research.show":
        return _research_show(args)
    if args.command_id == "report.publish":
        return _report_publish(args)
    if args.command_id == "report.list":
        return _report_list(args)
    if args.command_id == "report.show":
        return _report_show(args)
    if args.command_id == "studio.snapshot":
        return _studio_snapshot(args)
    if args.command_id == "studio.serve":
        return _studio_serve(args)
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
        "research",
        "report",
        "studio",
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
        if getattr(parsed, "json", False):
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
