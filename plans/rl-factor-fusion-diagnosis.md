# Diagnose RL factor-fusion value

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/rl-factor-policy-lab]],
  [[docs/design/rl-factor-opportunity-audit]],
  [[docs/design/rl-incremental-value-attribution]],
  [[docs/design/rl-policy-evidence-explorer]],
  [[docs/design/quant-research-lifecycle]], and
  [[docs/design/program-research-dossiers]].

## Outcome

One governed RL Run explains whether the content-locked candidate factor is
useful, whether the frozen policy captures its local opportunities, whether
adaptive book selection adds gross and net value versus the
validation-selected mechanical baseline, whether that value survives
risk-adjusted comparison and seed/fold stability, and where any loss
concentrates. The same validation-only diagnosis is visible in CLI, Studio,
Report, Dossier, and OpenAlice handoff.

## Context

AutoQuant already preserves fixed-sleeve baselines, exact linear Q rationale,
same-pretrade one-step opportunity evidence, and independent full-path
incremental attribution. These surfaces answer different questions but leave
the operator to manually join them. A real quant review needs one bounded
decision bridge that distinguishes a weak candidate factor from poor policy
capture, negative active book selection, implementation drag, risk-adjusted
underperformance, and unstable apparent value.

## Scope

### In scope

- A Core-owned factor-fusion diagnosis synthesized only from already verified
  candidate, opportunity, policy, baseline, and incremental-attribution
  evidence.
- Separate local one-step candidate opportunity, full-path active gross/cost/net
  transmission, risk-adjusted advantage, and seed/fold stability semantics.
- Validation-only stage/focus plus visible-test audit and exact loss locators by
  causal regime, action pair, switch state, and asset.
- CLI, Studio, immutable Report, Project Dossier, and legacy compatibility.

### Out of scope

- Changing candidate factors, RL state, reward, actions, training, hyperparameters,
  baseline selection, execution, or historical Runs.
- Treating the one-step oracle as learnable or executable, using test to choose
  a policy, or granting Broker/UTA/order authority.
- Claiming causal factor importance from Q coefficients or endogenous selected
  action outcomes.

## Acceptance

- [x] Candidate standalone and local-opportunity evidence remain explicitly
      distinct from full-path adaptive value.
- [x] Validation diagnosis separates negative gross selection, cost-destroyed
      edge, absent risk-adjusted value, seed/fold instability, and positive
      adaptive value without test leakage.
- [x] Loss locators and trial stability reconcile the verified incremental
      attribution and preserve their descriptive authority.
- [x] CLI, Studio, frozen Report, and Dossier expose one identical diagnosis;
      historical evidence remains readable without invented fusion claims.
- [x] Deterministic tests, real bounded evidence, browser inspection,
      documentation, full regression, and package checks pass.

## Work

- [x] Audit existing candidate, opportunity, policy, baseline, and incremental
      evidence contracts.
- [x] Implement and schema the validation-only fusion diagnosis.
- [x] Freeze and render the projection across Report, Dossier, CLI, and Studio.
- [x] Add reconstruction, compatibility, and UI regression coverage.
- [x] Complete real evidence verification and documentation.
- [x] Commit and push the completed milestone.

## Findings and decisions

- 2026-07-25 — Same-pretrade one-step opportunity and independent full-path
  attribution answer different questions and must never be merged into one
  pseudo-counterfactual return.
- 2026-07-25 — Candidate factor assessment will report both fixed-sleeve net
  Sharpe and candidate-versus-balanced local reward. Neither alone authorizes
  inclusion or promotion.
- 2026-07-25 — Adaptive transmission will diagnose gross active selection,
  incremental cost, net active return, risk-adjusted Sharpe advantage, and
  positive trial-path breadth in that order. Test remains visible audit only.
- 2026-07-25 — The deterministic reference Run diagnoses
  `adaptive-book-selection-negative` / `factor-sleeve-research`: candidate
  fixed-sleeve Sharpe delta versus balanced `-10.1787`, full-path validation
  gross / cost / net active return `-33.8762%` / `0.5620%` / `-34.4382%`,
  Sharpe advantage `-27.9803`, and `0%` positive net trial paths.

## Verification

- `uv run python -m unittest
  tests.test_rl_explorer.RlPolicyEvidenceExplorerTests.test_projection_reconciles_trials_baselines_training_and_actions`
  — passed.
- `uv run python -m unittest
  tests.test_dossiers.ProgramResearchDossierTests.test_rl_report_is_included_and_analysis_must_cover_every_lane`
  — passed.
- `uv run python -m unittest
  tests.test_studio.StudioObservationTests.test_http_server_exposes_only_fixed_read_only_routes_and_headers`
  — passed.
- `uv run python -m unittest
  tests.test_reports.ResearchHandoffTests.test_prior_decision_support_without_rl_diagnosis_remains_loadable`
  — passed.
- `uv run python -m unittest discover -s tests` — `166` tests passed in
  `1042.608s`.
- `node --check autoquant/studio_assets/studio.js`,
  `uv run python -m compileall -q autoquant tests/test_rl_explorer.py
  tests/test_dossiers.py tests/test_studio.py`, `git diff --check`, and
  `uv run python scripts/check_doc_links.py` — passed.
- `uv build` — source distribution and wheel built successfully.
- Browser inspection at `1280×720` confirmed the five-stage diagnosis chain,
  validation/test separation, loss locators, and no horizontal overflow.
- Bounded evidence workspace:
  `/private/tmp/autoquant-rl-fusion-ui-20260725/workspace`; Run
  `run-20260725T042823628954Z-fcd2cd652240`; Studio
  `http://127.0.0.1:8785/#rl-evidence`.

## Progress log

- 2026-07-25 — Plan activated after Portfolio signal monetization made the
  missing RL-versus-mechanical decision bridge explicit.
- 2026-07-25 — Added the strict diagnosis contract, immutable handoff freeze,
  CLI/Studio views, browser-verified value chain, and legacy compatibility.

## Completion

Completed. One immutable governed RL Run now answers where candidate-factor
opportunity fails to become stable post-cost adaptive value, while keeping
local ex-post opportunity, full-path active attribution, validation selection,
test audit, and all authority boundaries explicit.
