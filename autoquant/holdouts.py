"""Frozen cross-Project external-period challenge evidence."""

from __future__ import annotations

import json
import math
import os
import shlex
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .dossiers import list_dossiers, load_dossier, load_dossier_status
from .intake import load_project_intake
from .runs import execute_study, list_runs, load_run
from .sessions import list_sessions
from .studies import hash_file, hash_json, load_study
from .templates import OHLCV_STUDY_ID, PORTFOLIO_STUDY_ID, RL_STUDY_ID
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


HOLDOUT_DIRECTORY = "holdout"
HOLDOUT_BINDING = "binding.json"
HOLDOUT_BINDING_MANIFEST = "manifest.json"
HOLDOUT_SOURCE_DOSSIER = "source-dossier.json"
HOLDOUT_IMPORTED_SOURCES = "imported-sources"
HOLDOUT_RESULT_DIRECTORY = "result"
HOLDOUT_RESULT = "result.json"
HOLDOUT_RESULT_MANIFEST = "manifest.json"
HOLDOUT_BINDING_KIND = "autoquant-frozen-holdout-binding"
HOLDOUT_BINDING_MANIFEST_KIND = "autoquant-frozen-holdout-binding-manifest"
HOLDOUT_RESULT_KIND = "autoquant-frozen-holdout-result"
HOLDOUT_RESULT_MANIFEST_KIND = "autoquant-frozen-holdout-result-manifest"
HOLDOUT_STATUS_KIND = "autoquant-frozen-holdout-status"
HOLDOUT_METHOD = "strictly-later-frozen-dossier-leaders-v1"

LANE_STUDIES = {
    "factor": OHLCV_STUDY_ID,
    "portfolio": PORTFOLIO_STUDY_ID,
    "rl": RL_STUDY_ID,
}
LANE_ORDER = tuple(LANE_STUDIES)


@dataclass(frozen=True)
class HoldoutBindingContext:
    root_dir: Path
    manifest: dict[str, Any]
    binding: dict[str, Any]


@dataclass(frozen=True)
class HoldoutResultContext:
    root_dir: Path
    manifest: dict[str, Any]
    result: dict[str, Any]


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.missing", f"Missing {label}: {path}")]
        ) from None
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.json", f"Invalid {label}: {error}")]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.type", f"{label} must be an object")]
        )
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _action(
    action_id: str,
    description: str,
    argv: list[str],
    effect: str,
) -> dict[str, Any]:
    return {
        "id": action_id,
        "description": description,
        "argv": argv,
        "display": shlex.join(argv),
        "effect": effect,
    }


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


def _holdout_root(project: ProjectContext) -> Path:
    return confined_path(
        project.root_dir,
        HOLDOUT_DIRECTORY,
        "project/holdout",
    )


def _binding_root(project: ProjectContext, *, create: bool = False) -> Path:
    root = project.root_dir / HOLDOUT_DIRECTORY
    if create:
        if root.exists() or root.is_symlink():
            raise AutoQuantValidationError(
                [_issue(root, "holdout.exists", "Project already has holdout state")]
            )
        return root
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "holdout.missing", "Project has no frozen holdout binding")]
        )
    return _holdout_root(project)


def has_holdout_binding(project: ProjectContext) -> bool:
    root = project.root_dir / HOLDOUT_DIRECTORY
    return root.is_dir() and not root.is_symlink()


def assert_iterative_research_allowed(project: ProjectContext) -> None:
    """Reject candidate-selection lifecycle operations in bound Projects."""

    if has_holdout_binding(project):
        raise AutoQuantValidationError(
            [
                _issue(
                    project.root_dir / HOLDOUT_DIRECTORY,
                    "holdout.frozen-project",
                    "This Project is a frozen external-period challenge; "
                    "candidate Sessions and research Campaigns are not allowed",
                )
            ]
        )


def assert_run_authorized(
    project: ProjectContext,
    *,
    holdout_authorized: bool,
) -> None:
    """Keep generic Run execution outside a bound one-shot challenge."""

    bound = has_holdout_binding(project)
    if bound and not holdout_authorized:
        raise AutoQuantValidationError(
            [
                _issue(
                    project.root_dir / HOLDOUT_DIRECTORY,
                    "holdout.run-required",
                    "This frozen Project may run only through 'aq holdout run'",
                )
            ]
        )
    if holdout_authorized and not bound:
        raise AutoQuantValidationError(
            [
                _issue(
                    project.root_dir,
                    "holdout.binding-required",
                    "Holdout-authorized execution requires a verified binding",
                )
            ]
        )


def _binding_files(root: Path) -> dict[str, str]:
    paths = [
        root / HOLDOUT_BINDING,
        root / HOLDOUT_SOURCE_DOSSIER,
        *sorted((root / HOLDOUT_IMPORTED_SOURCES).rglob("*")),
    ]
    result: dict[str, str] = {}
    for path in paths:
        if path.is_symlink():
            raise AutoQuantValidationError(
                [_issue(path, "holdout.symlink", "Holdout evidence cannot be a symlink")]
            )
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hash_file(path)
    return result


def _result_files(root: Path) -> dict[str, str]:
    path = root / HOLDOUT_RESULT
    if path.is_symlink() or not path.is_file():
        raise AutoQuantValidationError(
            [_issue(path, "holdout.result-missing", "Missing holdout result")]
        )
    return {HOLDOUT_RESULT: hash_file(path)}


def _source_hashes(run) -> dict[str, str]:
    sources_root = run.root_dir / "sources"
    expected = run.result["subject"]["sourcePaths"]
    hashes: dict[str, str] = {}
    issues: list[ValidationIssue] = []
    for relative in expected:
        path = confined_path(sources_root, relative, f"run/source/{relative}")
        if path.is_symlink() or not path.is_file():
            issues.append(
                _issue(path, "holdout.source-missing", "Frozen Run source is missing")
            )
            continue
        hashes[relative] = hash_file(path)
    if hash_json(hashes) != run.result["subject"]["sourceHash"]:
        issues.append(
            _issue(
                sources_root,
                "holdout.source-hash",
                "Frozen Run source bytes differ from the Run subject identity",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return hashes


def _objective_value(result: dict[str, Any]) -> float | None:
    if result["status"] != "succeeded":
        return None
    metric = result["objective"]["metric"]
    value = result["metrics"].get(metric)
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        return None
    return float(value)


def _dataset_projection(
    dataset: dict[str, Any],
    *,
    dataset_hash: str,
) -> dict[str, Any]:
    return {
        "id": dataset["id"],
        "version": dataset["version"],
        "assetClass": dataset["assetClass"],
        "universe": dataset["universe"],
        "timeRange": dataset["timeRange"],
        "market": dataset["market"],
        "priceAdjustment": dataset["priceAdjustment"],
        **(
            {"frequency": dataset["frequency"]}
            if "frequency" in dataset
            else {}
        ),
        **(
            {"intervalSurface": dataset["intervalSurface"]}
            if "intervalSurface" in dataset
            else {}
        ),
        "hash": dataset_hash,
    }


def _dataset_contract(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        key: dataset[key]
        for key in (
            "assetClass",
            "universe",
            "market",
            "priceAdjustment",
            "frequency",
            "intervalSurface",
        )
        if key in dataset
    }


def _binding_identity(binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "method": binding["method"],
        "sourceDossierHash": binding["source"]["dossier"]["dossierHash"],
        "sourceDatasetHash": binding["source"]["dataset"]["hash"],
        "targetProjectId": binding["target"]["project"]["id"],
        "targetDatasetHash": binding["target"]["dataset"]["hash"],
        "lanes": [
            {
                "id": lane["id"],
                "runId": lane["runId"],
                "sourceHash": lane["sourceHash"],
            }
            for lane in binding["source"]["lanes"]
        ],
        "importedSources": binding["importedSources"],
        "createdAt": binding["createdAt"],
    }


def _expected_binding_id(binding: dict[str, Any]) -> str:
    return f"holdout-{hash_json(_binding_identity(binding))[:16]}"


def _portable_source_evidence_issues(
    binding: dict[str, Any],
    source_dossier: dict[str, Any],
    source_dossier_hash: str | None,
    path: Path,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    source = binding.get("source", {})
    dossier_identity = source.get("dossier", {})
    evidence = source_dossier.get("evidence")
    if (
        source_dossier.get("id") != dossier_identity.get("id")
        or source_dossier.get("evidenceHash")
        != dossier_identity.get("evidenceHash")
        or source_dossier_hash != dossier_identity.get("dossierHash")
        or not isinstance(evidence, dict)
        or hash_json(evidence) != source_dossier.get("evidenceHash")
    ):
        issues.append(
            _issue(
                path,
                "holdout.source-dossier",
                "Portable source Dossier identity or evidence hash mismatch",
            )
        )
        return issues
    try:
        expected_dataset = _dataset_projection(
            evidence["dataset"],
            dataset_hash=evidence["datasetHash"],
        )
    except (KeyError, TypeError):
        issues.append(
            _issue(
                path,
                "holdout.source-dataset",
                "Portable source Dossier dataset evidence is incomplete",
            )
        )
        return issues
    if (
        source.get("requestHash") != evidence.get("requestHash")
        or source.get("dataset") != expected_dataset
    ):
        issues.append(
            _issue(
                path,
                "holdout.source-authority",
                "Binding source request or dataset differs from its frozen Dossier",
            )
        )
    dossier_lanes = {
        lane.get("id"): lane
        for lane in evidence.get("lanes", [])
        if isinstance(lane, dict)
    }
    for lane in source.get("lanes", []):
        frozen = dossier_lanes.get(lane.get("id"))
        leader = frozen.get("leaderRun") if isinstance(frozen, dict) else None
        if (
            not isinstance(leader, dict)
            or lane.get("runId") != leader.get("id")
            or lane.get("resultHash") != leader.get("resultHash")
            or lane.get("studyInputHash") != leader.get("studyInputHash")
            or lane.get("objective") != leader.get("objective")
            or lane.get("sourceHash")
            != leader.get("subject", {}).get("sourceHash")
            or hash_json(lane.get("sourceHashes", {}))
            != lane.get("sourceHash")
        ):
            issues.append(
                _issue(
                    path,
                    "holdout.source-lane",
                    f"Binding {lane.get('id')} lane differs from frozen Dossier evidence",
                )
            )
    return issues


def _timestamp(value: str, path: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise AutoQuantValidationError(
            [_issue(path, "holdout.time-range", f"Invalid time range: {error}")]
        ) from error
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC").tz_localize(None)
    return timestamp


def _target_history_issues(project: ProjectContext) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    runs = list_runs(project)
    sessions = list_sessions(project)
    dossiers = list_dossiers(project)
    for values, code, label in (
        (runs, "holdout.target-runs", "Runs"),
        (sessions, "holdout.target-sessions", "Sessions"),
        (dossiers, "holdout.target-dossiers", "Dossiers"),
    ):
        if values:
            issues.append(
                _issue(
                    project.root_dir,
                    code,
                    f"Fresh holdout target must have no existing {label}",
                )
            )
    return issues


def _lane_projection(source_project: ProjectContext, lane: dict[str, Any]) -> dict[str, Any]:
    lane_id = lane["id"]
    expected_study = LANE_STUDIES.get(lane_id)
    if expected_study is None or lane["study"]["id"] != expected_study:
        raise AutoQuantValidationError(
            [
                _issue(
                    lane_id,
                    "holdout.lane",
                    "Holdout V1 supports only coordinated Factor, Portfolio, "
                    "and governed-RL Dossier lanes",
                )
            ]
        )
    run_id = lane["leaderRun"]["id"]
    run = load_run(source_project, run_id)
    hashes = _source_hashes(run)
    return {
        "id": lane_id,
        "studyId": expected_study,
        "runId": run_id,
        "resultHash": run.manifest["resultHash"],
        "inputHash": run.result["inputHash"],
        "studyInputHash": run.result["studyInputHash"],
        "harness": run.result["harness"],
        "objective": run.result["objective"],
        "objectiveValue": _objective_value(run.result),
        "sourceHash": run.result["subject"]["sourceHash"],
        "sourceHashes": hashes,
        **(
            {
                "dependencyHash": run.result["dependencies"]["hash"],
                "dependencySourceHashes": run.result["dependencies"][
                    "sourceHashes"
                ],
            }
            if "dependencies" in run.result
            else {}
        ),
    }


def _validate_lane_source_consistency(
    lanes: list[dict[str, Any]],
) -> None:
    by_id = {lane["id"]: lane for lane in lanes}
    factor = by_id.get("factor")
    if factor is None:
        raise AutoQuantValidationError(
            [_issue("source/lanes", "holdout.factor-required", "Factor lane is required")]
        )
    portfolio = by_id.get("portfolio")
    if portfolio is not None and (
        portfolio["sourceHash"] != factor["sourceHash"]
        or portfolio["sourceHashes"] != factor["sourceHashes"]
    ):
        raise AutoQuantValidationError(
            [
                _issue(
                    "source/lanes/portfolio",
                    "holdout.factor-disagreement",
                    "Factor and Portfolio Dossier leaders do not freeze the same "
                    "factor source",
                )
            ]
        )
    rl = by_id.get("rl")
    if rl is not None:
        dependency_sources = rl.get("dependencySourceHashes", {})
        mismatched = [
            path
            for path, digest in factor["sourceHashes"].items()
            if dependency_sources.get(path) != digest
        ]
        if mismatched:
            raise AutoQuantValidationError(
                [
                    _issue(
                        "source/lanes/rl",
                        "holdout.rl-factor-disagreement",
                        "RL Dossier leader does not bind the frozen Factor source: "
                        + ", ".join(mismatched),
                    )
                ]
            )


def _copy_imported_sources(
    source_project: ProjectContext,
    lanes: list[dict[str, Any]],
    staging: Path,
    target_project: ProjectContext,
) -> list[dict[str, str]]:
    by_id = {lane["id"]: lane for lane in lanes}
    owners = [by_id["factor"]]
    if "rl" in by_id:
        owners.append(by_id["rl"])
    imported: list[dict[str, str]] = []
    for lane in owners:
        source_run = load_run(source_project, lane["runId"])
        for relative, digest in sorted(lane["sourceHashes"].items()):
            expected_root = "models/" if lane["id"] == "rl" else "factors/"
            if not relative.startswith(expected_root):
                raise AutoQuantValidationError(
                    [
                        _issue(
                            relative,
                            "holdout.source-surface",
                            f"{lane['id']} source must stay under {expected_root}",
                        )
                    ]
                )
            source = confined_path(
                source_run.root_dir / "sources",
                relative,
                f"holdout/source/{relative}",
            )
            imported_target = staging / HOLDOUT_IMPORTED_SOURCES / relative
            imported_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, imported_target)
            actual_target = confined_path(
                target_project.root_dir,
                relative,
                f"holdout/target/{relative}",
            )
            actual_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, actual_target)
            if hash_file(actual_target) != digest:
                raise AutoQuantValidationError(
                    [
                        _issue(
                            actual_target,
                            "holdout.import-hash",
                            "Imported target source hash mismatch",
                        )
                    ]
                )
            imported.append(
                {
                    "path": relative,
                    "hash": digest,
                    "role": "rl-encoder" if lane["id"] == "rl" else "factor",
                    "sourceRunId": lane["runId"],
                }
            )
    return imported


def _backup_source_roots(project: ProjectContext, backup: Path) -> None:
    for key in ("factors", "models"):
        source = project.root_dir / project.manifest.directories[key]
        destination = backup / key
        if source.is_symlink():
            raise AutoQuantValidationError(
                [_issue(source, "holdout.symlink", "Source roots cannot be symlinks")]
            )
        shutil.copytree(source, destination)


def _restore_source_roots(project: ProjectContext, backup: Path) -> None:
    for key in ("factors", "models"):
        target = project.root_dir / project.manifest.directories[key]
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(backup / key, target)


def bind_holdout(
    source_project: ProjectContext,
    dossier_id: str,
    target_project: ProjectContext,
) -> HoldoutBindingContext:
    """Freeze one current Dossier's leaders into one fresh later Project."""

    if source_project.root_dir == target_project.root_dir:
        raise AutoQuantValidationError(
            [
                _issue(
                    target_project.root_dir,
                    "holdout.same-project",
                    "Source and target Projects must be different",
                )
            ]
        )
    _binding_root(target_project, create=True)
    issues = _target_history_issues(target_project)
    source_status = load_dossier_status(source_project)
    if (
        source_status is None
        or source_status["latestDossier"] is None
        or source_status["latestDossier"]["id"] != dossier_id
        or not source_status["latestDossier"]["current"]
    ):
        issues.append(
            _issue(
                dossier_id,
                "holdout.source-dossier-current",
                "Source Dossier must be the current verified Project Dossier",
            )
        )
    source_intake = load_project_intake(source_project)
    target_intake = load_project_intake(target_project)
    if source_intake is None or target_intake is None:
        issues.append(
            _issue(
                target_project.root_dir,
                "holdout.intake-required",
                "Both Projects must have verified request-driven intake",
            )
        )
    elif (
        source_intake["manifest"]["template"] != "ohlcv-research-desk"
        or target_intake["manifest"]["template"] != "ohlcv-research-desk"
    ):
        issues.append(
            _issue(
                target_project.root_dir,
                "holdout.template",
                "Holdout V1 requires two ohlcv-research-desk Projects",
            )
        )
    elif source_intake["request"] != target_intake["request"]:
        issues.append(
            _issue(
                target_project.root_dir / "request.json",
                "holdout.request-mismatch",
                "Target request must exactly match the source research request",
            )
        )
    else:
        source_dataset = source_intake["dataset"]
        target_dataset = target_intake["dataset"]
        if _dataset_contract(source_dataset) != _dataset_contract(target_dataset):
            issues.append(
                _issue(
                    target_project.root_dir,
                    "holdout.dataset-contract",
                    "Target asset, universe, calendar, adjustment, and interval "
                    "surface must match the source",
                )
            )
        source_end = _timestamp(
            source_dataset["timeRange"]["end"],
            "source/dataset/timeRange/end",
        )
        target_start = _timestamp(
            target_dataset["timeRange"]["start"],
            "target/dataset/timeRange/start",
        )
        if target_start <= source_end:
            issues.append(
                _issue(
                    "target/dataset/timeRange",
                    "holdout.period-overlap",
                    "Target dataset must start strictly after the source dataset ends",
                )
            )
        if (
            source_dataset["id"] == target_dataset["id"]
            and source_dataset["version"] == target_dataset["version"]
        ) or (
            source_intake["manifest"]["datasetHash"]
            == target_intake["manifest"]["datasetHash"]
        ):
            issues.append(
                _issue(
                    "target/dataset",
                    "holdout.dataset-identity",
                    "Target dataset identity and bytes must differ from the source",
                )
            )
    if issues:
        raise AutoQuantValidationError(issues)
    assert source_intake is not None and target_intake is not None
    dossier = load_dossier(source_project, dossier_id)
    lanes = [
        _lane_projection(source_project, lane)
        for lane in dossier.dossier["evidence"]["lanes"]
    ]
    lanes.sort(key=lambda lane: LANE_ORDER.index(lane["id"]))
    _validate_lane_source_consistency(lanes)

    target_root = target_project.root_dir / HOLDOUT_DIRECTORY
    staging = target_project.root_dir / f".{HOLDOUT_DIRECTORY}.creating"
    if staging.exists() or staging.is_symlink():
        raise AutoQuantValidationError(
            [_issue(staging, "holdout.staging", "Holdout staging path already exists")]
        )
    with tempfile.TemporaryDirectory(prefix="aq-holdout-backup-") as directory:
        backup = Path(directory)
        _backup_source_roots(target_project, backup)
        try:
            staging.mkdir()
            _write_json(
                staging / HOLDOUT_SOURCE_DOSSIER,
                dossier.dossier,
            )
            imported = _copy_imported_sources(
                source_project,
                lanes,
                staging,
                target_project,
            )
            target_studies = []
            for lane in lanes:
                study = load_study(target_project, lane["studyId"])
                expected_hashes = {
                    item["path"]: item["hash"]
                    for item in imported
                    if (
                        item["role"] == "rl-encoder"
                        if lane["id"] == "rl"
                        else item["role"] == "factor"
                    )
                }
                if study.editable_hashes != expected_hashes:
                    raise AutoQuantValidationError(
                        [
                            _issue(
                                study.manifest_path,
                                "holdout.target-source",
                                f"Target {lane['id']} Study source closure differs "
                                "from the frozen import",
                            )
                        ]
                    )
                target_studies.append(
                    {
                        "laneId": lane["id"],
                        "studyId": lane["studyId"],
                        "studyHash": study.study_hash,
                        "inputHash": study.input_hash,
                        "judgeHash": study.judge_hash,
                        "sourceHash": study.source_hash,
                        "datasetHash": study.dataset_hash,
                        "dependencyHash": study.dependency_hash,
                    }
                )
            created_at = datetime.now(timezone.utc).isoformat()
            source_dataset = _dataset_projection(
                source_intake["dataset"],
                dataset_hash=source_intake["manifest"]["datasetHash"],
            )
            target_dataset = _dataset_projection(
                target_intake["dataset"],
                dataset_hash=target_intake["manifest"]["datasetHash"],
            )
            binding = {
                "schemaVersion": SCHEMA_VERSION,
                "kind": HOLDOUT_BINDING_KIND,
                "method": HOLDOUT_METHOD,
                "id": "",
                "createdAt": created_at,
                "source": {
                    "project": {
                        "id": source_project.manifest.id,
                        "name": source_project.manifest.name,
                    },
                    "dossier": {
                        "id": dossier_id,
                        "dossierHash": dossier.manifest["dossierHash"],
                        "evidenceHash": dossier.dossier["evidenceHash"],
                    },
                    "requestHash": source_intake["manifest"]["requestHash"],
                    "dataset": source_dataset,
                    "lanes": lanes,
                },
                "target": {
                    "project": {
                        "id": target_project.manifest.id,
                        "name": target_project.manifest.name,
                    },
                    "requestHash": target_intake["manifest"]["requestHash"],
                    "dataset": target_dataset,
                    "studies": target_studies,
                },
                "importedSources": imported,
                "nonOverlap": {
                    "sourceEnd": source_dataset["timeRange"]["end"],
                    "targetStart": target_dataset["timeRange"]["start"],
                    "strictlyLater": True,
                },
                "policy": {
                    "evaluationRole": "external-temporal-audit",
                    "candidateFrozen": True,
                    "selectionAllowed": False,
                    "sessionAllowed": False,
                    "automaticPromotion": False,
                    "tradingAuthority": "none",
                    "maximumExecutionsPerLane": 1,
                },
            }
            binding["id"] = _expected_binding_id(binding)
            binding_id = binding["id"]
            _write_json(staging / HOLDOUT_BINDING, binding)
            files = _binding_files(staging)
            manifest = {
                "schemaVersion": SCHEMA_VERSION,
                "kind": HOLDOUT_BINDING_MANIFEST_KIND,
                "id": binding_id,
                "completed": True,
                "bindingHash": files[HOLDOUT_BINDING],
                "files": files,
            }
            _write_json(staging / HOLDOUT_BINDING_MANIFEST, manifest)
            os.replace(staging, target_root)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            _restore_source_roots(target_project, backup)
            raise
    return load_holdout_binding(target_project)


def _validate_binding_shape(
    binding: dict[str, Any],
    path: Path,
) -> list[ValidationIssue]:
    required = {
        "schemaVersion",
        "kind",
        "method",
        "id",
        "createdAt",
        "source",
        "target",
        "importedSources",
        "nonOverlap",
        "policy",
    }
    issues = _strict_keys(binding, required, path)
    if (
        binding.get("schemaVersion") != SCHEMA_VERSION
        or binding.get("kind") != HOLDOUT_BINDING_KIND
        or binding.get("method") != HOLDOUT_METHOD
    ):
        issues.append(_issue(path, "holdout.binding-contract", "Invalid binding contract"))
    imported = binding.get("importedSources")
    if not isinstance(imported, list) or not imported:
        issues.append(
            _issue(f"{path}/importedSources", "schema.array", "Imported sources required")
        )
    lanes = (
        binding.get("source", {}).get("lanes")
        if isinstance(binding.get("source"), dict)
        else None
    )
    lane_ids = (
        [lane.get("id") for lane in lanes]
        if isinstance(lanes, list)
        and lanes
        and all(isinstance(lane, dict) for lane in lanes)
        else []
    )
    expected_lane_ids = [
        lane_id for lane_id in LANE_ORDER if lane_id in lane_ids
    ]
    if not lane_ids or lane_ids != expected_lane_ids:
        issues.append(
            _issue(f"{path}/source/lanes", "holdout.lanes", "Invalid lane sequence")
        )
    return issues


def load_holdout_binding(project: ProjectContext) -> HoldoutBindingContext:
    root = _binding_root(project)
    manifest_path = root / HOLDOUT_BINDING_MANIFEST
    binding_path = root / HOLDOUT_BINDING
    manifest = _read_json(manifest_path, "holdout binding manifest")
    binding = _read_json(binding_path, "holdout binding")
    required = {
        "schemaVersion",
        "kind",
        "id",
        "completed",
        "bindingHash",
        "files",
    }
    issues = _strict_keys(manifest, required, manifest_path)
    files = manifest.get("files")
    try:
        actual_files = _binding_files(root)
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
        actual_files = {}
    if (
        manifest.get("schemaVersion") != SCHEMA_VERSION
        or manifest.get("kind") != HOLDOUT_BINDING_MANIFEST_KIND
        or manifest.get("completed") is not True
        or not isinstance(files, dict)
        or files != actual_files
        or manifest.get("bindingHash") != actual_files.get(HOLDOUT_BINDING)
        or manifest.get("id") != binding.get("id")
    ):
        issues.append(
            _issue(manifest_path, "holdout.binding-manifest", "Invalid binding manifest")
        )
    issues.extend(_validate_binding_shape(binding, binding_path))
    try:
        if binding.get("id") != _expected_binding_id(binding):
            issues.append(
                _issue(
                    binding_path,
                    "holdout.binding-id",
                    "Binding id is not derived from its frozen identity",
                )
            )
    except (KeyError, TypeError):
        issues.append(
            _issue(binding_path, "holdout.binding-id", "Binding identity is incomplete")
        )
    source_dossier = {}
    try:
        source_dossier = _read_json(
            root / HOLDOUT_SOURCE_DOSSIER,
            "portable source Dossier",
        )
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
    issues.extend(
        _portable_source_evidence_issues(
            binding,
            source_dossier,
            actual_files.get(HOLDOUT_SOURCE_DOSSIER),
            root / HOLDOUT_SOURCE_DOSSIER,
        )
    )
    if binding.get("target", {}).get("project", {}).get("id") != project.manifest.id:
        issues.append(
            _issue(binding_path, "holdout.target-project", "Binding target Project mismatch")
        )
    intake = None
    try:
        intake = load_project_intake(project)
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
    if intake is None:
        issues.append(
            _issue(project.root_dir, "holdout.intake", "Target intake is unavailable")
        )
    else:
        target = binding.get("target", {})
        expected_dataset = _dataset_projection(
            intake["dataset"],
            dataset_hash=intake["manifest"]["datasetHash"],
        )
        if (
            target.get("requestHash") != intake["manifest"]["requestHash"]
            or target.get("dataset") != expected_dataset
        ):
            issues.append(
                _issue(
                    binding_path,
                    "holdout.target-authority",
                    "Target request or dataset differs from the frozen binding",
                )
            )
    imported = binding.get("importedSources", [])
    if isinstance(imported, list):
        for item in imported:
            if not isinstance(item, dict):
                issues.append(
                    _issue(binding_path, "holdout.import-shape", "Invalid import entry")
                )
                continue
            relative = item.get("path")
            digest = item.get("hash")
            if not isinstance(relative, str) or not isinstance(digest, str):
                issues.append(
                    _issue(binding_path, "holdout.import-shape", "Invalid import identity")
                )
                continue
            actual = confined_path(project.root_dir, relative, f"holdout/import/{relative}")
            frozen = confined_path(
                root / HOLDOUT_IMPORTED_SOURCES,
                relative,
                f"holdout/frozen/{relative}",
            )
            if (
                actual.is_symlink()
                or frozen.is_symlink()
                or not actual.is_file()
                or not frozen.is_file()
                or hash_file(actual) != digest
                or hash_file(frozen) != digest
            ):
                issues.append(
                    _issue(
                        relative,
                        "holdout.import-tampered",
                        "Imported candidate source differs from the frozen binding",
                    )
                )
    studies = (
        binding.get("target", {}).get("studies", [])
        if isinstance(binding.get("target"), dict)
        else []
    )
    if isinstance(studies, list):
        for expected in studies:
            try:
                study = load_study(project, expected["studyId"])
            except (AutoQuantValidationError, KeyError) as error:
                if isinstance(error, AutoQuantValidationError):
                    issues.extend(error.issues)
                else:
                    issues.append(
                        _issue(binding_path, "holdout.study", "Invalid bound Study")
                    )
                continue
            actual = {
                "laneId": expected.get("laneId"),
                "studyId": study.definition.id,
                "studyHash": study.study_hash,
                "inputHash": study.input_hash,
                "judgeHash": study.judge_hash,
                "sourceHash": study.source_hash,
                "datasetHash": study.dataset_hash,
                "dependencyHash": study.dependency_hash,
            }
            if expected != actual:
                issues.append(
                    _issue(
                        study.manifest_path,
                        "holdout.study-stale",
                        f"Bound {expected.get('laneId')} Study authority changed",
                    )
                )
    if issues:
        raise AutoQuantValidationError(issues)
    return HoldoutBindingContext(root, manifest, binding)


def _matching_partial_run(
    project: ProjectContext,
    *,
    study_id: str,
    input_hash: str,
) -> Any | None:
    matching = []
    for summary in list_runs(project, study_id):
        run = load_run(project, summary.id)
        if run.result["studyInputHash"] == input_hash:
            matching.append(run)
    if len(matching) > 1:
        raise AutoQuantValidationError(
            [
                _issue(
                    project.root_dir,
                    "holdout.duplicate-run",
                    f"Holdout lane {study_id} has more than one execution",
                )
            ]
        )
    return matching[0] if matching else None


def run_holdout(project: ProjectContext) -> HoldoutResultContext:
    """Execute or resume the exact frozen lane set and publish one result."""

    binding = load_holdout_binding(project)
    result_root = binding.root_dir / HOLDOUT_RESULT_DIRECTORY
    if result_root.exists() or result_root.is_symlink():
        return load_holdout_result(project)
    expected_studies = {
        item["laneId"]: item
        for item in binding.binding["target"]["studies"]
    }
    expected_by_study = {
        item["studyId"]: item for item in expected_studies.values()
    }
    existing_runs = list_runs(project)
    unrelated = []
    for summary in existing_runs:
        expected = expected_by_study.get(summary.study_id)
        if expected is None:
            unrelated.append(summary.id)
            continue
        run = load_run(project, summary.id)
        if run.result["studyInputHash"] != expected["inputHash"]:
            unrelated.append(summary.id)
    if unrelated:
        raise AutoQuantValidationError(
            [
                _issue(
                    project.root_dir,
                    "holdout.unrelated-run",
                    "Bound Project contains Runs outside the exact challenge "
                    "identity: "
                    + ", ".join(unrelated),
                )
            ]
        )
    lanes = []
    for source_lane in binding.binding["source"]["lanes"]:
        expected = expected_studies[source_lane["id"]]
        run = _matching_partial_run(
            project,
            study_id=expected["studyId"],
            input_hash=expected["inputHash"],
        )
        if run is None:
            run = execute_study(
                project,
                expected["studyId"],
                holdout_authorized=True,
            )
        holdout_value = _objective_value(run.result)
        source_value = source_lane["objectiveValue"]
        lanes.append(
            {
                "id": source_lane["id"],
                "studyId": expected["studyId"],
                "status": run.result["status"],
                "source": {
                    "runId": source_lane["runId"],
                    "resultHash": source_lane["resultHash"],
                    "inputHash": source_lane["inputHash"],
                    "harness": source_lane["harness"],
                    "objective": source_lane["objective"],
                    "value": source_value,
                },
                "holdout": {
                    "runId": run.result["id"],
                    "resultHash": run.manifest["resultHash"],
                    "inputHash": run.result["inputHash"],
                    "studyInputHash": run.result["studyInputHash"],
                    "harness": run.result["harness"],
                    "objective": run.result["objective"],
                    "value": holdout_value,
                    "errors": run.result["errors"],
                },
                "delta": (
                    holdout_value - source_value
                    if holdout_value is not None and source_value is not None
                    else None
                ),
            }
        )
    completed_at = datetime.now(timezone.utc).isoformat()
    identity = {
        "bindingHash": binding.manifest["bindingHash"],
        "completedAt": completed_at,
        "lanes": [
            {
                "id": lane["id"],
                "runId": lane["holdout"]["runId"],
                "resultHash": lane["holdout"]["resultHash"],
            }
            for lane in lanes
        ],
    }
    result_id = f"holdout-result-{hash_json(identity)[:16]}"
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": HOLDOUT_RESULT_KIND,
        "method": HOLDOUT_METHOD,
        "id": result_id,
        "bindingId": binding.binding["id"],
        "bindingHash": binding.manifest["bindingHash"],
        "status": (
            "succeeded"
            if all(lane["status"] == "succeeded" for lane in lanes)
            else "failed"
        ),
        "completedAt": completed_at,
        "source": {
            "project": binding.binding["source"]["project"],
            "dossier": binding.binding["source"]["dossier"],
            "dataset": binding.binding["source"]["dataset"],
        },
        "target": {
            "project": binding.binding["target"]["project"],
            "dataset": binding.binding["target"]["dataset"],
        },
        "lanes": lanes,
        "interpretation": {
            "role": "external-temporal-audit",
            "claim": (
                "These metrics describe the frozen research object on one "
                "strictly later period; Core does not convert them into a "
                "production or trading decision."
            ),
            "universalPassThreshold": None,
        },
        "authority": {
            "candidateFrozen": True,
            "selectionAllowed": False,
            "automaticPromotion": False,
            "tradingAuthority": "none",
        },
    }
    staging = binding.root_dir / f".{HOLDOUT_RESULT_DIRECTORY}.creating"
    if staging.exists() or staging.is_symlink():
        raise AutoQuantValidationError(
            [_issue(staging, "holdout.result-staging", "Result staging path exists")]
        )
    try:
        staging.mkdir()
        _write_json(staging / HOLDOUT_RESULT, result)
        files = _result_files(staging)
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "kind": HOLDOUT_RESULT_MANIFEST_KIND,
            "id": result_id,
            "bindingId": binding.binding["id"],
            "completed": True,
            "resultHash": files[HOLDOUT_RESULT],
            "files": files,
        }
        _write_json(staging / HOLDOUT_RESULT_MANIFEST, manifest)
        os.replace(staging, result_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return load_holdout_result(project)


def _validate_result_shape(
    result: dict[str, Any],
    path: Path,
) -> list[ValidationIssue]:
    required = {
        "schemaVersion",
        "kind",
        "method",
        "id",
        "bindingId",
        "bindingHash",
        "status",
        "completedAt",
        "source",
        "target",
        "lanes",
        "interpretation",
        "authority",
    }
    issues = _strict_keys(result, required, path)
    if (
        result.get("schemaVersion") != SCHEMA_VERSION
        or result.get("kind") != HOLDOUT_RESULT_KIND
        or result.get("method") != HOLDOUT_METHOD
        or result.get("status") not in {"succeeded", "failed"}
    ):
        issues.append(_issue(path, "holdout.result-contract", "Invalid result contract"))
    lanes = result.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        issues.append(_issue(f"{path}/lanes", "schema.array", "Result lanes required"))
    return issues


def _expected_result_id(result: dict[str, Any]) -> str:
    identity = {
        "bindingHash": result["bindingHash"],
        "completedAt": result["completedAt"],
        "lanes": [
            {
                "id": lane["id"],
                "runId": lane["holdout"]["runId"],
                "resultHash": lane["holdout"]["resultHash"],
            }
            for lane in result["lanes"]
        ],
    }
    return f"holdout-result-{hash_json(identity)[:16]}"


def load_holdout_result(project: ProjectContext) -> HoldoutResultContext:
    binding = load_holdout_binding(project)
    root = binding.root_dir / HOLDOUT_RESULT_DIRECTORY
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "holdout.result-missing", "Holdout has no terminal result")]
        )
    manifest_path = root / HOLDOUT_RESULT_MANIFEST
    result_path = root / HOLDOUT_RESULT
    manifest = _read_json(manifest_path, "holdout result manifest")
    result = _read_json(result_path, "holdout result")
    required = {
        "schemaVersion",
        "kind",
        "id",
        "bindingId",
        "completed",
        "resultHash",
        "files",
    }
    issues = _strict_keys(manifest, required, manifest_path)
    try:
        actual_files = _result_files(root)
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
        actual_files = {}
    if (
        manifest.get("schemaVersion") != SCHEMA_VERSION
        or manifest.get("kind") != HOLDOUT_RESULT_MANIFEST_KIND
        or manifest.get("completed") is not True
        or manifest.get("id") != result.get("id")
        or manifest.get("bindingId") != binding.binding["id"]
        or manifest.get("resultHash") != actual_files.get(HOLDOUT_RESULT)
        or manifest.get("files") != actual_files
    ):
        issues.append(
            _issue(manifest_path, "holdout.result-manifest", "Invalid result manifest")
        )
    issues.extend(_validate_result_shape(result, result_path))
    if (
        result.get("bindingId") != binding.binding["id"]
        or result.get("bindingHash") != binding.manifest["bindingHash"]
    ):
        issues.append(
            _issue(result_path, "holdout.result-binding", "Result binding mismatch")
        )
    try:
        if result.get("id") != _expected_result_id(result):
            issues.append(
                _issue(
                    result_path,
                    "holdout.result-id",
                    "Result id is not derived from its frozen evidence",
                )
            )
    except (KeyError, TypeError):
        issues.append(
            _issue(result_path, "holdout.result-id", "Result identity is incomplete")
        )
    if (
        result.get("source")
        != {
            "project": binding.binding["source"]["project"],
            "dossier": binding.binding["source"]["dossier"],
            "dataset": binding.binding["source"]["dataset"],
        }
        or result.get("target")
        != {
            "project": binding.binding["target"]["project"],
            "dataset": binding.binding["target"]["dataset"],
        }
    ):
        issues.append(
            _issue(
                result_path,
                "holdout.result-authority",
                "Result source or target differs from the binding",
            )
        )
    source_lanes = {
        lane["id"]: lane for lane in binding.binding["source"]["lanes"]
    }
    expected_run_ids: set[str] = set()
    lanes = result.get("lanes", [])
    if isinstance(lanes, list):
        for lane in lanes:
            try:
                source_lane = source_lanes[lane["id"]]
                expected_source = {
                    "runId": source_lane["runId"],
                    "resultHash": source_lane["resultHash"],
                    "inputHash": source_lane["inputHash"],
                    "harness": source_lane["harness"],
                    "objective": source_lane["objective"],
                    "value": source_lane["objectiveValue"],
                }
                if lane["source"] != expected_source:
                    issues.append(
                        _issue(
                            result_path,
                            "holdout.result-source",
                            f"Stored {lane.get('id')} source differs from the binding",
                        )
                    )
                run_id = lane["holdout"]["runId"]
                run = load_run(project, run_id)
                expected_run_ids.add(run_id)
                actual = {
                    "runId": run.result["id"],
                    "resultHash": run.manifest["resultHash"],
                    "inputHash": run.result["inputHash"],
                    "studyInputHash": run.result["studyInputHash"],
                    "harness": run.result["harness"],
                    "objective": run.result["objective"],
                    "value": _objective_value(run.result),
                    "errors": run.result["errors"],
                }
                if lane["holdout"] != actual or lane["status"] != run.result["status"]:
                    issues.append(
                        _issue(
                            result_path,
                            "holdout.result-run",
                            f"Stored {lane.get('id')} result differs from immutable Run",
                        )
                    )
                source_value = expected_source["value"]
                holdout_value = actual["value"]
                expected_delta = (
                    holdout_value - source_value
                    if holdout_value is not None and source_value is not None
                    else None
                )
                if lane.get("delta") != expected_delta:
                    issues.append(
                        _issue(
                            result_path,
                            "holdout.result-delta",
                            f"Stored {lane.get('id')} delta does not reconcile",
                        )
                    )
            except (KeyError, TypeError, AutoQuantValidationError) as error:
                if isinstance(error, AutoQuantValidationError):
                    issues.extend(error.issues)
                else:
                    issues.append(
                        _issue(result_path, "holdout.result-lane", "Invalid result lane")
                    )
    actual_run_ids = {summary.id for summary in list_runs(project)}
    if expected_run_ids != actual_run_ids:
        issues.append(
            _issue(
                project.root_dir,
                "holdout.result-run-set",
                "Project Run set differs from the one-shot holdout result",
            )
        )
    expected_status = (
        "succeeded"
        if isinstance(lanes, list)
        and lanes
        and all(lane.get("status") == "succeeded" for lane in lanes)
        else "failed"
    )
    if result.get("status") != expected_status:
        issues.append(
            _issue(
                result_path,
                "holdout.result-status",
                "Terminal status does not reconcile with lane Runs",
            )
        )
    if result.get("authority") != {
        "candidateFrozen": True,
        "selectionAllowed": False,
        "automaticPromotion": False,
        "tradingAuthority": "none",
    }:
        issues.append(
            _issue(
                result_path,
                "holdout.result-authority",
                "Result authority must remain frozen and non-trading",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return HoldoutResultContext(root, manifest, result)


def load_holdout_status(
    project: ProjectContext,
    *,
    optional: bool = False,
) -> dict[str, Any] | None:
    if not has_holdout_binding(project):
        if optional:
            return None
        return {
            "schemaVersion": SCHEMA_VERSION,
            "kind": HOLDOUT_STATUS_KIND,
            "state": "unbound",
            "binding": None,
            "result": None,
            "nextAction": None,
            "authority": {
                "candidateFrozen": False,
                "selectionAllowed": True,
                "tradingAuthority": "none",
            },
        }
    binding = load_holdout_binding(project)
    result_path = binding.root_dir / HOLDOUT_RESULT_DIRECTORY
    result_context = (
        load_holdout_result(project)
        if result_path.is_dir() and not result_path.is_symlink()
        else None
    )
    state = "completed" if result_context is not None else "bound"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": HOLDOUT_STATUS_KIND,
        "state": state,
        "binding": {
            "id": binding.binding["id"],
            "createdAt": binding.binding["createdAt"],
            "sourceProjectId": binding.binding["source"]["project"]["id"],
            "sourceDossierId": binding.binding["source"]["dossier"]["id"],
            "sourceDataset": binding.binding["source"]["dataset"],
            "targetDataset": binding.binding["target"]["dataset"],
            "laneIds": [
                lane["id"] for lane in binding.binding["source"]["lanes"]
            ],
            "nonOverlap": binding.binding["nonOverlap"],
            "policy": binding.binding["policy"],
        },
        "result": (
            {
                "id": result_context.result["id"],
                "status": result_context.result["status"],
                "completedAt": result_context.result["completedAt"],
                "lanes": result_context.result["lanes"],
                "interpretation": result_context.result["interpretation"],
                "authority": result_context.result["authority"],
            }
            if result_context is not None
            else None
        ),
        "nextAction": (
            _action(
                "holdout.run",
                "Execute the exact frozen external-period challenge once.",
                [
                    "aq",
                    "holdout",
                    "run",
                    str(project.root_dir),
                    "--json",
                ],
                "creates-artifact",
            )
            if result_context is None
            else _action(
                "holdout.show",
                "Verify the immutable external-period challenge result.",
                [
                    "aq",
                    "holdout",
                    "show",
                    str(project.root_dir),
                    "--json",
                ],
                "read-only",
            )
        ),
        "authority": {
            "candidateFrozen": True,
            "selectionAllowed": False,
            "tradingAuthority": "none",
        },
    }


HOLDOUT_BINDING_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "method",
        "id",
        "createdAt",
        "source",
        "target",
        "importedSources",
        "nonOverlap",
        "policy",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": HOLDOUT_BINDING_KIND},
        "method": {"const": HOLDOUT_METHOD},
        "id": {"type": "string", "pattern": "^holdout-[0-9a-f]{16}$"},
        "createdAt": {"type": "string", "minLength": 1},
        "source": {"type": "object"},
        "target": {"type": "object"},
        "importedSources": {"type": "array", "minItems": 1},
        "nonOverlap": {
            "type": "object",
            "additionalProperties": False,
            "required": ["sourceEnd", "targetStart", "strictlyLater"],
            "properties": {
                "sourceEnd": {"type": "string", "minLength": 1},
                "targetStart": {"type": "string", "minLength": 1},
                "strictlyLater": {"const": True},
            },
        },
        "policy": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "evaluationRole",
                "candidateFrozen",
                "selectionAllowed",
                "sessionAllowed",
                "automaticPromotion",
                "tradingAuthority",
                "maximumExecutionsPerLane",
            ],
            "properties": {
                "evaluationRole": {"const": "external-temporal-audit"},
                "candidateFrozen": {"const": True},
                "selectionAllowed": {"const": False},
                "sessionAllowed": {"const": False},
                "automaticPromotion": {"const": False},
                "tradingAuthority": {"const": "none"},
                "maximumExecutionsPerLane": {"const": 1},
            },
        },
    },
}

HOLDOUT_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "method",
        "id",
        "bindingId",
        "bindingHash",
        "status",
        "completedAt",
        "source",
        "target",
        "lanes",
        "interpretation",
        "authority",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": HOLDOUT_RESULT_KIND},
        "method": {"const": HOLDOUT_METHOD},
        "id": {
            "type": "string",
            "pattern": "^holdout-result-[0-9a-f]{16}$",
        },
        "bindingId": {"type": "string", "pattern": "^holdout-[0-9a-f]{16}$"},
        "bindingHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "status": {"enum": ["succeeded", "failed"]},
        "completedAt": {"type": "string", "minLength": 1},
        "source": {"type": "object"},
        "target": {"type": "object"},
        "lanes": {"type": "array", "minItems": 1, "maxItems": 3},
        "interpretation": {"type": "object"},
        "authority": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "candidateFrozen",
                "selectionAllowed",
                "automaticPromotion",
                "tradingAuthority",
            ],
            "properties": {
                "candidateFrozen": {"const": True},
                "selectionAllowed": {"const": False},
                "automaticPromotion": {"const": False},
                "tradingAuthority": {"const": "none"},
            },
        },
    },
}

HOLDOUT_STATUS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "state",
        "binding",
        "result",
        "nextAction",
        "authority",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": HOLDOUT_STATUS_KIND},
        "state": {"enum": ["unbound", "bound", "completed"]},
        "binding": {"type": ["object", "null"]},
        "result": {"type": ["object", "null"]},
        "nextAction": {"type": ["object", "null"]},
        "authority": {"type": "object"},
    },
}
