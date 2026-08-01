# Close-time-aware cross-market daily Factor

- Status: `active`
- Updated: `2026-08-02`
- Target release: `0.9.24`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/panel-native-factor-api]],
  [[docs/design/causal-multi-interval-factor-inputs]], and
  [[docs/design/versioning-and-release]].

## Outcome

Let one Factor-only temporal Study use daily bars from markets whose sessions
close at different UTC instants without collapsing them onto a shared date,
filling holidays, or exposing a context close before it actually completed.
Prove the contract with a fresh installed-wheel coworker studying a Tokyo
target from already-completed New York context.

## Context

V5 already preserves timezone-aware completed bar-close timestamps, ragged
observed-only rows, absent-no-fill semantics, exact per-asset classes, one
explicit temporal target, and a horizon measured on that target's own observed
bars. Those are the correct primitives for causal cross-market research.

The public contract nevertheless calls V5 “observed intraday” and rejects
`baseInterval: 1d` with `interval.base-unsupported`. V4 admits ragged daily
dates but has no close instant, so it cannot distinguish a Tokyo close from a
New York close on the same civil date. Forcing a cross-market question into V4
can therefore make same-date context look available several hours too early.

## Scope

### In scope

- Generalize V5 from observed intraday bars to observed base bars and admit
  `1d` alongside existing intraday intervals.
- Preserve strict UTC completed-bar-close timestamps, observed-only rows,
  absent-no-fill semantics, per-target-observed-bar horizons, per-asset class,
  one explicit temporal target, and Factor-only authority.
- Make schema, validation codes/messages, snapshot/readback, Candidate
  Contract, orientation, CLI, Studio, and docs describe the generalized
  surface consistently.
- Add deterministic asynchronous-market fixtures proving that context at a
  later close is invisible to an earlier target close, while the prior
  completed context close remains usable through causal candidate code.
- Prove target forward returns advance on target observations rather than
  union timestamps or a fabricated common calendar.
- Bump to `0.9.24`, refresh the root sample without rewriting old Runs, run a
  fresh installed-wheel Grok assignment, and publish only after full release
  audit.

### Out of scope

- Authenticating exchange calendars or deriving close timestamps from a
  provider's date-only file inside Core.
- Automatic forward-filling, implicit as-of joins, timezone guessing, FX
  conversion, holiday synthesis, or a universal global-calendar service.
- Portfolio/RL authority over asynchronous daily panels.
- Claiming causality, trading authority, or remote data authenticity from a
  timestamp contract.

## Acceptance

- [x] V5 accepts `baseInterval: 1d` and rejects naive, duplicate, unordered,
  non-finite, or non-OHLC bar-close input exactly as it does intraday input.
- [x] Existing V5 intraday behavior remains internally consistent under the
  generalized observed-bar naming and schema.
- [x] A deterministic Tokyo/New York fixture proves strict close-time
  visibility and target-observed horizon alignment without fill.
- [x] Public discovery and Agent guidance make the causal asynchronous-market
  pattern understandable without implementation inspection.
- [ ] Historical V1–V5 Projects and immutable evidence remain truthfully
  readable unless an intentional breaking contract is explicitly documented.
- [ ] A fresh installed-wheel Grok coworker completes one bounded cross-market
  daily Factor assignment and hands off the exact limitation/authority state.
- [ ] Focused tests, full regression, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.24`.

## Work

- [x] Generalize the observed-bar schema and implementation.
- [x] Add asynchronous close-time correctness and regression fixtures.
- [x] Update Agent, CLI, Project format, architecture, Studio, and design docs.
- [ ] Run a fresh installed-wheel cross-market field assignment.
- [ ] Refresh release evidence, publish, tag, and verify `v0.9.24`.

## Findings and decisions

- 2026-08-02 — V4 date-only daily authority is insufficient for cross-market
  lead/lag because civil-date equality does not establish information
  availability. V5's completed UTC close instant is the correct existing
  primitive.
- 2026-08-02 — Core will not manufacture an as-of-filled panel. Candidate code
  may use only context observations whose exact close timestamp is at or before
  the target decision timestamp; no-fill input and prefix causality audits stay
  authoritative.
- 2026-08-02 — Source availability and prediction evidence own different
  clocks. `factor-availability.csv` retains the complete asynchronous source
  union; daily IC, targets, splits, and purge evidence retain the target's
  observed clock. Explorer reconciliation must not require those complete
  timelines to be identical.

## Verification

Pending.

## Progress log

- 2026-08-02 — Current `0.9.23` public intake reproduced
  `interval.base-unsupported` for an otherwise V5-shaped `1d` package. The
  accepted interval list stops at `12h` even though V5's other semantics are
  already appropriate for daily asynchronous markets.
- 2026-08-02 — V5 now accepts `1d`; Candidate Contract, CLI, and Studio expose
  completed-close timestamp meaning, ragged/no-fill shape, causal context
  visibility, and the target-owned clock. A deterministic Toyota/SPY fixture
  proves that the later same-date New York close remains invisible at Tokyo
  close while the prior completed close is usable through explicit backward
  as-of code.
- 2026-08-02 — The asynchronous fixture exposed a Run-evidence bug: temporal
  projection erased fully offset context before availability reporting and
  attempted to index an empty series. The Factor Judge now reports source-panel
  availability separately from the target evaluation timeline.
- 2026-08-02 — The first installed `0.9.24` Grok 4.5 candidate trial authored
  the correct explicit backward-as-of SPY context and completed one negative
  Run, but normal Report publication exposed a second clock-coupling defect:
  aggregate availability described the 3,749-row source union while its CSV
  still described Toyota's 1,847-row prediction clock. Grok used a runtime
  monkeypatch to omit optional leader decision support, so this attempt is
  diagnostic evidence rather than a passing employability trial. The Judge,
  Explorer, and Run-to-Report regression are being corrected before a fresh
  installed-wheel retry.

## Completion

Pending.
