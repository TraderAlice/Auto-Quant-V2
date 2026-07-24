# Turn a real research request into a content-locked Project

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/study-run-evidence]].

## Outcome

An OpenAlice or local caller can provide one strict research request and one
bounded daily-OHLCV dataset package, then atomically create a self-contained
Factor, Portfolio, or governed-RL Project whose exact real-market bytes,
provenance, universe, Study, next actions, and Studio state are verifiable.

## Context

AutoQuant already preserves a delegated request once a compatible Study and
Project exist. The reference Labs, however, are fixed synthetic `ALPHA` through
`FOXTROT` fixtures. A request for actual listed assets therefore cannot cross
the request → Project boundary without manual file copying and Study rewrites.
That breaks the workbench collaboration model precisely where caller intent
should become reproducible quantitative work.

The next step is not a network downloader or universal market-data platform.
It is a strict intake boundary for caller-supplied OHLCV snapshots. Core should
normalize and content-lock those bytes inside the new Project, disclose what
the provider says the prices represent, and refuse ambiguous calendars,
misaligned panels, unsafe paths, or unsupported research shapes.

## Scope

### In scope

- A versioned external daily-OHLCV package manifest with provider, retrieval,
  adjustment, market-clock, universe, currency, venue, and source-file fields.
- Strict path confinement, source hashing, OHLCV normalization, common-panel
  validation, minimum breadth/history, and request compatibility.
- Transactional Project construction using the existing Factor, Portfolio, or
  RL fixed Judge while replacing only the synthetic fixture and Study dataset
  identity.
- Project-level request/intake/snapshot evidence and exact CLI next actions for
  baseline execution and delegated Session start.
- Studio display of an intake before a Session exists.
- Deterministic fixtures plus one bounded smoke over the existing Yahoo daily
  sample.

### Out of scope

- Downloading from Yahoo or another provider inside the Core command.
- Corporate-action calculation, survivorship-bias correction, point-in-time
  fundamentals, intraday calendars, futures rolls, FX sessions, or live feeds.
- Treating provider metadata as authenticated truth.
- Automatically starting an Agent Campaign or publishing to OpenAlice Inbox.

## Acceptance

- [x] Invalid, escaping, duplicated, misaligned, non-positive, weekend-session,
      or request-incompatible packages create no partial Project.
- [x] A valid package is normalized into Project-local canonical CSV, hashes
      every source and normalized file, and records explicit provenance and
      price-adjustment claims.
- [x] The generated Study universe/time range/dataset identity exactly matches
      the snapshot and locks every dataset byte.
- [x] `aq project intake --json` is machine-discoverable and returns the
      Project, request, snapshot, Study, and executable next actions.
- [x] Studio shows request → dataset → baseline → iterate state before a
      Session exists and derives it from verified Core evidence.
- [x] Existing synthetic template creation remains byte-compatible in behavior.
- [x] Factor, Portfolio, and RL intake Runs are bounded; real Yahoo Portfolio
      smoke evidence succeeds without reading repository-global data at Run
      time.

## Work

- [x] Audit the request/Project/data/Study boundary and choose strict caller-
      supplied snapshots over an embedded downloader.
- [x] Fix the intake manifest, normalization, compatibility, and identity
      contract.
- [x] Implement transactional construction, CLI discovery, and Studio
      projection.
- [x] Complete regressions, real-data smoke, docs, packaging, and completion
      audit.

## Findings and decisions

- 2026-07-24 — Session request validation is intentionally strict, but today it
  only rejects a mismatch; it cannot construct the compatible Study it needs.
- 2026-07-24 — The first production-shaped intake supports aligned daily
  session bars only. Existing Judges annualize at 252 and do not yet own
  multi-calendar or mixed-asset semantics, so pretending otherwise would make
  metrics wrong.
- 2026-07-24 — Network retrieval stays outside Core. The caller supplies a
  package; AutoQuant owns validation, normalization, confinement, identity,
  and repeatable Project construction.
- 2026-07-24 — Studio promotes the latest verified baseline metrics over
  generic object counts. It distinguishes requested assets from the research
  universe and never treats a merely positive number as a passed threshold.
- 2026-07-24 — The bounded Yahoo baseline was intentionally not optimized:
  validation net Sharpe was `-1.467921554920368`. Negative evidence is a valid
  intake/Run/UI proof and must not be presented as alpha.

## Verification

- `uv run python scripts/check_doc_links.py` — 251 links resolved.
- `uv run python -m unittest discover -s tests -v` — 101 tests passed in
  133.924 seconds after the final Studio changes.
- `node --check autoquant/studio_assets/studio.js`,
  `uv run python -m compileall -q autoquant tests`, and `git diff --check`
  passed.
- Factor, Portfolio, and RL Projects constructed from `HEAD` and from this
  worktree were recursively byte-identical under
  `/tmp/autoquant-synthetic-compat.r1ucyB`.
- `uv build` produced the sdist and wheel; the wheel contained Core intake,
  all Studio assets, and the Portfolio Judge.
- An isolated wheel smoke under
  `/tmp/autoquant-final-wheel-intake.fQempp` discovered `project.intake`,
  ingested five Yahoo daily assets, removed the external source directory,
  revalidated the Project, executed a successful Portfolio Run, reconciled
  attribution, and exposed the Portfolio metric layer through Studio.
- Manual in-app browser verification at `http://127.0.0.1:8766` confirmed the
  request/data/baseline/iterate first viewport, adverse-metric presentation,
  structured Inspector, and exact copy-command label restoration.

## Progress log

- 2026-07-24 — Activated after the full-goal audit found the request-to-real-
  Project boundary was the first broken link in OpenAlice collaboration.
- 2026-07-24 — Implemented strict package/request validation, content-locked
  construction, CLI/schema/capability discovery, Core verification, and
  pre-Session Studio projection.
- 2026-07-24 — Added malformed/type, path/symlink, OHLCV, alignment, request,
  tamper, all-template Run, real Yahoo, wheel, and legacy-template evidence.
- 2026-07-24 — Completed after the acceptance audit and live Studio tuning.

## Completion

OpenAlice or a local Agent can now turn one strict request and one bounded
caller-supplied daily-OHLCV package into a self-contained Factor, Portfolio, or
RL Project. Request, canonical data, provenance claims, snapshot, Study, Run,
Session next action, and Studio state share one verifiable identity chain.
