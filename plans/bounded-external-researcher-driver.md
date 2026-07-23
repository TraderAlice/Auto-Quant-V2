# Add a bounded external Researcher driver

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/research-session-loop]] and
  [[docs/design/external-researcher-driver]].

## Outcome

A replaceable external coding Agent can consume one complete Session brief,
edit only the existing governed worktree, return one strict proposal per turn,
and autonomously drive a bounded sequence of Experiment evaluations whose
prompts, logs, proposals, verdicts, stopping reason, budgets, and terminal
result remain inspectable.

## Context

The Session/Experiment milestone made the classic edit/evaluate loop safe, but
a caller must still manually alternate between editing and
`experiment evaluate`. AutoQuant should orchestrate that repetition without
hard-coding OpenAlice, Codex, or another model provider into Core.

INM and Mujica prove the useful connector shape: an explicit external command
receives structured current-best/history evidence and returns strict proposal
JSON. AutoQuant differs because the Researcher edits code in the already
confined Session worktree; the Harness continues to own diff validation,
evaluation, verdict, restoration, and promotion.

## Scope

### In scope

- A versioned Researcher stdin/stdout JSON protocol.
- One explicit user-supplied command, bounded per-turn and in aggregate.
- A fresh complete Session brief for every turn.
- Strict `propose` and `stop` responses.
- Automatic Experiment evaluation after a valid proposal.
- Restoration to the leader after command/protocol failure when authority
  permits.
- Immutable Campaign evidence with per-turn input, stdout, stderr, proposal,
  Experiment reference, timing, errors, and terminal manifest.
- `aq research run/list/show` with human/JSON parity and capability discovery.
- Fast fake-Researcher tests covering KEEP/REVERT/stop, process failure,
  timeout, malformed output, fixed-file escape, and budget exhaustion.

### Out of scope

- Shipping credentials or one vendor-specific Agent client.
- OS sandboxing the external command.
- Parallel Researcher turns or competing Session branches.
- Automatic Project promotion.
- Statistical stopping or token accounting not reported by the Researcher.
- Studio implementation.

## Acceptance

- [x] A fake external Researcher can autonomously produce KEEP then REVERT then
  STOP from fresh briefs and the Session remains consistent.
- [x] Command exit, timeout, malformed response, fixed-file mutation, and
  unchanged proposal create inspectable failed Campaign evidence.
- [x] Max-turn and wall-clock budgets are enforced and recorded.
- [x] The Researcher never gains Judge, verdict, or promotion authority.
- [x] Campaign listing/show verifies terminal hashes and referenced immutable
  Experiments.
- [x] CLI capabilities and schemas fully describe the protocol.
- [x] Documentation, full bounded tests, build, legacy discovery, and a real
  provider-neutral command smoke pass.

## Work

- [x] Audit INM and Mujica external command and source-research protocols.
- [x] Define Researcher response, turn, Campaign result, and manifest formats.
- [x] Implement bounded command invocation and strict response parsing.
- [x] Implement Campaign execution, failure restoration, evidence, and loads.
- [x] Add CLI, capability, and schema surfaces.
- [x] Add focused and end-to-end tests.
- [x] Update durable design and public documentation.
- [x] Complete acceptance, commit, and publish.

## Findings and decisions

- 2026-07-24 — The command is an explicit user-authorized shell connector, not
  a hidden provider choice. Its authority is no broader than any other external
  coding Agent: ordinary host execution plus a Session worktree contract.
- 2026-07-24 — The response describes hypothesis/strategy or STOP; it does not
  contain metrics or verdicts. Those always come from immutable Judge Runs.
- 2026-07-24 — Campaign evidence is distinct from Session and Experiment
  evidence. A Campaign may fail while every Experiment it already produced
  remains valid.
- 2026-07-24 — Aggregate wall time reserves the fixed Judge timeout before
  starting another Researcher turn. Reaching a declared budget is terminal
  `budget_exhausted` evidence rather than a protocol failure.

## Verification

- `git diff --check`
- `uv run python -m compileall -q autoquant tests`
- `uv run python scripts/check_doc_links.py` — 99 links resolved.
- `uv run python -m unittest discover -s tests -v` — 47 tests passed.
- `uv build` — source distribution and wheel built.
- `uv run prepare.py --list-profiles` and
  `uv run run.py --list-profiles` — legacy crypto/equity profiles discovered
  without executing a backtest.
- `uv run python -m unittest
  tests.test_cli.AgentCliTests.test_json_cli_runs_and_inspects_a_bounded_external_campaign
  -v` — an actual external Python command completed a CLI Campaign and its
  immutable result was listed and shown.

## Progress log

- 2026-07-24 — Plan created after the manual governed loop was published in
  commit `536bf5a`.
- 2026-07-24 — Implemented the connector, Campaign publication/verification,
  Session worktree reconstruction, public CLI/schema/capability surfaces, and
  deterministic fake-Researcher coverage.
- 2026-07-24 — All acceptance checks passed; the bounded external Researcher
  driver is ready to publish.

## Completion

AutoQuant now composes any explicit host shell Researcher with the governed
Session loop through a strict provider-neutral protocol. Core retains fixed
Judge, verdict, restoration, immutable evidence, and promotion authority.
