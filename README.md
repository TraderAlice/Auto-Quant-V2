# Auto-Quant

> LLM-native autonomous quant research loop. Karpathy's
> [autoresearch](https://github.com/karpathy/autoresearch) pattern applied to
> OHLCV strategy research.

The idea: give an LLM agent a fixed backtest Harness and a small strategy
workspace. The agent modifies strategies, runs bounded studies, checks the
results, and keeps or discards hypotheses. The **loop lives in `program.md`**,
not in an orchestrator.

AutoQuant V2 is growing this proven loop into one long-lived quantitative
Workspace with many self-contained research Projects. The Workspace supplies
the standardized Harness and Agent CLI; Projects own the concrete strategy,
factor, model, dataset, Study, and Run work.

## V2 Workspace quick start

```bash
uv sync
uv run aq capabilities --json
uv run aq workspace init ./quant-workspace --name "Quant Research Desk"
uv run aq project create ./quant-workspace research-desk \
  --name "Research Desk" \
  --description "Coordinate factor, portfolio, and RL evidence" \
  --template ohlcv-research-desk
uv run aq project program ./quant-workspace --project research-desk
uv run aq project create ./quant-workspace ml-lab --name "ML Lab"
uv run aq project list ./quant-workspace
uv run aq validate ./quant-workspace
uv run aq inspect ./quant-workspace --project factor-lab --json
```

`aq` emits compact human output by default and one versioned JSON envelope with
contexts, artifacts, operation effects, and executable next actions under
`--json`. See [`docs/PROJECT_FORMAT.md`](docs/PROJECT_FORMAT.md) and
[`docs/CLI.md`](docs/CLI.md).

For an actual delegated question, construct a Project from a strict request and
caller-supplied OHLCV package instead of editing a synthetic template:

```bash
uv run aq schema ohlcv-dataset-package --json
uv run aq project intake ./quant-workspace us-leadership \
  --request research-request.json \
  --dataset /path/to/dataset.json \
  --json
```

Intake validates and normalizes the complete aligned panel, confines every
source path, preserves provider/calendar/adjustment claims, hashes source and
Project-local bytes, and transactionally creates one coordinated Project with
Factor, Portfolio, and governed RL Studies. It also derives one fixed
Portfolio Mandate: requested assets and direction define position authority,
while other panel assets remain research context. The Mandate also fixes a
causal one-sided covariance volatility ceiling shared by Portfolio and RL. It
does not download data or silently start research. `aq project program`
returns verified lane status,
shared-source conflicts, evidence currentness, and the exact recommended
headless command. The narrow single-lane templates remain available when a
caller intentionally selects one method.

Daily V1 packages remain valid. A V2 package may declare a continuous UTC 1h
base with completed 3h/4h/6h/12h/1d context. AutoQuant derives and reconciles
those bars from the locked base, joins them only after their close, and gives
all three research lanes the same ordinary pandas frame. RunResults and the
OpenAlice-facing evidence surfaces disclose the exact interval contract.

For a new coding Agent, start with one read-only command:

```bash
uv run aq orient ./quant-workspace --project us-leadership --json
```

It returns the current research question, scientific/coordination reason,
exact writable Session worktree closure, protected authority, and one primary
command with its declared effect. Studio renders the same Core object and
hash, so the AI operator and human reviewer share one current work contract.

The `ohlcv-factor-lab` starter is the first runnable V2 research Project. It
uses ordinary pandas/NumPy factor code, a deterministic six-asset synthetic
OHLCV fixture, dataset-fixed purge-aware chronological evaluation, dataset
byte locks, and a fixed causality audit. Its professional tear sheet adds
1/5/10-bar rank/Pearson IC and decay, HAC strength, fixed-tertile behavior,
OHLCV-style overlap, and asset/fold/causal-regime stability with exact daily
artifacts. A candidate may also explicitly declare causal components. The
Judge then reports component raw/residual IC, final-factor association,
pairwise redundancy, and leave-one-out impact on one fixed equal-rank
diagnostic blend; it never guesses Python column use or treats that blend as
the arbitrary final factor. Its baseline is intentionally fast and the fixture
is a Harness benchmark—not a market alpha claim.

The `ohlcv-portfolio-lab` starter keeps the same ordinary pandas candidate API
but fixes the downstream research contract: causal percentile
entry/hold/exit/reversal state, inverse-volatility conviction sizing,
request-mapped long/cash, short/cash, or dollar-neutral capped targets,
then a trailing-covariance portfolio forecast that only scales exposure down
above a fixed 15% annualized ceiling. It also fixes drift-aware rebalance,
turnover, costs, volume participation, and dataset-fixed purged splits.
After drift, the final book is checked again: an excessive retained book
bypasses the no-trade band and receives only the proportional scale-down
needed to restore the same ceiling. Governed RL uses this exact execution
primitive for training and evaluation.
It inverts the exact executed trade path against causal trailing
close-times-volume at fixed 1%/5% participation ceilings, producing a
reconciled capital-capacity envelope rather than pretending OHLCV can model
spread, impact, or fills.
Context-only assets participate in research
ranking but never become positions. Its decision ledger reconciles each
asset's mandate, proposed/executed weight, trade, return, cost, regime, and
component risk contribution; a no-hysteresis baseline shows whether intent
persistence actually reduces churn. A split-bounded position-lifecycle
artifact then reconstructs contiguous executed long/short episodes, allocates
entry/resize/exit/reversal costs, and reports complete-episode holding, win,
payoff, MFE/MAE, and intent-mismatch evidence without treating censored
segments as completed trades. A fixed 5×3 entry/exit and no-trade parameter
neighborhood then shows local Sharpe, turnover, cost, and transition stability
without choosing a winning cell. Studio summarizes the verified policy,
attribution, lifecycle, and parameter-neighborhood evidence. Its current
mechanical-decision ticket also shows every Mandate-permitted next
entry/exit/reversal percentile boundary, the current same-cross-section buffer,
raw/governed target, drifted/executed weight, and the exact no-trade or
risk-repair reason. Those buffers are not price targets or forecasts. It emits
research targets only and has no Broker or trading-account authority.

Every reference Project uses validation-only KEEP/REVERT. Test metrics remain
visible diagnostic evidence; after a Session iterates candidates, Core marks a
new external holdout as required. Core also groups every matching immutable
Run into a Project-wide fixed-evaluation research family, deduplicates repeated
source executions, and carries the complete as-of search count through Studio
and immutable Research Reports. Factor evidence receives family-wise
Bonferroni-HAC inference; Portfolio evidence receives PSR/DSR and a minimum
track-record check. These are diagnostic selection-risk disclosures and never
rewrite KEEP/REVERT.

The `ohlcv-rl-factor-lab` starter asks a narrower question than “can an RL bot
trade?”: can a bounded policy use causal regime features to choose among a
content-locked candidate factor and fixed reference factors? Agents edit only
a pure state encoder. The Judge audits the factor dependency and fixes
Q-learning, actions, next-bar reward, portfolio accounting, two expanding
folds, three seeds, and fixed-factor/contextual-ridge baselines. Each action is
a governed stateful factor sleeve using the same request-bound Portfolio
Mandate, mechanical signal policy, and one-sided risk governor. Evidence
reports both
RL-minus-best-baseline and RL-minus-candidate-factor.
The Harness-owned episode budget, learning rate, discount, and exploration
schedule are frozen from a predeclared train-only blocked stability audit;
new Runs preserve that provenance, while legacy Runs remain readable without
fabricated provenance.
New Runs also preserve exact chosen-versus-runner-up linear-Q rationales and
split/fold/seed-bounded action runs. This exposes one-bar churn, persistence,
uncalibrated Q margins, and dominant margin contributions without calling
them probability, confidence, causal importance, or trading authority.
Validation is the promotion metric; test evidence is reported separately with
an explicit repeated-inspection warning. A higher RL score does not count as
value added when a simple baseline still wins.

The repository-root strategy arena described below remains the V0.5
compatibility Harness while its execution and evidence contracts are migrated
into Projects.

V2 Projects can also define strict Studies and publish immutable RunResults
through one bounded Python Judge lane. This is the common evidence contract for
Freqtrade, factor, portfolio, and governed model research:

```bash
uv run aq study list ./quant-workspace
uv run aq study inspect ./quant-workspace --study factor-quality --json
uv run aq run execute ./quant-workspace --study factor-quality --json
uv run aq run list ./quant-workspace --study factor-quality
```

Study, Judge output, and RunResult formats are documented in
[`docs/PROJECT_FORMAT.md`](docs/PROJECT_FORMAT.md). The autonomous
mutation loop now builds on these immutable Runs rather than parsing free-form
backtest output:

```bash
# Establish a fresh successful baseline and a disposable candidate worktree.
uv run aq session start ./quant-workspace --study factor-quality --json

# Or bind an OpenAlice/local request into the Session's exact Research Brief.
uv run aq session start ./quant-workspace \
  --study factor-quality \
  --request research-request.json \
  --json

# Edit only the returned worktree/editablePaths. Reference Studies first offer
# a fast fixed Check with no metric, verdict, or selection authority.
uv run aq session check ./quant-workspace \
  --session session-... \
  --json

# After the exact candidate passes, judge one hypothesis formally.
uv run aq experiment evaluate ./quant-workspace \
  --session session-... \
  --hypothesis "Add volatility normalization" \
  --json

# Repeat after KEEP/REVERT/CRASH, or explicitly publish the current KEEP.
uv run aq session promote ./quant-workspace --session session-... --json
```

REVERT and CRASH restore the exact Session leader. Promotion is separate,
requires an unchanged Project base, and rolls back if its receipt cannot be
committed. Candidate Checks are optional operational feedback: they create no
Run or Experiment, leave failures editable, and never replace the fixed Judge.

The same loop can be driven by any explicit external coding-Agent command.
AutoQuant sends a complete versioned brief on stdin, accepts only a strict
proposal or stop response, and preserves every bounded turn as immutable
Campaign evidence:

```bash
uv run aq research run ./quant-workspace \
  --session session-... \
  --agent-command 'my-coding-agent --autoquant-research' \
  --max-turns 5 \
  --max-wall-seconds 900 \
  --turn-timeout-seconds 300 \
  --json
uv run aq research list ./quant-workspace --session session-...
```

The supplied command is authorized host-code execution, not an AutoQuant
sandbox. It may propose candidate code, but the locked Judge still owns
metrics and verdicts, and Project promotion remains a separate explicit
operation.

A delegated Session preserves the caller's question, assets, direction,
horizon, constraints, deliverables, and caller-supplied origin context. The
selected Study must cover the requested assets. After research, an Agent
submits strict findings that reference verified Session evidence; AutoQuant
publishes immutable machine and human handoffs:

```bash
uv run aq schema research-request --json
uv run aq schema report-analysis --json
uv run aq report publish ./quant-workspace \
  --session session-... \
  --analysis report-analysis.json \
  --json
uv run aq report show ./quant-workspace \
  --session session-... \
  --report report-... \
  --json
```

Core validates every cited Run, Experiment, Campaign, and Run artifact, then
freezes `report.json` and deterministically renders `report.md`. Reports are
quantitative decision support only and have no live-trading authority.
Portfolio Reports additionally freeze the exact leader Run's historical
mechanical decision—state transitions, next percentile conditions, weights,
turnover/risk gate, sizing anatomy, and decision hashes. The anatomy explains
conviction/inverse-volatility strength, proportional side budget,
cap/water-fill redistribution, governed/executed weight, and component risk.
It also freezes effective risk bets and the 25% / 50% / 100% covariance-blend
ladder toward perfect position-aligned correlation, including validation/test
ceiling-breach rates and per-asset stress-risk shares.
The same frozen support diagnoses whether validation evidence fails at factor
prediction, gross portfolio monetization, or trading friction, with cost
break-even, delay, monthly breadth, best-day dependence, and underwater
duration. Its next focus prioritizes research only.
Factor Reports similarly freeze the verified candidate-declared component
diagnosis when available, including its non-exhaustive declaration,
fixed-blend-only ablation semantics, and lack of Portfolio/RL/trading
authority.
Project Dossiers inherit those exact Report bytes; neither artifact silently
changes when a later Run appears.
OpenAlice should publish the exact Markdown through its own Inbox so OpenAlice
can stamp authoritative Workspace, Session, and document-revision provenance.

After a lane Report is current, an Agent either promotes an improved KEEP or
finishes a baseline-retaining lane without changing Project source:

```bash
uv run aq session complete ./quant-workspace \
  --session session-... \
  --report report-... \
  --json
```

The immutable completion receipt removes the Session from active Program
conflicts while preserving its Report as point-in-time evidence.

For the canonical evidence-gated Factor → Portfolio → optional RL Research
Program, lane Reports are composed into one immutable Project Research
Dossier:

```bash
uv run aq dossier status ./quant-workspace --json
uv run aq schema dossier-analysis --json
uv run aq dossier publish ./quant-workspace \
  --analysis dossier-analysis.json \
  --json
uv run aq dossier show ./quant-workspace \
  --dossier dossier-... \
  --json
```

Core admits Portfolio only after the frozen Factor leader reaches
`factor-qualification-positive`, admits optional RL only after the frozen
Portfolio leader reaches `post-cost-edge-positive`, and never confuses a
reported coordination phase with a scientific pass. Core verifies exact
Report/finding references, freezes every included lane and explicit gated or
optional omission, and renders `dossier.json` plus `dossier.md`. A weak Factor
may therefore end in a valid Factor-only early-stop Dossier instead of forcing
downstream compute.
AutoQuant still has no trading authority; OpenAlice owns Inbox publication and
authenticated collaboration provenance.

Humans can watch the same Workspace through the lightweight local Studio:

```bash
uv run aq studio snapshot ./quant-workspace --json
uv run aq studio serve ./quant-workspace
uv run aq run factor ./quant-workspace --run RUN_ID --json
uv run aq run rl ./quant-workspace --run RUN_ID --json
uv run aq session compare ./quant-workspace --session SESSION_ID --json
```

Studio shows Projects, delegated requests, active Session leaders, running
Researcher turns, verdict trajectories, lane Report/Dossier readiness, recent
evidence, and fixed Studies. For the latest successful Portfolio Run it also
shows the request-bound mandate, authorized/context-only assets, bounded
verified growth/drawdown, exposure/cash/turnover, the historical mechanical
book, raw/governed targets, the conviction → inverse-volatility →
cap/water-fill position-sizing anatomy, a validation-only factor → gross →
friction → net viability diagnosis, portfolio-volatility forecast/scale, signal
transitions, effective risk bets and the 25% / 50% / 100% correlation-breakdown
ladder, final executed-book risk compliance, split attribution, and
validation/test liquidity-capacity envelopes with binding assets, plus
validation/test mechanical position episodes and per-asset lifecycle
statistics, plus a validation/test 5×3 mechanical-parameter heatmap whose cells
are context-only and cannot enter selection. It is read-only, exposes
copy-only exact CLI commands, and uses the same verified Core loaders as the
CLI. A specific historical Run is available through `aq run factor <path>
--run ID --json`, `aq run portfolio <path> --run ID --json`, or
`aq run rl <path> --run ID --json`. The RL explorer leads with value-add
versus the fixed validation-selected baseline, then preserves every fold/seed,
training episode, action allocation, turnover, cost, and test-audit warning.
Its action ledger also proves post-drift risk compliance for every fold and
seed. Its policy-behavior panel reconciles action-run persistence and exact
linear chosen-versus-runner-up rationale against the frozen model and action
ledger; legacy Runs remain readable with rationale evidence marked unavailable.
See
[`docs/STUDIO.md`](docs/STUDIO.md).

The v0.5 development Harness still uses **Freqtrade as its one core engine**,
but assets are no longer hardwired into that engine:

- `crypto-majors` preserves the existing Binance, 24/7, five-pair study.
- `us-equities` is the first session-market profile. It consumes local OHLCV,
  uses a static US-composite market facade (no Broker account), preserves overnight
  and weekend gaps, and fills stops at the opening price when a session gaps
  through the stop.

Both profiles and their data contracts are versioned in `harness.json`. Candle
files live under the repository-local, gitignored `data/<profile>/` tree.

This is a prototype to validate whether Karpathy's autoresearch pattern
transfers to quant research. The success metric is "did the loop run and
produce an interpretable `results.tsv`", **not** "did we find a profitable
strategy". Nothing in this repo is a recommendation to trade real capital.

## A run in one picture

![Sharpe frontier — v0.1.0 run](sharpe-frontier.png)

One dot per backtest over 99 experiments on BTC/USDT + ETH/USDT @ 1h. Green
dots were kept by the agent, gray were discarded. The red line is the
running best of *kept only* — it plateaus at Sharpe 1.44, **not** at the
Sharpe-18 cluster on the right. Those high-Sharpe runs are gray because the
agent itself identified them as oracle-gaming (ROI-clipping that compressed
return variance without improving real return) and retroactively discarded
them. Full write-up in
[`versions/0.1.0/retrospective.md`](versions/0.1.0/retrospective.md).

## How it works

Five things that matter:

- **`harness.json`** — versioned Harness and asset-profile manifest: universe,
  venue metadata, market clock, timeframes, fees, local data path, and engine
  version. The agent does not touch this.
- **`config.json`** — compatibility base config for Freqtrade. Profile values
  are applied by the Harness at runtime. The agent does not touch this.
- **`prepare.py`** — prepares one selected profile. Crypto can download through
  Freqtrade; other profiles import conventional CSV, Parquet, or Feather OHLCV.
  The agent does not touch this.
- **`run.py`** — in-process **batch backtest**. Discovers every `.py` under
  `user_data/strategies/` (skipping files prefixed `_`), runs FreqTrade's
  `Backtesting` for each compatible strategy, and prints profile and Harness
  identity in every result block. The agent does not touch this.
- **`user_data/strategies/`** — **the directory the agent owns**. Each `.py`
  is one strategy; up to 3 active at a time. Agent creates / evolves / forks
  / kills strategies here. A strategy can declare `asset_classes` or the
  narrower `asset_profiles`; incompatible strategies are explicitly skipped.

Plus:

- **`program.md`** — the autonomous-research instructions the human points the
  LLM agent at.
- **`results.tsv`** — event log. Schema: `commit | event | strategy_name | sharpe | max_dd | note`.
  Events: `create | evolve | stable | fork | kill`. Gitignored so it survives
  `git reset --hard` — past lessons stay available even when experimental
  commits get thrown away.
- **`analysis.ipynb`** — post-hoc read: per-strategy trajectories, cap
  utilization, event distribution, note word frequency.

*Version history*:
- **v0.1.0** ([archive](versions/0.1.0/)): single-file mutation. Anchored
  on one paradigm for all 99 rounds. Headline Sharpe 1.44 was mostly
  oracle gaming (true-edge 0.19). See [retrospective](versions/0.1.0/retrospective.md).
- **v0.2.0** ([archive](versions/0.2.0/)): multi-strategy (up to 3 slots).
  5 paradigms tested / 3 kept / 0 Goodhart attempts. Peak clean Sharpe
  0.67 (~3.5× better than v0.1.0's true-edge). See [retrospective](versions/0.2.0/retrospective.md).
- **v0.3.0** ([archive](versions/0.3.0/)): multi-strategy + multi-timeframe +
  multi-asset portfolio. Adds 4h + 1d informative data, expands universe to
  5 pairs (BTC/ETH/SOL/BNB/AVAX), and emits per-pair metrics. **First
  project-wide clean Sharpe > 1.0** (1.07 on BTCLeaderBreakX). Also: first
  fork event + isolation experiment. See [retrospective](versions/0.3.0/retrospective.md).
- **v0.4.0** ([archive](versions/0.4.0/)): regime extension to 2021-2025
  + dynamic position sizing. Real-edge clean Sharpe **1.122 / +232%** on
  5-year regime mix (strictly stronger than v0.3.0 on harder data). Surfaced
  the "Sharpe-as-single-oracle has a degeneracy boundary" finding and the
  cleanest sizing-vs-edge controlled experiment in the project.
  See [retrospective](versions/0.4.0/retrospective.md).
- **v0.4.1** ([archive](versions/0.4.1/)): four affordances bundled —
  `pair_basket` (strategy-declared portfolio), `test_timeranges` (multi-regime
  backtest with `robust_sharpe = min` as headline), per-timerange buy-and-hold
  benchmark, and multi-objective signals (`profit_floor`, `pareto_dominated_by`,
  plus an advisory tiny-stakes watch on capital utilization) flanking the
  headline metric. Direct response to
  v0.4.0's Sharpe-degeneracy finding. **First multi-strategy lineup with
  `robust_sharpe > 0` across all four declared regimes (bull/winter/recovery/
  full-5y) simultaneously**, but the run also surfaced an "early Pareto lock"
  pattern where the regime-robust frontier was set at round 9 by a single
  sizing ablation and never broken across the next 20 rounds. Five new
  cross-version findings + four reinforcements + two narrows of prior
  universal claims. See [retrospective](versions/0.4.1/retrospective.md).

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- TA-Lib (the C library — installed separately from the Python binding)

## Install

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install the TA-Lib C library
#    macOS:  brew install ta-lib
#    Linux:  see https://github.com/mrjbq7/ta-lib#dependencies
#    If native install is painful on your platform, the FreqTrade Docker
#    image ships with TA-Lib pre-built and works as an alternate runtime.

# 3. Install Python deps
uv sync

# 4. Prepare the default crypto profile
uv run prepare.py

# 5. List profiles and run the selected research arena
uv run prepare.py --list-profiles
uv run run.py > run.log 2>&1; echo "exit=$?"
```

To import US-equity data, provide one file per pair and timeframe using names
such as `AAPL_USD-1h.csv` and `AAPL_USD-1d.parquet`:

```bash
uv run prepare.py --profile us-equities --source-dir /path/to/ohlcv
uv run run.py --profile us-equities > run.log 2>&1
```

Required columns are `date` (or `datetime`, `timestamp`, `time`), `open`,
`high`, `low`, `close`, and `volume`. Timestamps are normalized to UTC.
Equity data must omit weekend candles. The importer writes normalized Feather
files to `data/us-equities/`.

## Running the agent

Open a **second** terminal (keep your editor/IDE in the first so the two
sessions don't fight over the working tree), `cd` into the repo, and start
your preferred LLM agent (Claude Code, Codex, Cursor agent, etc.). Then
prompt something like:

> Have a look at `program.md` and let's kick off a new experiment. Let's do
> the setup first.

The agent reads `program.md`, goes through setup, then enters the experiment
loop. It keeps iterating until you interrupt it or it runs out of context.

Framework development uses a separate, repository-native coordination loop.
Read [`AGENTS.md`](AGENTS.md) before non-trivial changes, find live work in
[`PLANS.md`](PLANS.md), and keep lasting subsystem truth under
[`docs/design/`](docs/design/). This lets humans and Coding Agents continue
long-running V2 development without treating chat history as the system of
record.

### Permissions

The loop only works if the agent can run commands without a human approving
each one — it will invoke `uv run run.py`, `git commit`, `git reset`, and
edit the strategy file hundreds of times. How you grant that depends on your
tooling:

- **Claude Code**: prefer a scoped allowlist via a project-level
  `.claude/settings.json`. See the
  [permissions docs](https://docs.claude.com/en/docs/claude-code/settings#permissions)
  for patterns like `Bash(uv run *)` and `Bash(git commit:*)`.
- **Other agents**: most have an equivalent — a config flag or settings file
  to mark specific commands or tools as pre-approved.

Read the docs and choose a permission posture you're comfortable with before
leaving a loop running unattended. The agent is pointed at a sandboxed
FreqTrade workspace and has no live-trading access (all `dry_run`), but it
does run arbitrary shell commands and write files inside this directory.

## Project structure

```
Auto-Quant/
├── README.md
├── pyproject.toml                     # uv-managed deps
├── .python-version                    # 3.11
├── harness.json                       # Harness + asset profiles
├── autoquant/                         # profile/data/engine adaptations
├── config.json                        # FreqTrade compatibility base
├── prepare.py                         # download/import/validate profile data
├── run.py                             # backtest + summary (read-only for agent)
├── program.md                         # agent instructions
├── analysis.ipynb                     # post-hoc analysis
├── data/                              # gitignored, project-local OHLCV
│   ├── crypto-majors/
│   └── us-equities/
├── user_data/
│   ├── strategies/
│   │   ├── _template.py.example       # skeleton the agent copies from
│   │   ├── _equity_template.py.example
│   │   └── <agent-created files>.py   # up to 3 active at a time
│   └── backtest_results/              # gitignored — FreqTrade outputs
├── tests/                             # deterministic, no long backtest
├── versions/                          # frozen snapshots of past runs
└── results.tsv                        # gitignored — agent's event log
```

## Design notes

- **Agent owns one directory, not one file.** `user_data/strategies/` is its
  workspace; everything else is evaluation contract. Up to 3 strategies
  simultaneously, hard cap. Multi-strategy exists specifically to fight
  the single-paradigm anchoring that v0.1.0 exhibited.
- **No CLI indirection.** The agent only runs `uv run prepare.py` and
  `uv run run.py`. `run.py` uses FreqTrade's `Backtesting` class in-process,
  so startup is fast and errors surface as real Python stack traces.
- **One engine, explicit market clocks.** Asset profiles do not choose random
  backtest libraries. The session adapter is deliberately narrow: it disables
  Freqtrade's crypto-style missing-candle fill, expands indicator warmup by
  real bars, handles stop gaps, and uses a 252-session risk clock.
- **No Broker abstraction in the Harness.** `us-equities` uses venue metadata
  only to satisfy the backtest engine's precision and market contracts. It
  cannot place or download live orders. OpenAlice's Unified Trading Account
  remains a separate forward-execution concern.
- **Bar-model limits remain visible.** This is OHLCV simulation, not L2 replay.
  Weekend validation is deterministic, but v0.5-dev does not yet validate
  exchange holidays, early closes, or vendor-specific corporate-action rules.
- **`results.tsv` is a gitignored event log.** Each round, the agent appends
  rows (one per strategy touched, with event type: create/evolve/stable/fork/kill).
  It survives `git reset --hard` so past lessons stay available even when
  experimental commits get thrown away.
- **LLM decides keep/kill, not a scalar rule.** Sharpe on a finite window
  is noisy and gameable. Agent reads the full per-strategy summary blocks
  and decides inline which strategies to evolve, fork, or kill — the
  program.md rules force action but not which action.
- **Stagnation rule.** A strategy can't sit idle for more than 3 consecutive
  stable rounds — agent must evolve, fork, or kill it. With only 3 slots,
  dead weight is expensive.

## License

MIT.
