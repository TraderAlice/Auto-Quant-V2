# Governed RL factor opportunity audit

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/rl-factor-opportunity-audit]],
  [[docs/design/rl-factor-policy-lab]],
  [[docs/design/rl-policy-behavior-rationale]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Every governed RL validation/test decision exposes what each fixed factor sleeve
would have earned for one bar from the policy's exact actual pretrade book. A
researcher can distinguish model-score rationale from realized local
opportunity, quantify selection regret, and see where the candidate factor adds
marginal value without granting hindsight any promotion or trading authority.

## Context

The current RL lane preserves exact Q values, chosen-versus-runner-up feature
contributions, action runs, and realized accounting for the selected sleeve.
Those are necessary but incomplete. Action-conditioned outcomes are endogenous:
they do not reveal whether another governed sleeve would have been better at
the same decision. Running five independent fixed-sleeve backtests does not
answer the question either because each path arrives with a different book and
therefore different turnover, cost, no-trade, and risk-governor behavior.

## Scope

### In scope

- One-step counterfactual execution of all five fixed sleeves from the exact
  actual policy pretrade book at each validation/test timestamp.
- Exact proposed/executed weights, trades, next-bar returns, reward, turnover,
  cost, exposure, and execution-risk evidence.
- Selected-versus-oracle rank/regret plus candidate-versus-selected and
  candidate-versus-balanced opportunity summaries.
- Strict reconstruction and selected-action reconciliation with the immutable
  policy action ledger.
- CLI, Report, Dossier, decision matrix, Studio, docs, schema, and wheel
  integration with legacy fallback.

### Out of scope

- Multi-step alternate policy paths, an oracle strategy, hindsight training,
  reward changes, action promotion, parameter selection, SHAP, or causal
  attribution.
- New factor experts, continuous allocation, live orders, Broker/UTA state, or
  any OpenAlice trading authority.

## Acceptance

- [x] Every opportunity row starts from the selected policy path's exact
  pretrade book and evaluates every governed action with the same execution and
  reward primitives.
- [x] The selected counterfactual exactly reconciles the existing action ledger
  and actual executed book; all accounting identities are reconstructible from
  immutable public evidence.
- [x] Split and trial summaries exactly reconcile decision count, oracle hits,
  selected rank/regret, candidate opportunity, turnover, cost, and risk repair.
- [x] Validation and visible-diagnostic test remain separate; opportunity
  evidence is context-only and cannot affect KEEP/REVERT.
- [x] Explorer, CLI, Reports, Dossiers, matrix, and Studio expose the evidence
  without calling ex-post oracle reward a deployable strategy.
- [x] Legacy Runs remain readable and malformed or rehashed evidence is rejected
  by deterministic bounded tests.

## Work

- [x] Audit current RL actions, sleeves, reward, execution, and public evidence.
- [x] Define the local counterfactual unit and authority boundary.
- [x] Implement fixed Judge evidence and strict public reconstruction.
- [x] Add professional consumption surfaces and Studio diagnostics.
- [x] Run focused/full tests, wheel smoke, browser QA, and completion audit.

## Findings and decisions

- 2026-07-25 — Fixed-sleeve backtests are path counterfactuals, not action
  counterfactuals; their different pretrade books confound local factor choice
  with prior turnover and execution.
- 2026-07-25 — The valid comparison unit is one next-bar action from the actual
  selected policy pretrade book. The following bar resumes the actual policy
  path; no alternative state or holdings path is propagated.
- 2026-07-25 — “Oracle” means only the ex-post best one-step governed reward
  among the five already-declared sleeves. It is an audit upper bound, never a
  policy, baseline candidate, or promotion input.
- 2026-07-25 — Exact pretrade, proposed, executed, trade, and forward-return
  vectors are worth preserving because aggregate regret without book-level
  accounting cannot distinguish factor opportunity from implementation cost.
- 2026-07-25 — The real reference validation audit found 20% one-step oracle
  hits and mean selected rank 2.6861. Intraday was locally best 60% of the
  time while balanced was selected 75%; this identifies policy headroom.
- 2026-07-25 — The same evidence rejects a false candidate-factor story:
  candidate was selected 0%, locally best only 1.6667%, lost to balanced on
  average, and beat balanced on only 30% of validation decisions.
- 2026-07-25 — The complete pretty-printed opportunity artifact is 6,783,184
  bytes for 780 decisions and 3,900 action evaluations, below the existing
  32 MiB strict artifact bound.
- 2026-07-25 — Reusing one causal risk-covariance cache across training,
  baselines, rollouts, and opportunity evaluation preserved exact semantics
  while reducing the full suite from the prior milestone's 666 seconds to
  585.77 seconds.
- 2026-07-25 — Browser QA exposed a missing Test-audit rerender call for the
  new panel; validation/test switching now updates every RL evidence section.
- 2026-07-25 — The right Inspector is now a default-collapsed, explicit
  top-bar control so comparison-heavy research evidence owns the main canvas.

## Verification

- `uv run --with pytest pytest -q`: 155 tests and 17 subtests passed in
  585.77 seconds.
- Focused template determinism: 4 tests passed in 81.64 seconds.
- Focused strict Explorer, including legacy and rehashed vector corruption:
  2 tests passed in 34.46 seconds.
- Studio plus full three-lane Report/Dossier handoff: 8 tests passed in
  47.02 seconds.
- `scripts/check_doc_links.py`: 530 documentation double-links resolve;
  Python compilation, `node --check`, and `git diff --check` passed.
- Fresh Python 3.11 wheel smoke installed 161 dependencies, created and ran a
  new governed RL Project, verified all six artifact kinds, reconstructed 360
  validation decisions / 1,800 action evaluations, and confirmed packaged
  Studio assets.
- In-app browser QA used the real immutable reference Run at
  `http://127.0.0.1:8778/`: validation/test opportunity switching,
  default-collapsed and interactive Inspector, 1280px zero-overflow layout,
  selected/local-best/candidate evidence, and zero console logs.

## Progress log

- 2026-07-25 — Plan created after auditing the existing Q-rationale and selected
  action evidence.
- 2026-07-25 — Added one shared-pretrade five-action accounting path, immutable
  artifact, split/trial aggregates, and covariance-cache reuse.
- 2026-07-25 — Added strict vector/accounting reconstruction and legacy/tamper
  behavior to the public RL Explorer.
- 2026-07-25 — Added CLI, Report, Dossier, decision-matrix, Studio, template,
  schema, and documentation consumption surfaces.
- 2026-07-25 — Completed full tests, fresh-wheel smoke, real-Run browser QA,
  UI density correction, and completion audit.

## Completion

Completed with every acceptance item backed by executable, package, or browser
evidence. Multi-step alternate-policy simulation remains intentionally outside
this contract; it would answer a different path-dependence question and must
not be inferred from the shipped one-step audit.
