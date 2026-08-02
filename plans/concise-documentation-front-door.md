# Concise documentation front door

- Status: `active`
- Updated: `2026-08-02`
- Target release: `0.9.29`
- Related design: [[docs/design/documentation-system]],
  [[docs/design/versioning-and-release]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Make repository documentation behave like an Agent-loadable information
system instead of one linearly growing README. A newcomer should understand
what AutoQuant is and start the root Workspace from the README, while an Agent
performing research, framework development, or a release follows one explicit
route to the document that owns that work.

## Context

The intended ownership already exists: README is the product entrance,
`docs/STATUS.md` owns current capability, `docs/CHANGELOG.md` owns chronological
release summaries, `docs/design/versioning-and-release.md` owns release and
upgrade rules, completed plans own exact proof, and `AGENTS.md` routes work.
However, README is still 389 lines and duplicates detailed data acquisition,
intake, Session, Report, Dossier, and Studio procedures. The architecture says
to load those details on demand, but the entry surface does not yet obey it.

The answer is not another version-policy document. It is to make the existing
document boundaries executable, move the complete operator walkthrough to one
stable guide, and keep README small enough to remain a useful first read.

## Scope

### In scope

- Reduce README to product identity, Workspace/Project mental model, current
  release pointer, one clone-to-orientation quick start, a compact workflow
  map, repository map, contributor entry, and license.
- Create one durable operator guide for standalone/OpenAlice composition,
  Project construction, demand-led data acquisition, strict intake, governed
  research, evidence publication, and Studio observation.
- Keep version semantics, release audit, tags, checkout behavior, compatibility,
  and host pins exclusively in the existing versioning-and-release document.
- Route `AGENTS.md` directly to the operator guide for public workflow detail
  and to the version document for any version or release action.
- Add bounded documentation tests that prevent README from regaining release
  ledgers, detailed operator sections, or unbounded size while preserving the
  OpenAlice-readable version frontmatter.
- Ask a fresh Grok coworker to locate both the new-project path and the release
  path from the repository entrance without repository-internal coaching.

### Out of scope

- Changing quantitative contracts, CLI behavior, Studio behavior, OpenAlice's
  pinned `0.8.31` Harness, or the Workspace upgrade model.
- Rewriting every subsystem design document or aggressively shortening domain
  safety rules that must remain in `AGENTS.md` on every Agent entry.
- Building a generated documentation site or a second navigation taxonomy.

## Acceptance

- [x] README is a concise product entrance no longer than 220 physical lines
  and contains no detailed release checklist, historical release ledger, data
  packaging tutorial, Session loop, Report/Dossier procedure, or feature-by-
  feature capability catalogue.
- [x] One linked operator guide preserves every still-current public workflow
  removed from README and points to canonical CLI, Project-format, acquisition,
  research-lifecycle, evidence, and Studio references rather than duplicating
  their complete contracts.
- [x] `AGENTS.md` tells an Agent exactly which document to load for product
  orientation, operation, current capability, release history, release work,
  active implementation, and subsystem design.
- [x] Deterministic documentation tests enforce the entry-surface budget,
  ownership headings, direct routing links, version-frontmatter parity, and all
  repository double-links.
- [x] A fresh Grok coworker can discover how to create and orient a real Project
  and how to prepare a release from the front door, without being told which
  internal files to inspect.
- [ ] Focused tests, full regression, build/install smoke, clean-clone read
  path, and remote branch/tag identity pass for `v0.9.29`.

## Work

- [x] Extract the current operator walkthrough and reduce README to the bounded
  entrance surface without losing a working quick start.
- [x] Update AGENTS and documentation-system ownership rules; add regression
  tests for the new boundary.
- [x] Run a fresh Grok documentation-navigation trial and repair only reusable
  entry/routing friction.
- [ ] Advance version and release records, complete the release audit, publish
  the commit/tag, and verify remote identity.

## Findings and decisions

- 2026-08-02 — The repository already has a dedicated versioning-and-release
  document and an early AGENTS route to it. Creating another file would split
  authority; this patch will enforce and expose the existing boundary instead.
- 2026-08-02 — README length is not the only concern, but a physical-line
  ceiling is a useful executable tripwire. Rich detail remains available one
  direct link away and the ceiling can be deliberately revised with the
  documentation-system contract if the product entrance genuinely changes.
- 2026-08-02 — `AGENTS.md` is intentionally not subject to the same small line
  budget: it is an automatically loaded safety and research-governance surface.
  This topic removes duplication but does not hide mandatory invariants merely
  to optimize a count.
- 2026-08-02 — The first fresh Grok navigation trial found no missing or
  contradictory authority and correctly followed only five public documents,
  but noticed that README and the operator guide offered slightly different
  first-inspection command sets. Both now share the exact five-command entrance;
  deeper build/capability discovery remains an explicitly subsequent step.

## Verification

- README is 154 physical lines versus the enforced maximum of 220. It retains
  the required OpenAlice-readable version frontmatter and no longer contains
  the moved acquisition, intake, Session, Report/Dossier, or release-procedure
  sections. The operator guide contains all six required workflow stages.
- Focused documentation/version verification passes all five tests, including
  source/build version agreement and sdist/wheel provenance. All 1,524 current
  repository double-links resolve and `git diff --check` passes at the
  candidate checkpoint.
- First clean-clone field trial at documentation commit `c51f06d`: Grok `4.5`
  session `019fc010-6e3d-7b71-bb6e-a2d1352bad9c` used no memory, web, or
  subagents, opened exactly README → operator guide → version policy → STATUS
  → CHANGELOG, and recovered both handoffs without source/test/history access.
  It found only the differing initial command set. Assignment SHA-256 is
  `997766d7b0340668e8c4f6953548231e5dfb6b8bcb271e5184fd5b9daf1b5119`;
  transcript SHA-256 is
  `9a9fc39f1e3dff6abf2857767cef72e3f055ee5f76fbc18a57705b0829737988`.
- Final clean-clone retry at repaired commit `c8c26cc`: fresh Grok `4.5`
  session `019fc012-a855-7b70-b185-1d921feea53a` again recovered exact
  commands, blank-template choice, `research.md` gate, release authority,
  complete audit, publish order, and host-pin independence. It found no missing
  step or competing authority and left the checkout clean. Assignment SHA-256
  is unchanged; final transcript SHA-256 is
  `50ac4277966a2bb412958f233e8df0abd71e2049037f64f157d6b66d3b57c507`.
- The installed Grok CLI now exposes `grok-4.5`; its former
  `grok-4.5-build` model id was rejected before a Session began. This external
  model-name change did not alter the isolation or acceptance criteria.

## Progress log

- 2026-08-02 — Plan activated from clean published `v0.9.28` after measuring
  the 389-line README and confirming the intended ownership documents and
  initial AGENTS release route already exist.
- 2026-08-02 — Reduced README to 154 physical lines and moved the complete
  current Project, acquisition, intake, governed-research, evidence, and Studio
  path into one directly linked operator guide. Added AGENTS routing and a
  deterministic 220-line/section-ownership guard; focused documentation and
  version-contract tests pass.
- 2026-08-02 — Fresh no-memory/no-web/no-subagent Grok `4.5` session
  `019fc010-6e3d-7b71-bb6e-a2d1352bad9c` opened only README, the operator
  guide, version policy, STATUS, and CHANGELOG. It recovered both requested
  handoffs exactly and declared the entrance sufficient without source or test
  inspection. Its sole navigation friction was the initial command-set drift,
  which was repaired before the required fresh retry. The previously used
  `grok-4.5-build` id is no longer offered by the installed Grok CLI; the
  current same-generation model is `grok-4.5`.

## Completion

Pending.
