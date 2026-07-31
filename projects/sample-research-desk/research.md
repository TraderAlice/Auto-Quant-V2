# Multi-Study Quantitative Research Desk

## About this sample

This checked-in Project is a deterministic, self-contained example of the
AutoQuant Factor → Portfolio → governed-RL research desk. Use it to inspect the
Project layout, ordinary pandas research surfaces, fixed Study authority,
immutable evidence, Agent orientation, and Studio before starting real work.

The repository default intentionally points here, but a genuinely new caller
question should normally become a new sibling Project created with
`aq project create . <project-id>` after the assignment is understood. Do not
rewrite this example to make unrelated research look like one continuing
question.

The immutable Factor Run
`run-20260729T075403870227Z-6b7cf30b394f` was produced by the clean released
AutoQuant `0.8.7` Harness at commit `0c9de83`. It is preserved as historical
evidence and records that identity in its RunResult; it is not relabeled as a
later execution.

The earlier surface-aligned Factor Run
`run-20260730T035544913232Z-4b19e3a63890` was produced by the clean `0.8.28`
Harness at commit `b5881b6`. The current Factor Run
`run-20260731T120304794599Z-6d6cdab313fe` was produced by the clean `0.9.0`
development Harness at commit `37b0029` after the sample protocol was brought
up to date. Neither development execution is relabeled as a released version.
The candidate declares only base-clock momentum because this sample dataset
has no higher-interval feature surface. Studio uses the latest ordinary
immutable Run as the current Factor Explorer. Portfolio and governed-RL
baselines are deliberately absent.

## Research brief and clarification

Before downloading data, editing research code, or running an evaluation,
rewrite the incoming assignment in this file as a bounded English research
brief. Make the decision to support, question, motivation, universe, horizon
or cadence, evidence, material constraints, evaluation meaning, expected
deliverable, assumptions, open questions, and proposed route explicit.

Use researcher judgment to choose and sequence Factor, Portfolio, and governed
RL work, but do not invent caller-owned intent. If an ambiguity could
materially change the research, record it here and ask the delegating Agent or
user. Repeat until the question is falsifiable and safe to bind into fixed
Study authority. The caller may use any language; English is the internal
working language of the AutoQuant desk.

## Purpose

Research one investment question through three distinct evidence lanes without
changing Project, request, universe, or dataset:

1. **Factor quality** — test whether a causal signal predicts forward returns
   across horizons, folds, regimes, assets, and style overlap.
2. **Portfolio quality** — test whether the same `factors/candidate.py`
   survives the request-bound tradable/context universe, direction, cash,
   mechanical signal state, sizing, causal covariance ceiling, constraints,
   drift, costs, risk, attribution, and a causal OHLCV liquidity-capacity
   envelope over the exact trade path.
3. **Governed RL policy** — bind the current candidate factor as a read-only
   sleeve and test whether a bounded adaptive state encoder adds value beyond
   that factor and fixed/contextual policies across every declared fold and
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

All three lanes bind the same fixed
`strategies/portfolio-mandate.json`. For a request-bound `decision-signal`,
Factor uses its tradable assets as the prediction/evaluation population while
the complete research universe remains available as causal input context.
Novel-factor and known-style validation claims retain complete-universe
evaluation. Exactly one tradable asset selects temporal evaluation; exactly
two symmetric, two-sided, dollar-neutral assets select temporal
first-minus-second factor/return contrast evaluation; four or more select
cross-sectional evaluation. Three assets require explicit caller-owned
relative-basket contrast weights. Portfolio and RL may never turn context
assets into implicit positions, learn around the requested direction, or bypass the shared
scale-down-only target and final executed-book portfolio-volatility ceiling.
Risk may override no-trade only by reducing the chosen book; the same
primitive governs both lanes. The RL lane also content-locks the current
`factors/candidate.py` bytes. Promoting a different factor makes prior RL
evidence stale; create fresh RL evidence or start a new RL Session. Factor
writers and active RL readers are surfaced as a concurrency conflict.

AutoQuant produces quantitative decision support only. Target weights,
historical actions, and Reports are not Broker orders, account state, or
OpenAlice trading approval.

When the RL lane is present, inspect whether action sleeves persist coherently
or churn one bar at a time, then inspect exact chosen-versus-runner-up linear-Q
rationales. Q margins are uncalibrated and feature contributions are not causal
importance. This behavior evidence is contextual only and cannot override the
validation objective or promote an encoder.
