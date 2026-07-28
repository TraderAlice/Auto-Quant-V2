# OHLCV Factor Lab

## Research brief and clarification

Before downloading data, editing `factors/candidate.py`, or running an
evaluation, rewrite the incoming assignment in this file as a bounded English
research brief. Make the decision to support, question, motivation, universe,
horizon, evidence, material constraints, evaluation meaning, expected
deliverable, assumptions, open questions, and proposed route explicit.

Use researcher judgment for factor design and diagnostics, but do not invent
caller-owned intent. If an ambiguity could materially change the research,
record it here and ask the delegating Agent or user. Repeat until the question
is falsifiable and safe to bind into fixed Study authority. The caller may use
any language; English is the internal working language of the AutoQuant desk.

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
- A V4 intake may supply an observed-only ragged daily panel. Missing and
  pre-listing asset/timestamp rows remain absent; the Run and Factor Explorer
  expose input, finite-factor, and forward-target-pair availability.
- A `known-style-validation` intake seeds `factors/candidate.py` from the exact
  requested style before Study identity is created. Inspect it, but do not
  replace it with the generic exploratory baseline.
- Every candidate is evaluated through `aq experiment evaluate`; never call the
  Judge directly or optimize against the test target outside that contract.
- Quantitative evidence describes historical behavior. It is not an order,
  Broker integration, or live-trading instruction.

Successful declaring Runs include a complete JSON tear sheet plus exact daily
IC/regime, quantile-return, observed-input availability,
candidate/style/residual/blend qualification, and candidate-declared component
artifacts.
Use `aq run factor --run <id> --json` and Studio for the verified summary; read
artifacts when a conclusion depends on a specific date or slice.

## First commands

```bash
aq study inspect . --study ohlcv-factor-quality --json
aq run execute . --study ohlcv-factor-quality --json
aq session start . --study ohlcv-factor-quality --json
```
