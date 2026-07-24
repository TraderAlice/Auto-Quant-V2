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

from judges.portfolio_core import constraint_audit
from judges.rl_core import (
    ACTIONS,
    BASE_COST_BPS,
    BASE_STATE_COLUMNS,
    DISCOUNT,
    EPISODES,
    EPSILON_END,
    EPSILON_START,
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


def _panels(
    study: dict[str, Any],
    data_root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dataset = study["dataset"]
    time_range = dataset["time_range"]
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
        index = pd.DatetimeIndex(frame["timestamp"])
        for target, column in (
            (opens, "open"),
            (closes, "close"),
            (volumes, "volume"),
        ):
            values = frame[column].astype(float)
            values.index = index
            target[asset] = values
    return pd.DataFrame(opens), pd.DataFrame(closes), pd.DataFrame(volumes)


def _factor_panels(
    opens: pd.DataFrame,
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    return {
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
            }
        )
    return rows


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


def _evaluate() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    study, data_root = _load_contract()
    module = importlib.import_module("models.candidate")
    feature_names, encoder = _candidate_encoder(module)
    opens, closes, volumes = _panels(study, data_root)
    action_targets = build_action_targets(
        _factor_panels(opens, closes, volumes),
        closes,
    )
    audits = {
        action: constraint_audit(targets)
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
    failures: list[dict[str, Any]] = []
    validation_sharpes: list[float] = []
    test_sharpes: list[float] = []
    validation_advantages: list[float] = []
    test_advantages: list[float] = []

    for fold_name, split in folds.items():
        baselines, ridge_model, best_baseline = _fixed_baselines(
            raw_states,
            action_targets,
            closes,
            volumes,
            split,
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
                )
                selector = q_selector(trained.weights, encoder)
                validation_rollout = rollout_policy(
                    selector,
                    raw_states,
                    action_targets,
                    closes,
                    volumes,
                    split["validation"],
                )
                test_rollout = rollout_policy(
                    selector,
                    raw_states,
                    action_targets,
                    closes,
                    volumes,
                    split["test"],
                )
                validation = rollout_metrics(validation_rollout)
                test = rollout_metrics(test_rollout)
                validation_sharpe = float(validation["net"]["sharpe"])
                test_sharpe = float(test["net"]["sharpe"])
                fold_validation.append(validation_sharpe)
                fold_test.append(test_sharpe)
                validation_sharpes.append(validation_sharpe)
                test_sharpes.append(test_sharpe)
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
                action_rows.extend(
                    _rollout_action_rows(
                        fold_name,
                        seed,
                        "test",
                        test_rollout,
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
        validation_advantages.append(validation_advantage)
        test_advantages.append(test_advantage)
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
                "best_validation_baseline": best_baseline,
            },
        }

    total_trials = len(folds) * len(SEEDS)
    if failures:
        raise TrialFailures(failures)
    metrics = {
        "validation_mean_net_sharpe": float(np.mean(validation_sharpes)),
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
        },
        "constraint_audit": audits,
        "configuration": {
            "actions": list(ACTIONS),
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
        },
        "research_integrity": {
            "selection_split": "validation",
            "test_role": "visible-diagnostic",
            "test_enters_selection": False,
            "external_holdout_rule": (
                "required-after-test-guided-iteration"
            ),
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
        "semantics": {
            "simulation": "governed-factor-mixture-q-policy",
            "state": "fixed causal scalars known through close t",
            "action": "one of four fixed factor mixtures at close t",
            "return": "close t to close t+1",
            "reward": "net return after 10bps cost minus 0.10 * gross_return^2",
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
    return metrics, report, models, histories, action_rows


def main() -> None:
    try:
        metrics, report, models, histories, action_rows = _evaluate()
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
                            "turnover, and costs"
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
