# Build a multi-Study quantitative research desk

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/quant-research-lifecycle]] and
  [[docs/design/research-program-orchestration]].

## Outcome

An OpenAlice or local caller can submit one research request and one
content-locked OHLCV package without choosing an evaluation technique. One
self-contained Project is created with coordinated Factor, Portfolio, and
governed-RL Studies plus a machine-readable research-program status shared by
CLI and Studio.

## Context

AutoQuant currently has professional Factor, Portfolio, and RL lanes, but
request intake requires callers to choose exactly one template. That leaks
quant-research implementation detail into the collaboration boundary and
encourages three disposable Projects for one investment question.

A real quantitative desk should own method selection. Factor discovery and
portfolio implementation also share one editable factor surface, so their
sequencing and stale-evidence state must be explicit.

## Scope

### In scope

- A new `ohlcv-research-desk` Project/intake template with one shared dataset,
  one shared factor candidate, one RL state encoder, and three fixed Studies.
- A strict Project-local research-program manifest.
- A verified Core projection of lane dependencies, current/stale evidence,
  Sessions, Reports, shared editable surfaces, and exact next actions.
- `aq project program` plus capability/schema discovery.
- A Studio research-program board for humans and Agents.
- Intake defaults that let the quantitative desk choose the methods.
- Bounded real-intake tests that execute all three Studies.

### Out of scope

- Automatically claiming a lane is scientifically complete.
- Concurrently merging two Sessions that edit the same factor source.
- Making the governed RL lane consume a promoted arbitrary candidate factor;
  V1 keeps its fixed reference sleeves and exposes that boundary explicitly.
- OpenAlice Inbox mutation or authenticated caller provenance.

## Acceptance

- [x] One intake creates exactly one Project, one normalized dataset snapshot,
      and the three canonical Studies.
- [x] Factor and Portfolio Studies share the same candidate bytes while each
      Study keeps precise Judge authority; RL keeps a separate model surface.
- [x] Every Study binds the same dataset identity and time/universe contract.
- [x] Core detects missing lanes, dataset divergence, stale Runs, and
      concurrent shared-surface research.
- [x] CLI returns exact lane-specific read/mutation commands without executing
      them.
- [x] Studio renders the same Core program object and does no workflow
      inference in JavaScript.
- [x] Existing single-lane templates remain supported.
- [x] Focused/full tests, wheel contents, and browser QA pass.

## Work

- [x] Audit the existing intake, template, Study, Run, Session, and Report
      boundaries.
- [x] Select one Project / three Study orchestration as the next product
      boundary.
- [x] Implement the composite template and strict program manifest.
- [x] Implement Core/CLI research-program projection.
- [x] Implement Studio board and interaction.
- [x] Verify real intake, all three Runs, corruption/staleness, packaging, and
      browser behavior.

## Findings and decisions

- 2026-07-24 — The external caller should provide the investment question,
  universe, horizon, and constraints, not choose `factor`, `portfolio`, or
  `RL` as an intake mode.
- 2026-07-24 — Factor and Portfolio use the same `factors/candidate.py`.
  Their Sessions must be sequential because concurrent promotion would create
  ambiguous source ownership.
- 2026-07-24 — A research-program board is advisory evidence and coordination,
  not a new promotion authority. A Report is evidence readiness, not proof
  that a research question is permanently complete.
- 2026-07-24 — The current governed RL lane remains an explicit high-burden
  adaptivity challenge over fixed sleeves. Connecting arbitrary promoted
  factors into its action set requires a separate causal artifact-dependency
  contract.

## Verification

- `node --check autoquant/studio_assets/studio.js`
- `uv run python -m compileall -q autoquant tests`
- `uv run python -m unittest tests.test_research_program tests.test_cli
  tests.test_intake tests.test_studio` — 29 tests passed.
- `uv run python -m unittest discover -s tests` — 118 tests passed in
  229.614 seconds.
- Real aligned five-asset intake executed successful Factor, Portfolio, and RL
  baselines over one snapshot.
- Browser QA at 1280×720 confirmed no horizontal overflow, aligned recommended
  lane/summary/command context, and working clipboard interaction.
- `uv build` packaged the Core module, composite template, and Studio assets;
  an installed-wheel smoke created an `ohlcv-research-desk` Project and
  discovered the `research-program-status` schema.

## Progress log

- 2026-07-24 — Activated after the RL Policy Evidence Explorer exposed that
  the remaining product gap is cross-lane Project orchestration.
- 2026-07-24 — Completed with the composite template, strict program status,
  default request intake, Core/CLI/Studio projection, stale/conflict detection,
  and a browser-verified three-lane research board.
