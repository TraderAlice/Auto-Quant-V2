# RL policy evidence explorer

Status: V1 implemented.

Related: [[docs/design/rl-factor-policy-lab]],
[[docs/design/portfolio-decision-explorer]],
[[docs/design/request-bound-portfolio-mandates]],
[[docs/design/session-decision-matrix]], and
[[docs/design/studio-observation-surface]].

## Purpose

The explorer answers one narrow question:

> Did the governed adaptive factor-mixture policy add stable validation value
> beyond declared simple baselines, and what training and implementation
> evidence explains that result?

It is a verified projection of one immutable successful Run. It is not an RL
trainer, a policy selector, a backtest implementation, or a trading surface.

## Authority boundary

The fixed Judge remains the sole authority for states, actions, rewards,
portfolio accounting, folds, seeds, baselines, and the validation objective.
The exact Portfolio Mandate is also fixed Judge/Study authority.
The explorer may:

- verify artifact identity and reconcile redundant evidence;
- compute deterministic summaries from already-authoritative rows;
- sample long timestamp paths with documented fixed rules;
- format the same Core read model for CLI and Studio.

It may not:

- drop or select seeds;
- substitute a baseline;
- train or evaluate a model;
- use test evidence for promotion;
- infer causal state explanations absent from artifacts;
- publish live positions or orders.

## Required evidence

A successful governed RL Run declares exactly one of each:

- `rl-report`: complete metrics and semantics;
- `policy-models`: feature names, fixed configuration, ridge parameters, and
  learned Q weights;
- `training-history`: every fixed episode for every fold and seed;
- `policy-actions`: timestamped validation/test actions, rewards, returns,
  turnover, and cost.

Every file must be present in the immutable Run manifest, remain size-bounded,
and match the Run input hash. Report metrics and dataset identity must exactly
match `RunResult`.

## Reconciliation

The read layer verifies:

1. configured folds, seeds, actions, features, episodes, and model dimensions;
2. one succeeded or failed trial for every declared fold/seed pair;
3. exact training episode sequence, epsilon schedule, finite rewards, and
   action-count totals equal to training observations;
4. exact validation/test row coverage for every successful trial;
5. action frequencies, cumulative/mean reward, turnover, and cost reconcile
   with trial metrics;
6. fold aggregate and RL-minus-validation-selected-baseline values reconcile
   with their constituent trials;
7. no duplicate timestamps or undeclared actions/splits occur.
8. the Run/report/config mandate identities match, the dependency hash is
   fixed, and every action sleeve passed the same constraint audit.

The first inconsistent field fails the projection with a structured validation
issue. Studio then shows a Project diagnostic instead of partial RL evidence.

## Bounded read model

`aq run rl` returns `autoquant-rl-policy-diagnostics` with:

- immutable Run, dataset, Harness, artifact, and protocol identity;
- fixed Portfolio Mandate direction, construction, authorized/context-only
  assets, cash/cap, and benchmark;
- a headline validation/test audit summary;
- one row per fold/seed trial;
- one row per declared baseline and fold;
- exact bounded training histories;
- fold/seed/split action allocation and implementation summaries;
- a deterministic bounded action path;
- warnings about test reuse and lack of trading authority.

The action path preserves first/last, split boundaries, action transitions,
and reward/cost extremes before evenly filling remaining slots. Sampling never
changes metrics.

## Studio interaction

The Studio explorer has three views:

- **Performance** — fold/seed RL Sharpe versus each fold's
  validation-selected baseline, with validation and test kept separate;
- **Training** — per-fold/seed episode reward and action allocation, exposing
  dispersion rather than selecting a lucky seed;
- **Actions** — fixed-sleeve allocation, transitions, reward, turnover, and
  cost from the immutable action ledger.

The summary leads with validation advantage versus the best baseline, then
minimum and dispersion across trials. Raw high Sharpe never visually overrides
negative value-add evidence.
The mandate strip is shared with Portfolio so humans can verify that adaptive
actions answer the same requested position question.

## Invariants

1. One Core read model serves CLI and Studio.
2. All declared folds and seeds remain visible.
3. Validation is selection; test is visible audit only.
4. Baseline choice comes from the fixed Judge and is never recomputed by UI.
5. Training history is descriptive evidence, not a new promotion metric.
6. Action names describe fixed factor-mixture sleeves, not executable orders.
7. Corrupt evidence produces diagnostics, never a best-effort chart.
8. Studio remains read-only and has no trading authority.
9. RL cannot use a different tradable universe or permitted direction from the
   Portfolio lane.
