# Make signal triggers and position attribution explicit

- Status: `proposed`
- Updated: `2026-07-24`
- Related design: [[docs/design/portfolio-construction-lab]],
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

- [ ] Every position change has one fixed causal reason and target calculation.
- [ ] Entry/exit hysteresis prevents rank noise from becoming unexplained
      turnover while preserving explicit timing.
- [ ] Asset targets reconcile exactly to portfolio constraints, daily returns,
      trades, costs, and attribution totals.
- [ ] Risk and contribution concentration are visible by asset/state/regime.
- [ ] CLI artifacts and Studio show the same verified decision path.
- [ ] Tests prove timing, state transitions, constraint reconciliation,
      attribution identities, isolation, and packaging.

## Work

- [ ] Activate after reviewing the completed Factor diagnostics evidence.
- [ ] Fix signal-state and risk-budget semantics before implementation.
- [ ] Implement decision ledger, attribution, and observation surfaces.
- [ ] Complete regression, documentation, and package audits.

## Findings and decisions

- 2026-07-24 — Portfolio target weights are the correct AutoQuant/OpenAlice
  handoff, but a target without a causal state transition and reason ledger is
  too opaque for human/AI collaboration.

## Verification

Pending.

## Progress log

- 2026-07-24 — Proposed from the post-factor-diagnostics completion audit.

## Completion

Pending.
