# RL train-only learning stability

- Status: `completed`
- Updated: `2026-07-25`
- Related design:
  [[docs/design/rl-factor-policy-lab]],
  [[docs/design/causal-rl-policy-state-and-baseline]], and
  [[docs/design/rl-incremental-value-attribution]].

## Outcome

The fixed linear-Q learner no longer turns an otherwise useful causal state
encoder into a lucky-seed result. Harness-owned learning parameters are frozen
from a blocked train-only audit before outer validation and are preserved as
immutable learning-contract provenance in every new RL Run.

## Selection discipline

Five configurations were declared before inspection:

1. current 4 episodes, discount `0.85`;
2. 12 episodes, discount `0.85`;
3. 12 episodes, discount `0.30`;
4. 12 episodes, discount `0.00`; and
5. conservative 12 episodes, discount `0.30`, learning rate `0.02`,
   epsilon `0.15 → 0.01`.

For each outer fold, only its training interval was split into a chronological
70% fit / 30% blocked audit. Every candidate ran seeds 11, 29, and 47. The
comparison baseline was a contextual ridge trained only on the same fit rows.
Configuration choice used worst-seed advantage, mean advantage, within-fold
seed dispersion, and pairwise action mismatch in that order. Outer validation
and test were not inspected until the choice was frozen.

## Train-only evidence

The selected conservative configuration:

- increased mean blocked-audit advantage from `5.146251` to `9.566273`;
- increased minimum seed advantage from `-22.326387` to `+3.219813`;
- reduced mean within-fold seed Sharpe dispersion from `6.166504` to `0`;
- reduced mean pairwise action mismatch from `45.94%` to `0%`;
- remained adaptive rather than collapsing to one sleeve:
  fold 1 used balanced/intraday `70% / 30%`, and fold 2 used
  `46.15% / 53.85%`.

## Frozen outer evidence

Controlled Run `run-20260725T011505096710Z-cf52610466be` used the frozen
configuration without further tuning:

- validation mean net Sharpe: `38.759284`;
- validation advantage versus the selected mechanical baseline: `+0.644361`;
- fold advantages: `+0.857647` and `+0.431075`;
- within each fold, all three seeds produced identical validation behavior;
- mean-trial-path gross / incremental cost / net active return:
  `+0.003746 / +0.000365 / +0.003381`;
- annualized active return / tracking error / information ratio:
  `1.4201% / 0.6046% / 2.2317`;
- active-day rate / conditional active-day win:
  `15.0% / 72.22%`;
- relative maximum drawdown: `-0.1005%`.

Test advantage was `+0.995650`, but remains visible audit evidence and did not
select the configuration.

## Acceptance

- [x] Candidate configurations are predeclared and bounded.
- [x] Hyperparameter choice uses only an outer-train blocked audit.
- [x] Every declared seed participates in every comparison.
- [x] The selected behavior is not a fixed-action collapse.
- [x] The configuration is frozen before outer validation.
- [x] Both outer validation folds beat their validation-selected mechanical
      baseline.
- [x] New Runs preserve exact learning-contract provenance.
- [x] Legacy Runs remain readable without fabricated provenance.

## Verification

- Fresh-template controlled Run — succeeded in `47.950s`; strict `aq run rl`
  projection preserved the complete learning contract.
- Deterministic duplicate-template Run test — 1 test in `91.179s`.
- Governed campaign, KEEP, nondeterminism, and failed-seed regression — 1 test
  in `117.913s`.
- Strict projection, legacy compatibility, rehashed learning-contract
  tampering, and existing artifact-corruption checks — 2 tests in `94.592s`.
- Final complete-action-path consensus projection — 1 test in `47.537s`.
- Studio HTTP/assets regression — 7 tests in `3.676s`.
- Compile, JavaScript syntax, diff checks, and 547 documentation double-links
  — passed.
- Wheel smoke — fixed Judge, learner, program, and all three Studio assets are
  packaged.
- Browser QA — positive decision brief, `train-only frozen learner`,
  within-fold seed `σ = 0`, `2/2` exact-consensus folds, zero horizontal
  overflow, and zero console warnings/errors.
