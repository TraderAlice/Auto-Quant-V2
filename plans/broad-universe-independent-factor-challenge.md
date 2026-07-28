# Broad-universe independent Factor challenge

- Status: `completed`
- Updated: `2026-07-28`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/panel-native-factor-api]],
  [[docs/design/factor-diagnostics]],
  [[docs/design/factor-evidence-explorer]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Complete one realistic delegated Factor assignment over a content-locked,
50–100-stock US equity panel that shares neither assets nor dates with the
source research. Keep the predeclared `reversal_5` definition frozen, preserve
real listing-history and missing-session availability rather than silently
intersecting timestamps, and return one immutable evidence Report that is
usable whether the factor qualifies or fails.

## Context

The first real cross-sectional Project proved that AutoQuant can express
request-bound known-style validation, but it used only twelve assets over
2024–2026. Its five-session validation IC was positive while its HAC evidence
remained below the fixed qualification threshold. The resulting Agent agenda
correctly required a frozen independent sample.

The current V1 daily intake requires every asset to share an exact timestamp
panel. That assumption is convenient for small fixtures but unsuitable for a
broad equity universe: it either rejects genuine listing-history and isolated
missing sessions or encourages a downloader to erase them through a global
intersection. The Factor runtime and diagnostics already operate on long-form
pandas data and can support causal per-timestamp availability, but the public
intake, snapshot, Judge loading, evidence, and documentation do not yet make
that contract explicit.

## Scope

### In scope

- Define a V4 daily ragged-panel contract for Factor intake without implicit
  fill, global timestamp intersection, or invented pre-listing history.
- Content-lock each asset's own observed start, end, row count, and bytes while
  recording union coverage and time-varying cross-sectional breadth.
- Require enough per-asset history and enough assets per evaluated timestamp
  for the fixed Factor Judge, while allowing bounded missingness.
- Project coverage and breadth evidence through RunResult, Factor Explorer,
  CLI, Studio, and immutable Report.
- Build one independent Yahoo-derived research package with 50–100 equities,
  no source-Project assets, and no source-Project dates.
- Run the exact frozen `reversal_5` candidate once through the public
  Project/Session/Report workflow and record observed Workbench needs.

### Out of scope

- Point-in-time index reconstruction, delisting-return recovery, provider
  authentication, corporate-action reconciliation, or a claim that the
  convenience universe is survivorship-free.
- Ragged intraday V2/V3 panels.
- Portfolio or governed-RL support for ragged panels, Orders, Broker authority,
  or live trading.
- Candidate tuning, alternative factor search, repeated independent-sample
  attempts, or visible-test selection.

## Acceptance

- [x] V4 Factor intake accepts a bounded ragged daily panel and preserves every
  asset's observed timestamps without forward fill or global intersection.
- [x] Snapshot, Study, Run, Explorer, CLI, Studio, and Report expose verified
  union coverage plus time-varying usable-universe evidence.
- [x] Portfolio/RL intake rejects ragged panels explicitly until those lanes
  own a scientifically valid missing-data contract.
- [x] A strict request and package contain 50–100 equities with zero asset and
  date overlap with the source Project, plus explicit survivorship and provider
  limitations.
- [x] The Project Agent completes the assignment using public `aq` operations,
  with the exact `reversal_5` source frozen before the independent Run.
- [x] One unique frozen candidate trial is used for the terminal conclusion
  and one immutable Report binds one evidence Run. `session start`
  unexpectedly produced a second byte-identical execution; the Report
  discloses it, the family ledger counts it as a duplicate rather than an
  independent trial, and Core now reuses an exact current baseline.
- [x] Focused tests, full regression, documentation links, compilation,
  package build, and the real Project validation all pass.

## Work

- [x] Reproduce the exact-panel failure and define the bounded ragged-panel
  evidence contract.
- [x] Implement intake, snapshot, Judge, Explorer, CLI, Studio, and Report
  support with explicit non-Factor rejection.
- [x] Build and validate the independent broad-universe data package.
- [x] Create the delegated Project and complete one frozen Factor trial.
- [x] Publish the immutable Report and audit the two-line Agent/Core experience.
- [x] Complete regression, documentation, packaging, commit, and push.

## Findings and decisions

- 2026-07-28 — Independence is stronger than the prior agenda minimally
  required: the challenge will use both a disjoint asset set and a
  non-overlapping date interval. It is an external historical validation, not
  a prospective later-period claim.
- 2026-07-28 — Global date intersection is not a neutral cleaning step. It
  conditions every asset on the availability of every other asset and erases
  listing/missingness evidence, so the package must retain per-asset rows.
- 2026-07-28 — Ragged-panel authority is initially Factor-only. Extending
  target-weight accounting and governed RL requires separate execution and
  state semantics and is not necessary to answer this assignment.
- 2026-07-28 — The daily ragged contract is schema V4, not a relaxation of V1.
  V1 keeps its exact aligned semantics so existing consumers and snapshots do
  not silently change meaning.
- 2026-07-28 — A successful Run already matching every current scientific and
  Harness identity is valid Session baseline evidence. Session construction
  must reuse it; the old unconditional execution was surprising mutation and
  caused one disclosed duplicate in the real assignment.

## Verification

- `uv run python -m unittest tests.test_intake tests.test_factor_lab
  tests.test_factor_explorer tests.test_reports tests.test_dossiers
  tests.test_sessions tests.test_selection tests.test_research_program -v` —
  85 related tests passed.
- `uv run python -m unittest discover -s tests` — 234 tests passed in
  1600.304 seconds.
- `uv run python scripts/check_doc_links.py` — 929 documentation links
  resolved.
- `git diff --check` — passed.
- `uv build` — source distribution and wheel built successfully.
- Real Project `aq validate --json` — `ok=true`, `valid=true`.
- Immutable Report `aq report show --json` — verified Report
  `report-20260728T015158529983Z-d56a4afba270`, including the frozen
  availability evidence and one disclosed duplicate execution.

## Progress log

- 2026-07-28 — Plan created after inspecting the completed twelve-asset
  Project, public intake contract, and fixed exact-panel guard.
- 2026-07-28 — Built and content-locked a 72-stock, 2018–2023 Yahoo-derived
  observed-only panel with 105093/108648 rows and no source asset/date overlap.
- 2026-07-28 — The exact reversal candidate reproduced identity 1.0 but failed
  robust transfer: validation IC `0.015696` (HAC p `0.469`) and test IC
  `-0.001052` (HAC p `0.964`).
- 2026-07-28 — Published terminal Report
  `report-20260728T015158529983Z-d56a4afba270` and completed the delegated
  Session without promotion.

## Completion

The challenge is complete. AutoQuant accepted and preserved a realistic
ragged 72-stock Factor panel, proved the exact request-seeded known-style
candidate, returned a negative independent research conclusion through one
immutable Report, and completed the delegated Session without promotion.

The Agent experience was strong after the Project existed: the English brief,
content locks, Factor diagnostics, Explorer, Report, and completion path made a
negative answer easy to preserve and hand off. The assignment exposed three
material construction problems, all repaired in Core: exact daily intake
erased real availability, known-style requests initially opened with an
unrelated generic candidate, and Session start duplicated an exact successful
baseline. The historical duplicate remains visible evidence; future exact
Session starts reuse it rather than mutating research history.
