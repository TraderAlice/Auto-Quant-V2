# Make one Portfolio Run explorable as a quantitative decision surface

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/portfolio-decision-explorer]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/signal-policy-and-attribution]], and
  [[docs/design/studio-observation-surface]].

## Outcome

A human or Agent can inspect one verified immutable Portfolio Run through a
bounded Core/CLI contract and understand performance path, drawdown, exposure,
turnover/cost, current target versus executed weights, mechanical signal
events, and per-asset return/risk contribution without opening arbitrary
artifact files or granting Studio evaluation authority.

## Context

The Portfolio Judge already emits professional aggregate metrics and complete
daily/asset ledgers. Studio currently projects only a small metric ribbon, so
the evidence a real quantitative researcher needs to diagnose why a strategy
won or failed remains buried in CSV. Letting browser JavaScript parse arbitrary
Run paths would duplicate validation, make snapshots unbounded, and weaken the
Core/Studio authority boundary.

The next step is one strict domain read model over the existing immutable
artifacts. It must preserve validation versus visible-test semantics, use the
exact fixed mechanical state/weight/contribution ledger, and remain small
enough for frequent local Studio refresh.

## Scope

### In scope

- Strict verified loading of the five fixed Portfolio artifacts.
- Deterministic bounded sampling of full-history performance, drawdown,
  exposure, turnover, costs, and executed weights.
- Current proposed/executed book, signal state/action/reason, and recent
  mechanical transitions.
- Validation/test per-asset contribution and risk evidence.
- A discoverable read-only CLI/schema plus latest-Run Studio projection.
- A dependency-free browser explorer using only Core-projected values.

### Out of scope

- Recomputing Judge metrics, changing selection, opening arbitrary artifacts,
  comparing many Runs, live positions/orders, or Broker/UTA state.
- Production covariance optimization, capacity/impact models, or intraday
  execution charts.

## Acceptance

- [x] Core rejects missing, malformed, oversized, misaligned, non-finite, or
      non-Portfolio artifact sets with structured errors after immutable Run
      verification.
- [x] A bounded diagnostics object preserves exact Run/artifact identity,
      selection/test roles, full-history derived path anchors, current book,
      recent transitions, and validation/test attribution.
- [x] `aq run portfolio --json` and its JSON Schema/capability descriptor are
      machine-discoverable and deterministic for a caller-selected point cap.
- [x] Studio shows latest verified Portfolio performance/drawdown, exposure
      and position state, attribution, and transition evidence without reading
      artifacts in the browser.
- [x] Synthetic and real Yahoo Portfolio Runs reconcile against their source
      artifacts; invalid categories never become display claims.
- [x] Routine tests, browser QA, full regression, and isolated wheel smoke
      remain bounded.

## Work

- [x] Audit current artifacts and choose a Core-owned bounded projection over
      browser-side CSV access.
- [x] Implement strict artifact parsing, alignment, sampling, and diagnostics
      schema.
- [x] Add CLI discovery and latest-Run Studio projection/explorer.
- [x] Complete regressions, real-data/browser/wheel evidence, docs, and
      acceptance audit.

## Findings and decisions

- 2026-07-24 — The fixed artifacts already carry the required truth:
  `daily-portfolio.csv`, proposed/executed weights, long-form decisions, and
  `portfolio-report.json`. No new backtest metric is needed for this UI layer.
- 2026-07-24 — Studio will receive only the latest successful Portfolio Run
  diagnostics per Project. Historical selection remains an explicit CLI
  operation so Workspace polling stays bounded.
- 2026-07-24 — Full-history summary includes all fixed splits; selection and
  visible-test attribution remain separate. The browser labels this scope and
  never promotes the resulting historical book to live holdings.

## Verification

- `uv run python -m unittest discover -s tests -v` — 106 tests passed in
  143.249 seconds.
- `uv run python scripts/check_doc_links.py` — 268 links resolved.
- Draft 2020-12 schema validation passed against the real Yahoo diagnostics
  object at the minimum 40-point cap.
- Real Yahoo Run `run-20260724T051917800917Z-9b8d72896b38` projected 1,253
  reconciled daily rows into bounded 40/64/180-point views with no diagnostic
  failures.
- In-app browser QA verified the Performance/Exposure and
  Validation/Test-audit controls, audit labels, five-asset current book, and
  recent transition ledger at `127.0.0.1:8766`.
- An isolated `auto_quant-0.1.0` wheel loaded the same real Run through
  `aq run portfolio --points 64` and `aq studio snapshot`.

## Progress log

- 2026-07-24 — Activated after live Yahoo Studio review showed aggregate
  metrics but not the position, path, signal, and attribution evidence needed
  to diagnose them.
- 2026-07-24 — Implemented strict Core projection, public CLI/schema,
  latest-Run Studio explorer, dependency-free SVG views, tests, and packaged
  documentation.

## Completion

Completed 2026-07-24. The fixed Portfolio Lab now has one shared bounded
decision surface for Agents and humans without weakening immutable evidence,
selection integrity, or trading-authority boundaries.
