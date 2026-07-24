# Build a governed RL factor-policy laboratory

- Status: `proposed`
- Updated: `2026-07-24`
- Related design: [[docs/design/quant-research-lifecycle]].

## Outcome

AutoQuant can test whether a bounded RL policy improves causal factor blending
or portfolio targets beyond simple fixed baselines under frozen rewards,
costs, walk-forward splits, multiple seeds, and locked evaluation authority.

## Context

RL is useful only when it is treated as a falsifiable research candidate rather
than an opaque order generator. Financial samples are small, non-stationary,
and unusually vulnerable to reward leakage and seed selection. The portfolio
laboratory must exist first so actions, costs, and constraints have one fixed
meaning.

## Scope

### In scope

- Causal state features, previous-position state, factor-blend or target-weight
  actions, and next-period net-return rewards with explicit penalties.
- Train/validation/test or walk-forward isolation, multiple fixed seeds,
  deterministic budgets, and saved model/config artifacts.
- Comparisons against equal-weight, fixed-factor, and simple linear policies.
- Cross-seed dispersion, cross-fold stability, turnover, cost, risk, and
  generalization evidence.

### Out of scope

- Autonomous live order placement.
- Letting candidate code choose its reward, test split, costs, seed count, or
  benchmark.
- A general-purpose distributed ML platform.

## Acceptance

- [ ] The Judge owns state/action/reward semantics and rejects lookahead.
- [ ] Every result includes simple baselines, all declared seeds and folds,
      dispersion, failure evidence, and exact model/config artifacts.
- [ ] A deterministic tiny fixture proves the complete loop without installing
      a heavyweight platform or running a long training campaign.

## Work

- [ ] Finalize after the portfolio laboratory contract is implemented.
- [ ] Implement a minimal replaceable policy adapter and fixed evaluator.
- [ ] Ship reference candidates, evidence, Studio projection, and tests.
- [ ] Audit reproducibility and failure behavior.

## Findings and decisions

- 2026-07-24 — The first RL lane chooses factor mixtures or portfolio targets;
  it does not emulate a broker or own order execution.

## Verification

- Pending.

## Progress log

- 2026-07-24 — Proposed as a portfolio-dependent follow-up.

## Completion

Pending.
