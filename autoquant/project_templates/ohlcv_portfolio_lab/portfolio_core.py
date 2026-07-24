"""Fixed causal target construction and portfolio accounting primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


ANNUAL_PERIODS = 252
VOLATILITY_WINDOW = 20
GROSS_TARGET = 1.0
SIDE_BUDGET = GROSS_TARGET / 2.0
MAX_ABS_WEIGHT = 0.30
NO_TRADE_ONE_WAY = 0.05
BASE_COST_BPS = 10.0
REFERENCE_NAV = 1_000_000.0


class PortfolioFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Simulation:
    daily: pd.DataFrame
    weights: pd.DataFrame
    trades: pd.DataFrame
    participation: pd.DataFrame


def _allocate_capped_side(
    strengths: pd.Series,
    *,
    budget: float = SIDE_BUDGET,
    cap: float = MAX_ABS_WEIGHT,
) -> pd.Series:
    """Proportionally water-fill one non-negative side under a hard cap."""

    clean = strengths.astype(float)
    clean = clean[np.isfinite(clean.to_numpy()) & (clean > 0)]
    output = pd.Series(0.0, index=strengths.index, dtype=float)
    if clean.empty or len(clean) * cap + 1e-12 < budget:
        return output
    remaining = list(clean.index)
    remaining_budget = float(budget)
    while remaining:
        values = clean.loc[remaining]
        total = float(values.sum())
        if total <= 0:
            return pd.Series(0.0, index=strengths.index, dtype=float)
        proposed = values / total * remaining_budget
        capped = proposed[proposed > cap + 1e-12]
        if capped.empty:
            output.loc[remaining] = proposed
            remaining_budget = 0.0
            break
        for asset in capped.index:
            output.loc[asset] = cap
            remaining.remove(asset)
            remaining_budget -= cap
        if remaining_budget < -1e-10:
            raise PortfolioFailure(
                "portfolio.allocation",
                "Capped side allocation exceeded its budget",
            )
    if abs(float(output.sum()) - budget) > 1e-9:
        return pd.Series(0.0, index=strengths.index, dtype=float)
    return output


def construct_targets(
    factors: pd.DataFrame,
    closes: pd.DataFrame,
    *,
    volatility_window: int = VOLATILITY_WINDOW,
    gross_target: float = GROSS_TARGET,
    max_abs_weight: float = MAX_ABS_WEIGHT,
) -> pd.DataFrame:
    """Map causal factor values to dollar-neutral capped target weights."""

    if not factors.index.equals(closes.index) or list(factors.columns) != list(
        closes.columns
    ):
        raise PortfolioFailure(
            "portfolio.alignment",
            "Factor and close panels must have identical index and columns",
        )
    if (
        volatility_window < 2
        or not 0 < gross_target <= 2
        or not 0 < max_abs_weight <= gross_target / 2
    ):
        raise PortfolioFailure(
            "portfolio.parameters",
            "Invalid fixed target-construction parameters",
        )
    returns = closes.pct_change(fill_method=None)
    volatility = (
        returns.rolling(
            volatility_window,
            min_periods=volatility_window,
        )
        .std(ddof=0)
        .clip(lower=1e-6)
    )
    side_budget = gross_target / 2.0
    targets = pd.DataFrame(0.0, index=factors.index, columns=factors.columns)
    for timestamp in factors.index:
        pair = pd.DataFrame(
            {
                "factor": factors.loc[timestamp],
                "volatility": volatility.loc[timestamp],
            }
        ).dropna()
        if len(pair) < 4 or pair["factor"].nunique() < 2:
            continue
        ranks = pair["factor"].rank(method="average")
        centered = ranks - ranks.mean()
        scaled = centered / pair["volatility"]
        positive = scaled[scaled > 0]
        negative = -scaled[scaled < 0]
        long_weights = _allocate_capped_side(
            positive.reindex(pair.index, fill_value=0.0),
            budget=side_budget,
            cap=max_abs_weight,
        )
        short_weights = _allocate_capped_side(
            negative.reindex(pair.index, fill_value=0.0),
            budget=side_budget,
            cap=max_abs_weight,
        )
        if (
            abs(float(long_weights.sum()) - side_budget) > 1e-9
            or abs(float(short_weights.sum()) - side_budget) > 1e-9
        ):
            continue
        targets.loc[timestamp, pair.index] = long_weights - short_weights
    return targets


def drift_weights(
    previous: pd.Series,
    realized_returns: pd.Series,
) -> pd.Series:
    """Drift prior close targets through the just-realized asset return."""

    aligned_returns = realized_returns.reindex(previous.index).fillna(0.0).astype(float)
    gross_return = float((previous * aligned_returns).sum())
    denominator = 1.0 + gross_return
    if not math.isfinite(denominator) or denominator <= 1e-9:
        raise PortfolioFailure(
            "portfolio.bankrupt",
            "Portfolio drift denominator is non-positive",
        )
    drifted = previous * (1.0 + aligned_returns) / denominator
    if not np.isfinite(drifted.to_numpy()).all():
        raise PortfolioFailure("portfolio.non-finite", "Drift produced non-finite weights")
    return drifted


def simulate_targets(
    targets: pd.DataFrame,
    closes: pd.DataFrame,
    volumes: pd.DataFrame,
    *,
    cost_bps: float = BASE_COST_BPS,
    no_trade_one_way: float = NO_TRADE_ONE_WAY,
    reference_nav: float = REFERENCE_NAV,
    extra_delay: int = 0,
) -> Simulation:
    """Execute close targets, then credit only the following close return."""

    if (
        not targets.index.equals(closes.index)
        or not targets.index.equals(volumes.index)
        or list(targets.columns) != list(closes.columns)
        or list(targets.columns) != list(volumes.columns)
    ):
        raise PortfolioFailure(
            "portfolio.alignment",
            "Targets, closes, and volumes must share one panel shape",
        )
    if cost_bps < 0 or not 0 <= no_trade_one_way <= 1 or reference_nav <= 0:
        raise PortfolioFailure(
            "portfolio.parameters",
            "Invalid accounting parameters",
        )
    if not isinstance(extra_delay, int) or extra_delay < 0:
        raise PortfolioFailure("portfolio.delay", "extra_delay must be non-negative")
    proposed_targets = targets.shift(extra_delay).fillna(0.0)
    close_returns = closes.pct_change(fill_method=None)
    forward_returns = closes.shift(-1) / closes - 1.0
    executed = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    trades = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    participation = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    daily_rows: list[dict[str, float | bool]] = []
    prior = pd.Series(0.0, index=targets.columns, dtype=float)

    for row_number, timestamp in enumerate(targets.index):
        pretrade = (
            pd.Series(0.0, index=targets.columns, dtype=float)
            if row_number == 0
            else drift_weights(prior, close_returns.loc[timestamp])
        )
        proposed = proposed_targets.loc[timestamp].fillna(0.0).astype(float)
        proposed_delta = proposed - pretrade
        proposed_one_way = 0.5 * float(proposed_delta.abs().sum())
        rebalance = proposed_one_way + 1e-12 >= no_trade_one_way
        current = proposed if rebalance else pretrade
        trade = current - pretrade
        traded_notional = float(trade.abs().sum())
        one_way_turnover = 0.5 * traded_notional
        cost = traded_notional * cost_bps / 10_000.0
        next_returns = forward_returns.loc[timestamp].fillna(0.0).astype(float)
        gross_return = float((current * next_returns).sum())
        net_return = gross_return - cost
        benchmark_return = float(next_returns.mean())
        dollar_volume = (
            closes.loc[timestamp].astype(float)
            * volumes.loc[timestamp].astype(float)
        )
        row_participation = (
            trade.abs() * reference_nav / dollar_volume.replace(0.0, np.nan)
        ).fillna(0.0)
        if not all(
            math.isfinite(value)
            for value in (
                gross_return,
                net_return,
                benchmark_return,
                cost,
                one_way_turnover,
                traded_notional,
            )
        ):
            raise PortfolioFailure(
                "portfolio.non-finite",
                "Accounting produced non-finite values",
            )
        executed.loc[timestamp] = current
        trades.loc[timestamp] = trade
        participation.loc[timestamp] = row_participation
        daily_rows.append(
            {
                "gross_return": gross_return,
                "net_return": net_return,
                "benchmark_return": benchmark_return,
                "one_way_turnover": one_way_turnover,
                "traded_notional": traded_notional,
                "cost": cost,
                "gross_exposure": float(current.abs().sum()),
                "net_exposure": float(current.sum()),
                "max_abs_weight": float(current.abs().max()),
                "concentration_hhi": float(current.pow(2).sum()),
                "rebalanced": rebalance,
                "max_participation": float(row_participation.max()),
                "mean_participation": float(row_participation.mean()),
            }
        )
        prior = current
    daily = pd.DataFrame(daily_rows, index=targets.index)
    valid = forward_returns.notna().any(axis=1)
    return Simulation(
        daily=daily.loc[valid].copy(),
        weights=executed.loc[valid].copy(),
        trades=trades.loc[valid].copy(),
        participation=participation.loc[valid].copy(),
    )


def performance_metrics(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    annual_periods: int = ANNUAL_PERIODS,
) -> dict[str, float | int]:
    pair = pd.DataFrame(
        {"returns": returns, "benchmark": benchmark}
    ).dropna()
    if len(pair) < 20:
        raise PortfolioFailure(
            "portfolio.population",
            "Portfolio split has fewer than 20 valid observations",
        )
    values = pair["returns"].astype(float)
    benchmark_values = pair["benchmark"].astype(float)
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    annual_volatility = std * math.sqrt(annual_periods)
    total_growth = float((1.0 + values).prod())
    annual_return = (
        total_growth ** (annual_periods / len(values)) - 1.0
        if total_growth > 0
        else -1.0
    )
    sharpe = mean / std * math.sqrt(annual_periods) if std > 1e-12 else 0.0
    downside = np.minimum(values.to_numpy(dtype=float), 0.0)
    downside_deviation = float(np.sqrt(np.mean(np.square(downside))))
    sortino = (
        mean / downside_deviation * math.sqrt(annual_periods)
        if downside_deviation > 1e-12
        else 0.0
    )
    equity = (1.0 + values).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    maximum_drawdown = float(drawdown.min())
    calmar = (
        annual_return / abs(maximum_drawdown)
        if maximum_drawdown < -1e-12
        else 0.0
    )
    tail_count = max(1, math.ceil(len(values) * 0.05))
    expected_shortfall = -float(values.nsmallest(tail_count).mean())
    benchmark_variance = float(benchmark_values.var(ddof=0))
    beta = (
        float(values.cov(benchmark_values, ddof=0)) / benchmark_variance
        if benchmark_variance > 1e-12
        else 0.0
    )
    active = values - benchmark_values
    tracking_error_daily = float(active.std(ddof=0))
    tracking_error = tracking_error_daily * math.sqrt(annual_periods)
    active_annual_return = float(active.mean()) * annual_periods
    information_ratio = (
        float(active.mean()) / tracking_error_daily * math.sqrt(annual_periods)
        if tracking_error_daily > 1e-12
        else 0.0
    )
    result: dict[str, float | int] = {
        "observations": int(len(values)),
        "total_return": total_growth - 1.0,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "maximum_drawdown": maximum_drawdown,
        "calmar": calmar,
        "expected_shortfall_95": expected_shortfall,
        "positive_rate": float((values > 0).mean()),
        "benchmark_beta": beta,
        "active_annual_return": active_annual_return,
        "tracking_error": tracking_error,
        "information_ratio": information_ratio,
    }
    if not all(
        math.isfinite(float(value))
        for value in result.values()
    ):
        raise PortfolioFailure(
            "portfolio.non-finite",
            "Performance metrics contain non-finite values",
        )
    return result


def implementation_metrics(
    simulation: Simulation,
    index: pd.Index,
    *,
    annual_periods: int = ANNUAL_PERIODS,
) -> dict[str, float]:
    daily = simulation.daily.loc[index]
    weights = simulation.weights.loc[index]
    result = {
        "mean_one_way_turnover": float(daily["one_way_turnover"].mean()),
        "annualized_one_way_turnover": float(
            daily["one_way_turnover"].mean() * annual_periods
        ),
        "mean_traded_notional": float(daily["traded_notional"].mean()),
        "total_cost_drag": float(daily["cost"].sum()),
        "rebalance_rate": float(daily["rebalanced"].mean()),
        "no_trade_rate": float((~daily["rebalanced"]).mean()),
        "average_gross_exposure": float(daily["gross_exposure"].mean()),
        "maximum_gross_exposure": float(daily["gross_exposure"].max()),
        "average_abs_net_exposure": float(daily["net_exposure"].abs().mean()),
        "maximum_abs_net_exposure": float(daily["net_exposure"].abs().max()),
        "average_max_abs_weight": float(daily["max_abs_weight"].mean()),
        "maximum_abs_weight": float(weights.abs().max().max()),
        "average_concentration_hhi": float(daily["concentration_hhi"].mean()),
        "mean_volume_participation": float(daily["mean_participation"].mean()),
        "maximum_volume_participation": float(daily["max_participation"].max()),
    }
    if not all(math.isfinite(value) for value in result.values()):
        raise PortfolioFailure(
            "portfolio.non-finite",
            "Implementation metrics contain non-finite values",
        )
    return result


def constraint_audit(
    targets: pd.DataFrame,
    *,
    gross_target: float = GROSS_TARGET,
    max_abs_weight: float = MAX_ABS_WEIGHT,
) -> dict[str, float | int | bool]:
    active = targets[targets.abs().sum(axis=1) > 1e-12]
    if active.empty:
        raise PortfolioFailure("portfolio.no-targets", "No active targets were constructed")
    gross_error = float((active.abs().sum(axis=1) - gross_target).abs().max())
    net_error = float(active.sum(axis=1).abs().max())
    maximum_weight = float(active.abs().max().max())
    passed = (
        gross_error <= 1e-8
        and net_error <= 1e-8
        and maximum_weight <= max_abs_weight + 1e-8
    )
    return {
        "passed": passed,
        "active_dates": int(len(active)),
        "maximum_gross_error": gross_error,
        "maximum_abs_net_target": net_error,
        "maximum_abs_target_weight": maximum_weight,
    }
