# AutoQuant V2

AutoQuant is an AI-native quantitative research workbench. A long-lived
Workspace contains self-contained Projects; each Project owns its research
question, caller-supplied OHLCV, factor or model source, fixed Studies and
Judges, governed Sessions, immutable Runs, and decision-support artifacts.

The working model is:

```text
Workspace
└── Project
    ├── request + content-locked dataset
    ├── Factor / Portfolio / governed-RL Studies
    ├── Agent Sessions and bounded Experiments
    ├── immutable Runs, Reports, and Dossiers
    └── read-only Studio projections
```

AutoQuant produces historical quantitative evidence, not orders. It has no
Broker, account, OpenAlice UTA, or live-trading authority.

## Quick start

AutoQuant requires Python 3.11 and
[uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run aq capabilities --json
uv run aq workspace init ./quant-workspace --name "Quant Research Desk"
uv run aq project create ./quant-workspace research-desk \
  --name "Research Desk" \
  --description "Coordinate factor, portfolio, and RL evidence" \
  --template ohlcv-research-desk
uv run aq project program ./quant-workspace --project research-desk
uv run aq validate ./quant-workspace
uv run aq orient ./quant-workspace --project research-desk --json
```

`aq` emits compact human output by default and a versioned machine envelope
under `--json`. See [CLI.md](docs/CLI.md) and
[PROJECT_FORMAT.md](docs/PROJECT_FORMAT.md).

CSV intake works in the base environment. Parquet and Feather are optional:

```bash
uv sync --extra columnar
```

## Start from a real research request

The caller supplies a strict research request and an OHLCV package. Intake
validates and normalizes the complete panel, checks its market-clock and
interval contract, confines all paths, copies the data into the Project, and
locks every source byte before creating Studies.

```bash
uv run aq schema research-request --json
uv run aq schema ohlcv-dataset-package --json
uv run aq project intake ./quant-workspace us-leadership \
  --request research-request.json \
  --dataset /path/to/dataset.json \
  --json
```

The request may lock:

- long-only, short-only, two-sided, or context-only duties per asset;
- gross, per-asset, volatility, cost, no-trade, and reference-NAV assumptions;
- cash or one named dataset asset as the evaluation benchmark;
- primary and diagnostic forward horizons;
- Portfolio/RL decision cadence and dataset/session clock anchor.

These are immutable research assumptions. They never grant live position or
execution authority.

## Research loop

A Session creates a disposable worktree with an exact editable closure. A fast
candidate Check can catch structural errors without creating evidence.
The fixed Judge alone publishes metrics and a KEEP, REVERT, or CRASH verdict.
Promotion remains a separate guarded operation.

```bash
uv run aq session start ./quant-workspace \
  --study factor-quality \
  --request research-request.json \
  --json

uv run aq session check ./quant-workspace \
  --session session-... \
  --json

uv run aq experiment evaluate ./quant-workspace \
  --session session-... \
  --hypothesis "Add volatility normalization" \
  --json

uv run aq session promote ./quant-workspace \
  --session session-... \
  --json
```

Any explicit external coding-Agent command can drive the same bounded loop.
AutoQuant supplies the verified brief, protects fixed source, and retains every
turn and evaluation as evidence:

```bash
uv run aq research run ./quant-workspace \
  --session session-... \
  --agent-command 'my-coding-agent --autoquant-research' \
  --max-turns 5 \
  --max-wall-seconds 900 \
  --turn-timeout-seconds 300 \
  --json
```

## Evidence and handoff

Factor Runs publish purge-aware IC, decay, quantile, style, regime, and
component evidence. Portfolio Runs apply one fixed causal signal-to-position
policy with caps, side limits, covariance risk scaling, drift/no-trade
execution, costs, capacity, lifecycle, and robustness diagnostics. Governed RL
may select only among fixed factor sleeves built through that same Portfolio
Mandate; it cannot rewrite the action, reward, risk, or execution contracts.

Agents publish lane Reports, and the canonical Factor → Portfolio → optional
RL program can compose them into one immutable Project Dossier for OpenAlice:

```bash
uv run aq report publish ./quant-workspace \
  --session session-... \
  --analysis report-analysis.json \
  --json

uv run aq dossier status ./quant-workspace --json
uv run aq dossier publish ./quant-workspace \
  --analysis dossier-analysis.json \
  --json
```

OpenAlice may publish the exact handoff Markdown through its own Inbox and
attach authenticated collaboration provenance. AutoQuant deliberately does
not impersonate that authority.

## Studio

Studio is a lightweight read-only view over the same verified Core loaders
used by the CLI:

```bash
uv run aq studio snapshot ./quant-workspace --json
uv run aq studio serve ./quant-workspace
```

It shows current Projects, requests, Agent work briefs, Sessions, experiments,
lane progression, Portfolio Mandates, mechanical position evidence, governed
RL evidence, Reports, Dossiers, and exact copyable next commands.

## Repository structure

```text
Auto-Quant/
├── autoquant/                 # V2 Core, CLI, templates, and Studio
├── docs/                      # canonical contracts and design invariants
├── plans/                     # bounded engineering execution records
├── scripts/                   # repository checks
├── tests/                     # deterministic bounded verification
├── AGENTS.md                  # contributor and Agent routing guide
├── PLANS.md                   # active/completed plan index
└── pyproject.toml             # package and runtime dependencies
```

The repository-root Auto-Quant Classic/Freqtrade arena is retired. Research
data belongs inside caller-created Projects; Git history is the archive for
the removed Classic strategies, notebooks, and experiment snapshots. See
[retired-flat-freqtrade-harness.md](docs/design/retired-flat-freqtrade-harness.md).

## Development

Read [AGENTS.md](AGENTS.md) and [PLANS.md](PLANS.md) before non-trivial
changes. Do not launch an unbounded autonomous loop or a long multi-year
backtest as routine validation.

```bash
uv run python scripts/check_doc_links.py
uv run python -m unittest discover -s tests -v
uv build
```

## License

MIT.
