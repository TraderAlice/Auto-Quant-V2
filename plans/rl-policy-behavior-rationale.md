# RL policy behavior and decision rationale

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/rl-policy-behavior-rationale]],
  [[docs/design/rl-factor-policy-lab]],
  [[docs/design/cross-study-factor-dependencies]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Every new governed RL Run explains both how its fixed factor-sleeve actions
persist over time and why its linear Q policy selected each action over the
runner-up. A researcher can distinguish useful regime adaptation from noisy
switching, identify which encoded features drive the policy, and inspect
realized reward, turnover, and cost conditional on each selected sleeve.

## Context

The current RL lane already preserves folds, seeds, training histories,
baselines, action frequencies, rewards, implementation costs, and executed-book
risk. It does not preserve the exact state/feature/Q evidence behind an action,
and a transition count alone does not describe action-run duration or one-bar
churn. That leaves a material interpretation gap between “RL beat or trailed a
baseline” and “the learned policy behaved coherently enough to iterate.”

## Scope

### In scope

- Exact validation/test raw state, encoded feature, action-Q, runner-up,
  chosen margin, and per-feature margin contribution evidence.
- Deterministic action-run segmentation within every fold/seed/split.
- Transition/retention, run-length, tie, Q-margin, action-conditional
  reward/net/turnover/cost, and feature-driver summaries.
- Strict reconstruction from the immutable model and action artifacts.
- Legacy fallback plus CLI, Report, Dossier, decision matrix, Studio, docs,
  schema, and wheel integration.

### Out of scope

- Treating Q values as calibrated probabilities, causal feature importance,
  SHAP, counterfactual market simulation, or policy promotion authority.
- Changing the encoder API, reward, learner, actions, folds, seeds, or
  validation-only objective.
- Continuous allocation, live orders, OpenAlice UTA mutation, or Broker state.

## Acceptance

- [x] Every rationale row exactly reproduces model Q values, selected action,
  deterministic runner-up, action margin, and feature contribution identity.
- [x] Action runs are split/fold/seed bounded and exactly reconcile all action
  rows without crossing rollout resets.
- [x] Aggregate behavior reconciles frequency, reward, net return, turnover,
  cost, transitions, and every rationale row.
- [x] Q margin is explicitly uncalibrated; feature contribution is a linear
  chosen-versus-runner decomposition, not causal importance.
- [x] Explorer, CLI, Reports, Dossiers, matrix, and Studio expose context-only
  behavior while preserving validation/test authority.
- [x] Legacy Runs remain readable and fully rehashed rationale/model/action
  inconsistencies are rejected by deterministic tests.

## Work

- [x] Audit current RL model, action, baseline, implementation, and UI evidence.
- [x] Implement rationale artifact and action-run metrics in the fixed Judge.
- [x] Add strict public reconstruction and professional consumption surfaces.
- [x] Run focused/full tests, wheel smoke, browser QA, and completion audit.

## Findings and decisions

- 2026-07-25 — Existing action frequency and transition counts show allocation
  but not persistence or decision rationale.
- 2026-07-25 — The fixed learner is linear, so chosen-versus-runner-up margin
  has an exact additive feature decomposition. This is more faithful than
  introducing a generic post-hoc explainer.
- 2026-07-25 — Q magnitude is model-scale dependent and uncalibrated. Public
  evidence may compare rank/margin inside one model path but cannot call it
  confidence or probability.
- 2026-07-25 — All behavior metrics are contextual and cannot enter
  KEEP/REVERT, baseline selection, or Session dominance.
- 2026-07-25 — The reference policy exposes a professionally useful warning:
  validation mean action-run length is 1.967 bars while 98.36% of runs are
  single-bar. A few longer balanced runs hide pervasive one-bar churn.

## Verification

- `uv run --with pytest pytest -q`: 154 tests and 17 subtests passed in
  562.58 seconds.
- `python -m unittest discover -s tests`: 154 tests passed in 537.184
  seconds.
- Final invariant-focused decision-matrix check passed after all behavior
  metrics were made explicitly context-preference rather than “better/worse”.
- `scripts/check_doc_links.py`: 505 documentation double-links resolve;
  Python compilation, `node --check`, and `git diff --check` passed.
- Fresh Python 3.11 wheel smoke installed 161 dependencies, created and ran
  the governed RL template, verified 780 action/rationale rows through
  `aq run rl`, and confirmed the packaged Studio behavior assets.
- In-app browser QA verified the real reference Run at
  `http://127.0.0.1:8776/`: Validation/Test switching, 360/420 decision
  coverage, desktop and 820/640 responsive layouts, and zero console warnings
  or errors.

## Progress log

- 2026-07-25 — Plan created from the post-lifecycle RL evidence audit.
- 2026-07-25 — Added the immutable rationale ledger, split-bounded action-run
  aggregates, exact cross-artifact reconstruction, and legacy fallback.
- 2026-07-25 — Added CLI, Report, Dossier, decision-matrix, Studio, template,
  schema, and documentation consumption surfaces.
- 2026-07-25 — Completed full tests, wheel smoke, real-Run browser QA, and
  final reconciliation audit.

## Completion

Completed with every acceptance item backed by executable or browser evidence.
