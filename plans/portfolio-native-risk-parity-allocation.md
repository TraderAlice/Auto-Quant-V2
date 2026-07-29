# Portfolio-native risk-parity allocation

- Status: `complete`
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

- [x] The exact honest request passes public intake and creates one
  self-contained allocation Project without Factor/RL Studies.
- [x] Request, policy, fixed weighted reference, data, Judge, and no-trading
  authority are content-locked and reject unknown or unfunded inputs.
- [x] Deterministic fixtures prove causality, capped ERC behavior, scale-down
  only risk control, schedule timing, drift, no-trade, cost, and reference-path
  reconciliation.
- [x] Successful Runs publish complete immutable evidence and a strict
  Explorer independently rederives weights, component risk, parity error,
  accounting, relative metrics, and the latest decision.
- [x] CLI, orientation, Studio, schemas, capabilities, docs, and package
  contents expose the allocation route without suggesting a Factor Session.
- [x] The real six-asset, 4,922-session Yahoo field trial returns a useful
  validation-only support/reject conclusion and immutable Report.
- [x] Focused/full tests, docs, wheel smoke, patch version, milestone
  commit/push, tag, clean release replay, and repository cleanliness pass.

## Work

- [x] Clarify the real request in English and preserve the public intake
  failure without a partial Project.
- [x] Record the Project-derived framework need and reject factor-shaped
  workarounds.
- [x] Define the narrow allocation and weighted-reference contracts.
- [x] Implement request intake, template, fixed Judge, evidence, Explorer, CLI,
  and Studio.
- [x] Run deterministic and real-data validation, then publish the Report.
- [x] Release, reproduce from a clean version, and close the field trial.

## Findings and decisions

- 2026-07-29 — A construction rule is not a predictive factor. Portfolio-native
  research must be able to start and finish without Factor qualification.
- 2026-07-29 — The reference is a complete portfolio path, not a named-asset
  return series. Candidate and reference must share schedule, drift, no-trade,
  cost, and return timing for the comparison to be meaningful.
- 2026-07-29 — V1 is deliberately one fixed ERC method. The request contract
  may name the method and its trailing window, but it does not open an
  arbitrary optimizer or candidate DSL.
- 2026-07-29 — The latest scheduled target and the end-of-dataset model state
  are different evidence. A partial terminal month publishes the drifted
  hold-state and `ordinaryRebalanceDue: false`; it must not relabel the last
  completed month-end target as current.

## Verification

- Public `aq project intake` with the honest request returned
  `validation.failed` for unknown `allocationPolicy`, missing benchmark
  `symbol`, unknown benchmark `weights`, and unsupported benchmark kind.
  `global-etf-risk-parity-intake-repro` was not created.
- Public intake on clean `0.8.7` created
  `global-etf-risk-parity-allocation-v087-clean` with only the fixed
  `ohlcv-risk-parity-allocation` Study and `ready-for-run` status.
- Clean Run `run-20260729T035547148203Z-23025272478a` at commit `f7018ab`
  succeeded in 16,458 ms with `dirty: false`. Validation candidate/reference
  net Sharpe was `0.643539` / `0.658658`; the fixed selection therefore
  rejected ERC at advantage `-0.015119`. Test advantage `+0.017948` remained
  visible audit only.
- The strict Explorer reconciled accounting, weights, risk contributions,
  parity, solver counts, current state, and validation authority. On
  2026-07-28 the incomplete month was a hold, not a fabricated month-end
  decision. Validation, orientation, CLI, Studio snapshot, docs, package
  contents, and adversarial rehashed-artifact tests pass.
- The pre-release full regression ran 276 tests with one version-frontmatter
  mismatch, which was corrected. The final regression result is recorded in
  Completion.

## Progress log

- 2026-07-29 — Created the blank
  `global-etf-risk-parity-allocation` construction site, clarified the complete
  request before data work, reproduced the current boundary, and promoted the
  observed need into this plan.
- 2026-07-29 — Implemented the narrow contract, fixed Study/Judge, strict
  read model, CLI/Studio route, docs, and deterministic fixtures; fixed the
  code milestone at `f7018ab`.
- 2026-07-29 — Recreated the exact real request through public intake on the
  clean milestone and published the immutable rejected Run without opening a
  Factor, RL, or Session lane.

## Completion

AutoQuant `0.8.7` makes one non-predictive portfolio-construction request a
first-class fixed Study. The clean real-data result rejects the ERC model
against the caller's fixed 60/40 validation reference while preserving its
lower-volatility and lower-drawdown evidence, its latest historical target,
the current drifted hold-state, and no-trading authority. Final verification:
277/277 tests, 1,014 documentation links, source/wheel smoke, strict CLI
Explorer, orientation, Studio snapshot, clean release replay, tag, push, and
clean repository.
