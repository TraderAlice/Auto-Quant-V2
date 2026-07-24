# Compare one research Session as a professional decision matrix

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/session-decision-matrix]],
  [[docs/design/research-session-loop]],
  [[docs/design/research-selection-integrity]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

An Agent or human can compare one Session's verified baseline, candidates, and
current leader across the factor, portfolio, implementation, robustness,
mechanical-policy, and RL evidence that matters for the fixed Study—not only
the primary promotion metric—while preserving validation-only selection and
visible-test limitations.

## Context

Sessions currently expose an immutable KEEP/REVERT/CRASH chain and one primary
value. That proves linear promotion authority but hides the trade-offs a
working quantitative researcher must inspect: a higher validation Sharpe can
arrive with worse drawdown, turnover, cost stress, contribution concentration,
seed dispersion, or baseline advantage. Studio's bar trace and CLI's
Experiment summaries cannot answer which evidence layer improved or regressed.

The missing layer is a read-only comparison projection over existing verified
Runs. It must not silently replace the fixed objective with a new acceptance
rule or allow visible test evidence into dominance claims.

## Scope

### In scope

- A bounded verified Session comparison object shared by CLI and Studio.
- Fixed metric dictionaries for Factor, Portfolio, and governed RL Studies,
  with unit, preference, split, and selection-eligibility metadata.
- Baseline/candidate/leader identity, verdict, hypothesis, objective, metric
  values, and directional comparison with baseline.
- A descriptive validation-only non-dominated set for displayed successful
  trials plus explicit leader gains/regressions.
- A horizontally inspectable Studio decision matrix with audit-only test rows.

### Out of scope

- Changing KEEP/REVERT rules, multi-objective promotion, branching search,
  parameter sweeps, statistical multiple-testing correction, or live trading.
- Comparing unlike Studies, Sessions, Projects, datasets, or Harness locks.

## Acceptance

- [x] Core verifies Session authority, Experiment history, and every referenced
      Run before projecting a metric.
- [x] Trial output is bounded, always includes baseline/current leader when
      available, and discloses omitted history.
- [x] Metric descriptors make units, preference, split, contextual fields, and
      test exclusion machine-readable.
- [x] Non-dominance and leader trade-offs use validation/selection-eligible
      fields only and never change the fixed Experiment verdict.
- [x] `aq session compare --json` and its schema/capability descriptor are
      discoverable and deterministic.
- [x] Studio consumes the same Core object and presents baseline, candidates,
      leader, gains/regressions, and test-audit rows without browser-side
      evidence inference.
- [x] Bounded Portfolio and RL Sessions prove metric extraction, failed-trial
      handling, selection integrity, UI behavior, full regression, and wheel
      packaging.

## Work

- [x] Audit current Session, Portfolio, RL, Studio, and report boundaries.
- [x] Implement and test the shared comparison projection and schema.
- [x] Add CLI discovery and Studio decision matrix.
- [x] Complete deterministic Portfolio/RL, browser, regression, docs, and
      isolated-wheel evidence.

## Findings and decisions

- 2026-07-24 — Mechanical policy and RL portfolio accounting already share
  fixed causal target-weight mechanics. The missing product surface is
  comparison, not another execution engine.
- 2026-07-24 — V1 compares only Runs from one verified Session. Dataset,
  Study, objective, Judge, and Harness identity therefore remain fixed.
- 2026-07-24 — The descriptive non-dominated set is scoped to displayed
  successful trials and validation-eligible fields. It is not a promotion
  rule; the immutable Experiment verdict remains authoritative.

## Verification

- `node --check autoquant/studio_assets/studio.js`
- `uv run python -m unittest discover -s tests -q`
  — 109 tests passed in 172.796 seconds.
- `uv build` produced both sdist and wheel.
- A fresh Python 3.11 virtual environment installed the wheel with its full
  dependency set, then successfully ran `aq schema session-decision-matrix`,
  `aq session compare` over a bounded KEEP/REVERT/CRASH Portfolio Session, and
  `aq studio snapshot`.
- Browser QA at desktop and narrow widths verified the Selection/Test audit
  switch, sticky metric column, preference arrows, leader/trade-off summary,
  audit-only relations, failed-trial N/A cells, and explicit holdout warning.
- The first rejected wheel install used unsupported Python 3.9; the package
  correctly declares Python 3.11–3.12, and the supported Python 3.11 install
  passed.

## Progress log

- 2026-07-24 — Activated after the single-Run Portfolio Explorer made path and
  position evidence visible but left multi-candidate trade-offs hidden behind
  the primary objective.
- 2026-07-24 — Implemented one shared Core matrix for Factor, Portfolio, RL,
  and generic Studies; CLI and Studio now consume that exact read model.
- 2026-07-24 — Verified bounded leader anchoring, validation-only
  non-dominance, audit/display/context relation separation, and explicit
  failed-trial evidence.

## Completion

Delivered a versioned read-only Session comparison contract, discoverable CLI,
and responsive Studio matrix without changing immutable Experiment verdicts or
granting browser-side evaluation authority.
