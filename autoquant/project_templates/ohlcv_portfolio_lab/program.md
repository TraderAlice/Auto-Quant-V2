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

- centered cross-sectional rank divided by trailing 20-bar volatility;
- gross 1.0, long +0.5, short -0.5;
- maximum absolute target weight 0.30;
- retain the drifted book below 0.05 one-way turnover;
- cost every bought/sold dollar at 10 basis points;
- signal at close `t` earns only close `t` to close `t+1`;
- chronological 60/20/20 train/validation/test;
- primary score is the lower validation/test net Sharpe;
- mandatory 0/10/25bps and one-extra-bar-delay stresses.

The Judge owns every rule above. Do not edit `judges/**`, the Study, program,
or dataset while comparing candidates.

## Evidence discipline

Inspect factor, portfolio/risk, implementation, constraint, and robustness
layers. A higher primary score is not enough when coverage collapses,
concentration rises, turnover/costs dominate, delayed performance reverses, or
one asset explains the result.

This is a synthetic bar-target-weight simulation, not an L2 fill model, order
instruction, or live-trading recommendation.
