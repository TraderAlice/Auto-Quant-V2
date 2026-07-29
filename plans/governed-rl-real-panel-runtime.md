# Governed RL real-panel runtime

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/rl-factor-policy-lab]],
  [[docs/design/rl-incremental-value-attribution]], and
  [[docs/design/caller-owned-decision-cadence]].
- Source field trial: [[plans/global-etf-calendar-month-allocation]] and
  [[docs/trading-request-field-trials]].

## Outcome

Complete the optional governed-RL lane for the real nine-asset global ETF
calendar-month allocation request inside its fixed 120-second Judge boundary,
without changing the research question, learning budget, folds, seeds,
baselines, portfolio semantics, or immutable evidence contract.

## Context

The clean AutoQuant `0.8.4` field trial successfully completed Factor and
Portfolio research over 4,922 aligned Yahoo sessions, but the governed-RL lane
reached its exact 120-second timeout. Its Project-root `framework-needs.md`
records this as a real Workbench capacity gap.

The caller has explicitly accepted a 120-second bounded RL evaluation. That is
the ceiling to satisfy, not permission to enlarge training or reduce evidence.
The current implementation repeatedly reconstructs pandas portfolio state,
decision schedules, mandate resolution, risk accounting, and one-step action
evidence across folds, seeds, episodes, baselines, and actions. Profiling must
identify which repeated work can be shared while preserving exact results.

## Scope

### In scope

- Profile the fixed governed-RL Judge on a representative real panel.
- Reuse immutable market, mandate, schedule, target, covariance, and accounting
  inputs where doing so preserves exact chronological behavior.
- Optimize the episode/rollout and evidence paths without changing public
  research semantics or artifact contents.
- Re-run the real global ETF RL Study, independently validate its artifacts,
  and record whether adaptive selection adds evidence beyond the mechanical
  baseline.
- Preserve the fixed 120-second hard timeout in new Projects.

### Out of scope

- More episodes, hyperparameter search, GPU/distributed training, new actions,
  new state features, reduced folds or seeds, truncated history, evidence
  sampling, or a longer timeout.
- Treating a successful RL Run as proof that RL is useful; a negative
  incremental conclusion is acceptable.
- Live-account, Order, TPSL, or execution authority.

## Acceptance

- [x] A reproducible profile identifies the dominant real-panel costs before
  optimization.
- [x] Optimized and reference paths produce exact or explicitly tolerance-bound
  equivalent actions, weights, rewards, metrics, models, and evidence on
  deterministic fixtures.
- [x] The unchanged nine-asset, 4,922-session governed-RL Study completes
  within 120 seconds from a fresh Project and passes strict Explorer, Project,
  orientation, CLI, and Studio verification.
- [x] The final Report/Dossier states whether RL adds validation value beyond
  the selected mechanical baseline without using test evidence for selection.
- [x] Focused/full tests, docs, package smoke, patch version, commit/push, tag,
  clean release replay, and repository cleanliness pass.

## Work

- [x] Preserve the timeout reproduction and profile the current Judge.
- [x] Implement semantics-preserving shared runtime primitives and regression
  equivalence tests.
- [x] Complete the real-data development Run and inspect the incremental RL
  diagnosis.
- [x] Update Agent/human surfaces and durable runtime documentation.
- [x] Release, create a fresh clean Project, reproduce under 120 seconds, and
  close the field-trial need.

## Findings and decisions

- 2026-07-29 — Runtime is a product property for an Agent-operated workbench.
  The 120-second bound is caller-approved and Harness-owned; the fixed
  scientific workload must fit inside it.
- 2026-07-29 — Optimization may share pure inputs and exact deterministic
  calculations, but it may not reduce the number of declared learning trials,
  baseline paths, or evidence rows.
- 2026-07-29 — Calendar-held dates still advance drift, risk compliance,
  reward, and causal state, but they do not reconstruct unchanged target
  allocations or five identical executed opportunity books.
- 2026-07-29 — Training-only fixed policies, contextual ridge, and Q-learning
  use an exact array accounting path. Validation, test, immutable metrics, and
  public evidence retain the full governed accounting path.
- 2026-07-29 — The first sub-120-second Run exposed a separate evidence-size
  failure: 9,102 schedule-held rows repeated one executed book five times and
  produced a 92 MiB artifact. The fixed contract stores one shared execution
  plus five distinct proposed targets on those dates; decision-eligible dates
  retain five complete counterfactual books.

## Verification

- Preserved AutoQuant `0.8.3` Run
  `run-20260728T215047604954Z-f5cb1ac946d0` failed with
  `judge.timeout` after 120,008 ms on the unchanged 4,922-session,
  nine-asset Study.
- Interrupted `cProfile` evidence over the same panel recorded roughly
  989 million calls. Signal-policy target construction consumed 209.8 profiled
  seconds because allocation ran on every date despite a calendar-month
  schedule; rollout/accounting and contextual-ridge opportunity construction
  were the next repeated costs.
- Exact target-construction timing fell from 74.47 seconds to 26.47 seconds
  while all five full-panel target hashes remained byte-identical.
- Focused equivalence tests compare the array and full governed paths for
  actions, policy state, executed weights, rewards, benchmark returns,
  fixed-policy Sharpe, and same-pretrade action opportunity rewards.
- Development Project
  `global-etf-calendar-month-allocation-v086-rl-runtime-dev5` Run
  `run-20260729T022441138315Z-d98f539430d7` completed the unchanged
  4,922-session, two-fold, three-seed, 12-episode Study in 96,184 ms under the
  120-second hard timeout. The schedule-aware opportunity artifact is 25 MiB,
  down from 92 MiB. Strict RL Explorer, Project validation, orientation, CLI,
  and Studio verification pass with zero diagnostics and zero executed
  volatility-ceiling breaches.
- The development Run rejects adaptive RL promotion:
  mean validation net Sharpe is `0.632201`, mean validation advantage versus
  the best baseline is `-0.096178`, and all six validation paths have
  non-positive full-path net active return. Test remains visible audit only.
- Modified-surface regression passes 41/41 tests in 160.685 seconds.
- Complete source regression passes 271/271 tests in 819.224 seconds.
- `uv build` produces `auto_quant-0.8.6.tar.gz` and the matching universal
  wheel. A fresh Python 3.11 environment installs only that wheel with pandas
  3.0.5, reports `aq 0.8.6`, executes the governed-RL template in 13,378 ms,
  and passes strict RL Explorer and Studio checks without diagnostics.
- Release commit `a9796b2`, tag `v0.8.6`, and `main` were pushed to
  `luokerenx4/auto-quant-v2`.
- Clean release Project `global-etf-calendar-month-allocation-v086-clean`
  Run `run-20260729T024800277277Z-f483dfb0a313` completed in 88,877 ms
  with Harness `0.8.6`, commit `a9796b2`, and `dirty: false`. Its 25 MiB
  opportunity artifact, strict RL Explorer, Project validation, orientation,
  CLI, and Studio pass without diagnostics.
- Immutable Report `report-20260729T025100457743Z-379fef8ccfac` records the
  validation-only negative conclusion and baseline-retaining recommendation;
  its delegated Session completed without candidate promotion.

## Progress log

- 2026-07-29 — Promoted the global ETF Project's governed-RL interactive
  capacity observation into this active Workbench plan.
- 2026-07-29 — Replaced repeated off-schedule allocation, evidence, and
  training accounting with strict-equivalent schedule-aware and array paths.
- 2026-07-29 — Completed real-panel execution and strict public-surface
  verification in 96.2 seconds; retained the mechanical baseline because RL
  failed validation incremental-value evidence.
- 2026-07-29 — Released and pushed `v0.8.6`, reproduced the complete result
  from the clean release in 88.9 seconds, published the immutable negative
  Report, completed the baseline-retaining Session, and closed the originating
  Workbench need.

## Completion

Completed on 2026-07-29. AutoQuant `0.8.6` runs the unchanged real
nine-asset, 4,922-session, two-fold, three-seed, 12-episode governed-RL
challenge inside its 120-second product boundary while retaining complete
validation/test and counterfactual evidence. Exact schedule-aware targets,
train-only governed array accounting, and shared off-schedule execution reduce
runtime without changing results; compact immutable opportunity storage keeps
the artifact below the strict reader bound and remains independently
reconciled. The clean release evidence rejects adaptive promotion: every
validation path has non-positive full-path incremental value, so the existing
mechanical Portfolio remains the supported research handoff.
