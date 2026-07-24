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
- `activity_trailing_reward_10`;
- `intraday_trailing_reward_10`;
- `reversal_trailing_reward_10`;
- `previous_activity`, `previous_intraday`, `previous_reversal`, and
  `previous_balanced`.

Do not read files, environment variables, clocks, randomness, or mutable global
state from the encoder. Test one representation hypothesis at a time.

## Fixed Judge authority

The Judge owns:

- activity, intraday, reversal, and equal-blend governed signal sleeves;
- fixed percentile entry/exit hysteresis, inverse-volatility conviction,
  gross-one dollar-neutral target construction, and 0.30 asset caps;
- drift, 0.05 no-trade threshold, full-notional 10bps costs, and benchmark;
- next-bar reward and fixed quadratic risk penalty;
- linear Q-learning, 4 episodes, learning rate, discount, and exploration;
- seeds 11, 29, and 47;
- two expanding chronological train/validation/test folds;
- fixed-factor, training-selected expert, equal blend, and contextual-ridge
  baselines;
- all metrics, artifacts, and the validation-only promotion score.

Candidate code cannot improve by changing any evaluation rule above.
Each action's sleeve maintains its own causal intent history; RL chooses a
sleeve but never controls its signal triggers or position sizing.

## Evidence discipline

Inspect every seed and fold, seed dispersion, failures, action frequencies,
turnover/cost/risk, and RL-minus-best-baseline evidence. A positive RL Sharpe
does not prove RL added value.

Any failed declared seed/fold fails the complete Run; successful seeds are
never averaged after silently dropping a failed trial.

Test-fold evidence never enters the objective. Repeatedly editing after reading
it consumes its holdout value; disclose that fact and obtain a new external
holdout before making a production claim.

This laboratory emits target-weight research only. It has no Broker,
OpenAlice UTA, order, or live-trading authority.
