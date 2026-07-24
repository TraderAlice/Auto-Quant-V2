# Reported Session completion

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/research-session-loop]],
  [[docs/design/research-program-orchestration]],
  [[docs/design/program-research-dossiers]], and
  [[docs/design/studio-observation-surface]].

## Outcome

Let a delegated research lane end truthfully without promoting source when its
verified conclusion is to retain the baseline. The terminal Session, immutable
Report, Research Program, Dossier readiness, CLI, and Studio must all agree
that the lane is complete and no longer an active writer/reader.

## Context

Sessions currently have only `active` and `promoted` states. A baseline-only or
all-REVERT/CRASH lane can publish a valid Report, but it remains active forever
unless a KEEP is promoted. In a multi-Study Project this creates false ongoing
writer/writer and writer/reader conflicts after the Project Dossier is already
published.

Promotion and completion are intentionally different:

- `promoted` copies an improved KEEP leader into the owning Project;
- `completed` mutates no Project source and is allowed only when the Session
  leader remains the baseline and a current verified Report freezes that
  conclusion.

## Scope

### In scope

- Strict `active → completed` transition for delegated Sessions.
- Immutable `completion.json` receipt bound to the exact current Report,
  baseline leader, request, Study, and Project.
- Receipt/file/Report tamper validation on Session load.
- Rejection of completion with an unpromoted KEEP, changed worktree, running
  Campaign, stale authority, missing/current-mismatched Report, or legacy
  unbound Session.
- Terminal-state enforcement for Experiment, Campaign, Report, promotion, and
  repeat completion operations.
- CLI capability/next-action support and Research Program completion
  recommendation.
- Studio terminal-state and exact copy-only completion command.
- Real three-lane completion smoke proving conflicts fall to zero while the
  current Dossier remains valid.

### Out of scope

- Rejecting/dismissing a KEEP while retaining it as the official Session
  leader.
- Automatic command execution from Studio.
- Program-wide multi-process scheduling or automatic lane completion.
- Changing Judge promotion semantics or Dossier composition.

## Acceptance

- [x] Completion requires an active delegated Session whose leader equals its
  baseline and whose worktree matches that leader.
- [x] Completion selects one explicit verified Report for the current leader
  and rejects any running Campaign.
- [x] `completion.json` is immutable, strict, content-bound, and verified on
  every Session load; receipt/report/session tampering is detected.
- [x] Completed Sessions cannot evaluate, run Campaigns, publish new Reports,
  promote, or complete twice.
- [x] Research Program conflicts count only active Sessions and recommends
  completion for an active reported baseline lane.
- [x] CLI discovery, envelopes, artifacts, schemas, and next actions expose the
  transition; Studio displays the same Core command without executing it.
- [x] Existing active/promoted Sessions and historical Reports remain valid.
- [x] Focused/full tests, real three-lane Dossier survival, browser QA, docs,
  wheel installation, commit, and push pass.

## Work

- [x] Audit Session status, Report publication, Program conflict, Dossier, CLI,
  and Studio behavior.
- [x] Implement completion Core contract and receipt validation.
- [x] Add CLI, capability, Program, Studio, and documentation projections.
- [x] Complete deterministic, real-project, browser, full-suite, and wheel
  verification.

## Findings and decisions

- 2026-07-24 — A Report is immutable evidence but does not itself end a
  Session because multiple point-in-time Reports are allowed.
- 2026-07-24 — Completion is not a substitute for promotion. V1 completion is
  deliberately baseline-only; an improved KEEP must be promoted before its
  downstream source can be treated as current.
- 2026-07-24 — The operator/Agent must select the exact Report id. Core does
  not guess which qualitative conclusion should close the lane.
- 2026-07-24 — A pre-existing demo Session correctly became harness-stale
  after the Core source changed. Completion was therefore verified with a
  freshly constructed three-lane Project rather than weakening source
  identity checks.

## Verification

- `uv run python -m unittest tests.test_reports -v` plus selected CLI
  completion tests: 10 tests passed in 9.470 seconds.
- Cross-domain focused suite over Reports, Sessions, Research, Dossiers,
  Research Program, Studio, and selected CLI behavior: 33 tests passed in
  86.589 seconds.
- `uv run python -m unittest discover -v`: 126 tests passed in 277.878
  seconds.
- `uv run python scripts/check_doc_links.py`: 359 documentation double-links
  resolved.
- `git diff --check`, `uv run python -m compileall -q autoquant tests`, and
  `node --check autoquant/studio_assets/studio.js`: passed.
- A fresh three-lane request-driven Project completed Factor, Portfolio, and
  governed-RL Sessions, preserved their Reports and published Dossier
  `dossier-20260724T123313084454Z-ac0e9354e20f`; Program status reported three
  reported lanes, zero active Sessions, and zero conflicts.
- Studio browser QA at 1280×720 and 640×900 showed all three lanes as
  `completed`, three Reports, a published Dossier, no coordination warning,
  no horizontal overflow, and no browser console errors.
- Built `auto_quant-0.1.0-py3-none-any.whl`, inspected the packaged completion
  Core/CLI/Studio assets, installed it into a fresh Python 3.11 environment,
  and verified the installed `session-completion` schema and
  `session.complete` capability descriptor.

## Progress log

- 2026-07-24 — Plan activated after the real three-lane Dossier demo exposed
  three permanently active Sessions and two coordination conflicts.
- 2026-07-24 — Added the strict baseline/Report-bound terminal contract across
  Core, CLI, Program, Studio, tests, and durable design documentation.
- 2026-07-24 — Full, packaged-install, real Project, and browser verification
  passed; the milestone was committed and pushed to `main`.

## Completion

AutoQuant can now distinguish ongoing research from a delegated lane whose
verified conclusion is to retain the baseline. That conclusion is frozen in a
strict completion receipt without mutating Project source, and every Core,
Agent, Program, Dossier, and Studio projection agrees that the Session is
terminal.
