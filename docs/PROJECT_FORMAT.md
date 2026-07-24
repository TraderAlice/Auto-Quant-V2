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

`aq project create` produces a complete blank Project. The optional
`--template ohlcv-factor-lab` construction input additionally creates an
independently owned factor, Judge, Study, and deterministic local dataset; it
is not recorded as a runtime parent in `autoquant.json`.

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
Study `dataset.paths` may bind exact Project-local bytes without adding them to
Git. Project-locality does not imply that every large byte must be copied into
Sessions or Runs: their SHA-256 inventories are frozen while Judges receive the
canonical data root.

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
    },
    "paths": ["ohlcv/**"]
  }
}
```

Subject kinds are `strategy`, `factor`, `model`, or `research`. Editable paths
must be exact files or trailing-`/**` closures beneath the Project's declared
strategy, factor, or model directories. Judge paths use the same closure syntax
but stay beneath the declared Judge directory and are fixed and disjoint from
editable source.

`dataset.paths` is optional and relative to the Project's declared `data/`
directory. When absent, the historical declarative dataset hash is preserved.
When present, exact files or non-empty trailing-`/**` closures are content
hashed; a byte change changes Study input identity and stales existing
Sessions.

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
    │   ├── dataset-files.json  # content-locked Studies only
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
- dataset id/version, asset class, universe, date range, dataset hash, and
  optional content-locked source hashes;
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
    ├── request.json                 # delegated Sessions only
    ├── brief.json                   # delegated Sessions only
    ├── worktree/<project-id>/
    ├── experiments/
    │   └── exp-0001-<candidate identity>/
    │       ├── result.json
    │       ├── changes.json
    │       ├── diff.patch
    │       └── manifest.json
    ├── campaigns/
    │   └── campaign-<UTC timestamp>-<identity>/
    │       ├── progress.json
    │       ├── turns/turn-0001/
    │       ├── result.json
    │       └── manifest.json
    ├── reports/
    │   └── report-<UTC timestamp>-<identity>/
    │       ├── analysis.json
    │       ├── report.json
    │       ├── report.md
    │       └── manifest.json
    └── promotion.json
```

`session.json` V1 is a strict mutable coordination pointer. It records:

- Session status, Project, Study, worktree, timestamps, and next sequence;
- exact editable paths and Project source hash at Session start;
- successful baseline and current leader Run/source/metric/value pointers;
- Study/program/Judge/dataset/Harness locks;
- a complete hash inventory of every non-editable worktree file.

When Session start receives a strict delegated Research Request,
`session.json` also pins its `brief` id, normalized request hash, and derived
Brief hash. `request.json` records the exact normalized caller input:

```json
{
  "schemaVersion": 1,
  "kind": "autoquant-research-request",
  "title": "Assess AAPL trend support",
  "question": "Does current evidence support a conditional long view?",
  "decisionContext": "OpenAlice is preparing an investment discussion.",
  "assets": [
    {"symbol": "AAPL", "assetClass": "equity", "venue": "NASDAQ"}
  ],
  "direction": "long",
  "horizon": "one to three months",
  "hypotheses": ["Trend quality remains stable out of sample."],
  "constraints": ["Use only the locked dataset and cost assumptions."],
  "deliverables": ["factor evidence", "risk limitations"],
  "source": {
    "system": "openalice",
    "workspaceId": "equity-desk",
    "sessionId": "resume-...",
    "artifactPath": "requests/aapl.md",
    "artifactRevision": "sha256:..."
  }
}
```

Origin fields are caller-supplied content, not authenticated OpenAlice
provenance. Requested symbols and asset classes must fit the selected Study.
`brief.json` is derived from that request plus Project/Session/Study identity,
baseline, objective, dataset, Judge, and Harness locks. Its authority is
`research-prioritization`; trading authority is `none`. Every Session load
reconstructs the expected Brief and rejects a changed request, Brief, or
pointer. Sessions without a `brief` field remain valid and must not contain
untracked request/Brief files.

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

An immutable Campaign groups a bounded sequence of external Researcher turns.
Each turn preserves its complete input brief, stdout, stderr, parsed response
when valid, timing, terminal result, and optional Experiment reference.
Campaign `result.json` records the hashed command identity, budgets, stopping
reason, Experiment ids, verdict counts, and initial/final leader. Its terminal
manifest pins every Campaign file; opening a Campaign also verifies every
referenced Experiment. The full connector and recovery contract is
[[docs/design/external-researcher-driver]].

While a Campaign is executing, its hidden staging directory contains a strict
mutable `progress.json` with phase, turn, budget, command hash, completed
Experiment ids, and verdict counts. It is operational telemetry, never a
verdict. Terminal publication updates it to the final status and pins it in the
Campaign manifest. Studio may observe hidden progress only through the
Research module validator.

The complete operating and authority contract is
[[docs/design/research-session-loop]].

## Immutable Research Report

A delegated Session may publish any number of point-in-time Reports. The Agent
provides strict `analysis.json` with:

- title and executive summary;
- one or more findings, each with a kebab-case id, confidence, and non-empty
  evidence references;
- conditional recommendations with evidence references;
- limitations and unresolved questions.

Evidence kinds are `run`, `experiment`, or `campaign`. Only Run references may
select an `artifactPath`, and that path must match a declared immutable Run
artifact. Every id must belong to the Session baseline or chronological
Experiment/Campaign history.

Core freezes a complete evidence projection into `report.json`: the exact
request/Brief, Session baseline and leader at publication, fixed locks, Harness,
Run metrics and artifacts, Experiment verdicts, and Campaign outcomes. It
validates every reference, renders deterministic `report.md`, hashes the three
files, and writes `manifest.json` last. Loading a Report verifies:

1. every Report file hash and canonical Markdown;
2. strict normalized analysis and analysis/evidence hashes;
3. the unchanged delegated request/Brief;
4. exact projections of every referenced immutable Run, Experiment, and
   Campaign;
5. chronological Experiment/Campaign prefixes and the corresponding KEEP
   leader chain.

An older Report remains valid when a Session later adds evidence. Rewriting a
conclusion requires a new immutable Report. Report authority is
`quantitative-decision-support`; `tradingAuthority` is always `none`.

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
aq schema researcher-response --json
aq schema campaign-result --json
aq schema campaign-progress --json
aq schema research-request --json
aq schema report-analysis --json
aq schema studio-snapshot --json
```

The Python validators are authoritative executable behavior in
`autoquant/workspace.py`, `autoquant/studies.py`, `autoquant/runs.py`,
`autoquant/sessions.py`, `autoquant/research.py`, and `autoquant/studio.py`.
Delegated request/Brief parsing is in `autoquant/briefs.py`; immutable Report
publication and verification are in `autoquant/reports.py`.

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
uv run aq project create /tmp/quant-workspace ohlcv-lab \
  --template ohlcv-factor-lab
uv run aq validate /tmp/quant-workspace
uv run aq inspect /tmp/quant-workspace --project factor-lab --json
uv run python -m unittest \
  tests.test_workspace tests.test_cli tests.test_studies \
  tests.test_runs tests.test_sessions tests.test_factor_lab -v
uv run python -m unittest tests.test_reports tests.test_studio -v
```
