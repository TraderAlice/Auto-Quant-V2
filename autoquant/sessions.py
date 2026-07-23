"""Governed research Sessions, Experiments, and source promotion."""

from __future__ import annotations

import difflib
import json
import math
import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .runs import RunContext, execute_study, harness_identity, load_run
from .studies import (
    StudyContext,
    copy_hashed_files,
    hash_file,
    hash_json,
    load_study,
    path_matches_pattern,
)
from .workspace import (
    PROJECT_MANIFEST,
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
    load_project,
)


SESSION_MANIFEST = "session.json"
EXPERIMENT_RESULT = "result.json"
EXPERIMENT_CHANGES = "changes.json"
EXPERIMENT_DIFF = "diff.patch"
EXPERIMENT_MANIFEST = "manifest.json"
PROMOTION_RECEIPT = "promotion.json"
SESSION_ID = re.compile(
    r"^session-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$"
)
EXPERIMENT_ID = re.compile(r"^exp-[0-9]{4}-[0-9a-f]{12}$")
SESSION_STATUSES = {"active", "promoted"}
VERDICTS = {"KEEP", "REVERT", "CRASH"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SessionContext:
    root_dir: Path
    manifest_path: Path
    manifest: dict[str, Any]
    worktree_project: ProjectContext
    baseline_run: RunContext
    leader_run: RunContext


@dataclass(frozen=True)
class SessionSummary:
    id: str
    status: str
    study_id: str
    baseline_run_id: str
    leader_run_id: str
    leader_value: float
    experiments: int
    updated_at: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "studyId": self.study_id,
            "baselineRunId": self.baseline_run_id,
            "leaderRunId": self.leader_run_id,
            "leaderValue": self.leader_value,
            "experiments": self.experiments,
            "updatedAt": self.updated_at,
            "path": self.path,
        }


@dataclass(frozen=True)
class ExperimentContext:
    root_dir: Path
    manifest: dict[str, Any]
    result: dict[str, Any]
    changes: list[dict[str, Any]]


@dataclass(frozen=True)
class ExperimentSummary:
    id: str
    sequence: int
    verdict: str
    hypothesis: str
    leader_value: float
    candidate_value: float | None
    improvement: float | None
    run_id: str
    completed_at: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sequence": self.sequence,
            "verdict": self.verdict,
            "hypothesis": self.hypothesis,
            "leaderValue": self.leader_value,
            "candidateValue": self.candidate_value,
            "improvement": self.improvement,
            "runId": self.run_id,
            "completedAt": self.completed_at,
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
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    _write_json(temporary, value)
    os.replace(temporary, path)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.missing", f"Missing {label} JSON: {path}")]
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
            [_issue(path, f"{label}.type", f"{label} JSON must be an object")]
        )
    return value


def _strict_keys(
    value: dict[str, Any],
    required: set[str],
    path: Path | str,
) -> list[ValidationIssue]:
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - required)
    )
    return issues


def _sessions_root(project: ProjectContext) -> Path:
    return confined_path(
        project.root_dir,
        project.manifest.directories["sessions"],
        "project/directories/sessions",
    )


def _session_root(project: ProjectContext, session_id: str) -> Path:
    if not SESSION_ID.fullmatch(session_id):
        raise AutoQuantValidationError(
            [_issue(session_id, "session.id", "Invalid Session id")]
        )
    return confined_path(_sessions_root(project), session_id, f"session/{session_id}")


def _experiment_root(session: SessionContext, experiment_id: str) -> Path:
    if not EXPERIMENT_ID.fullmatch(experiment_id):
        raise AutoQuantValidationError(
            [_issue(experiment_id, "experiment.id", "Invalid Experiment id")]
        )
    experiments = confined_path(
        session.root_dir,
        "experiments",
        f"{session.manifest_path}/experiments",
    )
    return confined_path(experiments, experiment_id, f"experiment/{experiment_id}")


def _metric_value(run: RunContext) -> float:
    metric = run.result["objective"]["metric"]
    value = run.result["metrics"].get(metric)
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or run.result["status"] != "succeeded"
    ):
        raise AutoQuantValidationError(
            [
                _issue(
                    run.root_dir / "result.json",
                    "session.baseline",
                    f"Run must be successful with finite primary metric '{metric}'",
                )
            ]
        )
    return float(value)


def _run_source_hashes(run: RunContext) -> dict[str, str]:
    paths = run.result["subject"].get("sourcePaths")
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        raise AutoQuantValidationError(
            [_issue(run.root_dir, "run.source-paths", "Run sourcePaths are invalid")]
        )
    hashes: dict[str, str] = {}
    for relative in paths:
        candidate = PurePosixPath(relative)
        if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
            raise AutoQuantValidationError(
                [_issue(relative, "run.source-path", "Run source path is not confined")]
            )
        path = run.root_dir / "sources" / relative
        if path.is_symlink() or not path.is_file():
            raise AutoQuantValidationError(
                [_issue(path, "run.source-missing", "Run source file is missing")]
            )
        hashes[relative] = hash_file(path)
    hashes = dict(sorted(hashes.items()))
    if hash_json(hashes) != run.result["subject"].get("sourceHash"):
        raise AutoQuantValidationError(
            [_issue(run.root_dir, "run.source-hash", "Run sourceHash is inconsistent")]
        )
    return hashes


def _fixed_inventory(
    worktree: ProjectContext,
    editable_patterns: list[str],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(worktree.root_dir.rglob("*")):
        relative = path.relative_to(worktree.root_dir).as_posix()
        if path.is_symlink():
            raise AutoQuantValidationError(
                [_issue(path, "path.symlink", "Session worktree cannot contain symlinks")]
            )
        if not path.is_file():
            continue
        if any(path_matches_pattern(relative, pattern) for pattern in editable_patterns):
            continue
        hashes[relative] = hash_file(path)
    return hashes


def _copy_project_file(project: ProjectContext, relative: str, target: Path) -> None:
    source = confined_path(project.root_dir, relative, f"project/{relative}")
    if source.is_symlink() or not source.is_file():
        raise AutoQuantValidationError(
            [_issue(source, "session.source", f"Missing fixed Project file: {relative}")]
        )
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _materialize_worktree(
    project: ProjectContext,
    study: StudyContext,
    session_staging: Path,
) -> ProjectContext:
    worktree_root = session_staging / "worktree" / project.manifest.id
    worktree_root.mkdir(parents=True)
    shutil.copy2(project.root_dir / PROJECT_MANIFEST, worktree_root / PROJECT_MANIFEST)
    _copy_project_file(
        project,
        project.manifest.research_program,
        worktree_root,
    )
    for relative in project.manifest.directories.values():
        (worktree_root / relative).mkdir(parents=True)

    study_relative = (
        Path(project.manifest.directories["studies"])
        / study.definition.id
        / "study.json"
    ).as_posix()
    program_relative = (
        Path(project.manifest.directories["studies"])
        / study.definition.id
        / study.definition.program
    ).as_posix()
    _copy_project_file(project, study_relative, worktree_root)
    _copy_project_file(project, program_relative, worktree_root)
    copy_hashed_files(project, study.judge_hashes, worktree_root)
    copy_hashed_files(project, study.editable_hashes, worktree_root)
    return load_project(worktree_root, expected_id=project.manifest.id)


def _session_lock(study: StudyContext, baseline: RunContext) -> dict[str, Any]:
    return {
        "studyHash": study.study_hash,
        "programHash": study.program_hash,
        "judgeHash": study.judge_hash,
        "datasetHash": study.dataset_hash,
        "harness": baseline.result["harness"],
    }


def _run_pointer(run: RunContext) -> dict[str, Any]:
    return {
        "runId": run.result["id"],
        "sourceHash": run.result["subject"]["sourceHash"],
        "metric": run.result["objective"]["metric"],
        "value": _metric_value(run),
    }


def start_session(project: ProjectContext, study_id: str) -> SessionContext:
    study = load_study(project, study_id)
    baseline = execute_study(project, study_id)
    if baseline.result["status"] != "succeeded":
        raise AutoQuantValidationError(
            [
                _issue(
                    baseline.root_dir,
                    "session.baseline-failed",
                    "Cannot start a research Session from a failed baseline Run "
                    f"({baseline.result['id']})",
                )
            ]
        )
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
    identity = hash_json(
        {
            "project": project.manifest.id,
            "study": study.definition.id,
            "baseline": baseline.result["id"],
            "startedAt": started.isoformat(),
        }
    )
    session_id = f"session-{stamp}-{identity[:12]}"
    target = _session_root(project, session_id)
    temporary = _sessions_root(project) / f".{session_id}.creating"
    if target.exists() or target.is_symlink() or temporary.exists():
        raise AutoQuantValidationError(
            [_issue(target, "session.collision", "Session path already exists")]
        )
    try:
        temporary.mkdir()
        worktree = _materialize_worktree(project, study, temporary)
        worktree_study = load_study(worktree, study_id)
        fixed_hashes = _fixed_inventory(
            worktree,
            worktree_study.definition.editable["paths"],
        )
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "id": session_id,
            "status": "active",
            "projectId": project.manifest.id,
            "studyId": study.definition.id,
            "createdAt": started.isoformat(),
            "updatedAt": started.isoformat(),
            "worktree": f"worktree/{project.manifest.id}",
            "editablePaths": study.definition.editable["paths"],
            "baseProjectSourceHash": study.source_hash,
            "baseline": _run_pointer(baseline),
            "leader": _run_pointer(baseline),
            "locks": {
                **_session_lock(study, baseline),
                "fixedHashes": fixed_hashes,
            },
            "nextExperiment": 1,
        }
        (temporary / "experiments").mkdir()
        _write_json(temporary / SESSION_MANIFEST, manifest)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return load_session(project, session_id)


def _validate_session_manifest(
    value: dict[str, Any],
    path: Path,
    expected_id: str,
) -> None:
    required = {
        "schemaVersion",
        "id",
        "status",
        "projectId",
        "studyId",
        "createdAt",
        "updatedAt",
        "worktree",
        "editablePaths",
        "baseProjectSourceHash",
        "baseline",
        "leader",
        "locks",
        "nextExperiment",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected V1"))
    if value.get("id") != expected_id:
        issues.append(_issue(f"{path}/id", "session.directory-id", "Session id mismatch"))
    if value.get("status") not in SESSION_STATUSES:
        issues.append(_issue(f"{path}/status", "schema.choice", "Invalid Session status"))
    if not isinstance(value.get("projectId"), str) or not value["projectId"]:
        issues.append(_issue(f"{path}/projectId", "schema.string", "Invalid projectId"))
    if not isinstance(value.get("studyId"), str) or not value["studyId"]:
        issues.append(_issue(f"{path}/studyId", "schema.string", "Invalid studyId"))
    for key in ("createdAt", "updatedAt", "worktree"):
        if not isinstance(value.get(key), str) or not value[key]:
            issues.append(_issue(f"{path}/{key}", "schema.string", f"Invalid {key}"))
    editable_paths = value.get("editablePaths")
    if (
        not isinstance(editable_paths, list)
        or not editable_paths
        or not all(isinstance(item, str) and item for item in editable_paths)
    ):
        issues.append(
            _issue(f"{path}/editablePaths", "schema.array", "Invalid editablePaths")
        )
    if (
        not isinstance(value.get("nextExperiment"), int)
        or isinstance(value.get("nextExperiment"), bool)
        or value.get("nextExperiment", 0) < 1
    ):
        issues.append(
            _issue(
                f"{path}/nextExperiment",
                "schema.number",
                "nextExperiment must be a positive integer",
            )
        )
    for key in ("baseline", "leader"):
        pointer = value.get(key)
        if not isinstance(pointer, dict):
            issues.append(_issue(f"{path}/{key}", "schema.type", f"{key} must be an object"))
            continue
        issues.extend(
            _strict_keys(
                pointer,
                {"runId", "sourceHash", "metric", "value"},
                f"{path}/{key}",
            )
        )
        if isinstance(pointer, dict):
            if not isinstance(pointer.get("runId"), str) or not pointer["runId"].startswith("run-"):
                issues.append(_issue(f"{path}/{key}/runId", "schema.string", "Invalid Run id"))
            if not isinstance(pointer.get("sourceHash"), str) or not SHA256.fullmatch(
                pointer.get("sourceHash", "")
            ):
                issues.append(_issue(f"{path}/{key}/sourceHash", "schema.hash", "Invalid sourceHash"))
            if not isinstance(pointer.get("metric"), str) or not pointer["metric"]:
                issues.append(_issue(f"{path}/{key}/metric", "schema.string", "Invalid metric"))
            pointer_value = pointer.get("value")
            if (
                not isinstance(pointer_value, (int, float))
                or isinstance(pointer_value, bool)
                or not math.isfinite(float(pointer_value))
            ):
                issues.append(_issue(f"{path}/{key}/value", "schema.number", "Invalid metric value"))
    if not isinstance(value.get("baseProjectSourceHash"), str) or not SHA256.fullmatch(
        value.get("baseProjectSourceHash", "")
    ):
        issues.append(
            _issue(
                f"{path}/baseProjectSourceHash",
                "schema.hash",
                "Invalid baseProjectSourceHash",
            )
        )
    locks = value.get("locks")
    if not isinstance(locks, dict):
        issues.append(_issue(f"{path}/locks", "schema.type", "locks must be an object"))
    else:
        issues.extend(
            _strict_keys(
                locks,
                {
                    "studyHash",
                    "programHash",
                    "judgeHash",
                    "datasetHash",
                    "harness",
                    "fixedHashes",
                },
                f"{path}/locks",
            )
        )
        fixed = locks.get("fixedHashes")
        if not isinstance(fixed, dict) or not all(
            isinstance(key, str) and isinstance(item, str)
            for key, item in (fixed.items() if isinstance(fixed, dict) else [])
        ):
            issues.append(
                _issue(f"{path}/locks/fixedHashes", "schema.map", "Invalid fixedHashes")
            )
        elif any(not SHA256.fullmatch(item) for item in fixed.values()):
            issues.append(
                _issue(f"{path}/locks/fixedHashes", "schema.hash", "Invalid fixed file hash")
            )
        for key in ("studyHash", "programHash", "judgeHash", "datasetHash"):
            if not isinstance(locks.get(key), str) or not SHA256.fullmatch(locks.get(key, "")):
                issues.append(_issue(f"{path}/locks/{key}", "schema.hash", f"Invalid {key}"))
        harness = locks.get("harness")
        if not isinstance(harness, dict):
            issues.append(_issue(f"{path}/locks/harness", "schema.type", "Invalid Harness lock"))
        else:
            issues.extend(
                _strict_keys(
                    harness,
                    {"id", "version", "commit", "dirty", "sourceHash", "python"},
                    f"{path}/locks/harness",
                )
            )
            if not isinstance(harness.get("dirty"), bool):
                issues.append(_issue(f"{path}/locks/harness/dirty", "schema.boolean", "Invalid dirty flag"))
            if not isinstance(harness.get("sourceHash"), str) or not SHA256.fullmatch(
                harness.get("sourceHash", "")
            ):
                issues.append(_issue(f"{path}/locks/harness/sourceHash", "schema.hash", "Invalid Harness hash"))
    if issues:
        raise AutoQuantValidationError(issues)


def load_session(project: ProjectContext, session_id: str) -> SessionContext:
    root = _session_root(project, session_id)
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "session.missing", f"Unknown Session: {session_id}")]
        )
    manifest_path = root / SESSION_MANIFEST
    manifest = _read_json(manifest_path, "session")
    _validate_session_manifest(manifest, manifest_path, session_id)
    if manifest["projectId"] != project.manifest.id:
        raise AutoQuantValidationError(
            [_issue(manifest_path, "session.project", "Session Project id mismatch")]
        )
    expected_worktree = f"worktree/{project.manifest.id}"
    if manifest["worktree"] != expected_worktree:
        raise AutoQuantValidationError(
            [_issue(manifest_path, "session.worktree", "Unexpected Session worktree path")]
        )
    worktree_root = confined_path(root, manifest["worktree"], "session/worktree")
    worktree = load_project(worktree_root, expected_id=project.manifest.id)
    baseline = load_run(project, manifest["baseline"]["runId"])
    leader = load_run(project, manifest["leader"]["runId"])
    for key, run in (("baseline", baseline), ("leader", leader)):
        pointer = manifest[key]
        if (
            run.result["study"]["id"] != manifest["studyId"]
            or run.result["subject"]["sourceHash"] != pointer["sourceHash"]
            or run.result["objective"]["metric"] != pointer["metric"]
            or _metric_value(run) != float(pointer["value"])
        ):
            raise AutoQuantValidationError(
                [_issue(manifest_path, "session.run-pointer", f"Invalid {key} Run pointer")]
            )
    receipt_path = root / PROMOTION_RECEIPT
    if manifest["status"] == "active" and (receipt_path.exists() or receipt_path.is_symlink()):
        raise AutoQuantValidationError(
            [_issue(receipt_path, "promotion.uncommitted", "Active Session has a promotion receipt")]
        )
    if manifest["status"] == "promoted":
        receipt = _read_json(receipt_path, "promotion")
        receipt_required = {
            "schemaVersion",
            "id",
            "sessionId",
            "projectId",
            "studyId",
            "leaderRunId",
            "beforeSourceHash",
            "afterSourceHash",
            "sourceHashes",
            "promotedAt",
        }
        receipt_issues = _strict_keys(receipt, receipt_required, receipt_path)
        if (
            receipt.get("schemaVersion") != SCHEMA_VERSION
            or receipt.get("sessionId") != session_id
            or receipt.get("projectId") != project.manifest.id
            or receipt.get("studyId") != manifest["studyId"]
            or receipt.get("leaderRunId") != manifest["leader"]["runId"]
            or receipt.get("beforeSourceHash") != manifest["baseProjectSourceHash"]
            or receipt.get("afterSourceHash") != manifest["leader"]["sourceHash"]
            or receipt.get("sourceHashes") != _run_source_hashes(leader)
        ):
            receipt_issues.append(
                _issue(receipt_path, "promotion.receipt", "Promotion receipt differs from Session leader")
            )
        if receipt_issues:
            raise AutoQuantValidationError(receipt_issues)
    return SessionContext(root, manifest_path, manifest, worktree, baseline, leader)


def list_sessions(project: ProjectContext) -> list[SessionSummary]:
    summaries: list[SessionSummary] = []
    for entry in sorted(_sessions_root(project).iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir():
            raise AutoQuantValidationError(
                [_issue(entry, "session.entry", "Session entries must be real directories")]
            )
        session = load_session(project, entry.name)
        summaries.append(
            SessionSummary(
                id=session.manifest["id"],
                status=session.manifest["status"],
                study_id=session.manifest["studyId"],
                baseline_run_id=session.manifest["baseline"]["runId"],
                leader_run_id=session.manifest["leader"]["runId"],
                leader_value=float(session.manifest["leader"]["value"]),
                experiments=session.manifest["nextExperiment"] - 1,
                updated_at=session.manifest["updatedAt"],
                path=str(session.root_dir),
            )
        )
    return summaries


def _history_issues(
    project: ProjectContext,
    session: SessionContext,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected = dict(session.manifest["baseline"])
    experiments = list_experiments(project, session)
    for sequence, experiment in enumerate(experiments, start=1):
        result = load_experiment(project, session, experiment.id).result
        if result["sequence"] != sequence:
            issues.append(
                _issue(
                    experiment.path,
                    "session.history-sequence",
                    f"Expected Experiment sequence {sequence}",
                )
            )
        if result["leader"] != expected:
            issues.append(
                _issue(
                    experiment.path,
                    "session.history-leader",
                    "Experiment leader does not match the preceding KEEP chain",
                )
            )
        run = load_run(project, result["candidate"]["runId"])
        if result["objective"] != run.result["objective"]:
            issues.append(
                _issue(
                    experiment.path,
                    "session.history-objective",
                    "Experiment objective differs from its candidate Run",
                )
            )
        if result["errors"] != run.result["errors"]:
            issues.append(
                _issue(
                    experiment.path,
                    "session.history-errors",
                    "Experiment errors differ from its candidate Run",
                )
            )
        if run.result["status"] == "failed":
            expected_verdict = "CRASH"
            expected_value = None
            expected_improvement = None
        else:
            expected_value = _metric_value(run)
            direction = run.result["objective"]["direction"]
            expected_improvement = (
                expected_value - float(expected["value"])
                if direction == "maximize"
                else float(expected["value"]) - expected_value
            )
            minimum = float(run.result["objective"]["minimumImprovement"])
            expected_verdict = (
                "KEEP"
                if expected_improvement > 0
                and expected_improvement >= minimum
                else "REVERT"
            )
        if (
            result["candidate"]["metric"] != run.result["objective"]["metric"]
            or result["candidate"]["value"] != expected_value
            or result["improvement"] != expected_improvement
            or result["verdict"] != expected_verdict
        ):
            issues.append(
                _issue(
                    experiment.path,
                    "session.history-verdict",
                    "Experiment verdict or comparison differs from its immutable Run",
                )
            )
        if expected_verdict == "KEEP":
            expected = dict(result["candidate"])
    if session.manifest["leader"] != expected:
        issues.append(
            _issue(
                session.manifest_path,
                "session.leader-chain",
                "Session leader does not match immutable KEEP history",
            )
        )
    if session.manifest["nextExperiment"] != len(experiments) + 1:
        issues.append(
            _issue(
                session.manifest_path,
                "session.history-count",
                "Session nextExperiment does not match immutable history",
            )
        )
    return issues


def _authority_issues(
    project: ProjectContext,
    session: SessionContext,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = session.manifest
    locks = manifest["locks"]
    try:
        canonical = load_study(project, manifest["studyId"])
        worktree = load_study(session.worktree_project, manifest["studyId"])
    except AutoQuantValidationError as error:
        return list(error.issues)
    for label, study in (("Project", canonical), ("worktree", worktree)):
        actual = {
            "studyHash": study.study_hash,
            "programHash": study.program_hash,
            "judgeHash": study.judge_hash,
            "datasetHash": study.dataset_hash,
        }
        for key, value in actual.items():
            if value != locks[key]:
                issues.append(
                    _issue(
                        session.manifest_path,
                        "session.lock-stale",
                        f"{label} {key} differs from the Session lock",
                    )
                )
    if worktree.definition.editable["paths"] != manifest["editablePaths"]:
        issues.append(
            _issue(
                session.manifest_path,
                "session.editable-stale",
                "Worktree editable paths differ from the Session",
            )
        )
    try:
        fixed = _fixed_inventory(
            session.worktree_project,
            manifest["editablePaths"],
        )
        if fixed != locks["fixedHashes"]:
            issues.append(
                _issue(
                    session.worktree_project.root_dir,
                    "session.fixed-modified",
                    "Session worktree files outside the editable closure changed",
                )
            )
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
    if harness_identity() != locks["harness"]:
        issues.append(
            _issue(
                session.manifest_path,
                "session.harness-stale",
                "Installed Harness differs from the Session baseline",
            )
        )
    try:
        issues.extend(_history_issues(project, session))
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
    return issues


def validate_session_authority(
    project: ProjectContext,
    session: SessionContext,
) -> StudyContext:
    issues = _authority_issues(project, session)
    if issues:
        raise AutoQuantValidationError(issues)
    return load_study(session.worktree_project, session.manifest["studyId"])


def session_snapshot(
    project: ProjectContext,
    session: SessionContext,
) -> dict[str, Any]:
    issues = _authority_issues(project, session)
    candidate: dict[str, Any] | None = None
    program_relative = "program.md"
    try:
        study = load_study(session.worktree_project, session.manifest["studyId"])
        program_relative = study.definition.program
        candidate = {
            "sourceHash": study.source_hash,
            "sourceHashes": study.editable_hashes,
            "differsFromLeader": (
                study.source_hash != session.manifest["leader"]["sourceHash"]
            ),
        }
    except AutoQuantValidationError:
        pass
    return {
        "session": session.manifest,
        "path": str(session.root_dir),
        "worktree": str(session.worktree_project.root_dir),
        "programPath": str(
            session.worktree_project.root_dir
            / session.worktree_project.manifest.directories["studies"]
            / session.manifest["studyId"]
            / program_relative
        ),
        "candidate": candidate,
        "authority": {
            "valid": not issues,
            "issues": [issue.to_dict() for issue in issues],
        },
        "experiments": [
            summary.to_dict() for summary in list_experiments(project, session)
        ],
    }


def _source_changes(
    leader: RunContext,
    candidate: StudyContext,
    candidate_project: ProjectContext,
) -> tuple[list[dict[str, Any]], str]:
    before = _run_source_hashes(leader)
    after = candidate.editable_hashes
    changes: list[dict[str, Any]] = []
    patches: list[str] = []
    for relative in sorted(before.keys() | after.keys()):
        before_hash = before.get(relative)
        after_hash = after.get(relative)
        if before_hash == after_hash:
            continue
        kind = "modified"
        if before_hash is None:
            kind = "added"
        elif after_hash is None:
            kind = "deleted"
        changes.append(
            {
                "path": relative,
                "kind": kind,
                "beforeHash": before_hash,
                "afterHash": after_hash,
            }
        )
        before_path = leader.root_dir / "sources" / relative
        after_path = candidate_project.root_dir / relative
        try:
            before_text = (
                before_path.read_text(encoding="utf-8").splitlines(keepends=True)
                if before_path.is_file()
                else []
            )
            after_text = (
                after_path.read_text(encoding="utf-8").splitlines(keepends=True)
                if after_path.is_file()
                else []
            )
        except UnicodeDecodeError:
            continue
        patches.extend(
            difflib.unified_diff(
                before_text,
                after_text,
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    return changes, "".join(patches)


def _clear_editable(project: ProjectContext, study: StudyContext) -> None:
    files: set[str] = set()
    for pattern in study.definition.editable["paths"]:
        closure = pattern.endswith("/**")
        relative = pattern[:-3] if closure else pattern
        root = confined_path(project.root_dir, relative, f"editable/{pattern}")
        if root.is_symlink():
            raise AutoQuantValidationError(
                [_issue(root, "path.symlink", "Editable source cannot be a symlink")]
            )
        if closure:
            if not root.exists():
                root.mkdir(parents=True)
                continue
            if not root.is_dir():
                raise AutoQuantValidationError(
                    [_issue(root, "study.source-directory", "Editable closure root is not a directory")]
                )
            for path in root.rglob("*"):
                if path.is_symlink():
                    raise AutoQuantValidationError(
                        [_issue(path, "path.symlink", "Editable source cannot contain symlinks")]
                    )
                if path.is_file():
                    files.add(path.relative_to(project.root_dir).as_posix())
        elif root.exists():
            if not root.is_file():
                raise AutoQuantValidationError(
                    [_issue(root, "study.source-file", "Editable exact path is not a file")]
                )
            files.add(relative)
    for relative in sorted(files, reverse=True):
        confined_path(project.root_dir, relative, f"editable/{relative}").unlink()


def _copy_run_sources(
    run: RunContext,
    target_project: ProjectContext,
    study: StudyContext,
) -> None:
    hashes = _run_source_hashes(run)
    for relative, expected_hash in hashes.items():
        if not any(
            path_matches_pattern(relative, pattern)
            for pattern in study.definition.editable["paths"]
        ):
            raise AutoQuantValidationError(
                [_issue(relative, "session.source-escape", "Run source is outside editable closure")]
            )
        source = run.root_dir / "sources" / relative
        if hash_file(source) != expected_hash:
            raise AutoQuantValidationError(
                [_issue(source, "run.source-stale", "Run source hash changed")]
            )
        target = confined_path(
            target_project.root_dir,
            relative,
            f"editable/{relative}",
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _restore_leader(session: SessionContext, candidate: StudyContext) -> None:
    _clear_editable(session.worktree_project, candidate)
    _copy_run_sources(
        session.leader_run,
        session.worktree_project,
        candidate,
    )
    restored = load_study(session.worktree_project, session.manifest["studyId"])
    if restored.source_hash != session.manifest["leader"]["sourceHash"]:
        raise AutoQuantValidationError(
            [_issue(session.root_dir, "session.restore", "Leader source restoration failed")]
        )


def _experiment_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AutoQuantValidationError(
                [_issue(path, "path.symlink", "Experiment cannot contain symlinks")]
            )
        if path.is_file() and path != root / EXPERIMENT_MANIFEST:
            hashes[path.relative_to(root).as_posix()] = hash_file(path)
    return hashes


def _publish_experiment(
    project: ProjectContext,
    session: SessionContext,
    result: dict[str, Any],
    changes: list[dict[str, Any]],
    patch: str,
) -> ExperimentContext:
    experiments_root = session.root_dir / "experiments"
    experiment_id = result["id"]
    target = experiments_root / experiment_id
    temporary = experiments_root / f".{experiment_id}.creating"
    if target.exists() or temporary.exists():
        raise AutoQuantValidationError(
            [_issue(target, "experiment.collision", "Experiment already exists")]
        )
    try:
        temporary.mkdir()
        _write_json(temporary / EXPERIMENT_RESULT, result)
        _write_json(temporary / EXPERIMENT_CHANGES, changes)
        (temporary / EXPERIMENT_DIFF).write_text(patch, encoding="utf-8")
        files = _experiment_hashes(temporary)
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "id": experiment_id,
            "sessionId": session.manifest["id"],
            "completed": True,
            "verdict": result["verdict"],
            "runId": result["candidate"]["runId"],
            "resultHash": files[EXPERIMENT_RESULT],
            "files": files,
        }
        _write_json(temporary / EXPERIMENT_MANIFEST, manifest)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return load_experiment(project, session, experiment_id)


def evaluate_experiment(
    project: ProjectContext,
    session_id: str,
    hypothesis: str,
) -> ExperimentContext:
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        raise AutoQuantValidationError(
            [_issue("hypothesis", "schema.string", "Hypothesis must be non-empty")]
        )
    session = load_session(project, session_id)
    if session.manifest["status"] != "active":
        raise AutoQuantValidationError(
            [_issue(session.manifest_path, "session.closed", "Session is not active")]
        )
    candidate = validate_session_authority(project, session)
    if candidate.source_hash == session.manifest["leader"]["sourceHash"]:
        raise AutoQuantValidationError(
            [_issue(candidate.root_dir, "experiment.unchanged", "Candidate source is unchanged")]
        )
    changes, patch = _source_changes(
        session.leader_run,
        candidate,
        session.worktree_project,
    )
    if not changes:
        raise AutoQuantValidationError(
            [_issue(candidate.root_dir, "experiment.unchanged", "Candidate has no source changes")]
        )
    started_at = datetime.now(timezone.utc).isoformat()
    data_root = confined_path(
        project.root_dir,
        project.manifest.directories["data"],
        "project/directories/data",
    )
    run = execute_study(
        project,
        session.manifest["studyId"],
        execution_project=session.worktree_project,
        data_root=data_root,
    )
    leader_value = float(session.manifest["leader"]["value"])
    candidate_value: float | None = None
    improvement: float | None = None
    if run.result["status"] == "failed":
        verdict = "CRASH"
    else:
        candidate_value = _metric_value(run)
        direction = run.result["objective"]["direction"]
        improvement = (
            candidate_value - leader_value
            if direction == "maximize"
            else leader_value - candidate_value
        )
        minimum = float(run.result["objective"]["minimumImprovement"])
        verdict = (
            "KEEP"
            if improvement > 0 and improvement >= minimum
            else "REVERT"
        )
    sequence = int(session.manifest["nextExperiment"])
    experiment_id = f"exp-{sequence:04d}-{candidate.source_hash[:12]}"
    completed_at = datetime.now(timezone.utc).isoformat()
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "id": experiment_id,
        "sessionId": session.manifest["id"],
        "sequence": sequence,
        "hypothesis": hypothesis.strip(),
        "verdict": verdict,
        "startedAt": started_at,
        "completedAt": completed_at,
        "studyId": session.manifest["studyId"],
        "objective": run.result["objective"],
        "leader": {
            **session.manifest["leader"],
            "runId": session.manifest["leader"]["runId"],
        },
        "candidate": {
            "runId": run.result["id"],
            "sourceHash": run.result["subject"]["sourceHash"],
            "metric": run.result["objective"]["metric"],
            "value": candidate_value,
        },
        "improvement": improvement,
        "changesHash": hash_json(changes),
        "errors": run.result["errors"],
    }
    experiment = _publish_experiment(project, session, result, changes, patch)
    if verdict in {"REVERT", "CRASH"}:
        _restore_leader(session, candidate)
        leader_pointer = session.manifest["leader"]
    else:
        leader_pointer = _run_pointer(run)
    updated = {
        **session.manifest,
        "updatedAt": completed_at,
        "leader": leader_pointer,
        "nextExperiment": sequence + 1,
    }
    _atomic_write_json(session.manifest_path, updated)
    return load_experiment(project, load_session(project, session_id), experiment_id)


def _validate_experiment_result(
    value: dict[str, Any],
    path: Path,
    experiment_id: str,
    session_id: str,
) -> None:
    required = {
        "schemaVersion",
        "id",
        "sessionId",
        "sequence",
        "hypothesis",
        "verdict",
        "startedAt",
        "completedAt",
        "studyId",
        "objective",
        "leader",
        "candidate",
        "improvement",
        "changesHash",
        "errors",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(path, "schema.version", "Expected Experiment V1"))
    if value.get("id") != experiment_id or value.get("sessionId") != session_id:
        issues.append(_issue(path, "experiment.identity", "Experiment identity mismatch"))
    if value.get("verdict") not in VERDICTS:
        issues.append(_issue(path, "experiment.verdict", "Invalid Experiment verdict"))
    if (
        not isinstance(value.get("sequence"), int)
        or isinstance(value.get("sequence"), bool)
        or value.get("sequence", 0) < 1
    ):
        issues.append(_issue(path, "schema.number", "Invalid Experiment sequence"))
    for key in ("hypothesis", "startedAt", "completedAt", "studyId"):
        if not isinstance(value.get(key), str) or not value[key]:
            issues.append(_issue(f"{path}/{key}", "schema.string", f"Invalid {key}"))
    if not isinstance(value.get("changesHash"), str) or not SHA256.fullmatch(
        value.get("changesHash", "")
    ):
        issues.append(_issue(f"{path}/changesHash", "schema.hash", "Invalid changesHash"))
    improvement = value.get("improvement")
    if improvement is not None and (
        not isinstance(improvement, (int, float))
        or isinstance(improvement, bool)
        or not math.isfinite(float(improvement))
    ):
        issues.append(_issue(f"{path}/improvement", "schema.number", "Invalid improvement"))
    objective = value.get("objective")
    if not isinstance(objective, dict):
        issues.append(_issue(f"{path}/objective", "schema.type", "Invalid objective"))
    else:
        issues.extend(
            _strict_keys(
                objective,
                {"metric", "direction", "minimumImprovement"},
                f"{path}/objective",
            )
        )
    for key, required_keys in (
        ("leader", {"runId", "sourceHash", "metric", "value"}),
        ("candidate", {"runId", "sourceHash", "metric", "value"}),
    ):
        pointer = value.get(key)
        if not isinstance(pointer, dict):
            issues.append(_issue(f"{path}/{key}", "schema.type", f"Invalid {key}"))
            continue
        issues.extend(_strict_keys(pointer, required_keys, f"{path}/{key}"))
        if not isinstance(pointer.get("runId"), str) or not pointer["runId"].startswith("run-"):
            issues.append(_issue(f"{path}/{key}/runId", "schema.string", "Invalid Run id"))
        if not isinstance(pointer.get("sourceHash"), str) or not SHA256.fullmatch(
            pointer.get("sourceHash", "")
        ):
            issues.append(_issue(f"{path}/{key}/sourceHash", "schema.hash", "Invalid sourceHash"))
    errors = value.get("errors")
    if not isinstance(errors, list):
        issues.append(_issue(f"{path}/errors", "schema.array", "Errors must be an array"))
    if value.get("verdict") == "CRASH":
        candidate = value.get("candidate")
        if isinstance(candidate, dict) and candidate.get("value") is not None:
            issues.append(_issue(f"{path}/candidate/value", "experiment.crash-value", "CRASH cannot have a candidate value"))
        if improvement is not None:
            issues.append(_issue(f"{path}/improvement", "experiment.crash-improvement", "CRASH cannot have an improvement"))
    elif value.get("verdict") in {"KEEP", "REVERT"}:
        candidate = value.get("candidate")
        candidate_value = candidate.get("value") if isinstance(candidate, dict) else None
        if (
            not isinstance(candidate_value, (int, float))
            or isinstance(candidate_value, bool)
            or not math.isfinite(float(candidate_value))
        ):
            issues.append(_issue(f"{path}/candidate/value", "schema.number", "Verdict requires a candidate value"))
    if issues:
        raise AutoQuantValidationError(issues)


def load_experiment(
    project: ProjectContext,
    session: SessionContext,
    experiment_id: str,
) -> ExperimentContext:
    root = _experiment_root(session, experiment_id)
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "experiment.missing", f"Unknown Experiment: {experiment_id}")]
        )
    manifest = _read_json(root / EXPERIMENT_MANIFEST, "experiment-manifest")
    required = {
        "schemaVersion",
        "id",
        "sessionId",
        "completed",
        "verdict",
        "runId",
        "resultHash",
        "files",
    }
    issues = _strict_keys(manifest, required, root / EXPERIMENT_MANIFEST)
    if (
        manifest.get("schemaVersion") != SCHEMA_VERSION
        or manifest.get("id") != experiment_id
        or manifest.get("sessionId") != session.manifest["id"]
        or manifest.get("completed") is not True
        or manifest.get("verdict") not in VERDICTS
    ):
        issues.append(
            _issue(root / EXPERIMENT_MANIFEST, "experiment.manifest", "Invalid terminal manifest")
        )
    files = manifest.get("files")
    actual = _experiment_hashes(root)
    if not isinstance(files, dict) or files != actual:
        issues.append(_issue(root, "experiment.tampered", "Experiment files changed"))
    if isinstance(files, dict) and files.get(EXPERIMENT_RESULT) != manifest.get("resultHash"):
        issues.append(_issue(root, "experiment.result-hash", "Experiment result hash mismatch"))
    if issues:
        raise AutoQuantValidationError(issues)
    result = _read_json(root / EXPERIMENT_RESULT, "experiment-result")
    _validate_experiment_result(
        result,
        root / EXPERIMENT_RESULT,
        experiment_id,
        session.manifest["id"],
    )
    changes_value = json.loads((root / EXPERIMENT_CHANGES).read_text(encoding="utf-8"))
    if not isinstance(changes_value, list) or hash_json(changes_value) != result["changesHash"]:
        raise AutoQuantValidationError(
            [_issue(root / EXPERIMENT_CHANGES, "experiment.changes", "Invalid source changes")]
        )
    run = load_run(project, manifest["runId"])
    if (
        run.result["id"] != result["candidate"]["runId"]
        or run.result["subject"]["sourceHash"] != result["candidate"]["sourceHash"]
    ):
        raise AutoQuantValidationError(
            [_issue(root, "experiment.run", "Candidate Run differs from Experiment")]
        )
    return ExperimentContext(root, manifest, result, changes_value)


def list_experiments(
    project: ProjectContext,
    session: SessionContext,
) -> list[ExperimentSummary]:
    root = session.root_dir / "experiments"
    summaries: list[ExperimentSummary] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir():
            raise AutoQuantValidationError(
                [_issue(entry, "experiment.entry", "Experiment entries must be directories")]
            )
        experiment = load_experiment(project, session, entry.name)
        result = experiment.result
        summaries.append(
            ExperimentSummary(
                id=result["id"],
                sequence=result["sequence"],
                verdict=result["verdict"],
                hypothesis=result["hypothesis"],
                leader_value=float(result["leader"]["value"]),
                candidate_value=(
                    float(result["candidate"]["value"])
                    if result["candidate"]["value"] is not None
                    else None
                ),
                improvement=(
                    float(result["improvement"])
                    if result["improvement"] is not None
                    else None
                ),
                run_id=result["candidate"]["runId"],
                completed_at=result["completedAt"],
                path=str(experiment.root_dir),
            )
        )
    return summaries


def promote_session(project: ProjectContext, session_id: str) -> dict[str, Any]:
    session = load_session(project, session_id)
    if session.manifest["status"] != "active":
        raise AutoQuantValidationError(
            [_issue(session.manifest_path, "session.closed", "Session is not active")]
        )
    if session.manifest["leader"]["runId"] == session.manifest["baseline"]["runId"]:
        raise AutoQuantValidationError(
            [_issue(session.manifest_path, "promotion.no-keep", "Session has no KEEP to promote")]
        )
    validate_session_authority(project, session)
    canonical = load_study(project, session.manifest["studyId"])
    if canonical.source_hash != session.manifest["baseProjectSourceHash"]:
        raise AutoQuantValidationError(
            [
                _issue(
                    canonical.root_dir,
                    "promotion.stale-base",
                    "Project candidate source changed since Session start",
                )
            ]
        )
    receipt_path = session.root_dir / PROMOTION_RECEIPT
    if receipt_path.exists() or receipt_path.is_symlink():
        raise AutoQuantValidationError(
            [_issue(receipt_path, "promotion.exists", "Promotion receipt already exists")]
        )
    leader_hashes = _run_source_hashes(session.leader_run)
    before_hashes = canonical.editable_hashes
    promoted_at = datetime.now(timezone.utc).isoformat()
    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "id": f"promotion-{session_id}",
        "sessionId": session_id,
        "projectId": project.manifest.id,
        "studyId": session.manifest["studyId"],
        "leaderRunId": session.manifest["leader"]["runId"],
        "beforeSourceHash": session.manifest["baseProjectSourceHash"],
        "afterSourceHash": session.manifest["leader"]["sourceHash"],
        "sourceHashes": leader_hashes,
        "promotedAt": promoted_at,
    }
    with tempfile.TemporaryDirectory(prefix=f"aq-promote-{session_id}-") as directory:
        backup = Path(directory) / "backup"
        copy_hashed_files(project, before_hashes, backup)
        try:
            _clear_editable(project, canonical)
            _copy_run_sources(session.leader_run, project, canonical)
            promoted = load_study(project, session.manifest["studyId"])
            if promoted.source_hash != session.manifest["leader"]["sourceHash"]:
                raise AutoQuantValidationError(
                    [_issue(project.root_dir, "promotion.hash", "Promoted source hash mismatch")]
                )
            _write_json(receipt_path, receipt)
            _atomic_write_json(
                session.manifest_path,
                {
                    **session.manifest,
                    "status": "promoted",
                    "updatedAt": promoted_at,
                },
            )
        except Exception:
            _clear_editable(project, canonical)
            for relative, expected_hash in before_hashes.items():
                source = backup / relative
                if hash_file(source) != expected_hash:
                    raise RuntimeError("Promotion backup hash mismatch")
                target = confined_path(project.root_dir, relative, f"rollback/{relative}")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            if receipt_path.is_file():
                receipt_path.unlink()
            _atomic_write_json(session.manifest_path, session.manifest)
            raise
    return receipt


SESSION_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant Research Session",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "id",
        "status",
        "projectId",
        "studyId",
        "createdAt",
        "updatedAt",
        "worktree",
        "editablePaths",
        "baseProjectSourceHash",
        "baseline",
        "leader",
        "locks",
        "nextExperiment",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "pattern": SESSION_ID.pattern},
        "status": {"enum": sorted(SESSION_STATUSES)},
        "projectId": {"type": "string", "minLength": 1},
        "studyId": {"type": "string", "minLength": 1},
        "createdAt": {"type": "string", "format": "date-time"},
        "updatedAt": {"type": "string", "format": "date-time"},
        "worktree": {"type": "string", "minLength": 1},
        "editablePaths": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "baseProjectSourceHash": {
            "type": "string",
            "pattern": SHA256.pattern,
        },
        "baseline": {"$ref": "#/$defs/runPointer"},
        "leader": {"$ref": "#/$defs/runPointer"},
        "locks": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "studyHash",
                "programHash",
                "judgeHash",
                "datasetHash",
                "harness",
                "fixedHashes",
            ],
            "properties": {
                "studyHash": {"type": "string", "pattern": SHA256.pattern},
                "programHash": {"type": "string", "pattern": SHA256.pattern},
                "judgeHash": {"type": "string", "pattern": SHA256.pattern},
                "datasetHash": {"type": "string", "pattern": SHA256.pattern},
                "harness": {"type": "object"},
                "fixedHashes": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string",
                        "pattern": SHA256.pattern,
                    },
                },
            },
        },
        "nextExperiment": {"type": "integer", "minimum": 1},
    },
    "$defs": {
        "runPointer": {
            "type": "object",
            "additionalProperties": False,
            "required": ["runId", "sourceHash", "metric", "value"],
            "properties": {
                "runId": {"type": "string", "pattern": "^run-"},
                "sourceHash": {"type": "string", "pattern": SHA256.pattern},
                "metric": {"type": "string", "minLength": 1},
                "value": {"type": "number"},
            },
        }
    },
}


EXPERIMENT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant immutable Experiment result",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "id",
        "sessionId",
        "sequence",
        "hypothesis",
        "verdict",
        "startedAt",
        "completedAt",
        "studyId",
        "objective",
        "leader",
        "candidate",
        "improvement",
        "changesHash",
        "errors",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "pattern": EXPERIMENT_ID.pattern},
        "sessionId": {"type": "string", "pattern": SESSION_ID.pattern},
        "sequence": {"type": "integer", "minimum": 1},
        "hypothesis": {"type": "string", "minLength": 1},
        "verdict": {"enum": sorted(VERDICTS)},
        "startedAt": {"type": "string", "format": "date-time"},
        "completedAt": {"type": "string", "format": "date-time"},
        "studyId": {"type": "string", "minLength": 1},
        "objective": {"type": "object"},
        "leader": {"type": "object"},
        "candidate": {"type": "object"},
        "improvement": {"type": ["number", "null"]},
        "changesHash": {"type": "string", "pattern": SHA256.pattern},
        "errors": {"type": "array"},
    },
}
