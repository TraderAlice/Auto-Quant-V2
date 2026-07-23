# AutoQuant V2 CLI

Status: Workspace/Project, Study/Run evidence, and governed
Session/Experiment research implemented.

`aq` is the public human- and Agent-facing command line interface. Humans
receive compact text by default. `--json` emits exactly one versioned envelope.

## Discovery

```bash
aq capabilities
aq capabilities --json
aq schema
aq schema project --json
```

`capabilities --json` is the authoritative machine discovery surface. Each
command descriptor includes:

- stable command id and usage;
- description and operation effect;
- JSON support;
- positional and option argument types, requirements, defaults, and choices;
- success, failure, and usage exit codes;
- output sections, currently empty for the foundation commands.

Agents should discover the contract rather than scrape `--help`.

## Workspace and Project commands

```bash
aq workspace init <workspace-dir> [--name NAME] [--json]
aq project create <workspace-dir> <project-id> \
  [--name NAME] [--description TEXT] [--json]
aq project list <workspace-dir> [--json]
aq project default <workspace-dir> <project-id> [--json]
aq validate <project-or-workspace-dir> [--project ID] [--json]
aq inspect <project-or-workspace-dir> [--project ID] [--json]
```

`validate` and `inspect` resolve exactly one Project before reading its
manifest. A direct Project path rejects `--project`; a Workspace path selects
the explicit id or its default.

## Study and Run commands

```bash
aq study create <path> <study-id> \
  --subject-kind factor \
  --judge judges/evaluate.py \
  --judge-path 'judges/**' \
  --editable 'factors/**' \
  --metric score \
  --dataset-id synthetic-bars \
  --asset-class equity \
  --asset AAA/USD \
  --start 2026-01-01 \
  --end 2026-01-31

aq study list <path> [--project ID] [--json]
aq study inspect <path> --study ID [--project ID] [--json]
aq run execute <path> --study ID [--project ID] [--json]
aq run list <path> [--study ID] [--project ID] [--json]
aq run show <path> --run ID [--project ID] [--json]
```

`study create` validates the complete fixed contract immediately. `run execute`
freezes inputs, runs the Python Judge under its timeout, and atomically
publishes one immutable Run whether the Judge succeeds or fails. `run list`
and `run show` verify terminal file hashes before returning evidence.

A failed Run is a successful artifact-creation operation whose RunResult has
`status: failed`; it retains errors and logs. A CLI error means trustworthy Run
evidence could not be created or verified.

## Session and Experiment commands

```bash
aq session start <path> --study ID [--project ID] [--json]
aq session list <path> [--project ID] [--json]
aq session show <path> --session ID [--project ID] [--json]
aq session promote <path> --session ID [--project ID] [--json]

aq experiment evaluate <path> \
  --session ID \
  --hypothesis TEXT \
  [--project ID] [--json]
aq experiment list <path> --session ID [--project ID] [--json]
aq experiment show <path> \
  --session ID \
  --experiment ID \
  [--project ID] [--json]
```

`session start` runs a fresh successful baseline and returns an Agent brief
containing the disposable worktree, fixed program, editable closure, leader,
authority status, and exact next commands. The caller edits only that worktree.

`experiment evaluate` freezes the candidate into a canonical Run, compares the
primary metric with the current leader, publishes immutable Experiment
evidence, and returns `KEEP`, `REVERT`, or `CRASH`. REVERT and CRASH restore the
leader bytes in the worktree. `session promote` is the only operation that
copies a KEEP into Project source; it rejects a stale Project base and rolls
back if the source, receipt, and Session pointer cannot all be committed.

## Success envelope

```json
{
  "schemaVersion": 1,
  "ok": true,
  "command": "project.create",
  "context": {
    "scope": "project",
    "project": {
      "id": "factor-lab",
      "name": "Factor Lab",
      "rootDir": "/absolute/path/projects/factor-lab"
    }
  },
  "data": {},
  "diagnostics": [],
  "artifacts": [
    {
      "kind": "project",
      "id": "factor-lab",
      "path": "/absolute/path/projects/factor-lab/autoquant.json",
      "immutable": false
    }
  ],
  "nextActions": [
    {
      "id": "validate",
      "description": "Validate the newly created Project.",
      "argv": [
        "aq",
        "validate",
        "/absolute/path/projects/factor-lab",
        "--json"
      ],
      "effect": "read-only"
    }
  ]
}
```

Contexts are `global`, `workspace`, or `project`. Artifacts name an identity,
path, kind, and mutability. `nextActions.argv` is directly executable and its
effect is explicit.

Current operation effects are:

- `read-only`;
- `creates-artifact`;
- `mutates-workspace`;
- `mutates-project`.

Only `session.promote` currently uses `mutates-project`, after locked-history,
stale-base, source-hash, and rollback checks. A future Studio must project
these same Core operations and effects rather than write files independently.

## Error envelope

```json
{
  "schemaVersion": 1,
  "ok": false,
  "command": "project.create",
  "context": {
    "scope": "global"
  },
  "error": {
    "code": "validation.failed",
    "message": "Must be a lowercase kebab-case id",
    "retryable": false,
    "issues": [
      {
        "path": "project_id",
        "code": "schema.id",
        "message": "Must be a lowercase kebab-case id"
      }
    ]
  }
}
```

## Exit behavior

- `0`: success;
- `1`: validation or operation failure;
- `2`: CLI usage failure.

When `--json` is present, validation and usage failures still emit one JSON
error envelope. Human errors are written to stderr.

## Packaging and invocation

The repository installs the command as a Python project:

```bash
uv sync
uv run aq capabilities --json
```

`python -m autoquant` is an equivalent source-tree entry point.

## Current boundary

This CLI owns Workspace/Project lifecycle, fixed Study and immutable Run
evidence, and the governed Session/Experiment edit/evaluate/promotion loop. The
legacy `prepare.py` and `run.py` commands remain the V0.5 compatibility
Harness. External Researcher invocation, automatic stopping, richer robust
comparison, and Studio remain separate future surfaces.

## Verification

```bash
uv run aq capabilities --json
uv run python -m unittest \
  tests.test_cli tests.test_studies tests.test_runs tests.test_sessions -v
```
