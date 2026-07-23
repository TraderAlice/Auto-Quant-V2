# Establish governed Research Sessions and Experiments

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/ARCHITECTURE]],
  [[docs/design/study-run-evidence]], and
  [[docs/design/research-session-loop]].

## Outcome

An Agent can start from one successful locked Study baseline, edit only a
disposable candidate source closure, evaluate a sequence of hypotheses through
the unchanged Judge, receive immutable KEEP/REVERT/CRASH Experiment evidence,
and explicitly promote the best accepted source back to the Project without
overwriting concurrent Project changes.

## Context

Study/Run V1 produces trustworthy evidence but does not yet provide the classic
AutoQuant operating loop. Editing Project source in place would make rejected
candidates destructive, let a candidate touch its Judge, and make long-running
research impossible to inspect or resume safely.

Mujica's transferable rules are disposable candidate construction, locked
evaluation, manifest-last evidence, hash-checked promotion, and no source
publication on REVERT/CRASH. AutoQuant needs those rules around arbitrary
strategy/factor/model Python closures while keeping the Researcher itself
replaceable.

## Scope

### In scope

- A strict Project-local Session contract pinned to one Study and successful
  baseline Run.
- One durable disposable working Project per Session, populated only with fixed
  Study/Judge inputs and the declared editable source closure.
- Session start/list/show operations that expose the exact candidate edit root,
  fixed program, current leader, history, and next Agent action.
- Experiment evaluation after an Agent edits the working copy.
- Validation that fixed inputs remain unchanged and all candidate files stay
  within the declared editable closure.
- Immutable Experiment evidence with hypothesis, source diff, baseline and
  candidate Runs/metrics, delta, verdict, errors, and terminal hashes.
- Deterministic KEEP/REVERT/CRASH decisions from the Study objective.
- Automatic restoration of the leader source after REVERT or CRASH.
- Explicit promotion of the current KEEP with stale-base detection, staged
  hash verification, and rollback on failure.
- Human and JSON CLI parity plus fast synthetic tests.

### Out of scope

- Calling a specific external coding-agent provider.
- Natural-language proposal generation or automatic stopping policy.
- Parallel branches, Pareto frontiers, per-asset guardrails, or statistical
  significance gates.
- Studio implementation.
- Long market-data backtests.

## Acceptance

- [x] Starting a Session executes or verifies a successful baseline and creates
  a resumable working copy without changing Project candidate source.
- [x] The Session exposes a complete Agent brief: program, editable closure,
  worktree, leader metric/hash, history, and exact evaluate command.
- [x] A better candidate produces KEEP and becomes the Session leader.
- [x] An inferior candidate produces REVERT and restores leader bytes.
- [x] A failed Judge produces CRASH evidence and restores leader bytes.
- [x] Candidate changes to fixed or undeclared paths are rejected before Judge
  execution.
- [x] Every Experiment and Run remains inspectable and tamper-evident.
- [x] Promotion succeeds only for the exact current KEEP against the unchanged
  Project base and leaves a receipt; stale promotion changes nothing.
- [x] Documentation links, full bounded tests, build, legacy profile discovery,
  and real human/JSON CLI flows pass.

## Work

- [x] Audit the classic AutoQuant loop and Mujica/INM source-research and
  promotion invariants.
- [x] Define Session, Experiment, verdict, working-copy, and promotion formats.
- [x] Refactor Run execution to accept a separately confined execution Project
  while publishing evidence to the owning Project.
- [x] Implement Session creation/loading and disposable working construction.
- [x] Implement Experiment comparison, evidence, and candidate restoration.
- [x] Implement guarded promotion and receipt.
- [x] Add CLI/capability/schema surfaces and Agent-oriented next actions.
- [x] Add focused and end-to-end tests.
- [x] Update durable design and public documentation.
- [x] Complete acceptance, commit, and publish.

## Findings and decisions

- 2026-07-24 — A Session working copy is durable and resumable, but it is not a
  second Project of record. Canonical Runs and promotion receipts remain in the
  owning Project.
- 2026-07-24 — V1 uses one linear leader. A KEEP advances it; REVERT and CRASH
  restore it. Branching and Pareto retention require a separate design.
- 2026-07-24 — The external Researcher is intentionally outside this milestone.
  The CLI must first make the edit/evaluate loop safe and fully discoverable so
  Codex, another Agent, or a human can all drive the same protocol.
- 2026-07-24 — Candidate Runs execute from the Session worktree but publish in
  the owning Project. `execute_study` independently proves that fixed
  Study/program/Judge/dataset identities match across those roots.
- 2026-07-24 — A mutable Session leader is never accepted on its own. Every
  operation reconstructs the linear leader and next sequence from immutable
  Experiment Runs and recomputes each verdict.
- 2026-07-24 — Promotion includes Project source, one-time receipt, and Session
  status in one rollback boundary. A simulated receipt commit failure restored
  both source and Session state.

## Verification

- `uv run python scripts/check_doc_links.py` — 87 links resolved.
- `uv run python -m unittest discover -s tests -v` — 41 bounded tests passed.
- `uv build` — source distribution and wheel built.
- `uv run prepare.py --list-profiles` and
  `uv run run.py --list-profiles` — both legacy profiles remained discoverable.
- `uv run aq capabilities --json`, `uv run aq schema session --json`, and
  `uv run aq schema experiment --json` — public Agent discovery passed.
- `git diff --check` and `uv run python -m compileall -q autoquant` — passed.
- A disposable real Workspace completed human and JSON Study creation,
  `session start`, Agent-style worktree editing, a `KEEP` Experiment from
  `score=1.0` to `score=2.5`, Session/history inspection, guarded promotion,
  receipt verification, and promoted Project source inspection.

## Progress log

- 2026-07-24 — Plan created after Study/Run evidence was fixed and published in
  commit `5217cdf`.
- 2026-07-24 — Added the `sessions/` Project slot, strict Session and Experiment
  schemas, separately rooted candidate execution, source diffs, linear verdict
  history, leader restoration, and guarded promotion.
- 2026-07-24 — Exercised KEEP, REVERT, CRASH, fixed/undeclared changes,
  Experiment tampering, invented leader pointers, stale Project bases, and
  promotion rollback failure.

## Completion

Completed on 2026-07-24. The stable manual Agent protocol now exists. The next
independent milestone can invoke a replaceable external Researcher with
explicit iteration/time budgets and stopping evidence, without giving that
Researcher authority over the Judge or promotion.
