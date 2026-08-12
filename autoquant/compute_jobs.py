"""Provider-neutral ComputeJob receipts over immutable Study execution."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .runs import execute_study, load_run
from .studies import STUDY_ID, hash_file, load_study
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


COMPUTE_JOB_SCHEMA_VERSION = 1
COMPUTE_JOBS_DIRECTORY = "compute-jobs"
COMPUTE_JOB_RECEIPT = "receipt.json"
COMPUTE_JOB_MANIFEST = "manifest.json"
COMPUTE_JOB_ID = re.compile(
    r"^job-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$"
)
TERMINAL_STATES = {"succeeded", "failed", "cancelled"}


@dataclass(frozen=True)
class ComputeResourcePolicy:
    cpu_cores: int = 1
    memory_mb: int | None = None
    gpu_count: int = 0
    wall_time_seconds: int | None = None

    def to_dict(self) -> dict[str, int | None]:
        return {
            "cpuCores": self.cpu_cores,
            "memoryMb": self.memory_mb,
            "gpuCount": self.gpu_count,
            "wallTimeSeconds": self.wall_time_seconds,
        }


@dataclass(frozen=True)
class ComputeJobContext:
    root_dir: Path
    manifest: dict[str, Any]
    receipt: dict[str, Any]


_EXECUTORS = {
    "cpu": {
        "kind": "cpu",
        "provider": "builtin",
        "available": True,
        "reason": None,
    },
    "gpu": {
        "kind": "gpu",
        "provider": "private-plugin",
        "available": False,
        "reason": "No GPU provider plugin is installed",
    },
    "moss": {
        "kind": "moss",
        "provider": "private-plugin",
        "available": False,
        "reason": "No MOSS provider plugin is installed",
    },
}


def compute_executor_declarations() -> list[dict[str, Any]]:
    """Return public capability declarations without credentials or plugin config."""

    return [dict(_EXECUTORS[kind]) for kind in ("cpu", "gpu", "moss")]


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as error:
        raise AutoQuantValidationError(
            [_issue(path, "compute-job.read", f"Cannot read ComputeJob JSON: {error}")]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "compute-job.schema", "ComputeJob JSON must be an object")]
        )
    return value


def _jobs_root(project: ProjectContext, *, create: bool = False) -> Path:
    root = confined_path(
        project.root_dir,
        COMPUTE_JOBS_DIRECTORY,
        "project/compute-jobs",
    )
    if root.is_symlink():
        raise AutoQuantValidationError(
            [_issue(root, "compute-job.symlink", "ComputeJob root cannot be a symlink")]
        )
    if create:
        root.mkdir(exist_ok=True)
    return root


def _validate_policy(policy: ComputeResourcePolicy) -> None:
    issues: list[ValidationIssue] = []
    for name, value, minimum in (
        ("cpuCores", policy.cpu_cores, 1),
        ("gpuCount", policy.gpu_count, 0),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            issues.append(
                _issue(name, "compute-job.resource-policy", f"{name} must be >= {minimum}")
            )
    for name, value in (
        ("memoryMb", policy.memory_mb),
        ("wallTimeSeconds", policy.wall_time_seconds),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 1
        ):
            issues.append(
                _issue(name, "compute-job.resource-policy", f"{name} must be null or >= 1")
            )
    if issues:
        raise AutoQuantValidationError(issues)


def _new_job_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"job-{stamp}-{uuid.uuid4().hex[:12]}"


def _retry_identity(
    project: ProjectContext,
    study_id: str,
    input_hash: str,
    retry_of: str | None,
) -> dict[str, Any]:
    if retry_of is None:
        return {"rootJobId": None, "parentJobId": None, "attempt": 1}
    parent = load_compute_job(project, retry_of).receipt
    if parent["study"]["id"] != study_id or parent["inputHash"] != input_hash:
        raise AutoQuantValidationError(
            [
                _issue(
                    retry_of,
                    "compute-job.retry-input",
                    "Retry must preserve the exact Study and input identity",
                )
            ]
        )
    return {
        "rootJobId": parent["retry"]["rootJobId"] or parent["id"],
        "parentJobId": parent["id"],
        "attempt": parent["retry"]["attempt"] + 1,
    }


def _terminal_receipt(
    *,
    job_id: str,
    project: ProjectContext,
    study: Any,
    executor: dict[str, Any],
    policy: ComputeResourcePolicy,
    created_at: str,
    started_at: str,
    completed_at: str,
    status: str,
    retry: dict[str, Any],
    run: Any | None,
    error: dict[str, str] | None,
) -> dict[str, Any]:
    run_ref = None
    output_refs: list[dict[str, Any]] = []
    if run is not None:
        run_ref = {
            "id": run.result["id"],
            "path": f"{project.manifest.directories['runs']}/{run.result['id']}",
            "resultHash": run.manifest["resultHash"],
        }
        output_refs = [
            {
                "kind": item["kind"],
                "path": f"{run_ref['path']}/{item['path']}",
                "immutable": True,
            }
            for item in run.result["artifacts"]
        ]
    return {
        "schemaVersion": COMPUTE_JOB_SCHEMA_VERSION,
        "id": job_id,
        "status": status,
        "createdAt": created_at,
        "startedAt": started_at,
        "completedAt": completed_at,
        "project": {"id": project.manifest.id},
        "study": {"id": study.definition.id, "hash": study.study_hash},
        "inputHash": study.input_hash,
        "executor": {
            "kind": executor["kind"],
            "provider": executor["provider"],
        },
        "resourcePolicy": policy.to_dict(),
        "stateHistory": [
            {"state": "queued", "at": created_at},
            {"state": "running", "at": started_at},
            {"state": status, "at": completed_at},
        ],
        "runRef": run_ref,
        "outputRefs": output_refs,
        "error": error,
        "retry": retry,
        "tradingAuthority": "none",
    }


def execute_compute_job(
    project: ProjectContext,
    study_id: str,
    *,
    executor_kind: str = "cpu",
    resource_policy: ComputeResourcePolicy | None = None,
    retry_of: str | None = None,
) -> ComputeJobContext:
    """Synchronously execute one verified Study and publish a terminal receipt."""

    if not STUDY_ID.fullmatch(study_id):
        raise AutoQuantValidationError(
            [_issue(study_id, "compute-job.study-id", "Invalid Study id")]
        )
    executor = _EXECUTORS.get(executor_kind)
    if executor is None:
        raise AutoQuantValidationError(
            [_issue(executor_kind, "compute-job.executor", "Unknown compute executor")]
        )
    if not executor["available"]:
        raise AutoQuantValidationError(
            [
                _issue(
                    executor_kind,
                    "compute-job.executor-unavailable",
                    executor["reason"],
                )
            ]
        )
    policy = resource_policy or ComputeResourcePolicy()
    _validate_policy(policy)
    if executor_kind == "cpu" and policy.gpu_count != 0:
        raise AutoQuantValidationError(
            [
                _issue(
                    "gpuCount",
                    "compute-job.resource-policy",
                    "Built-in CPU execution cannot request GPUs",
                )
            ]
        )

    study = load_study(project, study_id)
    retry = _retry_identity(project, study_id, study.input_hash, retry_of)
    job_id = _new_job_id()
    jobs_root = _jobs_root(project, create=True)
    staging = jobs_root / f".{job_id}-{uuid.uuid4().hex}"
    target = jobs_root / job_id
    staging.mkdir()
    created_at = _now()
    started_at = _now()
    run = None
    error = None
    status = "succeeded"
    try:
        try:
            run = execute_study(project, study_id)
        except Exception as execution_error:
            status = "failed"
            error = {
                "code": "executor.failed",
                "type": execution_error.__class__.__name__,
                "message": "Built-in CPU executor failed before publishing a Run",
            }
        completed_at = _now()
        receipt = _terminal_receipt(
            job_id=job_id,
            project=project,
            study=study,
            executor=executor,
            policy=policy,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            retry=retry,
            run=run,
            error=error,
        )
        _write_json(staging / COMPUTE_JOB_RECEIPT, receipt)
        manifest = {
            "schemaVersion": COMPUTE_JOB_SCHEMA_VERSION,
            "id": job_id,
            "completed": True,
            "receiptHash": hash_file(staging / COMPUTE_JOB_RECEIPT),
        }
        _write_json(staging / COMPUTE_JOB_MANIFEST, manifest)
        if target.exists() or target.is_symlink():
            raise AutoQuantValidationError(
                [_issue(target, "compute-job.collision", "ComputeJob id collision")]
            )
        os.replace(staging, target)
        return load_compute_job(project, job_id)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def _validate_receipt(receipt: dict[str, Any], path: Path, job_id: str) -> None:
    required = {
        "schemaVersion",
        "id",
        "status",
        "createdAt",
        "startedAt",
        "completedAt",
        "project",
        "study",
        "inputHash",
        "executor",
        "resourcePolicy",
        "stateHistory",
        "runRef",
        "outputRefs",
        "error",
        "retry",
        "tradingAuthority",
    }
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing field '{key}'")
        for key in sorted(required - receipt.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(receipt.keys() - required)
    )
    if receipt.get("schemaVersion") != COMPUTE_JOB_SCHEMA_VERSION:
        issues.append(_issue(path, "schema.version", "Invalid ComputeJob schema version"))
    if receipt.get("id") != job_id:
        issues.append(_issue(path, "compute-job.directory-id", "Receipt id differs from directory"))
    status = receipt.get("status")
    if status not in TERMINAL_STATES:
        issues.append(_issue(path, "compute-job.status", "Receipt must be terminal"))
    history = receipt.get("stateHistory")
    expected_states = ["queued", "running", status]
    if not isinstance(history, list) or [
        item.get("state") for item in history if isinstance(item, dict)
    ] != expected_states:
        issues.append(
            _issue(path, "compute-job.history", "Invalid ComputeJob state history")
        )
    if receipt.get("tradingAuthority") != "none":
        issues.append(
            _issue(
                path,
                "compute-job.trading-authority",
                "ComputeJob has no trading authority",
            )
        )
    for key, expected_keys in (
        ("project", {"id"}),
        ("study", {"id", "hash"}),
        ("executor", {"kind", "provider"}),
        (
            "resourcePolicy",
            {"cpuCores", "memoryMb", "gpuCount", "wallTimeSeconds"},
        ),
        ("retry", {"rootJobId", "parentJobId", "attempt"}),
    ):
        value = receipt.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            issues.append(
                _issue(path, "compute-job.schema", f"Invalid {key} contract")
            )
    if isinstance(history, list):
        timestamps = [
            receipt.get("createdAt"),
            receipt.get("startedAt"),
            receipt.get("completedAt"),
        ]
        if len(history) != 3 or any(
            not isinstance(item, dict)
            or set(item) != {"state", "at"}
            or item.get("at") != timestamps[index]
            for index, item in enumerate(history)
        ):
            issues.append(
                _issue(path, "compute-job.history", "State timestamps differ from receipt")
            )
    run_ref = receipt.get("runRef")
    error = receipt.get("error")
    if run_ref is not None and (
        not isinstance(run_ref, dict)
        or set(run_ref) != {"id", "path", "resultHash"}
    ):
        issues.append(_issue(path, "compute-job.run-ref", "Invalid Run reference"))
    outputs = receipt.get("outputRefs")
    if not isinstance(outputs, list) or any(
        not isinstance(item, dict)
        or set(item) != {"kind", "path", "immutable"}
        or item.get("immutable") is not True
        for item in outputs
    ):
        issues.append(_issue(path, "compute-job.outputs", "Invalid output references"))
    if error is not None and (
        not isinstance(error, dict)
        or set(error) != {"code", "type", "message"}
    ):
        issues.append(_issue(path, "compute-job.error", "Invalid executor error"))
    if status == "succeeded" and (not isinstance(run_ref, dict) or error is not None):
        issues.append(
            _issue(
                path,
                "compute-job.success",
                "Succeeded job requires one Run and no error",
            )
        )
    if status in {"failed", "cancelled"} and (run_ref is not None or not isinstance(error, dict)):
        issues.append(
            _issue(
                path,
                "compute-job.failure",
                "Unsuccessful job requires an error and no Run",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)


def load_compute_job(project: ProjectContext, job_id: str) -> ComputeJobContext:
    """Verify one immutable terminal ComputeJob receipt and its Run reference."""

    if not COMPUTE_JOB_ID.fullmatch(job_id):
        raise AutoQuantValidationError(
            [_issue(job_id, "compute-job.id", "Invalid ComputeJob id")]
        )
    root = confined_path(_jobs_root(project), job_id, f"compute-job/{job_id}")
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "compute-job.missing", f"Unknown ComputeJob: {job_id}")]
        )
    manifest = _read_json(root / COMPUTE_JOB_MANIFEST)
    expected_manifest_keys = {"schemaVersion", "id", "completed", "receiptHash"}
    if (
        set(manifest) != expected_manifest_keys
        or manifest.get("schemaVersion") != COMPUTE_JOB_SCHEMA_VERSION
        or manifest.get("id") != job_id
        or manifest.get("completed") is not True
        or manifest.get("receiptHash") != hash_file(root / COMPUTE_JOB_RECEIPT)
    ):
        raise AutoQuantValidationError(
            [_issue(root, "compute-job.tampered", "Invalid immutable ComputeJob manifest")]
        )
    receipt = _read_json(root / COMPUTE_JOB_RECEIPT)
    _validate_receipt(receipt, root / COMPUTE_JOB_RECEIPT, job_id)
    run_ref = receipt["runRef"]
    if run_ref is not None:
        run = load_run(project, run_ref["id"])
        expected = {
            "id": run.result["id"],
            "path": f"{project.manifest.directories['runs']}/{run.result['id']}",
            "resultHash": run.manifest["resultHash"],
        }
        if run_ref != expected:
            raise AutoQuantValidationError(
                [
                    _issue(
                        root,
                        "compute-job.run-ref",
                        "ComputeJob Run reference differs from immutable Run",
                    )
                ]
            )
        if (
            receipt["project"] != {"id": project.manifest.id}
            or receipt["study"]
            != {"id": run.result["study"]["id"], "hash": run.result["study"]["hash"]}
            or receipt["inputHash"] != run.result["studyInputHash"]
        ):
            raise AutoQuantValidationError(
                [
                    _issue(
                        root,
                        "compute-job.input-ref",
                        "ComputeJob input identity differs from immutable Run",
                    )
                ]
            )
        expected_outputs = [
            {
                "kind": item["kind"],
                "path": f"{run_ref['path']}/{item['path']}",
                "immutable": True,
            }
            for item in run.result["artifacts"]
        ]
        if receipt["outputRefs"] != expected_outputs:
            raise AutoQuantValidationError(
                [
                    _issue(
                        root,
                        "compute-job.outputs",
                        "ComputeJob outputs differ from immutable Run",
                    )
                ]
            )
    return ComputeJobContext(root, manifest, receipt)


def list_compute_jobs(project: ProjectContext) -> list[ComputeJobContext]:
    """Verify and list published ComputeJobs in deterministic id order."""

    root = _jobs_root(project)
    if not root.exists():
        return []
    if not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "compute-job.root", "ComputeJob root must be a directory")]
        )
    jobs: list[ComputeJobContext] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir() or not COMPUTE_JOB_ID.fullmatch(entry.name):
            raise AutoQuantValidationError(
                [_issue(entry, "compute-job.entry", "Invalid ComputeJob directory entry")]
            )
        jobs.append(load_compute_job(project, entry.name))
    return jobs
