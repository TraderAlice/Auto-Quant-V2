# Causal signal-to-portfolio laboratory

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]],
[[docs/design/study-run-evidence]], [[docs/design/ohlcv-factor-lab]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the first fixed portfolio Judge and reference Project:
causal signal timing, target-weight construction, portfolio accounting,
transaction-cost and capacity proxies, professional metric layers, stress
tests, artifacts, and candidate authority.

It does not own live orders, Broker/UTA state, L2 fills, intrabar TPSL, capital
allocation across OpenAlice users, or a universal portfolio optimizer.

## Candidate and Judge boundary

The Agent edits one ordinary pandas function:

```python
def compute_factor(frame: pandas.DataFrame) -> pandas.Series:
    ...
```

It receives one asset's chronological OHLCV frame and returns an aligned
numeric Series. It may create NaNs during warmup but may not mutate input,
return infinity, change alignment, or depend on future rows. Prefix
re-evaluation at multiple cuts audits causality.

The fixed Judge owns:

- next-bar close-to-close targets and returns;
- cross-sectional rank transformation and trailing volatility scaling;
- long/short budgets, gross/net targets, and per-asset caps;
- no-trade tolerance, drift, turnover, costs, and volume participation;
- chronological splits, benchmark, metrics, stresses, and primary score.

The candidate cannot improve by changing portfolio machinery.

## Timing and target construction

For decision date `t`:

```text
OHLCV known through close t
→ candidate factor(t)
→ cross-sectional centered rank
→ divide by trailing 20-bar realized volatility known at t
→ allocate +0.5 long and -0.5 short
→ cap each absolute target weight at 0.30
→ proposed gross 1.0 / net 0.0 target
→ compare with the prior book drifted through return t
→ retain the drifted book when one-way turnover is below 0.05
→ otherwise rebalance at close t
→ earn close(t)→close(t+1) return
```

This is a `bar-target-weight simulation`. It does not claim a particular
intraday fill, queue priority, spread path, or order type.

The allocator treats positive and negative scores separately. Each side uses
proportional water-filling under its cap. If either side lacks enough valid
cross-sectional breadth to fund the declared budget, the target is flat rather
than silently changing net exposure.

## Drift, turnover, costs, and participation

Before choosing the target at close `t`, the prior target is drifted by the
asset returns realized from `t-1` to `t` and normalized by portfolio gross
return. The trade vector is proposed or retained target minus that drifted
book.

- `one_way_turnover = 0.5 * sum(abs(trade_weight))`;
- `traded_notional = sum(abs(trade_weight))`;
- cost is `traded_notional * one_way_cost_bps / 10_000`;
- participation is absolute trade dollars divided by close times volume under
  a fixed reference NAV.

The factor-of-two distinction is explicit: turnover reports portfolio
replacement fraction, while cost applies to every bought or sold dollar.
OHLCV volume supports only a coarse participation proxy, not a market-impact
or capacity guarantee.

## Evidence layers

### Factor

- coverage;
- chronological rank IC mean, ICIR, hit rate, and observations;
- top-minus-bottom forward-return spread.

### Portfolio and risk

- total return, annualized return and volatility;
- Sharpe, Sortino, maximum drawdown, Calmar;
- 95% expected shortfall and positive-period rate;
- benchmark beta, active annualized return, tracking error, and information
  ratio.

### Implementation

- mean/annualized one-way turnover and traded notional;
- total cost drag and rebalance/no-trade rates;
- average/max gross and net exposure;
- average/max absolute asset weight and concentration HHI;
- mean/max volume participation at the fixed reference NAV.

### Robustness

- chronological 60/20/20 train, validation, and visible diagnostic test splits;
- net results under 0, 10, and 25 basis-point cost assumptions;
- one additional bar of signal delay;
- annualized per-asset gross contribution;
- complete deterministic daily returns and target-weight artifacts.

The primary `validation_net_sharpe` is validation net Sharpe under the base
10 basis-point cost assumption. Test and stress metrics remain mandatory
visible evidence but never enter KEEP/REVERT. Candidate iteration after
inspecting them requires a new external holdout for a fresh production-grade
claim. See [[docs/design/research-selection-integrity]].

## Benchmark

The fixed reference benchmark is equal-weight long-only over assets with valid
next-bar returns. It is not a tradable recommendation. Beta, active return,
tracking error, and information ratio use the exact same chronological dates
as the evaluated portfolio.

## Artifacts

Every successful Run declares:

- `portfolio-report.json`: assumptions, split metrics, stresses, per-asset
  contribution, constraint audit, and causality cuts;
- `daily-portfolio.csv`: gross/net/benchmark returns, turnover, cost,
  exposures, rebalance state, and participation;
- `target-weights.csv`: exact executed per-date asset weights.

RunResult remains the immutable authority for artifact identities.

## Invariants

1. Factor and portfolio values at date `t` use no data after close `t`.
2. Returns credited to a target begin strictly after its decision timestamp.
3. Candidate code never controls targets, costs, benchmark, splits, metrics, or
   score.
4. Long and short budgets, gross/net exposure, and caps are explicit and
   audited.
5. Turnover and cost conventions are reported separately.
6. Aggregate performance retains split, per-asset, implementation, and stress
   evidence.
7. Validation alone owns candidate selection; test is visible diagnostic
   evidence.
8. The simulation emits target weights only and has no trading authority.
9. Routine tests use a small deterministic OHLCV fixture.

## Change checklist

- State decision and return timestamps for every accounting change.
- Prove allocator constraints and drift/turnover/cost identities with focused
  deterministic tests.
- Keep all portfolio mechanics in the fixed Judge closure.
- Update template discovery, Study/Run docs, Studio interpretation, package
  assets, and known-improvement/lookahead tests together.
- Do not add a metric without defining its annualization, sign, benchmark, and
  finite-value behavior.

## Known gaps

- V1 has one fixed dollar-neutral construction, not long-only or configurable
  portfolio families.
- Costs are linear and participation is a proxy; spread, impact, borrow,
  funding, and futures margin are absent.
- Corporate actions, calendar metadata, and production price adjustments
  remain outside the synthetic fixture.
- Parameter-neighborhood and selection-adjusted statistics are not yet
  automated.
