# Make signal triggers and position attribution explicit

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/signal-policy-and-attribution]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/factor-diagnostics]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

AutoQuant can explain mechanically how a causal factor becomes each asset's
long, flat, or short state and target weight, then attribute portfolio return,
risk, turnover, and cost back to those decisions for both Agents and humans.

## Context

The existing Portfolio Lab maps cross-sectional ranks into a fixed
dollar-neutral top/bottom book with volatility scaling, caps, drift-aware
turnover, and costs. That proves portfolio accounting, but it still compresses
the central trading question into one function: when exactly did an asset
enter, remain, resize, or exit, and which signal/risk rule caused the change?

The professional Factor diagnostics now establish whether an input signal is
credible. The next boundary should make the factor-to-position policy and its
contribution evidence equally explicit before RL is allowed to choose among
such policies.

## Scope

### In scope

- Fixed signal-state semantics for entry, hold, exit, and reversal with
  hysteresis/no-trade behavior.
- Mechanical conviction and volatility/risk-budget sizing under gross, net,
  per-asset, concentration, and liquidity constraints.
- Timestamped decision reasons and before/target/executed position evidence.
- Return, risk, turnover, and cost attribution by asset, signal state, and
  declared market regime.
- Validation-only comparison, CLI/Studio parity, and bounded deterministic
  regressions.

### Out of scope

- Broker orders, TPSL placement, venue fills, balances, or OpenAlice UTA
  mutation.
- Candidate-controlled constraints, costs, attribution, or acceptance rules.
- A universal optimizer or arbitrary portfolio DSL.

## Acceptance

- [x] Every position change has one fixed causal reason and target calculation.
- [x] Entry/exit hysteresis prevents rank noise from becoming unexplained
      turnover while preserving explicit timing.
- [x] Asset targets reconcile exactly to portfolio constraints, daily returns,
      trades, costs, and attribution totals.
- [x] Risk and contribution concentration are visible by asset/state/regime.
- [x] CLI artifacts and Studio show the same verified decision path.
- [x] Tests prove timing, state transitions, constraint reconciliation,
      attribution identities, isolation, and packaging.

## Work

- [x] Activate after reviewing the completed Factor diagnostics evidence.
- [x] Fix signal-state and risk-budget semantics before implementation.
- [x] Implement decision ledger, attribution, and observation surfaces.
- [x] Complete regression, documentation, and package audits.

## Findings and decisions

- 2026-07-24 — Portfolio target weights are the correct AutoQuant/OpenAlice
  handoff, but a target without a causal state transition and reason ledger is
  too opaque for human/AI collaboration.
- 2026-07-24 — Current Portfolio splits depend on candidate-active dates and do
  not purge the final forward-return row. V1 fixes boundaries from the dataset
  timeline and purges one signal row per split.
- 2026-07-24 — Signal hysteresis and portfolio no-trade execution are distinct:
  one governs intent persistence; the other governs whether a proposed target
  is worth trading after drift.
- 2026-07-24 — The richer warm reference Judge runs in roughly three seconds.
  Its hard timeout is 60 seconds so installed-wheel cold imports and fixed
  attribution do not become false failures; Campaign wall budgets must exceed
  that bound.
- 2026-07-24 — RL factor-mixture actions now resolve to four independently
  stateful governed signal sleeves. RL still chooses only the sleeve; the
  fixed portfolio Core owns thresholds, sizing, constraints, and costs.

## Verification

- `uv run python -m unittest tests.test_portfolio_lab -v` — 11 tests passed.
- `uv run python -m unittest tests.test_rl_factor_policy_lab -v` — 3 tests
  passed.
- `uv run python -m unittest discover -s tests -v` — 92 tests passed.
- `uv run python scripts/check_doc_links.py` — 230 links resolved.
- `uv run python -m compileall -q autoquant tests` — passed.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `git diff --check` — passed.
- `uv build --wheel --out-dir <temporary-directory>` — wheel built with the
  Portfolio/RL fixed Cores, Project assets, and Studio JavaScript.
- A fresh-path isolated wheel install created and executed both reference
  Projects successfully. Portfolio published five artifacts, reconciled
  validation attribution, and produced validation net Sharpe `1.770107`; RL
  produced validation mean net Sharpe `8.967443`.

## Progress log

- 2026-07-24 — Proposed from the post-factor-diagnostics completion audit.
- 2026-07-24 — Activated after source audit fixed the state machine, sizing,
  split, ledger, risk-attribution, and no-hysteresis comparison semantics.
- 2026-07-24 — Completed after deterministic transition/timing, future-prefix,
  exact attribution, Studio, full-suite, and isolated-wheel audits passed.

## Completion

Portfolio V2 now converts every causal factor percentile through an explicit
entry/hold/exit/reversal state machine, conviction and inverse-volatility
sizing, fixed portfolio constraints, drift, and the execution no-trade band.
Its immutable decision ledger reconciles asset-level trades, return, cost, and
trailing component risk to portfolio evidence, while Studio exposes the
verified policy effect and return/risk concentration.

The governed RL lane now selects among four independently stateful sleeves that
use this same fixed policy. Candidate factor or state-encoder code still cannot
control thresholds, sizing, constraints, costs, attribution, or promotion.
