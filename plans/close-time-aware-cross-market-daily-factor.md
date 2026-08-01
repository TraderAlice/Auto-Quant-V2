# Close-time-aware cross-market daily Factor

- Status: `completed`
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
- [x] Historical V1–V5 Projects and immutable evidence remain truthfully
  readable unless an intentional breaking contract is explicitly documented.
- [x] A fresh installed-wheel Grok coworker completes one bounded cross-market
  daily Factor assignment and hands off the exact limitation/authority state.
- [x] Focused tests, full regression, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.24`.

## Work

- [x] Generalize the observed-bar schema and implementation.
- [x] Add asynchronous close-time correctness and regression fixtures.
- [x] Update Agent, CLI, Project format, architecture, Studio, and design docs.
- [x] Run a fresh installed-wheel cross-market field assignment.
- [x] Refresh release evidence, publish, tag, and verify `v0.9.24`.

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

- Clean retry candidate commit:
  `2868f4aefa72a591834ff771abf5395c5208380b`.
- Wheel:
  `auto_quant-0.9.24-py3-none-any.whl`, SHA-256
  `25213600792e4b68a2e414f7823b097a204238e9071e22e8e8edfbea5dfcdd13`.
  Installed identity was `autoquant.python-judge@0.9.24`, embedded clean commit
  `2868f4a`, Python `3.11.14`, runtime source hash
  `ee73ba7f2a81d034e255f2081997afedb2f4baea03c2c8404a70562aa5ee604c`.
- Fresh Grok 4.5 retry:
  `/Users/ame/2607AutoQuant/grok-field-trials/cohort-36-cross-market-daily-v0924-retry`.
  It completed in 16 model turns using only the installed public surface and
  produced exactly one Factor Study, Run, Session, and Report, with no
  Portfolio, RL, or Dossier lane.
- Immutable identities:
  Run `run-20260801T191512297218Z-ac8a044f8273`, Session
  `session-20260801T191512863288Z-011c79dc60db`, Report
  `report-20260801T191714694932Z-56274f8f184a`, completion
  `completion-20260801T191721941073Z-ac030b682110`.
- Independent public CLI verification passed Workspace validation,
  orientation, strict Run/Factor/Report/Session readers, and Studio snapshot.
  Explorer reconciled 3,749 source-union timestamps, 1,847 Toyota target
  timestamps, 3,749 observed rows, and 0.5 ragged observation coverage.
- Independent candidate replay reconciled every one of 1,845 finite Toyota
  factor rows to the most recent SPY return whose completed close was no later
  than the Toyota close. All 1,778 Toyota rows with a later same-civil-date SPY
  close ignored that unavailable observation.
- The research result was correctly negative: validation mean rank IC
  `0.014908492563816994`, HAC t `0.2901765741438921`, p
  `0.7716811566958051`, with chronological folds `0.11135016641709361` and
  `-0.07202354808686726`; visible test audit mean IC was
  `-0.0444362920627448`. The Agent reported that the candidate is not useful
  decision support and stopped without retuning.
- Field audit SHA-256:
  `823892b846db642723ed8594f3b205f4f07080b1afa4a30749bd37b3bf4a0cbb`;
  Grok event log SHA-256:
  `c23f7821a70559dda37b318614eb04facc64d943fa747c6baa563edc18f1cb18`.
- Full regression: 433 tests in 1,076.723 seconds, all passing. This includes
  V1–V5 intake, legacy Factor decision-support readback, all thirteen sample
  Runs, the asynchronous Run-to-Explorer-to-Report path, and the complete
  Factor/Portfolio/RL/Session/Report/Review/Dossier surfaces.
- Documentation graph: 1,436 links resolved. `uv lock --check`, Python
  byte-compilation, Studio JavaScript syntax, and diff whitespace checks pass.
- Post-audit clean candidate commit:
  `6b190d558ec7c692aa12c9436d1fb5980ecc16df`. Its wheel SHA-256 was
  `b2d5738d79da93cca14f0eccb3cc28e533d45c034628ddbb4a9a8d3f58b27416`
  and sdist SHA-256 was
  `0f2e370796a834b2ec2268538f6c44e14eda496c6edb4f163379271c449fb186`.
  A fresh Python 3.11.14 installation reported that exact embedded clean
  commit and the same runtime closure hash as the field candidate. Capability
  discovery returned the identical seven-field Harness object.
- A no-local-override clone at that commit was clean, discovered only
  `sample-research-desk`, selected it by default, validated successfully, and
  projected three Studies and all thirteen Runs through Studio.
- Final release commit, `main`, and annotated `v0.9.24` were published and
  verified at one remote identity.

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
- 2026-08-02 — After the source-union availability correction, a second fresh
  installed-wheel Grok 4.5 coworker completed the same bounded assignment in
  16 turns through public APIs only. Normal Report publication and Session
  completion passed with one immutable Run. The coworker preserved the weak,
  unstable negative answer and did not retune against visible test evidence.

## Completion

Completed. AutoQuant now admits exact completed daily close instants into the
observed-only Factor contract, keeps asynchronous source availability distinct
from the target clock, and lets a fresh installed-wheel coworker answer one
Tokyo/New York lead/lag question through a normal immutable Report handoff
without civil-date look-ahead or trading authority.
