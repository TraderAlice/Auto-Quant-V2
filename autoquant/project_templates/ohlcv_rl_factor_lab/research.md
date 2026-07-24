# Governed RL Factor-Policy Lab

## Purpose

Research causal state representations for a fixed factor-mixture policy and
test whether adaptation survives chronological folds, multiple seeds,
stateful signal-sleeve triggers, portfolio constraints, drift, costs, risk,
and simple non-RL baselines.

## Workflow

```bash
aq study inspect . --study ohlcv-rl-factor-policy --json
aq run execute . --study ohlcv-rl-factor-policy --json
aq session start . --study ohlcv-rl-factor-policy --json
```

Work only inside the returned Session worktree and edit `models/**`. State one
falsifiable representation hypothesis, evaluate it, and inspect seed/fold,
baseline, implementation, and model artifacts before accepting a KEEP.
`factors/**` is a fixed content-locked input to this Study; start a fresh RL
Session after promoting different factor bytes.
`strategies/portfolio-mandate.json` is the shared fixed position contract for
every RL action sleeve and is also not editable. Every sleeve receives the
same causal covariance forecast and one-sided volatility ceiling before the
policy may select it; editable state encoding cannot bypass position or risk
authority.
After selection, the shared accounting path also rechecks the actual
post-drift/no-trade book. Risk may override no-trade only through the minimum
proportional scale-down, identically to the Portfolio lane.

The fixed Judge owns all learning and evaluation authority. Test results are
audit evidence, not the promotion metric, and repeated inspection must be
reported as a limitation. Inspect the locked risk policy alongside action
constraints, baseline advantage, seed/fold dispersion, action frequency,
turnover, costs, final-book forecast coverage, risk-only overrides, and
executed breaches. Also inspect the one-step same-pretrade factor opportunity
audit: selected-versus-local-best rank/regret, candidate locally-best and
missed rates, and candidate-versus-balanced reward. The local best is ex-post
hindsight, not an oracle strategy or promotion input. AutoQuant has no
trading-account authority.
