# Caller-owned benchmark reference

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/caller-owned-benchmark-reference]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/portfolio-construction-lab]], and
  [[docs/design/program-research-dossiers]].

## Outcome

Let an OpenAlice or local caller state whether a delegated equity question
should be judged against cash or one named asset such as SPY, then make Factor-
to-Portfolio and governed-RL evidence use, audit, explain, and hand off that
exact reference without granting the benchmark asset position authority.

## Context

The current Mandate derives a benchmark only from direction. A long AAPL/MSFT
request is always compared with equal-weight AAPL/MSFT; neutral requests are
always compared with cash. That is reproducible but does not necessarily match
the caller's opportunity cost.

A support requester often needs to know whether a proposed book adds value
over a market or sector reference. The benchmark is part of the question, not
a candidate-tunable strategy input and not an instruction to trade it.

## Scope

### In scope

- Add an optional strict `benchmarkPolicy` to the Research Request with
  `cash` and named `asset` modes.
- Require a named benchmark to exist in the locked dataset universe.
- Derive one structured complete benchmark contract inside the immutable
  Portfolio Mandate, including source, kind, asset, and full-universe weights.
- Compute every Portfolio and governed-RL benchmark return from the same
  content-locked weight vector.
- Preserve the benchmark through performance metrics, daily ledgers,
  Explorer, Studio, Reports, Dossiers, and OpenAlice handoff.
- Prove that a context-only SPY benchmark never becomes a permitted position.

### Out of scope

- Dynamic benchmarks, factor models, custom indices, signed or leveraged
  benchmark baskets, risk-free-rate feeds, and live UTA opportunity cost.
- Letting candidate factor or RL encoder code choose the benchmark.

## Acceptance

- [x] Strict request and Mandate validation reject malformed, missing, unknown,
  or tampered named benchmarks.
- [x] Omission preserves an explicit direction-derived reference; caller cash
  and single-asset references are content-derived and immutable.
- [x] Portfolio and every governed-RL sleeve use the identical full-universe
  benchmark weights for daily returns and professional active metrics.
- [x] A named context-only benchmark remains zero-cap, non-tradable, and absent
  from mechanical position signals.
- [x] Explorer, Studio, Reports, and Dossiers clearly state benchmark source,
  method, asset, and no-trading-authority boundary.
- [x] A deterministic AAPL/MSFT versus SPY fixture reconciles benchmark returns,
  Portfolio/RL metrics, schemas, complete regression, and package build.

## Work

- [x] Audit request, Mandate, Portfolio accounting, RL, Explorer, Studio, and
  handoff paths for hard-coded direction benchmarks.
- [x] Define caller/Core/Agent authority and bounded cash/single-asset scope.
- [x] Implement strict request and content-derived Mandate contracts.
- [x] Replace branch-based benchmark accounting with the fixed weight vector.
- [x] Update all verified read and handoff surfaces.
- [x] Complete focused/full verification, commit, and push.

## Findings and decisions

- 2026-07-27 — The dataset universe, not `request.assets`, owns benchmark
  availability. A benchmark may intentionally remain context-only.
- 2026-07-27 — A benchmark is evaluation context. It never expands
  `tradableAssets`, position caps, permitted signals, or trading authority.
- 2026-07-27 — V1 supports cash and one unlevered long asset. This covers the
  common cash/SPY/QQQ support question without prematurely creating a custom
  index DSL.
- 2026-07-27 — Omission remains explicit and direction-derived; it is not
  treated as caller intent.

## Verification

- `uv run python -m unittest discover -s tests -v` — 217 tests passed in
  1458.153 seconds.
- The deterministic caller-SPY intake acceptance reconciled every published
  daily benchmark return to the locked SPY next-bar return and verified
  Portfolio, governed-RL, Studio, Report, and Dossier semantics.
- `uv run python -m compileall -q autoquant tests` — passed.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `uv run python -m unittest tests.test_documentation -v` — passed.
- `git diff --check` — passed.
- `uv build --out-dir /tmp/autoquant-v2-dist-20260727-benchmark` — built the
  wheel and source distribution successfully.

## Progress log

- 2026-07-27 — Plan activated after a request-to-handoff product audit showed
  that active metrics were reproducible but could not express the caller's
  actual opportunity-cost asset.
- 2026-07-27 — Added strict cash/single-asset request policies, complete
  content-derived Mandate weights, and one shared Portfolio/RL accounting
  path.
- 2026-07-27 — Carried the benchmark source and evaluation-only role through
  Explorer, Studio, Report, Dossier, and OpenAlice-facing documentation.
- 2026-07-27 — Completed deterministic caller-SPY acceptance, all 217
  repository tests, syntax/link checks, and package construction.

## Completion

Completed on 2026-07-27. A caller can now choose cash or one dataset-universe
asset as the immutable evaluation reference. The reference changes relative
evidence and Run identity while leaving tradable assets, caps, signals,
positions, costs, and governed-RL rewards unchanged.
