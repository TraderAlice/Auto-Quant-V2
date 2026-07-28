# OHLCV event-reaction field trial

- Status: `active`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/design/factor-diagnostics]].
- Field matrix: [[docs/trading-request-field-trials]].

## Outcome

Let an AutoQuant coworker answer one bounded, price-defined event question:
when NVDA opens at least 5% below its previous adjusted close, does entering at
the third session's close and holding five sessions have historical advantage
over explicit unconditional and market references?

## Context

Representative request:

> NVDA 如果某天相对前收跳空低开至少 5%，我想等两个完整交易日、第三天收盘买，
> 持有 5 个交易日。历史上有优势吗？只看这种价格事件，先别管财报标签和下单。

This intentionally avoids pretending that OHLCV proves an earnings event. The
event, entry clock, holding period, asset, and evidence meaning are all
observable from a content-locked daily price package. The trial asks whether
the current continuous-factor machinery can preserve conditional event
sampling, overlapping-event dependence, matched references, and event-level
evidence without changing the user's question.

## Scope

### In scope

- One causal OHLCV event defined from current open and previous adjusted close.
- One named asset, exact threshold/direction, two-session wait, third-session
  close entry, and five-session close-to-close holding return.
- Explicit event counts, timestamps, forward outcomes, unconditional same-asset
  reference, matched-date market reference, uncertainty, and overlap handling.
- One content-locked bounded real-data package and immutable evidence.
- Agent/CLI/Studio handoff with no claim that an event is an earnings release
  and no Order or trading authority.

### Out of scope

- Earnings labels, fundamentals, news, intraday execution, options, causal
  attribution, automatic threshold search, or an event taxonomy DSL.
- Treating a sparse event indicator as an ordinary continuous factor merely to
  reuse an IC objective.
- Claiming that historical conditional returns guarantee the next event.

## Acceptance

- [x] Preserve a strict English research brief before downloading or running
  data.
- [ ] Reproduce whether the current public route can or cannot answer the exact
  event-conditional question without a misleading success.
- [ ] If a Core gap exists, define the smallest event authority, immutable
  result, strict Explorer, and no-trading boundary.
- [ ] Deterministic tests cover timing, forward-return alignment, overlap,
  insufficient events, references, tamper rejection, and authority.
- [ ] A clean bounded Yahoo field trial returns a useful positive or negative
  conclusion with sample-size limitations.
- [ ] CLI, orientation, Studio, documentation, full regression, package smoke,
  commit, push, tag, and cleanliness pass.

## Work

- [x] Create and clarify the Project.
- [ ] Reproduce the current semantic boundary.
- [ ] Promote and implement only the reusable Workbench gap.
- [ ] Execute and interpret the clean field trial.
- [ ] Complete the release audit and close the plan.

## Findings and decisions

- 2026-07-29 — The first event trial is price-defined. Calling a price gap an
  earnings event without locked event observations would be false provenance.
- 2026-07-29 — The request fixes the event and trade clock. AutoQuant may own
  statistics and robustness diagnostics, but it may not search thresholds,
  entry delays, or holding periods.
- 2026-07-29 — Current single-asset Factor evaluation is a temporal
  rank/Pearson association contract. A constant sparse event selector has no
  defined correlation among selected observations; substituting gap magnitude
  would answer a different monotonic-association question.

## Verification

Pending.

## Progress log

- 2026-07-29 — Selected the first event-conditional trading request after the
  AutoQuant `0.8.0` one-leg Book Risk release.
- 2026-07-29 — Created and clarified the external
  `nvda-gap-reaction-third-day` Project before any data download or Run. The
  brief freezes event `open[t] / adjusted_close[t-1] - 1 <= -5%`, entry at
  `t+2` close, exit at `t+7` close, unconditional NVDA and matched-date SPY
  references, overlap disclosure, and no-trading authority.

## Completion

Pending.
