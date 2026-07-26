# Request-bound numerical research horizon

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/request-bound-research-horizon]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/ohlcv-factor-lab]],
  [[docs/design/portfolio-construction-lab]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Make a delegated request's numerical forward horizon part of the immutable
research question. Factor selection, purge, diagnostics, component evidence,
Portfolio/RL identity, Studio, Reports, and Dossiers must all describe the
same decision-bar contract.

## Context

The Research Request currently has only a free-text `horizon`. The Factor
Judge always selects one-bar IC and diagnoses fixed 5/10-bar returns. On a
daily US-equity dataset that means “tomorrow”; on an hourly dataset it means
“next hour”, even when the caller asked about one to three months. The text
survives into handoff while the numerical experiment answers another question.

AutoQuant must not infer “month” from prose because sessions, continuous
markets, base intervals, and caller intent differ. The caller supplies exact
decision bars and AutoQuant binds them to the locked dataset clock.

## Scope

### In scope

- Add optional strict `horizonPolicy` to Research Request with one primary and
  a bounded ordered diagnostic forward-bar set.
- Derive one content-addressed `research-horizon.json` fixed dependency shared
  by Factor, Portfolio, and governed RL.
- Reject a horizon that leaves insufficient purged observations in the locked
  dataset.
- Make Factor selection, split purge, folds, quantiles, qualification,
  candidate-declared component evidence, summaries, and artifacts use the
  exact policy.
- Keep Portfolio/RL next-bar accounting truthful while binding and disclosing
  the wider research horizon; do not mislabel one-step reward as a direct
  holding-period forecast.
- Project the policy through CLI schemas, Explorers, Studio, Reports, Dossiers,
  and OpenAlice-facing documentation.

### Out of scope

- Parsing natural-language time spans.
- Forced minimum/maximum holding periods, timed exits, TPSL, or intrabar fills.
- Changing Portfolio accounting or RL reward to overlapping multi-bar returns.
- Choosing the dataset cadence for the caller.

## Acceptance

- [x] Strict validation rejects unknown, boolean, unordered, duplicate,
  out-of-bound, or primary-missing horizon policies.
- [x] Intake rejects a numerically valid horizon whose purged split evidence
  is too short.
- [x] Every lane depends on the same content-addressed Horizon Mandate.
- [x] Factor primary score and every primary-only diagnostic use
  `primaryForwardBars`, not hidden bar 1.
- [x] Dynamic diagnostic bars reconcile through immutable artifacts and the
  Factor Explorer schema.
- [x] Portfolio/RL evidence and all handoff surfaces disclose the same policy
  without claiming it changes one-step accounting.
- [x] Custom daily-equity and configurable-interval tests, tamper checks, full
  regression, JavaScript syntax, docs, and package build pass.

## Work

- [x] Audit request horizon flow against Factor/Portfolio/RL numerical
  semantics and OpenAlice handoff.
- [x] Define caller/Core authority and explicit non-goals.
- [x] Implement request, Horizon Mandate, intake, and Study dependency
  contracts.
- [x] Make Factor diagnostics and selection dynamic.
- [x] Bind Portfolio/RL and expose verified read surfaces.
- [x] Complete documentation, full verification, commit, and push.

## Findings and decisions

- 2026-07-27 — Free-text horizon is useful human context but cannot be a
  numerical evaluation contract.
- 2026-07-27 — A decision bar is defined by the locked dataset base clock.
  AutoQuant will display that clock rather than infer calendar duration.
- 2026-07-27 — Portfolio and RL remain causal sequential simulations. Their
  cumulative evidence may support a longer question, but one-step accounting
  is not relabelled as a multi-bar target.

## Verification

- `.venv/bin/python -m unittest discover -v`
  - 215 tests passed in 1394.394 seconds.
- `.venv/bin/python -m unittest tests.test_horizons tests.test_cli
  tests.test_research_program tests.test_studio tests.test_reports
  tests.test_dossiers tests.test_decision_matrix tests.test_factor_lab
  tests.test_intake -v`
  - 84 focused contract and real-lane tests passed in 652.399 seconds.
- Custom daily-equity request with primary `5` and diagnostics `[1, 5, 20]`
  - Factor score, purge, immutable artifacts, Explorer, and JSON schema
    reconciled to the exact policy.
- `node --check autoquant/studio_assets/studio.js`
  - passed.
- `.venv/bin/python -m compileall -q autoquant tests`
  - passed.
- `git diff --check`
  - passed.
- `uv build`
  - built `auto_quant-0.1.0.tar.gz` and
    `auto_quant-0.1.0-py3-none-any.whl`.

## Progress log

- 2026-07-27 — Plan activated after proving that all existing Factor Runs
  select one-bar IC regardless of the delegated request or configured base
  interval.
- 2026-07-27 — Added strict optional `horizonPolicy`, a content-addressed
  Horizon Mandate, capacity checks, and exact Study dependencies across all
  three lanes.
- 2026-07-27 — Replaced Factor's hidden primary-one-bar assumptions throughout
  score, purge, folds, regimes, styles, components, artifacts, Decision
  Matrix, Explorer, and Studio.
- 2026-07-27 — Bound Portfolio/RL, Reports, Dossiers, and public schemas to the
  same research question while preserving truthful sequential accounting.
- 2026-07-27 — Focused/full regression, JavaScript/static checks, docs, and
  package build passed.

## Completion

AutoQuant now keeps three clocks separate and explicit: the market/session
clock, the configurable base K-line clock, and the caller's forward research
horizon measured on that base clock. A daily XNYS request may select a
21-session target while a 15-minute request may select a different exact bar
count; neither silently falls back to “next bar.” Candidate Agents cannot edit
the Horizon Mandate, non-primary diagnostics cannot select a Factor, and every
downstream read/handoff surface preserves the same identity with
`tradingAuthority: none`.
