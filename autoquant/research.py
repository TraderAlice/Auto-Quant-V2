"""Bounded provider-neutral external Researcher Campaigns."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_definitions import load_experiment_definition
from .sessions import (
    EXPERIMENT_ID,
    SessionContext,
    evaluate_experiment,
    load_experiment,
    load_session,
    restore_session_worktree,
    session_snapshot,
    validate_session_authority,
)
from .studies import SCHEMA_VERSION, hash_file, hash_json
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


CAMPAIGN_RESULT = "result.json"
CAMPAIGN_MANIFEST = "manifest.json"
CAMPAIGN_PROGRESS = "progress.json"
CAMPAIGN_STOP_REQUEST = "stop-request.json"
CAMPAIGN_ID = re.compile(
    r"^campaign-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$"
)
CAMPAIGN_STATUSES = {
    "stopped",
    "budget_exhausted",
    "failed",
    "evidence_ready",
    "failed_gate",
    "blocked",
    "stopped_by_user",
    "inconclusive",
}
RESPONSE_VERSION = 1
MAX_OUTPUT_BYTES = 1_000_000
PROGRESS_PHASES = {
    "starting",
    "researcher",
    "judge",
    "restoring",
    "ready",
    "terminal",
}


@dataclass(frozen=True)
class CampaignContext:
    root_dir: Path
    manifest: dict[str, Any]
    result: dict[str, Any]


@dataclass(frozen=True)
class CampaignSummary:
    id: str
    status: str
    reason: str
    turns_completed: int
    experiments: int
    keeps: int
    reverts: int
    crashes: int
    started_at: str
    completed_at: str
    budget: dict[str, Any]
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "reason": self.reason,
            "turnsCompleted": self.turns_completed,
            "experiments": self.experiments,
            "verdicts": {
                "KEEP": self.keeps,
                "REVERT": self.reverts,
                "CRASH": self.crashes,
            },
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "budget": self.budget,
            "path": self.path,
        }


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _atomic_write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _write_json(temporary, value)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.missing", f"Missing {label}: {path}")]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    f"{label}.json",
                    f"Invalid JSON at line {error.lineno}, column "
                    f"{error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.type", f"{label} must be an object")]
        )
    return value


def _strict_keys(
    value: dict[str, Any],
    required: set[str],
    path: Path | str,
    *,
    optional: set[str] = frozenset(),
) -> list[ValidationIssue]:
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - required - optional)
    )
    return issues


def _campaigns_root(
    session: SessionContext,
    *,
    create: bool = False,
) -> Path:
    root = session.root_dir / "campaigns"
    if root.is_symlink():
        raise AutoQuantValidationError(
            [_issue(root, "path.symlink", "Campaign root cannot be a symlink")]
        )
    if create:
        root.mkdir(exist_ok=True)
    return confined_path(session.root_dir, "campaigns", "session/campaigns")


def _campaign_root(
    session: SessionContext,
    campaign_id: str,
    *,
    create_root: bool = False,
) -> Path:
    if not CAMPAIGN_ID.fullmatch(campaign_id):
        raise AutoQuantValidationError(
            [_issue(campaign_id, "campaign.id", "Invalid Campaign id")]
        )
    return confined_path(
        _campaigns_root(session, create=create_root),
        campaign_id,
        f"campaign/{campaign_id}",
    )


def parse_researcher_response(text: str, path: Path | str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "researcher.response-json",
                    f"Researcher returned invalid JSON at line {error.lineno}, "
                    f"column {error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "researcher.response-type", "Response must be an object")]
        )
    action = value.get("action")
    required = (
        {"schema_version", "action", "strategy", "hypothesis", "expected_effect"}
        if action == "propose"
        else {"schema_version", "action", "reason"}
        if action == "stop"
        else {"schema_version", "action"}
    )
    issues = _strict_keys(value, required, path)
    if value.get("schema_version") != RESPONSE_VERSION:
        issues.append(
            _issue(
                f"{path}/schema_version",
                "schema.version",
                f"Expected Researcher response version {RESPONSE_VERSION}",
            )
        )
    if action not in {"propose", "stop"}:
        issues.append(
            _issue(f"{path}/action", "schema.choice", "Action must be propose or stop")
        )
    for key in required - {"schema_version", "action"}:
        if not isinstance(value.get(key), str) or not value[key].strip():
            issues.append(
                _issue(f"{path}/{key}", "schema.string", f"{key} must be non-empty")
            )
    if issues:
        raise AutoQuantValidationError(issues)
    return {
        key: item.strip() if isinstance(item, str) else item
        for key, item in value.items()
    }


def _campaign_file_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AutoQuantValidationError(
                [_issue(path, "path.symlink", "Campaign cannot contain symlinks")]
            )
        if path.is_file() and path != root / CAMPAIGN_MANIFEST:
            hashes[path.relative_to(root).as_posix()] = hash_file(path)
    return hashes


def _progress_value(
    *,
    campaign_id: str,
    session_id: str,
    command_hash: str,
    started_at: str,
    phase: str,
    status: str,
    message: str,
    turn: int,
    budget: dict[str, Any],
    experiment_ids: list[str],
    verdicts: dict[str, int],
    experiment_definition_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "campaign-progress",
        "campaignId": campaign_id,
        "sessionId": session_id,
        "status": status,
        "phase": phase,
        "message": message,
        "startedAt": started_at,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "turn": turn,
        "commandHash": command_hash,
        "budget": budget,
        "experiments": list(experiment_ids),
        "verdicts": dict(verdicts),
    }
    if experiment_definition_ref is not None:
        value["experimentDefinitionRef"] = experiment_definition_ref
    return value


def _write_progress(
    root: Path,
    *,
    campaign_id: str,
    session_id: str,
    command_hash: str,
    started_at: str,
    phase: str,
    status: str,
    message: str,
    turn: int,
    budget: dict[str, Any],
    experiment_ids: list[str],
    verdicts: dict[str, int],
    experiment_definition_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _progress_value(
        campaign_id=campaign_id,
        session_id=session_id,
        command_hash=command_hash,
        started_at=started_at,
        phase=phase,
        status=status,
        message=message,
        turn=turn,
        budget=budget,
        experiment_ids=experiment_ids,
        verdicts=verdicts,
        experiment_definition_ref=experiment_definition_ref,
    )
    _atomic_write_json(root / CAMPAIGN_PROGRESS, value)
    return value


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _bounded_output(value: str) -> tuple[str, bool]:
    encoded = value.encode()
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return value, False
    clipped = encoded[:MAX_OUTPUT_BYTES].decode(errors="replace")
    return clipped + "\n[AutoQuant truncated output]\n", True


def _invoke_researcher(
    command: str,
    session: SessionContext,
    campaign_id: str,
    input_path: Path,
    brief: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    started = time.monotonic()
    environment = dict(os.environ)
    environment.update(
        {
            "AUTOQUANT_RESEARCH_INPUT": str(input_path),
            "AUTOQUANT_WORKTREE": str(session.worktree_project.root_dir),
            "AUTOQUANT_SESSION_ID": session.manifest["id"],
            "AUTOQUANT_CAMPAIGN_ID": campaign_id,
        }
    )
    exit_code: int | None = None
    timed_out = False
    stdout = ""
    stderr = ""
    try:
        process = subprocess.Popen(
            ["sh" if os.name == "nt" else "/bin/sh", "-lc", command],
            cwd=session.worktree_project.root_dir,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(
                json.dumps(brief, ensure_ascii=False),
                timeout=max(0.001, timeout_seconds),
            )
            exit_code = process.returncode
        except subprocess.TimeoutExpired as error:
            timed_out = True
            stdout = _text(error.stdout)
            stderr = _text(error.stderr)
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                    text=True,
                )
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            final_stdout, final_stderr = process.communicate()
            stdout = final_stdout or stdout
            stderr = final_stderr or stderr
    except OSError as error:
        stderr = str(error)
    stdout, stdout_truncated = _bounded_output(stdout)
    stderr, stderr_truncated = _bounded_output(stderr)
    return {
        "exitCode": exit_code,
        "timedOut": timed_out,
        "timeoutSeconds": timeout_seconds,
        "durationMs": int((time.monotonic() - started) * 1000),
        "stdout": stdout,
        "stderr": stderr,
        "stdoutTruncated": stdout_truncated,
        "stderrTruncated": stderr_truncated,
    }


def _history_for_brief(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "sequence": item["sequence"],
            "hypothesis": item["hypothesis"],
            "verdict": item["verdict"],
            "leaderValue": item["leaderValue"],
            "candidateValue": item["candidateValue"],
            "improvement": item["improvement"],
            "runId": item["runId"],
        }
        for item in snapshot["experiments"]
    ]


def _brief(
    project: ProjectContext,
    session: SessionContext,
    campaign_id: str,
    turn: int,
    max_turns: int,
    max_wall_seconds: int,
    elapsed_seconds: float,
    campaign_history: list[dict[str, Any]],
) -> dict[str, Any]:
    snapshot = session_snapshot(project, session)
    program_path = Path(snapshot["programPath"])
    program = program_path.read_text(encoding="utf-8")
    study = validate_session_authority(project, session)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "campaignId": campaign_id,
        "turn": turn,
        "sessionId": session.manifest["id"],
        "studyId": session.manifest["studyId"],
        "program": {"text": program, "hash": session.manifest["locks"]["programHash"]},
        "worktree": str(session.worktree_project.root_dir),
        "editablePaths": session.manifest["editablePaths"],
        "objective": {
            "metric": study.definition.objective.metric,
            "direction": study.definition.objective.direction,
            "minimumImprovement": study.definition.objective.minimum_improvement,
        },
        "leader": session.manifest["leader"],
        "delegation": snapshot["delegation"],
        "locks": {
            key: value
            for key, value in session.manifest["locks"].items()
            if key != "fixedHashes"
        },
        "history": _history_for_brief(snapshot),
        "campaignHistory": campaign_history,
        "budget": {
            "maxTurns": max_turns,
            "remainingTurns": max_turns - turn + 1,
            "maxWallSeconds": max_wall_seconds,
            "remainingWallSeconds": max(0.0, max_wall_seconds - elapsed_seconds),
        },
        "responseContract": {
            "version": RESPONSE_VERSION,
            "propose": {
                "schema_version": 1,
                "action": "propose",
                "strategy": "non-empty string",
                "hypothesis": "non-empty string",
                "expected_effect": "non-empty string",
            },
            "stop": {
                "schema_version": 1,
                "action": "stop",
                "reason": "non-empty string",
            },
        },
    }


def _turn_failure(
    turn_root: Path,
    code: str,
    message: str,
    execution: dict[str, Any] | None,
) -> dict[str, str]:
    error = {"code": code, "message": message}
    _write_json(
        turn_root / "result.json",
        {
            "schemaVersion": SCHEMA_VERSION,
            "status": "failed",
            "experimentId": None,
            "verdict": None,
            "execution": execution,
            "error": error,
        },
    )
    return error


def _load_stop_request(
    root: Path,
    *,
    campaign_id: str,
    session_id: str,
) -> dict[str, Any] | None:
    path = root / CAMPAIGN_STOP_REQUEST
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise AutoQuantValidationError(
            [_issue(path, "campaign.stop-request", "Campaign stop request must be a regular file")]
        )
    value = _read_json(path, "campaign-stop-request")
    issues = _strict_keys(
        value,
        {
            "schemaVersion",
            "kind",
            "campaignId",
            "sessionId",
            "actor",
            "requestedAt",
            "lastCompletedExperiments",
        },
        path,
    )
    if value.get("schemaVersion") != 1 or value.get("kind") != "autoquant-campaign-stop-request":
        issues.append(_issue(path, "campaign.stop-request", "Invalid Campaign stop request"))
    if value.get("campaignId") != campaign_id or value.get("sessionId") != session_id:
        issues.append(_issue(path, "campaign.stop-request", "Campaign stop request identity mismatch"))
    actor = value.get("actor")
    if not isinstance(actor, dict) or set(actor) != {"id", "kind"}:
        issues.append(_issue(path, "campaign.stop-request", "Campaign stop actor is invalid"))
    if not isinstance(value.get("requestedAt"), str) or not value["requestedAt"]:
        issues.append(_issue(path, "campaign.stop-request", "Campaign stop time is invalid"))
    experiments = value.get("lastCompletedExperiments")
    if not isinstance(experiments, list) or not all(
        isinstance(item, str) and EXPERIMENT_ID.fullmatch(item)
        for item in (experiments if isinstance(experiments, list) else [])
    ):
        issues.append(
            _issue(path, "campaign.stop-request", "Campaign stop Experiment references are invalid")
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return value


def request_campaign_stop(
    project: ProjectContext,
    session_id: str,
    campaign_id: str,
    actor: dict[str, str],
) -> dict[str, Any]:
    session = load_session(project, session_id)
    if not CAMPAIGN_ID.fullmatch(campaign_id):
        raise AutoQuantValidationError([_issue(campaign_id, "campaign.id", "Invalid Campaign id")])
    progress = next(
        (
            item
            for item in list_campaign_progress(session)
            if item["campaignId"] == campaign_id
        ),
        None,
    )
    if progress is None:
        raise AutoQuantValidationError(
            [_issue(campaign_id, "campaign.not-running", "Campaign is not running")]
        )
    root = confined_path(
        _campaigns_root(session),
        f".{campaign_id}.creating",
        "campaign/staging",
    )
    existing = _load_stop_request(root, campaign_id=campaign_id, session_id=session_id)
    if existing is not None:
        return existing
    value = {
        "schemaVersion": 1,
        "kind": "autoquant-campaign-stop-request",
        "campaignId": campaign_id,
        "sessionId": session_id,
        "actor": actor,
        "requestedAt": datetime.now(timezone.utc).isoformat(),
        "lastCompletedExperiments": list(progress["experiments"]),
    }
    _atomic_write_json(root / CAMPAIGN_STOP_REQUEST, value)
    return _load_stop_request(root, campaign_id=campaign_id, session_id=session_id) or value


def run_campaign(
    project: ProjectContext,
    session_id: str,
    agent_command: str,
    *,
    max_turns: int = 5,
    max_wall_seconds: int = 900,
    turn_timeout_seconds: int = 300,
    max_candidates: int | None = None,
    max_cpu_seconds: int | None = None,
    max_gpu_seconds: int = 0,
    max_cost: float | None = None,
    cost_currency: str | None = None,
    cost_telemetry_available: bool = False,
    private_executor_requested: bool = False,
    private_executor_available: bool = False,
    stop_conditions: tuple[str, ...] = (
        "candidate-limit",
        "wall-time-limit",
        "cpu-limit",
        "immediate-user-stop",
    ),
    holdout_sealed: bool = True,
    experiment_definition_ref: dict[str, Any] | None = None,
) -> CampaignContext:
    if not isinstance(agent_command, str) or not agent_command.strip():
        raise AutoQuantValidationError(
            [_issue("agent_command", "schema.string", "Agent command must be non-empty")]
        )
    budget_issues: list[ValidationIssue] = []
    for value, name, maximum in (
        (max_turns, "max_turns", 100),
        (max_wall_seconds, "max_wall_seconds", 86400),
        (turn_timeout_seconds, "turn_timeout_seconds", 3600),
    ):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= maximum
        ):
            budget_issues.append(
                _issue(
                    name,
                    "schema.range",
                    f"{name} must be an integer from 1 to {maximum}",
                )
            )
    max_candidates = max_turns if max_candidates is None else max_candidates
    max_cpu_seconds = (
        max_wall_seconds if max_cpu_seconds is None else max_cpu_seconds
    )


    for value, name, minimum, maximum in (
        (max_candidates, "max_candidates", 1, 100),
        (max_cpu_seconds, "max_cpu_seconds", 1, 86400),
        (max_gpu_seconds, "max_gpu_seconds", 0, 86400),
    ):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not minimum <= value <= maximum
        ):
            budget_issues.append(
                _issue(
                    name,
                    "schema.range",
                    f"{name} must be an integer from {minimum} to {maximum}",
                )
            )
    if (
        isinstance(max_candidates, int)
        and not isinstance(max_candidates, bool)
        and isinstance(max_turns, int)
        and not isinstance(max_turns, bool)
        and max_candidates > max_turns
    ):
        budget_issues.append(
            _issue(
                "max_candidates",
                "campaign.budget",
                "Candidate ceiling cannot exceed the legacy turn ceiling",
            )
        )
    if max_cost is not None and (
        not isinstance(max_cost, (int, float))
        or isinstance(max_cost, bool)
        or not math.isfinite(float(max_cost))
        or max_cost <= 0
    ):
        budget_issues.append(
            _issue("max_cost", "schema.range", "max_cost must be a positive finite number")
        )
    if max_cost is not None and (
        not isinstance(cost_currency, str) or not cost_currency.strip()
    ):
        budget_issues.append(
            _issue("cost_currency", "schema.string", "A cost ceiling requires a currency")
        )
    if not isinstance(cost_telemetry_available, bool):
        budget_issues.append(_issue("cost_telemetry_available", "schema.boolean", "Cost telemetry flag must be boolean"))
    if not isinstance(private_executor_requested, bool) or not isinstance(private_executor_available, bool):
        budget_issues.append(_issue("private_executor", "schema.boolean", "Private executor flags must be boolean"))
    if not isinstance(holdout_sealed, bool) or not holdout_sealed:
        budget_issues.append(
            _issue(
                "holdout_sealed",
                "campaign.holdout",
                "Candidate research requires a sealed holdout; opening it is a separate confirmed terminal action",
            )
        )
    if (
        not isinstance(stop_conditions, tuple)
        or not stop_conditions
        or not all(isinstance(item, str) and item.strip() for item in stop_conditions)
    ):
        budget_issues.append(_issue("stop_conditions", "schema.list", "At least one fixed stop condition is required"))
    if budget_issues:
        raise AutoQuantValidationError(budget_issues)
    resolved_experiment_definition_ref: dict[str, Any] | None = None
    if experiment_definition_ref is not None:
        ref_issues: list[ValidationIssue] = []
        if not isinstance(experiment_definition_ref, dict):
            ref_issues.append(_issue("experiment_definition_ref", "schema.type", "experiment_definition_ref must be an object"))
        else:
            ref_issues.extend(
                _strict_keys(experiment_definition_ref, {"id", "version", "contentHash"}, "experiment_definition_ref")
            )
            ref_id = experiment_definition_ref.get("id")
            if not isinstance(ref_id, str) or not ref_id.strip():
                ref_issues.append(_issue("experiment_definition_ref/id", "schema.string", "id must be non-empty"))
            ref_version = experiment_definition_ref.get("version")
            if not isinstance(ref_version, int) or isinstance(ref_version, bool) or ref_version < 1:
                ref_issues.append(_issue("experiment_definition_ref/version", "schema.version", "version must be a positive integer"))
            ref_hash = experiment_definition_ref.get("contentHash")
            if not isinstance(ref_hash, str) or not re.fullmatch(r"^[0-9a-f]{64}$", ref_hash):
                ref_issues.append(_issue("experiment_definition_ref/contentHash", "schema.hash", "contentHash must be a lowercase SHA-256 hex digest"))
        if ref_issues:
            raise AutoQuantValidationError(ref_issues)
        loaded_def = load_experiment_definition(
            project, session_id,
            experiment_definition_ref["id"],
            experiment_definition_ref["version"],
        )
        if loaded_def.definition["status"] != "frozen":
            raise AutoQuantValidationError(
                [_issue("experiment_definition_ref", "definition.not-frozen", "ExperimentDefinition must be frozen")]
            )
        if loaded_def.manifest["contentHash"] != experiment_definition_ref["contentHash"]:
            raise AutoQuantValidationError(
                [_issue("experiment_definition_ref/contentHash", "definition.hash-mismatch",
                       "Supplied contentHash does not match the loaded ExperimentDefinition manifest")]
            )
        resolved_experiment_definition_ref = {
            "id": experiment_definition_ref["id"],
            "version": experiment_definition_ref["version"],
            "contentHash": experiment_definition_ref["contentHash"],
        }
    session = load_session(project, session_id)
    if session.manifest["status"] != "active":
        raise AutoQuantValidationError(
            [_issue(session.manifest_path, "session.closed", "Session is not active")]
        )
    study = validate_session_authority(project, session)
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
    command_hash = hash_json({"shell": agent_command})
    identity_payload = {
        "session": session_id,
        "startedAt": started.isoformat(),
        "commandHash": command_hash,
        "maxTurns": max_turns,
        "maxWallSeconds": max_wall_seconds,
        "turnTimeoutSeconds": turn_timeout_seconds,
        "maxCandidates": max_candidates,
        "maxCpuSeconds": max_cpu_seconds,
        "maxGpuSeconds": max_gpu_seconds,
        "maxCost": (
            {"currency": cost_currency, "amount": max_cost}
            if max_cost is not None
            else None
        ),
        "privateExecutorRequested": private_executor_requested,
        "privateExecutorAvailable": private_executor_available,
        "stopConditions": list(stop_conditions),
    }
    if resolved_experiment_definition_ref is not None:
        identity_payload["experimentDefinitionRef"] = resolved_experiment_definition_ref
    identity = hash_json(identity_payload)
    campaign_id = f"campaign-{stamp}-{identity[:12]}"
    root = _campaign_root(session, campaign_id, create_root=True)
    staging = _campaigns_root(session, create=True) / f".{campaign_id}.creating"
    if root.exists() or root.is_symlink() or staging.exists():
        raise AutoQuantValidationError(
            [_issue(root, "campaign.collision", "Campaign already exists")]
        )
    staging.mkdir()
    (staging / "turns").mkdir()
    monotonic_started = time.monotonic()
    initial_leader = dict(session.manifest["leader"])
    experiment_ids: list[str] = []
    verdicts = {"KEEP": 0, "REVERT": 0, "CRASH": 0}
    budget = {
        "maxTurns": max_turns,
        "maxCandidates": max_candidates,
        "maxWallSeconds": max_wall_seconds,
        "turnTimeoutSeconds": turn_timeout_seconds,
        "maxCpuSeconds": max_cpu_seconds,
        "maxGpuSeconds": max_gpu_seconds,
        "maxCost": (
            {"currency": cost_currency, "amount": max_cost}
            if max_cost is not None
            else None
        ),
        "costTelemetry": (
            "available"
            if cost_telemetry_available
            else ("unknown" if max_cost is not None else "not-applicable")
        ),
        "executorPolicy": {
            "default": "cpu",
            "privateRequested": private_executor_requested,
            "privateAvailable": private_executor_available,
        },
        "stopConditions": list(stop_conditions),
        "holdoutPolicy": {"sealed": True},
        "used": {
            "turns": 0,
            "candidates": 0,
            "wallSeconds": 0,
            "cpuSeconds": 0,
            "gpuSeconds": 0,
            "cost": (
                {"known": True, "currency": cost_currency, "amount": 0}
                if cost_telemetry_available
                else {"known": False, "currency": cost_currency, "amount": None}
            ),
        },
        "remaining": {
            "turns": max_turns,
            "candidates": max_candidates,
            "wallSeconds": max_wall_seconds,
            "cpuSeconds": max_cpu_seconds,
            "gpuSeconds": max_gpu_seconds,
            "cost": (
                {"known": True, "currency": cost_currency, "amount": max_cost}
                if cost_telemetry_available and max_cost is not None
                else {"known": False, "currency": cost_currency, "amount": None}
            ),
        },
    }
    campaign_history: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    turns_completed = 0
    blocked_reason = None
    if private_executor_requested and not private_executor_available:
        blocked_reason = "Requested private GPU/MOSS provider is unavailable; CPU remains the public executor"
    elif max_cost is not None and not cost_telemetry_available:
        blocked_reason = "Provider cost telemetry is unknown under an approved monetary ceiling"
    status = "blocked" if blocked_reason is not None else "budget_exhausted"
    reason = blocked_reason or "Maximum turn budget reached"
    try:
        _write_progress(
            staging,
            campaign_id=campaign_id,
            session_id=session_id,
            command_hash=command_hash,
            started_at=started.isoformat(),
            phase="starting",
            status="running",
            message="Preparing the first bounded Researcher turn",
            turn=0,
            budget=budget,
            experiment_ids=experiment_ids,
            verdicts=verdicts,
            experiment_definition_ref=resolved_experiment_definition_ref,
        )
        turns = () if blocked_reason is not None else range(1, max_turns + 1)
        for turn in turns:
            if _load_stop_request(staging, campaign_id=campaign_id, session_id=session_id) is not None:
                status = "stopped_by_user"
                reason = "Authorized user requested immediate stop before the next candidate"
                break
            session = load_session(project, session_id)
            study = validate_session_authority(project, session)
            elapsed = time.monotonic() - monotonic_started
            budget["used"].update(
                {
                    "turns": turns_completed,
                    "candidates": len(experiment_ids),
                    "wallSeconds": min(max_wall_seconds, int(elapsed)),
                    "cpuSeconds": min(max_cpu_seconds, int(elapsed)),
                }
            )
            budget["remaining"].update(
                {
                    "turns": max(0, max_turns - turns_completed),
                    "candidates": max(0, max_candidates - len(experiment_ids)),
                    "wallSeconds": max(0, max_wall_seconds - int(elapsed)),
                    "cpuSeconds": max(0, max_cpu_seconds - int(elapsed)),
                }
            )
            if len(experiment_ids) >= max_candidates:
                status = "budget_exhausted"
                reason = "Maximum candidate budget reached"
                break
            remaining = max_wall_seconds - elapsed
            judge_reserve = study.definition.judge.timeout_seconds
            if remaining <= judge_reserve:
                status = "budget_exhausted"
                reason = "Insufficient wall-clock budget for another fixed Judge"
                break
            if max_cpu_seconds - elapsed <= judge_reserve:
                status = "budget_exhausted"
                reason = "Insufficient CPU budget for another fixed Judge"
                break
            turn_root = staging / "turns" / f"turn-{turn:04d}"
            turn_root.mkdir()
            brief = _brief(
                project,
                session,
                campaign_id,
                turn,
                max_turns,
                max_wall_seconds,
                elapsed,
                campaign_history,
            )
            input_path = turn_root / "input.json"
            _write_json(input_path, brief)
            _write_progress(
                staging,
                campaign_id=campaign_id,
                session_id=session_id,
                command_hash=command_hash,
                started_at=started.isoformat(),
                phase="researcher",
                status="running",
                message=f"External Researcher is working on turn {turn}",
                turn=turn,
                budget=budget,
                experiment_ids=experiment_ids,
                verdicts=verdicts,
                experiment_definition_ref=resolved_experiment_definition_ref,
            )
            command_timeout = min(
                float(turn_timeout_seconds),
                max(0.001, remaining - judge_reserve),
            )
            execution = _invoke_researcher(
                agent_command,
                session,
                campaign_id,
                input_path,
                brief,
                command_timeout,
            )
            (turn_root / "stdout.txt").write_text(
                execution.pop("stdout"),
                encoding="utf-8",
            )
            (turn_root / "stderr.txt").write_text(
                execution.pop("stderr"),
                encoding="utf-8",
            )
            turns_completed = turn
            try:
                if execution["timedOut"]:
                    raise AutoQuantValidationError(
                        [
                            _issue(
                                turn_root,
                                "researcher.timeout",
                                "Researcher exceeded its bounded turn timeout",
                            )
                        ]
                    )
                if execution["exitCode"] != 0:
                    raise AutoQuantValidationError(
                        [
                            _issue(
                                turn_root,
                                "researcher.exit",
                                f"Researcher exited with code {execution['exitCode']}",
                            )
                        ]
                    )
                if execution["stdoutTruncated"]:
                    raise AutoQuantValidationError(
                        [
                            _issue(
                                turn_root,
                                "researcher.output-limit",
                                "Researcher stdout exceeded the output limit",
                            )
                        ]
                    )
                stdout = (turn_root / "stdout.txt").read_text(encoding="utf-8")
                response = parse_researcher_response(stdout.strip(), turn_root)
                _write_json(turn_root / "response.json", response)
                if response["action"] == "stop":
                    candidate = validate_session_authority(project, session)
                    if candidate.source_hash != session.manifest["leader"]["sourceHash"]:
                        raise AutoQuantValidationError(
                            [
                                _issue(
                                    candidate.root_dir,
                                    "researcher.stop-changed-source",
                                    "Researcher returned stop after changing candidate source",
                                )
                            ]
                        )
                    _write_json(
                        turn_root / "result.json",
                        {
                            "schemaVersion": SCHEMA_VERSION,
                            "status": "stopped",
                            "experimentId": None,
                            "verdict": None,
                            "execution": execution,
                            "error": None,
                        },
                    )
                    status = "stopped"
                    reason = response["reason"]
                    break

                remaining_after_command = max_wall_seconds - (
                    time.monotonic() - monotonic_started
                )
                if remaining_after_command <= judge_reserve:
                    restore_session_worktree(project, session)
                    _write_json(
                        turn_root / "result.json",
                        {
                            "schemaVersion": SCHEMA_VERSION,
                            "status": "budget_exhausted",
                            "experimentId": None,
                            "verdict": None,
                            "execution": execution,
                            "error": None,
                        },
                    )
                    status = "budget_exhausted"
                    reason = "Researcher consumed the remaining fixed Judge budget"
                    break
                _write_progress(
                    staging,
                    campaign_id=campaign_id,
                    session_id=session_id,
                    command_hash=command_hash,
                    started_at=started.isoformat(),
                    phase="judge",
                    status="running",
                    message=f"Fixed Judge is evaluating turn {turn}",
                    turn=turn,
                    budget=budget,
                    experiment_ids=experiment_ids,
                    verdicts=verdicts,
                    experiment_definition_ref=resolved_experiment_definition_ref,
                )
                experiment = evaluate_experiment(
                    project,
                    session_id,
                    response["hypothesis"],
                )
                experiment_ids.append(experiment.result["id"])
                verdict = experiment.result["verdict"]
                verdicts[verdict] += 1
                campaign_history.append(
                    {
                        "turn": turn,
                        "strategy": response["strategy"],
                        "hypothesis": response["hypothesis"],
                        "expectedEffect": response["expected_effect"],
                        "experimentId": experiment.result["id"],
                        "verdict": verdict,
                    }
                )
                _write_json(
                    turn_root / "result.json",
                    {
                        "schemaVersion": SCHEMA_VERSION,
                        "status": "evaluated",
                        "experimentId": experiment.result["id"],
                        "verdict": verdict,
                        "execution": execution,
                        "error": None,
                    },
                )
                _write_progress(
                    staging,
                    campaign_id=campaign_id,
                    session_id=session_id,
                    command_hash=command_hash,
                    started_at=started.isoformat(),
                    phase="ready",
                    status="running",
                    message=f"Turn {turn} completed with {verdict}",
                    turn=turn,
                    budget=budget,
                    experiment_ids=experiment_ids,
                    verdicts=verdicts,
                    experiment_definition_ref=resolved_experiment_definition_ref,
                )
            except Exception as error:
                validation_error = (
                    error
                    if isinstance(error, AutoQuantValidationError)
                    else AutoQuantValidationError(
                        [
                            _issue(
                                turn_root,
                                "campaign.operation",
                                str(error),
                            )
                        ]
                    )
                )
                try:
                    _write_progress(
                        staging,
                        campaign_id=campaign_id,
                        session_id=session_id,
                        command_hash=command_hash,
                        started_at=started.isoformat(),
                        phase="restoring",
                        status="running",
                        message="Restoring the verified Session leader",
                        turn=turn,
                        budget=budget,
                        experiment_ids=experiment_ids,
                        verdicts=verdicts,
                        experiment_definition_ref=resolved_experiment_definition_ref,
                    )
                    restore_session_worktree(project, session)
                except AutoQuantValidationError as restore_error:
                    validation_error = AutoQuantValidationError(
                        [*validation_error.issues, *restore_error.issues]
                    )
                errors = [
                    {
                        "code": issue.code,
                        "message": f"{issue.path}: {issue.message}",
                    }
                    for issue in validation_error.issues
                ]
                _turn_failure(
                    turn_root,
                    errors[0]["code"],
                    errors[0]["message"],
                    execution,
                )
                status = "failed"
                reason = errors[0]["message"]
                break

        if _load_stop_request(staging, campaign_id=campaign_id, session_id=session_id) is not None:
            status = "stopped_by_user"
            reason = "Authorized user requested immediate stop; completed evidence was preserved"
        completed = datetime.now(timezone.utc)
        elapsed_final = time.monotonic() - monotonic_started
        budget["used"].update(
            {
                "turns": turns_completed,
                "candidates": len(experiment_ids),
                "wallSeconds": min(max_wall_seconds, int(elapsed_final)),
                "cpuSeconds": min(max_cpu_seconds, int(elapsed_final)),
            }
        )
        budget["remaining"].update(
            {
                "turns": max(0, max_turns - turns_completed),
                "candidates": max(0, max_candidates - len(experiment_ids)),
                "wallSeconds": max(0, max_wall_seconds - int(elapsed_final)),
                "cpuSeconds": max(0, max_cpu_seconds - int(elapsed_final)),
            }
        )
        final_session = load_session(project, session_id)
        _write_progress(
            staging,
            campaign_id=campaign_id,
            session_id=session_id,
            command_hash=command_hash,
            started_at=started.isoformat(),
            phase="terminal",
            status=status,
            message=reason,
            turn=turns_completed,
            budget=budget,
            experiment_ids=experiment_ids,
            verdicts=verdicts,
            experiment_definition_ref=resolved_experiment_definition_ref,
        )
        result = {
            "schemaVersion": SCHEMA_VERSION,
            "id": campaign_id,
            "sessionId": session_id,
            "status": status,
            "reason": reason,
            "startedAt": started.isoformat(),
            "completedAt": completed.isoformat(),
            "durationMs": int((time.monotonic() - monotonic_started) * 1000),
            "researcher": {
                "kind": "external-shell-command",
                "commandHash": command_hash,
            },
            "budget": budget,
            "turnsCompleted": turns_completed,
            "experiments": experiment_ids,
            "verdicts": verdicts,
            "initialLeader": initial_leader,
            "finalLeader": final_session.manifest["leader"],
            "errors": errors,
        }
        if resolved_experiment_definition_ref is not None:
            result["experimentDefinitionRef"] = resolved_experiment_definition_ref
        _write_json(staging / CAMPAIGN_RESULT, result)
        files = _campaign_file_hashes(staging)
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "id": campaign_id,
            "sessionId": session_id,
            "status": status,
            "completed": True,
            "resultHash": files[CAMPAIGN_RESULT],
            "files": files,
        }
        if resolved_experiment_definition_ref is not None:
            manifest["experimentDefinitionRef"] = resolved_experiment_definition_ref
        _write_json(staging / CAMPAIGN_MANIFEST, manifest)
        os.replace(staging, root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return load_campaign(project, load_session(project, session_id), campaign_id)


def _validate_campaign_budget(
    budget: Any,
    path: Path | str,
) -> list[ValidationIssue]:
    if not isinstance(budget, dict):
        return [_issue(path, "schema.type", "Campaign budget must be an object")]
    legacy = {"maxTurns", "maxWallSeconds", "turnTimeoutSeconds"}
    extended = legacy | {
        "maxCandidates",
        "maxCpuSeconds",
        "maxGpuSeconds",
        "maxCost",
        "costTelemetry",
        "executorPolicy",
        "stopConditions",
        "holdoutPolicy",
        "used",
        "remaining",
    }
    if set(budget) == legacy:
        issues: list[ValidationIssue] = []
    else:
        issues = _strict_keys(budget, extended, path)
    limits = {
        "maxTurns": (1, 100),
        "maxWallSeconds": (1, 86400),
        "turnTimeoutSeconds": (1, 3600),
    }
    for key, (minimum, maximum) in limits.items():
        item = budget.get(key)
        if (
            not isinstance(item, int)
            or isinstance(item, bool)
            or not minimum <= item <= maximum
        ):
            issues.append(_issue(f"{path}/{key}", "schema.range", f"Invalid budget {key}"))
    if set(budget) == legacy:
        return issues
    for key, minimum in (("maxCandidates", 1), ("maxCpuSeconds", 1), ("maxGpuSeconds", 0)):
        item = budget.get(key)
        if not isinstance(item, int) or isinstance(item, bool) or item < minimum:
            issues.append(_issue(f"{path}/{key}", "schema.range", f"Invalid budget {key}"))
    if isinstance(budget.get("maxCandidates"), int) and isinstance(budget.get("maxTurns"), int) and budget["maxCandidates"] > budget["maxTurns"]:
        issues.append(_issue(path, "campaign.budget", "Candidate ceiling exceeds turn ceiling"))
    max_cost = budget.get("maxCost")
    if max_cost is not None:
        issues.extend(_strict_keys(max_cost, {"currency", "amount"}, f"{path}/maxCost"))
    if budget.get("costTelemetry") not in {"available", "unknown", "not-applicable"}:
        issues.append(_issue(f"{path}/costTelemetry", "campaign.cost", "Invalid cost telemetry state"))
    executor = budget.get("executorPolicy")
    issues.extend(_strict_keys(executor, {"default", "privateRequested", "privateAvailable"}, f"{path}/executorPolicy"))
    if isinstance(executor, dict) and executor.get("default") != "cpu":
        issues.append(_issue(f"{path}/executorPolicy/default", "campaign.executor", "Public Campaign default must be CPU"))
    if not isinstance(budget.get("stopConditions"), list) or not budget["stopConditions"]:
        issues.append(_issue(f"{path}/stopConditions", "campaign.stop", "Campaign requires fixed stop conditions"))
    if budget.get("holdoutPolicy") != {"sealed": True}:
        issues.append(_issue(f"{path}/holdoutPolicy", "campaign.holdout", "Campaign holdout must remain sealed"))
    usage_keys = {"turns", "candidates", "wallSeconds", "cpuSeconds", "gpuSeconds", "cost"}
    for name in ("used", "remaining"):
        usage = budget.get(name)
        issues.extend(_strict_keys(usage, usage_keys, f"{path}/{name}"))
        if isinstance(usage, dict):
            for key in usage_keys - {"cost"}:
                if not isinstance(usage.get(key), int) or isinstance(usage.get(key), bool) or usage.get(key, -1) < 0:
                    issues.append(_issue(f"{path}/{name}/{key}", "schema.range", "Budget usage must be non-negative"))
            cost = usage.get("cost")
            issues.extend(_strict_keys(cost, {"known", "currency", "amount"}, f"{path}/{name}/cost"))
            if isinstance(cost, dict) and not isinstance(cost.get("known"), bool):
                issues.append(_issue(f"{path}/{name}/cost/known", "schema.boolean", "Cost knowledge must be boolean"))
    return issues


def _validate_campaign_result(
    value: dict[str, Any],
    path: Path,
    campaign_id: str,
    session_id: str,
) -> None:
    required = {
        "schemaVersion",
        "id",
        "sessionId",
        "status",
        "reason",
        "startedAt",
        "completedAt",
        "durationMs",
        "researcher",
        "budget",
        "turnsCompleted",
        "experiments",
        "verdicts",
        "initialLeader",
        "finalLeader",
        "errors",
    }
    optional = {"experimentDefinitionRef"}
    issues = _strict_keys(value, required, path, optional=optional)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(path, "schema.version", "Expected Campaign V1"))
    if value.get("id") != campaign_id or value.get("sessionId") != session_id:
        issues.append(_issue(path, "campaign.identity", "Campaign identity mismatch"))
    if value.get("status") not in CAMPAIGN_STATUSES:
        issues.append(_issue(path, "campaign.status", "Invalid Campaign status"))
    if not isinstance(value.get("reason"), str) or not value["reason"]:
        issues.append(_issue(path, "schema.string", "Campaign reason must be non-empty"))
    for key in ("startedAt", "completedAt"):
        if not isinstance(value.get(key), str) or not value[key]:
            issues.append(_issue(f"{path}/{key}", "schema.string", f"{key} must be non-empty"))
    if (
        not isinstance(value.get("durationMs"), int)
        or isinstance(value.get("durationMs"), bool)
        or value.get("durationMs", -1) < 0
    ):
        issues.append(_issue(path, "schema.number", "durationMs must be non-negative"))
    researcher = value.get("researcher")
    if not isinstance(researcher, dict):
        issues.append(_issue(path, "schema.type", "researcher must be an object"))
    else:
        issues.extend(
            _strict_keys(researcher, {"kind", "commandHash"}, f"{path}/researcher")
        )
        if researcher.get("kind") != "external-shell-command":
            issues.append(_issue(path, "campaign.researcher", "Invalid Researcher kind"))
        if not isinstance(researcher.get("commandHash"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", researcher.get("commandHash", "")
        ):
            issues.append(_issue(path, "schema.hash", "Invalid Researcher command hash"))
    budget = value.get("budget")
    issues.extend(_validate_campaign_budget(budget, f"{path}/budget"))
    turns = value.get("turnsCompleted")
    max_turns_value = budget.get("maxTurns") if isinstance(budget, dict) else None
    if (
        not isinstance(turns, int)
        or isinstance(turns, bool)
        or turns < 0
        or (
            isinstance(max_turns_value, int)
            and not isinstance(max_turns_value, bool)
            and turns > max_turns_value
        )
    ):
        issues.append(_issue(path, "campaign.turns", "Invalid completed turn count"))
    if not isinstance(value.get("experiments"), list) or not all(
        isinstance(item, str) and EXPERIMENT_ID.fullmatch(item)
        for item in value.get("experiments", [])
    ):
        issues.append(_issue(path, "campaign.experiments", "Invalid Experiment ids"))
    verdicts = value.get("verdicts")
    if not isinstance(verdicts, dict):
        issues.append(_issue(path, "schema.type", "verdicts must be an object"))
    else:
        issues.extend(
            _strict_keys(verdicts, {"KEEP", "REVERT", "CRASH"}, f"{path}/verdicts")
        )
        if any(
            not isinstance(verdicts.get(key), int)
            or isinstance(verdicts.get(key), bool)
            or verdicts.get(key, -1) < 0
            for key in ("KEEP", "REVERT", "CRASH")
        ):
            issues.append(_issue(path, "campaign.verdicts", "Invalid verdict counts"))
        elif isinstance(value.get("experiments"), list) and sum(verdicts.values()) != len(
            value["experiments"]
        ):
            issues.append(
                _issue(path, "campaign.verdicts", "Verdict counts differ from Experiments")
            )
    for key in ("initialLeader", "finalLeader"):
        leader = value.get(key)
        if not isinstance(leader, dict):
            issues.append(_issue(path, "schema.type", f"{key} must be an object"))
            continue
        issues.extend(
            _strict_keys(
                leader,
                {"runId", "sourceHash", "metric", "value"},
                f"{path}/{key}",
            )
        )
        if (
            not isinstance(leader.get("runId"), str)
            or not leader["runId"].startswith("run-")
            or not isinstance(leader.get("sourceHash"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", leader.get("sourceHash", ""))
            or not isinstance(leader.get("metric"), str)
            or not leader["metric"]
            or not isinstance(leader.get("value"), (int, float))
            or isinstance(leader.get("value"), bool)
            or not math.isfinite(float(leader.get("value", 0)))
        ):
            issues.append(_issue(path, "campaign.leader", f"Invalid {key} pointer"))
    errors = value.get("errors")
    if not isinstance(errors, list) or not all(
        isinstance(item, dict)
        and set(item) == {"code", "message"}
        and isinstance(item["code"], str)
        and bool(item["code"])
        and isinstance(item["message"], str)
        and bool(item["message"])
        for item in (errors if isinstance(errors, list) else [])
    ):
        issues.append(_issue(path, "campaign.errors", "Invalid Campaign errors"))
    elif value.get("status") == "failed" and not errors:
        issues.append(_issue(path, "campaign.errors", "Failed Campaign must record an error"))
    elif value.get("status") not in {"failed", "stopped_by_user"} and errors:
        issues.append(_issue(path, "campaign.errors", "Only failed or user-stopped Campaigns can record errors"))
    experiment_definition_ref = value.get("experimentDefinitionRef")
    if experiment_definition_ref is not None:
        if not isinstance(experiment_definition_ref, dict):
            issues.append(_issue(f"{path}/experimentDefinitionRef", "schema.type", "experimentDefinitionRef must be an object"))
        else:
            issues.extend(
                _strict_keys(experiment_definition_ref, {"id", "version", "contentHash"}, f"{path}/experimentDefinitionRef")
            )
            if not isinstance(experiment_definition_ref.get("id"), str) or not experiment_definition_ref["id"].strip():
                issues.append(_issue(f"{path}/experimentDefinitionRef/id", "schema.string", "id must be non-empty"))
            if (
                not isinstance(experiment_definition_ref.get("version"), int)
                or isinstance(experiment_definition_ref.get("version"), bool)
                or experiment_definition_ref.get("version", 0) < 1
            ):
                issues.append(_issue(f"{path}/experimentDefinitionRef/version", "schema.version", "version must be a positive integer"))
            if (
                not isinstance(experiment_definition_ref.get("contentHash"), str)
                or not re.fullmatch(r"^[0-9a-f]{64}$", experiment_definition_ref.get("contentHash", ""))
            ):
                issues.append(_issue(f"{path}/experimentDefinitionRef/contentHash", "schema.hash", "contentHash must be a lowercase SHA-256 hex digest"))
    if issues:
        raise AutoQuantValidationError(issues)


def _validate_campaign_progress(
    value: dict[str, Any],
    path: Path,
    *,
    campaign_id: str,
    session_id: str,
) -> None:
    required = {
        "schemaVersion",
        "kind",
        "campaignId",
        "sessionId",
        "status",
        "phase",
        "message",
        "startedAt",
        "updatedAt",
        "turn",
        "commandHash",
        "budget",
        "experiments",
        "verdicts",
    }
    optional_progress = {"experimentDefinitionRef"}
    issues = _strict_keys(value, required, path, optional=optional_progress)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(path, "schema.version", "Expected Campaign progress V1"))
    if value.get("kind") != "campaign-progress":
        issues.append(_issue(path, "progress.kind", "Invalid Campaign progress kind"))
    if (
        value.get("campaignId") != campaign_id
        or value.get("sessionId") != session_id
    ):
        issues.append(_issue(path, "progress.identity", "Progress identity mismatch"))
    status = value.get("status")
    if status not in {"running", *CAMPAIGN_STATUSES}:
        issues.append(_issue(path, "progress.status", "Invalid progress status"))
    phase = value.get("phase")
    if phase not in PROGRESS_PHASES:
        issues.append(_issue(path, "progress.phase", "Invalid progress phase"))
    if status == "running" and phase == "terminal":
        issues.append(_issue(path, "progress.phase", "Running progress cannot be terminal"))
    if status in CAMPAIGN_STATUSES and phase != "terminal":
        issues.append(_issue(path, "progress.phase", "Terminal progress must use terminal phase"))
    for key in ("message", "startedAt", "updatedAt"):
        if not isinstance(value.get(key), str) or not value[key]:
            issues.append(_issue(f"{path}/{key}", "schema.string", f"{key} must be non-empty"))
    if not isinstance(value.get("commandHash"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", value.get("commandHash", "")
    ):
        issues.append(_issue(path, "schema.hash", "Invalid Researcher command hash"))
    budget = value.get("budget")
    issues.extend(_validate_campaign_budget(budget, f"{path}/budget"))
    budget = budget if isinstance(budget, dict) else {}
    turn = value.get("turn")
    if (
        not isinstance(turn, int)
        or isinstance(turn, bool)
        or turn < 0
        or (
            isinstance(budget.get("maxTurns"), int)
            and turn > budget["maxTurns"]
        )
    ):
        issues.append(_issue(path, "progress.turn", "Invalid progress turn"))
    experiments = value.get("experiments")
    if not isinstance(experiments, list) or not all(
        isinstance(item, str) and EXPERIMENT_ID.fullmatch(item)
        for item in (experiments if isinstance(experiments, list) else [])
    ):
        issues.append(_issue(path, "progress.experiments", "Invalid progress Experiments"))
    verdicts = value.get("verdicts")
    if not isinstance(verdicts, dict):
        issues.append(_issue(path, "schema.type", "Progress verdicts must be an object"))
    else:
        issues.extend(
            _strict_keys(verdicts, {"KEEP", "REVERT", "CRASH"}, f"{path}/verdicts")
        )
        counts_valid = all(
            isinstance(verdicts.get(key), int)
            and not isinstance(verdicts.get(key), bool)
            and verdicts[key] >= 0
            for key in ("KEEP", "REVERT", "CRASH")
        )
        if not counts_valid:
            issues.append(_issue(path, "progress.verdicts", "Invalid progress verdicts"))
        elif isinstance(experiments, list) and sum(verdicts.values()) != len(experiments):
            issues.append(
                _issue(path, "progress.verdicts", "Progress verdicts differ from Experiments")
            )
    progress_ref = value.get("experimentDefinitionRef")
    if progress_ref is not None:
        if not isinstance(progress_ref, dict):
            issues.append(_issue(f"{path}/experimentDefinitionRef", "schema.type", "experimentDefinitionRef must be an object"))
        else:
            issues.extend(
                _strict_keys(progress_ref, {"id", "version", "contentHash"}, f"{path}/experimentDefinitionRef")
            )
            if not isinstance(progress_ref.get("id"), str) or not progress_ref["id"].strip():
                issues.append(_issue(f"{path}/experimentDefinitionRef/id", "schema.string", "id must be non-empty"))
            if (
                not isinstance(progress_ref.get("version"), int)
                or isinstance(progress_ref.get("version"), bool)
                or progress_ref.get("version", 0) < 1
            ):
                issues.append(_issue(f"{path}/experimentDefinitionRef/version", "schema.version", "version must be a positive integer"))
            if (
                not isinstance(progress_ref.get("contentHash"), str)
                or not re.fullmatch(r"^[0-9a-f]{64}$", progress_ref.get("contentHash", ""))
            ):
                issues.append(_issue(f"{path}/experimentDefinitionRef/contentHash", "schema.hash", "contentHash must be a lowercase SHA-256 hex digest"))
    if issues:
        raise AutoQuantValidationError(issues)


def list_campaign_progress(session: SessionContext) -> list[dict[str, Any]]:
    root = _campaigns_root(session)
    if not root.exists():
        return []
    values: list[dict[str, Any]] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if not entry.name.startswith(".campaign-") or not entry.name.endswith(
            ".creating"
        ):
            continue
        if entry.is_symlink() or not entry.is_dir():
            raise AutoQuantValidationError(
                [_issue(entry, "progress.entry", "Campaign progress must be a directory")]
            )
        campaign_id = entry.name[1 : -len(".creating")]
        if not CAMPAIGN_ID.fullmatch(campaign_id):
            raise AutoQuantValidationError(
                [_issue(entry, "campaign.id", "Invalid staged Campaign id")]
            )
        progress_path = entry / CAMPAIGN_PROGRESS
        if progress_path.is_symlink():
            raise AutoQuantValidationError(
                [_issue(progress_path, "path.symlink", "Campaign progress cannot be a symlink")]
            )
        if not progress_path.is_file():
            continue
        value = _read_json(progress_path, "campaign-progress")
        _validate_campaign_progress(
            value,
            progress_path,
            campaign_id=campaign_id,
            session_id=session.manifest["id"],
        )
        values.append(
            {
                **value,
                "mutable": True,
                "path": str(entry),
            }
        )
    return values


def load_campaign(
    project: ProjectContext,
    session: SessionContext,
    campaign_id: str,
) -> CampaignContext:
    root = _campaign_root(session, campaign_id)
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "campaign.missing", f"Unknown Campaign: {campaign_id}")]
        )
    manifest = _read_json(root / CAMPAIGN_MANIFEST, "campaign-manifest")
    required = {
        "schemaVersion",
        "id",
        "sessionId",
        "status",
        "completed",
        "resultHash",
        "files",
    }
    optional_manifest = {"experimentDefinitionRef"}
    issues = _strict_keys(manifest, required, root / CAMPAIGN_MANIFEST, optional=optional_manifest)
    files = manifest.get("files")
    actual = _campaign_file_hashes(root)
    if (
        manifest.get("schemaVersion") != SCHEMA_VERSION
        or manifest.get("id") != campaign_id
        or manifest.get("sessionId") != session.manifest["id"]
        or manifest.get("status") not in CAMPAIGN_STATUSES
        or manifest.get("completed") is not True
    ):
        issues.append(_issue(root, "campaign.manifest", "Invalid terminal Campaign manifest"))
    if not isinstance(files, dict) or files != actual:
        issues.append(_issue(root, "campaign.tampered", "Campaign files changed"))
    if isinstance(files, dict) and files.get(CAMPAIGN_RESULT) != manifest.get("resultHash"):
        issues.append(_issue(root, "campaign.result-hash", "Campaign result hash mismatch"))
    manifest_ref = manifest.get("experimentDefinitionRef")
    if manifest_ref is not None:
        if not isinstance(manifest_ref, dict):
            issues.append(_issue(root / CAMPAIGN_MANIFEST, "schema.type",
                                 "manifest experimentDefinitionRef must be an object"))
        else:
            issues.extend(
                _strict_keys(manifest_ref, {"id", "version", "contentHash"},
                             f"{root / CAMPAIGN_MANIFEST}/experimentDefinitionRef")
            )
            if not isinstance(manifest_ref.get("id"), str) or not manifest_ref["id"].strip():
                issues.append(_issue(f"{root / CAMPAIGN_MANIFEST}/experimentDefinitionRef/id",
                                     "schema.string", "id must be non-empty"))
            if (not isinstance(manifest_ref.get("version"), int)
                    or isinstance(manifest_ref.get("version"), bool)
                    or manifest_ref.get("version", 0) < 1):
                issues.append(_issue(f"{root / CAMPAIGN_MANIFEST}/experimentDefinitionRef/version",
                                     "schema.version", "version must be a positive integer"))
            if (not isinstance(manifest_ref.get("contentHash"), str)
                    or not re.fullmatch(r"^[0-9a-f]{64}$", manifest_ref.get("contentHash", ""))):
                issues.append(_issue(f"{root / CAMPAIGN_MANIFEST}/experimentDefinitionRef/contentHash",
                                     "schema.hash", "contentHash must be a lowercase SHA-256 hex digest"))
    if issues:
        raise AutoQuantValidationError(issues)
    result = _read_json(root / CAMPAIGN_RESULT, "campaign-result")
    _validate_campaign_result(
        result,
        root / CAMPAIGN_RESULT,
        campaign_id,
        session.manifest["id"],
    )
    if result["status"] != manifest["status"]:
        raise AutoQuantValidationError(
            [_issue(root, "campaign.status", "Campaign status differs from manifest")]
        )
    # Reference equality: all three artifacts must agree.
    # All absent  OR  all present and exactly equal.
    result_ref = result.get("experimentDefinitionRef")
    if manifest_ref is None and result_ref is not None:
        raise AutoQuantValidationError(
            [_issue(root, "campaign.experiment-definition-ref",
                    "result has experimentDefinitionRef but manifest does not")]
        )
    if manifest_ref is not None and result_ref is None:
        raise AutoQuantValidationError(
            [_issue(root, "campaign.experiment-definition-ref",
                    "manifest has experimentDefinitionRef but result does not")]
        )
    if manifest_ref is not None and result_ref is not None and manifest_ref != result_ref:
        raise AutoQuantValidationError(
            [_issue(root, "campaign.experiment-definition-ref",
                    "manifest experimentDefinitionRef does not match result")]
        )
    progress_path = root / CAMPAIGN_PROGRESS
    if progress_path.exists() or progress_path.is_symlink():
        progress = _read_json(progress_path, "campaign-progress")
        _validate_campaign_progress(
            progress,
            progress_path,
            campaign_id=campaign_id,
            session_id=session.manifest["id"],
        )
        if progress["status"] != result["status"]:
            raise AutoQuantValidationError(
                [_issue(root, "campaign.status", "Campaign progress differs from result")]
            )
        # Reference equality: progress must agree with result
        progress_ref = progress.get("experimentDefinitionRef")
        if result_ref is None and progress_ref is not None:
            raise AutoQuantValidationError(
                [_issue(root, "campaign.experiment-definition-ref",
                        "progress has experimentDefinitionRef but result does not")]
            )
        if result_ref is not None and progress_ref is None:
            raise AutoQuantValidationError(
                [_issue(root, "campaign.experiment-definition-ref",
                        "result has experimentDefinitionRef but progress does not")]
            )
        if result_ref is not None and progress_ref is not None and progress_ref != result_ref:
            raise AutoQuantValidationError(
                [_issue(root, "campaign.experiment-definition-ref",
                        "progress experimentDefinitionRef does not match result")]
            )
    _load_stop_request(root, campaign_id=campaign_id, session_id=session.manifest["id"])
    for experiment_id in result["experiments"]:
        load_experiment(project, session, experiment_id)
    if result_ref is not None:
        loaded_def = load_experiment_definition(
            project,
            session.manifest["id"],
            result_ref["id"],
            result_ref["version"],
        )
        if loaded_def.manifest["contentHash"] != result_ref["contentHash"]:
            raise AutoQuantValidationError(
                [_issue(root, "campaign.experiment-definition-ref",
                       "Referenced ExperimentDefinition contentHash mismatch; the artifact may have been tampered")]
            )
        if loaded_def.definition["status"] != "frozen":
            raise AutoQuantValidationError(
                [_issue(root, "campaign.experiment-definition-ref",
                       "Referenced ExperimentDefinition is no longer frozen")]
            )
    return CampaignContext(root, manifest, result)


def list_campaigns(
    project: ProjectContext,
    session: SessionContext,
) -> list[CampaignSummary]:
    root = _campaigns_root(session)
    if not root.exists():
        return []
    summaries: list[CampaignSummary] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir():
            raise AutoQuantValidationError(
                [_issue(entry, "campaign.entry", "Campaign entries must be directories")]
            )
        campaign = load_campaign(project, session, entry.name)
        result = campaign.result
        summaries.append(
            CampaignSummary(
                id=result["id"],
                status=result["status"],
                reason=result["reason"],
                turns_completed=result["turnsCompleted"],
                experiments=len(result["experiments"]),
                keeps=result["verdicts"]["KEEP"],
                reverts=result["verdicts"]["REVERT"],
                crashes=result["verdicts"]["CRASH"],
                started_at=result["startedAt"],
                completed_at=result["completedAt"],
                budget=result["budget"],
                path=str(campaign.root_dir),
            )
        )
    return summaries


RESEARCHER_RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant external Researcher response",
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "action",
                "strategy",
                "hypothesis",
                "expected_effect",
            ],
            "properties": {
                "schema_version": {"const": RESPONSE_VERSION},
                "action": {"const": "propose"},
                "strategy": {"type": "string", "minLength": 1},
                "hypothesis": {"type": "string", "minLength": 1},
                "expected_effect": {"type": "string", "minLength": 1},
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "action", "reason"],
            "properties": {
                "schema_version": {"const": RESPONSE_VERSION},
                "action": {"const": "stop"},
                "reason": {"type": "string", "minLength": 1},
            },
        },
    ],
}


_LEGACY_CAMPAIGN_BUDGET_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["maxTurns", "maxWallSeconds", "turnTimeoutSeconds"],
    "properties": {
        "maxTurns": {"type": "integer", "minimum": 1, "maximum": 100},
        "maxWallSeconds": {"type": "integer", "minimum": 1, "maximum": 86400},
        "turnTimeoutSeconds": {"type": "integer", "minimum": 1, "maximum": 3600},
    },
}

_CAMPAIGN_USAGE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["turns", "candidates", "wallSeconds", "cpuSeconds", "gpuSeconds", "cost"],
    "properties": {
        "turns": {"type": "integer", "minimum": 0},
        "candidates": {"type": "integer", "minimum": 0},
        "wallSeconds": {"type": "integer", "minimum": 0},
        "cpuSeconds": {"type": "integer", "minimum": 0},
        "gpuSeconds": {"type": "integer", "minimum": 0},
        "cost": {
            "type": "object",
            "additionalProperties": False,
            "required": ["known", "currency", "amount"],
            "properties": {
                "known": {"type": "boolean"},
                "currency": {"type": ["string", "null"]},
                "amount": {"type": ["number", "null"]},
            },
        },
    },
}

CAMPAIGN_BUDGET_JSON_SCHEMA: dict[str, Any] = {
    "oneOf": [
        _LEGACY_CAMPAIGN_BUDGET_JSON_SCHEMA,
        {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "maxTurns", "maxCandidates", "maxWallSeconds", "turnTimeoutSeconds",
                "maxCpuSeconds", "maxGpuSeconds", "maxCost", "costTelemetry",
                "executorPolicy", "stopConditions", "holdoutPolicy", "used", "remaining",
            ],
            "properties": {
                **_LEGACY_CAMPAIGN_BUDGET_JSON_SCHEMA["properties"],
                "maxCandidates": {"type": "integer", "minimum": 1, "maximum": 100},
                "maxCpuSeconds": {"type": "integer", "minimum": 1, "maximum": 86400},
                "maxGpuSeconds": {"type": "integer", "minimum": 0, "maximum": 86400},
                "maxCost": {
                    "oneOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["currency", "amount"],
                            "properties": {
                                "currency": {"type": "string", "minLength": 1},
                                "amount": {"type": "number", "exclusiveMinimum": 0},
                            },
                        },
                    ]
                },
                "costTelemetry": {"enum": ["available", "unknown", "not-applicable"]},
                "executorPolicy": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["default", "privateRequested", "privateAvailable"],
                    "properties": {
                        "default": {"const": "cpu"},
                        "privateRequested": {"type": "boolean"},
                        "privateAvailable": {"type": "boolean"},
                    },
                },
                "stopConditions": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
                "holdoutPolicy": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["sealed"],
                    "properties": {"sealed": {"const": True}},
                },
                "used": _CAMPAIGN_USAGE_JSON_SCHEMA,
                "remaining": _CAMPAIGN_USAGE_JSON_SCHEMA,
            },
        },
    ]
}


CAMPAIGN_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant external Research Campaign result",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "id",
        "sessionId",
        "status",
        "reason",
        "startedAt",
        "completedAt",
        "durationMs",
        "researcher",
        "budget",
        "turnsCompleted",
        "experiments",
        "verdicts",
        "initialLeader",
        "finalLeader",
        "errors",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "id": {
            "type": "string",
            "pattern": CAMPAIGN_ID.pattern,
        },
        "sessionId": {"type": "string", "minLength": 1},
        "status": {"enum": sorted(CAMPAIGN_STATUSES)},
        "reason": {"type": "string", "minLength": 1},
        "startedAt": {"type": "string", "minLength": 1},
        "completedAt": {"type": "string", "minLength": 1},
        "durationMs": {"type": "integer", "minimum": 0},
        "researcher": {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "commandHash"],
            "properties": {
                "kind": {"const": "external-shell-command"},
                "commandHash": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        },
        "budget": CAMPAIGN_BUDGET_JSON_SCHEMA,
        "turnsCompleted": {"type": "integer", "minimum": 0},
        "experiments": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": EXPERIMENT_ID.pattern,
            },
        },
        "verdicts": {
            "type": "object",
            "additionalProperties": False,
            "required": ["KEEP", "REVERT", "CRASH"],
            "properties": {
                "KEEP": {"type": "integer", "minimum": 0},
                "REVERT": {"type": "integer", "minimum": 0},
                "CRASH": {"type": "integer", "minimum": 0},
            },
        },
        "experimentDefinitionRef": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "version", "contentHash"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "version": {"type": "integer", "minimum": 1},
                "contentHash": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        },
        "initialLeader": {"$ref": "#/$defs/leader"},
        "finalLeader": {"$ref": "#/$defs/leader"},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "message"],
                "properties": {
                    "code": {"type": "string", "minLength": 1},
                    "message": {"type": "string", "minLength": 1},
                },
            },
        },
    },
    "$defs": {
        "leader": {
            "type": "object",
            "additionalProperties": False,
            "required": ["runId", "sourceHash", "metric", "value"],
            "properties": {
                "runId": {"type": "string", "pattern": "^run-"},
                "sourceHash": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "metric": {"type": "string", "minLength": 1},
                "value": {"type": "number"},
            },
        }
    },
    "allOf": [
        {
            "if": {"properties": {"status": {"const": "failed"}}},
            "then": {"properties": {"errors": {"minItems": 1}}},
        },
        {
            "if": {
                "properties": {
                    "status": {
                        "not": {"enum": ["failed", "stopped_by_user"]}
                    }
                }
            },
            "then": {"properties": {"errors": {"maxItems": 0}}},
        },
    ],
}


CAMPAIGN_PROGRESS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant mutable Research Campaign progress",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "campaignId",
        "sessionId",
        "status",
        "phase",
        "message",
        "startedAt",
        "updatedAt",
        "turn",
        "commandHash",
        "budget",
        "experiments",
        "verdicts",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": "campaign-progress"},
        "campaignId": {"type": "string", "pattern": CAMPAIGN_ID.pattern},
        "sessionId": {"type": "string", "minLength": 1},
        "status": {"enum": ["running", *sorted(CAMPAIGN_STATUSES)]},
        "phase": {"enum": sorted(PROGRESS_PHASES)},
        "message": {"type": "string", "minLength": 1},
        "startedAt": {"type": "string", "minLength": 1},
        "updatedAt": {"type": "string", "minLength": 1},
        "turn": {"type": "integer", "minimum": 0},
        "commandHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "budget": CAMPAIGN_RESULT_JSON_SCHEMA["properties"]["budget"],
        "experiments": CAMPAIGN_RESULT_JSON_SCHEMA["properties"]["experiments"],
        "verdicts": CAMPAIGN_RESULT_JSON_SCHEMA["properties"]["verdicts"],
        "experimentDefinitionRef": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "version", "contentHash"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "version": {"type": "integer", "minimum": 1},
                "contentHash": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        },
    },
}
