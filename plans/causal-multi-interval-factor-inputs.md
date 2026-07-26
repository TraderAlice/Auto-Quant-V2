# Add causal multi-interval factor inputs

- Status: `completed`
- Updated: `2026-07-26`
- Related design: [[docs/design/causal-multi-interval-factor-inputs]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/ohlcv-factor-lab]],
  [[docs/design/portfolio-construction-lab]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

One content-locked AutoQuant Project can research a base 1h decision clock
using completed 3h, 4h, 6h, 12h, and 1d OHLCV context through the existing
ordinary pandas candidate API. Factor, Portfolio, and governed RL consume the
same causally aligned feature surface; no higher-interval value is visible
before its bar closes.

## Context

V1 request intake accepts `frequency: 1d` only, writes one
`data/ohlcv/<asset>.csv`, and every reference Judge passes that one frame to
`compute_factor(frame)`. This is too narrow for real research: a 1h decision
may need daily regime, 12h trend, 6h volatility, and 3h activity context.

Simply joining provider files on labels is unsafe. Vendors differ on whether a
timestamp means bar open or close, interval anchors differ across UTC,
exchange sessions, and daylight saving time, and forward-filled higher bars
leak incomplete information. The Harness must own those semantics.

## Scope

### In scope

- Preserve V1 daily package/Project compatibility.
- Define a strict V2 multi-interval package and snapshot with base interval,
  requested derived intervals, bar-close timestamp semantics, clock,
  timezone/session anchor, and aggregation identity.
- First support a 1h continuous UTC base with exact completed
  3h/4h/6h/12h/1d aggregates.
- Materialize every interval under a content-locked Project data closure.
- Build one ordinary pandas candidate frame whose base OHLCV columns remain
  unchanged and whose completed higher-interval fields are namespaced.
- Include source bar-close and age/provenance columns so availability is
  auditable.
- Use backward-as-of visibility only; never expose a forming bar.
- Make Factor, Portfolio, RL, preflight, Run identity, Report, Dossier, and
  Studio disclose the interval surface.
- Add known-leak, boundary, missing-bar, aggregation, alignment, and
  cross-lane consistency tests with bounded fixtures.

### Out of scope

- Tick/L2/order-book data.
- Provider-specific websocket ingestion.
- Arbitrary non-integral interval conversion.
- Silent forward-fill of missing base bars.
- Session-market intraday aggregation before an explicit exchange calendar,
  early-close, DST, and partial-session contract exists.
- Selecting intervals from visible test performance.
- Giving RL access to a different data surface than mechanical baselines.

## Acceptance

- [x] V1 daily packages, snapshots, Studies, and historical Runs remain valid
      in focused regression.
- [x] A strict V2 package locks base/derived interval and bar-close semantics.
- [x] Derived OHLCV exactly reconciles to complete base-bar groups.
- [x] At decision close `t`, every joined high-period source close is `<= t`;
      a bar ending after `t` is unavailable, not partially filled.
- [x] Candidate code still uses ordinary pandas `compute_factor(frame)`.
- [x] Factor, Portfolio, and governed RL consume byte-identical aligned factor
      inputs and disclose their interval surface.
- [x] Prefix/future-withholding tests reject representative cross-interval
      leakage and pass a causal multi-horizon baseline.
- [x] OpenAlice intake/report handoff records the intervals requested,
      materialized, locked, and supplied without turning them into trading
      authority. Arbitrary pandas column use is deliberately not inferred.
- [x] Bounded CLI, schema, package, docs, Studio, and full regression pass
      before commit and push.

## Work

- [x] Audit existing V1 intake, dataset identity, candidate APIs, and Judge
      timestamp assumptions.
- [x] Choose one shared causally joined pandas frame instead of an engine- or
      lane-specific multi-timeframe strategy API.
- [x] Implement strict interval/clock primitives and aggregation fixtures.
- [x] Extend intake/package/snapshot contracts compatibly.
- [x] Integrate the shared aligned frame into Factor, Portfolio, and RL.
- [x] Add evidence disclosure, Studio projection, tests, docs, and release
      verification.

## Findings and decisions

- 2026-07-26 — Keep `compute_factor(frame) -> Series`. Fixed Harness code
  should own interval materialization and causal alignment; editable AI code
  should receive ordinary inspectable pandas columns.
- 2026-07-26 — Timestamps mean bar close in V2. Higher intervals join with
  backward-as-of semantics only after completion.
- 2026-07-26 — Start with continuous UTC 1h because 3h/4h/6h/12h/1d are exact
  multiples with unambiguous midnight anchors. Session-market intraday support
  requires a separate explicit exchange-calendar contract, not crypto-like
  modulo arithmetic.
- 2026-07-26 — All lanes share one aligned surface. RL may learn how to weight
  multi-horizon factor sleeves, but cannot receive privileged timestamps or a
  different feature history.
- 2026-07-26 — Do not pretend arbitrary pandas column use is observable.
  Evidence records the surface supplied to the candidate. A future semantic
  usage declaration, if needed, must be explicit and fixed rather than guessed
  from source text.
- 2026-07-26 — Portfolio and RL use 8760 annualization periods on the exact
  continuous 1h clock; V1 daily behavior remains 252.
- 2026-07-26 — Materialized higher bars are cache/evidence, not independent
  authority. Intake and every Judge reaggregate from the locked 1h file and
  reject even rehashed divergence.

## Verification

- `tests.test_intervals`: 5 deterministic aggregation/alignment tests pass.
- V2 rehashed-derived-bar tamper test passes in 0.53 seconds.
- One 420-hour, five-asset research desk passed CandidateCheck, executed
  Factor, Portfolio, and governed RL, loaded all three evidence Explorers, and
  rendered a valid Studio snapshot on one dataset hash and interval surface in
  71.35 seconds; Portfolio/RL annualization is 8760.
- `uv run python scripts/check_doc_links.py`: 665 links resolve.
- `uv build`: source distribution and wheel built; the wheel contains interval
  Core and both multi-horizon candidate templates.
- `uv run python -m unittest discover -s tests -v`: 190 tests passed in
  1114.337 seconds.

## Progress log

- 2026-07-26 — Plan activated after user feedback requested 1h decisions with
  3h/4h/6h/12h/1d factor context.
- 2026-07-26 — Implemented strict V2 package/snapshot materialization,
  completed-bar aggregation, causal alignment, shared Judge loading,
  RunResult disclosure, and continuous-hourly annualization.
- 2026-07-26 — Initial multi-horizon baseline failed prefix causality because
  it attached a carried high-period value to the last observed row. Rebinding
  returns by exact `bar_close__<interval>` removed sample-length dependence and
  passed the fixed audit.

## Completion

Completed on 2026-07-26. V1 daily intake remains readable and behaviorally
compatible. V2 now fixes a continuous UTC 1h authority, deterministic
completed-bar aggregation, causal namespaced pandas alignment, shared
Factor/Portfolio/RL use, 8760-period risk and performance semantics, immutable
RunResult/OpenAlice disclosure, and bounded tamper/leak/Studio evidence. A
future session-market intraday contract remains intentionally separate.
