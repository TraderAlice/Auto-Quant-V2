# Make mechanical portfolio parameters locally auditable

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/portfolio-parameter-neighborhood]] and
  [[docs/design/portfolio-construction-lab]].

## Outcome

Every fixed Portfolio Run shows whether its result survives a small,
predeclared neighborhood of signal entry/exit thresholds and execution
no-trade bands without allowing the neighborhood to become another
candidate-selection or parameter-optimization channel.

## Context

The Portfolio Judge already fixes one mechanical signal policy and reports
cost, delay, hysteresis, risk, capacity, and position-lifecycle evidence. A
quantitative researcher still cannot tell whether the result exists only at
the single `0.75/0.55/0.45/0.25` threshold point and `0.05` no-trade band.
That makes the current headline vulnerable to local parameter fragility.

This surface must remain Judge-owned and context-only. Selecting the strongest
cell after seeing validation or test would create a hidden correlated strategy
search and contradict the existing validation-only research contract.

## Scope

### In scope

- A fixed five-profile signal neighborhood crossed with three no-trade bands.
- Complete validation/test net-return, turnover, cost, rebalance, and signal
  transition paths for every declared configuration.
- Strict public reconstruction and base-configuration reconciliation.
- CLI, Report, Dossier, Decision Matrix, and Studio heatmap projections.

### Out of scope

- Automatic parameter selection, optimization, or promotion authority.
- Changes to request-derived position authority, risk ceiling, costs, delay,
  benchmark, data splits, or the candidate factor.
- Effective correlated-trial estimation, PBO, or a claim of global parameter
  robustness.

## Acceptance

- [x] The fixed Judge evaluates exactly the declared neighborhood and emits
      immutable daily rows plus aggregate validation/test evidence.
- [x] The base cell reconciles the ordinary Portfolio metrics exactly.
- [x] Public Explorer reconstruction rejects missing, extra, duplicate,
      misaligned, or numerically inconsistent rows.
- [x] CLI, reports, dossiers, the context-only Decision Matrix, and Studio
      communicate local robustness without naming a recommended configuration.
- [x] Studio shows validation and visible-test heatmaps with base-cell
      identity and parameter-search disclosures.
- [x] Bounded deterministic tests, complete suite, docs, wheel contents, and
      real desktop/narrow-browser behavior agree.

## Work

- [x] Specify the fixed neighborhood and its authority boundary.
- [x] Implement Judge metrics and exact daily artifact.
- [x] Implement strict Explorer reconstruction and downstream projections.
- [x] Implement Studio heatmap and responsive presentation.
- [x] Complete regression, documentation, packaging, and browser audit.

## Findings and decisions

- 2026-07-25 — The neighborhood varies only entry selectivity, hysteresis
  width, and the execution no-trade band. Mandate, risk, cost, split, and
  candidate inputs remain identical.
- 2026-07-25 — Five signal profiles crossed with `0.00`, `0.05`, and `0.10`
  one-way no-trade bands produce 15 predeclared configurations. The current
  policy is an explicitly identified base cell, not an implicitly selected
  winner.
- 2026-07-25 — Browser inspection exposed that the first proposed `0.65`
  entry and `0.51/0.49` exit perturbations mapped to the same discrete ranks
  as the base in the six-asset fixture. Profiles now cross adjacent attainable
  rank buckets and separately stress entry, exit, and their joint effect.
- 2026-07-25 — Validation and test are both visible, but neither may choose a
  cell. The surface is local robustness context only.
- 2026-07-25 — Repeated Portfolio simulations reuse one causal covariance
  cache per Run. Cached and uncached targets, ledgers, daily accounting, and
  weights are exactly equal; configuration-specific drift/no-trade/risk
  decisions remain independent.

## Verification

- `uv run --with pytest pytest -q`: 155 tests and 17 subtests passed in
  666.01 seconds.
- Focused cached/uncached covariance, reference-template, strict artifact
  tamper rejection, CLI, Decision Matrix, Report, Dossier, and Explorer tests
  passed.
- `uv run python scripts/check_doc_links.py`: 516 documentation double-links
  resolve.
- Python `compileall`, `node --check`, and `git diff --check` passed.
- The built Python 3.11 wheel contains the updated Portfolio Judge/Core,
  candidate program/research instructions, and all Studio HTML/JS/CSS assets.
- In-app browser QA on the real reference Run at
  `http://127.0.0.1:8777/` verified distinct attainable percentile profiles,
  validation/test switching, desktop/820/640 presentation, zero page
  horizontal overflow at 640px, and zero console warnings or errors.

## Progress log

- 2026-07-25 — Plan created and activated after the governed-RL behavior
  milestone exposed the next missing professional portfolio diagnostic.
- 2026-07-25 — Added exact daily neighborhood paths, strict public
  reconstruction, context-only downstream interfaces, and the Studio heatmap.
- 2026-07-25 — Corrected duplicate discrete-rank profiles through browser QA,
  optimized repeated covariance work without changing semantics, and
  completed full regression, docs, wheel, and responsive-browser audits.

## Completion

Completed with every acceptance item backed by executable or browser evidence.
