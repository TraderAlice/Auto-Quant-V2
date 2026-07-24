# Mechanical signal policy and portfolio attribution

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]],
[[docs/design/factor-diagnostics]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]],
[[docs/design/research-selection-integrity]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the fixed causal path from one candidate factor value to
signal intent, proposed target, executed bar weight, and attributed portfolio
evidence. It makes a research position explainable without granting the
candidate or AutoQuant live-trading authority.

It does not define Broker orders, TPSL, intrabar fills, exchange rules,
available balance, or OpenAlice UTA mutation.

## Dataset-fixed timing

At close `t`, the policy may use factors and OHLCV through `t`. The resulting
executed weight earns only close `t` to close `t + 1` return.

Train/validation/test boundaries are fixed from the dataset timestamp panel,
not from candidate coverage, warm-up length, active targets, or successful
trades. The final signal row of each split is purged so its `t + 1` target
return cannot cross into the next split.

Validation net Sharpe remains the sole promotion objective. Test, attribution,
policy comparison, and robustness fields are visible diagnostics.

## Signal-state machine

For each date, valid factor values become cross-sectional percentile scores on
`[0, 1]` using `(rank - 1) / (count - 1)`. The fixed intent states are `short
(-1)`, `flat (0)`, and `long (+1)`.

Entry thresholds:

- flat enters long at score `>= 0.75`;
- flat enters short at score `<= 0.25`.

Exit thresholds create hysteresis:

- long remains long at score `>= 0.55`, exits below `0.55`, and reverses
  directly to short at `<= 0.25`;
- short remains short at score `<= 0.45`, exits above `0.45`, and reverses
  directly to long at `>= 0.75`.

Missing or insufficient cross-sectional evidence resets intent to flat. Every
asset/date receives one fixed event such as `enter_long`, `hold_short`,
`exit_long`, `reverse_short_to_long`, `stay_flat`, or
`unavailable_reset`.

Hysteresis changes signal intent, while the existing portfolio no-trade band
changes execution. They are separate controls and both remain visible.

## Conviction and target sizing

An active intent receives:

```text
conviction = 2 * abs(percentile_score - 0.5)
risk_strength = conviction / trailing_20_bar_volatility
```

Long and short strengths are independently water-filled into fixed `+0.5` and
`-0.5` budgets under the existing `0.30` absolute asset cap. If either side
lacks sufficient breadth to fund its budget, the proposed portfolio is flat
and the allocation status records the reason.

This is inverse-volatility conviction sizing under diagonal risk assumptions,
not covariance optimization or equal risk contribution. The ledger discloses
each asset's conviction, volatility, raw strength, target weight, and
diagonal-risk-budget share.

## Execution and decision ledger

Before trading at close `t`, the prior executed book is drifted through the
return from `t - 1` to `t`. The fixed portfolio band compares this pre-trade
book with the proposed target:

- rebalance when proposed one-way turnover is at least `0.05`;
- otherwise retain the drifted book.

Each asset/date ledger row contains:

- factor value, percentile, prior/new signal state, and signal event;
- conviction, volatility, risk strength, allocation status, and proposed
  target;
- drifted pre-trade weight, executed weight, trade, target action, execution
  action, and execution reason;
- next-bar asset return, gross contribution, allocated linear cost, and net
  contribution;
- causal market regime and ex-ante component variance contribution/share from
  trailing returns through `t`.

Signal intent can be flat while the execution band retains a small residual
position. Keeping both fields is deliberate: it exposes implementation lag
rather than rewriting history.

## Attribution

For every split, Core/Judge evidence groups the exact ledger by:

- asset;
- signal-intent state;
- causal `up/down × calm/stressed` market regime.

It reports gross, cost, net, and one-way-turnover contribution plus average
absolute executed weight and variance-contribution share. Reconciliation
audits prove, per date:

```text
sum(asset gross contribution) = portfolio gross return
sum(asset allocated cost) = portfolio cost
sum(asset net contribution) = portfolio net return
sum(abs(asset trade)) = portfolio traded notional
sum(component variance share) = 1 when variance is positive
```

Concentration reports maximum absolute net-contribution and trailing
component-variance shares across assets, plus their Herfindahl indices. This
identifies whether aggregate return or ex-ante risk is effectively one-name
research.

## Hysteresis baseline

The Judge also constructs a fixed no-hysteresis diagnostic policy whose exit
thresholds equal its entry thresholds. It reports signal-transition counts,
target turnover, implementation turnover, and validation/test net performance
beside the governed policy.

This comparison does not enter KEEP/REVERT. It shows whether persistence
actually reduces signal churn and whether any reduction survives portfolio
accounting.

## Artifacts

Every successful Portfolio Lab Run publishes:

- `portfolio-report.json`: full policy, performance, attribution, stress,
  constraint, split, and causality evidence;
- `daily-portfolio.csv`: portfolio-level accounting;
- `proposed-target-weights.csv`: exact signal-policy targets;
- `executed-weights.csv`: exact post-band research weights;
- `portfolio-decisions.csv`: the long-form per-asset decision and attribution
  ledger.

The reference Study keeps a 60-second hard Judge timeout for installed-wheel
cold pandas/NumPy startup and the fixed attribution pass. Normal warm Runs are
much faster; this is still a bounded research evaluation, not permission for a
long backtest.

## Invariants

1. Candidate code controls factor values only.
2. Dataset-fixed split boundaries and one-bar purge are candidate-independent.
3. Every asset/date has one explicit signal event and allocation status.
4. Signal hysteresis and portfolio no-trade execution remain separate.
5. Proposed targets obey gross, net, side-budget, and asset-cap rules.
6. Every executed trade and contribution reconciles exactly to portfolio
   accounting.
7. Risk attribution uses only trailing information available at the decision
   close.
8. Validation net Sharpe alone controls promotion.
9. Output is research target-weight evidence with no trading authority.

## Known limits

- The state machine is one fixed reference policy, not a universal strategy
  DSL.
- Diagonal inverse-vol sizing and trailing covariance attribution do not model
  a production optimizer or covariance-estimation uncertainty.
- Linear costs and OHLCV participation remain coarse implementation proxies.
- Stop-loss/take-profit and order execution belong to forward OpenAlice/UTA
  decision and execution layers, not this historical research contract.
