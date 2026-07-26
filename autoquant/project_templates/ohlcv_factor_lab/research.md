# OHLCV Factor Lab

This Project is a self-contained construction site for causal, vectorized
factor research on local OHLCV data. The checked-in construction recipe
generates a small deterministic synthetic fixture; it is a Harness benchmark,
not evidence about real markets.

## Workbench contract

- The Agent edits only `factors/candidate.py`.
- The fixed Study is `ohlcv-factor-quality`.
- The fixed Judge reads the immutable Horizon Mandate and computes
  purge-aware primary/diagnostic forward-bar returns, chronological splits,
  HAC/decay/tertile/style/stability diagnostics, a train-selected
  style-neutral qualification funnel, optional candidate-declared component
  quality/redundancy/fixed-blend ablation, and the causality audit.
- Dataset bytes under `data/ohlcv/**` participate in Study and Run identity.
- Every candidate is evaluated through `aq experiment evaluate`; never call the
  Judge directly or optimize against the test target outside that contract.
- Quantitative evidence describes historical behavior. It is not an order,
  Broker integration, or live-trading instruction.

Successful declaring Runs include a complete JSON tear sheet plus exact daily
IC/regime, quantile-return, candidate/style/residual/blend qualification, and
candidate-declared component artifacts.
Use `aq run factor --run <id> --json` and Studio for the verified summary; read
artifacts when a conclusion depends on a specific date or slice.

## First commands

```bash
aq study inspect . --study ohlcv-factor-quality --json
aq run execute . --study ohlcv-factor-quality --json
aq session start . --study ohlcv-factor-quality --json
```
