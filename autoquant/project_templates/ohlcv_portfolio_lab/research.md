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
transaction costs, benchmark, causal portfolio covariance, a one-sided
annualized volatility ceiling, dataset-fixed purged splits, attribution,
stress tests, and the verdict metric. Risk governance happens after raw
signal allocation and before drift-aware execution; it can only move exposure
into cash, never lever a weak signal up. The fixed
`strategies/portfolio-mandate.json` is not candidate-editable.

The Judge also measures the exact executed trade path against a causal
20-observation trailing average of `close × volume`. It reports 1% and 5%
participation capacity, missing-history trade dates, reference-$1m breaches,
and binding assets. This is a contextual OHLCV envelope, not an impact or fill
model, and it cannot affect KEEP/REVERT.

Successful Runs include proposed and executed weights plus a long-form
per-asset decision ledger. Use it to trace factor → intent → raw target →
covariance forecast/scale → governed target → trade → return/risk/cost
contribution. Inspect activation rate, average active scale, maximum
pre/post-governor forecast, and the diagnostic ungoverned comparison before
claiming that a factor survives implementation. Inspect validation capacity
coverage, the conservative 1% minimum/p10/median, and binding assets before
claiming the path can scale. AutoQuant produces
target-weight research only; it has no Broker or trading-account authority.
