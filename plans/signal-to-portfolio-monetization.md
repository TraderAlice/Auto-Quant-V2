# Explain signal-to-portfolio monetization

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/signal-policy-and-attribution]],
  [[docs/design/portfolio-decision-explorer]],
  [[docs/design/quant-research-lifecycle]], and
  [[docs/design/program-research-dossiers]].

## Outcome

One verified Portfolio Run decomposes the additive return path from a
normalized signal-intent book through fixed sizing, covariance governance,
historical execution, and cost. A quant researcher can identify which
transformation most damaged validation monetization without changing the
strategy, selection verdict, or trading authority.

## Context

The strategy-viability projection now distinguishes positive factor rank IC
from negative gross portfolio Sharpe, but `factor-not-monetized` still groups
signal thresholds, unequal sizing, risk scaling, no-trade retention, and
execution together. The immutable decision ledger already contains every
asset/date input required to separate those transformations and reconcile the
actual gross and net path.

## Scope

### In scope

- A Core-owned normalized equal-intent diagnostic using the fixed signal state,
  Portfolio Mandate, and gross budget.
- Split-bounded additive return contribution at equal intent, pre-governor
  sizing, governed target, historical executed gross, and executed net stages.
- Exact stage deltas, per-asset decomposition, gate coverage, and reconciliation
  to immutable daily accounting.
- Validation-only identification of the largest adverse transformation.
- CLI, Studio, Report, and Dossier parity with legacy compatibility.

### Out of scope

- Changing the factor, signal state machine, allocator, risk governor,
  execution policy, cost model, objective, or historical Run.
- Treating the normalized equal-intent book as an investable baseline or
  allowing it to enter KEEP/REVERT.
- Compounded counterfactual equity curves, fill simulation, Broker behavior,
  live trading, or RL policy selection.

## Acceptance

- [x] Validation and visible-test stages reconcile exact ledger contributions
      and retain their selection roles.
- [x] Equal-intent weights obey tradability, direction, side funding, gross
      budget, and context-only constraints without inventing exposure.
- [x] Core identifies the largest validation-only adverse transformation and
      explicitly preserves research-prioritization-only authority.
- [x] CLI, Studio, frozen Portfolio Report, and Dossier display the same
      immutable projection; older artifacts remain readable.
- [x] Deterministic tests, real Yahoo evidence, browser inspection,
      documentation links, and package checks pass.

## Work

- [x] Audit the decision ledger, Mandate allocator, split, and compatibility
      contracts.
- [x] Implement and schema the monetization projection with strict
      reconciliation.
- [x] Freeze and render the projection across Report, Dossier, CLI, and Studio.
- [x] Add reconstruction, tamper, compatibility, and UI regression coverage.
- [x] Complete real-data verification, documentation, commit, and push.

## Findings and decisions

- 2026-07-25 — The verified decision ledger already freezes signal state,
  pre-governor target, governed target, executed weight, forward asset return,
  allocated cost, and net contribution for every asset/date. No Judge rerun or
  evaluation-contract change is required.
- 2026-07-25 — The equal-intent layer is a normalized arithmetic diagnostic,
  not a tradable comparator. Dollar-neutral intent is flat unless both sides
  can be funded, matching the fixed allocator's side-breadth rule; directional
  mandates allocate only their permitted side and may leave cash.
- 2026-07-25 — Stage contribution is additive
  `weight × next-bar asset return`. It is intentionally not a separately
  compounded counterfactual path because changing weights would also change
  drift, turnover, execution, and cost.
- 2026-07-25 — Real Yahoo validation equal intent is already negative at
  `-8.3330%` annualized additive contribution. Fixed sizing improves it to
  `-8.1466%`, covariance governance contributes zero, and historical
  no-trade/execution improves it to `-7.8375%` gross. The 10 bps cost path then
  contributes `-9.4185%`, producing `-17.2560%` net. The primary failure is
  signal direction/threshold conversion, not unequal sizing.

## Verification

- `uv run python -m unittest tests.test_portfolio_explorer tests.test_intake
  tests.test_reports tests.test_dossiers tests.test_studio tests.test_cli -v`
  — 62 affected tests passed.
- `uv run python -m unittest discover -s tests -v` — all 165 repository tests
  passed.
- Offset-preserving decision-ledger tampering is rejected by the new
  weight/return formula reconciliation. Directional intake proves context-only
  equal-intent/raw/governed contributions remain exactly zero.
- Yahoo Run `run-20260725T034047473666Z-0df0d62fff9e` published immutable
  Report `report-20260725T034148700329Z-e3eb2954c182` with monetization hash
  `6137a672398b27309625d73e456bb21cbe54c67a72c037002e48166695705107`;
  Session completion
  `completion-20260725T034156270092Z-f2b8d79e4a55` succeeded.
- Browser verification showed all five validation stages, four transformation
  deltas, gate counts, test audit, PASS reconciliation, and the frozen Report
  summary. At 1280px the document, panel, and chain have no horizontal
  overflow; mobile breakpoints stack the diagnosis and stage grid.
- Python compile, JavaScript syntax, `git diff --check`, 573 documentation
  double-links, and source/wheel builds passed.

## Progress log

- 2026-07-25 — Plan activated after the Yahoo validation diagnosis showed
  positive rank IC but negative gross portfolio Sharpe.
- 2026-07-25 — Core projection, strict Schema/reconciliation, CLI/Studio,
  Report/Dossier freezing, compatibility, real Yahoo handoff, browser audit,
  full test suite, documentation, and package checks completed.

## Completion

Completed: one immutable Portfolio Run now explains whether signal intent,
fixed sizing, risk governance, historical execution, or cost damaged
monetization, while preserving validation-only research prioritization and no
trading authority.
