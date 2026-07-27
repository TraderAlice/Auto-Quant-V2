# Clarified English research briefs

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/agent-operator-experience]], and [[docs/PROJECT_FORMAT]].

## Outcome

Every AutoQuant Project starts from an Agent-maintained English Markdown
research brief. The Quant Agent clarifies material ambiguity with the
delegating Agent or user before beginning data, code, or evaluation work, while
strict manifests remain later machine contracts rather than an intake
substitute.

## Context

AutoQuant receives assignments through ordinary human or Agent conversation.
The workbench must not require a rigid external intake parser, but a coding
Agent also must not silently invent the caller's investment question,
universe, horizon, constraints, evaluation meaning, or desired deliverable.
The repository currently creates `research.md` for every Project but does not
make clarification or the desk's English working language explicit.

## Scope

### In scope

- Define the pre-research clarification discipline in `AGENTS.md`.
- Make blank and built-in Project research programs carry the same English
  Markdown brief guidance.
- Document the boundary between caller-language conversation, English
  workbench materials, and later strict execution contracts.
- Add focused regression coverage for generated Project guidance.

### Out of scope

- Parse natural-language requests automatically.
- Define a rigid schema for the Markdown brief.
- Change Study, Session, Run, Report, or host communication protocols.
- Translate user-facing conversation or require the caller to use English.

## Acceptance

- [x] A newly seated Agent is told to write or update `research.md` in English
  before data, code, or backtest work.
- [x] The guidance identifies material ambiguities that require asking the
  delegating Agent or user and requires clarification until the question is
  bounded and testable.
- [x] Agent-owned methods may use judgment, while caller-owned intent may not
  be invented.
- [x] Blank and all built-in Project templates expose the same brief and
  clarification contract.
- [x] Documentation states that strict manifests lock understood execution
  authority but do not replace the Markdown brief.
- [x] Focused tests and documentation-link validation pass.

## Work

- [x] Inspect repository, blank-Project, and built-in template entry points.
- [x] Define one concise research-brief and language contract.
- [x] Update Agent guidance, Project starters, CLI output, and durable design
  docs.
- [x] Add and run focused regression checks.
- [x] Complete the acceptance audit, commit, and push the milestone.

## Findings and decisions

- 2026-07-27 — Every Project already owns a root `research.md`, but blank
  Projects and four built-in templates obtain its contents from different
  sources, so both paths need the same stable marker and rule.
- 2026-07-27 — Markdown remains intentionally flexible and Agent-maintained.
  JSON requests and manifests are derived locked contracts only after intent
  is clear enough to execute.
- 2026-07-27 — Existing `aq project create` already owns the correct
  construction boundary. Its envelope now exposes `researchBriefPath` and a
  mutable `research-brief` artifact instead of requiring a second scaffold
  command.

## Verification

- `uv run python -m unittest tests.test_workspace tests.test_cli` — 21 tests
  passed in 40.480 seconds.
- `uv run python scripts/check_doc_links.py` — 894 documentation double-links
  resolve.
- `uv build` — source distribution and wheel built successfully; all four
  built-in `research.md` templates are present in the wheel.
- `uv run aq capabilities --json` — public discovery envelope emitted.
- `uv run python -m compileall -q autoquant tests/test_workspace.py
  tests/test_cli.py` — passed.
- `git diff --check` — clean.

## Progress log

- 2026-07-27 — Plan created and Project entry points inspected.
- 2026-07-27 — Added the repository start discipline, generated brief
  guidance, CLI artifact/path projection, built-in template gates, durable
  design documentation, and regression coverage.

## Completion

Completed on 2026-07-27. Every new Project now exposes an English Markdown
research brief as its first working surface. Quant Agents are instructed to
clarify caller-owned ambiguity until the assignment is bounded and falsifiable,
while retaining judgment over research methods. Strict requests and manifests
remain later machine contracts, and caller-facing conversation remains free to
use the context-appropriate language.
