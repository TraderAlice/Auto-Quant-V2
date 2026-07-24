# Add a professional factor-diagnostics protocol

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/factor-diagnostics]],
  [[docs/design/ohlcv-factor-lab]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

The reference Factor Lab produces a fixed, causal, purge-aware factor tear
sheet that lets a quantitative researcher or Agent judge predictive decay,
quantile monotonicity, statistical strength, style overlap, and stability
across assets, chronological folds, and causal market regimes before sending a
signal into portfolio construction or RL.

## Context

The current Factor Lab proves causality and reports one-bar train/validation/test
rank IC, ICIR, coverage, and rank turnover. That is enough to test the governed
research loop, but not enough to explain why a candidate works or whether its
aggregate score hides concentration in one horizon, asset, period, or familiar
OHLCV style. Forward returns at the edge of a chronological split also need an
explicit purge so their target bars never cross into the next split.

## Scope

### In scope

- Fixed 1/5/10-bar forward-return diagnostics with split-boundary purging.
- Rank/Pearson IC significance, factor decay, quantile returns/monotonicity, causal
  regime stability, chronological fold stability, per-asset stability, and
  correlation to fixed OHLCV style proxies.
- Immutable JSON and CSV tear-sheet evidence.
- Full machine-readable Run output plus concise Studio factor evidence.
- Deterministic synthetic regressions for timing, isolation, known signal
  behavior, artifacts, Studio, documentation, and packaging.

### Out of scope

- Treating a synthetic fixture as market alpha.
- Candidate-selected horizons, regimes, quantiles, significance methods, or
  acceptance rules.
- A general factor registry, optimizer, ML feature store, or live execution.
- Statistical claims that ignore visible-test reuse or repeated trials.

## Acceptance

- [x] Every forward target remains inside its declared chronological split;
      fixed split dates do not depend on candidate coverage or warm-up length.
- [x] The validation-only objective remains stable while 1/5/10-bar IC and
      HAC significance, decay, quantiles, fixed-style correlations, per-asset,
      fold, and causal-regime evidence are published.
- [x] Quantile evidence reports low/middle/high returns, high-minus-low spread,
      and monotonicity without candidate-controlled bins.
- [x] Regime labels use only information known at the signal close and preserve
      observation counts instead of hiding sparse cells.
- [x] Exact daily IC/regime and quantile-return CSVs are immutable Run
      artifacts alongside the structured tear sheet.
- [x] CLI Run JSON and Studio project the same verified evidence; Reports
      inherit it through their existing frozen Run projection.
- [x] Bounded tests prove purging, test isolation, known-signal diagnostics,
      generic failure behavior, artifact contents, and Studio parity.
- [x] Canonical docs, wheel contents, full tests, links, and frontend syntax
      agree.

## Work

- [x] Define fixed diagnostic timing, statistics, regimes, styles, and artifact
      schemas.
- [x] Implement the self-contained diagnostic Core and integrate the Factor
      Judge/template.
- [x] Project concise diagnostics through Studio while retaining full CLI
      evidence.
- [x] Complete regression, package, documentation, and completion audits.

## Findings and decisions

- 2026-07-24 — The greatest remaining evidence gap is before portfolio
  construction: one aggregate one-bar IC cannot distinguish decay, familiar
  style repackaging, regime dependence, or single-asset concentration.
- 2026-07-24 — Split boundaries are fixed from the dataset timeline, not
  candidate-valid rows. Each horizon purges signal rows whose target bar would
  cross a boundary.
- 2026-07-24 — V1 uses deterministic HAC inference and descriptive slices. It
  does not convert them into a second hidden promotion rule.
- 2026-07-24 — A true isolated-wheel smoke exposed cold pandas/NumPy startup
  exceeding the old 10-second Judge timeout and varying from roughly 16 to 38
  seconds across clean environments. The reference timeout is 60 seconds;
  warm Runs remain fast and execution stays hard-bounded with cold-start
  margin.

## Verification

- `uv run python -m unittest discover -s tests` — 89 tests passed.
- `uv run python scripts/check_doc_links.py` — 210 links resolved.
- `uv run python -m compileall -q autoquant tests` — passed.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `git diff --check` — passed.
- `uv build` — source distribution and wheel built.
- Wheel inventory contains the fixed diagnostic Core, Factor Judge/program,
  template construction code, and Studio JavaScript.
- A fresh-path isolated wheel install created and executed the reference Factor
  Project successfully, using the installed package rather than repository
  source.
- The known relative-volume signal produced validation one-bar rank IC
  `0.8041`, HAC t-statistic `28.32`, monotonicity `1.0`, high-minus-low spread
  `0.0187`, positive validation folds/assets, and exact style identity.

## Progress log

- 2026-07-24 — Activated after the full-goal audit compared implemented
  factor evidence with the canonical quantitative evidence stack.
- 2026-07-24 — Completed after timing, isolation, sparse-cell, structured
  failure, artifact-reconciliation, Studio, full-suite, and installed-wheel
  audits passed.

## Completion

The Factor Lab now emits a fixed professional tear sheet without expanding
candidate authority: purge-aware 1/5/10-bar rank/Pearson IC, deterministic HAC
inference, tertile behavior, fixed-style overlap, and asset/fold/causal-regime
stability, plus exact daily artifacts and a concise Studio projection.

The next distinct problem—mechanical signal state, target sizing, risk budgets,
and contribution attribution—is indexed as
[[plans/mechanical-signal-policy-and-attribution]].
