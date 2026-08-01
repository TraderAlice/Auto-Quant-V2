---
version: 0.9.18
---

# AutoQuant V2

AutoQuant turns quantitative research into a versioned, testable,
Agent-operable engineering workflow.

It is a usable pre-alpha AI-native quantitative workbench, not only a backtest
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
    └── Reports, Reviews, Dossiers, and read-only Studio projections
```

One Workspace may hold multiple self-contained Projects. A Project is one
evolving body of research; a Study locks one evaluation question; a Research
Session is a bounded editable investigation; a Run is an immutable
measurement.

## Current release candidate: `v0.9.18`

`v0.9.18` is the current AutoQuant release candidate; `v0.9.17` remains the
latest published tag until the candidate replay and release audit pass.
OpenAlice remains independently pinned to `v0.8.31` until the host deliberately
selects another tag; publishing AutoQuant does not migrate a Workspace or move
a host pin.

For the tested capability, current honest boundary, verification summary, and
release history, read [docs/STATUS.md](docs/STATUS.md). Version increments,
release audit, compatibility, tagging, and host-selection rules live in
[docs/design/versioning-and-release.md](docs/design/versioning-and-release.md).

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

OpenAlice keeps the desk's original Git checkout. AutoQuant V2 does not add an
`aq upgrade` workflow or promise automatic Workspace migration: a coding Agent
may pull and reconcile ordinary Git changes, or retire an old desk and create a
fresh one. Immutable Runs keep the Harness identity under which they were
produced even when the mutable checkout later moves.

AutoQuant owns quantitative research and historical simulation. An optional
host owns cross-Workspace communication and authenticated provenance. Brokers,
live accounts, approvals, and real order submission remain outside AutoQuant;
in OpenAlice that authority belongs to UTA. AutoQuant may model target
portfolios, orders, and TPSL when required for valid research without claiming
live-trading authority.

Existing-book questions use the separate `ohlcv-book-risk-lab`. It preserves
one caller-supplied baseline weight snapshot and may compare up to eight
caller-specified complete hypothetical books under the same historical
covariance windows. It returns component-risk, common-movement, standardized
reduction-sensitivity, fixed static-weight drawdown, and explicit
scenario-delta evidence without pretending that any snapshot is authenticated
account truth, reconstructed broker equity, or an optimized target.
See [reported-position Book Risk](docs/design/reported-position-book-risk.md).
When a later question uses the exact same dataset but needs an independent
position snapshot, `aq study intake . <study-id> --request <request.json>` adds
a Study-owned fixed request/Judge/input set inside the same Project. It does
not overwrite the original Study or manufacture a duplicate Project.

Price-defined conditional-history questions use
`ohlcv-event-study-lab`. Its first fixed contract preserves a downside opening
gap, exact delayed close entry and holding clock, every qualifying or censored
event, overlap treatment, unconditional same-asset history, and matched
reference-asset outcomes. It has no candidate Session, does not pretend an
OHLCV gap proves an earnings/news event, and returns no Order or live-trading
authority. See [OHLCV Price Event Study](docs/design/ohlcv-price-event-study.md).

Non-predictive strategic-allocation questions use
`ohlcv-allocation-lab`. Its narrow V1 contract constructs a long-only
equal-risk-contribution book from trailing completed returns, enforces
caller-owned caps and a scale-down-only volatility ceiling, and compares it
with a separately drifted and costed fixed-weight reference on the same
decision schedule. It has no Factor, RL, editable candidate, Session, Order, or
trading authority. See
[Portfolio-native Allocation Lab](docs/design/portfolio-native-allocation-lab.md).

See the canonical
[Agent-native workbench model](docs/design/agent-native-quant-workbench.md)
and [architecture](docs/ARCHITECTURE.md).

## Quick start

AutoQuant requires Python 3.11 and
[uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:TraderAlice/Auto-Quant-V2.git
cd Auto-Quant-V2
uv sync
uv run aq --version
uv run aq capabilities --json
uv run aq project list .
uv run aq validate .
uv run aq orient . --json
uv run aq studio serve .

# Start a genuinely new assignment as a sibling Project.
uv run aq project create . research-desk \
  --name "Research Desk" \
  --description "Coordinate factor, portfolio, and RL evidence" \
  --template ohlcv-research-desk \
  --json
# A Quant Agent now completes researchBriefPath and records any real
# framework gap at frameworkNeedsPath.
uv run aq project program . --project research-desk
uv run aq orient . --project research-desk --json
```

The checked-in `autoquant-workspace.json` selects the repository's internal
`projects/` and `sample-research-desk`. The sample is an ordinary Project, not
special runtime state. Its first Factor Run truthfully records the clean
`0.8.7` Harness that created it; it is retained so Studio has inspectable
evidence on first launch.

Framework contributors with a separate real-research collection may add the
Git-ignored `autoquant-workspace.local.json`. It is a complete strict Workspace
manifest and may point `projects_directory` outside the repository:

```json
{
  "default_project": "my-current-research",
  "name": "AutoQuant Development Desk",
  "projects_directory": "../quant-workspace/projects",
  "schema_version": 1
}
```

CLI and Studio disclose the effective Projects directory and whether this
local override is active. Invalid overrides fail explicitly. A normal clone
has no override and remains self-contained.

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

If the package does not exist yet, start from the Workspace's
`$acquire-market-ohlcv` Skill. It routes one market at a time to exact
provider procedures, requires two independently executable sources for
accepted coverage, preserves raw responses and transformation audits under
Workspace staging, and compares only matching price contracts. Official
routes come first when practical; Yahoo is broad but not an automatic primary.
`$package-autoquant-ohlcv` then bridges the selected staging package into the
same strict intake below. See
[Agent-native market-data acquisition](docs/design/agent-native-market-data-acquisition.md)
and the [field-trial ledger](docs/market-data-acquisition-field-trials.md).
Bundled Python Skill procedures use `aq-python <script> ...`, which guarantees
the same interpreter and dependencies as the installed Harness even when an
Agent shell's ambient `python3` points elsewhere.

Package asset paths resolve from the directory containing the dataset manifest.
If raw files already exist under `staging/raw-ohlcv/`, place
`dataset-package.json` at `staging/` and use paths such as
`raw-ohlcv/AAPL.csv`. This avoids a temporary second raw-data copy; the
Project-local normalized content-locked snapshot created by intake remains
intentional. Parent paths, absolute paths, and symlinks are rejected.

Data acquisition is demand-led. Existing local bytes may satisfy a later
Study only when their complete identity matches the clarified question; their
availability never limits which market, symbol, interval, or history the Agent
may research. Cross-Project deduplication is optional storage work, not a Core
research contract.

```bash
uv run aq schema research-request --json
uv run aq schema ohlcv-dataset-package --json
uv run aq project intake . us-leadership \
  --request research-request.json \
  --dataset /path/to/dataset.json \
  --json
```

The request may lock:

- long-only, short-only, two-sided, or context-only duties per asset;
- gross, per-asset, volatility, cost, no-trade, and reference-NAV assumptions;
- cash, one named dataset asset, or one funded non-negative fixed-weight
  basket as the evaluation benchmark;
- primary and diagnostic forward horizons;
- Portfolio/RL decision cadence and dataset/session clock anchor;
- one reported or hypothetical funded baseline plus optional caller-authored
  complete hypothetical books for a fixed, non-authenticated Book Risk audit.
- one fixed adjusted-OHLCV opening-gap event, delayed return clock, matched
  reference asset, overlap policy, and minimum useful sample count.
- one fixed equal-risk-contribution construction and complete funded
  fixed-weight reference portfolio.

These are immutable research assumptions. They never grant live position or
execution authority.

## Research loop

A Session creates a disposable worktree with an exact editable closure. A fast
candidate Check can catch structural errors without creating evidence.
The fixed Judge alone publishes metrics and a KEEP, REVERT, or CRASH verdict.
Promotion remains a separate guarded operation.

```bash
uv run aq session start . \
  --study factor-quality \
  --request research-request.json \
  --json

uv run aq session check . \
  --session session-... \
  --json

uv run aq experiment evaluate . \
  --session session-... \
  --hypothesis "Add volatility normalization" \
  --json

uv run aq session promote . \
  --session session-... \
  --json
```

Any explicit external coding-Agent command can drive the same bounded loop.
AutoQuant supplies the verified brief, protects fixed source, and retains every
turn and evaluation as evidence:

```bash
uv run aq research run . \
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
Fixed Price Event Runs instead publish a complete conditional-event ledger,
reference distributions, descriptive uncertainty, and an evidence-status
conclusion without entering the candidate-selection lifecycle.

Agents may publish lane Reports, and the canonical Factor → Portfolio →
optional RL program can compose them into one immutable Project Dossier:

```bash
uv run aq report publish . \
  --session session-... \
  --analysis report-analysis.json \
  --json

uv run aq dossier status . --json
uv run aq dossier publish . \
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
uv run aq studio snapshot . --json
uv run aq studio serve .
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

The current release proof and tested capability boundary are recorded in
[docs/STATUS.md](docs/STATUS.md); detailed real-request outcomes live in
[docs/trading-request-field-trials.md](docs/trading-request-field-trials.md).
Before changing versions or publishing tags, follow
[docs/design/versioning-and-release.md](docs/design/versioning-and-release.md).

```bash
uv run python scripts/check_doc_links.py
uv run python -m unittest discover -s tests -v
uv build
```

## License

MIT.
