# Build a governed RL factor-policy laboratory

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/quant-research-lifecycle]] and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

AutoQuant can test whether a bounded RL policy improves causal factor blending
or portfolio targets beyond simple fixed baselines under frozen rewards,
costs, walk-forward splits, multiple seeds, and locked evaluation authority.

## Context

RL is useful only when it is treated as a falsifiable research candidate rather
than an opaque order generator. Financial samples are small, non-stationary,
and unusually vulnerable to reward leakage and seed selection. The portfolio
laboratory must exist first so actions, costs, and constraints have one fixed
meaning.

## Scope

### In scope

- A fixed set of factor-mixture actions, causal regime/expert state, previous
  action/position state, and next-period costed portfolio rewards with an
  explicit risk penalty.
- Two expanding chronological folds, three fixed seeds, deterministic Q-learning
  budgets, and exact policy/config/training artifacts.
- Comparisons against equal-weight, fixed-factor, and simple linear policies.
- Cross-seed dispersion, cross-fold stability, turnover, cost, risk, and
  generalization evidence.

### Out of scope

- Autonomous live order placement.
- Letting candidate code choose its reward, test split, costs, seed count, or
  benchmark.
- A general-purpose distributed ML platform.

## Acceptance

- [x] The Judge owns state/action/reward semantics and rejects lookahead.
- [x] Every result includes simple baselines, all declared seeds and folds,
      dispersion, failure evidence, and exact model/config artifacts.
- [x] A deterministic tiny fixture proves the complete loop without installing
      a heavyweight platform or running a long training campaign.
- [x] Candidate code can change only a deterministic row-level causal state
      encoder; it cannot change actions, reward, costs, seeds, folds, budgets,
      training algorithm, or portfolio accounting.
- [x] Promotion uses only aggregate validation evidence; test-fold evidence is
      reported separately with an explicit repeated-inspection warning.
- [x] The self-contained Project runs through CLI, Session, Experiment,
      Campaign, and Studio and preserves the no-trading-authority boundary.
- [x] Tests prove state determinism, chronological reward timing, multi-seed
      reproducibility, baseline comparison, a known improvement, and candidate
      failure behavior.
- [x] Capabilities, canonical docs, wheel contents, full bounded tests, and
      documentation links agree.

## Work

- [x] Finalize after the portfolio laboratory contract is implemented.
- [x] Implement a minimal replaceable policy adapter and fixed evaluator.
- [x] Ship reference candidates, evidence, Studio projection, and tests.
- [x] Audit reproducibility and failure behavior.

## Findings and decisions

- 2026-07-24 — The first RL lane chooses factor mixtures or portfolio targets;
  it does not emulate a broker or own order execution.
- 2026-07-24 — V1 fixes four factor-mixture actions and one linear Q-learning
  algorithm. The Agent edits only a pure row-level state encoder, making factor
  representation research possible without giving candidate code evaluation
  authority.
- 2026-07-24 — The objective aggregates validation folds only. Test-fold
  metrics are visible audit evidence, not a promotion input; repeated
  inspection consumes their research value and requires a new external
  holdout before a production claim.

## Verification

- `git diff --check`
- `uv run python -m compileall -q autoquant tests/test_rl_factor_policy_lab.py`
- `node --check autoquant/studio_assets/studio.js`
- `uv run python scripts/check_doc_links.py` — 177 links.
- `uv run python -m unittest discover -s tests -v` — 81 tests in 72.593s.
- `uv build --wheel --out-dir <temporary-directory>` — wheel built and all
  six `ohlcv_rl_factor_lab` assets plus the shared portfolio Core were present.
- Deterministic smoke: weak global-preference encoder scored
  `8.111940` validation mean net Sharpe; adding the causal volume-regime state
  scored `33.508568` across the same six fold/seed trials.
- The improved RL policy still trailed the validation-selected contextual ridge
  baseline by `3.482239` Sharpe on average, proving the comparison layer does
  not equate RL improvement with RL value-add.
- Pure-state violations CRASH before training; delayed non-finite behavior
  publishes all six fold/seed errors and fails the complete Run.

## Progress log

- 2026-07-24 — Proposed as a portfolio-dependent follow-up.
- 2026-07-24 — Activated after commit `57eeb80` fixed causal portfolio
  construction and accounting.
- 2026-07-24 — Completed the causal encoder boundary, fixed policy environment,
  folds/seeds/baselines, immutable model/training/action artifacts, Studio
  evidence, and bounded verification.

## Completion

V1 is a small governed factor-mixture policy laboratory, not a general RL
platform. It proves adaptive representation research can use the same
portfolio evidence contract while remaining subordinate to simple baselines
and explicit holdout limitations. Continuous actions, deep models, larger
walk-forward studies, and new external holdouts remain separate work.
