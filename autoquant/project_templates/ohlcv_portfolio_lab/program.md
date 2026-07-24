# OHLCV Portfolio Construction Study

## Question

Can one causal per-asset factor become a stable cross-asset portfolio after
fixed sizing, position caps, drift-aware turnover, costs, and chronological
out-of-sample evaluation?

## Editable closure

Edit only `factors/**`. Keep the API:

```python
def compute_factor(frame: pandas.DataFrame) -> pandas.Series:
    ...
```

The factor receives one asset's chronological OHLCV rows. It must return one
numeric aligned Series and may use only the current and prior rows.

## Fixed portfolio contract

- factor rank becomes a `short / flat / long` percentile state;
- enter long/short at `0.75 / 0.25`, exit at `0.55 / 0.45`, and reverse at the
  opposite entry threshold;
- size conviction by inverse trailing 20-bar volatility;
- gross 1.0, long +0.5, short -0.5;
- maximum absolute target weight 0.30;
- retain the drifted book below 0.05 one-way turnover;
- cost every bought/sold dollar at 10 basis points;
- signal at close `t` earns only close `t` to close `t+1`;
- dataset-fixed purged 60/20/20 train/validation/test;
- primary score is validation net Sharpe only;
- mandatory 0/10/25bps, one-extra-bar-delay, and no-hysteresis comparisons.

The Judge owns every rule above. Do not edit `judges/**`, the Study, program,
or dataset while comparing candidates.

Test metrics are visible diagnostic evidence and never enter KEEP/REVERT.
Changing a candidate after inspecting them consumes their holdout value; use a
new external period or dataset before a production-grade claim.

## Evidence discipline

Inspect factor, signal-state, portfolio/risk, implementation, attribution,
constraint, and robustness layers. Read `portfolio-decisions.csv` when a
conclusion depends on one asset or date. A higher primary score is not enough
when coverage collapses, hysteresis adds no value, concentration rises,
turnover/costs dominate, delayed performance reverses, attribution fails to
reconcile, or one asset explains the result.

This is a synthetic bar-target-weight simulation, not an L2 fill model, order
instruction, or live-trading recommendation.
