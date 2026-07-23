# AutoQuant V2 Project format

Status: V1 Workspace and Project manifests implemented.

AutoQuant uses a long-lived Workspace containing immediate, self-contained
Projects. The Workspace is the standardized Harness workbench; each Project is
the construction site for one evolving body of quantitative research.

## Workspace

A Workspace contains:

```text
quant-workspace/
├── autoquant-workspace.json
└── projects/
    ├── factor-lab/
    └── ml-lab/
```

`autoquant-workspace.json` V1:

```json
{
  "schema_version": 1,
  "name": "Quant Research Desk",
  "projects_directory": "projects",
  "default_project": "factor-lab"
}
```

The Workspace manifest has no datasets, factors, strategies, models, Studies,
or Runs. It owns only discovery and an optional default Project.

## Project

`aq project create` produces a complete Project:

```text
factor-lab/
├── autoquant.json
├── research.md
├── strategies/
├── factors/
├── models/
├── studies/
├── data/
│   └── .gitignore
├── runs/
└── .autoquant/
    └── .gitignore
```

`autoquant.json` V1:

```json
{
  "schema_version": 1,
  "id": "factor-lab",
  "name": "Factor Lab",
  "description": "Mine robust cross-asset factors",
  "research_program": "research.md",
  "directories": {
    "strategies": "strategies",
    "factors": "factors",
    "models": "models",
    "studies": "studies",
    "data": "data",
    "runs": "runs",
    "cache": ".autoquant"
  }
}
```

The declared directory names are semantic ownership slots, not complete Study
or Run contracts. Those schemas will be added only with their execution,
identity, and immutability rules.

## Identity and confinement

- Project ids use lowercase letters, digits, and single hyphen-separated
  segments.
- A Project id must match its immediate directory name.
- `projects_directory`, `research_program`, and every Project directory are
  confined POSIX relative paths.
- Unknown manifest keys fail validation.
- Workspace roots, the Projects directory, Project entries, the Project root,
  and declared Project paths cannot be symlinks.
- Workspace discovery scans one directory level. Every visible entry must be a
  complete real Project directory.
- A directory cannot contain both Workspace and Project manifests.
- A direct Project path cannot also receive `--project`; Workspace paths resolve
  either the explicit id or the default.

These rules prevent one Project from silently reading or mutating another
Project through Workspace inheritance or path traversal.

## Project-local data

The generated `data/` directory ignores its contents by default so OHLCV and
later ML datasets do not enter the Harness source repository accidentally.
Project-locality does not imply that every large byte must be copied: a future
dataset manifest may bind content-addressed external storage, but the Project
must retain the exact dataset identity needed for reproduction.

`.autoquant/` is disposable Project-local cache state. It cannot be the source
of durable research truth.

## Research program

`research.md` is human-owned guidance for the Project. The generated starter
requires:

- a clear research question;
- fixed evaluation inputs and acceptance rules while comparing candidates;
- explicit Harness, dataset, universe, and time-range evidence;
- one falsifiable code change at a time;
- explicit KEEP, REVERT, or BRANCH decisions;
- no candidate authority over the Harness or locked Judge.

The current file is guidance only. A later Research Lab contract will bind the
editable source closure, budgets, benchmarks, Sessions, Experiments, and
promotion policy.

## Canonical schemas

Machine-readable JSON Schemas are available without loading a Project:

```bash
aq schema
aq schema workspace --json
aq schema project --json
```

The Python validators are authoritative executable behavior:
`autoquant/workspace.py`.

## Compatibility surface

The repository-root `harness.json`, `user_data/strategies/`, `data/`,
`prepare.py`, and `run.py` remain the V0.5 flat compatibility Harness documented
in [[docs/harness]]. They are not a generated V2 Project. Migrating that
research arena will be a separately planned change that preserves historical
snapshots.

## Verification

```bash
uv run aq schema workspace --json
uv run aq workspace init /tmp/quant-workspace
uv run aq project create /tmp/quant-workspace factor-lab
uv run aq validate /tmp/quant-workspace
uv run aq inspect /tmp/quant-workspace --project factor-lab --json
uv run python -m unittest tests.test_workspace tests.test_cli -v
```
