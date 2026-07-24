# Mine a causal OHLCV factor

## Research question

Can one causal transformation of ordinary OHLCV history produce stable
cross-sectional next-bar rank information across the fixed universe and both
held-out chronological periods?

## Editable API

Edit only `factors/candidate.py` and preserve:

```python
def compute_factor(frame: pandas.DataFrame) -> pandas.Series:
    ...
```

The returned Series must align exactly with the input index. Missing warm-up
values are allowed. Future rows, centered windows, negative shifts, global
full-sample normalization, external data, and mutation of the input are not.

## Iteration protocol

1. Read the current candidate and immutable leader evidence.
2. State one falsifiable hypothesis about price or volume behavior.
3. Make one coherent code change inside the editable closure.
4. Run the bounded Experiment command supplied by the Session.
5. Inspect validation/test one-bar IC, HAC strength, 5/10-bar decay, tertile
   monotonicity/spread, style overlap, asset/fold/regime stability, coverage,
   turnover, errors, and verdict.
6. KEEP only when the fixed objective improves; otherwise accept restoration
   and form a different hypothesis.

The fixed objective is validation mean IC only. Test IC is visible diagnostic
evidence and never enters KEEP/REVERT. Changing a candidate after inspecting
test evidence consumes its holdout value; obtain a new external period or
dataset before a production-grade claim.

The Judge fixes dataset-derived split dates and purges the last 1/5/10 signal
rows whose targets would cross each boundary. Treat sparse regimes, one weak
fold, one dominant asset, fast decay, or near-perfect overlap with a familiar
OHLCV style as findings to explain—not fields to hide or alternate scores to
optimize opportunistically.

Do not modify the Study, Judge, program, dataset, or AutoQuant Core to improve a
candidate. Do not treat this synthetic benchmark as a real-market alpha claim.
