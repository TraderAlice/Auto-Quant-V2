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
├── judges/
├── studies/
├── sessions/
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
    "judges": "judges",
    "studies": "studies",
    "sessions": "sessions",
    "data": "data",
    "runs": "runs",
    "cache": ".autoquant"
  }
}
```

The declared directory names are semantic ownership slots. Study, Judge output,
and RunResult contracts appear below.

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

## Study

Each fixed evaluation contract lives beneath its Project:

```text
studies/
└── factor-quality/
    ├── study.json
    └── program.md
```

`study.json` V1:

```json
{
  "schema_version": 1,
  "id": "factor-quality",
  "name": "Factor Quality",
  "description": "Measure one cross-asset factor",
  "program": "program.md",
  "subject": {
    "kind": "factor",
    "name": "candidate-factor",
    "version": "working"
  },
  "editable": {
    "paths": ["factors/**"]
  },
  "judge": {
    "kind": "python",
    "entrypoint": "judges/evaluate.py",
    "paths": ["judges/**"],
    "arguments": [],
    "timeout_seconds": 60
  },
  "objective": {
    "metric": "robust_sharpe",
    "direction": "maximize",
    "minimum_improvement": 0.01
  },
  "dataset": {
    "id": "us-equities-bars",
    "version": "2026-07-24",
    "asset_class": "equity",
    "universe": ["SPY/USD", "QQQ/USD"],
    "time_range": {
      "start": "2021-01-01",
      "end": "2025-12-31"
    }
  }
}
```

Subject kinds are `strategy`, `factor`, `model`, or `research`. Editable paths
must be exact files or trailing-`/**` closures beneath the Project's declared
strategy, factor, or model directories. Judge paths use the same closure syntax
but stay beneath the declared Judge directory and are fixed and disjoint from
editable source.

The Study's `program.md` is human-owned operating intent. The Study, program,
Judge closure, objective, and dataset identity are never candidate-editable.

## Python Judge output

The fixed Judge receives paths through environment variables documented in
[[docs/design/study-run-evidence]] and must write:

```json
{
  "schema_version": 1,
  "status": "succeeded",
  "summary": "The factor remains positive across the declared universe.",
  "metrics": {
    "robust_sharpe": 0.82,
    "per_asset": {
      "SPY/USD": {"sharpe": 0.91},
      "QQQ/USD": {"sharpe": 0.82}
    }
  },
  "artifacts": [
    {
      "kind": "report",
      "path": "factor-report.json",
      "description": "Per-asset factor evidence"
    }
  ],
  "errors": []
}
```

Metrics may contain nested finite JSON values. A successful result must provide
the Study's primary metric as a finite top-level number. Every file written to
the artifact directory must appear exactly once in `artifacts`.

## Immutable Run

Completed Runs live at:

```text
runs/
└── run-<UTC timestamp>-<identity>/
    ├── inputs/
    │   ├── study.json
    │   ├── program.md
    │   ├── identity.json
    │   └── judge-sources/<project-relative files>
    ├── sources/<editable project-relative files>
    ├── artifacts/<declared Judge files>
    ├── judge-output.json
    ├── stdout.txt
    ├── stderr.txt
    ├── result.json
    └── manifest.json
```

`result.json` is the structured RunResult. It records:

- terminal status, summary, timestamps, and duration;
- complete input and Study-input hashes;
- Harness id/version/commit/dirty/source/Python identity;
- Project, Study, subject/version, and editable source identity;
- dataset id/version, asset class, universe, date range, and dataset hash;
- Judge entrypoint and fixed source hashes;
- objective and execution details;
- nested metrics, immutable artifact references, and structured errors.

`manifest.json` is written last and pins every other Run file hash. Run listing
ignores incomplete directories; opening a completed Run rejects changed,
deleted, or added files.

## Research Session and Experiment

Sessions provide the governed candidate-editing layer above Studies and Runs:

```text
sessions/
└── session-<UTC timestamp>-<identity>/
    ├── session.json
    ├── worktree/<project-id>/
    ├── experiments/
    │   └── exp-0001-<candidate identity>/
    │       ├── result.json
    │       ├── changes.json
    │       ├── diff.patch
    │       └── manifest.json
    └── promotion.json
```

`session.json` V1 is a strict mutable coordination pointer. It records:

- Session status, Project, Study, worktree, timestamps, and next sequence;
- exact editable paths and Project source hash at Session start;
- successful baseline and current leader Run/source/metric/value pointers;
- Study/program/Judge/dataset/Harness locks;
- a complete hash inventory of every non-editable worktree file.

The worktree is a complete structural Project containing only the selected
fixed Study/Judge inputs and candidate-editable source bytes. It has empty
data, run, cache, and nested Session directories. Candidate Runs read the
owning Project data directory and publish to the owning Project Run catalog.

Each immutable Experiment `result.json` records its hypothesis, sequence,
verdict, objective, leader and candidate Run/source/metric/value, normalized
improvement, source-change hash, errors, and timestamps. `changes.json`
contains exact added/modified/deleted file hashes; `diff.patch` contains
available UTF-8 unified diffs. Its terminal manifest pins all three.

Verdicts are:

- `KEEP` when direction-normalized improvement is strictly positive and meets
  `minimum_improvement`;
- `REVERT` when a successful candidate does not meet that threshold;
- `CRASH` when the candidate Run failed.

KEEP advances the Session leader. REVERT and CRASH restore the exact leader
source from its verified Run. `promotion.json` is written once only after the
current KEEP replaces an unchanged Project base and the applied source hash is
verified. Any failure rolls Project source and Session state back.

The complete operating and authority contract is
[[docs/design/research-session-loop]].

## Canonical schemas

Machine-readable JSON Schemas are available without loading a Project:

```bash
aq schema
aq schema workspace --json
aq schema project --json
aq schema study --json
aq schema judge-output --json
aq schema run-result --json
aq schema session --json
aq schema experiment --json
```

The Python validators are authoritative executable behavior in
`autoquant/workspace.py`, `autoquant/studies.py`, `autoquant/runs.py`, and
`autoquant/sessions.py`.

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
uv run python -m unittest \
  tests.test_workspace tests.test_cli tests.test_studies \
  tests.test_runs tests.test_sessions -v
```
