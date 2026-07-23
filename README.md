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
uv run aq project create ./quant-workspace factor-lab \
  --name "Factor Lab" \
  --description "Mine robust cross-asset factors"
uv run aq project create ./quant-workspace ml-lab --name "ML Lab"
uv run aq project list ./quant-workspace
uv run aq validate ./quant-workspace
uv run aq inspect ./quant-workspace --project factor-lab --json
```

`aq` emits compact human output by default and one versioned JSON envelope with
contexts, artifacts, operation effects, and executable next actions under
`--json`. See [`docs/PROJECT_FORMAT.md`](docs/PROJECT_FORMAT.md) and
[`docs/CLI.md`](docs/CLI.md).

The repository-root strategy arena described below remains the V0.5
compatibility Harness while its execution and evidence contracts are migrated
into Projects.

V2 Projects can also define strict Studies and publish immutable RunResults
through one bounded Python Judge lane. This is the common evidence contract for
future Freqtrade, factor, and ML research:

```bash
uv run aq study list ./quant-workspace
uv run aq study inspect ./quant-workspace --study factor-quality --json
uv run aq run execute ./quant-workspace --study factor-quality --json
uv run aq run list ./quant-workspace --study factor-quality
```

Study, Judge output, and RunResult formats are documented in
[`docs/PROJECT_FORMAT.md`](docs/PROJECT_FORMAT.md). The autonomous
KEEP/REVERT/CRASH mutation loop will build on these immutable Runs rather than
parsing free-form backtest output.

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
