# Portfolio-native risk-parity allocation

- Status: `active`
- Updated: `2026-07-29`
- Related design: [[docs/design/portfolio-construction-lab]],
  [[docs/design/portfolio-risk-governor]],
  [[docs/design/caller-owned-decision-cadence]], and
  [[docs/design/research-intake-and-dataset-snapshots]].
- Source field trial: [[docs/trading-request-field-trials]] and Project
  `global-etf-risk-parity-allocation`.

## Outcome

Let an AutoQuant coworker answer one real Portfolio-native strategic allocation
request without inventing a predictive factor: causally construct and evaluate
a caller-fixed long-only equal-risk-contribution ETF portfolio against one
caller-fixed weighted reference on the same monthly clock, cost convention,
and immutable evidence surface.

## Context

The current Research Desk assumes that target weights originate from
`factors/candidate.py`. That is correct for predictive allocation questions but
wrong for a caller who explicitly asks not to forecast returns and instead
fixes a covariance risk-budget construction rule.

The field-trial request binds SPY, EFA, TLT, IEF, GLD, and DBC; trailing 252
completed XNYS sessions; official calendar-month decisions; long-only gross
1.0; 35% per-asset cap; scale-down-only 10% annualized volatility ceiling;
5 bps cost; 2% one-way no-trade band; and a same-schedule 60% SPY / 40% IEF
reference. Public intake rejects both `allocationPolicy` and the fixed-weight
benchmark. A factor-shaped workaround would change the question.

## Scope

### In scope

- Add one strict request-bound equal-risk-contribution allocation policy.
- Add one strict fixed-weight portfolio benchmark with complete funded weights,
  same decision schedule, drift, no-trade, and cost semantics.
- Add a self-contained Portfolio-native allocation Project template and fixed
  Study/Judge; it does not require Factor qualification or RL.
- Use only trailing completed returns known through decision close `t`.
- Solve non-negative capped equal risk contribution deterministically, disclose
  convergence/tolerance/cap binding, and never call an unequal capped result
  exact parity.
- Apply the existing final-book mandate repair and scale-down-only covariance
  volatility ceiling.
- Publish immutable target, executed book, trades, cost, performance,
  benchmark-relative, component-risk, parity, constraint, and current-decision
  evidence.
- Add strict CLI Explorer and Studio projections with no trading authority.
- Complete a clean real Yahoo field trial and immutable Report.

### Out of scope

- Expected-return optimization, Black-Litterman, efficient frontiers,
  hierarchical risk parity, cluster selection, arbitrary constraints, leverage
  targeting, shorting, tax lots, account truth, or Orders/TPSL.
- Treating 60/40 as a security benchmark or letting it use a different
  rebalance/cost clock.
- Hiding infeasibility, solver failure, or cap-induced parity error.
- Forcing the allocation request through Factor or RL lanes.

## Acceptance

- [ ] The exact honest request passes public intake and creates one
  self-contained allocation Project without Factor/RL Studies.
- [ ] Request, policy, fixed weighted reference, data, Judge, and no-trading
  authority are content-locked and reject unknown or unfunded inputs.
- [ ] Deterministic fixtures prove causality, capped ERC behavior, scale-down
  only risk control, schedule timing, drift, no-trade, cost, and reference-path
  reconciliation.
- [ ] Successful Runs publish complete immutable evidence and a strict
  Explorer independently rederives weights, component risk, parity error,
  accounting, relative metrics, and the latest decision.
- [ ] CLI, orientation, Studio, schemas, capabilities, docs, and package
  contents expose the allocation route without suggesting a Factor Session.
- [ ] The real six-asset, 4,922-session Yahoo field trial returns a useful
  validation-only support/reject conclusion and immutable Report.
- [ ] Focused/full tests, docs, wheel smoke, patch version, milestone
  commit/push, tag, clean release replay, and repository cleanliness pass.

## Work

- [x] Clarify the real request in English and preserve the public intake
  failure without a partial Project.
- [x] Record the Project-derived framework need and reject factor-shaped
  workarounds.
- [ ] Define the narrow allocation and weighted-reference contracts.
- [ ] Implement request intake, template, fixed Judge, evidence, Explorer, CLI,
  and Studio.
- [ ] Run deterministic and real-data validation, then publish the Report.
- [ ] Release, reproduce from a clean version, and close the field trial.

## Findings and decisions

- 2026-07-29 — A construction rule is not a predictive factor. Portfolio-native
  research must be able to start and finish without Factor qualification.
- 2026-07-29 — The reference is a complete portfolio path, not a named-asset
  return series. Candidate and reference must share schedule, drift, no-trade,
  cost, and return timing for the comparison to be meaningful.
- 2026-07-29 — V1 is deliberately one fixed ERC method. The request contract
  may name the method and its trailing window, but it does not open an
  arbitrary optimizer or candidate DSL.

## Verification

- Public `aq project intake` with the honest request returned
  `validation.failed` for unknown `allocationPolicy`, missing benchmark
  `symbol`, unknown benchmark `weights`, and unsupported benchmark kind.
  `global-etf-risk-parity-intake-repro` was not created.

## Progress log

- 2026-07-29 — Created the blank
  `global-etf-risk-parity-allocation` construction site, clarified the complete
  request before data work, reproduced the current boundary, and promoted the
  observed need into this plan.

## Completion

Pending.
