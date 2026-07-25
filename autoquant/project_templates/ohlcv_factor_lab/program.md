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
   monotonicity/spread, train-selected dominant style, style-neutral residual
   IC, equal-blend uplift, residual fold stability, asset/regime stability,
   coverage, turnover, errors, verdict, Project-family trial count, and
   family-wise adjusted HAC significance.
6. KEEP only when the fixed objective improves; otherwise accept restoration
   and form a different hypothesis.

The fixed objective is validation mean IC only. Test IC is visible diagnostic
evidence and never enters KEEP/REVERT. Changing a candidate after inspecting
test evidence consumes its holdout value; obtain a new external period or
dataset before a production-grade claim.

Starting a new Session does not create a fresh statistical search. Core counts
unique editable source hashes across every Run with the same fixed Study,
Judge, data, dependencies, and objective. Treat the Bonferroni-HAC result as a
selection-risk diagnostic, not permission to hide failed attempts or override
the immutable verdict.

The Judge fixes dataset-derived split dates and purges the last 1/5/10 signal
rows whose targets would cross each boundary. Treat sparse regimes, one weak
fold, one dominant asset, fast decay, or near-perfect overlap with a familiar
OHLCV style as findings to explain—not fields to hide or alternate scores to
optimize opportunistically.

The dominant comparison style is chosen on train overlap only. Validation
qualification asks whether raw and style-neutral IC are positive with fixed
HAC t at least 1.96, whether an equal rank blend improves the selected style,
and whether both residual folds remain positive. This prioritizes the next
research lane; it does not change KEEP/REVERT, replace Project-family
selection adjustment, or automatically admit the source into Portfolio or RL.

Do not modify the Study, Judge, program, dataset, or AutoQuant Core to improve a
candidate. Do not treat this synthetic benchmark as a real-market alpha claim.
