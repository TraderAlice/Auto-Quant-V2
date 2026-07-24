# Selection-adjusted research evidence

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/selection-adjusted-research-evidence]],
  [[docs/design/research-selection-integrity]],
  [[docs/design/session-decision-matrix]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/rl-factor-policy-lab]], and
  [[docs/design/program-research-dossiers]].

## Outcome

Make repeated AI strategy search statistically visible. Every governed
Session, Report, Dossier, CLI comparison, and Studio readout must identify its
Project-wide fixed-evaluation research family, count unique attempted
candidate sources across Session boundaries, and publish only the
selection-adjusted evidence justified by the available immutable data.

## Context

AutoQuant currently protects validation/test roles and discloses the number of
Experiments in one Session. That does not quantify selection bias, and opening
a new Session resets the displayed count even though the same data and Judge
are still being searched. This is especially dangerous for an AI workbench
that can generate many candidate factors cheaply.

A professional review needs to know whether an attractive result survives its
search history. Factor Runs already publish HAC inference. Portfolio Runs
publish validation returns but omit the higher moments needed for
Probabilistic and Deflated Sharpe. Governed RL reports a mean across dependent
fold/seed paths, so treating that aggregate as one return path would violate
the DSR assumptions.

## Scope

### In scope

- A content-derived research-family identity over fixed Study id, program,
  Judge, dataset, dependencies, and objective.
- Project-wide, as-of-time counting of unique candidate source hashes,
  successful/failed trials, duplicate executions, and reproducibility.
- Factor family-wise error evidence using the existing HAC p-value and a
  conservative Bonferroni correction.
- Portfolio return skewness, non-excess kurtosis, period Sharpe, PSR, DSR,
  expected maximum Sharpe, and minimum track-record observations.
- An explicit unsupported result for aggregate governed-RL objectives whose
  fold/seed evidence is not one independent return path.
- Immutable Report and Dossier freezing plus Session/CLI/Studio projection.
- Historical Run compatibility: old evidence remains loadable and explains
  why an adjustment is unavailable.

### Out of scope

- Probability of Backtest Overfitting without a complete combinatorial
  train/test performance matrix.
- Estimating an unobservable effective number of independent correlated
  strategies. Unique source trials are disclosed as a conservative upper-bound
  assumption.
- Blind test execution, external data provenance, live capital approval, or
  automatic trading authority.
- Retrofactively changing existing KEEP/REVERT verdicts. Selection adjustment
  is a Core-authored professional diagnostic in this version.

## Acceptance

- [x] Restarting or completing a Session cannot reset the research-family
  trial count for the same fixed evaluation contract.
- [x] Duplicate executions of identical source do not inflate unique trials,
  and inconsistent repeated results become a visible reproducibility failure.
- [x] Factor evidence reports raw and family-wise adjusted HAC significance.
- [x] Portfolio evidence uses fixed, tested PSR/DSR equations with explicit
  annualization, higher moments, trial-count assumption, confidence threshold,
  and minimum track record.
- [x] RL and legacy evidence fail closed with an exact unsupported/insufficient
  reason instead of receiving a fabricated DSR.
- [x] Session snapshot, comparison CLI, Reports, Dossiers, and Studio reconcile
  the same Core projection; immutable Reports remain valid after later trials.
- [x] Bounded synthetic and request-driven tests prove cross-Session counting,
  as-of freezing, tamper rejection, statistical fixtures, UI behavior, wheel
  packaging, and full regression.

## Work

- [x] Audit current metrics, immutable history, Report freezing, and published
  statistical literature.
- [x] Fix the research-family and objective-family statistical contract.
- [x] Implement return moments, family discovery, and adjustment calculations.
- [x] Freeze and project the evidence through Session, Report, Dossier, CLI,
  and Studio.
- [x] Complete focused/full tests, real-project/browser QA, wheel verification,
  and documentation.

## Findings and decisions

- 2026-07-24 — The family boundary is fixed evaluation authority, not Session
  lifetime: Study id, program, Judge, dataset, dependency, and objective.
- 2026-07-24 — Unique candidate source hashes are a conservative trial-count
  upper bound. AutoQuant will not claim they are statistically independent.
- 2026-07-24 — DSR is valid for the Portfolio validation return path after the
  Judge publishes length and the first four moments. Factor inference instead
  uses its existing HAC p-value with family-wise correction.
- 2026-07-24 — The governed-RL objective averages dependent fold/seed Sharpe
  values. V1 must label single-path DSR unsupported rather than collapse or
  concatenate those paths.
- 2026-07-24 — PBO is out of scope until a future evaluator produces the full
  combinatorial selection matrix it requires.

## Verification

- `uv run python scripts/check_doc_links.py`
  - 409 documentation double-links resolved.
- `uv run python -m unittest discover -s tests -v`
  - 140 tests passed in 277.435 seconds.
- Focused selection/Report/Dossier/Studio suite:
  - 11 tests passed in 20.272 seconds.
- Real reference paths:
  - Factor known-improvement/leakage test proves family-wise HAC adjustment;
  - Portfolio known-improvement/leakage test proves a three-source family,
    failed-trial disclosure, and PSR greater than DSR;
  - governed-RL Campaign test proves the dependent fold/seed unsupported
    boundary.
- Wheel:
  - built `auto_quant-0.1.0-py3-none-any.whl`;
  - verified `selection.py`, all three updated programs, and Studio assets are
    packaged;
  - installed into a fresh Python 3.11 environment with all dependencies;
  - started a Portfolio Session from the installed `aq`, which published
    `deflated-sharpe-ratio-v1`, 63 observations, and a 230-observation minimum
    track record for the one-trial baseline.
- Browser:
  - verified a two-source Portfolio family at 1440×900 with DSR, expected-max
    Sharpe, and track-record evidence in the Inspector;
  - verified 390×844 responsive layout with no horizontal overflow;
  - no browser warnings or errors.

## Progress log

- 2026-07-24 — Plan activated after the full-workbench audit identified
  selection adjustment as the largest remaining credibility gap for autonomous
  factor search.
- 2026-07-24 — Implemented Project-wide fixed-evaluation families, Factor
  Bonferroni-HAC, Portfolio PSR/DSR, explicit governed-RL refusal, immutable
  as-of Report/Dossier evidence, and Studio selection-risk inspection.
- 2026-07-24 — Full tests, documentation graph, isolated wheel, and desktop /
  mobile browser QA passed.

## Completion

Completed 2026-07-24. Selection risk is now a verified Project-wide evidence
layer and remains diagnostic-only: it cannot rewrite an Experiment verdict or
grant trading authority.
