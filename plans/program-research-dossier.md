# Program research dossier

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/program-research-dossiers]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/research-program-orchestration]], and
  [[docs/design/studio-observation-surface]].

## Outcome

Let one request-driven multi-Study Project publish a single immutable Research
Dossier that synthesizes current Factor, Portfolio, and optional governed-RL
lane Reports into a verified JSON/Markdown handoff for OpenAlice.

## Context

AutoQuant can receive one OpenAlice Research Request, run three coordinated
Studies, publish evidence-bound Reports inside individual Sessions, and show
the complete evidence chain in Studio. It cannot yet return one Project-level
answer. Treating one lane Report as the final answer loses the distinction
between predictive signal, investable implementation, and adaptive value-add.
Reinterpreting raw Runs at the Project layer would duplicate Judge and Report
authority.

The Dossier therefore composes already verified lane Reports. It freezes their
identities and bounded evidence projections, requires coverage of every
included lane, discloses omitted optional lanes, and preserves the rule that
OpenAlice alone stamps authoritative Inbox provenance.

## Scope

### In scope

- Project-level Dossier readiness over the canonical Research Program.
- Strict Agent-authored cross-lane analysis with Report/finding references.
- Immutable `analysis.json`, `dossier.json`, `dossier.md`, and manifest under
  a confined Project-owned `dossiers/` root.
- CLI status/publish/list/show commands and schemas.
- Studio readiness, latest-Dossier, OpenAlice handoff, and timeline projection.
- Deterministic tests for currentness, optional RL disclosure, tampering,
  later-research survival, CLI parity, and browser presentation.

### Out of scope

- Replacing or weakening lane-specific Session Reports.
- Automatically generating qualitative analysis in Core.
- OpenAlice Inbox writes, authenticated caller provenance, or trading
  authorization.
- Cross-Project aggregation, remote registries, or portfolio/order execution.

## Acceptance

- [x] Readiness requires verified Project intake, one canonical Research
  Program, and current Reports for every required lane.
- [x] An optional RL lane is included only with a current Report; otherwise the
  Dossier explicitly records why it was omitted.
- [x] Agent analysis can reference only included lane Reports and their
  verified finding ids, and findings cover every included lane.
- [x] Publication freezes request, dataset, program, Study, Report, leader Run,
  selection-integrity, Harness, and source/dependency identities.
- [x] Loading detects changed files, fabricated references, inconsistent
  request/dataset/program identity, and altered frozen projections.
- [x] An immutable Dossier remains valid when later Session evidence is added.
- [x] CLI capabilities and schemas expose the complete headless lifecycle.
- [x] Studio shows whether the overall OpenAlice handoff is blocked, ready to
  publish, or already published without creating a browser verdict.
- [x] Documentation, focused/full tests, wheel installation, real three-lane
  smoke, and browser QA pass.

## Work

- [x] Audit Session Report, request intake, Research Program, CLI, Project
  storage, and Studio boundaries.
- [x] Choose Report composition rather than raw-Run reinterpretation.
- [x] Implement Dossier analysis, readiness, publication, loading, and listing.
- [x] Add CLI/capability/schema contracts.
- [x] Add Studio and documentation projections.
- [x] Complete the acceptance and release audit.

## Findings and decisions

- 2026-07-24 — A Project Dossier composes verified lane Reports. It does not
  create a second evaluator over raw Runs.
- 2026-07-24 — Factor and Portfolio are required canonical lanes. Governed RL
  remains optional, but omission is frozen and visible.
- 2026-07-24 — The Dossier uses a reserved optional `dossiers/` directory so
  existing V1 Project manifests and historical Projects remain loadable.
- 2026-07-24 — Publication requires lane Reports that match the current
  Session leader and current Study identity. Loading later verifies the frozen
  prefix rather than requiring the Project to remain current.
- 2026-07-24 — Studio consumes Core Dossier status/list operations as a
  separate diagnostic category. Browser code can display and copy the next
  action but cannot compose or publish analysis.
- 2026-07-24 — An installed Harness version mismatch makes current Dossier
  readiness stale while the immutable older Dossier remains loadable. This
  preserves both runtime-version honesty and point-in-time evidence.

## Verification

- `uv run python -m unittest tests.test_dossiers -v` — both required-lane and
  all-three-lane publication/tamper/currentness cases passed.
- `uv run python -m unittest tests.test_studio -v` — all 7 Studio snapshot,
  HTTP, invalid-category, and mutable-progress tests passed.
- `uv run python -m unittest discover -v` — all 124 tests passed in 389.646
  seconds.
- `uv run python -m unittest tests.test_documentation -v` — all repository
  double-links resolved.
- `node --check autoquant/studio_assets/studio.js` and Python byte compilation
  passed.
- `uv build --wheel --out-dir /tmp/autoquant-dossier-wheel-20260724` built the
  wheel; inspection confirmed `dossiers.py`, Studio Core, and Studio
  JavaScript. A fresh Python 3.11 environment installed all 161 packages,
  loaded the real immutable Dossier, and exposed the Dossier analysis schema.
- A real request-driven `ohlcv-research-desk` Project executed Factor,
  Portfolio, and RL baselines, published three delegated lane Reports, then
  published `dossier-20260724T114946909861Z-956dc2554a16`.
- Browser QA at 1280×720 and 640×900 showed the Research Cockpit, current
  Dossier handoff, and Inspector authority boundary with no horizontal
  overflow. Browser logs were empty.

## Progress log

- 2026-07-24 — Plan activated after the Research Cockpit made the missing
  Project-level OpenAlice return artifact explicit.
- 2026-07-24 — Implemented the immutable Dossier Core, CLI/schema/capability
  surface, Studio snapshot/HCI, canonical documentation, and deterministic
  contract tests.
- 2026-07-24 — Completed real three-lane, responsive browser, full-suite, and
  isolated-wheel audits.

## Completion

AutoQuant can now return one immutable Project-level answer without collapsing
lane-specific evidence or creating a second evaluator. Factor and Portfolio
Reports are required, compatible governed RL evidence is optional and explicit,
and OpenAlice receives a verified JSON/Markdown Dossier with no trading
authority. CLI and Studio share the same readiness and artifact loaders.
