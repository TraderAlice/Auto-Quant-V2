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

- [ ] README is a concise product entrance no longer than 220 physical lines
  and contains no detailed release checklist, historical release ledger, data
  packaging tutorial, Session loop, Report/Dossier procedure, or feature-by-
  feature capability catalogue.
- [ ] One linked operator guide preserves every still-current public workflow
  removed from README and points to canonical CLI, Project-format, acquisition,
  research-lifecycle, evidence, and Studio references rather than duplicating
  their complete contracts.
- [ ] `AGENTS.md` tells an Agent exactly which document to load for product
  orientation, operation, current capability, release history, release work,
  active implementation, and subsystem design.
- [ ] Deterministic documentation tests enforce the entry-surface budget,
  ownership headings, direct routing links, version-frontmatter parity, and all
  repository double-links.
- [ ] A fresh Grok coworker can discover how to create and orient a real Project
  and how to prepare a release from the front door, without being told which
  internal files to inspect.
- [ ] Focused tests, full regression, build/install smoke, clean-clone read
  path, and remote branch/tag identity pass for `v0.9.29`.

## Work

- [x] Extract the current operator walkthrough and reduce README to the bounded
  entrance surface without losing a working quick start.
- [ ] Update AGENTS and documentation-system ownership rules; add regression
  tests for the new boundary.
- [ ] Run a fresh Grok documentation-navigation trial and repair only reusable
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

## Verification

Pending.

## Progress log

- 2026-08-02 — Plan activated from clean published `v0.9.28` after measuring
  the 389-line README and confirming the intended ownership documents and
  initial AGENTS release route already exist.
- 2026-08-02 — Reduced README to 154 physical lines and moved the complete
  current Project, acquisition, intake, governed-research, evidence, and Studio
  path into one directly linked operator guide. Added AGENTS routing and a
  deterministic 220-line/section-ownership guard; focused documentation and
  version-contract tests pass.

## Completion

Pending.
