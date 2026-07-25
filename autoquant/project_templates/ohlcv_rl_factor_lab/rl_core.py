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
        RiskCovarianceCache,
        Simulation,
        build_risk_covariance_cache,
        construct_signal_policy,
        drift_weights,
        execution_risk_metrics,
        execute_risk_compliant_book,
        implementation_metrics,
        performance_metrics,
    )
except ModuleNotFoundError:  # Package-level deterministic primitive tests.
    from autoquant.project_templates.ohlcv_portfolio_lab.portfolio_core import (
        BASE_COST_BPS,
        NO_TRADE_ONE_WAY,
        REFERENCE_NAV,
        RiskCovarianceCache,
        Simulation,
        build_risk_covariance_cache,
        construct_signal_policy,
        drift_weights,
        execution_risk_metrics,
        execute_risk_compliant_book,
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
EPISODES = 12
LEARNING_RATE = 0.02
DISCOUNT = 0.30
EPSILON_START = 0.15
EPSILON_END = 0.01
RISK_AVERSION = 0.10
FEATURE_ABS_LIMIT = 20.0
RIDGE_PENALTY = 1e-3
CONTEXTUAL_RIDGE_ITERATIONS = 4
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
PRETRADE_STATE_COLUMNS = (
    "pretrade_gross_exposure",
    "pretrade_net_exposure",
    "pretrade_cash_weight",
    "pretrade_max_abs_weight",
    "pretrade_concentration_hhi",
)
ACTION_DISTANCE_COLUMNS = tuple(
    f"{action}_target_distance"
    for action in ACTIONS
)
PREVIOUS_ACTION_COLUMNS = tuple(
    f"previous_{action}"
    for action in ACTIONS
)
POLICY_STATE_COLUMNS = (
    BASE_STATE_COLUMNS
    + PRETRADE_STATE_COLUMNS
    + ACTION_DISTANCE_COLUMNS
    + PREVIOUS_ACTION_COLUMNS
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
    states: pd.DataFrame


@dataclass(frozen=True)
class TrainedPolicy:
    weights: np.ndarray
    history: list[dict[str, object]]


def build_action_targets(
    factor_panels: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
    *,
    mandate: dict[str, object] | None = None,
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
            mandate=mandate,
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


def build_policy_state(
    raw_state: pd.Series,
    previous_action: str,
    pretrade_weights: pd.Series,
    action_targets: dict[str, pd.Series],
) -> dict[str, float]:
    """Build one causal market-and-execution state at the decision close."""

    if set(action_targets) != set(ACTIONS):
        raise PolicyFailure(
            "policy.state-actions",
            "Policy state action targets differ from the fixed action set",
        )
    if (
        pretrade_weights.index.has_duplicates
        or any(
            not target.index.equals(pretrade_weights.index)
            for target in action_targets.values()
        )
    ):
        raise PolicyFailure(
            "policy.state-assets",
            "Policy state books do not share one ordered asset universe",
        )
    result = state_with_previous_action(raw_state, previous_action)
    result.update(
        {
            "pretrade_gross_exposure": float(
                pretrade_weights.abs().sum()
            ),
            "pretrade_net_exposure": float(pretrade_weights.sum()),
            "pretrade_cash_weight": (
                1.0 - float(pretrade_weights.abs().sum())
            ),
            "pretrade_max_abs_weight": float(
                pretrade_weights.abs().max()
            ),
            "pretrade_concentration_hhi": float(
                pretrade_weights.pow(2).sum()
            ),
        }
    )
    result.update(
        {
            f"{action}_target_distance": float(
                0.5
                * (
                    action_targets[action] - pretrade_weights
                ).abs().sum()
            )
            for action in ACTIONS
        }
    )
    if set(result) != set(POLICY_STATE_COLUMNS):
        raise PolicyFailure(
            "policy.state-fields",
            "Policy state fields differ from the fixed causal contract",
        )
    if not all(math.isfinite(value) for value in result.values()):
        raise PolicyFailure(
            "policy.state",
            "Causal policy state contains non-finite values",
        )
    return result


def _pretrade_weights(
    previous_weights: pd.Series,
    close_returns: pd.DataFrame,
    timestamp: object,
    *,
    first: bool,
) -> pd.Series:
    return (
        pd.Series(
            0.0,
            index=previous_weights.index,
            dtype=float,
        )
        if first
        else drift_weights(previous_weights, close_returns.loc[timestamp])
    )


def _account_step(
    previous_weights: pd.Series,
    proposed: pd.Series,
    close_returns: pd.DataFrame,
    timestamp: object,
    forward_return: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    *,
    first: bool,
    mandate: dict[str, object] | None = None,
    risk_covariance_cache: RiskCovarianceCache | None = None,
) -> tuple[pd.Series, pd.Series, pd.Series, dict[str, float | bool]]:
    pretrade = _pretrade_weights(
        previous_weights,
        close_returns,
        timestamp,
        first=first,
    )
    current, execution_risk = execute_risk_compliant_book(
        pretrade,
        proposed,
        close_returns,
        timestamp,
        mandate=mandate,
        no_trade_one_way=NO_TRADE_ONE_WAY,
        risk_covariance_cache=risk_covariance_cache,
    )
    rebalanced = bool(execution_risk["rebalanced"])
    trade = current - pretrade
    traded_notional = float(trade.abs().sum())
    one_way_turnover = 0.5 * traded_notional
    cost = traded_notional * BASE_COST_BPS / 10_000.0
    gross_return = float((current * forward_return).sum())
    net_return = gross_return - cost
    reward = net_return - RISK_AVERSION * gross_return**2
    if mandate is None:
        benchmark_return = float(forward_return.mean())
    else:
        construction = mandate["construction"]
        benchmark = construction["benchmark"]
        tradable = list(mandate["tradableAssets"])
        if benchmark == "cash":
            benchmark_return = 0.0
        elif benchmark == "equal-weight-long-research-universe":
            benchmark_return = float(forward_return.mean())
        elif benchmark == "equal-weight-long-tradable":
            benchmark_return = float(forward_return.loc[tradable].mean())
        elif benchmark == "equal-weight-short-tradable":
            benchmark_return = -float(forward_return.loc[tradable].mean())
        else:
            raise PolicyFailure(
                "mandate.benchmark",
                "Unknown Portfolio Mandate benchmark",
            )
    dollar_volume = close * volume
    participation = (
        trade.abs() * REFERENCE_NAV / dollar_volume.replace(0.0, np.nan)
    ).fillna(0.0)
    row: dict[str, object] = {
        "gross_return": gross_return,
        "net_return": net_return,
        "benchmark_return": benchmark_return,
        "reward": reward,
        "one_way_turnover": one_way_turnover,
        "traded_notional": traded_notional,
        "cost": cost,
        "gross_exposure": float(current.abs().sum()),
        "net_exposure": float(current.sum()),
        "cash_weight": 1.0 - float(current.abs().sum()),
        "max_abs_weight": float(current.abs().max()),
        "concentration_hhi": float(current.pow(2).sum()),
        "rebalanced": rebalanced,
        "execution_reason": str(execution_risk["execution_reason"]),
        "execution_risk_status": str(execution_risk["status"]),
        "execution_risk_forecast_available": bool(
            execution_risk["forecast_available"]
        ),
        "execution_risk_observations": int(
            execution_risk["observations"]
        ),
        "pretrade_risk_forecast_annualized": float(
            execution_risk["pretrade_forecast_annualized"]
        ),
        "proposed_risk_forecast_pre_annualized": float(
            execution_risk["proposed_forecast_pre_annualized"]
        ),
        "proposed_risk_forecast_post_annualized": float(
            execution_risk["proposed_forecast_post_annualized"]
        ),
        "executed_risk_forecast_annualized": float(
            execution_risk["executed_forecast_annualized"]
        ),
        "execution_risk_ceiling_annualized": float(
            execution_risk["annualized_volatility_ceiling"]
        ),
        "proposed_runtime_risk_scale": float(
            execution_risk["proposed_runtime_scale"]
        ),
        "execution_risk_repair_scale": float(
            execution_risk["risk_repair_scale"]
        ),
        "proposed_one_way_turnover": float(
            execution_risk["proposed_one_way"]
        ),
        "ordinary_rebalance": bool(
            execution_risk["ordinary_rebalance"]
        ),
        "risk_rebalance_override": bool(
            execution_risk["risk_rebalance_override"]
        ),
        "max_participation": float(participation.max()),
        "mean_participation": float(participation.mean()),
    }
    numeric = [
        float(value)
        for value in row.values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
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
    *,
    mandate: dict[str, object] | None = None,
    risk_covariance_cache: RiskCovarianceCache | None = None,
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
    daily_rows: list[dict[str, object]] = []
    weight_rows: list[pd.Series] = []
    trade_rows: list[pd.Series] = []
    participation_rows: list[pd.Series] = []
    actions: list[str] = []
    state_rows: list[dict[str, float]] = []
    for position, timestamp in enumerate(index):
        first = position == 0
        pretrade = _pretrade_weights(
            previous_weights,
            close_returns,
            timestamp,
            first=first,
        )
        state = build_policy_state(
            raw_states.loc[timestamp],
            previous_action,
            pretrade,
            {
                action: action_targets[action].loc[timestamp]
                for action in ACTIONS
            },
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
            close_returns,
            timestamp,
            forward_returns.loc[timestamp].fillna(0.0),
            closes.loc[timestamp],
            volumes.loc[timestamp],
            first=first,
            mandate=mandate,
            risk_covariance_cache=risk_covariance_cache,
        )
        daily_rows.append(row)
        weight_rows.append(current)
        trade_rows.append(trade)
        participation_rows.append(participation)
        actions.append(action)
        state_rows.append(state)
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
        states=pd.DataFrame(
            state_rows,
            index=index,
            columns=list(POLICY_STATE_COLUMNS),
        ),
    )


def one_step_action_opportunities(
    rollout: Rollout,
    action_targets: dict[str, pd.DataFrame],
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    index: pd.Index,
    *,
    mandate: dict[str, object] | None = None,
    risk_covariance_cache: RiskCovarianceCache | None = None,
) -> list[dict[str, object]]:
    """Audit every governed action from the actual policy pretrade book."""

    if (
        not rollout.actions.index.equals(index)
        or not rollout.simulation.daily.index.equals(index)
        or not rollout.simulation.weights.index.equals(index)
        or not rollout.simulation.trades.index.equals(index)
        or set(action_targets) != set(ACTIONS)
    ):
        raise PolicyFailure(
            "policy.opportunity-identity",
            "Opportunity audit inputs differ from the selected rollout",
        )
    cache = (
        risk_covariance_cache
        if risk_covariance_cache is not None
        else build_risk_covariance_cache(closes, mandate=mandate)
    )
    close_returns = closes.pct_change(fill_method=None)
    forward_returns = closes.shift(-1) / closes - 1.0
    zero = pd.Series(0.0, index=closes.columns, dtype=float)
    rows: list[dict[str, object]] = []
    for position, timestamp in enumerate(index):
        previous_weights = (
            zero
            if position == 0
            else rollout.simulation.weights.loc[index[position - 1]]
        )
        pretrade = (
            zero.copy()
            if position == 0
            else drift_weights(previous_weights, close_returns.loc[timestamp])
        )
        forward_return = forward_returns.loc[timestamp].fillna(0.0)
        action_evidence: dict[str, dict[str, object]] = {}
        for action in ACTIONS:
            proposed = action_targets[action].loc[timestamp]
            current, trade, _, daily = _account_step(
                previous_weights,
                proposed,
                close_returns,
                timestamp,
                forward_return,
                closes.loc[timestamp],
                volumes.loc[timestamp],
                first=position == 0,
                mandate=mandate,
                risk_covariance_cache=cache,
            )
            action_evidence[action] = {
                "proposedWeights": {
                    asset: float(proposed[asset])
                    for asset in closes.columns
                },
                "executedWeights": {
                    asset: float(current[asset])
                    for asset in closes.columns
                },
                "trades": {
                    asset: float(trade[asset])
                    for asset in closes.columns
                },
                "grossReturn": float(daily["gross_return"]),
                "netReturn": float(daily["net_return"]),
                "reward": float(daily["reward"]),
                "oneWayTurnover": float(daily["one_way_turnover"]),
                "cost": float(daily["cost"]),
                "grossExposure": float(daily["gross_exposure"]),
                "netExposure": float(daily["net_exposure"]),
                "executionRiskStatus": str(
                    daily["execution_risk_status"]
                ),
                "executionRiskForecastAvailable": bool(
                    daily["execution_risk_forecast_available"]
                ),
                "executionRiskObservations": int(
                    daily["execution_risk_observations"]
                ),
                "pretradeRiskForecastAnnualized": float(
                    daily["pretrade_risk_forecast_annualized"]
                ),
                "executedRiskForecastAnnualized": float(
                    daily["executed_risk_forecast_annualized"]
                ),
                "executionRiskCeilingAnnualized": float(
                    daily["execution_risk_ceiling_annualized"]
                ),
                "riskRebalanceOverride": bool(
                    daily["risk_rebalance_override"]
                ),
                "executionReason": str(daily["execution_reason"]),
            }
        selected = str(rollout.actions.loc[timestamp])
        selected_evidence = action_evidence[selected]
        actual_daily = rollout.simulation.daily.loc[timestamp]
        if (
            not np.allclose(
                np.asarray(
                    list(selected_evidence["executedWeights"].values()),
                    dtype=float,
                ),
                rollout.simulation.weights.loc[timestamp].to_numpy(dtype=float),
                rtol=0.0,
                atol=1e-12,
            )
            or not np.allclose(
                np.asarray(
                    list(selected_evidence["trades"].values()),
                    dtype=float,
                ),
                rollout.simulation.trades.loc[timestamp].to_numpy(dtype=float),
                rtol=0.0,
                atol=1e-12,
            )
            or any(
                not math.isclose(
                    float(selected_evidence[artifact_field]),
                    float(actual_daily[daily_field]),
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                for artifact_field, daily_field in (
                    ("grossReturn", "gross_return"),
                    ("netReturn", "net_return"),
                    ("reward", "reward"),
                    ("oneWayTurnover", "one_way_turnover"),
                    ("cost", "cost"),
                )
            )
        ):
            raise PolicyFailure(
                "policy.opportunity-selected",
                "Selected opportunity does not reproduce the actual rollout",
            )
        ranked = sorted(
            ACTIONS,
            key=lambda action: (
                -float(action_evidence[action]["reward"]),
                ACTIONS.index(action),
            ),
        )
        oracle = ranked[0]
        selected_reward = float(selected_evidence["reward"])
        oracle_reward = float(action_evidence[oracle]["reward"])
        regret = oracle_reward - selected_reward
        if regret < -1e-12:
            raise PolicyFailure(
                "policy.opportunity-regret",
                "Selected opportunity regret is negative",
            )
        candidate_reward = float(action_evidence["candidate"]["reward"])
        balanced_reward = float(action_evidence["balanced"]["reward"])
        rows.append(
            {
                "timestamp": timestamp,
                "selectedAction": selected,
                "oracleAction": oracle,
                "selectedRank": ranked.index(selected) + 1,
                "oracleHit": selected == oracle,
                "selectedReward": selected_reward,
                "oracleReward": oracle_reward,
                "realizedRegret": max(0.0, regret),
                "candidateMinusSelectedReward": (
                    candidate_reward - selected_reward
                ),
                "candidateMinusBalancedReward": (
                    candidate_reward - balanced_reward
                ),
                "pretradeWeights": {
                    asset: float(pretrade[asset])
                    for asset in closes.columns
                },
                "forwardReturns": {
                    asset: float(forward_return[asset])
                    for asset in closes.columns
                },
                "actions": action_evidence,
            }
        )
    return rows


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
    mandate: dict[str, object] | None = None,
    risk_covariance_cache: RiskCovarianceCache | None = None,
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
            first = position == 0
            pretrade = _pretrade_weights(
                previous_weights,
                close_returns,
                timestamp,
                first=first,
            )
            state = build_policy_state(
                raw_states.loc[timestamp],
                previous_action,
                pretrade,
                {
                    action: action_targets[action].loc[timestamp]
                    for action in ACTIONS
                },
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
                close_returns,
                timestamp,
                forward_returns.loc[timestamp].fillna(0.0),
                closes.loc[timestamp],
                volumes.loc[timestamp],
                first=first,
                mandate=mandate,
                risk_covariance_cache=risk_covariance_cache,
            )
            reward = float(row["reward"])
            done = position == len(train_index) - 1
            if done:
                target = reward
            else:
                next_timestamp = train_index[position + 1]
                next_pretrade = _pretrade_weights(
                    current,
                    close_returns,
                    next_timestamp,
                    first=False,
                )
                next_state = build_policy_state(
                    raw_states.loc[next_timestamp],
                    action,
                    next_pretrade,
                    {
                        candidate: action_targets[candidate].loc[
                            next_timestamp
                        ]
                        for candidate in ACTIONS
                    },
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
    *,
    mandate: dict[str, object] | None = None,
    risk_covariance_cache: RiskCovarianceCache | None = None,
) -> dict[str, object]:
    """Fit a deterministic train-only same-pretrade contextual comparator."""

    cache = (
        risk_covariance_cache
        if risk_covariance_cache is not None
        else build_risk_covariance_cache(closes, mandate=mandate)
    )
    selector = fixed_selector("balanced")
    history: list[dict[str, object]] = []
    model: dict[str, object] | None = None
    for iteration in range(CONTEXTUAL_RIDGE_ITERATIONS):
        behavior = rollout_policy(
            selector,
            raw_states,
            action_targets,
            closes,
            volumes,
            train_index,
            mandate=mandate,
            risk_covariance_cache=cache,
        )
        opportunities = one_step_action_opportunities(
            behavior,
            action_targets,
            closes,
            volumes,
            train_index,
            mandate=mandate,
            risk_covariance_cache=cache,
        )
        raw = behavior.states.loc[
            train_index,
            list(POLICY_STATE_COLUMNS),
        ]
        mean = raw.mean()
        scale = raw.std(ddof=0).replace(0.0, 1.0)
        normalized = (raw - mean) / scale
        design = np.column_stack(
            [
                np.ones(len(normalized)),
                normalized.to_numpy(dtype=float),
            ]
        )
        gram = (
            design.T @ design
            + RIDGE_PENALTY * np.eye(design.shape[1])
        )
        coefficients: list[list[float]] = []
        for action in ACTIONS:
            target = np.asarray(
                [
                    row["actions"][action]["reward"]
                    for row in opportunities
                ],
                dtype=float,
            )
            coefficients.append(
                np.linalg.solve(gram, design.T @ target).tolist()
            )
        model = {
            "method": (
                "iterative-same-pretrade-contextual-ridge-v1"
            ),
            "labelScope": "train-only",
            "anchorAction": "balanced",
            "iterations": CONTEXTUAL_RIDGE_ITERATIONS,
            "columns": list(POLICY_STATE_COLUMNS),
            "mean": mean.to_dict(),
            "scale": scale.to_dict(),
            "coefficients": coefficients,
        }
        selector = ridge_selector(model)
        improved = rollout_policy(
            selector,
            raw_states,
            action_targets,
            closes,
            volumes,
            train_index,
            mandate=mandate,
            risk_covariance_cache=cache,
        )
        history.append(
            {
                "iteration": iteration + 1,
                "trainingRows": len(opportunities),
                "sharedPretradeActionEvaluations": (
                    len(opportunities) * len(ACTIONS)
                ),
                "behaviorActionFrequency": {
                    action: float(
                        (behavior.actions == action).mean()
                    )
                    for action in ACTIONS
                },
                "improvedActionFrequency": {
                    action: float(
                        (improved.actions == action).mean()
                    )
                    for action in ACTIONS
                },
                "improvedTrainingNetSharpe": float(
                    rollout_metrics(improved)["net"]["sharpe"]
                ),
                "behaviorOracleHitRate": float(
                    np.mean(
                        [
                            row["selectedAction"]
                            == row["oracleAction"]
                            for row in opportunities
                        ]
                    )
                ),
                "behaviorMeanRealizedRegret": float(
                    np.mean(
                        [
                            row["realizedRegret"]
                            for row in opportunities
                        ]
                    )
                ),
            }
        )
    if model is None:
        raise PolicyFailure(
            "policy.ridge",
            "Contextual ridge did not execute its fixed iterations",
        )
    model["history"] = history
    return model


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
        "execution_risk": execution_risk_metrics(
            rollout.simulation,
            index,
        ),
        "cumulative_reward": float(rollout.rewards.sum()),
        "mean_reward": float(rollout.rewards.mean()),
        "action_frequency": action_frequency,
    }
    return result
