"""
run.py — READ-ONLY to research agents. The Harness oracle.

For each compatible strategy in `user_data/strategies/`, runs FreqTrade's Backtesting
in-process across one or more timeranges and pair baskets, computes per-pair
metrics + portfolio aggregate + buy-and-hold benchmark + multi-objective
flags, and prints the result blocks to stdout.

The asset universe and local data directory come from ``harness.json``.  The
default ``crypto-majors`` profile preserves the v0.4.1 contract; alternate
profiles can use an offline, session-aware market facade without turning a
Broker account into part of the research Harness.

Per-strategy class attributes:

- `asset_classes`: optional list of compatible asset classes. A strategy with
  `["crypto"]` is skipped, rather than misapplied, under an equity profile.

- `asset_profiles`: optional tighter allow-list of profile ids.

- `pair_basket`: list of pairs the strategy wants to trade. If unset, defaults
  to the full whitelist (BTC/ETH/SOL/BNB/AVAX). Strategy is only evaluated
  on its declared basket. This lets strategies opt into asset-specific
  universes (e.g., trend-only-on-alts, MR-only-on-BNB) instead of being
  forced through every pair in the whitelist.

- `test_timeranges`: list of `(label, "YYYYMMDD-YYYYMMDD")` tuples. If unset,
  defaults to a single backtest over the full v0.4.0 timerange. Each
  declared timerange produces its own `---` block in the output, plus the
  strategy gets a final summary block with `robust_sharpe` (= min sharpe
  across all declared timeranges).

Multi-objective oracle (new in v0.4.1):

- `profit_floor`: each timerange backtest's profit must clear a configurable
  floor (default 20% absolute) — flagged in summary.
- `avg_position_pct`: capital utilization, reported per-timerange as CONTEXT
  (not pass/fail). An advisory `NOTE tiny-stakes watch` is printed only when a
  keepable Sharpe coincides with thin participation AND thin profit — the actual
  v0.4.0 "Sharpe-via-tiny-stakes" degeneracy signature. Small positions alone
  never trigger it; there is no universal "correct" position size to gate on.
- `pareto_dominated_by`: cross-checks the strategy's robust metrics against
  prior commits' KEEP / EVOLVE rows in `results.tsv` for Pareto dominance.

Buy-and-hold benchmark: each timerange's `---` block reports the
equal-weight buy-and-hold portfolio return + Sharpe + DD computed from
1d feathers, so the agent can compare strategy edge to "doing nothing".

Usage:
    uv run run.py > run.log 2>&1
    uv run run.py --profile us-equities > run.log 2>&1
    uv run run.py --list-profiles
    grep "^---\\|^strategy:\\|^sharpe:\\|^trade_count:" run.log  # compact scan
    awk '/^---$/,/^$/' run.log                                   # full blocks
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode, TradingMode

from autoquant.data import (
    DataValidationError,
    candle_filename,
    inspect_profile_data,
    normalize_ohlcv,
)
from autoquant.freqtrade_adapter import build_backtester
from autoquant.metrics import normalize_session_risk_metrics
from autoquant.profiles import AssetProfile, ManifestError, load_manifest

# ---------------------------------------------------------------------------
# Fixed Harness paths and research gates. Do not modify from a Study.
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).parent.resolve()
USER_DATA = PROJECT_DIR / "user_data"
STRATEGIES_DIR = USER_DATA / "strategies"
CONFIG = PROJECT_DIR / "config.json"
MANIFEST = PROJECT_DIR / "harness.json"

# Multi-objective gates (v0.4.1)
PROFIT_FLOOR_PCT = 20.0   # each timerange must show at least +20% portfolio profit

# Tiny-stakes reminder (advisory — NOT a hard gate). v0.4.0 surfaced a
# degeneracy where shrinking per-trade stake monotonically inflates Sharpe while
# profit collapses (the portfolio stops participating). There is no universal
# "correct" position size, so we do NOT pass/fail on it. Instead we print an
# advisory NOTE only when the actual degeneracy signature is present: a Sharpe
# that looks keepable, coinciding with thin participation AND thin profit. Small
# positions alone never trigger it (a selective strategy with healthy profit is
# fine). These thresholds gate the *message*, not the strategy — tune freely.
TINY_STAKES_POS_PCT = 10.0     # min avg position notably below the ~20% equal-weight baseline
TINY_STAKES_SHARPE = 0.3       # robust_sharpe the agent might keep on (matches program.md soft bar)

# ---------------------------------------------------------------------------
# Strategy module loading + class-attr introspection
# ---------------------------------------------------------------------------
class IncompatibleStrategy(ValueError):
    """A strategy explicitly excludes the selected asset profile."""


def discover_strategies() -> list[str]:
    if not STRATEGIES_DIR.exists():
        return []
    names = []
    for path in sorted(STRATEGIES_DIR.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        names.append(path.stem)
    return names


def load_strategy_class(name: str):
    """Load the strategy class from its module file via importlib.

    We need this BEFORE invoking Backtesting so we can read class attributes
    (`pair_basket`, `test_timeranges`) and override the FreqTrade config
    per-strategy. FreqTrade's own StrategyResolver loads it again later;
    that's fine — Python caches the module.
    """
    path = STRATEGIES_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, name, None)
    if cls is None:
        raise AttributeError(
            f"file {path} does not define a class named {name} "
            "(class name must match filename stem)"
        )
    return cls


def get_strategy_overrides(
    name: str,
    profile: AssetProfile,
) -> tuple[list[str] | None, list[tuple[str, str]]]:
    """Return (pair_basket, test_timeranges) declared by the strategy class.

    Defaults: full whitelist + single full-timerange.
    """
    cls = load_strategy_class(name)
    asset_classes = getattr(cls, "asset_classes", None)
    asset_profiles = getattr(cls, "asset_profiles", None)
    if asset_classes is not None and profile.asset_class not in asset_classes:
        raise IncompatibleStrategy(
            f"{name} supports asset_classes={list(asset_classes)!r}, "
            f"not {profile.asset_class!r}"
        )
    if asset_profiles is not None and profile.id not in asset_profiles:
        raise IncompatibleStrategy(
            f"{name} supports asset_profiles={list(asset_profiles)!r}, "
            f"not {profile.id!r}"
        )

    pair_basket = getattr(cls, "pair_basket", None)
    test_timeranges = getattr(cls, "test_timeranges", None) or [("full", profile.timerange)]
    # Validate basket
    if pair_basket is not None:
        for p in pair_basket:
            if p not in profile.pairs:
                raise ValueError(
                    f"{name}: pair_basket entry {p!r} not in profile "
                    f"{profile.id!r} universe {list(profile.pairs)}"
                )
    # Validate timeranges
    for label, tr in test_timeranges:
        if "-" not in tr or len(tr) < 11:
            raise ValueError(
                f"{name}: test_timerange {label!r} = {tr!r} is malformed; "
                'expected "YYYYMMDD-YYYYMMDD"'
            )
    return pair_basket, test_timeranges


# ---------------------------------------------------------------------------
# Backtest invocation with overrides
# ---------------------------------------------------------------------------
def run_backtest(
    strategy_name: str,
    timerange: str,
    pair_basket: list[str] | None,
    profile: AssetProfile,
) -> dict[str, Any]:
    data_dir = profile.data_dir(PROJECT_DIR)
    args = {
        "config": [str(CONFIG)],
        "user_data_dir": str(USER_DATA),
        "datadir": str(data_dir),
        "strategy": strategy_name,
        "strategy_path": str(STRATEGIES_DIR),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    config["datadir"] = data_dir
    config["timeframe"] = profile.base_timeframe
    config["timerange"] = timerange
    config["stake_currency"] = profile.stake_currency
    config["fee"] = profile.fee
    config["max_open_trades"] = profile.max_open_trades
    config["trading_mode"] = TradingMode(profile.trading_mode)
    config["exchange"]["name"] = profile.venue
    config["exchange"]["pair_whitelist"] = list(pair_basket or profile.pairs)
    config["exchange"]["pair_blacklist"] = []

    backtester = build_backtester(config, profile)
    try:
        backtester.start()
        results = backtester.results
        normalize_session_risk_metrics(
            results,
            strategy_name,
            profile,
            PROJECT_DIR,
        )
        return results
    finally:
        backtester.exchange.close()
        backtester.cleanup()


# ---------------------------------------------------------------------------
# Metric extraction
# ---------------------------------------------------------------------------
def _get(d: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except (TypeError, ValueError):
                continue
    return default


def _entry_metrics(entry: dict[str, Any]) -> dict[str, float]:
    return {
        "sharpe": _get(entry, "sharpe", "sharpe_ratio"),
        "sortino": _get(entry, "sortino", "sortino_ratio"),
        "calmar": _get(entry, "calmar", "calmar_ratio"),
        "total_profit_pct": _get(entry, "profit_total_pct"),
        "max_drawdown_pct": -abs(_get(entry, "max_drawdown_account")) * 100,
        "trade_count": int(_get(entry, "trades", "total_trades")),
        "win_rate_pct": _get(entry, "winrate") * 100,
        "profit_factor": _get(entry, "profit_factor"),
    }


def extract_metrics(
    results: dict[str, Any],
    strategy_name: str,
    pairs: list[str],
) -> dict[str, Any]:
    strat = results.get("strategy", {}).get(strategy_name, {}) or {}
    per_pair_list = strat.get("results_per_pair", []) or []
    aggregate: dict[str, float] = {}
    per_pair: dict[str, dict[str, float]] = {}
    for entry in per_pair_list:
        key = entry.get("key", "")
        m = _entry_metrics(entry)
        if key == "TOTAL":
            aggregate = m
        elif key:
            per_pair[key] = m
    if not aggregate:
        aggregate = _entry_metrics(strat)
    return {"aggregate": aggregate, "per_pair": per_pair, "pairs": pairs}


# ---------------------------------------------------------------------------
# Buy-and-hold benchmark — equal-weight portfolio over 1d feathers
# ---------------------------------------------------------------------------
def compute_bah_benchmark(
    timerange: str,
    pairs: list[str],
    profile: AssetProfile,
) -> dict[str, Any]:
    """Compute equal-weight BUY-AND-HOLD portfolio metrics over the timerange.

    True buy-and-hold semantics: allocate 1/N of the wallet to each pair at the
    start of the window and then DO NOTHING — weights are allowed to drift as
    prices move (winners grow their share). This is the honest "doing nothing"
    baseline that program.md asks the agent to compare against.

    Implementation: each pair's equity multiple is `close / close[0]` (starts at
    1.0). The portfolio equity curve is the mean of those multiples — i.e. the
    drifting-weight 1/N portfolio. Sharpe / profit / max-DD are derived from that
    portfolio equity curve. Returns NaN-safe defaults on missing data.

    NOTE: a previous version averaged *daily returns* across pairs, which is a
    daily-REBALANCED equal-weight portfolio, NOT buy-and-hold. In divergent-trend
    regimes that understated true BaH by ~1000pp (e.g. bull_2021: +1742% reported
    vs +2748% actual) and was inconsistent with the per-pair `profit_pct` below
    (which has always been true BaH `last/first`). Fixed to be internally
    consistent and to match the "doing nothing" semantic.
    """
    start_str, end_str = timerange.split("-", 1)
    start = pd.Timestamp(start_str, tz="UTC")
    end = pd.Timestamp(end_str, tz="UTC")

    pair_gross: dict[str, pd.Series] = {}  # equity multiple per pair, starts at 1.0
    pair_summary: dict[str, dict[str, float]] = {}
    data_dir = profile.data_dir(PROJECT_DIR)
    for pair in pairs:
        path = data_dir / candle_filename(pair, "1d", profile.data_format)
        if not path.exists():
            continue
        if profile.data_format == "feather":
            df = pd.read_feather(path)
        elif profile.data_format == "parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)
        df = normalize_ohlcv(df, source=str(path))
        df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
        if len(df) < 2:
            continue
        gross = (df["close"] / df["close"].iloc[0])
        gross.index = df["date"]
        pair_gross[pair] = gross
        ret = df["close"].pct_change().fillna(0.0)
        cum = (1.0 + ret).cumprod()
        dd = float((cum / cum.cummax() - 1.0).min() * 100)
        pair_summary[pair] = {
            "profit_pct": float((gross.iloc[-1] - 1.0) * 100),
            "dd_pct": dd,
        }

    if not pair_gross:
        return {
            "sharpe": 0.0,
            "profit_total_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "per_pair": {},
        }

    # True BaH portfolio: equal initial weight, drifting thereafter.
    # Portfolio equity = mean of per-pair equity multiples (each starts at 1.0).
    # A pair that lists after the window start sits as cash (gross=1.0) until it
    # has data — consistent with "allocate the basket at t0 and do nothing".
    gross_df = pd.concat(pair_gross.values(), axis=1).sort_index().ffill().fillna(1.0)
    portfolio_equity = gross_df.mean(axis=1)
    portfolio_daily = portfolio_equity.pct_change().dropna()
    if portfolio_daily.std() > 0:
        sharpe = float(
            portfolio_daily.mean()
            / portfolio_daily.std()
            * math.sqrt(profile.annualization_days)
        )
    else:
        sharpe = 0.0
    total_profit = float((portfolio_equity.iloc[-1] - 1.0) * 100)
    max_dd = float((portfolio_equity / portfolio_equity.cummax() - 1.0).min() * 100)

    return {
        "sharpe": sharpe,
        "profit_total_pct": total_profit,
        "max_drawdown_pct": max_dd,
        "per_pair": pair_summary,
    }


# ---------------------------------------------------------------------------
# Position-size estimation (avg stake fraction across trades)
# ---------------------------------------------------------------------------
def estimate_avg_position_size_pct(results: dict[str, Any], strategy_name: str) -> float | None:
    """Best-effort estimate of one backtest's average stake / wallet fraction.

    Reads the trade list from FreqTrade's results, computes mean
    stake_amount / starting_balance.

    Returns ``None`` (not ``0.0``) when stakes can't be read — no trade list, no
    parseable stakes, or a bad wallet. This is deliberate: a *measurement gap*
    must never masquerade as a genuine "this strategy trades microscopic
    positions" finding (which 0.0 would imply). Callers report None as "n/a".
    """
    strat = results.get("strategy", {}).get(strategy_name, {}) or {}
    starting_balance = float(strat.get("starting_balance") or strat.get("dry_run_wallet") or 10000.0)
    if starting_balance <= 0:
        return None
    trades = strat.get("trades")
    if trades is None:
        trades = strat.get("results")
    if trades is None:
        return None
    stakes = []
    for t in trades:
        s = t.get("stake_amount") if isinstance(t, dict) else None
        if s is None:
            continue
        try:
            stakes.append(float(s))
        except (TypeError, ValueError):
            continue
    if not stakes:
        return None
    return float(np.mean(stakes)) / starting_balance * 100.0


# ---------------------------------------------------------------------------
# Pareto dominance vs prior results.tsv entries
# ---------------------------------------------------------------------------
def load_prior_robust_metrics() -> list[dict[str, Any]]:
    """Read results.tsv and return prior commits' (commit, sharpe, max_dd) rows.

    We use sharpe (already robust_sharpe in v0.4.1 schema) and max_dd from
    the existing 5-column schema. profit isn't stored in tsv so dominance
    here is on (sharpe, max_dd) only — partial Pareto, still useful.
    """
    path = PROJECT_DIR / "results.tsv"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        df = pd.read_csv(path, sep="\t", dtype={"commit": str})
    except Exception:
        return []
    if df.empty:
        return []
    # Skip rows where sharpe / max_dd are dashes or NaN (kill events)
    df = df[df["sharpe"].astype(str).str.strip().ne("-")]
    df = df[df["max_dd"].astype(str).str.strip().ne("-")]
    for _, r in df.iterrows():
        try:
            rows.append({
                "commit": str(r["commit"]),
                "strategy": str(r.get("strategy_name", "")),
                "sharpe": float(r["sharpe"]),
                "max_dd": float(r["max_dd"]),  # already negative-pct
            })
        except (ValueError, KeyError):
            continue
    return rows


def check_pareto_dominance(robust_sharpe: float, max_dd: float) -> str | None:
    """Return commit:strategy of any prior row that dominates (sharpe ≥, dd ≥).

    `max_dd` is stored as a negative percent in tsv (e.g. -8.5 means -8.5%);
    "better dd" = closer to 0 = greater value (since less negative).
    Strict dominance: at least one inequality is strict.
    """
    prior = load_prior_robust_metrics()
    for row in prior:
        if row["sharpe"] >= robust_sharpe and row["max_dd"] >= max_dd:
            if row["sharpe"] > robust_sharpe or row["max_dd"] > max_dd:
                return f"{row['commit']}:{row['strategy']}"
    return None


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------
def get_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_DIR),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def print_block(
    strategy_name: str,
    commit: str,
    profile: AssetProfile,
    harness_version: str,
    timerange_label: str,
    timerange: str,
    pairs: list[str],
    bundle: dict[str, Any],
    bah: dict[str, Any],
) -> None:
    agg = bundle["aggregate"]
    per_pair = bundle["per_pair"]
    print("---")
    print(f"strategy:         {strategy_name}")
    print(f"asset_profile:    {profile.id}")
    print(f"asset_class:      {profile.asset_class}")
    print(f"harness_version:  {harness_version}")
    print(f"timerange_label:  {timerange_label}")
    print(f"timerange:        {timerange}")
    print(f"commit:           {commit}")
    print(f"basket:           {','.join(pairs)}")
    print(f"sharpe:           {agg['sharpe']:.4f}")
    print(f"sortino:          {agg['sortino']:.4f}")
    print(f"calmar:           {agg['calmar']:.4f}")
    print(f"total_profit_pct: {agg['total_profit_pct']:.4f}")
    print(f"max_drawdown_pct: {agg['max_drawdown_pct']:.4f}")
    print(f"trade_count:      {agg['trade_count']}")
    print(f"win_rate_pct:     {agg['win_rate_pct']:.4f}")
    print(f"profit_factor:    {agg['profit_factor']:.4f}")
    print(f"bah_sharpe:       {bah['sharpe']:.4f}")
    print(f"bah_profit_pct:   {bah['profit_total_pct']:.4f}")
    print(f"bah_dd_pct:       {bah['max_drawdown_pct']:.4f}")
    print("per_pair:")
    for pair in pairs:
        m = per_pair.get(pair)
        if m is None:
            print(f"  {pair}: (no data)")
            continue
        bah_p = bah["per_pair"].get(pair, {})
        bah_str = ""
        if bah_p:
            bah_str = f" (bah_profit={bah_p['profit_pct']:.1f} bah_dd={bah_p['dd_pct']:.1f})"
        print(
            f"  {pair}: sharpe={m['sharpe']:.4f} "
            f"trades={m['trade_count']} "
            f"profit_pct={m['total_profit_pct']:.2f} "
            f"dd_pct={m['max_drawdown_pct']:.2f} "
            f"wr={m['win_rate_pct']:.1f} "
            f"pf={m['profit_factor']:.2f}"
            f"{bah_str}"
        )


def print_strategy_summary(
    strategy_name: str,
    commit: str,
    profile: AssetProfile,
    harness_version: str,
    labels: list[str],
    per_timerange_metrics: list[dict[str, Any]],
    positions: list[float | None],
) -> None:
    """Final per-strategy summary block. Headline = robust_sharpe = min over all
    declared timeranges. Reports the profit_floor gate, the pareto check, and
    capital utilization as context (per-timerange), plus an advisory tiny-stakes
    NOTE when the v0.4.0 Sharpe-via-de-risking signature is present."""
    if not per_timerange_metrics:
        return
    sharpes = [m["aggregate"]["sharpe"] for m in per_timerange_metrics]
    profits = [m["aggregate"]["total_profit_pct"] for m in per_timerange_metrics]
    dds = [m["aggregate"]["max_drawdown_pct"] for m in per_timerange_metrics]

    robust_sharpe = min(sharpes) if sharpes else 0.0
    worst_profit = min(profits) if profits else 0.0
    worst_dd = min(dds) if dds else 0.0  # most negative

    profit_floor_pass = all(p >= PROFIT_FLOOR_PCT for p in profits)
    pareto_dom = check_pareto_dominance(robust_sharpe, worst_dd)

    # Capital utilization — reported as CONTEXT, never pass/fail. Aggregate over
    # the timeranges actually measured; keep the per-timerange spread visible so
    # regime-conditional sizing-down (fine in bull, ~0 in winter) isn't hidden.
    measured = [p for p in positions if p is not None]
    avg_pos = float(np.mean(measured)) if measured else None
    min_pos = min(measured) if measured else None

    print("---")
    print(f"strategy:         {strategy_name}")
    print(f"asset_profile:    {profile.id}")
    print(f"asset_class:      {profile.asset_class}")
    print(f"harness_version:  {harness_version}")
    print(f"timerange_label:  SUMMARY")
    print(f"commit:           {commit}")
    print(f"robust_sharpe:    {robust_sharpe:.4f}   # min across declared timeranges")
    print(f"worst_profit_pct: {worst_profit:.4f}")
    print(f"worst_dd_pct:     {worst_dd:.4f}")
    if avg_pos is None:
        print(f"avg_position_pct: n/a   (could not read trade stakes)")
    else:
        per_tr = " ".join(
            f"{lbl}={('%.1f' % p) if p is not None else 'n/a'}"
            for lbl, p in zip(labels, positions)
        )
        print(f"avg_position_pct: {avg_pos:.1f}   (per-tr: {per_tr})")
    print(f"profit_floor:     {'PASS' if profit_floor_pass else 'FAIL'}   "
          f"(threshold ≥ {PROFIT_FLOOR_PCT}% per timerange)")
    if pareto_dom:
        print(f"pareto_dominated_by: {pareto_dom}")
    else:
        print(f"pareto_dominated_by: none (non-dominated)")

    # Advisory tiny-stakes reminder — fires ONLY on the actual degeneracy
    # signature (keepable Sharpe + thin participation + thin profit, all at
    # once). Small positions with healthy profit, or a weak Sharpe that will be
    # killed anyway, stay silent. Not a gate: the agent decides.
    if (
        min_pos is not None
        and min_pos < TINY_STAKES_POS_PCT
        and robust_sharpe > TINY_STAKES_SHARPE
        and worst_profit < PROFIT_FLOOR_PCT
    ):
        print(
            f"NOTE tiny-stakes watch: robust_sharpe {robust_sharpe:.2f} looks keepable "
            f"but min avg position is {min_pos:.1f}% and worst-tr profit {worst_profit:.1f}% "
            f"— confirm this is edge, not Sharpe-via-de-risking (cf. v0.4.0 Pareto-walk)."
        )


def print_error(
    strategy_name: str,
    commit: str,
    profile: AssetProfile,
    harness_version: str,
    timerange_label: str,
    timerange: str,
    err: BaseException,
) -> None:
    print("---")
    print(f"strategy:         {strategy_name}")
    print(f"asset_profile:    {profile.id}")
    print(f"asset_class:      {profile.asset_class}")
    print(f"harness_version:  {harness_version}")
    print(f"timerange_label:  {timerange_label}")
    print(f"timerange:        {timerange}")
    print(f"commit:           {commit}")
    print(f"status:           ERROR")
    print(f"error_type:       {type(err).__name__}")
    print(f"error_msg:        {err}")
    print("traceback:")
    print(traceback.format_exc())


def print_skipped(
    strategy_name: str,
    commit: str,
    profile: AssetProfile,
    harness_version: str,
    reason: str,
) -> None:
    print("---")
    print(f"strategy:         {strategy_name}")
    print(f"asset_profile:    {profile.id}")
    print(f"asset_class:      {profile.asset_class}")
    print(f"harness_version:  {harness_version}")
    print("timerange_label:  SETUP")
    print("timerange:        n/a")
    print(f"commit:           {commit}")
    print("status:           SKIPPED")
    print(f"reason:           {reason}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        help="asset profile id (default: manifest default or AUTOQUANT_PROFILE)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="list configured asset profiles and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = load_manifest(MANIFEST)
        profile = manifest.profile(args.profile)
    except ManifestError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    if args.list_profiles:
        for profile_id, candidate in manifest.profiles.items():
            marker = "*" if profile_id == manifest.default_profile else " "
            print(
                f"{marker} {profile_id}: {candidate.asset_class} @ {candidate.venue}, "
                f"{len(candidate.pairs)} pairs, {candidate.market_clock}"
            )
        return 0

    strategies = discover_strategies()
    if not strategies:
        print(
            f"ERROR: no strategies found in {STRATEGIES_DIR}.\n"
            "Create at least one `.py` file under user_data/strategies/ "
            "(see user_data/strategies/_template.py.example for the skeleton).",
            file=sys.stderr,
        )
        return 2

    try:
        coverage = inspect_profile_data(PROJECT_DIR, profile)
    except (DataValidationError, OSError) as err:
        print(
            f"ERROR: profile {profile.id!r} data is not ready: {err}\n"
            f"Run `uv run prepare.py --profile {profile.id}` first.",
            file=sys.stderr,
        )
        return 2

    commit = get_commit()
    print(f"Discovered {len(strategies)} strategies: {', '.join(strategies)}")
    print(
        f"Harness:     {manifest.harness_id} @ {manifest.harness_version} "
        f"({manifest.engine_name} {manifest.engine_version})"
    )
    print(f"Profile:     {profile.id} ({profile.asset_class}, {profile.market_clock})")
    print(f"Whitelist:   {','.join(profile.pairs)}")
    print(f"Default TR:  {profile.timerange}")
    print(f"Data:        {profile.data_dir(PROJECT_DIR)} ({len(coverage)} files)")
    print()

    n_ok_total = 0
    n_err_total = 0
    n_skipped_total = 0

    for name in strategies:
        try:
            pair_basket, test_timeranges = get_strategy_overrides(name, profile)
        except IncompatibleStrategy as err:
            print_skipped(
                name,
                commit,
                profile,
                manifest.harness_version,
                str(err),
            )
            n_skipped_total += 1
            print()
            continue
        except Exception as err:
            print_error(
                name,
                commit,
                profile,
                manifest.harness_version,
                "SETUP",
                "n/a",
                err,
            )
            n_err_total += 1
            print()
            continue

        active_pairs = list(pair_basket) if pair_basket else list(profile.pairs)
        per_timerange_metrics: list[dict[str, Any]] = []
        per_timerange_labels: list[str] = []
        per_timerange_positions: list[float | None] = []

        for label, timerange in test_timeranges:
            try:
                results = run_backtest(name, timerange, pair_basket, profile)
                bundle = extract_metrics(results, name, active_pairs)
                bah = compute_bah_benchmark(timerange, active_pairs, profile)
                print_block(
                    name,
                    commit,
                    profile,
                    manifest.harness_version,
                    label,
                    timerange,
                    active_pairs,
                    bundle,
                    bah,
                )
                per_timerange_metrics.append(bundle)
                per_timerange_labels.append(label)
                # Measure stake fraction per timerange so regime-conditional
                # sizing-down is visible, not just the first range's number.
                per_timerange_positions.append(estimate_avg_position_size_pct(results, name))
                n_ok_total += 1
            except BaseException as err:
                print_error(
                    name,
                    commit,
                    profile,
                    manifest.harness_version,
                    label,
                    timerange,
                    err,
                )
                n_err_total += 1
            print()

        # Summary block: aggregate across timeranges
        if per_timerange_metrics:
            print_strategy_summary(
                name,
                commit,
                profile,
                manifest.harness_version,
                per_timerange_labels,
                per_timerange_metrics, per_timerange_positions,
            )
            print()

    print(
        f"Done: {n_ok_total} backtests succeeded, {n_err_total} failed, "
        f"{n_skipped_total} skipped."
    )
    return 0 if n_err_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
