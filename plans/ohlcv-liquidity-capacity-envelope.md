# OHLCV liquidity-capacity envelope

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/portfolio-liquidity-capacity]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/portfolio-decision-explorer]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Every new Portfolio Run turns its exact mechanical trade path and causal
trailing OHLCV dollar volume into a reconciled capital-capacity envelope. A
trader or OpenAlice caller can see conservative and upper participation
capacity, reference-NAV breaches, missing-history dates, and binding assets
without mistaking the estimate for executable market impact or live account
authority.

## Context

The current implementation reports volume participation only at one fixed
`$1,000,000` reference NAV. That proves a unit-level accounting path but does
not answer the practical sizing question: how much capital could this exact
mechanical rebalance path carry before it exceeds a declared share of recent
dollar volume?

OHLCV cannot support queue position, spread, impact, or fill guarantees. It can
still support a useful causal envelope when every decision uses trailing
average dollar volume known through the decision close and explicitly exposes
dates where the estimate is unavailable.

## Scope

### In scope

- Fixed trailing-dollar-volume policy and participation ceilings.
- Per-asset/date capacity evidence reconciled to exact executed trade weights.
- Validation/test capacity distributions, reference-NAV breach rates, missing
  history, and binding-asset counts.
- Context-only Session comparison plus CLI, Report, Dossier, explorer, and
  Studio projection.
- Legacy Portfolio evidence remains readable with capacity marked unavailable.

### Out of scope

- Spread, nonlinear impact, order-book depth, queue priority, or fill claims.
- Liquidity-driven target changes, caller-selected capital, Broker/UTA state,
  or portfolio selection authority.
- Treating capacity as favorable candidate evidence before a capital mandate
  exists.

## Acceptance

- [x] Capacity at each decision uses only close and volume through that close,
  exact executed trade weights, and a fixed trailing ADV policy.
- [x] Every available per-date envelope reconciles to its binding asset and
  participation ceiling; incomplete active trades cannot produce a capacity
  claim.
- [x] Validation/test metrics expose trade-date coverage, conservative
  capacity distribution, reference-NAV breach rate, and binding assets.
- [x] Capacity remains contextual and cannot affect KEEP/REVERT or Session
  non-dominance.
- [x] Portfolio artifacts, explorer, CLI, Reports, Dossiers, and Studio expose
  the same verified interpretation and no trading-authority claim.
- [x] Legacy Runs stay readable and deterministic tests prove causality,
  scaling, reconciliation, tamper rejection, and no-trade/data-gap behavior.

## Work

- [x] Audit the current participation, artifact, explorer, and Studio boundary.
- [x] Implement fixed capacity evidence and aggregate metrics.
- [x] Add verified public projections, documentation, and Studio presentation.
- [x] Run focused/full tests, browser QA, package smoke, and completion audit.

## Findings and decisions

- 2026-07-25 — A single reference-NAV participation number is not an actionable
  capital answer. The fixed envelope will invert the exact trade-weight /
  trailing-dollar-volume relationship at declared participation ceilings.
- 2026-07-25 — Capacity is contextual until a caller supplies an explicit
  capital mandate. High capacity can otherwise reward an inactive strategy, so
  it cannot enter candidate dominance.
- 2026-07-25 — V1 will not invent an OHLCV impact curve. It reports a
  participation envelope and its limitations instead.

## Verification

- Focused Portfolio, explorer, matrix, CLI, Report, and Dossier tests passed
  across 25 applicable test cases.
- `uv run python -m unittest discover -s tests -v` passed all 147 tests in
  329.457 seconds.
- `uv run python scripts/check_doc_links.py` resolved all 450 documentation
  double-links.
- `node --check autoquant/studio_assets/studio.js`,
  `uv run python -m compileall -q autoquant`, and `git diff --check` passed.
- A wheel installed into a fresh Python 3.11 virtual environment, created a
  Portfolio Project, executed a Run, and projected a verified
  `$2,680,522.92` validation 1% capacity tenth percentile through the installed
  CLI.
- In-app browser QA at `http://127.0.0.1:8773/` confirmed the four-column
  Portfolio summary, `$2.6805M` validation capacity, `100%` coverage, the
  latest `$24.8948M` rebalance envelope, `ECHO` binding asset, no horizontal
  overflow, and no application warnings or errors.

## Progress log

- 2026-07-25 — Plan created after the professional workflow gap audit.
- 2026-07-25 — Added causal ADV20 capacity evidence, strict artifact
  reconciliation, public projections, context-only comparison descriptors,
  and legacy fallback.
- 2026-07-25 — Completed focused/full tests, package smoke, documentation
  audit, and visible Studio QA.

## Completion

Completed with every acceptance item backed by executable evidence. The final
implementation commit records the exact repository state.
