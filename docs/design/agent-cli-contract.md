# Agent CLI contract

Status: implemented for Workspace, Project, Study, Run, Session, Experiment,
and bounded Research Campaign operations.

Related: [[docs/CLI]], [[docs/PROJECT_FORMAT]],
[[docs/design/workspace-project-boundaries]], and
[[docs/design/study-run-evidence]], and
[[docs/design/external-researcher-driver]].

## Scope

This document owns versioned command envelopes, machine capability discovery,
contexts, artifact references, next actions, operation effects, and exit
behavior. It does not own the underlying Workspace/Project semantics or
Study/Run evaluation rules.

## Principles

- Agents consume structured contracts rather than scrape terminal prose.
- Humans and Agents invoke the same Core operations.
- JSON output is one complete envelope, not mixed logs and payload fragments.
- Every mutating or artifact-producing operation declares its effect.
- Successful commands expose executable next actions instead of requiring the
  caller to guess the next syntax.
- Errors retain stable codes and path-level issues.
- A future Studio is another projection of these operations, never a second
  evaluator or hidden write path.

## Source of truth

- Envelope constructors and schema version: `autoquant/cli_contract.py`
- Capability descriptors: `autoquant/capabilities.py`
- Parser, dispatch, human rendering, and JSON rendering: `autoquant/cli.py`
- Canonical command reference: [[docs/CLI]]
- Contract tests: `tests/test_cli.py`

## Envelope invariants

1. Every JSON success contains `schemaVersion`, `ok`, `command`, `context`,
   `data`, `diagnostics`, `artifacts`, and `nextActions`.
2. Every JSON failure contains `schemaVersion`, `ok`, `command`, `context`, and
   an `error` with `code`, `message`, `retryable`, and `issues`.
3. Context scope is exactly `global`, `workspace`, or `project`.
4. Artifact references declare `kind`, `id`, absolute `path`, and
   `immutable`.
5. Next actions declare stable `id`, human description, executable `argv`, and
   operation `effect`.
6. Capability discovery describes every public subcommand and every public
   argument, including JSON support and exit codes.
7. Exit `0` means success, `1` means a validation/operation failure, and `2`
   means invalid CLI usage.
8. `--json` usage errors remain parseable JSON rather than argparse prose.
9. Human output may improve without changing the machine contract.

## Operation effects

The current CLI supports:

- `read-only`;
- `creates-artifact`;
- `mutates-workspace`;
- `mutates-project`;
- `long-running-server`.

Study/Session creation, Run execution, and Experiment evaluation use
`creates-artifact`. Bounded `research.run` also uses `creates-artifact`: it may
advance the Session leader through ordinary KEEP Experiments but never copies
source into the owning Project. Only
`session.promote` uses `mutates-project`, after stale-base validation and
rollback-safe receipt publication. Future operations may add `mode-dependent`
only when their confirmation, progress, and evidence contracts are defined.
`studio.serve` uses `long-running-server`, does not support terminal JSON, and
exposes only fixed read-only HTTP routes.

## CLI-to-Studio flow

```text
Core operation
├── aq human projection
├── aq JSON envelope
└── Studio read-only snapshot and browser projection
```

Core operation data is authoritative. The Studio must not reimplement manifest
validation, Project selection, evaluation, or mutation policy.

Long-running research will require versioned progress events on stderr or a
separate stream while stdout retains one terminal envelope. That protocol is a
known future design task, not an implied behavior of the current CLI.

## Non-goals

- Treating natural-language terminal output as an API.
- Generic shell orchestration or a distributed task queue.
- Emitting unstructured Python tracebacks for expected validation failures.
- Claiming a next action is safe without declaring its effect.

## Change checklist

- Add or update the capability descriptor with every public command change.
- Exercise both human and JSON surfaces.
- Preserve the envelope schema or deliberately increment `schemaVersion`.
- Add stable error codes and issue paths for expected failure modes.
- Provide truthful artifacts and next actions; never advertise an operation
  that does not exist.
- Add the same Core operation to Studio rather than implementing a UI-only
  mutation.

## Verification

```bash
uv run aq capabilities --json
uv run python -m unittest tests.test_cli -v
```

## Known gaps

- No progress-event envelope exists.
- No output section selection exists.
- No confirmation receipt exists for future Project mutations.
- Studio has no confirmed mutation routes.
