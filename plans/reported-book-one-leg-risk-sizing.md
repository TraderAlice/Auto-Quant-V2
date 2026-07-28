# Reported-book one-leg risk sizing field trial

- Status: `active`
- Updated: `2026-07-28`
- Related design: [[docs/design/reported-position-book-risk]] and
  [[docs/design/research-intake-and-dataset-snapshots]].
- Field matrix: [[docs/trading-request-field-trials]].

## Outcome

Let an AutoQuant coworker answer one bounded target-position question: given a
caller-reported funded book, one caller-authorized reducible asset, cash as the
explicit destination, one fixed historical covariance window, and a maximum
annualized-volatility budget, find the smallest reduction that satisfies the
budget or prove that the permitted change cannot do so.

## Context

Representative request:

> 我现在 AAPL 20%、MSFT 25%、NVDA 30%、QQQ 25%。按最近一年的波动算，我最多想
> 承受 15% 年化波动；其他仓位都不动，只减 NVDA、剩下放现金，至少要减到多少？

AutoQuant `0.7.0` reports a 252-session modeled volatility of `19.7685%` for
this book and ranks a standardized one-percentage-point NVDA-to-cash reduction
first. It cannot bind the caller's `15%` ceiling, authorize only NVDA as the
adjustable leg, or derive the minimum compliant weight. Asking the Agent to
manufacture a grid of `positionScenarios` would violate that field's
caller-supplied-only authority.

This is not a universal portfolio optimizer. The caller has already fixed the
book, adjustable asset, destination, risk metric, covariance window, and
objective. The remaining calculation is a one-dimensional constrained
historical sizing problem.

## Scope

### In scope

- Preserve one external-reported funded baseline.
- Bind one requested held asset as the only reducible leg and cash as the only
  destination.
- Bind one annualized-volatility ceiling and one existing fixed covariance
  lookback as the governing constraint.
- Derive the smallest permitted reduction that reaches the ceiling, with an
  exact infeasible result when no point on the permitted path can satisfy it.
- Report the resulting complete book, cash, modeled volatility, HHI, effective
  risk bets, per-asset contributions, and diagnostic behavior under the other
  predeclared lookbacks.
- Preserve no-account, no-tax, no-order, and no-trading authority across Run,
  strict Explorer, orientation, CLI, Studio, and handoff.

### Out of scope

- Choosing which asset to reduce, adding another risky asset, changing multiple
  legs, or searching expected-return-optimal weights.
- A general optimization DSL, covariance-method selection, leverage, shorts,
  tax lots, transaction costs, liquidity, or execution.
- Claiming that a historical covariance ceiling guarantees future realized
  volatility.

## Acceptance

- [x] Preserve an AutoQuant `0.7.0` failure reproduction without fabricating a
  scenario grid or returning an irrelevant 1% sensitivity.
- [x] Define the smallest strict caller-authority and derived result contract.
- [x] Reject ambiguous adjustable legs, non-cash destinations, invalid
  ceilings/windows, unauthorized assets, and already-compliant or infeasible
  states with explicit semantics.
- [x] One immutable Run and strict Explorer reconcile the exact one-dimensional
  solution, complete resulting book, risk metrics, and boundary cases.
- [x] Orientation and Studio terminate at descriptive target-position review
  with no Session, automatic trading, or Order authority.
- [ ] A clean Yahoo field Run answers the 15%-ceiling NVDA question and records
  assumptions, Harness identity, evidence, and limitations.
- [ ] Focused/full regression, package smoke, documentation, commit, push, tag,
  and cleanliness pass.

## Work

- [x] Reproduce the current semantic gap from a strict real-data Project.
- [x] Define and implement the bounded sizing contract.
- [x] Add deterministic success, already-compliant, infeasible, malformed,
  tamper, and authority tests.
- [ ] Execute and interpret the clean Yahoo field trial.
- [ ] Complete release audit, record evidence, push, and close the plan.

## Findings and decisions

- 2026-07-28 — Target position sizing belongs in AutoQuant research when the
  caller fixes the allowed weight path and risk budget. How to realize that
  target through orders, TPSL, timing, or conversation remains an OpenAlice
  execution concern.
- 2026-07-28 — `positionScenarios` cannot be reused for an Agent-generated
  search grid. Its `0.7.0` authority is explicitly caller-supplied historical
  comparison; silently broadening it would make evidence provenance false.
- 2026-07-28 — Cash is the first useful destination because it creates one
  bounded scalar path and avoids premature multi-asset optimization.
- 2026-07-28 — Project `us-megacap-nvda-risk-budget-v070-gap` proves that
  natural-language request preservation is insufficient machine authority.
  Intake/validation succeed and orientation offers a baseline Run, while the
  fixed dependency contains neither ceiling, governing window, adjustable leg,
  destination, nor sizing objective.
- 2026-07-28 — The Agent stopped before executing a successful but irrelevant
  baseline audit. A field trial passes only when the recommended operation can
  answer the actual decision question, not merely when the Project is valid.
- 2026-07-28 — AutoQuant `0.8.0` freezes `positionSizing` as one caller-bound
  long-holding-to-cash path and solves its convex annualized-variance quadratic
  exactly. It does not generate a scenario grid or search another asset.
- 2026-07-28 — `infeasible` means no point anywhere on the permitted path
  satisfies the ceiling. The constrained minimum is returned as proof, not as
  a recommendation.

## Verification

- AutoQuant `0.7.0` public intake created
  `us-megacap-nvda-risk-budget-v070-gap` against the same 643-session,
  twelve-asset Yahoo XNYS package with `status: ready-for-run`.
- `aq validate` succeeds and `aq orient` returns only `run.execute` with
  `researchAgenda.status: waiting-evidence`.
- `strategies/position-snapshot.json` contains the exact reported baseline and
  `scenarios: []`; no frozen field represents the 15% ceiling, 252-session
  governing window, NVDA-only path, cash destination, or minimum reduction.
- Project `research.md` preserves the complete caller authority and explains
  why the ordinary 1% sensitivity Run does not answer it.
- Project `framework-needs.md` rejects an Agent-generated scenario grid and
  links this plan as the smallest bounded Core promotion.
- Twelve deterministic Book Risk tests cover valid authority freezing, exact
  boundary sizing, already-compliant and infeasible states, malformed requests,
  strict rehashed tamper rejection, CLI, orientation, and Studio projection.

## Progress log

- 2026-07-28 — Selected the next real trading request after completing the
  caller-supplied book-reallocation field trial.
- 2026-07-28 — Preserved the `0.7.0` machine-authority failure reproduction and
  stopped before an irrelevant baseline-only Run.
- 2026-07-28 — Implemented and strictly verified the `0.8.0` one-leg sizing
  contract through intake, immutable Run, Explorer, CLI, orientation, and
  Studio. The clean Yahoo reproduction remains pending.

## Completion

Pending.
