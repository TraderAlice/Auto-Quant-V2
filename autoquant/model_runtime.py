"""Deterministic, point-in-time supervised-model research runtime."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .intake import _read_source
from .studies import STUDY_ID, hash_file, load_study
from .workspace import AutoQuantValidationError, ProjectContext, ValidationIssue, confined_path


SPLIT_NAMES = ("train", "validation", "test")
MODEL_RUNS_DIRECTORY = "model-runs"
MODEL_RUN_ID = re.compile(r"^model-run-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")


@dataclass(frozen=True)
class ModelRunContext:
    root_dir: Path
    manifest: dict[str, Any]
    receipt: dict[str, Any]


class ModelRuntimeError(ValueError):
    """Stable supervised-model contract failure."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _timestamp_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        raise ModelRuntimeError(
            "model.columns",
            f"Point-in-time frame is missing {column}",
        )
    try:
        values = pd.to_datetime(frame[column], utc=True, errors="raise")
    except (TypeError, ValueError) as error:
        raise ModelRuntimeError(
            "model.timestamp",
            f"{column} must contain valid timestamps: {error}",
        ) from error
    if values.isna().any():
        raise ModelRuntimeError(
            "model.timestamp",
            f"{column} cannot contain missing timestamps",
        )
    return values


def _numeric_matrix(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    try:
        values = frame.loc[:, list(columns)].apply(
            pd.to_numeric,
            errors="raise",
        ).to_numpy(dtype=float)
    except (KeyError, TypeError, ValueError) as error:
        raise ModelRuntimeError(
            "model.numeric",
            f"Model inputs must be numeric: {error}",
        ) from error
    if not np.isfinite(values).all():
        raise ModelRuntimeError(
            "model.non-finite",
            "Model inputs cannot contain missing or non-finite values",
        )
    return values


def _split_labels(
    frame: pd.DataFrame,
    timestamps: pd.Series,
    *,
    split_column: str | None,
    split_timestamps: Mapping[str, Any] | None,
) -> pd.Series:
    if (split_column is None) == (split_timestamps is None):
        raise ModelRuntimeError(
            "model.split",
            "Supply exactly one fixed split_column or split_timestamps",
        )
    if split_column is not None:
        if split_column not in frame:
            raise ModelRuntimeError(
                "model.columns",
                f"Point-in-time frame is missing {split_column}",
            )
        labels = frame[split_column].astype("object").copy()
    else:
        assert split_timestamps is not None
        if set(split_timestamps) != {"trainEnd", "validationEnd"}:
            raise ModelRuntimeError(
                "model.split",
                "split_timestamps must contain trainEnd and validationEnd",
            )
        try:
            train_end = pd.Timestamp(split_timestamps["trainEnd"])
            validation_end = pd.Timestamp(split_timestamps["validationEnd"])
            train_end = (
                train_end.tz_localize("UTC")
                if train_end.tzinfo is None
                else train_end.tz_convert("UTC")
            )
            validation_end = (
                validation_end.tz_localize("UTC")
                if validation_end.tzinfo is None
                else validation_end.tz_convert("UTC")
            )
        except (TypeError, ValueError) as error:
            raise ModelRuntimeError(
                "model.split",
                f"Split boundaries must be valid timestamps: {error}",
            ) from error
        if train_end >= validation_end:
            raise ModelRuntimeError(
                "model.split",
                "trainEnd must precede validationEnd",
            )
        labels = pd.Series("test", index=frame.index, dtype="object")
        labels.loc[timestamps < validation_end] = "validation"
        labels.loc[timestamps < train_end] = "train"

    if set(labels.unique()) != set(SPLIT_NAMES):
        raise ModelRuntimeError(
            "model.split",
            "Fixed split must contain train, validation, and test",
        )
    order = labels.map({name: position for position, name in enumerate(SPLIT_NAMES)})
    if not order.is_monotonic_increasing:
        raise ModelRuntimeError(
            "model.split-overlap",
            "Train, validation, and test must be non-overlapping chronological blocks",
        )
    return labels


def _purged_indices(labels: pd.Series, purge_gap: int) -> dict[str, np.ndarray]:
    if isinstance(purge_gap, bool) or not isinstance(purge_gap, int) or purge_gap < 0:
        raise ModelRuntimeError(
            "model.purge-gap",
            "purge_gap must be a non-negative integer row count",
        )
    indices: dict[str, np.ndarray] = {}
    for name in SPLIT_NAMES:
        positions = np.flatnonzero(labels.to_numpy() == name)
        if name != "test" and purge_gap:
            positions = positions[:-purge_gap]
        if not len(positions):
            raise ModelRuntimeError(
                "model.split-empty",
                f"{name} is empty after the fixed purge gap",
            )
        indices[name] = positions
    return indices


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    residual = actual - predicted
    mse = float(np.mean(residual**2))
    denominator = float(np.sum((actual - np.mean(actual)) ** 2))
    correlation: float | None = None
    if len(actual) > 1 and np.std(actual) > 0 and np.std(predicted) > 0:
        correlation = float(np.corrcoef(actual, predicted)[0, 1])
    return {
        "rows": int(len(actual)),
        "mse": mse,
        "rmse": math.sqrt(mse),
        "mae": float(np.mean(np.abs(residual))),
        "r2": (1.0 - float(np.sum(residual**2)) / denominator)
        if denominator > 0
        else None,
        "correlation": correlation,
    }


def run_supervised_model(
    frame: pd.DataFrame,
    *,
    label_column: str,
    feature_columns: Sequence[str],
    split_column: str | None = None,
    split_timestamps: Mapping[str, Any] | None = None,
    timestamp_column: str = "timestamp",
    available_at_column: str = "available_at",
    label_at_column: str = "label_at",
    purge_gap: int = 0,
    ridge_alpha: float = 1.0,
    seed: int = 0,
) -> dict[str, Any]:
    """Fit on train, select on validation, and audit once on untouched test.

    Every feature row must declare when it was available and every label must
    declare when its outcome completed. The runtime never infers these clocks.
    """

    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ModelRuntimeError("model.frame", "Model frame must be non-empty")
    features = tuple(feature_columns)
    if not features or len(features) != len(set(features)):
        raise ModelRuntimeError(
            "model.features",
            "feature_columns must contain unique feature names",
        )
    reserved = {
        label_column,
        timestamp_column,
        available_at_column,
        label_at_column,
        split_column,
    }
    if any(feature in reserved for feature in features):
        raise ModelRuntimeError(
            "model.features",
            "Features cannot include labels, clocks, or split authority",
        )
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ModelRuntimeError("model.seed", "seed must be an integer")
    if isinstance(ridge_alpha, bool) or not isinstance(ridge_alpha, (int, float)):
        raise ModelRuntimeError("model.ridge", "ridge_alpha must be finite and non-negative")
    alpha = float(ridge_alpha)
    if not math.isfinite(alpha) or alpha < 0:
        raise ModelRuntimeError("model.ridge", "ridge_alpha must be finite and non-negative")

    timestamps = _timestamp_series(frame, timestamp_column)
    available_at = _timestamp_series(frame, available_at_column)
    label_at = _timestamp_series(frame, label_at_column)
    if timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
        raise ModelRuntimeError(
            "model.timestamp",
            "Prediction timestamps must be unique and chronological",
        )
    if (available_at > timestamps).any():
        raise ModelRuntimeError(
            "model.lookahead",
            "Feature availability cannot follow its prediction timestamp",
        )
    if (label_at <= timestamps).any():
        raise ModelRuntimeError(
            "model.label-clock",
            "Label completion must follow its prediction timestamp",
        )

    labels = _split_labels(
        frame,
        timestamps,
        split_column=split_column,
        split_timestamps=split_timestamps,
    )
    indices = _purged_indices(labels, purge_gap)
    for earlier, later in (("train", "validation"), ("validation", "test")):
        next_start = timestamps.iloc[indices[later][0]]
        if (label_at.iloc[indices[earlier]] >= next_start).any():
            raise ModelRuntimeError(
                "model.target-overlap",
                f"{earlier} labels overlap the {later} observation window",
            )

    matrix = _numeric_matrix(frame, features)
    target = _numeric_matrix(frame, (label_column,)).reshape(-1)
    train = indices["train"]
    mean = matrix[train].mean(axis=0)
    scale = matrix[train].std(axis=0)
    scale[scale == 0] = 1.0
    normalized = (matrix - mean) / scale
    design = np.column_stack((np.ones(len(train)), normalized[train]))
    penalty = np.eye(design.shape[1]) * alpha
    penalty[0, 0] = 0.0
    try:
        weights = np.linalg.solve(design.T @ design + penalty, design.T @ target[train])
    except np.linalg.LinAlgError:
        weights = np.linalg.pinv(design.T @ design + penalty) @ design.T @ target[train]
    if not np.isfinite(weights).all():
        raise ModelRuntimeError("model.fit", "Linear model produced non-finite weights")

    model_prediction = weights[0] + normalized @ weights[1:]
    baseline_value = float(target[train].mean())
    baseline_prediction = np.full(len(frame), baseline_value, dtype=float)
    validation = indices["validation"]
    model_validation = _metrics(target[validation], model_prediction[validation])
    baseline_validation = _metrics(target[validation], baseline_prediction[validation])
    selected = (
        "ridge-linear"
        if model_validation["mse"] <= baseline_validation["mse"]
        else "train-mean-baseline"
    )
    selected_prediction = (
        model_prediction if selected == "ridge-linear" else baseline_prediction
    )

    split_metrics: dict[str, Any] = {}
    for name in SPLIT_NAMES:
        positions = indices[name]
        split_metrics[name] = {
            "selected": _metrics(target[positions], selected_prediction[positions]),
            "ridgeLinear": _metrics(target[positions], model_prediction[positions]),
            "trainMeanBaseline": _metrics(
                target[positions],
                baseline_prediction[positions],
            ),
        }

    artifact = {
        "kind": "supervised-linear-model-v1",
        "featureColumns": list(features),
        "labelColumn": label_column,
        "intercept": float(weights[0]),
        "coefficients": [float(value) for value in weights[1:]],
        "trainFeatureMean": [float(value) for value in mean],
        "trainFeatureScale": [float(value) for value in scale],
        "ridgeAlpha": alpha,
        "seed": seed,
        "baseline": {"kind": "train-mean", "value": baseline_value},
    }
    identity = hashlib.sha256(
        json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "kind": "supervised-model-research-v1",
        "tradingAuthority": "none",
        "selectionAuthority": "validation-only",
        "testUse": "terminal-audit-only",
        "selectedModel": selected,
        "splitProtocol": {
            "method": "fixed-column" if split_column else "fixed-timestamp-boundaries",
            "purgeGapRows": purge_gap,
            "targetCrossesBoundary": False,
            "rows": {name: int(len(indices[name])) for name in SPLIT_NAMES},
            "boundaries": {
                name: {
                    "start": timestamps.iloc[positions[0]].isoformat(),
                    "end": timestamps.iloc[positions[-1]].isoformat(),
                }
                for name, positions in indices.items()
            },
        },
        "metrics": split_metrics,
        "artifacts": {
            "model": artifact,
            "modelSha256": identity,
        },
    }


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


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
            [_issue(path, "model-run.read", f"Cannot read model Run JSON: {error}")]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "model-run.schema", "Model Run JSON must be an object")]
        )
    return value


def _model_runs_root(project: ProjectContext, *, create: bool = False) -> Path:
    root = confined_path(project.root_dir, MODEL_RUNS_DIRECTORY, "project/model-runs")
    if root.is_symlink():
        raise AutoQuantValidationError(
            [_issue(root, "model-run.symlink", "Model Run root cannot be a symlink")]
        )
    if create:
        root.mkdir(exist_ok=True)
    return root


def _new_model_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"model-run-{stamp}-{uuid.uuid4().hex[:12]}"


def execute_supervised_model_run(
    project: ProjectContext,
    study_id: str,
    *,
    frame_path: str,
    label_column: str,
    feature_columns: Sequence[str],
    split_column: str,
    timestamp_column: str = "timestamp",
    available_at_column: str = "available_at",
    label_at_column: str = "label_at",
    purge_gap: int = 0,
    ridge_alpha: float = 1.0,
    seed: int = 0,
) -> ModelRunContext:
    """Execute and publish one immutable supervised-model research receipt."""

    if not STUDY_ID.fullmatch(study_id):
        raise AutoQuantValidationError(
            [_issue(study_id, "model-run.study-id", "Invalid Study id")]
        )
    study = load_study(project, study_id)
    if study.definition.subject.kind != "model":
        raise AutoQuantValidationError(
            [_issue(study_id, "model-run.subject", "Supervised runtime requires a model Study")]
        )
    declared_paths = study.definition.dataset.paths or []
    if frame_path not in declared_paths:
        raise AutoQuantValidationError(
            [_issue(frame_path, "model-run.dataset", "Frame must be declared by the model Study dataset")]
        )
    data_root = confined_path(
        project.root_dir,
        project.manifest.directories["data"],
        "project/data",
    )
    frame_file = confined_path(data_root, frame_path, "model-run/frame")
    if frame_file.is_symlink() or not frame_file.is_file():
        raise AutoQuantValidationError(
            [_issue(frame_file, "model-run.frame", "Model frame must be a real project file")]
        )
    frame = _read_source(frame_file)
    try:
        result = run_supervised_model(
            frame,
            label_column=label_column,
            feature_columns=feature_columns,
            split_column=split_column,
            timestamp_column=timestamp_column,
            available_at_column=available_at_column,
            label_at_column=label_at_column,
            purge_gap=purge_gap,
            ridge_alpha=ridge_alpha,
            seed=seed,
        )
    except ModelRuntimeError as error:
        raise AutoQuantValidationError(
            [_issue(frame_file, error.code, str(error))]
        ) from None

    run_id = _new_model_run_id()
    root = _model_runs_root(project, create=True)
    staging = root / f".{run_id}-{uuid.uuid4().hex}"
    target = root / run_id
    staging.mkdir()
    receipt = {
        "schemaVersion": 1,
        "kind": "autoquant-supervised-model-run",
        "id": run_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "project": {"id": project.manifest.id},
        "study": {
            "id": study.definition.id,
            "hash": study.study_hash,
            "inputHash": study.input_hash,
        },
        "frame": {"path": frame_path, "sha256": hash_file(frame_file)},
        "parameters": {
            "labelColumn": label_column,
            "featureColumns": list(feature_columns),
            "splitColumn": split_column,
            "timestampColumn": timestamp_column,
            "availableAtColumn": available_at_column,
            "labelAtColumn": label_at_column,
            "purgeGap": purge_gap,
            "ridgeAlpha": ridge_alpha,
            "seed": seed,
        },
        "result": result,
        "tradingAuthority": "none",
    }
    try:
        _write_json(staging / "receipt.json", receipt)
        manifest = {
            "schemaVersion": 1,
            "id": run_id,
            "completed": True,
            "receiptHash": hash_file(staging / "receipt.json"),
        }
        _write_json(staging / "manifest.json", manifest)
        if target.exists() or target.is_symlink():
            raise AutoQuantValidationError(
                [_issue(target, "model-run.collision", "Model Run id collision")]
            )
        os.replace(staging, target)
        return load_model_run(project, run_id)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def load_model_run(project: ProjectContext, run_id: str) -> ModelRunContext:
    """Verify one immutable supervised-model research receipt."""

    if not MODEL_RUN_ID.fullmatch(run_id):
        raise AutoQuantValidationError(
            [_issue(run_id, "model-run.id", "Invalid model Run id")]
        )
    root = confined_path(_model_runs_root(project), run_id, f"model-run/{run_id}")
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "model-run.missing", f"Unknown model Run: {run_id}")]
        )
    manifest = _read_json(root / "manifest.json")
    if manifest != {
        "schemaVersion": 1,
        "id": run_id,
        "completed": True,
        "receiptHash": hash_file(root / "receipt.json"),
    }:
        raise AutoQuantValidationError(
            [_issue(root, "model-run.tampered", "Invalid immutable model Run manifest")]
        )
    receipt = _read_json(root / "receipt.json")
    required = {
        "schemaVersion", "kind", "id", "createdAt", "project", "study",
        "frame", "parameters", "result", "tradingAuthority",
    }
    issues: list[ValidationIssue] = []
    if set(receipt) != required or receipt.get("schemaVersion") != 1:
        issues.append(_issue(root, "model-run.schema", "Invalid model Run receipt fields"))
    if receipt.get("kind") != "autoquant-supervised-model-run" or receipt.get("id") != run_id:
        issues.append(_issue(root, "model-run.identity", "Invalid model Run identity"))
    if receipt.get("project") != {"id": project.manifest.id}:
        issues.append(_issue(root, "model-run.project", "Model Run project differs"))
    result = receipt.get("result")
    if (
        receipt.get("tradingAuthority") != "none"
        or not isinstance(result, dict)
        or result.get("tradingAuthority") != "none"
    ):
        issues.append(_issue(root, "model-run.authority", "Model Run has no trading authority"))
    study_ref = receipt.get("study")
    if not isinstance(study_ref, dict) or set(study_ref) != {"id", "hash", "inputHash"}:
        issues.append(_issue(root, "model-run.study", "Invalid model Study reference"))
    else:
        study = load_study(project, study_ref["id"])
        if study.definition.subject.kind != "model" or study_ref != {
            "id": study.definition.id,
            "hash": study.study_hash,
            "inputHash": study.input_hash,
        }:
            issues.append(_issue(root, "model-run.study", "Model Study identity differs"))
    frame_ref = receipt.get("frame")
    if not isinstance(frame_ref, dict) or set(frame_ref) != {"path", "sha256"}:
        issues.append(_issue(root, "model-run.frame", "Invalid model frame reference"))
    else:
        data_root = confined_path(
            project.root_dir,
            project.manifest.directories["data"],
            "project/data",
        )
        frame_file = confined_path(data_root, frame_ref["path"], "model-run/frame")
        if frame_file.is_symlink() or not frame_file.is_file() or hash_file(frame_file) != frame_ref["sha256"]:
            issues.append(_issue(root, "model-run.frame", "Model frame identity differs"))
    if issues:
        raise AutoQuantValidationError(issues)
    return ModelRunContext(root, manifest, receipt)


def list_model_runs(project: ProjectContext) -> list[ModelRunContext]:
    root = _model_runs_root(project)
    if not root.exists():
        return []
    runs: list[ModelRunContext] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir() or not MODEL_RUN_ID.fullmatch(entry.name):
            raise AutoQuantValidationError(
                [_issue(entry, "model-run.entry", "Invalid model Run directory entry")]
            )
        runs.append(load_model_run(project, entry.name))
    return runs
