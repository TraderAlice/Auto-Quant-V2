"""Fixed governed RL factor-policy Judge for the reference laboratory."""

from __future__ import annotations

import copy
import importlib
import json
import math
import os
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from autoquant.mandates import (
    PORTFOLIO_MANDATE,
    load_portfolio_mandate,
)
from judges.portfolio_core import constraint_audit
from judges.rl_core import (
    ACTIONS,
    BASE_COST_BPS,
    BASE_STATE_COLUMNS,
    DISCOUNT,
    EPISODES,
    EPSILON_END,
    EPSILON_START,
    EXPERTS,
    FEATURE_ABS_LIMIT,
    LEARNING_RATE,
    RISK_AVERSION,
    SEEDS,
    PolicyFailure,
    build_action_targets,
    build_raw_states,
    chronological_folds,
    fixed_selector,
    q_selector,
    ridge_selector,
    rollout_metrics,
    rollout_policy,
    state_with_previous_action,
    train_contextual_ridge,
    train_q_policy,
)


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
MIN_OBSERVATIONS = 240
MAX_FEATURES = 32


class JudgeFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class TrialFailures(JudgeFailure):
    def __init__(self, failures: list[dict[str, Any]]):
        self.failures = failures
        super().__init__(
            "policy.seed-failures",
            f"{len(failures)} declared fold/seed trials failed",
        )


def _write_output(value: dict[str, Any]) -> None:
    Path(os.environ["AUTOQUANT_RUN_OUTPUT"]).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_contract() -> tuple[dict[str, Any], Path]:
    study = json.loads(
        Path(os.environ["AUTOQUANT_STUDY_PATH"]).read_text(encoding="utf-8")
    )
    data_root = Path(os.environ["AUTOQUANT_DATA_ROOT"]).resolve()
    if not data_root.is_dir():
        raise JudgeFailure("dataset.root", "AUTOQUANT_DATA_ROOT is not a directory")
    return study, data_root


def _load_mandate() -> dict[str, Any]:
    path = Path(os.environ["AUTOQUANT_PROJECT_ROOT"]) / PORTFOLIO_MANDATE
    try:
        return load_portfolio_mandate(path)
    except Exception as error:
        raise JudgeFailure(
            "mandate.invalid",
            f"Invalid fixed Portfolio Mandate: {error}",
        ) from error


def _load_asset(data_root: Path, asset: str, start: str, end: str) -> pd.DataFrame:
    source = (data_root / "ohlcv" / f"{asset}.csv").resolve()
    if data_root not in source.parents or not source.is_file():
        raise JudgeFailure("dataset.asset", f"Missing confined OHLCV file for {asset}")
    frame = pd.read_csv(source)
    if tuple(frame.columns) != REQUIRED_COLUMNS:
        raise JudgeFailure(
            "dataset.columns",
            f"{asset} columns must be exactly {', '.join(REQUIRED_COLUMNS)}",
        )
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        format="%Y-%m-%d",
        errors="raise",
    )
    if (
        frame["timestamp"].duplicated().any()
        or not frame["timestamp"].is_monotonic_increasing
    ):
        raise JudgeFailure(
            "dataset.time-order",
            f"{asset} timestamps must be unique and chronological",
        )
    for column in REQUIRED_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    numeric = frame[list(REQUIRED_COLUMNS[1:])].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise JudgeFailure("dataset.non-finite", f"{asset} contains non-finite OHLCV")
    if (frame[["open", "high", "low", "close", "volume"]] <= 0).any().any():
        raise JudgeFailure("dataset.non-positive", f"{asset} contains non-positive OHLCV")
    if (
        (frame["high"] < frame[["open", "close"]].max(axis=1)).any()
        or (frame["low"] > frame[["open", "close"]].min(axis=1)).any()
    ):
        raise JudgeFailure("dataset.bar-shape", f"{asset} contains invalid bars")
    selected = frame[
        (frame["timestamp"] >= pd.Timestamp(start))
        & (frame["timestamp"] <= pd.Timestamp(end))
    ].copy()
    if len(selected) < MIN_OBSERVATIONS:
        raise JudgeFailure(
            "dataset.observations",
            f"{asset} has fewer than {MIN_OBSERVATIONS} observations",
        )
    return selected.reset_index(drop=True)


def _candidate_encoder(
    module: Any,
) -> tuple[list[str], Callable[[dict[str, float]], np.ndarray]]:
    raw_names = getattr(module, "FEATURE_NAMES", None)
    if (
        not isinstance(raw_names, (tuple, list))
        or not raw_names
        or len(raw_names) > MAX_FEATURES
        or any(not isinstance(name, str) or not name for name in raw_names)
        or len(set(raw_names)) != len(raw_names)
    ):
        raise JudgeFailure(
            "policy.features",
            f"FEATURE_NAMES must contain 1 to {MAX_FEATURES} unique strings",
        )
    names = list(raw_names)
    candidate = getattr(module, "encode_state", None)
    if not callable(candidate):
        raise JudgeFailure(
            "policy.api",
            "models.candidate must export callable encode_state(state)",
        )

    def encode(state: dict[str, float]) -> np.ndarray:
        before = copy.deepcopy(state)
        try:
            first = candidate(state)
            second = candidate(state)
        except Exception as error:
            raise PolicyFailure(
                "policy.encoder",
                f"encode_state raised {type(error).__name__}: {error}",
            ) from error
        if state != before:
            raise PolicyFailure(
                "policy.mutation",
                "encode_state mutated the fixed causal state",
            )
        if not isinstance(first, (tuple, list, np.ndarray)) or not isinstance(
            second,
            (tuple, list, np.ndarray),
        ):
            raise PolicyFailure(
                "policy.type",
                "encode_state must return a list, tuple, or numpy array",
            )
        try:
            first_array = np.asarray(first, dtype=float)
            second_array = np.asarray(second, dtype=float)
        except (TypeError, ValueError) as error:
            raise PolicyFailure(
                "policy.numeric",
                f"Encoded features must be numeric: {error}",
            ) from error
        if first_array.shape != (len(names),) or second_array.shape != (
            len(names),
        ):
            raise PolicyFailure(
                "policy.alignment",
                "Encoded vector length must exactly match FEATURE_NAMES",
            )
        if (
            not np.isfinite(first_array).all()
            or not np.isfinite(second_array).all()
        ):
            raise PolicyFailure(
                "policy.non-finite",
                "Encoded state contains a non-finite feature",
            )
        if (
            np.abs(first_array).max() > FEATURE_ABS_LIMIT
            or np.abs(second_array).max() > FEATURE_ABS_LIMIT
        ):
            raise PolicyFailure(
                "policy.bounds",
                f"Encoded features must be within ±{FEATURE_ABS_LIMIT:g}",
            )
        if not np.array_equal(first_array, second_array):
            raise PolicyFailure(
                "policy.nondeterministic",
                "encode_state returned different values for one fixed state",
            )
        return first_array

    return names, encode


def _factor_series(module: Any, frame: pd.DataFrame, asset: str) -> pd.Series:
    before = frame.copy(deep=True)
    try:
        first = module.compute_factor(frame)
        second = module.compute_factor(frame)
    except Exception as error:
        raise JudgeFailure(
            "factor.execution",
            f"compute_factor raised for {asset}: {type(error).__name__}: {error}",
        ) from error
    if not frame.equals(before):
        raise JudgeFailure("factor.mutation", f"compute_factor mutated {asset} input")
    if not isinstance(first, pd.Series) or not isinstance(second, pd.Series):
        raise JudgeFailure("factor.type", "compute_factor must return pandas.Series")
    if (
        len(first) != len(frame)
        or not first.index.equals(frame.index)
        or len(second) != len(frame)
        or not second.index.equals(frame.index)
    ):
        raise JudgeFailure(
            "factor.alignment",
            "Factor Series must preserve the input length and index",
        )
    try:
        first_numeric = pd.to_numeric(first, errors="raise").astype(float)
        second_numeric = pd.to_numeric(second, errors="raise").astype(float)
    except (TypeError, ValueError) as error:
        raise JudgeFailure("factor.numeric", f"Factor must be numeric: {error}") from error
    if (
        np.isinf(first_numeric.to_numpy()).any()
        or np.isinf(second_numeric.to_numpy()).any()
    ):
        raise JudgeFailure("factor.non-finite", "Factor cannot contain infinity")
    if not np.isclose(
        first_numeric.to_numpy(dtype=float),
        second_numeric.to_numpy(dtype=float),
        rtol=1e-10,
        atol=1e-12,
        equal_nan=True,
    ).all():
        raise JudgeFailure(
            "factor.nondeterministic",
            "compute_factor returned different values for one fixed input",
        )
    return first_numeric


def _audit_factor_causality(
    module: Any,
    frame: pd.DataFrame,
    full: pd.Series,
    asset: str,
) -> list[int]:
    cuts = sorted({len(frame) // 2, (len(frame) * 3) // 4, len(frame) - 2})
    for cut in cuts:
        prefix = _factor_series(module, frame.iloc[: cut + 1].copy(), asset)
        start = max(0, cut - 4)
        if not np.isclose(
            full.iloc[start : cut + 1].to_numpy(dtype=float),
            prefix.iloc[start : cut + 1].to_numpy(dtype=float),
            rtol=1e-10,
            atol=1e-12,
            equal_nan=True,
        ).all():
            raise JudgeFailure(
                "factor.lookahead",
                f"{asset} past factor values change when future rows are withheld",
            )
    return cuts


def _panels(
    study: dict[str, Any],
    data_root: Path,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dataset = study["dataset"]
    time_range = dataset["time_range"]
    frames: dict[str, pd.DataFrame] = {}
    opens: dict[str, pd.Series] = {}
    closes: dict[str, pd.Series] = {}
    volumes: dict[str, pd.Series] = {}
    for asset in dataset["universe"]:
        frame = _load_asset(
            data_root,
            asset,
            time_range["start"],
            time_range["end"],
        )
        frames[asset] = frame
        index = pd.DatetimeIndex(frame["timestamp"])
        for target, column in (
            (opens, "open"),
            (closes, "close"),
            (volumes, "volume"),
        ):
            values = frame[column].astype(float)
            values.index = index
            target[asset] = values
    return frames, pd.DataFrame(opens), pd.DataFrame(closes), pd.DataFrame(volumes)


def _factor_panels(
    opens: pd.DataFrame,
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    candidate: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    return {
        "candidate": candidate,
        "activity": np.log(
            volumes
            / volumes.rolling(20, min_periods=20).mean()
        ),
        "intraday": closes / opens - 1.0,
        "reversal": -closes.pct_change(fill_method=None),
    }


def _fixed_baselines(
    raw_states: pd.DataFrame,
    action_targets: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    split: dict[str, pd.Index],
    mandate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    fixed: dict[str, Any] = {}
    training_scores: dict[str, float] = {}
    for action in ACTIONS:
        training = rollout_policy(
            fixed_selector(action),
            raw_states,
            action_targets,
            closes,
            volumes,
            split["train"],
            mandate=mandate,
        )
        training_scores[action] = float(
            rollout_metrics(training)["net"]["sharpe"]
        )
        fixed[action] = {
            name: rollout_metrics(
                rollout_policy(
                    fixed_selector(action),
                    raw_states,
                    action_targets,
                    closes,
                    volumes,
                    index,
                    mandate=mandate,
                )
            )
            for name, index in (
                ("validation", split["validation"]),
                ("test", split["test"]),
            )
        }
    selected_action = max(training_scores, key=training_scores.__getitem__)
    ridge_model = train_contextual_ridge(
        raw_states,
        action_targets,
        closes,
        volumes,
        split["train"],
        mandate=mandate,
    )
    ridge = {
        name: rollout_metrics(
            rollout_policy(
                ridge_selector(ridge_model),
                raw_states,
                action_targets,
                closes,
                volumes,
                index,
                mandate=mandate,
            )
        )
        for name, index in (
            ("validation", split["validation"]),
            ("test", split["test"]),
        )
    }
    result = {
        "fixed_factor_or_blend": fixed,
        "best_training_expert": {
            "selected": selected_action,
            "training_net_sharpe": training_scores,
            "validation": fixed[selected_action]["validation"],
            "test": fixed[selected_action]["test"],
        },
        "contextual_ridge": ridge,
    }
    validation_candidates = {
        **{
            f"fixed:{action}": float(metrics["validation"]["net"]["sharpe"])
            for action, metrics in fixed.items()
        },
        "best-training-expert": float(
            result["best_training_expert"]["validation"]["net"]["sharpe"]
        ),
        "contextual-ridge": float(ridge["validation"]["net"]["sharpe"]),
    }
    best_name = max(validation_candidates, key=validation_candidates.__getitem__)
    return result, ridge_model, best_name


def _baseline_split(
    baselines: dict[str, Any],
    name: str,
    split: str,
) -> dict[str, Any]:
    if name.startswith("fixed:"):
        return baselines["fixed_factor_or_blend"][name.split(":", 1)[1]][split]
    if name == "best-training-expert":
        return baselines["best_training_expert"][split]
    return baselines["contextual_ridge"][split]


def _rollout_action_rows(
    fold: str,
    seed: int,
    split: str,
    rollout,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for timestamp in rollout.actions.index:
        daily = rollout.simulation.daily.loc[timestamp]
        rows.append(
            {
                "fold": fold,
                "seed": seed,
                "split": split,
                "timestamp": timestamp.date().isoformat(),
                "action": rollout.actions.loc[timestamp],
                "reward": float(daily["reward"]),
                "gross_return": float(daily["gross_return"]),
                "net_return": float(daily["net_return"]),
                "one_way_turnover": float(daily["one_way_turnover"]),
                "cost": float(daily["cost"]),
                "execution_risk_status": str(
                    daily["execution_risk_status"]
                ),
                "execution_risk_forecast_available": bool(
                    daily["execution_risk_forecast_available"]
                ),
                "execution_risk_observations": int(
                    daily["execution_risk_observations"]
                ),
                "pretrade_risk_forecast_annualized": float(
                    daily["pretrade_risk_forecast_annualized"]
                ),
                "executed_risk_forecast_annualized": float(
                    daily["executed_risk_forecast_annualized"]
                ),
                "execution_risk_ceiling_annualized": float(
                    daily["execution_risk_ceiling_annualized"]
                ),
                "risk_rebalance_override": bool(
                    daily["risk_rebalance_override"]
                ),
                "execution_reason": str(daily["execution_reason"]),
                "gross_exposure": float(daily["gross_exposure"]),
                "proposed_one_way_turnover": float(
                    daily["proposed_one_way_turnover"]
                ),
            }
        )
    return rows


def _rollout_rationale_rows(
    fold: str,
    seed: int,
    split: str,
    rollout,
    raw_states: pd.DataFrame,
    encoder: Callable[[dict[str, float]], np.ndarray],
    feature_names: list[str],
    weights: np.ndarray,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    previous_action = "balanced"
    for timestamp in rollout.actions.index:
        state = state_with_previous_action(
            raw_states.loc[timestamp],
            previous_action,
        )
        encoded = encoder(state)
        q_values = weights @ encoded
        ranked = sorted(
            range(len(ACTIONS)),
            key=lambda index: (-float(q_values[index]), index),
        )
        selected_index, runner_up_index = ranked[:2]
        selected_action = ACTIONS[selected_index]
        runner_up_action = ACTIONS[runner_up_index]
        if selected_action != rollout.actions.loc[timestamp]:
            raise JudgeFailure(
                "policy.rationale-action",
                "Rationale argmax differs from the policy rollout",
            )
        contributions = (
            weights[selected_index] - weights[runner_up_index]
        ) * encoded
        margin = float(
            q_values[selected_index] - q_values[runner_up_index]
        )
        if not math.isclose(
            float(contributions.sum()),
            margin,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise JudgeFailure(
                "policy.rationale-contribution",
                "Feature contributions do not reproduce the Q margin",
            )
        dominant_index = max(
            range(len(feature_names)),
            key=lambda index: (abs(float(contributions[index])), -index),
        )
        row = {
            "fold": fold,
            "seed": seed,
            "split": split,
            "timestamp": timestamp.date().isoformat(),
            "previousAction": previous_action,
            "selectedAction": selected_action,
            "runnerUpAction": runner_up_action,
            "rawState": {
                field: float(state[field])
                for field in (
                    list(BASE_STATE_COLUMNS)
                    + [f"previous_{action}" for action in ACTIONS]
                )
            },
            "encodedFeatures": {
                name: float(encoded[index])
                for index, name in enumerate(feature_names)
            },
            "qValues": {
                action: float(q_values[index])
                for index, action in enumerate(ACTIONS)
            },
            "actionMargin": margin,
            "tieForBest": margin <= 1e-12,
            "marginContributions": {
                name: float(contributions[index])
                for index, name in enumerate(feature_names)
            },
            "dominantMarginFeature": feature_names[dominant_index],
            "dominantMarginContribution": float(
                contributions[dominant_index]
            ),
        }
        numeric = [
            *row["rawState"].values(),
            *row["encodedFeatures"].values(),
            *row["qValues"].values(),
            row["actionMargin"],
            *row["marginContributions"].values(),
            row["dominantMarginContribution"],
        ]
        if not all(math.isfinite(float(value)) for value in numeric):
            raise JudgeFailure(
                "policy.rationale-non-finite",
                "Policy rationale contains non-finite evidence",
            )
        rows.append(row)
        previous_action = selected_action
    return rows


def _policy_behavior_metrics(
    rationale_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    split: str,
    feature_names: list[str],
) -> dict[str, Any]:
    selected_rationales = [
        row for row in rationale_rows if row["split"] == split
    ]
    selected_actions = [
        row for row in action_rows if row["split"] == split
    ]
    action_by_key = {
        (
            row["fold"],
            int(row["seed"]),
            row["split"],
            row["timestamp"],
        ): row
        for row in selected_actions
    }
    if (
        not selected_rationales
        or len(action_by_key) != len(selected_actions)
        or len(selected_rationales) != len(selected_actions)
    ):
        raise JudgeFailure(
            "policy.rationale-coverage",
            "Policy rationale and action coverage differ",
        )
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in selected_rationales:
        key = (row["fold"], int(row["seed"]))
        groups.setdefault(key, []).append(row)
        action = action_by_key.get(
            (
                row["fold"],
                int(row["seed"]),
                row["split"],
                row["timestamp"],
            )
        )
        if action is None or action["action"] != row["selectedAction"]:
            raise JudgeFailure(
                "policy.rationale-action",
                "Policy rationale differs from the action ledger",
            )

    run_lengths: list[int] = []
    runs_by_action = {action: [] for action in ACTIONS}
    transitions = 0
    comparable_decisions = 0
    trial_metrics: list[dict[str, Any]] = []
    for (fold, seed), rows in groups.items():
        lengths: list[int] = []
        current_action = rows[0]["selectedAction"]
        current_length = 0
        trial_transitions = 0
        for row in rows:
            if row["selectedAction"] != current_action:
                lengths.append(current_length)
                runs_by_action[current_action].append(current_length)
                current_action = row["selectedAction"]
                current_length = 0
                trial_transitions += 1
            current_length += 1
        lengths.append(current_length)
        runs_by_action[current_action].append(current_length)
        run_lengths.extend(lengths)
        transitions += trial_transitions
        comparable_decisions += max(0, len(rows) - 1)
        margins = [float(row["actionMargin"]) for row in rows]
        trial_metrics.append(
            {
                "fold": fold,
                "seed": seed,
                "decisions": len(rows),
                "action_runs": len(lengths),
                "transitions": trial_transitions,
                "transition_rate": (
                    trial_transitions / (len(rows) - 1)
                    if len(rows) > 1
                    else 0.0
                ),
                "mean_action_run_length": float(np.mean(lengths)),
                "mean_action_margin": float(np.mean(margins)),
                "tie_rate": float(
                    np.mean([row["tieForBest"] for row in rows])
                ),
            }
        )

    decisions = len(selected_rationales)
    margins = [
        float(row["actionMargin"]) for row in selected_rationales
    ]
    by_action: dict[str, dict[str, Any]] = {}
    for action_name in ACTIONS:
        rationale_group = [
            row
            for row in selected_rationales
            if row["selectedAction"] == action_name
        ]
        action_group = [
            action_by_key[
                (
                    row["fold"],
                    int(row["seed"]),
                    row["split"],
                    row["timestamp"],
                )
            ]
            for row in rationale_group
        ]
        action_runs = runs_by_action[action_name]
        by_action[action_name] = {
            "decisions": len(rationale_group),
            "frequency": len(rationale_group) / decisions,
            "action_runs": len(action_runs),
            "mean_action_run_length": (
                float(np.mean(action_runs)) if action_runs else 0.0
            ),
            "mean_action_margin": (
                float(
                    np.mean(
                        [row["actionMargin"] for row in rationale_group]
                    )
                )
                if rationale_group
                else 0.0
            ),
            "mean_reward": (
                float(np.mean([row["reward"] for row in action_group]))
                if action_group
                else 0.0
            ),
            "mean_net_return": (
                float(
                    np.mean([row["net_return"] for row in action_group])
                )
                if action_group
                else 0.0
            ),
            "mean_one_way_turnover": (
                float(
                    np.mean(
                        [row["one_way_turnover"] for row in action_group]
                    )
                )
                if action_group
                else 0.0
            ),
            "total_cost": float(
                sum(row["cost"] for row in action_group)
            ),
        }
    by_feature: dict[str, dict[str, Any]] = {}
    for feature_name in feature_names:
        contributions = [
            float(row["marginContributions"][feature_name])
            for row in selected_rationales
        ]
        dominant = sum(
            row["dominantMarginFeature"] == feature_name
            for row in selected_rationales
        )
        by_feature[feature_name] = {
            "dominant_decisions": dominant,
            "dominant_rate": dominant / decisions,
            "mean_signed_margin_contribution": float(
                np.mean(contributions)
            ),
            "mean_absolute_margin_contribution": float(
                np.mean(np.abs(contributions))
            ),
        }
    total_reward = float(sum(row["reward"] for row in selected_actions))
    total_net_return = float(
        sum(row["net_return"] for row in selected_actions)
    )
    total_cost = float(sum(row["cost"] for row in selected_actions))
    mean_turnover = float(
        np.mean([row["one_way_turnover"] for row in selected_actions])
    )
    reconciliation = {
        "rationale_rows": len(selected_rationales),
        "action_rows": len(selected_actions),
        "decision_count_error": abs(
            sum(item["decisions"] for item in by_action.values())
            - decisions
        ),
        "frequency_error": abs(
            sum(item["frequency"] for item in by_action.values()) - 1.0
        ),
        "reward_error": abs(
            sum(
                item["mean_reward"] * item["decisions"]
                for item in by_action.values()
            )
            - total_reward
        ),
        "net_return_error": abs(
            sum(
                item["mean_net_return"] * item["decisions"]
                for item in by_action.values()
            )
            - total_net_return
        ),
        "turnover_error": abs(
            sum(
                item["mean_one_way_turnover"] * item["frequency"]
                for item in by_action.values()
            )
            - mean_turnover
        ),
        "cost_error": abs(
            sum(item["total_cost"] for item in by_action.values())
            - total_cost
        ),
        "transition_run_error": abs(
            len(run_lengths) - transitions - len(groups)
        ),
        "dominant_feature_rate_error": abs(
            sum(item["dominant_rate"] for item in by_feature.values())
            - 1.0
        ),
    }
    reconciliation["passed"] = (
        reconciliation["rationale_rows"]
        == reconciliation["action_rows"]
        == decisions
        and max(
            float(value)
            for key, value in reconciliation.items()
            if key not in {"rationale_rows", "action_rows"}
        )
        <= 1e-10
    )
    return {
        "status": "available",
        "decisions": decisions,
        "trial_paths": len(groups),
        "transitions": transitions,
        "transition_rate": (
            transitions / comparable_decisions
            if comparable_decisions
            else 0.0
        ),
        "retention_rate": (
            1.0 - transitions / comparable_decisions
            if comparable_decisions
            else 1.0
        ),
        "action_runs": len(run_lengths),
        "mean_action_run_length": float(np.mean(run_lengths)),
        "median_action_run_length": float(np.median(run_lengths)),
        "maximum_action_run_length": int(max(run_lengths)),
        "single_bar_run_rate": float(
            np.mean([length == 1 for length in run_lengths])
        ),
        "mean_action_margin": float(np.mean(margins)),
        "median_action_margin": float(np.median(margins)),
        "minimum_action_margin": float(min(margins)),
        "maximum_action_margin": float(max(margins)),
        "tie_decisions": int(
            sum(row["tieForBest"] for row in selected_rationales)
        ),
        "tie_rate": float(
            np.mean(
                [row["tieForBest"] for row in selected_rationales]
            )
        ),
        "total_reward": total_reward,
        "total_net_return": total_net_return,
        "mean_one_way_turnover": mean_turnover,
        "total_cost": total_cost,
        "by_action": by_action,
        "by_feature": by_feature,
        "trials": trial_metrics,
        "reconciliation": reconciliation,
    }


def _aggregate(values: list[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    if not len(array) or not np.isfinite(array).all():
        raise JudgeFailure(
            "policy.aggregate",
            "Cannot aggregate missing or non-finite policy evidence",
        )
    return {
        "observations": int(len(array)),
        "mean": float(array.mean()),
        "standard_deviation": float(array.std(ddof=0)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def _aggregate_execution_risk_trials(
    folds: dict[str, Any],
    split: str,
) -> dict[str, float | int | str]:
    items = [
        seed[split]["execution_risk"]
        for fold in folds.values()
        for seed in fold["seeds"].values()
        if seed.get("status") == "succeeded"
    ]
    active = sum(int(item["active_dates"]) for item in items)
    available = sum(
        int(item["forecast_available_dates"]) for item in items
    )
    executed_breaches = sum(
        int(item["executed_breach_dates"]) for item in items
    )
    if executed_breaches:
        raise JudgeFailure(
            "policy.risk-breach",
            "A governed RL rollout contains an executed-book risk breach",
        )
    return {
        "status": "available" if available else "forecast_unavailable",
        "trial_paths": len(items),
        "active_dates": active,
        "forecast_available_dates": available,
        "forecast_coverage": available / active if active else 0.0,
        "pretrade_breach_dates": sum(
            int(item["pretrade_breach_dates"]) for item in items
        ),
        "risk_rebalance_override_dates": sum(
            int(item["risk_rebalance_override_dates"])
            for item in items
        ),
        "executed_breach_dates": executed_breaches,
        "maximum_executed_forecast_annualized": max(
            (
                float(item["maximum_executed_forecast_annualized"])
                for item in items
            ),
            default=0.0,
        ),
        "maximum_ceiling_error": max(
            (float(item["maximum_ceiling_error"]) for item in items),
            default=0.0,
        ),
    }


def _evaluate() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
]:
    study, data_root = _load_contract()
    mandate = _load_mandate()
    model_module = importlib.import_module("models.candidate")
    factor_module = importlib.import_module("factors.candidate")
    if not callable(getattr(factor_module, "compute_factor", None)):
        raise JudgeFailure(
            "factor.api",
            "factors.candidate must export callable compute_factor(frame)",
        )
    feature_names, encoder = _candidate_encoder(model_module)
    frames, opens, closes, volumes = _panels(study, data_root)
    candidate_by_asset: dict[str, pd.Series] = {}
    factor_causality_cuts: dict[str, list[int]] = {}
    for asset, frame in frames.items():
        factor = _factor_series(factor_module, frame, asset)
        factor_causality_cuts[asset] = _audit_factor_causality(
            factor_module,
            frame,
            factor,
            asset,
        )
        factor.index = pd.DatetimeIndex(frame["timestamp"])
        candidate_by_asset[asset] = factor
    candidate_panel = pd.DataFrame(candidate_by_asset)
    action_targets = build_action_targets(
        _factor_panels(opens, closes, volumes, candidate_panel),
        closes,
        mandate=mandate,
    )
    audits = {
        action: constraint_audit(targets, mandate=mandate)
        for action, targets in action_targets.items()
    }
    if not all(audit["passed"] for audit in audits.values()):
        raise JudgeFailure(
            "policy.constraints",
            "A fixed action violated portfolio target constraints",
        )
    raw_states = build_raw_states(
        closes,
        volumes,
        action_targets,
    )
    forward_valid = (closes.shift(-1) / closes - 1.0).notna().all(axis=1)
    active = pd.Series(True, index=closes.index)
    if mandate["construction"]["family"] == "dollar-neutral":
        for targets in action_targets.values():
            active &= targets.abs().sum(axis=1) > 1e-12
    valid = raw_states.notna().all(axis=1) & forward_valid & active
    active_index = closes.index[valid]
    folds = chronological_folds(active_index)

    sample_positions = sorted(
        {0, len(active_index) // 2, len(active_index) - 1}
    )
    for position in sample_positions:
        for previous_action in ACTIONS:
            encoder(
                state_with_previous_action(
                    raw_states.loc[active_index[position]],
                    previous_action,
                )
            )

    fold_metrics: dict[str, Any] = {}
    baseline_metrics: dict[str, Any] = {}
    policy_models: dict[str, Any] = {}
    training_history: dict[str, Any] = {}
    action_rows: list[dict[str, Any]] = []
    rationale_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    validation_sharpes: list[float] = []
    test_sharpes: list[float] = []
    validation_advantages: list[float] = []
    test_advantages: list[float] = []
    candidate_validation_sharpes: list[float] = []
    candidate_test_sharpes: list[float] = []
    validation_advantages_vs_candidate: list[float] = []
    test_advantages_vs_candidate: list[float] = []
    validation_candidate_action_frequencies: list[float] = []

    for fold_name, split in folds.items():
        baselines, ridge_model, best_baseline = _fixed_baselines(
            raw_states,
            action_targets,
            closes,
            volumes,
            split,
            mandate,
        )
        baseline_metrics[fold_name] = {
            **baselines,
            "best_validation_policy": best_baseline,
        }
        best_validation = float(
            _baseline_split(
                baselines,
                best_baseline,
                "validation",
            )["net"]["sharpe"]
        )
        matching_test = float(
            _baseline_split(
                baselines,
                best_baseline,
                "test",
            )["net"]["sharpe"]
        )
        candidate_validation = float(
            baselines["fixed_factor_or_blend"]["candidate"]["validation"][
                "net"
            ]["sharpe"]
        )
        candidate_test = float(
            baselines["fixed_factor_or_blend"]["candidate"]["test"]["net"][
                "sharpe"
            ]
        )
        candidate_validation_sharpes.append(candidate_validation)
        candidate_test_sharpes.append(candidate_test)
        seed_metrics: dict[str, Any] = {}
        policy_models[fold_name] = {
            "contextualRidgeBaseline": ridge_model,
            "seeds": {},
        }
        training_history[fold_name] = {}
        fold_validation: list[float] = []
        fold_test: list[float] = []
        for seed in SEEDS:
            try:
                trained = train_q_policy(
                    encoder,
                    len(feature_names),
                    raw_states,
                    action_targets,
                    closes,
                    volumes,
                    split["train"],
                    seed=seed,
                    mandate=mandate,
                )
                selector = q_selector(trained.weights, encoder)
                validation_rollout = rollout_policy(
                    selector,
                    raw_states,
                    action_targets,
                    closes,
                    volumes,
                    split["validation"],
                    mandate=mandate,
                )
                test_rollout = rollout_policy(
                    selector,
                    raw_states,
                    action_targets,
                    closes,
                    volumes,
                    split["test"],
                    mandate=mandate,
                )
                validation = rollout_metrics(validation_rollout)
                test = rollout_metrics(test_rollout)
                validation_sharpe = float(validation["net"]["sharpe"])
                test_sharpe = float(test["net"]["sharpe"])
                fold_validation.append(validation_sharpe)
                fold_test.append(test_sharpe)
                validation_sharpes.append(validation_sharpe)
                test_sharpes.append(test_sharpe)
                validation_candidate_action_frequencies.append(
                    float(validation["action_frequency"]["candidate"])
                )
                seed_metrics[str(seed)] = {
                    "status": "succeeded",
                    "validation": validation,
                    "test": test,
                }
                policy_models[fold_name]["seeds"][str(seed)] = {
                    "weights": trained.weights.tolist(),
                }
                training_history[fold_name][str(seed)] = trained.history
                action_rows.extend(
                    _rollout_action_rows(
                        fold_name,
                        seed,
                        "validation",
                        validation_rollout,
                    )
                )
                rationale_rows.extend(
                    _rollout_rationale_rows(
                        fold_name,
                        seed,
                        "validation",
                        validation_rollout,
                        raw_states,
                        encoder,
                        feature_names,
                        trained.weights,
                    )
                )
                action_rows.extend(
                    _rollout_action_rows(
                        fold_name,
                        seed,
                        "test",
                        test_rollout,
                    )
                )
                rationale_rows.extend(
                    _rollout_rationale_rows(
                        fold_name,
                        seed,
                        "test",
                        test_rollout,
                        raw_states,
                        encoder,
                        feature_names,
                        trained.weights,
                    )
                )
            except Exception as error:
                code = getattr(error, "code", "policy.seed-failed")
                failure = {
                    "fold": fold_name,
                    "seed": seed,
                    "code": code,
                    "message": f"{type(error).__name__}: {error}",
                }
                failures.append(failure)
                seed_metrics[str(seed)] = {
                    "status": "failed",
                    "error": failure,
                }
        if not fold_validation:
            fold_metrics[fold_name] = {
                "ranges": {
                    name: {
                        "start": index[0].date().isoformat(),
                        "end": index[-1].date().isoformat(),
                        "observations": len(index),
                    }
                    for name, index in split.items()
                },
                "seeds": seed_metrics,
                "aggregate": {
                    "status": "all-seeds-failed",
                    "best_validation_baseline": best_baseline,
                },
            }
            continue
        validation_advantage = float(np.mean(fold_validation)) - best_validation
        test_advantage = float(np.mean(fold_test)) - matching_test
        validation_advantage_vs_candidate = (
            float(np.mean(fold_validation)) - candidate_validation
        )
        test_advantage_vs_candidate = float(np.mean(fold_test)) - candidate_test
        validation_advantages.append(validation_advantage)
        test_advantages.append(test_advantage)
        validation_advantages_vs_candidate.append(
            validation_advantage_vs_candidate
        )
        test_advantages_vs_candidate.append(test_advantage_vs_candidate)
        fold_metrics[fold_name] = {
            "ranges": {
                name: {
                    "start": index[0].date().isoformat(),
                    "end": index[-1].date().isoformat(),
                    "observations": len(index),
                }
                for name, index in split.items()
            },
            "seeds": seed_metrics,
            "aggregate": {
                "validation_net_sharpe": _aggregate(fold_validation),
                "test_net_sharpe": _aggregate(fold_test),
                "validation_advantage_vs_best_baseline": validation_advantage,
                "test_advantage_vs_validation_selected_baseline": test_advantage,
                "validation_advantage_vs_candidate_factor": (
                    validation_advantage_vs_candidate
                ),
                "test_advantage_vs_candidate_factor": test_advantage_vs_candidate,
                "best_validation_baseline": best_baseline,
            },
        }

    total_trials = len(folds) * len(SEEDS)
    if failures:
        raise TrialFailures(failures)
    policy_rationale = {
        "policy": {
            "method": (
                "linear-q-chosen-vs-runner-up-decomposition-v1"
            ),
            "action_runs": (
                "contiguous-actions-clipped-to-fold-seed-split"
            ),
            "q_scale": "uncalibrated-linear-model-score",
            "feature_contribution": (
                "exact-linear-chosen-minus-runner-decomposition"
            ),
            "realized_outcomes": (
                "descriptive-endogenous-action-conditioning"
            ),
            "selection_authority": "context-only",
            "trading_authority": "none",
        },
        "validation": _policy_behavior_metrics(
            rationale_rows,
            action_rows,
            "validation",
            feature_names,
        ),
        "test": _policy_behavior_metrics(
            rationale_rows,
            action_rows,
            "test",
            feature_names,
        ),
    }
    execution_risk = {
        "policy": {
            "method": (
                "post-drift-executed-book-volatility-compliance-v1"
            ),
            "risk_policy": mandate["construction"]["riskPolicy"],
            "no_trade_priority": "risk-compliance-first",
            "repair": "minimum-proportional-scale-down",
            "selection_authority": "context-only",
            "trading_authority": "none",
        },
        "validation": _aggregate_execution_risk_trials(
            fold_metrics,
            "validation",
        ),
        "test": _aggregate_execution_risk_trials(
            fold_metrics,
            "test",
        ),
    }
    metrics = {
        "validation_mean_net_sharpe": float(np.mean(validation_sharpes)),
        "portfolio_mandate": mandate,
        "rl": {
            "aggregate": {
                "validation_net_sharpe": _aggregate(validation_sharpes),
                "test_net_sharpe": _aggregate(test_sharpes),
                "failure_rate": len(failures) / total_trials,
                "failures": failures,
            },
            "folds": fold_metrics,
        },
        "baselines": baseline_metrics,
        "comparison": {
            "mean_validation_advantage_vs_best_baseline": float(
                np.mean(validation_advantages)
            ),
            "mean_test_advantage_vs_validation_selected_baseline": float(
                np.mean(test_advantages)
            ),
            "candidate_factor_validation_net_sharpe": _aggregate(
                candidate_validation_sharpes
            ),
            "candidate_factor_test_net_sharpe": _aggregate(
                candidate_test_sharpes
            ),
            "mean_validation_advantage_vs_candidate_factor": float(
                np.mean(validation_advantages_vs_candidate)
            ),
            "mean_test_advantage_vs_candidate_factor": float(
                np.mean(test_advantages_vs_candidate)
            ),
            "mean_validation_candidate_action_frequency": float(
                np.mean(validation_candidate_action_frequencies)
            ),
        },
        "policy_rationale": policy_rationale,
        "execution_risk": execution_risk,
        "constraint_audit": audits,
        "configuration": {
            "portfolioMandateId": mandate["id"],
            "actions": list(ACTIONS),
            "factorExperts": list(EXPERTS),
            "rawStateFields": list(BASE_STATE_COLUMNS)
            + [f"previous_{action}" for action in ACTIONS],
            "featureNames": feature_names,
            "seeds": list(SEEDS),
            "folds": list(folds),
            "episodes": EPISODES,
            "learningRate": LEARNING_RATE,
            "discount": DISCOUNT,
            "epsilonStart": EPSILON_START,
            "epsilonEnd": EPSILON_END,
            "riskAversion": RISK_AVERSION,
            "costBps": BASE_COST_BPS,
            "executionRiskMethod": (
                "post-drift-executed-book-volatility-compliance-v1"
            ),
            "executionRiskPriority": "risk-compliance-first",
        },
        "research_integrity": {
            "selection_split": "validation",
            "test_role": "visible-diagnostic",
            "test_enters_selection": False,
            "external_holdout_rule": (
                "required-after-test-guided-iteration"
            ),
            "factor_dependency": {
                "module": "factors.candidate",
                "mode": "content-locked-study-dependency",
                "causalityAuditCuts": factor_causality_cuts,
            },
        },
    }
    if not math.isfinite(metrics["validation_mean_net_sharpe"]):
        raise JudgeFailure("policy.non-finite", "Primary score is non-finite")
    dataset = study["dataset"]
    report = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "dataset": {
            "id": dataset["id"],
            "version": dataset["version"],
            "universe": dataset["universe"],
            "timeRange": dataset["time_range"],
        },
        "portfolioMandate": mandate,
        "semantics": {
            "simulation": "governed-factor-mixture-q-policy",
            "state": "fixed causal scalars known through close t",
            "action": (
                "candidate factor, one of three reference factors, or their "
                "equal-weight blend at close t"
            ),
            "return": "close t to close t+1",
            "reward": "net return after 10bps cost minus 0.10 * gross_return^2",
            "policyRationale": (
                "exact linear chosen-versus-runner-up Q-margin "
                "decomposition; Q scores are uncalibrated and contextual"
            ),
            "executionRisk": (
                "every selected sleeve is rechecked after drift; risk "
                "compliance bypasses the no-trade band with minimum "
                "proportional scale-down"
            ),
            "objective": "mean validation net Sharpe across every successful seed/fold",
            "testRole": "reported audit evidence; never enters promotion",
            "testVisibilityWarning": (
                "Repeated candidate changes after inspecting test metrics consume "
                "their holdout value; use a new external holdout for production claims."
            ),
            "tradingAuthority": "none",
        },
        "dependencies": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "metrics": metrics,
    }
    models = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "featureNames": feature_names,
        "configuration": metrics["configuration"],
        "models": policy_models,
    }
    histories = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "histories": training_history,
    }
    rationales = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "method": (
            "linear-q-chosen-vs-runner-up-decomposition-v1"
        ),
        "actions": list(ACTIONS),
        "rawStateFields": list(BASE_STATE_COLUMNS)
        + [f"previous_{action}" for action in ACTIONS],
        "featureNames": feature_names,
        "rows": rationale_rows,
    }
    return metrics, report, models, histories, action_rows, rationales


def main() -> None:
    try:
        (
            metrics,
            report,
            models,
            histories,
            action_rows,
            rationales,
        ) = _evaluate()
        artifacts = Path(os.environ["AUTOQUANT_ARTIFACTS_DIR"])
        (artifacts / "rl-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (artifacts / "policy-models.json").write_text(
            json.dumps(models, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (artifacts / "training-history.json").write_text(
            json.dumps(histories, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pd.DataFrame(action_rows).to_csv(
            artifacts / "policy-actions.csv",
            index=False,
            float_format="%.12g",
        )
        (artifacts / "policy-rationales.json").write_text(
            json.dumps(rationales, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_output(
            {
                "schema_version": 1,
                "status": "succeeded",
                "summary": (
                    "Governed factor-mixture policy evaluated across all fixed "
                    "folds/seeds; validation mean net Sharpe="
                    f"{metrics['validation_mean_net_sharpe']:.6f}"
                ),
                "metrics": metrics,
                "artifacts": [
                    {
                        "kind": "rl-report",
                        "path": "rl-report.json",
                        "description": (
                            "State/action/reward semantics, folds, seeds, baselines, "
                            "comparisons, warnings, and complete metrics"
                        ),
                    },
                    {
                        "kind": "policy-models",
                        "path": "policy-models.json",
                        "description": (
                            "Exact candidate feature names, configuration, Q weights, "
                            "and contextual-ridge baseline parameters"
                        ),
                    },
                    {
                        "kind": "training-history",
                        "path": "training-history.json",
                        "description": "Every episode for every declared fold and seed",
                    },
                    {
                        "kind": "policy-actions",
                        "path": "policy-actions.csv",
                        "description": (
                            "Timestamped validation/test actions, rewards, returns, "
                            "turnover, costs, and executed-book risk compliance"
                        ),
                    },
                    {
                        "kind": "policy-rationales",
                        "path": "policy-rationales.json",
                        "description": (
                            "Exact raw state, encoded features, action Q values, "
                            "runner-up margins, and linear feature contributions"
                        ),
                    },
                ],
                "errors": [],
            }
        )
    except TrialFailures as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": str(error),
                "metrics": {
                    "declared_trials": len(SEEDS) * 2,
                    "failed_trials": len(error.failures),
                },
                "artifacts": [],
                "errors": [
                    {
                        "code": item["code"],
                        "message": (
                            f"{item['fold']} seed {item['seed']}: "
                            f"{item['message']}"
                        ),
                    }
                    for item in error.failures
                ],
            }
        )
    except (JudgeFailure, PolicyFailure) as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": str(error),
                "metrics": {},
                "artifacts": [],
                "errors": [
                    {
                        "code": getattr(error, "code", "policy.failure"),
                        "message": str(error),
                    }
                ],
            }
        )
    except Exception as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": f"RL evaluation raised {type(error).__name__}",
                "metrics": {},
                "artifacts": [],
                "errors": [
                    {
                        "code": "policy.exception",
                        "message": f"{type(error).__name__}: {error}",
                    }
                ],
            }
        )


if __name__ == "__main__":
    main()
