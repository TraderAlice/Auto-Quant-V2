# AutoQuant V2 CLI

Status: Workspace/Project and request-driven OHLCV intake, Study/Run evidence,
governed Session/Experiment research, bounded external Researcher Campaigns,
delegated requests, and evidence-bound Research Reports implemented.

`aq` is the public human- and Agent-facing command line interface. Humans
receive compact text by default. `--json` emits exactly one versioned envelope.

## Discovery

```bash
aq capabilities
aq capabilities --json
aq schema
aq schema project --json
aq schema research-request --json
aq schema ohlcv-dataset-package --json
aq schema report-analysis --json
aq schema factor-diagnostics --json
aq schema portfolio-diagnostics --json
aq schema portfolio-mandate --json
aq schema rl-policy-diagnostics --json
aq schema research-program-status --json
aq schema session-decision-matrix --json
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
  [--name NAME] [--description TEXT] \
  [--template blank|ohlcv-factor-lab|ohlcv-portfolio-lab|ohlcv-rl-factor-lab|ohlcv-research-desk] \
  [--json]
aq project intake <workspace-dir> <project-id> \
  --request research-request.json \
  --dataset ohlcv-dataset-package.json \
  [--template ohlcv-factor-lab|ohlcv-portfolio-lab|ohlcv-rl-factor-lab|ohlcv-research-desk] \
  [--name NAME] [--json]
aq project list <workspace-dir> [--json]
aq project default <workspace-dir> <project-id> [--json]
aq project program <project-or-workspace-dir> [--project ID] [--json]
aq validate <project-or-workspace-dir> [--project ID] [--json]
aq inspect <project-or-workspace-dir> [--project ID] [--json]
```

`validate` and `inspect` resolve exactly one Project before reading its
manifest. A direct Project path rejects `--project`; a Workspace path selects
the explicit id or its default.

`blank` is the default construction. `ohlcv-factor-lab` transactionally
creates a complete, self-contained pandas factor research Project with local
synthetic OHLCV, content-locked Study, fixed no-lookahead Judge, and executable
next actions. `ohlcv-portfolio-lab` uses the same causal candidate API and
adds fixed constrained target construction, drift-aware accounting,
transaction costs, layered professional metrics, and cost/delay stresses. New
Portfolio and RL Projects bind a strict `portfolio-mandate`: delegated intake
authorizes requested assets and direction while retaining other panel assets
as research context only.
`ohlcv-rl-factor-lab` adds a deterministic causal state encoder surface over
a content-locked candidate-factor sleeve plus fixed reference actions,
Q-learning, folds, seeds, rewards, portfolio accounting, and simple baselines.
All three reference templates are bounded, deterministic construction
fixtures.

`ohlcv-research-desk` coordinates those three evaluation questions in one
Project over one dataset snapshot. Factor and Portfolio deliberately share
`factors/candidate.py`; RL owns `models/candidate.py`. The program reports
simultaneous active Sessions on the shared Factor surface as a conflict and
also reports active factor-writer/RL-reader conflicts. The RL Study binds the
exact current candidate bytes and the same fixed Portfolio Mandate as the
Portfolio lane, so factor or mandate changes stale its Run evidence.

`project intake` defaults to this research-desk template. It validates the
strict request and a caller-supplied,
path-confined daily session-OHLCV package before creating anything. Every asset
must share the exact timestamp panel; template-specific breadth/history floors
apply. Core canonicalizes CSV into the Project, records provider, retrieval,
calendar, terms, and price-adjustment claims, hashes source and normalized
bytes, replaces the synthetic Study dataset identity, and atomically publishes
the Project. V1 does not download data, authenticate provider claims, fill
missing sessions, or support intraday/continuous/mixed-class packages.

The JSON result contains Project-level `request.json`, `intake.json`,
`data/ohlcv/snapshot.json`, three verified Study identities, and exact next
actions for inspecting the program and advancing its recommended lane.
`project program --json` is the stable Agent read model for lane phase, current
Run evidence, Sessions, Reports, shared-source conflicts, and next action. See
[[docs/design/research-intake-and-dataset-snapshots]].

## Study and Run commands

```bash
aq study create <path> <study-id> \
  --subject-kind factor \
  --judge judges/evaluate.py \
  --judge-path 'judges/**' \
  --editable 'factors/**' \
  [--dependency 'models/fixed-input.py'] \
  --metric score \
  --dataset-id synthetic-bars \
  --dataset-path 'ohlcv/**' \
  --asset-class equity \
  --asset AAA/USD \
  --start 2026-01-01 \
  --end 2026-01-31

aq study list <path> [--project ID] [--json]
aq study inspect <path> --study ID [--project ID] [--json]
aq run execute <path> --study ID [--project ID] [--json]
aq run list <path> [--study ID] [--project ID] [--json]
aq run show <path> --run ID [--project ID] [--json]
aq run factor <path> --run ID \
  [--points 180] [--project ID] [--json]
aq run portfolio <path> --run ID \
  [--points 180] [--project ID] [--json]
aq run rl <path> --run ID \
  [--points 180] [--project ID] [--json]
```

`--dataset-path` is optional and repeatable. When provided it is relative to
the selected Project's `data/` directory and binds matching file bytes into
Study and Run identity.

`--dependency` is optional and repeatable. It declares fixed Project-relative
strategy/factor/model source that the Judge may import but the Study cannot
edit. Dependency files are separately hashed, frozen into Run inputs, copied
read-only into Session worktrees, and included in Study currentness.

`study create` validates the complete fixed contract immediately. `run execute`
freezes inputs, runs the Python Judge under its timeout, and atomically
publishes one immutable Run whether the Judge succeeds or fails. `run list`
and `run show` verify terminal file hashes before returning evidence.

`run portfolio` is the bounded decision-explorer projection for a successful
Portfolio Lab Run. Core verifies the immutable Run and its report, daily path,
target weights, executed weights, and per-asset decision ledger before
returning compounded gross/net/benchmark paths, drawdown, exposure, unused
cash budget, turnover/cost, the latest historical mechanical book, recent
signal transitions, validation/test attribution, and exact mandate.
`--points` defaults to 180 and is bounded to 40–400; full history is
reconciled before deterministic sampling. The operation has no live account
or trading authority.

`run factor` is the corresponding bounded professional tear sheet for a
successful fixed Factor Lab Run. Core verifies the immutable report, daily
1/5/10-bar rank/Pearson IC, and fixed-tertile artifacts; reconciles every
split/horizon aggregate; then deterministically samples 40–400 timestamp
anchors. The response keeps horizon decay, quantiles, folds, causal regimes,
assets, styles, coverage, and rank turnover machine-readable. Validation
one-bar rank IC remains the only selection objective; test and all other
layers are explicitly diagnostic.

`run rl` projects one successful governed RL Factor-Policy Run. Core verifies
the immutable report, learned models, complete fixed-budget training histories,
and timestamped action ledger; reconciles every declared fold/seed, baseline,
reward, action frequency, observation count, turnover, and cost; then returns
a bounded action path with exact trial, training, and model evidence.
Validation advantage versus each fold's fixed validation-selected baseline is
the value-add test. Test remains visible audit only, failed seeds cannot be
hidden, every action must pass the shared Portfolio Mandate audit, and
factor-mixture actions carry no trading authority.

A failed Run is a successful artifact-creation operation whose RunResult has
`status: failed`; it retains errors and logs. A CLI error means trustworthy Run
evidence could not be created or verified.

## Session and Experiment commands

```bash
aq session start <path> --study ID \
  [--request research-request.json] \
  [--project ID] [--json]
aq session list <path> [--project ID] [--json]
aq session show <path> --session ID [--project ID] [--json]
aq session compare <path> --session ID \
  [--trials 24] [--project ID] [--json]
aq session promote <path> --session ID [--project ID] [--json]
aq session complete <path> \
  --session ID \
  --report ID \
  [--project ID] [--json]

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

With `--request`, Session start first validates the strict external question,
assets, direction, horizon, hypotheses, constraints, deliverables, and
caller-supplied origin context. Requested assets and asset classes must fit the
selected Study. Core copies canonical `request.json` and derives `brief.json`
from that request plus the Project, Study, baseline, dataset, Judge, and Harness
locks. Those files are verified on every Session load and are included in each
external Researcher turn. Existing local Sessions without a request remain
valid.

`experiment evaluate` freezes the candidate into a canonical Run, compares the
primary metric with the current leader, publishes immutable Experiment
evidence, and returns `KEEP`, `REVERT`, or `CRASH`. REVERT and CRASH restore the
leader bytes in the worktree. `session promote` is the only operation that
copies a KEEP into Project source; it rejects a stale Project base and rolls
back if the source, receipt, and Session pointer cannot all be committed.

`session complete` is the no-promotion terminal path for a delegated lane whose
leader remains its baseline. The caller selects the exact current Report.
Core rejects a changed worktree, incomplete Report prefix, running Campaign,
unpromoted KEEP, stale authority, or terminal Session. It writes immutable
`completion.json`, marks the Session `completed`, and leaves Project source
unchanged. A completed Session cannot run Experiments/Campaigns, publish later
Reports, promote, or complete again.

For the Factor Lab, `run execute/show --json` and Experiment output preserve
the full purge-aware factor tear sheet: 1/5/10-bar horizon quality, HAC
inference, fixed-tertile behavior, style overlap, and asset/fold/causal-regime
stability. Studio is a concise projection; exact daily IC/regime and quantile
rows remain Run artifacts.

For the Portfolio Lab, the same commands preserve the fixed signal policy,
dataset-fixed purged splits, hysteresis comparison, contribution
reconciliation, and attribution by asset, signal intent, and causal regime.
Proposed/executed weights and the exact per-asset decision path remain
immutable Run artifacts; Studio is the concise human projection.

`session show --json` also projects selection integrity from verified evidence:
selection metric/split, exact candidate and evaluated-Run counts, verdict
counts, test visibility/use, and whether a new external holdout is required.
Reference templates select on validation only. Generic Studies without a
declaration return explicit `unspecified` values.

`session compare` verifies the immutable Session, Experiment chain, and
referenced Runs before producing one bounded baseline/candidate/leader matrix.
`--trials` defaults to 24 and is bounded to 1–100; the current leader and
baseline remain visible even when older candidates are omitted. Core owns the
metric dictionary, units, preference direction, comparable set, and
validation-only non-dominance calculation. Test values are explicitly labelled
audit evidence, contextual policy state is display-only, and neither can
change an Experiment verdict. Failed candidates remain explicit rows without
invented metrics.

## Research Campaign commands

```bash
aq research run <path> \
  --session ID \
  --agent-command SHELL \
  [--max-turns 5] \
  [--max-wall-seconds 900] \
  [--turn-timeout-seconds 300] \
  [--project ID] [--json]
aq research list <path> --session ID [--project ID] [--json]
aq research show <path> \
  --session ID \
  --campaign ID \
  [--project ID] [--json]
```

`research run` invokes the explicit shell command in the Session worktree. A
fresh structured brief is provided on stdin every turn. The command edits the
declared candidate closure and returns exactly one strict JSON `propose` or
`stop` response. Valid proposals are evaluated through the existing fixed
Judge and Experiment path; they cannot supply metrics, verdicts, or promotion.

The aggregate and per-turn budgets are mandatory and bounded. Command exit,
timeout, malformed response, illegal fixed-source changes, unchanged
proposals, and changed-source STOP responses terminate the Campaign as
`failed` and reconstruct the worktree from verified fixed inputs and leader
Run evidence. `research list` and `research show` verify every Campaign file
hash and referenced Experiment.

The external command is explicit host-code execution, not an OS sandbox.
Callers that require stronger isolation can wrap the same stdin/stdout
protocol in their own sandbox.

## Research Report commands

```bash
aq report publish <path> \
  --session ID \
  --analysis report-analysis.json \
  [--project ID] [--json]
aq report list <path> --session ID [--project ID] [--json]
aq report show <path> \
  --session ID \
  --report ID \
  [--project ID] [--json]
```

`report publish` is available only for a delegated Session. The Agent-authored
analysis is strict JSON: title, executive summary, findings with confidence,
conditional recommendations, limitations, unresolved questions, and exact
Run/Experiment/Campaign evidence references. A Run reference may also name one
of that Run's declared artifact paths.

Core does not write the conclusions. It validates every reference against the
verified Session history, freezes the current baseline/leader, Run metrics,
Experiments, Campaigns, Study locks, Harness, dataset, request, and Brief, then
atomically publishes:

```text
reports/report-<UTC timestamp>-<identity>/
├── analysis.json
├── report.json
├── report.md
└── manifest.json
```

`report.md` is rendered deterministically for human/OpenAlice consumption.
`report.json` is the machine handoff. Both declare
`quantitative-decision-support` authority and `tradingAuthority: none`.
Later Session research does not reinterpret an older report; its frozen
Experiment/Campaign catalogs must remain chronological prefixes of the
verified history. OpenAlice should publish the exact Markdown through its own
Inbox boundary, where OpenAlice—not AutoQuant—stamps authoritative Workspace,
Session, and document-revision provenance.

## Project Research Dossier commands

```bash
aq dossier status <path> [--project ID] [--json]
aq schema dossier-analysis --json
aq dossier publish <path> \
  --analysis dossier-analysis.json \
  [--project ID] [--json]
aq dossier list <path> [--project ID] [--json]
aq dossier show <path> \
  --dossier ID \
  [--project ID] [--json]
```

A Session Report is one lane's point-in-time answer. A Project Research
Dossier is the cross-lane return artifact. `dossier status` uses the canonical
Research Program to require current Factor and Portfolio Reports and to include
governed RL only when its current Report pins the included Factor source.
Missing optional RL evidence is not silently ignored: its omission and reason
are frozen into the Dossier.

The Agent authors strict cross-lane analysis whose references select exact
included `laneId`, `reportId`, and optional Report `findingId`. Core verifies
coverage of every included lane and atomically publishes:

```text
dossiers/dossier-<UTC timestamp>-<identity>/
├── analysis.json
├── dossier.json
├── dossier.md
└── manifest.json
```

The Dossier freezes request, dataset, Research Program, lane Study, Report,
leader Run, selection-integrity, Harness, source/dependency, omission, and
analysis identities. It requires Portfolio and included RL evidence to use the
same fixed mandate and renders the authorized/context-only asset boundary.
Later lane research does not invalidate an older point-in-time Dossier.
`dossier.md` is the exact decision-support document that OpenAlice may publish
through its own Inbox authority; AutoQuant has no trading or authenticated
OpenAlice provenance authority.

## Studio commands

```bash
aq studio snapshot <path> [--project ID] [--json]
aq studio serve <path> \
  [--project ID] \
  [--host 127.0.0.1] \
  [--port 8765] \
  [--no-open]
```

`studio snapshot` builds one Workspace or direct-Project observation through
the same verified Core loaders used by other commands. It includes fixed
Studies, immutable Runs, Session/Experiment history, terminal Campaigns, and
explicitly mutable in-progress Campaign telemetry. Delegated requests, Research
Briefs, immutable Reports, and Core-generated copyable CLI commands are in the
same read model. For canonical multi-Study Projects the snapshot also includes
Dossier readiness, blockers, explicit optional-lane omissions, immutable
Dossier summaries, and the exact publish/show command.

`studio serve` is a foreground `long-running-server` operation. It serves the
packaged read-only browser presentation and the same snapshot contract. It
does not support `--json` because its stdout announces a live URL rather than
one terminal envelope. Loopback is the default; non-loopback binding is an
explicit operator choice and V1 has no authentication. See [[docs/STUDIO]].

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
- `mutates-project`;
- `long-running-server`.

Only `session.promote` currently uses `mutates-project`, after locked-history,
stale-base, source-hash, and rollback checks. `studio.serve` is the only
`long-running-server`; its routes are fixed and read-only.

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
evidence, the governed Session/Experiment edit/evaluate/promotion loop, and
bounded provider-neutral Researcher Campaigns. The legacy `prepare.py` and
`run.py` commands remain the V0.5 compatibility Harness. Delegated
request/Brief/Report handoff is Project-local and has no OpenAlice provenance
or live-trading authority. The local Studio projects the current read model.
Richer robust comparison and Studio mutation operations remain separate future
surfaces.

## Verification

```bash
uv run aq capabilities --json
uv run python -m unittest \
  tests.test_cli tests.test_studies tests.test_runs tests.test_sessions \
  tests.test_research tests.test_reports tests.test_studio -v
```
