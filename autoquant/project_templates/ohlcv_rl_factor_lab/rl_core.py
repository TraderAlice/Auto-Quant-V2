"""Fixed bounded RL environment, learner, and baseline primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

try:
    from judges.portfolio_core import (
        BASE_COST_BPS,
        NO_TRADE_ONE_WAY,
        REFERENCE_NAV,
        Simulation,
        construct_signal_policy,
        drift_weights,
        implementation_metrics,
        performance_metrics,
    )
except ModuleNotFoundError:  # Package-level deterministic primitive tests.
    from autoquant.project_templates.ohlcv_portfolio_lab.portfolio_core import (
        BASE_COST_BPS,
        NO_TRADE_ONE_WAY,
        REFERENCE_NAV,
        Simulation,
        construct_signal_policy,
        drift_weights,
        implementation_metrics,
        performance_metrics,
    )


ACTIONS = ("candidate", "activity", "intraday", "reversal", "balanced")
EXPERTS = ACTIONS[:4]
ACTION_MIXTURES = {
    expert: {
        candidate: float(candidate == expert)
        for candidate in EXPERTS
    }
    for expert in EXPERTS
}
ACTION_MIXTURES["balanced"] = {
    expert: 1.0 / len(EXPERTS)
    for expert in EXPERTS
}
SEEDS = (11, 29, 47)
EPISODES = 4
LEARNING_RATE = 0.06
DISCOUNT = 0.85
EPSILON_START = 0.30
EPSILON_END = 0.02
RISK_AVERSION = 0.10
FEATURE_ABS_LIMIT = 20.0
RIDGE_PENALTY = 1e-3
MIN_SPLIT_OBSERVATIONS = 24
BASE_STATE_COLUMNS = (
    "volume_regime",
    "market_return_5",
    "market_volatility_20",
    "candidate_trailing_reward_10",
    "activity_trailing_reward_10",
    "intraday_trailing_reward_10",
    "reversal_trailing_reward_10",
)


class PolicyFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Rollout:
    simulation: Simulation
    actions: pd.Series
    rewards: pd.Series


@dataclass(frozen=True)
class TrainedPolicy:
    weights: np.ndarray
    history: list[dict[str, object]]


def build_action_targets(
    factor_panels: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    if set(factor_panels) != set(EXPERTS):
        raise PolicyFailure(
            "policy.factors",
            "Factor panels must exactly match the fixed expert set",
        )
    targets: dict[str, pd.DataFrame] = {}
    for action, mixture in ACTION_MIXTURES.items():
        combined = sum(
            factor_panels[expert] * weight
            for expert, weight in mixture.items()
        )
        targets[action] = construct_signal_policy(
            combined,
            closes,
        ).targets
    return targets


def build_raw_states(
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    action_targets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    close_returns = closes.pct_change(fill_method=None)
    market_return = close_returns.mean(axis=1)
    log_volume = np.log(volumes)
    market_log_volume = log_volume.mean(axis=1)
    volume_regime = (
        market_log_volume
        - market_log_volume.expanding(min_periods=20).mean()
    )
    state = pd.DataFrame(
        {
            "volume_regime": volume_regime,
            "market_return_5": market_return.rolling(5, min_periods=5).mean(),
            "market_volatility_20": market_return.rolling(
                20,
                min_periods=20,
            ).std(ddof=0),
        }
    )
    for expert in EXPERTS:
        targets = action_targets[expert]
        gross = (
            targets
            * (closes.shift(-1) / closes - 1.0)
        ).sum(axis=1)
        state[f"{expert}_trailing_reward_10"] = (
            gross.shift(1).rolling(10, min_periods=10).mean()
        )
    state = state.replace([np.inf, -np.inf], np.nan)
    return state


def state_with_previous_action(
    raw_state: pd.Series,
    previous_action: str,
) -> dict[str, float]:
    if previous_action not in ACTIONS:
        raise PolicyFailure("policy.action", "Unknown previous action")
    result = {
        key: float(raw_state[key])
        for key in BASE_STATE_COLUMNS
    }
    result.update(
        {
            f"previous_{action}": float(action == previous_action)
            for action in ACTIONS
        }
    )
    if not all(math.isfinite(value) for value in result.values()):
        raise PolicyFailure("policy.state", "Causal state contains non-finite values")
    return result


def _account_step(
    previous_weights: pd.Series,
    proposed: pd.Series,
    close_return: pd.Series,
    forward_return: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    *,
    first: bool,
) -> tuple[pd.Series, pd.Series, pd.Series, dict[str, float | bool]]:
    pretrade = (
        pd.Series(0.0, index=proposed.index, dtype=float)
        if first
        else drift_weights(previous_weights, close_return)
    )
    proposed_delta = proposed - pretrade
    proposed_one_way = 0.5 * float(proposed_delta.abs().sum())
    rebalanced = proposed_one_way + 1e-12 >= NO_TRADE_ONE_WAY
    current = proposed if rebalanced else pretrade
    trade = current - pretrade
    traded_notional = float(trade.abs().sum())
    one_way_turnover = 0.5 * traded_notional
    cost = traded_notional * BASE_COST_BPS / 10_000.0
    gross_return = float((current * forward_return).sum())
    net_return = gross_return - cost
    reward = net_return - RISK_AVERSION * gross_return**2
    benchmark_return = float(forward_return.mean())
    dollar_volume = close * volume
    participation = (
        trade.abs() * REFERENCE_NAV / dollar_volume.replace(0.0, np.nan)
    ).fillna(0.0)
    row: dict[str, float | bool] = {
        "gross_return": gross_return,
        "net_return": net_return,
        "benchmark_return": benchmark_return,
        "reward": reward,
        "one_way_turnover": one_way_turnover,
        "traded_notional": traded_notional,
        "cost": cost,
        "gross_exposure": float(current.abs().sum()),
        "net_exposure": float(current.sum()),
        "max_abs_weight": float(current.abs().max()),
        "concentration_hhi": float(current.pow(2).sum()),
        "rebalanced": rebalanced,
        "max_participation": float(participation.max()),
        "mean_participation": float(participation.mean()),
    }
    numeric = [
        float(value)
        for value in row.values()
        if not isinstance(value, bool)
    ]
    if not all(math.isfinite(value) for value in numeric):
        raise PolicyFailure(
            "policy.non-finite",
            "Environment accounting produced non-finite evidence",
        )
    return current, trade, participation, row


def rollout_policy(
    selector: Callable[[dict[str, float]], str],
    raw_states: pd.DataFrame,
    action_targets: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    index: pd.Index,
) -> Rollout:
    if len(index) < MIN_SPLIT_OBSERVATIONS:
        raise PolicyFailure(
            "policy.population",
            "Policy rollout split is too short",
        )
    close_returns = closes.pct_change(fill_method=None)
    forward_returns = closes.shift(-1) / closes - 1.0
    previous_weights = pd.Series(0.0, index=closes.columns, dtype=float)
    previous_action = "balanced"
    daily_rows: list[dict[str, float | bool]] = []
    weight_rows: list[pd.Series] = []
    trade_rows: list[pd.Series] = []
    participation_rows: list[pd.Series] = []
    actions: list[str] = []
    for position, timestamp in enumerate(index):
        state = state_with_previous_action(
            raw_states.loc[timestamp],
            previous_action,
        )
        action = selector(state)
        if action not in ACTIONS:
            raise PolicyFailure(
                "policy.action",
                f"Policy selected unknown action: {action}",
            )
        current, trade, participation, row = _account_step(
            previous_weights,
            action_targets[action].loc[timestamp],
            close_returns.loc[timestamp].fillna(0.0),
            forward_returns.loc[timestamp].fillna(0.0),
            closes.loc[timestamp],
            volumes.loc[timestamp],
            first=position == 0,
        )
        daily_rows.append(row)
        weight_rows.append(current)
        trade_rows.append(trade)
        participation_rows.append(participation)
        actions.append(action)
        previous_weights = current
        previous_action = action
    simulation = Simulation(
        daily=pd.DataFrame(daily_rows, index=index),
        weights=pd.DataFrame(weight_rows, index=index),
        trades=pd.DataFrame(trade_rows, index=index),
        participation=pd.DataFrame(participation_rows, index=index),
    )
    return Rollout(
        simulation=simulation,
        actions=pd.Series(actions, index=index, name="action"),
        rewards=simulation.daily["reward"].copy(),
    )


def train_q_policy(
    encoder: Callable[[dict[str, float]], np.ndarray],
    feature_count: int,
    raw_states: pd.DataFrame,
    action_targets: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    train_index: pd.Index,
    *,
    seed: int,
) -> TrainedPolicy:
    if seed not in SEEDS:
        raise PolicyFailure("policy.seed", "Seed is outside the fixed set")
    rng = np.random.default_rng(seed)
    weights = rng.normal(0.0, 1e-5, size=(len(ACTIONS), feature_count))
    close_returns = closes.pct_change(fill_method=None)
    forward_returns = closes.shift(-1) / closes - 1.0
    history: list[dict[str, object]] = []
    for episode in range(EPISODES):
        fraction = episode / max(1, EPISODES - 1)
        epsilon = EPSILON_START + fraction * (EPSILON_END - EPSILON_START)
        previous_weights = pd.Series(0.0, index=closes.columns, dtype=float)
        previous_action = "balanced"
        total_reward = 0.0
        action_counts = {action: 0 for action in ACTIONS}
        for position, timestamp in enumerate(train_index):
            state = state_with_previous_action(
                raw_states.loc[timestamp],
                previous_action,
            )
            encoded = encoder(state)
            q_values = weights @ encoded
            if rng.random() < epsilon:
                action_number = int(rng.integers(0, len(ACTIONS)))
            else:
                action_number = int(np.argmax(q_values))
            action = ACTIONS[action_number]
            current, _, _, row = _account_step(
                previous_weights,
                action_targets[action].loc[timestamp],
                close_returns.loc[timestamp].fillna(0.0),
                forward_returns.loc[timestamp].fillna(0.0),
                closes.loc[timestamp],
                volumes.loc[timestamp],
                first=position == 0,
            )
            reward = float(row["reward"])
            done = position == len(train_index) - 1
            if done:
                target = reward
            else:
                next_timestamp = train_index[position + 1]
                next_state = state_with_previous_action(
                    raw_states.loc[next_timestamp],
                    action,
                )
                next_encoded = encoder(next_state)
                target = reward + DISCOUNT * float(
                    np.max(weights @ next_encoded)
                )
            error = float(np.clip(target - q_values[action_number], -0.10, 0.10))
            weights[action_number] += LEARNING_RATE * error * encoded
            if not np.isfinite(weights).all():
                raise PolicyFailure(
                    "policy.non-finite",
                    f"Seed {seed} produced non-finite Q weights",
                )
            total_reward += reward
            action_counts[action] += 1
            previous_weights = current
            previous_action = action
        history.append(
            {
                "episode": episode + 1,
                "epsilon": float(epsilon),
                "totalReward": total_reward,
                "meanReward": total_reward / len(train_index),
                "actionCounts": action_counts,
            }
        )
    return TrainedPolicy(weights=weights, history=history)


def q_selector(
    weights: np.ndarray,
    encoder: Callable[[dict[str, float]], np.ndarray],
) -> Callable[[dict[str, float]], str]:
    def select(state: dict[str, float]) -> str:
        return ACTIONS[int(np.argmax(weights @ encoder(state)))]

    return select


def fixed_selector(action: str) -> Callable[[dict[str, float]], str]:
    if action not in ACTIONS:
        raise PolicyFailure("policy.action", "Unknown fixed action")
    return lambda _: action


def train_contextual_ridge(
    raw_states: pd.DataFrame,
    action_targets: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    train_index: pd.Index,
) -> dict[str, object]:
    raw = raw_states.loc[train_index, list(BASE_STATE_COLUMNS)]
    mean = raw.mean()
    scale = raw.std(ddof=0).replace(0.0, 1.0)
    normalized = (raw - mean) / scale
    design = np.column_stack(
        [np.ones(len(normalized)), normalized.to_numpy(dtype=float)]
    )
    coefficients: list[list[float]] = []
    gram = design.T @ design + RIDGE_PENALTY * np.eye(design.shape[1])
    for action in ACTIONS:
        rollout = rollout_policy(
            fixed_selector(action),
            raw_states,
            action_targets,
            closes,
            volumes,
            train_index,
        )
        target = rollout.rewards.to_numpy(dtype=float)
        coefficients.append(
            np.linalg.solve(gram, design.T @ target).tolist()
        )
    return {
        "columns": list(BASE_STATE_COLUMNS),
        "mean": mean.to_dict(),
        "scale": scale.to_dict(),
        "coefficients": coefficients,
    }


def ridge_selector(model: dict[str, object]) -> Callable[[dict[str, float]], str]:
    columns = list(model["columns"])
    mean = dict(model["mean"])
    scale = dict(model["scale"])
    coefficients = np.asarray(model["coefficients"], dtype=float)

    def select(state: dict[str, float]) -> str:
        values = np.asarray(
            [
                (state[column] - float(mean[column])) / float(scale[column])
                for column in columns
            ],
            dtype=float,
        )
        encoded = np.concatenate(([1.0], values))
        return ACTIONS[int(np.argmax(coefficients @ encoded))]

    return select


def chronological_folds(index: pd.Index) -> dict[str, dict[str, pd.Index]]:
    count = len(index)
    boundaries = {
        "fold-1": (int(count * 0.50), int(count * 0.65), int(count * 0.80)),
        "fold-2": (int(count * 0.65), int(count * 0.80), count),
    }
    folds: dict[str, dict[str, pd.Index]] = {}
    for name, (train_end, validation_end, test_end) in boundaries.items():
        split = {
            "train": index[:train_end],
            "validation": index[train_end:validation_end],
            "test": index[validation_end:test_end],
        }
        if any(len(values) < MIN_SPLIT_OBSERVATIONS for values in split.values()):
            raise PolicyFailure(
                "policy.population",
                f"{name} contains a split shorter than {MIN_SPLIT_OBSERVATIONS}",
            )
        folds[name] = split
    return folds


def rollout_metrics(rollout: Rollout) -> dict[str, object]:
    index = rollout.simulation.daily.index
    action_frequency = {
        action: float((rollout.actions == action).mean())
        for action in ACTIONS
    }
    result = {
        "net": performance_metrics(
            rollout.simulation.daily["net_return"],
            rollout.simulation.daily["benchmark_return"],
        ),
        "gross": performance_metrics(
            rollout.simulation.daily["gross_return"],
            rollout.simulation.daily["benchmark_return"],
        ),
        "implementation": implementation_metrics(
            rollout.simulation,
            index,
        ),
        "cumulative_reward": float(rollout.rewards.sum()),
        "mean_reward": float(rollout.rewards.mean()),
        "action_frequency": action_frequency,
    }
    return result
