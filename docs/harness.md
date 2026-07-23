# Auto-Quant Harness contract (v0.5-dev)

`harness.json` is the versioned boundary between Auto-Quant framework code and
a research Study. It selects one stable core engine, Freqtrade 2026.3, while
making the market and data assumptions explicit.

## Select and prepare a profile

```bash
uv run prepare.py --list-profiles
uv run prepare.py --profile crypto-majors
uv run prepare.py --profile us-equities --source-dir /path/to/ohlcv
uv run prepare.py --profile us-equities --validate-only
```

Selection order is `--profile`, then `AUTOQUANT_PROFILE`, then
`default_profile` from the manifest.

Each profile declares:

- asset class and venue metadata;
- continuous or session market clock;
- pair universe, base timeframe, informative timeframes, and timerange;
- stake currency, fee, precision, and portfolio concurrency;
- annualization clock;
- data provider, repository-local directory, format, and missing-bar policy.

The local importer accepts CSV, Parquet, or Feather with:

```text
date, open, high, low, close, volume
```

`datetime`, `timestamp`, and `time` are accepted aliases for `date`. Files use
`BASE_QUOTE-timeframe` names, for example `SPY_USD-1h.csv`. Import normalizes
timestamps to UTC, checks numeric OHLCV and price bounds, rejects duplicates,
and rejects weekend bars for session profiles.

All normalized datasets are written to `data/<profile>/`, which is ignored as
a whole. The first default-profile prepare automatically moves the legacy
`user_data/data/` files into `data/crypto-majors/` without redownloading them.

## Run a bounded study

```bash
uv run run.py --profile crypto-majors
uv run run.py --profile us-equities
```

A strategy may declare:

```python
asset_classes = ["equity"]
# Or, for a narrower contract:
asset_profiles = ["us-equities"]
```

If neither is present, the strategy is treated as profile-agnostic. An
explicitly incompatible strategy produces a `SKIPPED` result block.

Every normal result block includes:

```text
asset_profile
asset_class
harness_version
timerange
commit
basket
metrics and per-pair metrics
```

## Session-market behavior

The session adapter is intentionally smaller than a Broker integration:

1. It constructs static market metadata and never contacts the venue.
2. It disables missing-candle forward fill so nights and weekends remain gaps.
3. It loads extra wall-clock history, then retains exactly the requested
   number of real warmup bars so indicators begin at the requested date.
4. A stop crossed by the opening gap fills at the bar open, not the stale stop.
5. Freqtrade's trade-based risk metrics are rescaled from its fixed 365-day
   clock to observed sessions and the profile annualization value (252 for
   `us-equities`). Buy-and-hold uses the same annualization value.

The fill model is still OHLCV bar simulation. This contract does not claim L2
precision, live order routing, exchange-calendar holiday validation, corporate
action adjustment, futures rolls, or margin accounting.

## Framework ownership and release

`autoquant/`, `harness.json`, `prepare.py`, `run.py`, `config.json`, dependency
pins, and tests belong to the Auto-Quant source repository. Study agents own
strategy files and gitignored results/data state; they do not patch the
Harness. Framework work is developed and tested here, committed normally,
tagged, and later consumed by OpenAlice by commit/tag. It is not recovered
from a disposable Workspace.

Fast validation:

```bash
uv run python -m unittest discover -s tests -v
uv run prepare.py --list-profiles
uv run run.py --list-profiles
```

These checks do not launch the autonomous loop or a multi-year backtest.
