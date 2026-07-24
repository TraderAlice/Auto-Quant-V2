# OHLCV Portfolio Lab

## Purpose

Research causal OHLCV factors and test whether their signal survives a fixed,
mechanical translation into constrained cross-asset target weights.

## Workflow

```bash
aq study inspect . --study ohlcv-portfolio-quality --json
aq run execute . --study ohlcv-portfolio-quality --json
aq session start . --study ohlcv-portfolio-quality --json
```

Work only inside the returned Session worktree and edit `factors/**`. State one
falsifiable factor hypothesis, evaluate it, and inspect all metric layers and
artifacts before accepting a KEEP.

The fixed Judge owns timing, percentile entry/hold/exit state,
inverse-volatility conviction sizing, request-bound tradable/context assets,
direction, cash, long/short budgets, caps, drift, no-trade behavior,
transaction costs, benchmark, dataset-fixed purged splits, attribution,
stress tests, and the verdict metric. The fixed
`strategies/portfolio-mandate.json` is not candidate-editable.

Successful Runs include proposed and executed weights plus a long-form
per-asset decision ledger. Use it to trace factor → intent → target → trade →
return/risk/cost contribution. AutoQuant produces target-weight research only;
it has no Broker or trading-account authority.
