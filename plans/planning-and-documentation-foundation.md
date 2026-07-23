# Establish planning and design-documentation governance

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/documentation-system]] and
  [[docs/ARCHITECTURE]].

## Outcome

AutoQuant V2 has a repository-native planning and documentation protocol that
a human or Coding Agent can use to coordinate long-running development, retain
discoveries, distinguish live work from durable system truth, and verify every
design route with a fast executable check.

## Context

Integrated Industry Maker and Mujica Robot already use the same family of
file-native engineering rules: indexed live plans, subsystem design documents,
bounded verification, and durable evidence. AutoQuant V2 needs that
coordination layer before Workspace, Project, Run, ML, or Studio implementation
begins, otherwise the architectural work will be spread across chat history and
ad hoc task notes.

The rules should preserve the proven semantics without copying IIM's industrial
domain language or its Bun/TypeScript tooling into this Python/uv repository.

## Scope

### In scope

- Add repository guidance that routes non-trivial changes through live plans
  and active design documents.
- Add a plan index, reusable plan template, and this initial execution record.
- Establish an honest architecture document that separates current V0.5
  compatibility behavior from the intended Workspace/Project design.
- Add a zero-dependency Python double-link checker and exercise it in the fast
  test suite.
- Link the new governance surfaces from the repository README.

### Out of scope

- Implementing Workspace, Project, Study, Session, RunResult, Candidate, or
  Studio code.
- Migrating the current flat strategy directory or historical snapshots.
- Starting an autonomous research loop, downloading data, or running a full
  backtest.
- Choosing the final ML execution contract.

## Acceptance

- [x] A contributor can discover when a plan is required, create one from a
  stable template, and follow its lifecycle from the repository root.
- [x] Plans and design documents have explicit, non-overlapping ownership.
- [x] The active architecture documents current reality, target
  Workspace/Project ownership, invariants, non-goals, and known gaps.
- [x] Every repository double-link resolves under a fast Python command.
- [x] The existing deterministic unit suite remains green without running a
  long backtest.

## Work

- [x] Adapt the IIM plan lifecycle and contributor routing to AutoQuant.
- [x] Add the documentation-system and architecture design documents.
- [x] Implement the double-link checker and its regression test.
- [x] Run link validation and the complete bounded unit suite.
- [x] Audit acceptance, move the plan to completed, and publish the change.

## Findings and decisions

- 2026-07-24 — AutoQuant V2 already contains a transitional V0.5 Freqtrade
  Harness. The architecture document must label that state honestly rather
  than describe unimplemented Workspace and Project schemas as current code.
- 2026-07-24 — The repository uses Python and `uv`; a standard-library Python
  checker preserves IIM's executable-documentation invariant without adding
  Bun solely for documentation.
- 2026-07-24 — The first plan governs only the development system. Workspace,
  Project, RunResult, ML, and Studio belong in separately reviewed plans.

## Verification

- `uv run python scripts/check_doc_links.py`: 29 repository double-links
  resolve.
- `uv run python -m unittest discover -s tests -v`: 12 bounded tests pass.
- `uv run prepare.py --list-profiles`: lists the crypto and US-equity profiles
  without downloading data.
- `uv run run.py --list-profiles`: lists the same two profiles without starting
  a backtest.
- `git diff --check`: no whitespace errors.

## Progress log

- 2026-07-24 — Plan created and indexed as active.
- 2026-07-24 — Contributor guide, documentation rules, architecture baseline,
  plan template, and executable documentation check added.
- 2026-07-24 — Link validation, the complete bounded unit suite, and both
  profile-discovery CLI paths passed; acceptance audit completed.

## Completion

Shipped the repository planning index, reusable plan lifecycle, contributor
routing, durable documentation ownership rules, honest Workspace/Project
architecture baseline, and a zero-dependency documentation-link check exercised
by the fast unit suite. AutoQuant V2 can now coordinate long-running human and
Agent development without relying on chat history or conflating active plans
with current system truth.

Workspace, Project, RunResult, ML, and Studio implementation remain outside
this bounded outcome and will receive their own indexed plans when commissioned.
