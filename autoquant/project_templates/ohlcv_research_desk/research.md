# Multi-Study Quantitative Research Desk

## Purpose

Research one investment question through three distinct evidence lanes without
changing Project, request, universe, or dataset:

1. **Factor quality** — test whether a causal cross-sectional signal predicts
   forward returns across horizons, folds, regimes, assets, and style overlap.
2. **Portfolio quality** — test whether the same `factors/candidate.py`
   survives mechanical signal state, sizing, constraints, drift, costs, risk,
   and attribution.
3. **Governed RL policy** — test whether a bounded adaptive state encoder adds
   value beyond fixed and contextual policies across every declared fold and
   seed.

## Working order

```bash
aq project program . --json
aq run execute . --study ohlcv-factor-quality --json
aq session start . --study ohlcv-factor-quality --request request.json --json
aq run execute . --study ohlcv-portfolio-quality --json
aq session start . --study ohlcv-portfolio-quality --request request.json --json
aq run execute . --study ohlcv-rl-factor-policy --json
aq session start . --study ohlcv-rl-factor-policy --request request.json --json
```

Factor and Portfolio Sessions edit the same source closure and must be
sequenced. Promote or stop one line of research before starting the other.

## Evidence boundary

The three lanes do not collapse into one score. A factor can predict but fail
after costs; a portfolio can be mechanically sound without proving a raw
factor claim; an RL policy can have high absolute Sharpe yet add no value over
a simple baseline.

The V1 RL lane uses fixed reference factor-mixture sleeves. It does not consume
the promoted arbitrary candidate factor. Treat it as an adaptivity challenge,
not as proof that the discovered factor has been fused into RL.

AutoQuant produces quantitative decision support only. Target weights,
historical actions, and Reports are not Broker orders, account state, or
OpenAlice trading approval.
