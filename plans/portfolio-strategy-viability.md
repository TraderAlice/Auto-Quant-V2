# Diagnose where a mechanical strategy loses its edge

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/portfolio-construction-lab]],
  [[docs/design/portfolio-decision-explorer]],
  [[docs/design/quant-research-lifecycle]], and
  [[docs/design/program-research-dossiers]].

## Outcome

One verified Portfolio Run explains whether its validation evidence fails at
factor prediction, gross portfolio monetization, trading friction, or
post-cost robustness. A quant researcher can see the exact gross-to-net wedge,
cost break-even, turnover efficiency, delay sensitivity, temporal
concentration, drawdown duration, and a bounded next research focus without
opening artifacts or using visible test evidence for selection.

## Context

AutoQuant already exposes professional metrics, mechanical target formation,
and exact position sizing. They remain distributed across Run metrics, stress
objects, and daily artifacts. The current Studio can say that a signal fails
after implementation, but it cannot show where the edge disappeared or which
part of the fixed research chain deserves the next iteration. That is the
ordinary diagnostic question a real quant desk asks after every backtest.

## Scope

### In scope

- A Core-owned strategy-viability projection reconstructed from the immutable
  Portfolio daily ledger and reconciled Run metrics.
- Validation-only stage diagnosis across factor edge, gross portfolio edge,
  and post-cost edge.
- Gross/net/benchmark return and Sharpe, cost/turnover wedge, return per unit
  turnover, exact non-negative break-even cost, 0/base/25 bps stress, extra
  delay, monthly breadth, best-day dependence, and underwater duration.
- One fixed research-prioritization focus that cannot alter KEEP/REVERT or
  authorize a trade.
- CLI, Studio, Report, and Dossier parity plus legacy compatibility.

### Out of scope

- Changing the factor, signal state machine, allocator, cost model, objective,
  promotion verdict, or historical Run.
- Optimizing cost assumptions, using test evidence to choose a strategy, or
  turning descriptive diagnostics into confidence or trading authority.
- Intraday spread/impact inference from OHLCV or a Broker execution model.

## Acceptance

- [x] Validation diagnosis distinguishes absent factor edge, failed gross
      monetization, cost fragility, and positive post-cost evidence from exact
      Core data.
- [x] Each split reconciles gross/net/benchmark, friction, timing breadth,
      concentration, drawdown duration, and stress evidence with explicit
      selection roles.
- [x] Cost break-even and return-per-turnover units are exact and reject
      ledger/Run metric tampering.
- [x] CLI, Studio, and frozen Portfolio Report/Dossier use the same Core object
      with research-prioritization-only and `tradingAuthority: none`.
- [x] Legacy Reports remain readable without invented viability evidence.
- [x] Deterministic, real Yahoo, responsive-browser, documentation, and package
      verification pass.

## Work

- [x] Audit current Portfolio metrics, daily ledger, Studio, and handoff.
- [x] Implement and schema the verified strategy-viability projection.
- [x] Render the same evidence in CLI, Studio, Report, and Dossier.
- [x] Add reconstruction, tamper, compatibility, and UI regression coverage.
- [x] Complete real-data verification, documentation, commit, and push.

## Findings and decisions

- 2026-07-25 — Existing evidence already contains gross/net performance,
  exact traded notional and cost, 0/10/25 bps stress, extra delay, factor rank
  IC, and full daily chronology. The gap is a reconciled diagnosis, not another
  Judge simulation.
- 2026-07-25 — Stage diagnosis must use validation only. Test can describe
  confirmation or deterioration but cannot change the stage or research focus.
- 2026-07-25 — Break-even cost means the non-negative per-traded-notional bps
  that drives compounded split return to zero under the frozen daily gross
  path. If zero-cost gross return is already non-positive, no non-negative
  break-even exists.
- 2026-07-25 — The real Yahoo validation path has rank IC `0.0028`, gross
  Sharpe `-0.6659`, and net Sharpe `-1.4679`. It is therefore
  `factor-not-monetized`, not `cost-fragile`; reducing the 10 bps assumption
  cannot recover an already-negative gross edge.
- 2026-07-25 — Yahoo validation is positive in `46.15%` of months, remains
  underwater for `244` bars, and returns `-22.35%` without its best five days.
  Test worsens to rank IC `-0.0768` and net Sharpe `-3.1475`, but it remains
  audit-only and does not change the validation diagnosis.

## Verification

- `uv run python -m unittest tests.test_portfolio_explorer tests.test_intake -v`
  — 27 tests passed.
- `uv run python -m unittest tests.test_reports tests.test_studio tests.test_cli -v`
  — 31 tests passed.
- `uv run python -m unittest tests.test_dossiers -v` — 2 end-to-end
  multi-lane Dossier tests passed.
- Focused post-review reconstruction/tamper and prior/legacy Report
  compatibility tests passed.
- Yahoo Run `run-20260725T030848361754Z-3ef48896cfcb` published immutable
  Report `report-20260725T030935732690Z-a81386e62551` with viability hash
  `efc9efc311a6eda21ae01331be1dabf61d9c787a4139ccb614c016a0c497a788`;
  Report reload and Session completion succeeded.
- Browser verification showed the exact validation/test chain and frozen
  Report proof. At 1280px, document and panel widths reconcile with no
  horizontal overflow.
- Python compile, JavaScript syntax, `git diff --check`, 568 documentation
  double-links, and source/wheel builds passed.

## Progress log

- 2026-07-25 — Plan activated after the sizing-anatomy milestone made the
  remaining factor → implementation → net-evidence gap visible.
- 2026-07-25 — Core diagnosis, strict schema/reconciliation, CLI/Studio,
  Report/Dossier freezing, compatibility, real Yahoo handoff, browser audit,
  documentation, and package checks completed.

## Completion

Completed: one immutable Run, Studio, CLI, Report, and Dossier now answer where
the strategy lost its edge and which bounded research layer deserves the next
iteration, without changing selection, promotion, or trading authority.
