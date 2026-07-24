# Causal RL policy state and path-consistent baseline

- Status: `completed`
- Updated: `2026-07-25`
- Related design:
  [[docs/design/causal-rl-policy-state-and-baseline]],
  [[docs/design/rl-factor-policy-lab]], and
  [[docs/design/rl-factor-opportunity-audit]].

## Outcome

The governed factor-policy laboratory must expose the execution state that
actually determines reward and compare RL with a contextual baseline trained on
same-pretrade train-only labels.

## Evidence motivating the change

- The current reward depends on the drifted pretrade book, no-trade decision,
  risk repair, and turnover cost, but policy state contains only the previous
  action. The environment is therefore not fully Markov.
- The current contextual ridge fits each action from a different fixed-action
  portfolio path and then dynamically switches actions. Its action labels are
  path-confounded.
- A controlled candidate that only adds causal `volume_regime` raises the real
  fixture's validation Sharpe from `9.965947` to `32.082895`, oracle hit rate
  from `20%` to `66.1111%`, and mean selected rank from `2.6861` to `1.4722`,
  but still trails the current ridge baseline by `6.144831`.
- A train-only blocked audit maps negative regime to `intraday` and
  non-negative regime to `activity`, reaching `81.67%` and `89.74%` local
  oracle hit in the two folds. The remaining failure is learning-contract
  inefficiency, not lack of visible structure.

## Scope

- Add drifted pretrade-book summaries and per-action target distance to every
  causal policy state.
- Preserve the exact state used by each rollout so immutable rationale evidence
  can reconstruct the model decision.
- Make Q-learning's next state use the executed current book drifted into the
  next timestamp.
- Replace the path-confounded contextual-ridge labels with fixed-iteration,
  train-only same-pretrade policy improvement.
- Preserve all existing actions, reward, folds, seeds, candidate authority,
  validation/test separation, and immutable historical Runs.

## Acceptance

- [x] Two identical market rows with different pretrade books expose different
      execution state and target distances.
- [x] Rollout rationale uses the exact state passed to the selector.
- [x] Every ridge action target at one timestamp shares one pretrade book.
- [x] Ridge policy improvement uses only the fold's train interval.
- [x] Baseline model evidence declares method, anchor, iterations, and training
      row reconciliation.
- [x] The bounded real fixture remains deterministic and publishes all prior
      artifacts without schema regression.
- [x] Full tests, wheel smoke, and browser evidence pass before completion.

## Findings

- The richer causal state raised the controlled fixture's validation mean net
  Sharpe from `9.965947` to `32.082895`.
- The policy reached `66.1111%` local-best hits and `1.4722 / 5` mean selected
  rank, but retained `0%` candidate usage.
- The new same-pretrade, train-only contextual baseline remained stronger:
  mean validation advantage was `-6.032028`. Adaptivity must not be promoted.
- Studio now projects the fixed four-iteration challenger contract, reconciled
  training rows and action labels, and the frozen-before-validation boundary.

## Verification

- `python -m unittest discover -s tests` — 157 tests in `924.078s`.
- RL environment and strict explorer subset — 8 tests in `215.151s`.
- Controlled real Run — succeeded in `29.643s` with all prior immutable
  artifacts plus the contextual-training contract.
- `python -m compileall`, `node --check`, and `git diff --check` — passed.
- Documentation link audit — 536 links resolved.
- Wheel smoke — all seven required RL template and Studio assets present.
- Browser QA — Training contract visible, zero horizontal overflow, and zero
  browser console errors.
