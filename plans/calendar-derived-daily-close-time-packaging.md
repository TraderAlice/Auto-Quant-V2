# Calendar-derived daily close-time packaging

- Status: `active`
- Updated: `2026-08-02`
- Target release: `0.9.25`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/design/versioning-and-release]].

## Outcome

Let an installed AutoQuant coworker turn one strict observed-only date-based
daily package plus explicit per-asset exchange-calendar authority into a fully
audited V5 close-time package through the public packaging Skill, without
writing a private materialization program or inventing nominal UTC close
times.

## Context

`0.9.24` made the Factor runtime and evidence chain correctly distinguish a
Tokyo close from a later same-date New York close. Its field setup still used
the one-off
`grok-field-trials/cohort-35-cross-market-daily-v0924/staging/prepare_close_time_package.py`
to convert Yahoo session dates into exact XTKS/XNYS scheduled closes before the
coworker entered the desk. The public `$package-autoquant-ohlcv` Skill explains
the required V5 authority but supplies only audit/comparison procedures, while
its own instructions forbid a private materialization script.

The missing product step is therefore narrow and observed: expose one
provider-neutral, fail-closed calendar-labeling procedure in the packaging
Skill. Core intake must continue to receive already-labeled timestamps and must
not become a downloader or calendar oracle.

## Scope

### In scope

- Add a bundled `materialize_daily_close_time.py` procedure invoked through
  `aq-python` from `$package-autoquant-ohlcv`.
- Accept one strict V4 observed-only daily source package and one explicit
  authority manifest mapping every asset to an `exchange_calendars` calendar,
  its exact timezone, and truthful V5 volume semantics.
- Preserve source OHLCV, asset class, venue, currency, provider, adjustment,
  retrieval time, terms, observed dates, and absent rows exactly; change only
  the date label into the matching scheduled session-close instant in UTC.
- Emit a complete V5 package, normalized per-asset CSVs, and a content-bound
  transformation audit recording source hashes, calendar library/version,
  timezone/calendar mapping, scheduled-close changes, output hashes, and
  limitations.
- Fail closed on non-session dates, unknown calendars, timezone or inventory
  mismatches, duplicate output closes, invalid source contracts, unsafe paths,
  symlinks, occupied output, or any OHLCV/value/row-count change.
- Prove both XNYS daylight-saving close changes and XTKS's November 2024 close
  extension with deterministic fixtures, strict V5 intake, Factor execution,
  Explorer, and Report publication.
- Publish `0.9.25`, refresh the root sample without rewriting old Runs, and
  run a fresh installed-wheel Grok assignment starting from date-based source
  data rather than a prebuilt V5 package.

### Out of scope

- Treating `exchange_calendars` as official exchange authentication or
  reconstructing unscheduled halts and exceptional closures.
- Inferring a calendar or timezone from venue/symbol, appending a fixed nominal
  clock time, silently dropping non-session rows, filling holidays, or aligning
  assets onto one calendar.
- Combining packages with different provider, adjustment, retrieval, or terms
  authority; multi-provider provenance needs a separate contract.
- Intraday bucket conversion, corporate-action correction, Portfolio/RL
  authority over asynchronous panels, or a Core downloader/calendar service.

## Acceptance

- [ ] The public Skill materializes a strict V4 daily source into V5 using only
  explicit per-asset calendar authority and unchanged OHLCV rows.
- [ ] The audit proves every input/output hash and exact scheduled-close
  transformation, including real XNYS DST and XTKS close-time changes.
- [ ] Invalid authority, calendar, session, path, output, or source-package
  cases fail without publishing a partial success package.
- [ ] The generated V5 package passes audit, strict Project intake, Factor Run,
  Explorer, and immutable Report publication.
- [ ] Public Skill guidance makes the V4 acquisition → close-time materialize
  → V5 audit/intake route discoverable without implementation inspection.
- [ ] A fresh installed-wheel Grok coworker completes one bounded cross-market
  daily assignment from the date-based source package and stops truthfully on
  the resulting evidence.
- [ ] Focused tests, full regression, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.25`.

## Work

- [ ] Define the strict authority manifest and deterministic transformation.
- [ ] Implement the bundled Skill procedure and negative checks.
- [ ] Add source-to-V5-to-Report integration tests and public guidance.
- [ ] Refresh version/sample evidence and run a fresh installed-wheel field
  assignment.
- [ ] Complete the release audit, commit, tag, push, and verify `v0.9.25`.

## Findings and decisions

- 2026-08-02 — The package author remains the timestamp authority. A bundled
  Skill may apply an explicit, audited calendar mapping; Core still validates
  only the already-materialized V5 timestamps and preserves no hidden calendar
  inference.
- 2026-08-02 — The first procedure accepts one V4 package so provider,
  adjustment, and retrieval provenance remain singular and exact. Combining
  independently acquired packages would require truthful per-source
  provenance rather than a synthetic top-level provider claim.

## Verification

Pending.

## Progress log

- 2026-08-02 — Plan created from the private calendar-labeling setup required
  by the otherwise successful `0.9.24` Toyota/SPY field trial.

## Completion

Pending.
