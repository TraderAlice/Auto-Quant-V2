# Factor evidence explorer

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/CLI]], [[docs/STUDIO]],
[[docs/design/factor-diagnostics]],
[[docs/design/factor-qualification-funnel]],
[[docs/design/research-selection-integrity]],
[[docs/design/session-decision-matrix]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the read-only projection from one immutable fixed Factor Lab
Run into a bounded professional tear sheet for Agents and Studio. It defines
artifact verification, reconciliation, sampling, split roles, response schema,
CLI discovery, and browser presentation.

It does not own factor computation, targets, Judge statistics, candidate
selection, Experiment verdicts, portfolio sizing, report authorship, or trading
authority.

## Authority flow

```text
verified successful Factor Run
→ verified factor-report + daily IC + quantile artifacts
→ full-history reconciliation with immutable Run metrics
→ bounded deterministic IC and quantile paths
→ fixed horizon/stability/style summaries
→ aq run factor / Studio Factor evidence explorer
```

The Run manifest hash-verifies every byte before this projection opens an
artifact. Core then checks the fixed artifact set, schema, row bounds,
chronology, split membership, horizon identity, and aggregate reconciliation.
Sampling happens last.

## Public contract

```text
aq run factor <project-or-workspace> --run <id>
  [--points 40..400] [--project <id>] [--json]
```

The result kind is `autoquant-factor-diagnostics`. The operation is read-only,
has no arbitrary file route, and returns no candidate source.

## Evidence model

### Identity and protocol

The projection preserves Run, Study, objective, dataset, Harness, artifact
hashes, fixed horizons, target semantics, style dictionary, and split roles:

- train — construction/training evidence;
- validation — the only selection split;
- test — visible audit evidence that never enters selection.

### Summary

Decision-useful summary fields include:

- validation and test-audit rank/Pearson IC, ICIR, hit rate, HAC t/p, and
  observations;
- weakest validation chronological fold;
- maximum absolute validation style correlation;
- mean factor coverage and mean cross-sectional rank turnover.

Positive values are evidence, not automatic approval. The browser must not
colour significance, stability, or monotonicity as “passed” without a fixed
threshold.

### IC path and horizon profile

The complete daily artifact is checked for strict dates, declared split,
causal regime, and nullable finite rank/Pearson IC at fixed 1/5/10-bar
horizons. For every split/horizon, Core recomputes observation counts and means
and reconciles them to Run metrics.

The response then samples one shared timestamp index. It preserves first/last,
split boundaries, regime transitions, and the maximum absolute one-bar IC.
Every point retains split, role, regime, and all six fixed IC values so chart
tabs never change the evidence population.

### Quantiles

The complete quantile artifact must contain one unique
`timestamp × split × horizon` row with finite low/middle/high and
high-minus-low returns. Core recomputes mean group returns, spread,
monotonicity, and observation count for every split/horizon and reconciles
them to the immutable metric tree.

Quantile path points use the same sampled date anchors where available.
Studio may switch horizon and split, but it cannot re-bin assets.

### Stability and style overlap

Core projects the fixed summary dictionaries as normalized rows:

- two chronological folds per split;
- causal `up/down × calm/stressed` regimes;
- per-asset time-series rank correlation;
- momentum, reversal, realized-volatility, and relative-volume style overlap.

Rows retain observations, sufficiency flags where declared, and null values.
Sparse evidence must remain visible rather than being pooled away.

### Factor qualification

New Runs add a train-selected one-style neutralization artifact. Core
reconstructs candidate, selected-style, style-neutral residual, and equal-rank
blend IC for every fixed split and horizon. Validation alone diagnoses raw
edge, conventional HAC support, distinct residual edge, blend uplift, and
residual chronological breadth. Test is a separate visible audit. Historical
Runs project qualification as unavailable rather than inventing evidence.

## HCI

The Factor Explorer answers four questions in one reading order:

1. Is validation evidence economically and statistically non-trivial?
2. Does it persist through time and across the fixed forward horizons?
3. Is the high-minus-low behavior monotonic rather than one lucky aggregate?
4. Is the signal stable across assets/regimes/folds and distinct from fixed
   OHLCV styles?

Studio uses a compact summary followed by:

- IC path / quantile-path tabs;
- 1 / 5 / 10-bar horizon controls;
- validation / test-audit controls;
- horizon profile and fold/regime/asset/style stability tables.

Test controls and cells carry an explicit audit label. The page remains
read-only and copy-only for CLI commands.

## Bounds

- artifact size: 32 MiB each;
- daily rows: 100,000;
- quantile rows: 300,000;
- universe: 256 assets;
- response points: 40–400;
- fixed horizons: 1, 5, and 10 bars.

Full artifacts are reconciled before these response bounds apply.

## Invariants

1. No artifact is read before immutable Run verification.
2. Exactly one fixed Factor artifact set is accepted.
3. Full daily/quantile evidence reconciles before deterministic sampling.
4. Validation one-bar mean rank IC remains the only selection objective.
5. Test, longer horizon, quantile, stability, and style evidence are
   diagnostic only.
6. Missing/sparse values remain null with observations; zero is never
   substituted.
7. CLI and Studio consume the same Core object.
8. The projection has no Project mutation, Broker, order, or account authority.
9. Qualification style selection uses train overlap only; validation/test
   cannot change it or authorize Factor promotion or RL admission.

## Change checklist

- Add an evidence field only with fixed timing, split, unit, and selection
  semantics.
- Preserve full-file reconciliation and response bounds.
- Update schema, capability, CLI, Studio, docs, tests, and package assets
  together.
- Exercise negative/tampered evidence and a real-data Factor Run.

## Known limits

- V1 supports the fixed cross-sectional OHLCV Factor Lab only.
- HAC and style evidence are Judge-authored summaries; Core reconciles the
  underlying mean paths but does not reimplement every statistical estimator.
- The explorer does not estimate capacity or portfolio performance.
- The fixed single-Run HAC threshold is diagnostic only; Project-family
  selection-adjusted significance remains a separate Session-level surface.
- Cross-Run comparison remains owned by the Session Decision Matrix.
