# Mechanical position lifecycle evidence

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/mechanical-position-lifecycle-evidence]],
  [[docs/design/signal-policy-and-attribution]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/portfolio-decision-explorer]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Every new Portfolio Run turns its exact per-asset executed-weight path into
split-bounded position episodes. A researcher can see how mechanical triggers
became held positions, how long those positions lasted, their additive gross
and net contribution, entry/resize/exit cost, favorable/adverse contribution
excursions, and bars where signal intent differed from execution.

## Context

AutoQuant already publishes every factor, signal event, target, executed
weight, trade, contribution, and cost. A real portfolio researcher still has
to manually reconstruct contiguous positions from hundreds of ledger rows to
answer basic iteration questions: whether profits come from many short-lived
entries or a few long holds, whether losers are larger than winners, whether
the no-trade band creates stale positions, and whether entry/exit costs erase
gross signal value.

The evidence must remain target-weight research. It describes historical
executed-weight episodes and does not create Broker orders, fills, stop-loss
semantics, or trade recommendations.

## Scope

### In scope

- One exact episode state machine based on the sign of executed weights.
- Split clipping with explicit left/right censoring and no cross-boundary PnL.
- Linear trade-cost allocation across close/open notional on reversals.
- Holding bars, gross/net contribution, entry/holding/exit cost,
  contribution MFE/MAE, signal mismatch, no-trade, and risk-override evidence.
- Complete-episode win rate, payoff/profit factor, holding distribution,
  per-asset summaries, and exact ledger reconciliation.
- Immutable artifact plus CLI, Report, Dossier, decision matrix, explorer, and
  Studio projection with legacy fallback.

### Out of scope

- Order fills, realized tax lots, intrabar MFE/MAE, TPSL, borrow/funding,
  Broker positions, or OpenAlice UTA mutation.
- Candidate selection based on episode statistics.
- RL action episodes; governed RL continues to consume the same mechanical
  sleeves and will receive a separate policy-lifecycle milestone.

## Acceptance

- [x] Episodes are deterministic, split-bounded, and derived only from exact
  executed weights, trades, contributions, and costs already in the ledger.
- [x] Entry, same-side resize, exit, reversal, carried-in, and carried-out
  positions allocate every cost exactly once.
- [x] Episode gross/cost/net totals reconcile to every selected ledger row
  within numeric tolerance, including cost-only boundary segments.
- [x] Complete-episode and clipped-segment statistics are named separately;
  censored paths never masquerade as completed trades.
- [x] Artifact, explorer, CLI, Reports, Dossiers, decision matrix, and Studio
  expose one context-only interpretation with no trading authority.
- [x] Legacy Runs remain readable and deterministic tests reject rehashed
  episode or metric fabrication.

## Work

- [x] Audit current signal, execution, attribution, and professional metric
  coverage.
- [x] Implement and verify the episode state machine and aggregate evidence.
- [x] Add immutable/public projections, documentation, and Studio UX.
- [x] Run focused/full tests, wheel smoke, browser QA, and completion audit.

## Findings and decisions

- 2026-07-25 — Existing signal-state and attribution evidence is exact but
  row-oriented. The missing professional object is a contiguous executed
  position episode.
- 2026-07-25 — Episodes are clipped at fixed split boundaries. Left/right
  censoring is explicit so validation never borrows a train entry or test exit.
- 2026-07-25 — MFE/MAE means cumulative additive portfolio-return
  contribution at daily-bar resolution, not intrabar asset-price excursion.
- 2026-07-25 — Lifecycle metrics are contextual diagnostics. They explain
  mechanics but cannot enter KEEP/REVERT or Session dominance.

## Verification

- `uv run --with pytest pytest -q`: 154 tests and 17 subtests passed.
- Final invariant-focused checks: 4 tests passed after duplicate-date and
  executed-transition validation were tightened.
- Fresh Python 3.11 wheel smoke created a Portfolio Project and Run, loaded
  the public explorer, reconciled 29 validation complete episodes, preserved
  both validation/test recent episodes, and found zero executed-risk breaches.
- In-app browser QA verified Validation/Test audit switching, per-asset and
  recent-episode rows, desktop layout, and zero browser console warnings or
  errors at `http://127.0.0.1:8775/`.

## Progress log

- 2026-07-25 — Plan created from the professional evidence-chain audit.
- 2026-07-25 — Implemented the split-bounded state machine, immutable artifact,
  strict reconstruction, public read models, and legacy fallback.
- 2026-07-25 — Added CLI, Report, Dossier, matrix, template, documentation, and
  Studio lifecycle surfaces.
- 2026-07-25 — Completed full tests, final focused hardening, fresh-wheel smoke,
  and browser QA.

## Completion

Completed with every acceptance item backed by executable or browser evidence.
