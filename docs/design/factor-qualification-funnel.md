# Factor qualification funnel

Status: implemented.

Related: [[docs/design/factor-diagnostics]],
[[docs/design/factor-evidence-explorer]],
[[docs/design/cross-study-factor-dependencies]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/research-program-orchestration]].

## Purpose

AutoQuant must not send every syntactically valid candidate factor directly
into portfolio construction or RL. A quant researcher first needs to know
whether the signal predicts, whether it is merely a known OHLCV style in
disguise, and whether adding it to a simple style baseline contributes
incremental information.

The qualification funnel is research evidence, not an automatic promotion or
trading gate:

```text
candidate source
→ raw cross-sectional IC
→ train-selected dominant known style
→ contemporaneous style-neutral residual IC
→ equal-blend uplift versus the known style
→ chronological stability
→ Portfolio monetization
→ optional governed-RL consumption
```

## Fixed comparison contract

The Factor Judge owns four fixed OHLCV style proxies:

- 20-bar momentum;
- 5-bar reversal;
- 20-bar realized volatility;
- 20-bar relative volume.

The dominant comparison style is selected once using only the training split:
maximum absolute mean daily cross-sectional rank overlap with the candidate.
Validation and test never choose the comparison.

At every timestamp, the Judge ranks the candidate and selected style across the
current asset universe and centers both rank vectors. It computes:

- the candidate signal;
- the selected style by itself;
- the candidate residual after a same-timestamp one-style OLS projection;
- an equal-weight rank blend of candidate and selected style.

This neutralization is causal because all inputs are observable at the signal
close. It is cross-sectional and contemporaneous; it is not a fitted
forward-return model and never sees the target.

## Evidence

For every Horizon Mandate target and train / validation / visible-test split,
the immutable Run records daily rank IC and descriptive/HAC summaries for all
four signals. It also records:

- train-only comparison-style candidates and the chosen style;
- validation residual-IC retention versus raw candidate IC;
- validation blend uplift versus style and versus candidate;
- two chronological residual-IC folds per split;
- exact method, timing, split roles, and authority.

Core reconstructs every mean and observation count from the immutable daily
qualification artifact before exposing a diagnosis.

## Diagnosis

Only validation can set the next research focus. The first demonstrated failure
is classified as:

1. `raw-predictive-edge-absent`;
2. `raw-statistical-evidence-weak`;
3. `style-neutral-edge-absent`;
4. `style-neutral-statistical-evidence-weak`;
5. `blend-uplift-absent`;
6. `residual-temporal-instability`;
7. `factor-qualification-positive`.

Positive raw and residual IC require a fixed positive HAC t-statistic of at
least `1.96` before the funnel advances. This is a conventional diagnostic
threshold, not a p-hacking surface or promotion rule. Project-family
selection-adjusted significance remains separately required after repeated
candidate search. Effect size, turnover, decay, quantile shape, and later
Portfolio monetization remain visible evidence for the researcher.

Test appears beside validation as visible audit only. It never changes the
stage, comparison style, Session verdict, Report recommendation, or RL policy.

## Reference evidence

The bounded Yahoo reference used actual provider-adjusted daily OHLCV for AAPL,
MSFT, NVDA, QQQ, and SPY over 1,254 sessions from 2021-07-23 through
2026-07-22. The default candidate produced:

- validation raw rank IC `+0.0028`, HAC t-statistic `+0.0782`;
- train-selected dominant style `reversal_5`;
- validation residual rank IC `+0.0495`, HAC t-statistic `+1.5031`;
- validation blend rank IC `+0.0200`; and
- visible-test raw/residual rank IC `-0.0768` / `-0.0682`.

The correct diagnosis is `raw-statistical-evidence-weak`, even though the raw
IC sign is positive. This reference caught and removed an earlier UI shortcut
that treated positive sign alone as sufficient evidence.

A separate deterministic relative-volume candidate provides the complementary
redundancy case: it improves the fixed Factor objective and receives KEEP, but
the train-selected comparison is `relative_volume_20` and style-neutral
residual IC is zero. The funnel therefore diagnoses
`style-neutral-edge-absent` without mutating the existing Session verdict.

## OpenAlice and RL boundary

An OpenAlice request gives the Project its assets, direction, horizon, and
decision context. Qualification answers whether a proposed model contains
distinct historical information worth carrying into the next research lane.
It does not answer whether OpenAlice should buy an asset.

Governed RL may consume the content-locked candidate source only as a research
dependency. The Factor qualification hash and diagnosis belong in immutable
Report/Dossier evidence so an operator can distinguish:

- weak factor research;
- useful factor evidence that fails Portfolio monetization;
- useful mechanical evidence that RL fails to improve; and
- genuine incremental adaptive value.

## Invariants

1. The dominant style is selected on train only.
2. Neutralization uses only same-timestamp factor/style observations.
3. Forward returns never enter style selection or neutralization.
4. Validation alone determines the research diagnosis.
5. Test is visible audit only.
6. Raw, residual, style, and blend IC remain separate; no composite score hides
   a failed layer.
7. Legacy Runs without qualification evidence remain immutable and readable.
8. Qualification grants no KEEP/REVERT, RL, Broker, order, account, capital, or
   trading authority.
