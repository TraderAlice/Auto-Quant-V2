# Same-Project Book Risk follow-up field trial

- Status: `completed`
- Updated: `2026-08-01`
- Target release: `0.9.8`
- Related design: [[docs/design/workspace-project-boundaries]],
  [[docs/design/reported-position-book-risk]],
  [[docs/design/study-run-evidence]],
  [[docs/design/run-bound-research-reports]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that “one Project is one evolving body of research” is executable rather
than documentary language. A fresh coworker must enter the completed
`0.9.7` U.S. mega-cap Book Risk Project, recognize a caller-specified
reallocation comparison as a related follow-up, preserve every existing fixed
request, Study, Run, Report, and artifact byte, and add one separately fixed
Study/Run/Report inside that same Project without creating a duplicate Project
or weakening immutable evidence. Agent-maintained `research.md` and
`framework-needs.md` remain appendable longitudinal notes rather than frozen
Run evidence.

## Field assignment

The retained Project already answers whether reducing NVDA alone to Cash can
meet a 20% 126-bar volatility ceiling. The same caller now asks a distinct but
related descriptive question over the exact same unauthenticated baseline
book, as-of date, split-adjusted aligned dataset, and fixed 63/126/252 method:

- scenario `fund-googl-from-nvda`: NVDA 20%, MSFT 25%, AMZN 15%, META 10%,
  GOOGL 20%, Cash 10%;
- scenario `fund-msft-from-nvda`: NVDA 20%, MSFT 35%, AMZN 15%, META 10%,
  GOOGL 10%, Cash 10%;
- compare each complete caller-supplied book with the retained 30/25/15/10/10
  baseline under historical covariance risk;
- return volatility, crowding, component-risk changes, and ranks without
  selecting, optimizing, or executing either scenario;
- no account, Broker, Order, TP/SL, or trading authority.

The existing content-locked dataset is exactly task-complete for this
follow-up, so reacquisition is neither required nor prohibited. If the worker
uses it, the new Study must bind the exact existing bytes; if it reacquires,
the caller question may not be narrowed or silently mixed across snapshots.

## Scope

### In scope

- Preserve a complete before/after hash inventory of the original Project
  state, distinguishing intentional new paths from forbidden mutation.
- Run one isolated installed `0.9.7` Grok baseline using only the existing
  Workspace, public CLI/schema/template surfaces, materialized Skills, and the
  follow-up assignment.
- Observe continue-versus-new reasoning, ability to represent a second fixed
  request/Study instance, Judge input isolation, Run and direct-Report
  identity, orientation, validation, and Studio projection.
- Promote only reproduced lifecycle friction needed for a related fixed Study
  to coexist with historical evidence.
- Preserve standalone operation and avoid a universal workflow engine or
  automatic conversational intent classifier.

### Out of scope

- Updating market data, rolling a live book, authenticated account state,
  general portfolio optimization, scenario generation, execution, or OpenAlice
  orchestration.
- Mutating the completed one-leg sizing Study to reinterpret it as scenario
  comparison.
- A general migration framework or compatibility layer for arbitrary old
  Project schemas.

## Acceptance

- [x] The fresh worker chooses the existing U.S. Book Risk Project and creates
  no sibling or nested Project/Workspace.
- [x] Every pre-existing fixed authority and immutable evidence file remains
  byte-for-byte unchanged; new fixed state occupies explicit follow-up-owned
  paths. Longitudinal `research.md` and `framework-needs.md` may only receive
  truthful append-only updates about the follow-up.
- [x] The caller's two complete scenarios, common baseline, dataset identity,
  fixed method, and no-selection/no-trading authority are preserved before
  execution.
- [x] Exactly one additional fixed Book Risk Study, Run, and direct Run Report
  answer the follow-up; no Session, candidate, Check, Experiment, or search
  loop is created.
- [x] Old and new Study inputs remain independently current and inspectable;
  neither Judge reads mutable singleton request/strategy state owned by the
  other Study.
- [x] Validation, explicit orientation, Run Explorer, Report listing, and
  Studio expose the follow-up without erasing or relabeling the original
  sizing evidence.
- [x] Every material baseline failure becomes a bounded repair with regression
  or an explicit worker/external limitation.
- [x] Complete tests, documentation links, build/install smoke, clean-clone
  checks, and a fresh final installed-worker pass before `v0.9.8` is tagged
  and pushed.

## Work

- [x] Select a related fixed follow-up that cannot honestly overwrite the old
  request or be dismissed as an unrelated new Project.
- [x] Prepare the immutable completed-Project handoff and installed `0.9.7`
  worker boundary.
- [x] Run the fresh baseline and preserve its transcript/filesystem evidence.
- [x] Design and implement only the lifecycle repair demonstrated necessary.
- [x] Complete final verification, installed-wheel replay, release, and push.

## Findings and decisions

- 2026-08-01 — Caller-supplied scenario comparison was chosen because Book
  Risk already supports the quantitative method in a fresh Project. Any
  failure therefore isolates Project/Study continuation rather than requiring
  a new model or metric.
- 2026-08-01 — Reusing exact content-locked bytes is allowed here because the
  follow-up explicitly fixes the same assets, as-of, price semantics, clock,
  and history. This is demand fidelity, not inventory authority.
- 2026-08-01 — Old Runs are not proof that singleton Project inputs may be
  overwritten. The new Study must remain reproducible alongside the old one
  from durable files after conversation context disappears.
- 2026-08-01 — The installed `0.9.7` baseline correctly continued the existing
  Project but could not execute the second Study. Its declared alternate
  snapshot reached the frozen Run dependencies while the fixed Judge and
  Explorer still required singleton `strategies/position-snapshot.json`.
- 2026-08-01 — The baseline also exposed an acceptance-language mistake:
  evolving Project notes are intentionally mutable. Preservation applies to
  fixed authorities and immutable evidence, not to truthful append-only
  research and framework-needs logs.
- 2026-08-01 — The first installed `0.9.8` worker completed the new Study, Run,
  and Report and preserved the original evidence, but revealed that direct
  Reports still copied the Project-root request. Report publication and loading
  now resolve request authority from immutable Run inputs and verify the
  Study-owned request against its frozen position snapshot.
- 2026-08-01 — Multiple independent fixed Studies still require explicit
  selection; AutoQuant must not guess their order. Orientation now states that
  their evidence remains available instead of incorrectly claiming that no
  successful verified Run exists.

## Verification

- `uv run python -m unittest discover` — 376 tests passed in 925.726 seconds.
- `uv run python scripts/check_doc_links.py` — all 1,298 double-links resolve.
- `uv lock --check`, Python compile, Studio JavaScript syntax, source/wheel
  build, and fresh Python 3.11.14 wheel installation passed.
- Final wheel SHA-256:
  `df80cf0ca3f46cb3526eff11f6d4a1d3d11e2e0c12a5da10a46b29a15fa72f26`.
- Fresh Grok 4.5 session `019fba4a-3429-7db1-b283-fef6ca81b3b4`
  used 13 turns, inspected no package/repository implementation, created one
  new Study, successful Run, and direct Report, and registered no framework
  need. Transcript and handoff evidence are retained in
  `cohort-16-same-project-book-risk-followup-v098`.
- Host diff against the pristine completed Project found only the new
  follow-up-owned paths and the allowed append to `research.md`; all prior
  fixed authority and immutable evidence remained byte-identical.
- Installed CLI validation, old/new Report loading, explicit orientation,
  Book Risk Explorer, Report listing, and Studio projection passed. The new
  Report embeds the Study-owned scenario request, not Project-root sizing
  intake.
- A no-hardlink clone without local override passed `aq orient`, `aq validate`,
  `aq project list`, and `aq studio snapshot` against the repository-root
  sample Workspace.

## Progress log

- 2026-08-01 — Created and indexed the `0.9.8` plan from the clean released
  `v0.9.7` tag before constructing the follow-up handoff.
- 2026-08-01 — Fresh Grok baseline used only installed `aq 0.9.7`, stayed in
  `us-mega-cap-book-risk-v097`, created no Project or Workspace, preserved the
  original fixed evidence, and stopped honestly after one failed Run proved
  the singleton Book Risk input defect. Transcript and filesystem evidence
  are retained in `cohort-14-same-project-book-risk-followup-v097`.
- 2026-08-01 — Source-checkout smoke created an independent follow-up Study,
  successful Run, and direct Report while all 47 original files remained
  unchanged. The first installed-wheel replay then exposed and reproduced the
  Report request-binding defect before release.
- 2026-08-01 — The final installed-wheel coworker stayed inside the existing
  Project, used public contracts only, completed the requested evidence chain,
  understood explicit multi-Study selection as intentional, and recorded no
  framework need. Host-side validation and immutable diff independently
  confirmed the handoff.

## Completion

`v0.9.8` establishes a narrow, proven continuation contract: a completed Book
Risk Project can add another independently fixed question over the exact same
retained dataset without overwriting original authority, duplicating the
Project, or mislabeling the new Report. It does not generalize this command
into automatic intent routing or make existing data an admission boundary.
