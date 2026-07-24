"""Bounded, verified diagnostics for immutable governed RL Runs."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .mandates import (
    PORTFOLIO_MANDATE,
    validate_portfolio_mandate,
)
from .runs import RunContext, load_run
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


RL_DIAGNOSTICS_KIND = "autoquant-rl-policy-diagnostics"
DEFAULT_RL_POINTS = 180
MIN_RL_POINTS = 40
MAX_RL_POINTS = 400
MAX_ARTIFACT_BYTES = 32 * 1024 * 1024
MAX_ACTION_ROWS = 1_000_000
EXPECTED_ARTIFACT_KINDS = {
    "rl-report",
    "policy-models",
    "training-history",
    "policy-actions",
}
ACTION_COLUMNS = [
    "fold",
    "seed",
    "split",
    "timestamp",
    "action",
    "reward",
    "gross_return",
    "net_return",
    "one_way_turnover",
    "cost",
]
SPLITS = ("validation", "test")


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _fail(path: Path | str, code: str, message: str) -> None:
    raise AutoQuantValidationError([_issue(path, code, message)])


def _finite(value: Any, path: Path | str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        _fail(path, "rl.number", "Expected a finite numeric value")
    if not math.isfinite(number):
        _fail(path, "rl.number", "Expected a finite numeric value")
    return number


def _integer(value: Any, path: Path | str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        _fail(path, "rl.integer", f"Expected an integer >= {minimum}")
    return value


def _session_date(value: Any, path: Path | str) -> str:
    if not isinstance(value, str):
        _fail(path, "rl.timestamp", "Timestamp must be an ISO session date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        _fail(path, "rl.timestamp", "Timestamp must be an ISO session date")
    if parsed.isoformat() != value:
        _fail(path, "rl.timestamp", "Timestamp must be an ISO session date")
    return value


def _close(
    actual: Any,
    expected: Any,
    path: Path | str,
    label: str,
    *,
    tolerance: float = 1e-9,
) -> None:
    actual_number = _finite(actual, path)
    expected_number = _finite(expected, path)
    if not math.isclose(
        actual_number,
        expected_number,
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        _fail(path, "rl.reconciliation", f"Artifact does not reconcile {label}")


def _artifact_paths(
    run: RunContext,
) -> tuple[dict[str, Path], dict[str, dict[str, str]]]:
    if run.result["status"] != "succeeded":
        _fail(
            run.root_dir,
            "rl.run-status",
            "RL diagnostics require a successful immutable Run",
        )
    artifacts = run.result.get("artifacts")
    if not isinstance(artifacts, list):
        _fail(run.root_dir, "rl.artifacts", "Run artifacts must be an array")
    paths: dict[str, Path] = {}
    identities: dict[str, dict[str, str]] = {}
    for index, artifact in enumerate(artifacts):
        artifact_path = f"{run.root_dir}/result.json/artifacts/{index}"
        if not isinstance(artifact, dict):
            _fail(artifact_path, "rl.artifact", "Artifact must be an object")
        kind = artifact.get("kind")
        if kind not in EXPECTED_ARTIFACT_KINDS:
            continue
        if kind in paths:
            _fail(
                artifact_path,
                "rl.duplicate-artifact",
                f"RL artifact kind must be unique: {kind}",
            )
        relative = artifact.get("path")
        if not isinstance(relative, str):
            _fail(
                artifact_path,
                "rl.artifact-path",
                "RL artifact path must be a string",
            )
        path = confined_path(run.root_dir, relative, artifact_path)
        if not path.is_file():
            _fail(path, "rl.artifact-missing", f"Missing artifact: {kind}")
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            _fail(
                path,
                "rl.artifact-size",
                f"RL artifact exceeds {MAX_ARTIFACT_BYTES} bytes",
            )
        content_hash = run.manifest["files"].get(relative)
        if not isinstance(content_hash, str):
            _fail(
                path,
                "rl.artifact-identity",
                "Artifact is absent from immutable Run identity",
            )
        paths[kind] = path
        identities[kind] = {"path": relative, "sha256": content_hash}
    missing = EXPECTED_ARTIFACT_KINDS - paths.keys()
    if missing:
        _fail(
            run.root_dir,
            "rl.artifacts",
            "Run does not declare the fixed RL artifact set: "
            + ", ".join(sorted(missing)),
        )
    return paths, identities


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail(path, "rl.json", f"{label} must be one UTF-8 JSON object")
    if not isinstance(value, dict):
        _fail(path, "rl.json", f"{label} must be one JSON object")
    return value


def _configuration(metrics: dict[str, Any]) -> dict[str, Any]:
    value = metrics.get("configuration")
    if not isinstance(value, dict):
        _fail("RunResult/metrics/configuration", "rl.configuration", "Missing configuration")
    actions = value.get("actions")
    folds = value.get("folds")
    seeds = value.get("seeds")
    features = value.get("featureNames")
    raw_fields = value.get("rawStateFields")
    factor_experts = value.get("factorExperts")
    if (
        not isinstance(actions, list)
        or not actions
        or len(actions) != len(set(actions))
        or not all(isinstance(item, str) and item for item in actions)
    ):
        _fail("metrics/configuration/actions", "rl.actions", "Actions must be unique strings")
    if (
        not isinstance(folds, list)
        or not folds
        or len(folds) != len(set(folds))
        or not all(isinstance(item, str) and item for item in folds)
    ):
        _fail("metrics/configuration/folds", "rl.folds", "Folds must be unique strings")
    if (
        not isinstance(seeds, list)
        or not seeds
        or len(seeds) != len(set(seeds))
        or not all(isinstance(item, int) and not isinstance(item, bool) for item in seeds)
    ):
        _fail("metrics/configuration/seeds", "rl.seeds", "Seeds must be unique integers")
    if (
        not isinstance(features, list)
        or not features
        or len(features) != len(set(features))
        or not all(isinstance(item, str) and item for item in features)
        or not isinstance(raw_fields, list)
        or not all(isinstance(item, str) and item for item in raw_fields)
    ):
        _fail("metrics/configuration/features", "rl.features", "Feature declarations are invalid")
    if factor_experts is None:
        if "candidate" in actions:
            _fail(
                "metrics/configuration/factorExperts",
                "rl.factor-experts",
                "Candidate-fusion Runs must declare their fixed factor experts",
            )
    elif (
        not isinstance(factor_experts, list)
        or "candidate" not in factor_experts
        or len(factor_experts) != len(set(factor_experts))
        or not all(
            isinstance(item, str) and item in actions
            for item in factor_experts
        )
    ):
        _fail(
            "metrics/configuration/factorExperts",
            "rl.factor-experts",
            "Factor experts must be unique declared actions including candidate",
        )
    episodes = _integer(value.get("episodes"), "metrics/configuration/episodes", minimum=1)
    return {
        **value,
        "actions": actions,
        "folds": folds,
        "seeds": seeds,
        "featureNames": features,
        "rawStateFields": raw_fields,
        "episodes": episodes,
        "epsilonStart": _finite(value.get("epsilonStart"), "configuration/epsilonStart"),
        "epsilonEnd": _finite(value.get("epsilonEnd"), "configuration/epsilonEnd"),
        "learningRate": _finite(value.get("learningRate"), "configuration/learningRate"),
        "discount": _finite(value.get("discount"), "configuration/discount"),
        "riskAversion": _finite(value.get("riskAversion"), "configuration/riskAversion"),
        "costBps": _finite(value.get("costBps"), "configuration/costBps"),
    }


def _ranges(
    fold_value: dict[str, Any],
    fold: str,
) -> dict[str, dict[str, Any]]:
    ranges = fold_value.get("ranges")
    if not isinstance(ranges, dict) or set(ranges) != {"train", *SPLITS}:
        _fail(f"metrics/rl/folds/{fold}/ranges", "rl.ranges", "Fold ranges are incomplete")
    output: dict[str, dict[str, Any]] = {}
    previous_end: str | None = None
    for split in ("train", *SPLITS):
        item = ranges.get(split)
        if not isinstance(item, dict):
            _fail(f"metrics/rl/folds/{fold}/ranges/{split}", "rl.range", "Range must be an object")
        start = _session_date(item.get("start"), f"{fold}/{split}/start")
        end = _session_date(item.get("end"), f"{fold}/{split}/end")
        observations = _integer(item.get("observations"), f"{fold}/{split}/observations", minimum=1)
        if start > end or (previous_end is not None and start <= previous_end):
            _fail(f"{fold}/{split}", "rl.range-order", "Fold ranges must be chronological")
        output[split] = {
            "start": start,
            "end": end,
            "observations": observations,
            "role": "training" if split == "train" else (
                "selection" if split == "validation" else "visible-audit"
            ),
        }
        previous_end = end
    return output


def _baseline_split(
    baselines: dict[str, Any],
    name: str,
    split: str,
    path: str,
) -> dict[str, Any]:
    if name.startswith("fixed:"):
        value = baselines.get("fixed_factor_or_blend", {}).get(name.split(":", 1)[1], {}).get(split)
    elif name == "best-training-expert":
        value = baselines.get("best_training_expert", {}).get(split)
    elif name == "contextual-ridge":
        value = baselines.get("contextual_ridge", {}).get(split)
    else:
        _fail(path, "rl.baseline-name", f"Unknown baseline: {name}")
    if not isinstance(value, dict):
        _fail(path, "rl.baseline", f"Missing {name} {split} baseline evidence")
    return value


def _performance(
    value: Any,
    path: str,
    actions: list[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "rl.performance", "Trial split evidence must be an object")
    net = value.get("net")
    implementation = value.get("implementation")
    frequencies = value.get("action_frequency")
    if not isinstance(net, dict) or not isinstance(implementation, dict) or not isinstance(frequencies, dict):
        _fail(path, "rl.performance", "Trial performance evidence is incomplete")
    if set(frequencies) != set(actions):
        _fail(path, "rl.action-frequency", "Action frequencies differ from configuration")
    normalized_frequencies = {
        action: _finite(frequencies[action], f"{path}/action_frequency/{action}")
        for action in actions
    }
    if (
        any(value < -1e-12 or value > 1.0 + 1e-12 for value in normalized_frequencies.values())
        or not math.isclose(sum(normalized_frequencies.values()), 1.0, abs_tol=1e-9)
    ):
        _fail(path, "rl.action-frequency", "Action frequencies must sum to one")
    return {
        "netSharpe": _finite(net.get("sharpe"), f"{path}/net/sharpe"),
        "netTotalReturn": _finite(net.get("total_return"), f"{path}/net/total_return"),
        "maximumDrawdown": _finite(net.get("maximum_drawdown"), f"{path}/net/maximum_drawdown"),
        "observations": _integer(net.get("observations"), f"{path}/net/observations", minimum=1),
        "cumulativeReward": _finite(value.get("cumulative_reward"), f"{path}/cumulative_reward"),
        "meanReward": _finite(value.get("mean_reward"), f"{path}/mean_reward"),
        "meanOneWayTurnover": _finite(
            implementation.get("mean_one_way_turnover"),
            f"{path}/implementation/mean_one_way_turnover",
        ),
        "totalCostDrag": _finite(
            implementation.get("total_cost_drag"),
            f"{path}/implementation/total_cost_drag",
        ),
        "actionFrequency": normalized_frequencies,
    }


def _aggregate(values: list[float]) -> dict[str, Any]:
    mean = sum(values) / len(values)
    return {
        "observations": len(values),
        "mean": mean,
        "standardDeviation": math.sqrt(
            sum((value - mean) ** 2 for value in values) / len(values)
        ),
        "minimum": min(values),
        "maximum": max(values),
    }


def _reconcile_aggregate(actual: Any, values: list[float], path: str) -> dict[str, Any]:
    if not isinstance(actual, dict):
        _fail(path, "rl.aggregate", "Aggregate evidence must be an object")
    expected = _aggregate(values)
    if actual.get("observations") != expected["observations"]:
        _fail(path, "rl.reconciliation", "Aggregate observation count differs")
    for actual_name, expected_name in (
        ("mean", "mean"),
        ("standard_deviation", "standardDeviation"),
        ("minimum", "minimum"),
        ("maximum", "maximum"),
    ):
        _close(actual.get(actual_name), expected[expected_name], f"{path}/{actual_name}", actual_name)
    return expected


def _models(
    value: dict[str, Any],
    configuration: dict[str, Any],
    input_hash: str,
) -> list[dict[str, Any]]:
    if (
        value.get("inputHash") != input_hash
        or value.get("featureNames") != configuration["featureNames"]
        or value.get("configuration") != configuration
    ):
        _fail("policy-models", "rl.model-identity", "Model identity/configuration differs from RunResult")
    models = value.get("models")
    if not isinstance(models, dict) or set(models) != set(configuration["folds"]):
        _fail("policy-models/models", "rl.models", "Model folds differ from configuration")
    output: list[dict[str, Any]] = []
    for fold in configuration["folds"]:
        fold_models = models.get(fold)
        if not isinstance(fold_models, dict) or not isinstance(fold_models.get("contextualRidgeBaseline"), dict):
            _fail(f"policy-models/models/{fold}", "rl.models", "Fold model evidence is incomplete")
        ridge = fold_models["contextualRidgeBaseline"]
        ridge_columns = ridge.get("columns")
        ridge_mean = ridge.get("mean")
        ridge_scale = ridge.get("scale")
        ridge_coefficients = ridge.get("coefficients")
        if (
            not isinstance(ridge_columns, list)
            or not ridge_columns
            or len(ridge_columns) != len(set(ridge_columns))
            or not all(isinstance(item, str) and item for item in ridge_columns)
            or not isinstance(ridge_mean, dict)
            or set(ridge_mean) != set(ridge_columns)
            or not isinstance(ridge_scale, dict)
            or set(ridge_scale) != set(ridge_columns)
            or not isinstance(ridge_coefficients, list)
            or len(ridge_coefficients) != len(configuration["actions"])
            or any(
                not isinstance(row, list)
                or len(row) != len(ridge_columns) + 1
                for row in ridge_coefficients
            )
        ):
            _fail(
                f"policy-models/models/{fold}/contextualRidgeBaseline",
                "rl.ridge-shape",
                "Contextual ridge parameters have the wrong shape",
            )
        for column in ridge_columns:
            _finite(ridge_mean[column], f"policy-models/{fold}/ridge/mean/{column}")
            if _finite(ridge_scale[column], f"policy-models/{fold}/ridge/scale/{column}") <= 0:
                _fail(
                    f"policy-models/{fold}/ridge/scale/{column}",
                    "rl.ridge-scale",
                    "Contextual ridge scale must be positive",
                )
        for action_index, coefficients in enumerate(ridge_coefficients):
            for coefficient_index, coefficient in enumerate(coefficients):
                _finite(
                    coefficient,
                    f"policy-models/{fold}/ridge/{action_index}/{coefficient_index}",
                )
        seeds = fold_models.get("seeds")
        if not isinstance(seeds, dict) or set(seeds) != {str(seed) for seed in configuration["seeds"]}:
            _fail(f"policy-models/models/{fold}/seeds", "rl.models", "Model seeds differ from configuration")
        for seed in configuration["seeds"]:
            weights = seeds[str(seed)].get("weights") if isinstance(seeds[str(seed)], dict) else None
            if (
                not isinstance(weights, list)
                or len(weights) != len(configuration["actions"])
                or any(
                    not isinstance(row, list)
                    or len(row) != len(configuration["featureNames"])
                    for row in weights
                )
            ):
                _fail(f"policy-models/{fold}/{seed}", "rl.model-shape", "Q weights have the wrong shape")
            normalized = [
                [
                    _finite(weight, f"policy-models/{fold}/{seed}/{action_index}/{feature_index}")
                    for feature_index, weight in enumerate(row)
                ]
                for action_index, row in enumerate(weights)
            ]
            output.append({"fold": fold, "seed": seed, "weights": normalized})
    return output


def _training(
    value: dict[str, Any],
    configuration: dict[str, Any],
    ranges: dict[str, dict[str, dict[str, Any]]],
    input_hash: str,
) -> list[dict[str, Any]]:
    if value.get("inputHash") != input_hash:
        _fail("training-history/inputHash", "rl.training-identity", "Training identity differs from RunResult")
    histories = value.get("histories")
    if not isinstance(histories, dict) or set(histories) != set(configuration["folds"]):
        _fail("training-history/histories", "rl.training", "Training folds differ from configuration")
    output: list[dict[str, Any]] = []
    for fold in configuration["folds"]:
        fold_histories = histories.get(fold)
        if not isinstance(fold_histories, dict) or set(fold_histories) != {
            str(seed) for seed in configuration["seeds"]
        }:
            _fail(f"training-history/{fold}", "rl.training", "Training seeds differ from configuration")
        for seed in configuration["seeds"]:
            episodes = fold_histories[str(seed)]
            if not isinstance(episodes, list) or len(episodes) != configuration["episodes"]:
                _fail(f"training-history/{fold}/{seed}", "rl.training-budget", "Training episode budget differs")
            for index, episode in enumerate(episodes, start=1):
                path = f"training-history/{fold}/{seed}/{index}"
                if not isinstance(episode, dict) or episode.get("episode") != index:
                    _fail(path, "rl.training-episode", "Training episodes must be complete and ordered")
                counts = episode.get("actionCounts")
                if not isinstance(counts, dict) or set(counts) != set(configuration["actions"]):
                    _fail(path, "rl.training-actions", "Training action counts differ from configuration")
                normalized_counts = {
                    action: _integer(counts[action], f"{path}/actionCounts/{action}")
                    for action in configuration["actions"]
                }
                if sum(normalized_counts.values()) != ranges[fold]["train"]["observations"]:
                    _fail(path, "rl.training-observations", "Training action counts do not match fold observations")
                epsilon = _finite(episode.get("epsilon"), f"{path}/epsilon")
                expected_epsilon = configuration["epsilonStart"] + (
                    (index - 1) / max(1, configuration["episodes"] - 1)
                ) * (configuration["epsilonEnd"] - configuration["epsilonStart"])
                _close(epsilon, expected_epsilon, f"{path}/epsilon", "epsilon schedule")
                total_reward = _finite(episode.get("totalReward"), f"{path}/totalReward")
                mean_reward = _finite(episode.get("meanReward"), f"{path}/meanReward")
                _close(
                    mean_reward,
                    total_reward / ranges[fold]["train"]["observations"],
                    f"{path}/meanReward",
                    "mean training reward",
                )
                output.append(
                    {
                        "fold": fold,
                        "seed": seed,
                        "episode": index,
                        "epsilon": epsilon,
                        "totalReward": total_reward,
                        "meanReward": mean_reward,
                        "actionCounts": normalized_counts,
                    }
                )
    return output


def _action_rows(
    path: Path,
    configuration: dict[str, Any],
    ranges: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ACTION_COLUMNS:
                _fail(path, "rl.csv-columns", "Action CSV columns differ from the fixed contract")
            rows: list[dict[str, Any]] = []
            seen: set[tuple[str, int, str, str]] = set()
            last_dates: dict[tuple[str, int, str], str] = {}
            for row_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    _fail(f"{path}:{row_number}", "rl.csv-width", "Action row width differs from header")
                fold = row["fold"]
                split = row["split"]
                action = row["action"]
                try:
                    seed = int(row["seed"])
                except ValueError:
                    _fail(f"{path}:{row_number}", "rl.seed", "Action seed must be an integer")
                if fold not in configuration["folds"] or seed not in configuration["seeds"]:
                    _fail(f"{path}:{row_number}", "rl.trial", "Action row uses an undeclared fold/seed")
                if split not in SPLITS or action not in configuration["actions"]:
                    _fail(f"{path}:{row_number}", "rl.action", "Action row uses an undeclared split/action")
                timestamp = _session_date(row["timestamp"], f"{path}:{row_number}/timestamp")
                declared = ranges[fold][split]
                if not declared["start"] <= timestamp <= declared["end"]:
                    _fail(f"{path}:{row_number}", "rl.action-range", "Action timestamp lies outside its fold split")
                key = (fold, seed, split, timestamp)
                group = (fold, seed, split)
                if key in seen or timestamp <= last_dates.get(group, ""):
                    _fail(f"{path}:{row_number}", "rl.action-order", "Action timestamps must be unique and ordered")
                seen.add(key)
                last_dates[group] = timestamp
                rows.append(
                    {
                        "fold": fold,
                        "seed": seed,
                        "split": split,
                        "timestamp": timestamp,
                        "action": action,
                        "reward": _finite(row["reward"], f"{path}:{row_number}/reward"),
                        "grossReturn": _finite(row["gross_return"], f"{path}:{row_number}/gross_return"),
                        "netReturn": _finite(row["net_return"], f"{path}:{row_number}/net_return"),
                        "oneWayTurnover": _finite(row["one_way_turnover"], f"{path}:{row_number}/one_way_turnover"),
                        "cost": _finite(row["cost"], f"{path}:{row_number}/cost"),
                    }
                )
                if rows[-1]["oneWayTurnover"] < -1e-12 or rows[-1]["cost"] < -1e-12:
                    _fail(
                        f"{path}:{row_number}",
                        "rl.implementation",
                        "Turnover and cost must be non-negative",
                    )
                if len(rows) > MAX_ACTION_ROWS:
                    _fail(path, "rl.row-limit", f"Action CSV exceeds {MAX_ACTION_ROWS} rows")
    except UnicodeDecodeError:
        _fail(path, "rl.csv-encoding", "Action CSV must be UTF-8")
    if not rows:
        _fail(path, "rl.csv-empty", "Action CSV must contain data rows")
    return rows


def _action_projection(
    rows: list[dict[str, Any]],
    trials_by_key: dict[tuple[str, int], dict[str, Any]],
    configuration: dict[str, Any],
    ranges: dict[str, dict[str, dict[str, Any]]],
    point_limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["fold"], row["seed"], row["split"])].append(row)
    summaries: list[dict[str, Any]] = []
    transitions: Counter[tuple[str, str]] = Counter()
    for fold in configuration["folds"]:
        for seed in configuration["seeds"]:
            trial = trials_by_key[(fold, seed)]
            for split in SPLITS:
                group = groups.get((fold, seed, split), [])
                expected_count = ranges[fold][split]["observations"]
                if len(group) != expected_count:
                    _fail(
                        f"policy-actions/{fold}/{seed}/{split}",
                        "rl.action-coverage",
                        "Action rows do not match declared split observations",
                    )
                expected = trial[split]
                counts = Counter(row["action"] for row in group)
                frequencies = {
                    action: counts[action] / len(group)
                    for action in configuration["actions"]
                }
                for action in configuration["actions"]:
                    _close(
                        frequencies[action],
                        expected["actionFrequency"].get(action),
                        f"policy-actions/{fold}/{seed}/{split}/{action}",
                        "action frequency",
                    )
                cumulative_reward = sum(row["reward"] for row in group)
                mean_turnover = sum(row["oneWayTurnover"] for row in group) / len(group)
                total_cost = sum(row["cost"] for row in group)
                _close(cumulative_reward, expected["cumulativeReward"], f"{fold}/{seed}/{split}/reward", "cumulative reward")
                _close(cumulative_reward / len(group), expected["meanReward"], f"{fold}/{seed}/{split}/meanReward", "mean reward")
                _close(mean_turnover, expected["meanOneWayTurnover"], f"{fold}/{seed}/{split}/turnover", "mean turnover")
                _close(total_cost, expected["totalCostDrag"], f"{fold}/{seed}/{split}/cost", "cost drag")
                transition_count = 0
                for prior, current in zip(group, group[1:]):
                    if prior["action"] != current["action"]:
                        transitions[(prior["action"], current["action"])] += 1
                        transition_count += 1
                summaries.append(
                    {
                        "fold": fold,
                        "seed": seed,
                        "split": split,
                        "role": "selection" if split == "validation" else "visible-audit",
                        "observations": len(group),
                        "actionFrequency": frequencies,
                        "cumulativeReward": cumulative_reward,
                        "meanReward": cumulative_reward / len(group),
                        "meanOneWayTurnover": mean_turnover,
                        "totalCostDrag": total_cost,
                        "actionTransitions": transition_count,
                    }
                )

    anchors: set[int] = set()
    group_indices: dict[tuple[str, int, str], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        group_indices[(row["fold"], row["seed"], row["split"])].append(index)
    for indices in group_indices.values():
        anchors.update((indices[0], indices[-1]))
    anchors.add(max(range(len(rows)), key=lambda index: abs(rows[index]["reward"])))
    anchors.add(max(range(len(rows)), key=lambda index: rows[index]["cost"]))
    selected = set(anchors)
    remaining = [index for index in range(len(rows)) if index not in selected]
    slots = max(0, point_limit - len(selected))
    if slots >= len(remaining):
        selected.update(remaining)
    elif slots == 1:
        selected.add(remaining[len(remaining) // 2])
    elif slots > 1:
        selected.update(
            remaining[
                round(position * (len(remaining) - 1) / (slots - 1))
            ]
            for position in range(slots)
        )
    transition_rows = [
        {"from": source, "to": target, "count": count}
        for (source, target), count in sorted(
            transitions.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    return summaries, {
        "totalRows": len(rows),
        "sampledRows": len(selected),
        "pointLimit": point_limit,
        "sampling": "deterministic-even-with-trial-endpoints-and-extremes",
        "points": [rows[index] for index in sorted(selected)],
        "transitions": transition_rows,
    }


def load_rl_diagnostics(
    project: ProjectContext,
    run_id: str,
    *,
    point_limit: int = DEFAULT_RL_POINTS,
) -> dict[str, Any]:
    """Verify and project one immutable governed RL Run."""

    if (
        not isinstance(point_limit, int)
        or isinstance(point_limit, bool)
        or not MIN_RL_POINTS <= point_limit <= MAX_RL_POINTS
    ):
        _fail(
            point_limit,
            "rl.point-limit",
            f"point_limit must be {MIN_RL_POINTS}..{MAX_RL_POINTS}",
        )
    run = load_run(project, run_id)
    if run.result["objective"]["metric"] != "validation_mean_net_sharpe":
        _fail(run.root_dir, "rl.run-kind", "Run is not a governed RL policy evaluation")
    paths, artifacts = _artifact_paths(run)
    report = _read_object(paths["rl-report"], "RL report")
    models_value = _read_object(paths["policy-models"], "Policy models")
    histories_value = _read_object(paths["training-history"], "Training history")
    for label, value, path in (
        ("report", report, paths["rl-report"]),
        ("models", models_value, paths["policy-models"]),
        ("training history", histories_value, paths["training-history"]),
    ):
        if value.get("schemaVersion") != SCHEMA_VERSION:
            _fail(path, "rl.schema-version", f"RL {label} schema version differs")
    if report.get("inputHash") != run.result["inputHash"]:
        _fail(paths["rl-report"], "rl.report-identity", "Report input identity differs from RunResult")
    if report.get("metrics") != run.result["metrics"]:
        _fail(paths["rl-report"], "rl.report-metrics", "Report metrics differ from immutable RunResult")
    report_dataset = report.get("dataset")
    if (
        not isinstance(report_dataset, dict)
        or report_dataset.get("id") != run.result["dataset"].get("id")
        or report_dataset.get("version") != run.result["dataset"].get("version")
        or report_dataset.get("universe") != run.result["dataset"].get("universe")
    ):
        _fail(paths["rl-report"], "rl.report-dataset", "Report dataset differs from RunResult")
    semantics = report.get("semantics")
    if not isinstance(semantics, dict) or semantics.get("tradingAuthority") != "none":
        _fail(paths["rl-report"], "rl.semantics", "RL report must preserve no-trading authority")

    metrics = run.result["metrics"]
    configuration = _configuration(metrics)
    has_candidate_fusion = "candidate" in configuration["actions"]
    factor_experts = configuration.get(
        "factorExperts",
        [
            action
            for action in configuration["actions"]
            if action != "balanced"
        ],
    )
    models = _models(models_value, configuration, run.result["inputHash"])
    fold_metrics = metrics.get("rl", {}).get("folds")
    baseline_metrics = metrics.get("baselines")
    if (
        not isinstance(fold_metrics, dict)
        or set(fold_metrics) != set(configuration["folds"])
        or not isinstance(baseline_metrics, dict)
        or set(baseline_metrics) != set(configuration["folds"])
    ):
        _fail("RunResult/metrics", "rl.folds", "RL and baseline folds differ from configuration")

    ranges: dict[str, dict[str, dict[str, Any]]] = {}
    trials: list[dict[str, Any]] = []
    baselines: list[dict[str, Any]] = []
    validation_sharpes: list[float] = []
    test_sharpes: list[float] = []
    validation_advantages: list[float] = []
    test_advantages: list[float] = []
    candidate_validation_sharpes: list[float] = []
    candidate_test_sharpes: list[float] = []
    validation_advantages_vs_candidate: list[float] = []
    test_advantages_vs_candidate: list[float] = []
    for fold in configuration["folds"]:
        fold_value = fold_metrics[fold]
        if not isinstance(fold_value, dict):
            _fail(f"metrics/rl/folds/{fold}", "rl.fold", "Fold evidence must be an object")
        ranges[fold] = _ranges(fold_value, fold)
        fold_baselines = baseline_metrics[fold]
        selected = fold_baselines.get("best_validation_policy")
        if not isinstance(selected, str):
            _fail(f"metrics/baselines/{fold}", "rl.baseline", "Missing validation-selected baseline")
        baseline_names = [
            *(f"fixed:{action}" for action in configuration["actions"]),
            "best-training-expert",
            "contextual-ridge",
        ]
        for name in baseline_names:
            validation_value = _performance(
                _baseline_split(fold_baselines, name, "validation", f"baselines/{fold}/{name}"),
                f"baselines/{fold}/{name}/validation",
                configuration["actions"],
            )
            test_value = _performance(
                _baseline_split(fold_baselines, name, "test", f"baselines/{fold}/{name}"),
                f"baselines/{fold}/{name}/test",
                configuration["actions"],
            )
            baselines.append(
                {
                    "fold": fold,
                    "name": name,
                    "selectedOnValidation": name == selected,
                    "validation": validation_value,
                    "test": test_value,
                }
            )
        selected_validation = _performance(
            _baseline_split(fold_baselines, selected, "validation", f"baselines/{fold}/{selected}"),
            f"baselines/{fold}/{selected}/validation",
            configuration["actions"],
        )
        selected_test = _performance(
            _baseline_split(fold_baselines, selected, "test", f"baselines/{fold}/{selected}"),
            f"baselines/{fold}/{selected}/test",
            configuration["actions"],
        )
        candidate_validation = None
        candidate_test = None
        if has_candidate_fusion:
            candidate_validation = _performance(
                _baseline_split(
                    fold_baselines,
                    "fixed:candidate",
                    "validation",
                    f"baselines/{fold}/fixed:candidate",
                ),
                f"baselines/{fold}/fixed:candidate/validation",
                configuration["actions"],
            )
            candidate_test = _performance(
                _baseline_split(
                    fold_baselines,
                    "fixed:candidate",
                    "test",
                    f"baselines/{fold}/fixed:candidate",
                ),
                f"baselines/{fold}/fixed:candidate/test",
                configuration["actions"],
            )
            candidate_validation_sharpes.append(
                candidate_validation["netSharpe"]
            )
            candidate_test_sharpes.append(candidate_test["netSharpe"])
        seed_values = fold_value.get("seeds")
        if not isinstance(seed_values, dict) or set(seed_values) != {
            str(seed) for seed in configuration["seeds"]
        }:
            _fail(f"metrics/rl/folds/{fold}/seeds", "rl.trials", "Trial seeds differ from configuration")
        fold_validation: list[float] = []
        fold_test: list[float] = []
        for seed in configuration["seeds"]:
            seed_value = seed_values[str(seed)]
            if not isinstance(seed_value, dict) or seed_value.get("status") != "succeeded":
                _fail(f"metrics/rl/folds/{fold}/seeds/{seed}", "rl.trial-status", "Successful RL Run must preserve every successful trial")
            validation = _performance(
                seed_value.get("validation"),
                f"rl/{fold}/{seed}/validation",
                configuration["actions"],
            )
            test = _performance(
                seed_value.get("test"),
                f"rl/{fold}/{seed}/test",
                configuration["actions"],
            )
            if (
                validation["observations"] != ranges[fold]["validation"]["observations"]
                or test["observations"] != ranges[fold]["test"]["observations"]
            ):
                _fail(f"rl/{fold}/{seed}", "rl.trial-observations", "Trial observations differ from fold ranges")
            validation_advantage = validation["netSharpe"] - selected_validation["netSharpe"]
            test_advantage = test["netSharpe"] - selected_test["netSharpe"]
            validation_advantage_vs_candidate = (
                validation["netSharpe"] - candidate_validation["netSharpe"]
                if candidate_validation is not None
                else None
            )
            test_advantage_vs_candidate = (
                test["netSharpe"] - candidate_test["netSharpe"]
                if candidate_test is not None
                else None
            )
            fold_validation.append(validation["netSharpe"])
            fold_test.append(test["netSharpe"])
            validation_sharpes.append(validation["netSharpe"])
            test_sharpes.append(test["netSharpe"])
            trials.append(
                {
                    "fold": fold,
                    "seed": seed,
                    "status": "succeeded",
                    "selectedBaseline": selected,
                    "validation": validation,
                    "test": test,
                    "validationAdvantage": validation_advantage,
                    "testAdvantage": test_advantage,
                    **(
                        {
                            "validationAdvantageVsCandidateFactor": (
                                validation_advantage_vs_candidate
                            ),
                            "testAdvantageVsCandidateFactor": (
                                test_advantage_vs_candidate
                            ),
                        }
                        if has_candidate_fusion
                        else {}
                    ),
                }
            )
        fold_aggregate = fold_value.get("aggregate")
        if not isinstance(fold_aggregate, dict):
            _fail(f"metrics/rl/folds/{fold}/aggregate", "rl.aggregate", "Missing fold aggregate")
        _reconcile_aggregate(fold_aggregate.get("validation_net_sharpe"), fold_validation, f"{fold}/validation")
        _reconcile_aggregate(fold_aggregate.get("test_net_sharpe"), fold_test, f"{fold}/test")
        validation_advantage = sum(fold_validation) / len(fold_validation) - selected_validation["netSharpe"]
        test_advantage = sum(fold_test) / len(fold_test) - selected_test["netSharpe"]
        validation_advantage_vs_candidate = (
            sum(fold_validation) / len(fold_validation)
            - candidate_validation["netSharpe"]
            if candidate_validation is not None
            else None
        )
        test_advantage_vs_candidate = (
            sum(fold_test) / len(fold_test)
            - candidate_test["netSharpe"]
            if candidate_test is not None
            else None
        )
        _close(
            fold_aggregate.get("validation_advantage_vs_best_baseline"),
            validation_advantage,
            f"{fold}/validationAdvantage",
            "validation baseline advantage",
        )
        _close(
            fold_aggregate.get("test_advantage_vs_validation_selected_baseline"),
            test_advantage,
            f"{fold}/testAdvantage",
            "test baseline advantage",
        )
        if has_candidate_fusion:
            _close(
                fold_aggregate.get("validation_advantage_vs_candidate_factor"),
                validation_advantage_vs_candidate,
                f"{fold}/validationCandidateAdvantage",
                "validation candidate-factor advantage",
            )
            _close(
                fold_aggregate.get("test_advantage_vs_candidate_factor"),
                test_advantage_vs_candidate,
                f"{fold}/testCandidateAdvantage",
                "test candidate-factor advantage",
            )
        validation_advantages.append(validation_advantage)
        test_advantages.append(test_advantage)
        if has_candidate_fusion:
            validation_advantages_vs_candidate.append(
                validation_advantage_vs_candidate
            )
            test_advantages_vs_candidate.append(test_advantage_vs_candidate)

    aggregate = metrics.get("rl", {}).get("aggregate")
    if not isinstance(aggregate, dict):
        _fail("metrics/rl/aggregate", "rl.aggregate", "Missing RL aggregate")
    validation_summary = _reconcile_aggregate(
        aggregate.get("validation_net_sharpe"),
        validation_sharpes,
        "metrics/rl/aggregate/validation",
    )
    test_summary = _reconcile_aggregate(
        aggregate.get("test_net_sharpe"),
        test_sharpes,
        "metrics/rl/aggregate/test",
    )
    if aggregate.get("failures") != []:
        _fail("metrics/rl/aggregate/failures", "rl.failures", "Successful Run cannot hide trial failures")
    _close(aggregate.get("failure_rate"), 0.0, "metrics/rl/aggregate/failure_rate", "failure rate")
    _close(
        metrics.get("validation_mean_net_sharpe"),
        validation_summary["mean"],
        "metrics/validation_mean_net_sharpe",
        "primary objective",
    )
    comparison = metrics.get("comparison")
    if not isinstance(comparison, dict):
        _fail("metrics/comparison", "rl.comparison", "Missing baseline comparison")
    mean_validation_advantage = sum(validation_advantages) / len(validation_advantages)
    mean_test_advantage = sum(test_advantages) / len(test_advantages)
    mean_validation_advantage_vs_candidate = (
        sum(validation_advantages_vs_candidate)
        / len(validation_advantages_vs_candidate)
        if has_candidate_fusion
        else None
    )
    mean_test_advantage_vs_candidate = (
        sum(test_advantages_vs_candidate)
        / len(test_advantages_vs_candidate)
        if has_candidate_fusion
        else None
    )
    _close(
        comparison.get("mean_validation_advantage_vs_best_baseline"),
        mean_validation_advantage,
        "metrics/comparison/validation",
        "mean validation advantage",
    )
    _close(
        comparison.get("mean_test_advantage_vs_validation_selected_baseline"),
        mean_test_advantage,
        "metrics/comparison/test",
        "mean test advantage",
    )
    candidate_validation_summary = None
    candidate_test_summary = None
    if has_candidate_fusion:
        candidate_validation_summary = _reconcile_aggregate(
            comparison.get("candidate_factor_validation_net_sharpe"),
            candidate_validation_sharpes,
            "metrics/comparison/candidateValidation",
        )
        candidate_test_summary = _reconcile_aggregate(
            comparison.get("candidate_factor_test_net_sharpe"),
            candidate_test_sharpes,
            "metrics/comparison/candidateTest",
        )
        _close(
            comparison.get("mean_validation_advantage_vs_candidate_factor"),
            mean_validation_advantage_vs_candidate,
            "metrics/comparison/validationCandidate",
            "mean validation advantage versus candidate factor",
        )
        _close(
            comparison.get("mean_test_advantage_vs_candidate_factor"),
            mean_test_advantage_vs_candidate,
            "metrics/comparison/testCandidate",
            "mean test advantage versus candidate factor",
        )

    training = _training(histories_value, configuration, ranges, run.result["inputHash"])
    action_rows = _action_rows(paths["policy-actions"], configuration, ranges)
    trials_by_key = {(item["fold"], item["seed"]): item for item in trials}
    action_summaries, action_path = _action_projection(
        action_rows,
        trials_by_key,
        configuration,
        ranges,
        point_limit,
    )
    validation_candidate_action_frequency = None
    if has_candidate_fusion:
        validation_candidate_action_frequency = sum(
            item["actionFrequency"]["candidate"]
            for item in action_summaries
            if item["split"] == "validation"
        ) / len(trials)
        _close(
            comparison.get("mean_validation_candidate_action_frequency"),
            validation_candidate_action_frequency,
            "metrics/comparison/candidateActionFrequency",
            "mean validation candidate action frequency",
        )
    dependencies = run.result.get("dependencies")
    if has_candidate_fusion and (
        not isinstance(dependencies, dict)
        or "factors/**" not in dependencies.get("paths", [])
        or not isinstance(dependencies.get("hash"), str)
        or not isinstance(dependencies.get("sourceHashes"), dict)
        or "factors/candidate.py" not in dependencies["sourceHashes"]
    ):
        _fail(
            "RunResult/dependencies",
            "rl.factor-dependency",
            "RL Run must bind the exact content-locked candidate factor source",
        )
    raw_mandate = metrics.get("portfolio_mandate")
    report_mandate = report.get("portfolioMandate")
    if raw_mandate is None and report_mandate is None:
        mandate_projection = {
            "available": False,
            "id": None,
            "sha256": None,
            "sourceKind": "legacy-implicit",
            "requestHash": None,
            "direction": "research-only",
            "family": "dollar-neutral",
            "researchUniverse": run.result["dataset"]["universe"],
            "tradableAssets": run.result["dataset"]["universe"],
            "contextAssets": [],
            "grossLimit": 1.0,
            "maxAbsWeight": 0.30,
            "cashAllowed": True,
            "shortAllowed": True,
            "benchmark": "equal-weight-long-research-universe",
            "riskPolicy": None,
        }
    else:
        if not isinstance(raw_mandate, dict) or not isinstance(
            report_mandate,
            dict,
        ):
            _fail(
                "RunResult/metrics/portfolio_mandate",
                "rl.portfolio-mandate",
                "RL Portfolio Mandate must exist in metrics and report",
            )
        mandate = validate_portfolio_mandate(
            raw_mandate,
            "RunResult/metrics/portfolio_mandate",
        )
        if (
            report_mandate != mandate
            or mandate["researchUniverse"]
            != run.result["dataset"]["universe"]
            or configuration.get("portfolioMandateId") != mandate["id"]
        ):
            _fail(
                "RunResult/metrics/portfolio_mandate",
                "rl.portfolio-mandate",
                "RL Portfolio Mandate does not reconcile report, dataset, and configuration",
            )
        source_hashes = (
            dependencies.get("sourceHashes")
            if isinstance(dependencies, dict)
            else None
        )
        mandate_hash = (
            source_hashes.get(PORTFOLIO_MANDATE)
            if isinstance(source_hashes, dict)
            else None
        )
        if not isinstance(mandate_hash, str):
            _fail(
                "RunResult/dependencies/sourceHashes",
                "rl.portfolio-mandate-dependency",
                "RL Run does not bind the fixed Portfolio Mandate",
            )
        source = mandate["source"]
        construction = mandate["construction"]
        mandate_projection = {
            "available": True,
            "id": mandate["id"],
            "sha256": mandate_hash,
            "sourceKind": source["kind"],
            "requestHash": source["requestHash"],
            "direction": source["direction"],
            "family": construction["family"],
            "researchUniverse": mandate["researchUniverse"],
            "tradableAssets": mandate["tradableAssets"],
            "contextAssets": mandate["contextAssets"],
            "grossLimit": construction["grossLimit"],
            "maxAbsWeight": construction["maxAbsWeight"],
            "cashAllowed": construction["cashAllowed"],
            "shortAllowed": construction["shortAllowed"],
            "benchmark": construction["benchmark"],
            "riskPolicy": construction["riskPolicy"],
        }
    mean_validation_turnover = sum(
        item["validation"]["meanOneWayTurnover"] for item in trials
    ) / len(trials)
    mean_validation_cost = sum(
        item["validation"]["totalCostDrag"] for item in trials
    ) / len(trials)
    research_integrity = metrics.get("research_integrity")
    if (
        not isinstance(research_integrity, dict)
        or research_integrity.get("selection_split") != "validation"
        or research_integrity.get("test_enters_selection") is not False
    ):
        _fail("metrics/research_integrity", "rl.selection-integrity", "RL selection integrity is incomplete")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": RL_DIAGNOSTICS_KIND,
        "run": {
            "id": run.result["id"],
            "status": run.result["status"],
            "summary": run.result["summary"],
            "startedAt": run.result["startedAt"],
            "completedAt": run.result["completedAt"],
            "inputHash": run.result["inputHash"],
            "studyId": run.result["study"]["id"],
            "studyHash": run.result["study"]["hash"],
            "sourceHash": run.result["subject"]["sourceHash"],
            "objective": run.result["objective"],
        },
        "dataset": {
            "id": run.result["dataset"]["id"],
            "version": run.result["dataset"]["version"],
            "hash": run.result["dataset"]["hash"],
            "timeRange": run.result["dataset"]["time_range"],
            "universe": run.result["dataset"]["universe"],
        },
        "harness": run.result["harness"],
        "artifacts": artifacts,
        "portfolioMandate": mandate_projection,
        "protocol": {
            "selectionSplit": "validation",
            "testRole": "visible-diagnostic",
            "testEntersSelection": False,
            "actions": configuration["actions"],
            "factorExperts": factor_experts,
            "folds": configuration["folds"],
            "seeds": configuration["seeds"],
            "featureNames": configuration["featureNames"],
            "rawStateFields": configuration["rawStateFields"],
            "episodes": configuration["episodes"],
            "configuration": configuration,
            "ranges": ranges,
            "semantics": semantics,
        },
        "summary": {
            "validation": validation_summary,
            "testAudit": test_summary,
            "meanValidationAdvantageVsBestBaseline": mean_validation_advantage,
            "meanTestAdvantageVsValidationSelectedBaseline": mean_test_advantage,
            "failureRate": 0.0,
            "trialCount": len(trials),
            "meanValidationOneWayTurnover": mean_validation_turnover,
            "meanValidationCostDrag": mean_validation_cost,
            "rlAddedValidationValue": mean_validation_advantage > 0.0,
        },
        "factorFusion": {
            "available": has_candidate_fusion,
            "mode": (
                "content-locked-candidate-source"
                if has_candidate_fusion
                else "legacy-reference-only"
            ),
            "dependency": dependencies if has_candidate_fusion else None,
            "candidateValidation": candidate_validation_summary,
            "candidateTestAudit": candidate_test_summary,
            "meanValidationAdvantageVsCandidateFactor": (
                mean_validation_advantage_vs_candidate
            ),
            "meanTestAdvantageVsCandidateFactor": (
                mean_test_advantage_vs_candidate
            ),
            "meanValidationCandidateActionFrequency": (
                validation_candidate_action_frequency
            ),
            "rlBeatCandidateOnValidation": (
                mean_validation_advantage_vs_candidate > 0.0
                if has_candidate_fusion
                else None
            ),
        },
        "trials": trials,
        "baselines": baselines,
        "models": models,
        "training": training,
        "actionSummaries": action_summaries,
        "actionPath": action_path,
        "warning": (
            (
                "RL value-add is the validation advantage versus each fold's "
                "fixed validation-selected baseline. Test is visible audit "
                "evidence only; repeated inspection consumes holdout value. "
                "The candidate sleeve is an exact content-locked Study "
                "dependency. Every action sleeve shares the exact fixed "
                "Portfolio Mandate and causal one-sided risk governor; all "
                "actions carry no trading authority."
            )
            if has_candidate_fusion
            else (
                "Legacy RL evidence predates candidate-factor fusion and uses "
                "reference sleeves only. It remains immutable and readable, "
                "but cannot support an RL-versus-candidate claim. Test is "
                "visible audit evidence and actions carry no trading authority."
            )
        ),
    }


RL_DIAGNOSTICS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant bounded governed RL policy diagnostics",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "run",
        "dataset",
        "harness",
        "artifacts",
        "portfolioMandate",
        "protocol",
        "summary",
        "factorFusion",
        "trials",
        "baselines",
        "models",
        "training",
        "actionSummaries",
        "actionPath",
        "warning",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": RL_DIAGNOSTICS_KIND},
        "run": {"type": "object"},
        "dataset": {"type": "object"},
        "harness": {"type": "object"},
        "artifacts": {"type": "object"},
        "portfolioMandate": {"type": "object"},
        "protocol": {"type": "object"},
        "summary": {"type": "object"},
        "factorFusion": {"type": "object"},
        "trials": {"type": "array", "items": {"type": "object"}},
        "baselines": {"type": "array", "items": {"type": "object"}},
        "models": {"type": "array", "items": {"type": "object"}},
        "training": {"type": "array", "items": {"type": "object"}},
        "actionSummaries": {"type": "array", "items": {"type": "object"}},
        "actionPath": {"type": "object"},
        "warning": {"type": "string", "minLength": 1},
    },
}
