# Calendar-derived daily close-time packaging

- Status: `completed`
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

- [x] The public Skill materializes a strict V4 daily source into V5 using only
  explicit per-asset calendar authority and unchanged OHLCV rows.
- [x] The audit proves every input/output hash and exact scheduled-close
  transformation, including real XNYS DST and XTKS close-time changes.
- [x] Invalid authority, calendar, session, path, output, or source-package
  cases fail without publishing a partial success package.
- [x] The generated V5 package passes audit, strict Project intake, Factor Run,
  Explorer, and immutable Report publication.
- [x] Public Skill guidance makes the V4 acquisition → close-time materialize
  → V5 audit/intake route discoverable without implementation inspection.
- [x] A fresh installed-wheel Grok coworker completes one bounded cross-market
  daily assignment from the date-based source package and stops truthfully on
  the resulting evidence.
- [x] Focused tests, full regression, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.25`.

## Work

- [x] Define the strict authority manifest and deterministic transformation.
- [x] Implement the bundled Skill procedure and negative checks.
- [x] Add source-to-V5-to-Report integration tests and public guidance.
- [x] Refresh version/sample evidence and run a fresh installed-wheel field
  assignment.
- [x] Complete the release audit, commit, tag, push, and verify `v0.9.25`.

## Findings and decisions

- 2026-08-02 — The package author remains the timestamp authority. A bundled
  Skill may apply an explicit, audited calendar mapping; Core still validates
  only the already-materialized V5 timestamps and preserves no hidden calendar
  inference.
- 2026-08-02 — The first procedure accepts one V4 package so provider,
  adjustment, and retrieval provenance remain singular and exact. Combining
  independently acquired packages would require truthful per-source
  provenance rather than a synthetic top-level provider claim.
- 2026-08-02 — V5 has one fixed `provider-observed`/UTC top-level market
  surface. The source V4 market claim is therefore preserved in the
  transformation audit rather than copied into V5; per-asset venue, class,
  explicit calendar, timezone, and volume authority remain exact.

## Verification

- Focused CLI, Studio, repository-Workspace, documentation, and bundled-Skill
  coverage passed 45 tests before the complete gate.
- The first complete pass exposed only two stale assertions that hard-coded
  current runtime version `0.9.24`; current-surface tests now compare with the
  package version authority while immutable historical Run identities remain
  exact. Both corrected tests passed independently.
- `uv run python -m unittest discover -s tests -q` passed all 437 tests in
  1,058.463 seconds. `uv lock --check`, Python compilation, `git diff --check`,
  and all 1,455 documentation links passed.
- Candidate commit `6b41714` built wheel SHA
  `e23da3b412ba94eb8f1766dd5c82721bd7799ab54c138e83fa1728026e5480f8`
  and sdist SHA
  `af3514a4d6234c7aa75b7decd4ef7949d2b5c8cf783cf7228df34ad9b8572d45`.
  Both distributions contain the public materializer; the wheel contains the
  canonical 16-Skill runtime bundle and embedded build identity.
- A fresh Python 3.11.14 wheel install reported `0.9.25`, clean embedded commit
  `6b417145d636df1c06f43cc53a74a2a55f983702`, runtime source hash
  `b1b83f033c20cb5a8bd4bcd269bd2338e8b9cd8ee2463a11bb1ec28663d4a93f`,
  `exchange_calendars@4.13.2`, and usable public materializer help.
- A no-hardlink clone without `autoquant-workspace.local.json` selected only
  `sample-research-desk`, validated and oriented successfully, and projected
  three Studies and fourteen Runs through installed Studio with the same
  Harness identity.
- Final release commit, `main`, and annotated `v0.9.25` were published and
  verified at one remote identity.

## Progress log

- 2026-08-02 — Plan created from the private calendar-labeling setup required
  by the otherwise successful `0.9.24` Toyota/SPY field trial.
- 2026-08-02 — Added the transactional bundled materializer, strict authority
  contract, real XNYS DST/XTKS close-extension fixtures, negative failure
  cases, and a deterministic V4 → V5 → intake → Factor → Explorer → Report
  integration proof.
- 2026-08-02 — Version and generated discovery bundles advanced to `0.9.25`.
  The root sample retained thirteen prior Runs and added clean Factor Run
  `run-20260801T200541529080Z-beb54535a432` from candidate commit `643b713`
  with unchanged validation IC `-0.031325301204819286`.
- 2026-08-02 — A fresh Grok 4.5 coworker installed candidate wheel SHA
  `c9aec447fae6ef2c4be56395b24cdecd7e10a5f1d4ab93caad60a5cc280fb01e`
  and began only with strict date-only V4 package SHA
  `75085064eab0abe69bafb4be5a3accd386bb6a6eb60de09fbb5dce5b632f1adf`.
  It discovered the generated packaging Skill, authored explicit
  `exchange_calendars@4.13.2` XTKS/XNYS authority, invoked the public
  materializer, audited and ingested the V5 output, and wrote no private
  materialization program.
- 2026-08-02 — The coworker completed exactly one Study, Run, Session, and
  Report with no Portfolio, RL, or Dossier work. Run
  `run-20260801T201252981010Z-0a2cc8bfc271` recorded the clean installed
  `0.9.25` candidate at commit `f7c9ad5`; validation mean rank IC was
  `+0.014908` (HAC `t=0.29`, `p=0.77`) and visible-test mean rank IC was
  `-0.044436`. It stopped without tuning the candidate against test evidence.
- 2026-08-02 — Independent replay reconciled all 1,845 finite factor values,
  proved every context close was no later than its Toyota target, and proved
  none of 1,779 later same-date SPY closes entered the signal. Exact source
  dates, 1,847/1,903 row counts, and all numeric OHLCV values survived the V4
  to V5 transformation unchanged.

## Completion

Completed. An installed coding coworker can now start with a truthful
date-labelled daily package, apply explicit pinned exchange-calendar authority
through the public packaging Skill, and obtain an audited close-time-aware V5
package without private conversion code. The procedure changes no OHLCV value
or availability row, fails without partial publication, and preserves the
boundary that calendars are declared research authority rather than facts
silently inferred by Core.
