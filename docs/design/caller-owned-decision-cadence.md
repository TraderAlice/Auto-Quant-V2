# Caller-owned decision cadence

Status: implemented.

Related: [[docs/design/configurable-session-interval-inputs]],
[[docs/design/caller-owned-portfolio-research-policy]],
[[docs/design/request-bound-portfolio-mandates]],
[[docs/design/signal-policy-and-attribution]],
[[docs/design/executed-book-risk-compliance]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/program-research-dossiers]].

## Purpose

The collaborating workbench owns how often the delegated strategy is allowed
to reconsider its research position; AutoQuant owns deterministic mechanics
and evidence on every intervening base bar.

```text
Research Request.portfolioPolicy.decisionEveryBars + decisionAnchor
→ content-addressed Portfolio Mandate decision schedule
→ mechanical signal / target eligibility
→ Portfolio execution and governed-RL action availability
→ immutable Run / Report / Dossier evidence
```

Candidate factor and encoder code cannot edit this chain.

## Request and Mandate contract

A complete caller `portfolioPolicy` includes:

```json
{
  "decisionEveryBars": 4,
  "decisionAnchor": "session-start"
}
```

The value is a non-boolean integer in `[1, 252]`. When Portfolio policy is
omitted, Core inserts the explicit reference default `1`.

The Mandate materializes:

```json
{
  "decisionPolicy": {
    "source": "caller-supplied",
    "kind": "every-bars",
    "bars": 4,
    "anchor": "session-start"
  }
}
```

`dataset-start` uses the first timestamp of the complete locked base panel.
`session-start` restarts at the first completed bar of every verified XNYS
regular session and is rejected for other inputs. Neither evaluation splits,
Study Sessions, nor Runs can reset or reinterpret the schedule. See
[[docs/design/market-clock-decision-anchors]].

## Mechanical signal and execution semantics

On an eligible bar, Core:

1. observes the completed causal factor cross-section;
2. advances entry/hold/exit/reversal signal states;
3. reconstructs capped conviction/inverse-volatility targets;
4. applies the one-sided proposed-book risk governor;
5. allows ordinary execution subject to the no-trade band.

On an ineligible bar:

- factor values may remain observable diagnostics;
- signal state and proposed target stay at their preceding values;
- ordinary execution is forbidden even if drift made the old target distant;
- the existing final-book covariance check still runs;
- only a scale-down/flat risk repair may trade.

This keeps three separate concepts honest:

- base cadence: when new OHLCV information exists;
- decision cadence: when ordinary strategy intent may change;
- no-trade band: whether one eligible proposed trade is large enough.

## Governed RL semantics

Every factor sleeve receives the same cadence-constrained mechanical target
surface. On an eligible bar the fixed policy may choose any declared sleeve.
On an ineligible bar the only available action is the previously selected
sleeve.

Q-learning uses that same action availability:

- eligible current/next state: select or bootstrap over all fixed actions;
- ineligible current/next state: act or bootstrap only through the held action.

Per-base-bar return, cost, risk, and reward accounting continues on every bar.
The policy cannot receive a hidden off-schedule switching privilege, and simple
baselines obey the identical mask.

## Evidence and handoff

Daily Portfolio/RL evidence records:

- `decision_eligible`;
- `decision_every_bars`;
- whether a scheduled hold or risk-only override occurred.

Signal and decision ledgers distinguish a schedule hold from hysteresis, a
small-trade no-op, missing factor evidence, and a risk repair. Explorer,
Studio, Reports, and Dossiers state whether cadence came from the caller or
the documented reference default. They retain
`quantitative-decision-support` and `tradingAuthority: none`.

## Invariants

1. One complete locked-panel mask with the caller's exact anchor is shared by
   every lane and split.
2. Signal state and ordinary targets do not change on ineligible bars.
3. Ordinary trades never occur on ineligible bars.
4. Risk repair may only reduce or flatten an off-schedule book.
5. RL action choice and Q bootstrap use the exact same availability mask.
6. Candidate source cannot tune cadence or reinterpret a scheduled hold.
7. Changing cadence changes immutable research identity, never prior evidence.

## Known limits

- V1 expresses dataset-start and verified XNYS session-start only; it does not
  express session-close, weekday, clock-time, event, or arbitrary phase-offset
  schedules.
- Cadence is a research assumption, not a live scheduler, exchange order, TPSL,
  or OpenAlice UTA authorization.
