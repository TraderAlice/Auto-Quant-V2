---
version: 0.4.2
---

# AutoQuant V2

AutoQuant turns quantitative research into a versioned, testable,
Agent-operable engineering workflow.

It is a complete AI-native quantitative workbench, not only a backtest
library, strategy generator, or integration backend. A coding Agent can enter
the filesystem, understand the current question and evidence, take one bounded
action, edit only an authorized research surface, evaluate through fixed
contracts, resume after interruption, and leave durable work for the next
Agent or human reviewer.

The working model is:

```text
long-lived Workspace
└── Project
    ├── question or delegated request
    ├── content-locked data and fixed Studies
    ├── bounded Agent Research Sessions
    ├── factors, portfolios, ML/RL policies, and simulations
    ├── immutable Runs and evidence
    └── Reports, Dossiers, and read-only Studio projections
```

One Workspace may hold multiple self-contained Projects. A Project is one
evolving body of research; a Study locks one evaluation question; a Research
Session is a bounded editable investigation; a Run is an immutable
measurement.

## Standalone or an OpenAlice desk

AutoQuant has one product shape in both environments:

```text
standalone clone                    OpenAlice Trading Harness
└── AutoQuant Workspace             └── AutoQuant Workspace desk
    └── Quant Agent                     └── Quant coworker
        └── Projects                        └── Projects
```

Standalone, a human or Agent clones AutoQuant and operates it directly.
Inside OpenAlice, the same workbench can be materialized as a specialized
Workspace desk. An Agent at another desk can delegate a quantitative task to a
coworker at the AutoQuant desk and receive a report when the work is useful.
There is no separate OpenAlice edition and no private service API defining the
research lifecycle.

AutoQuant owns quantitative research and historical simulation. An optional
host owns cross-Workspace communication and authenticated provenance. Brokers,
live accounts, approvals, and real order submission remain outside AutoQuant;
in OpenAlice that authority belongs to UTA. AutoQuant may model target
portfolios, orders, and TPSL when required for valid research without claiming
live-trading authority.

See the canonical
[Agent-native workbench model](docs/design/agent-native-quant-workbench.md)
and [architecture](docs/ARCHITECTURE.md).

## Quick start

AutoQuant requires Python 3.11 and
[uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run aq --version
uv run aq capabilities --json
uv run aq workspace init ./quant-workspace --name "Quant Research Desk"
uv run aq project create ./quant-workspace research-desk \
  --name "Research Desk" \
  --description "Coordinate factor, portfolio, and RL evidence" \
  --template ohlcv-research-desk \
  --json
# A Quant Agent now completes researchBriefPath and records any real
# framework gap at frameworkNeedsPath.
uv run aq project program ./quant-workspace --project research-desk
uv run aq validate ./quant-workspace
uv run aq orient ./quant-workspace --project research-desk --json
```

`project create` is the normal construction entry point. It creates
`research.md`, `framework-needs.md`, the Project manifest, and the Project-local
strategy, factor, model, Judge, Study, Session, data, Run, and cache surfaces.
Before quantitative work, the Agent rewrites `research.md` in English, asks the
delegating Agent or user about every material ambiguity, and continues only
when the question is bounded and testable. Real reusable Workbench gaps go in
`framework-needs.md`, not the research brief. The caller may converse in any
language.

Factor candidates receive the complete Study universe as one ordinary
long-form pandas DataFrame:

```python
def compute_factor(panel: pd.DataFrame) -> pd.Series:
    within_asset = panel.groupby("asset")["close"].pct_change(20)
    return within_asset.groupby(panel["timestamp"]).rank(pct=True)
```

This supports causal rolling features and same-timestamp cross-asset context
without a factor DSL. Factor, Portfolio, governed RL, and preflight use the
same panel runtime and whole-panel timestamp-prefix causality audit.

`aq` emits compact human output by default and a versioned machine envelope
under `--json`. See [CLI.md](docs/CLI.md) and
[PROJECT_FORMAT.md](docs/PROJECT_FORMAT.md).

CSV intake works in the base environment. Parquet and Feather are optional:

```bash
uv sync --extra columnar
```

## Start from a real research request

A caller may begin with an ordinary conversational assignment. The Quant Agent
first turns it into the Project's English Markdown research brief; strict JSON
does not replace that clarification step.

Once intent is understood and a matching OHLCV package is available, the Agent
can derive the strict request and use the atomic intake fast path below. Intake
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

## Evidence and deliverables

Factor Runs publish purge-aware IC, decay, quantile, style, regime, and
component evidence. Portfolio Runs apply one fixed causal signal-to-position
policy with caps, side limits, covariance risk scaling, drift/no-trade
execution, costs, capacity, lifecycle, and robustness diagnostics. Governed RL
may select only among fixed factor sleeves built through that same Portfolio
Mandate; it cannot rewrite the action, reward, risk, or execution contracts.

Agents may publish lane Reports, and the canonical Factor → Portfolio →
optional RL program can compose them into one immutable Project Dossier:

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

A Report or Dossier is a durable evidence-bound Project artifact, not a
mandatory RPC response. It may be reviewed locally, handed to another Agent,
or delivered through a host. When OpenAlice is the host, it may publish the
exact Markdown through Inbox and attach authenticated collaboration
provenance; AutoQuant deliberately does not impersonate that authority.

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
