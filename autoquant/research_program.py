"""Verified orchestration status for one canonical multi-Study Project."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

from .intake import PROJECT_REQUEST, load_project_intake
from .reports import list_reports
from .runs import list_runs, load_run
from .sessions import list_sessions, load_session
from .studies import load_study
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
)


RESEARCH_PROGRAM_MANIFEST = "research-program.json"
RESEARCH_PROGRAM_KIND = "autoquant-research-program"
RESEARCH_PROGRAM_STATUS_KIND = "autoquant-research-program-status"
RESEARCH_PROGRAM_ID = "factor-portfolio-rl"
RESEARCH_DESK_TEMPLATE = "ohlcv-research-desk"
CANONICAL_LANES: tuple[dict[str, Any], ...] = (
    {
        "id": "factor",
        "name": "Factor quality",
        "studyId": "ohlcv-factor-quality",
        "role": "causal-predictive-evidence",
        "dependsOn": [],
        "editablePaths": ["factors/**"],
        "optional": False,
    },
    {
        "id": "portfolio",
        "name": "Portfolio implementation",
        "studyId": "ohlcv-portfolio-quality",
        "role": "mechanical-portfolio-evidence",
        "dependsOn": ["factor"],
        "editablePaths": ["factors/**"],
        "optional": False,
    },
    {
        "id": "rl",
        "name": "Governed RL value-add",
        "studyId": "ohlcv-rl-factor-policy",
        "role": "adaptive-policy-challenge",
        "dependsOn": ["portfolio"],
        "editablePaths": ["models/**"],
        "optional": True,
    },
)
INTEGRATION = {
    "factorToPortfolio": "shared-candidate-source",
    "rlFactorDependency": "fixed-reference-sleeves-not-promoted-candidate",
    "tradingAuthority": "none",
}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _fail(path: Path | str, code: str, message: str) -> None:
    raise AutoQuantValidationError([_issue(path, code, message)])


def _strict_keys(
    value: dict[str, Any],
    required: set[str],
    path: Path | str,
) -> list[ValidationIssue]:
    return [
        *(
            _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
            for key in sorted(required - value.keys())
        ),
        *(
            _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
            for key in sorted(value.keys() - required)
        ),
    ]


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(
            path,
            "research-program.missing",
            "Project does not declare a multi-Study research program",
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail(
            path,
            "research-program.json",
            "Research program must be one UTF-8 JSON object",
        )
    if not isinstance(value, dict):
        _fail(path, "research-program.type", "Research program must be an object")
    return value


def canonical_research_program_manifest() -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": RESEARCH_PROGRAM_KIND,
        "id": RESEARCH_PROGRAM_ID,
        "template": RESEARCH_DESK_TEMPLATE,
        "lanes": [dict(lane) for lane in CANONICAL_LANES],
        "integration": dict(INTEGRATION),
    }


def create_research_program_manifest(project: ProjectContext) -> Path:
    path = project.root_dir / RESEARCH_PROGRAM_MANIFEST
    if path.exists():
        _fail(
            path,
            "research-program.exists",
            "Research program manifest already exists",
        )
    path.write_text(
        json.dumps(
            canonical_research_program_manifest(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _validate_manifest(value: dict[str, Any], path: Path) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "template",
        "lanes",
        "integration",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(
            _issue(f"{path}/schemaVersion", "schema.version", "Expected V1")
        )
    if value.get("kind") != RESEARCH_PROGRAM_KIND:
        issues.append(
            _issue(
                f"{path}/kind",
                "research-program.kind",
                f"Expected {RESEARCH_PROGRAM_KIND}",
            )
        )
    if value.get("id") != RESEARCH_PROGRAM_ID:
        issues.append(
            _issue(
                f"{path}/id",
                "research-program.id",
                f"Expected canonical id {RESEARCH_PROGRAM_ID}",
            )
        )
    if value.get("template") != RESEARCH_DESK_TEMPLATE:
        issues.append(
            _issue(
                f"{path}/template",
                "research-program.template",
                f"Expected {RESEARCH_DESK_TEMPLATE}",
            )
        )
    lanes = value.get("lanes")
    canonical_lanes = [dict(lane) for lane in CANONICAL_LANES]
    if lanes != canonical_lanes:
        issues.append(
            _issue(
                f"{path}/lanes",
                "research-program.lanes",
                "Research program lanes differ from the canonical contract",
            )
        )
    if value.get("integration") != INTEGRATION:
        issues.append(
            _issue(
                f"{path}/integration",
                "research-program.integration",
                "Research program integration boundary differs from the canonical contract",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return value


def _command(
    command_id: str,
    description: str,
    argv: list[str],
    effect: str,
) -> dict[str, Any]:
    return {
        "id": command_id,
        "description": description,
        "argv": argv,
        "display": shlex.join(argv),
        "effect": effect,
    }


def _run_summary(project: ProjectContext, run_id: str) -> dict[str, Any]:
    run = load_run(project, run_id)
    metric = run.result["objective"]["metric"]
    value = run.result["metrics"].get(metric)
    return {
        "id": run.result["id"],
        "status": run.result["status"],
        "studyInputHash": run.result["studyInputHash"],
        "sourceHash": run.result["subject"]["sourceHash"],
        "metric": metric,
        "value": (
            float(value)
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        ),
        "startedAt": run.result["startedAt"],
        "completedAt": run.result["completedAt"],
    }


def _lane_state(
    project: ProjectContext,
    lane: dict[str, Any],
    *,
    request_path: Path | None,
) -> dict[str, Any]:
    study = load_study(project, lane["studyId"])
    if study.definition.editable["paths"] != lane["editablePaths"]:
        _fail(
            study.manifest_path,
            "research-program.editable",
            f"{lane['id']} Study editable paths differ from program declaration",
        )
    run_summaries = list_runs(project, lane["studyId"])
    latest_run = (
        _run_summary(project, run_summaries[-1].id)
        if run_summaries
        else None
    )
    sessions = [
        item
        for item in list_sessions(project)
        if item.study_id == lane["studyId"]
    ]
    latest_session = sessions[-1] if sessions else None
    reports: list[dict[str, Any]] = []
    if latest_session is not None:
        session = load_session(project, latest_session.id)
        reports = [item.to_dict() for item in list_reports(project, session)]
    current_run = (
        latest_run is not None
        and latest_run["studyInputHash"] == study.input_hash
    )
    if latest_run is not None and not current_run:
        phase = "stale"
    elif latest_session is not None and reports:
        phase = "reported"
    elif latest_session is not None and latest_session.status == "active":
        phase = "researching"
    elif latest_run is not None:
        phase = "baseline-ready"
    else:
        phase = "not-started"

    commands = [
        _command(
            "study.inspect",
            f"Inspect fixed authority for {lane['name']}.",
            [
                "aq",
                "study",
                "inspect",
                str(project.root_dir),
                "--study",
                lane["studyId"],
                "--json",
            ],
            "read-only",
        )
    ]
    if latest_run is None or not current_run:
        commands.append(
            _command(
                "run.execute",
                f"Create current immutable baseline evidence for {lane['name']}.",
                [
                    "aq",
                    "run",
                    "execute",
                    str(project.root_dir),
                    "--study",
                    lane["studyId"],
                    "--json",
                ],
                "creates-artifact",
            )
        )
    if latest_session is None:
        argv = [
            "aq",
            "session",
            "start",
            str(project.root_dir),
            "--study",
            lane["studyId"],
        ]
        if request_path is not None:
            argv.extend(["--request", str(request_path)])
        argv.append("--json")
        commands.append(
            _command(
                "session.start",
                f"Start governed delegated research for {lane['name']}.",
                argv,
                "creates-artifact",
            )
        )
    else:
        commands.append(
            _command(
                "session.show",
                f"Inspect current Session evidence for {lane['name']}.",
                [
                    "aq",
                    "session",
                    "show",
                    str(project.root_dir),
                    "--session",
                    latest_session.id,
                    "--json",
                ],
                "read-only",
            )
        )
        if reports:
            commands.append(
                _command(
                    "report.show",
                    f"Inspect the latest immutable Report for {lane['name']}.",
                    [
                        "aq",
                        "report",
                        "show",
                        str(project.root_dir),
                        "--session",
                        latest_session.id,
                        "--report",
                        reports[-1]["id"],
                        "--json",
                    ],
                    "read-only",
                )
            )
    return {
        **lane,
        "phase": phase,
        "study": {
            "id": study.definition.id,
            "name": study.definition.name,
            "description": study.definition.description,
            "inputHash": study.input_hash,
            "sourceHash": study.source_hash,
            "datasetHash": study.dataset_hash,
            "objective": {
                "metric": study.definition.objective.metric,
                "direction": study.definition.objective.direction,
                "minimumImprovement": (
                    study.definition.objective.minimum_improvement
                ),
            },
            "dataset": {
                "id": study.definition.dataset.id,
                "version": study.definition.dataset.version,
                "assetClass": study.definition.dataset.asset_class,
                "universe": study.definition.dataset.universe,
                "timeRange": {
                    "start": study.definition.dataset.time_range.start,
                    "end": study.definition.dataset.time_range.end,
                },
            },
        },
        "latestRun": latest_run,
        "currentRun": current_run,
        "latestSession": (
            latest_session.to_dict() if latest_session is not None else None
        ),
        "reports": reports,
        "commands": commands,
    }


def load_research_program(
    project: ProjectContext,
    *,
    optional: bool = False,
) -> dict[str, Any] | None:
    """Verify and project the canonical multi-Study research program."""

    path = project.root_dir / RESEARCH_PROGRAM_MANIFEST
    if optional and not path.exists():
        return None
    manifest = _validate_manifest(_read_object(path), path)
    intake = load_project_intake(project)
    request_path = (
        project.root_dir / PROJECT_REQUEST
        if intake is not None
        else None
    )
    lanes = [
        _lane_state(project, lane, request_path=request_path)
        for lane in manifest["lanes"]
    ]
    dataset_hashes = {lane["study"]["datasetHash"] for lane in lanes}
    dataset_contracts = {
        json.dumps(lane["study"]["dataset"], sort_keys=True)
        for lane in lanes
    }
    if len(dataset_hashes) != 1 or len(dataset_contracts) != 1:
        _fail(
            path,
            "research-program.dataset",
            "Every research-program Study must bind the same dataset contract and bytes",
        )

    active_by_path: dict[str, list[dict[str, str]]] = {}
    for lane in lanes:
        session = lane["latestSession"]
        if session is None or session["status"] != "active":
            continue
        for editable in lane["editablePaths"]:
            active_by_path.setdefault(editable, []).append(
                {"laneId": lane["id"], "sessionId": session["id"]}
            )
    conflicts = [
        {
            "editablePath": editable,
            "sessions": sessions,
            "message": (
                "Concurrent active Sessions share one editable source surface; "
                "promotion order is ambiguous."
            ),
        }
        for editable, sessions in sorted(active_by_path.items())
        if len(sessions) > 1
    ]

    lane_by_id = {lane["id"]: lane for lane in lanes}
    recommended_lane = next(
        (
            lane
            for lane in lanes
            if lane["phase"] != "reported"
            and all(
                lane_by_id[dependency]["phase"] == "reported"
                for dependency in lane["dependsOn"]
            )
        ),
        None,
    )
    if recommended_lane is None:
        recommended_lane = next(
            (lane for lane in lanes if lane["phase"] != "reported"),
            None,
        )
    recommended_action = None
    if recommended_lane is not None:
        preferred_ids = (
            ("run.execute", "session.start", "session.show", "study.inspect")
            if recommended_lane["phase"] in {"not-started", "stale"}
            else ("session.start", "session.show", "run.execute", "study.inspect")
        )
        for command_id in preferred_ids:
            recommended_action = next(
                (
                    command
                    for command in recommended_lane["commands"]
                    if command["id"] == command_id
                ),
                None,
            )
            if recommended_action is not None:
                break

    phases = {
        phase: sum(lane["phase"] == phase for lane in lanes)
        for phase in (
            "not-started",
            "baseline-ready",
            "researching",
            "reported",
            "stale",
        )
    }
    warnings = [
        (
            "The governed RL lane uses fixed reference sleeves and does not "
            "consume promoted factors/candidate.py in V1."
        )
    ]
    warnings.extend(conflict["message"] for conflict in conflicts)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": RESEARCH_PROGRAM_STATUS_KIND,
        "manifest": manifest,
        "project": {
            "id": project.manifest.id,
            "name": project.manifest.name,
            "rootDir": str(project.root_dir),
        },
        "request": (
            {
                "title": intake["request"]["title"],
                "question": intake["request"]["question"],
                "path": str(request_path),
                "requestHash": intake["manifest"]["requestHash"],
            }
            if intake is not None
            else None
        ),
        "dataset": lanes[0]["study"]["dataset"],
        "datasetHash": lanes[0]["study"]["datasetHash"],
        "lanes": lanes,
        "summary": {
            "lanes": len(lanes),
            "phases": phases,
            "activeSessions": sum(
                lane["latestSession"] is not None
                and lane["latestSession"]["status"] == "active"
                for lane in lanes
            ),
            "reports": sum(len(lane["reports"]) for lane in lanes),
            "conflicts": len(conflicts),
        },
        "conflicts": conflicts,
        "recommendedLaneId": (
            recommended_lane["id"] if recommended_lane is not None else None
        ),
        "recommendedAction": recommended_action,
        "warnings": warnings,
    }


RESEARCH_PROGRAM_STATUS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant verified multi-Study research program status",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "manifest",
        "project",
        "request",
        "dataset",
        "datasetHash",
        "lanes",
        "summary",
        "conflicts",
        "recommendedLaneId",
        "recommendedAction",
        "warnings",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": RESEARCH_PROGRAM_STATUS_KIND},
        "manifest": {"type": "object"},
        "project": {"type": "object"},
        "request": {"type": ["object", "null"]},
        "dataset": {"type": "object"},
        "datasetHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "lanes": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {"type": "object"},
        },
        "summary": {"type": "object"},
        "conflicts": {"type": "array", "items": {"type": "object"}},
        "recommendedLaneId": {"type": ["string", "null"]},
        "recommendedAction": {"type": ["object", "null"]},
        "warnings": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
    },
}
