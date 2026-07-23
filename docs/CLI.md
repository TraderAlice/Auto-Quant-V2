# AutoQuant V2 CLI

Status: Workspace/Project plus Study/Run evidence implemented.

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
- `mutates-workspace`.

`mutates-project` will be introduced only when a reviewed Project operation
exists. A future Studio must project these same Core operations and effects
rather than write files independently.

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

This CLI currently owns Workspace/Project lifecycle plus fixed Study and
immutable Run evidence. The legacy `prepare.py` and `run.py` commands remain
the V0.5 compatibility Harness. Research Sessions, Experiments, Candidate
comparison/promotion, and Studio commands will join `aq capabilities` only
after their Core contracts exist.

## Verification

```bash
uv run aq capabilities --json
uv run python -m unittest tests.test_cli tests.test_studies tests.test_runs -v
```
