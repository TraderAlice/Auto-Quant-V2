# Governed RL Factor-Policy Study

## Question

Can a deterministic causal state representation help a fixed, bounded
Q-learning policy select factor mixtures across chronological regimes, after
the same target constraints, drift, turnover, and costs used by the portfolio
laboratory?

## Editable closure

Edit only `models/**`. Preserve:

```python
FEATURE_NAMES = (...)

def encode_state(state: dict[str, float]) -> list[float]:
    ...
```

The function receives one close-`t` scalar state. It must be pure,
deterministic, finite, bounded, and exactly aligned with `FEATURE_NAMES`.
Available fields are:

- `volume_regime`;
- `market_return_5`;
- `market_volatility_20`;
- `candidate_trailing_reward_10`;
- `activity_trailing_reward_10`;
- `intraday_trailing_reward_10`;
- `reversal_trailing_reward_10`;
- `previous_candidate`, `previous_activity`, `previous_intraday`,
  `previous_reversal`, and `previous_balanced`.

Do not read files, environment variables, clocks, randomness, or mutable global
state from the encoder. Test one representation hypothesis at a time.

## Fixed Judge authority

The Study declares `factors/**` and
`strategies/portfolio-mandate.json` as fixed, content-locked dependencies.
They are copied into the Session worktree for execution but are not editable
in this Study. The Judge independently checks
the `factors.candidate` pandas API,
alignment, determinism, numeric output, and prefix causality before using it.

The Judge owns:

- candidate, activity, intraday, reversal, and equal-blend governed signal
  sleeves;
- fixed percentile entry/exit hysteresis, inverse-volatility conviction,
  request-permitted long/cash, short/cash, or dollar-neutral target
  construction, context-only exclusions, and 0.30 asset caps;
- the shared trailing 60-row covariance forecast, 20-observation minimum,
  15% annualized volatility ceiling, and scale-down-only governance on every
  action sleeve before RL selection and reward;
- drift, 0.05 no-trade threshold, then shared final-book compliance where risk
  may override no-trade only through minimum proportional scale-down;
- full-notional 10bps costs and benchmark;
- next-bar reward and fixed quadratic risk penalty;
- linear Q-learning, 4 episodes, learning rate, discount, and exploration;
- seeds 11, 29, and 47;
- two expanding chronological train/validation/test folds;
- fixed-factor, training-selected expert, equal blend, and contextual-ridge
  baselines;
- all metrics, artifacts, and the validation-only promotion score.

Candidate code cannot improve by changing any evaluation rule above.
Each action's sleeve maintains its own causal intent history; RL chooses a
sleeve but never controls its signal triggers, position permissions, or
position/risk sizing.

## Evidence discipline

Inspect every seed and fold, seed dispersion, failures, action frequencies,
turnover/cost/risk, RL-minus-best-baseline, RL-minus-candidate-factor, and
candidate-action-frequency evidence. A positive RL Sharpe does not prove RL
added value.
Inspect action-run length, transition/retention, single-bar churn, Q-margin
ties, and the chosen-versus-runner-up rationale ledger. Q margins are
uncalibrated linear-model scores. Their exact feature decomposition explains
one frozen comparison only; it is not probability, confidence, causal
importance, or a selection metric. Realized outcomes conditioned on the chosen
action are descriptive and endogenous.
Inspect the same-pretrade one-step opportunity ledger separately. It replays
all five governed sleeves from the actual policy pretrade book for the same
next bar, so selected rank/regret and candidate-versus-balanced reward are
locally comparable after identical turnover, cost, no-trade, and risk rules.
The ex-post local best is known only after that bar, never propagates an
alternate path, and cannot enter training, KEEP/REVERT, or a trading decision.
Reconcile final-book risk coverage, pretrade breaches, risk-only overrides,
executed breaches, and execution reasons across every declared policy path;
these are implementation context and cannot select the editable encoder.

Any failed declared seed/fold fails the complete Run; successful seeds are
never averaged after silently dropping a failed trial.

Core counts unique encoder sources across the complete fixed-evaluation
Project family. It does not assign this fold/seed aggregate a single-path DSR:
the expanding folds and repeated seeds are dependent evidence, not one longer
return history. Treat the explicit unsupported reason as statistical honesty,
while continuing to inspect baseline advantage, dispersion, and failures.

Test-fold evidence never enters the objective. Repeatedly editing after reading
it consumes its holdout value; disclose that fact and obtain a new external
holdout before making a production claim.

This laboratory emits target-weight research only. It has no Broker,
OpenAlice UTA, order, or live-trading authority.
