# Configurable base intervals and session-market inputs

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/configurable-session-interval-inputs]],
  [[docs/design/causal-multi-interval-factor-inputs]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/design/portfolio-construction-lab]].

## Outcome

Let one request-driven AutoQuant Project choose a content-locked base bar
interval instead of requiring `1h`, and let US-equity research consume
calendar-verified XNYS intraday bars plus completed session-aligned higher
intervals without treating overnight gaps, DST, or early closes as bad data.

## Context

The implemented V2 multi-interval surface is deliberately narrow:

```text
continuous UTC 1h
→ fixed UTC-midnight 3h/4h/6h/12h/1d
```

That proved the causal pandas interface but makes two incorrect assumptions
for broader use:

1. research cadence is always one hour;
2. every missing wall-clock hour is a data gap.

The first assumption prevents shorter or slower decision clocks. The second
would reject every US-equity overnight/weekend boundary and would build false
daily bars if simply disabled.

## Scope

### In scope

- Add a V3 dataset package/snapshot while preserving exact V1 and V2
  serialization and verification.
- Support explicit continuous-market base intervals from a bounded canonical
  set, with higher intervals required to be larger exact multiples.
- Support the XNYS regular session with version-locked exchange schedule
  authority, including holidays, DST, and scheduled early closes.
- Treat session `1d` as one exchange session and disclose short terminal
  intraday buckets that complete at market close.
- Generalize derived-bar aggregation, causal backward alignment,
  `age_bars__*`, materialization, reload reconciliation, Run interval evidence,
  and annualization.
- Preserve the ordinary pandas `compute_factor(frame)` surface across Factor,
  Portfolio, and governed RL.
- Add deterministic continuous/session fixtures and bounded real-lane tests.

### Out of scope

- Premarket, after-hours, auctions, unscheduled exchange halts, or vendor
  correction feeds.
- Arbitrary calendars, futures sessions spanning midnight, split sessions,
  or every possible duration string.
- Downloading market data or claiming that provider adjustment/calendar
  metadata is true.
- Changing strategy selection, Portfolio construction, or trading authority.

## Acceptance

- [x] V1 daily and V2 fixed-1h Projects retain their exact contracts and tests.
- [x] V3 continuous intake accepts every documented base interval, rejects
  non-divisible/earlier feature intervals, and remains prefix-causal.
- [x] V3 XNYS intake accepts exact regular-session panels across DST and early
  closes while rejecting missing, extra, off-calendar, or misclosed bars.
- [x] Session aggregation reconciles OHLCV to exact base rows; `1d` closes at
  the scheduled exchange close and forming higher bars remain invisible.
- [x] Factor, Portfolio, and governed-RL Judges consume the same V3 pandas
  surface and publish the exact interval/calendar authority in Run evidence.
- [x] CLI schemas/docs, focused tests, complete regression, package build, and
  Studio/browser observation pass.

## Work

- [x] Audit the fixed V2 interval/intake/Run/Judge contracts and runtime
  dependency surface.
- [x] Define V3 compatibility, interval algebra, XNYS schedule authority,
  terminal-bucket semantics, and explicit non-goals.
- [x] Implement the generalized Core interval surface and calendar-aware
  validators/aggregators.
- [x] Implement V3 intake, materialization, reload reconciliation, schemas,
  Run evidence, and annualization.
- [x] Add continuous and XNYS fixtures spanning early close and DST, then run
  all three real research lanes.
- [x] Update canonical docs and Studio interval presentation.
- [x] Run focused/full/browser/build verification, complete, commit, and push.

## Findings and decisions

- 2026-07-27 — V2 remains immutable compatibility evidence. Configurable
  cadence and session clocks enter through schema V3 rather than changing the
  meaning or hashes of an existing package.
- 2026-07-27 — `exchange-calendars` supplies only the version-locked XNYS
  schedule. AutoQuant still validates every expected base close, aggregates
  OHLCV, aligns completed bars, and content-locks all materialized bytes.
- 2026-07-27 — XNYS V3 covers regular sessions only. A terminal bucket shorter
  than its nominal interval is complete exactly at the scheduled session close
  and is explicitly identified by the interval-surface method.
- 2026-07-27 — Bounded interval identifiers are preferable to an arbitrary
  duration parser in the public contract; unsupported cadence fails before
  Project creation.

## Verification

- `uv run python -m unittest tests.test_intervals tests.test_mandates
  tests.test_runs ...` — 23 focused contract and real-lane tests passed.
- `uv run python -m unittest discover -s tests` — 206 tests passed in
  1353.037 seconds, including Studio assets/read models and all three XNYS
  research lanes.
- `uv run python -m compileall -q autoquant tests` — passed.
- `git diff --check` — passed.
- `uv run aq schema ohlcv-dataset-package --json` and
  `uv run aq schema run-result --json` — passed; package schema advertises V3
  and every bounded base interval.
- `uv build` — source distribution and wheel built successfully.

## Progress log

- 2026-07-27 — Plan created after confirming the current implementation fixes
  the base interval, UTC continuity, and midnight aggregation in one V2
  contract and has no installed exchange-calendar authority.
- 2026-07-27 — Added pinned `exchange-calendars`, generalized continuous
  aggregation/alignment, and implemented strict XNYS schedule validation with
  DST, holiday, early-close, and terminal-partial-bar semantics.
- 2026-07-27 — Published V3 through Intake, snapshots, RunResult, Portfolio
  annualization, Factor component claims, Studio evidence, schemas, and
  canonical documentation.
- 2026-07-27 — Proved one `15m` continuous Factor Project and one five-asset
  XNYS research desk whose Factor, Portfolio, and governed-RL Runs all
  succeeded on the same surface.

## Completion

AutoQuant now treats cadence and market clock as content-locked research
authority. Continuous projects can choose a bounded base interval; US-equity
projects can use exact XNYS regular-session bars without mistaking overnight,
DST, holiday, or early-close structure for missing data. Every research lane
and OpenAlice-facing evidence projection consumes the same causally aligned
pandas surface.
