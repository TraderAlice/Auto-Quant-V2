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
`--template ohlcv-factor-lab`, `--template ohlcv-portfolio-lab`, or
`--template ohlcv-rl-factor-lab` construction input additionally creates an
independently owned candidate, Judge, Study, and deterministic local dataset;
it is not recorded as a runtime parent in `autoquant.json`.

`--template ohlcv-research-desk` creates the canonical multi-Study Project:
one shared dataset, one Factor candidate shared by Factor and Portfolio
evaluation, one RL state encoder, three fixed Studies, and a strict
`research-program.json` coordination manifest. See
[[docs/design/research-program-orchestration]].

The factor template evaluates causal cross-sectional predictive evidence with
dataset-fixed purged 1/5/10-bar rank/Pearson IC, HAC inference, fixed-tertile
behavior, OHLCV-style overlap, and asset/fold/causal-regime stability. The
portfolio template fixes the next layer: factor normalization, target weights,
explicit entry/hold/exit/reversal intent, gross/net and per-asset constraints,
drift, no-trade behavior, turnover, costs, benchmark, a causal covariance
volatility ceiling, risk/implementation metrics, decision attribution, and
cost/delay/no-hysteresis/risk-governor stresses. A fixed 15-cell local
signal-threshold × no-trade parameter neighborhood is emitted as context-only
robustness evidence and has no parameter-selection authority.
The final post-drift Portfolio and RL books share an additional fixed
execution-risk decision: risk outranks the no-trade band and may only scale
the chosen book down.
Candidate code remains confined to `factors/**`; `judges/**` owns every
comparison rule. See [[docs/design/ohlcv-factor-lab]],
[[docs/design/factor-diagnostics]], and
[[docs/design/portfolio-construction-lab]],
[[docs/design/portfolio-parameter-neighborhood]],
[[docs/design/executed-book-risk-compliance]], and
[[docs/design/signal-policy-and-attribution]], and
[[docs/design/mechanical-position-lifecycle-evidence]].

New Portfolio and governed-RL Projects also contain the fixed
`strategies/portfolio-mandate.json`. For request intake it derives the
tradable/context asset partition, direction, cash, gross/net, cap, and
benchmark from the canonical request. It also fixes a 60-bar/20-observation
covariance policy, 15% annualized volatility ceiling, 252-period
annualization, and `scaleUp: false`; synthetic templates explicitly declare
the all-universe research-neutral position contract with the same V2 risk
policy. It is a Study dependency, not candidate code. See
[[docs/design/request-bound-portfolio-mandates]].

The RL template confines candidates to a pure row-level state encoder under
`models/**`. Its fixed Judge owns factor-mixture actions, Q-learning, reward,
portfolio accounting, chronological folds, seeds, baselines, and the
validation-only objective. Every model, episode, fold, seed, action, failure,
and baseline comparison is Run evidence. Each action resolves to a fixed
stateful signal sleeve before portfolio accounting. See
[[docs/design/rl-factor-policy-lab]].

All three reference templates publish a nested `research_integrity` metric
declaring validation-only selection, visible diagnostic test evidence, and the
external-holdout rule. Session snapshots derive exact candidate/verdict counts
from immutable Experiments. They also discover every verified Project Run with
the same Study/program/Judge/dataset/dependency/objective contract, deduplicate
editable source hashes, and publish a content-derived research-family ledger
summary plus the supported selection adjustment. Reports freeze that family
as of publication. Generic Studies without the declaration remain valid and
are explicitly shown as `unspecified`; unsupported statistic families name an
exact reason. See [[docs/design/research-selection-integrity]] and
[[docs/design/selection-adjusted-research-evidence]].

`aq project intake` uses one of these same fixed templates but replaces the
construction fixture with a validated caller-supplied OHLCV snapshot. V1
stores a daily session panel:

```text
request.json
intake.json
research-program.json
data/ohlcv/
├── <SYMBOL>.csv
├── README.md
└── snapshot.json
```

V2 stores one authoritative continuous UTC 1h panel plus deterministic
completed-bar aggregates:

```text
data/ohlcv/
├── 1h/<SYMBOL>.csv
├── 3h/<SYMBOL>.csv
├── 4h/<SYMBOL>.csv
├── 6h/<SYMBOL>.csv
├── 12h/<SYMBOL>.csv
├── 1d/<SYMBOL>.csv
├── README.md
└── snapshot.json
```

`snapshot.json` preserves package/provider/market/adjustment claims, requested
assets, research universe, coverage, source hashes, and canonical hashes. V2
also fixes base/features, bar-close semantics, continuous UTC clock, midnight
anchor, aggregation method, and per-interval inventories. Fixed loading
recomputes derived files from 1h before causal backward-as-of alignment.
`intake.json` binds request, snapshot, primary construction Study, dataset, and
the Study input identity at handoff. Editable source may evolve; its current
hash determines whether existing Run evidence is stale rather than corrupting
the intake record. `research-program.json` binds the canonical Factor,
Portfolio, and governed RL lanes and their editable surfaces. Every Study's
`ohlcv/**` closure makes every local dataset byte part of Run and Session
identity. See
[[docs/design/research-intake-and-dataset-snapshots]].

```text
factor-lab/
├── autoquant.json
├── research.md
├── strategies/
│   └── portfolio-mandate.json  # Portfolio/RL templates only
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
  "dependencies": {
    "paths": ["models/fixed-input.py"]
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

`dependencies` is optional. Its exact paths or trailing-`/**` closures use the
same confined strategy/factor/model roots, must be non-empty and disjoint from
the editable closure, and remain fixed for that Study. Their individual and
aggregate hashes enter Study input identity without becoming candidate source
identity. Runs freeze them under `inputs/dependency-sources/`; Sessions copy
them into the worktree but reject edits or upstream byte changes.

The canonical Portfolio Study depends on
`strategies/portfolio-mandate.json`. The RL Study depends on both
`factors/**` and that same mandate, so adaptive actions cannot change the
position question.

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
    │   ├── dependency-sources/ # declared fixed source dependencies only
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
- optional fixed dependency paths, aggregate hash, and source-file hashes;
- dataset id/version, asset class, universe, date range, dataset hash, optional
  content-locked source hashes, and the V2 interval surface when present;
- Judge entrypoint and fixed source hashes;
- objective and execution details;
- nested metrics, immutable artifact references, and structured errors.

Declaring Factor Runs add `metrics.factor_components` and
`artifacts/factor-components.json`. Both appear together and describe only
candidate-declared materialized components: fixed split/horizon IC,
final-factor association, pairwise redundancy, train-selected nearest-peer
residual IC, and leave-one-out impact on a fixed equal-rank diagnostic blend.
Historical and non-declaring Runs omit both. The evidence has no
final-factor-selection, Portfolio, RL-action, or trading authority.

Portfolio and RL Run metrics include the complete normalized
`portfolio_mandate`; their artifact ledgers record the mandate id and
per-asset tradability. New Portfolio decision ledgers also record the
pre-governor target, covariance observations, pre/post annualized forecast,
ceiling, scale, and status on every asset/date. Governed RL action sleeves bind
the same complete Mandate before training or rollout. New Portfolio ledgers
and daily artifacts also record pretrade/proposed/executed forecasts,
forecast coverage, proportional repair scale, risk-only override, and exact
execution reason. RL action artifacts publish the same final-book fields.
New governed RL Runs additionally declare `policy-rationales.json`: one exact
row per validation/test action with raw causal state, encoded features, all
frozen linear-Q values, deterministic runner-up, chosen margin, and the exact
per-feature chosen-minus-runner contribution. `policy_rationale` Run metrics
summarize split-bounded action runs, transitions, margins, and descriptive
action/feature conditionals. Q scale is uncalibrated and the evidence remains
context-only with no trading authority. Older Runs may omit both the metric
and artifact and remain readable as legacy evidence.
New governed RL Runs also declare `policy-opportunities.json`: every fixed
governed sleeve is evaluated for one next bar from the selected policy path's
exact actual pretrade book. Proposed/executed weights, trades, costs, reward,
local ex-post oracle rank/regret, and candidate-factor deltas are immutable
audit evidence. Alternate books never propagate to a later timestamp; the
oracle is context-only hindsight, not a strategy or promotion input. See
[[docs/design/rl-factor-opportunity-audit]].
New Portfolio ledgers
also record causal trailing dollar volume, reference-NAV participation,
1%/5% asset and portfolio capacity, availability, and one deterministic
binding asset per trade date. Aggregate capacity remains contextual and cannot
enter candidate selection. New Portfolio Runs also declare
`portfolio-position-episodes`: one exact split-bounded row per contiguous
executed long/short state, including entry/holding/exit cost allocation,
complete-versus-censored status, decision bars, additive net contribution,
cumulative-contribution MFE/MAE, and signal/execution mismatch counts. Its
aggregate `position_lifecycle` metrics reconcile exactly to the decision
ledger and remain contextual only.

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
    ├── checks/
    │   └── check-<UTC timestamp>-<identity>/
    │       ├── raw-output.json
    │       ├── stdout.txt
    │       ├── stderr.txt
    │       ├── result.json
    │       └── manifest.json
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
    ├── promotion.json                # promoted terminal state only
    └── completion.json               # completed terminal state only
```

`session.json` V1 is a strict mutable coordination pointer. It records:

- Session status, Project, Study, worktree, timestamps, and next sequence;
- exact editable paths and Project source hash at Session start;
- successful baseline and current leader Run/source/metric/value pointers;
- Study/program/Judge/dataset/dependency/Harness locks;
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

A Study may also contain an optional strict `preflight.json` beside
`study.json`. It declares a fixed Python entrypoint, fixed source closure,
arguments, and a 1–60 second timeout. The closure must remain under `judges/`,
include its entrypoint, and not overlap editable paths. Preflight definition
and source hashes must also remain disjoint from the formal Judge closure.
Thus a legacy broad `judges/**` Study must deliberately narrow that inventory
before opting in. The separate operational identity means later preflight
improvements do not rewrite scientific Study or historical Run identity. A
new Session copies and locks the manifest and source bytes as fixed authority.

Each immutable CandidateCheck records only passed/failed structural feedback,
execution details, exact candidate/leader/Study/dataset/preflight/Harness
identity, and explicit `none` selection/promotion/trading authority. Its
terminal manifest hashes normalized output, logs, and result. Checks contain
no metrics or KEEP/REVERT/CRASH verdict and never affect Runs, Experiments,
trial counts, leader pointers, or Project source. Currentness is reconstructed
from hashes; editing a candidate makes earlier Checks stale.

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

For a delegated Session whose leader still equals baseline, `completion.json`
can instead bind one explicitly selected current Report and mark the Session
`completed` without changing Project source. Its content-derived identity
freezes the Brief, baseline leader, Report manifest/result/evidence hashes,
Study, Project, and completion time. Completion requires the Report to cover
the complete current Experiment/Campaign prefix and no Campaign may be
running. `promoted` and `completed` receipts are mutually exclusive.

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
also freezes Core-derived selection metric/split, Session trial and verdict
counts, the complete as-of Project research-family summary, selection
adjustment, test visibility, and external-holdout status. It
validates every reference, renders deterministic `report.md`, hashes the three
files, and writes `manifest.json` last. Loading a Report verifies:

1. every Report file hash and canonical Markdown;
2. strict normalized analysis and analysis/evidence hashes;
3. the unchanged delegated request/Brief;
4. exact projections of every referenced immutable Run, Experiment, and
   Campaign;
5. chronological Experiment/Campaign prefixes and the corresponding KEEP
   leader chain;
6. selection-integrity equality with the frozen Experiment prefix and leader
   Run, including every matching Project Run completed by `publishedAt`.

An older Report remains valid when a Session later adds evidence. Rewriting a
conclusion requires a new immutable Report. Report authority is
`quantitative-decision-support`; `tradingAuthority` is always `none`.

## Immutable Project Research Dossier

A request-driven canonical Research Program can compose verified lane Reports
into one Project-level handoff:

```text
dossiers/
└── dossier-<UTC timestamp>-<identity>/
    ├── analysis.json
    ├── dossier.json
    ├── dossier.md
    └── manifest.json
```

`dossiers/` is a reserved optional Project root, so existing V1 manifests and
historical Projects remain valid. Factor and Portfolio Reports are required.
Governed RL is optional, but omission is explicit. When RL is included, the
`factors/**` subset of its frozen dependency closure must equal the included
Factor source identity and its Portfolio Mandate must equal the included
Portfolio lane mandate.

Agent analysis references exact lane Report and optional finding ids. Core
requires finding coverage of every included lane, freezes the current request,
dataset, Research Program, Studies, Reports, leader Runs, selection integrity,
Harnesses, and source/dependency identities, and renders canonical
`dossier.md`. The terminal manifest hashes the other three files.

Loading verifies the immutable frozen prefix rather than requiring the Project
to remain current. Thus later Sessions, Reports, or leaders create a new
publication opportunity without invalidating an older Dossier. Authority is
`quantitative-decision-support`; `tradingAuthority` is always `none`. See
[[docs/design/program-research-dossiers]].

## Frozen external holdout

A fresh request-driven research-desk Project can bind one current source
Dossier before any target Run or Session exists:

```text
holdout/
├── binding.json
├── source-dossier.json
├── imported-sources/
│   ├── factors/...
│   └── models/...              # only when RL is included
├── manifest.json
└── result/                     # after the one-shot challenge
    ├── result.json
    └── manifest.json
```

The binding hashes the portable Dossier, exact imported Run source bytes,
source and target datasets, non-overlap proof, target Studies, and frozen
authority. Those imported bytes also replace the corresponding target
candidate closures, then become non-editable operationally. A bound Project
rejects Sessions, Campaigns, and generic Runs.

`holdout run` publishes one ordinary immutable Run for every Dossier-included
lane and then a terminal result that reconciles those Runs with the binding.
Partial lane execution can resume, but duplicate or unrelated Runs invalidate
publication. The result records source/later objective values and deltas with
`selectionAllowed: false` and `tradingAuthority: none`. See
[[docs/design/frozen-external-holdout-challenge]].

## Canonical schemas

Machine-readable JSON Schemas are available without loading a Project:

```bash
aq schema
aq schema workspace --json
aq schema project --json
aq schema study --json
aq schema judge-output --json
aq schema run-result --json
aq schema portfolio-mandate --json
aq schema session --json
aq schema session-completion --json
aq schema candidate-preflight --json
aq schema candidate-check-output --json
aq schema candidate-check-result --json
aq schema holdout-binding --json
aq schema holdout-result --json
aq schema holdout-status --json
aq schema experiment --json
aq schema researcher-response --json
aq schema campaign-result --json
aq schema campaign-progress --json
aq schema research-request --json
aq schema report-analysis --json
aq schema dossier-analysis --json
aq schema dossier-result --json
aq schema dossier-status --json
aq schema studio-snapshot --json
```

The Python validators are authoritative executable behavior in
`autoquant/workspace.py`, `autoquant/studies.py`, `autoquant/runs.py`,
`autoquant/sessions.py`, `autoquant/checks.py`, `autoquant/research.py`,
`autoquant/dossiers.py`, and `autoquant/studio.py`.
Delegated request/Brief parsing is in `autoquant/briefs.py`; immutable Report
publication and verification are in `autoquant/reports.py`; Project Dossier
composition and verification are in `autoquant/dossiers.py`.

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
uv run aq project create /tmp/quant-workspace portfolio-lab \
  --template ohlcv-portfolio-lab
uv run aq project create /tmp/quant-workspace rl-factor-lab \
  --template ohlcv-rl-factor-lab
uv run aq project create /tmp/quant-workspace research-desk \
  --template ohlcv-research-desk
uv run aq project program /tmp/quant-workspace --project research-desk --json
uv run aq validate /tmp/quant-workspace
uv run aq inspect /tmp/quant-workspace --project factor-lab --json
uv run python -m unittest \
  tests.test_workspace tests.test_cli tests.test_studies \
  tests.test_runs tests.test_sessions tests.test_factor_lab \
  tests.test_portfolio_lab tests.test_rl_factor_policy_lab -v
uv run python -m unittest \
  tests.test_reports tests.test_studio tests.test_research_program -v
```
