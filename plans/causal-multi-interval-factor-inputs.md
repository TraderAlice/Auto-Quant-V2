# Add causal multi-interval factor inputs

- Status: `active`
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

- [ ] V1 daily packages, snapshots, Studies, and historical Runs remain valid.
- [ ] A strict V2 package locks base/derived interval and bar-close semantics.
- [ ] Derived OHLCV exactly reconciles to complete base-bar groups.
- [ ] At decision close `t`, every joined high-period source close is `<= t`;
      a bar ending after `t` is unavailable, not partially filled.
- [ ] Candidate code still uses ordinary pandas `compute_factor(frame)`.
- [ ] Factor, Portfolio, and governed RL consume byte-identical aligned factor
      inputs and disclose their interval surface.
- [ ] Prefix/future-withholding tests reject representative cross-interval
      leakage and pass a causal multi-horizon baseline.
- [ ] OpenAlice intake/report handoff records what intervals were requested,
      available, used, and unavailable without turning them into trading
      authority.
- [ ] Bounded CLI, schema, package, docs, Studio, and full regression pass
      before commit and push.

## Work

- [x] Audit existing V1 intake, dataset identity, candidate APIs, and Judge
      timestamp assumptions.
- [x] Choose one shared causally joined pandas frame instead of an engine- or
      lane-specific multi-timeframe strategy API.
- [ ] Implement strict interval/clock primitives and aggregation fixtures.
- [ ] Extend intake/package/snapshot contracts compatibly.
- [ ] Integrate the shared aligned frame into Factor, Portfolio, and RL.
- [ ] Add evidence disclosure, Studio projection, tests, docs, and release
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

## Verification

Pending.

## Progress log

- 2026-07-26 — Plan activated after user feedback requested 1h decisions with
  3h/4h/6h/12h/1d factor context.

## Completion

Pending.
