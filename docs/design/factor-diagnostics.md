# Professional factor diagnostics

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]],
[[docs/design/ohlcv-factor-lab]],
[[docs/design/factor-component-attribution]],
[[docs/design/factor-evidence-explorer]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]],
[[docs/design/research-selection-integrity]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the fixed research diagnostics between a candidate's causal
factor Series and later portfolio/RL work. Candidate code remains a plain
per-asset pandas function. The Judge owns every target, horizon, split, bin,
regime, style proxy, statistic, artifact, and acceptance rule.

The protocol is a research tear sheet, not a trading simulator. It describes
predictive evidence before sizing and execution assumptions are applied.
When the candidate explicitly declares components, the separate governed
contract in [[docs/design/factor-component-attribution]] adds component
diagnostics without changing this document's final-factor objective.

## Timing and purged splits

At close `t`, a candidate may use OHLCV through `t`. Horizon `h` evaluates:

```text
factor(asset, t)
against
close(asset, t + h) / close(asset, t) - 1
```

The dataset timestamp index fixes chronological 60/20/20 boundaries before the
candidate runs. Candidate warm-up or missingness cannot move those boundaries.
For every split and horizon, the Judge drops the final `h` signal rows of the
split so the target bar remains inside that split. This is an explicit purge,
not a random split or an inferred embargo.

The promotion objective remains validation one-bar mean rank IC. Longer
horizons and all test metrics are diagnostics only.

## Fixed evidence

### Horizon quality and inference

For horizons 1, 5, and 10 bars, each split reports daily cross-sectional
Spearman rank IC and Pearson IC:

- mean, population dispersion, ICIR, hit rate, and observations;
- Newey-West/HAC t-statistic with fixed lag `min(5, n - 1)`;
- a two-sided normal-approximation p-value, labeled as an approximation.

Overlapping multi-bar returns make naive independent-sample t-statistics
misleading. HAC does not remove all financial-model risk, but it makes the
autocorrelation treatment explicit and deterministic.

### Quantile behavior

Each date sorts valid assets by factor and partitions them into fixed
low/middle/high groups. Each split/horizon reports:

- mean return for each group;
- high-minus-low mean spread;
- rank correlation between group order and group mean return as monotonicity;
- valid observation count.

With the small reference universe, tertiles are honest; pretending to have
stable deciles or quintiles would create mostly singleton bins.

### Stability

The one-bar IC is sliced without changing the objective:

- two fixed chronological folds inside each train/validation/test split;
- causal `up/down × calm/stressed` market regimes;
- per-asset time-series rank correlation between factor and forward return.

Regime direction uses trailing equal-weight market return through `t`.
Regime volatility uses trailing market volatility through `t` compared with a
lagged rolling median threshold. No future sample statistic labels a past row.
Sparse cells remain present with observation counts and null statistics.
Every slice also carries its fixed minimum-observation threshold and an
explicit `sufficient` flag.

### Fixed style overlap

The Judge compares cross-sectional factor ranks with four causal OHLCV style
proxies:

- 20-bar momentum;
- 5-bar reversal;
- 20-bar realized volatility;
- 20-bar relative volume.

Mean rank correlation by split describes overlap. It does not prove economic
equivalence, neutralize the candidate, or reject a signal automatically.

## Artifacts

Every successful reference Run publishes:

- `factor-report.json`: semantics, split protocol, aggregate diagnostics,
  causality cuts, and coverage;
- `daily-factor-evidence.csv`: timestamp, fixed split, causal regime, and
  purge-aware 1/5/10-bar daily rank/Pearson IC;
- `factor-quantiles.csv`: timestamp, split, horizon, low/middle/high return,
  and high-minus-low spread.
- `factor-qualification.csv`: timestamp, split, train-selected dominant style,
  and candidate/style/style-neutral/equal-blend daily rank IC for fixed
  1/5/10-bar horizons.
- optional `factor-components.json`: bounded candidate-declared component
  quality, final-factor association, pairwise redundancy, nearest-peer
  residual, and fixed diagnostic-blend leave-one-out evidence.

The Run metric object contains the complete machine-readable summary. The
bounded Core projection in [[docs/design/factor-evidence-explorer]] verifies
and reconciles the fixed artifacts before CLI and Studio expose their path,
stability, and optional component evidence. Research Reports retain the full
verified Run as authority.

The reference Study keeps a 60-second hard Judge timeout. Normal warm source
runs are much faster; the allowance covers cold pandas/NumPy import and
bytecode startup from an installed wheel without turning routine research into
an unbounded backtest.

## Invariants

1. Candidate code controls only factor values.
2. Split dates are dataset-fixed and candidate-independent.
3. A target bar never crosses its split boundary.
4. Validation one-bar mean rank IC is the only promotion objective.
5. Test, horizon, slice, style, and significance metrics never become hidden
   acceptance rules.
6. Regime labels are causal at the signal close.
7. Sparse slices are disclosed, not silently omitted or pooled.
8. Daily artifacts reconcile to aggregate metrics.
9. Synthetic evidence is a Harness regression, not a market claim.
10. Optional component diagnostics never enter the final-factor promotion
    score or dynamically alter Portfolio/RL authority.

## Known limits

- HAC p-values are asymptotic normal approximations, not exact finite-sample
  inference or multiple-testing corrections.
- OHLCV style proxies are intentionally small and do not represent a complete
  commercial risk model.
- Per-asset time-series correlation answers a different question from
  cross-sectional IC and must not be averaged into the promotion score.
- Causal regime labels are descriptive conditioning variables, not a guarantee
  that the same states recur in live markets.
- Portfolio capacity, constraints, costs, and execution remain owned by the
  Portfolio Lab.
