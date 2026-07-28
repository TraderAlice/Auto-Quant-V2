# Global ETF calendar-month allocation field trial

- Status: `active`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/caller-owned-portfolio-research-policy]],
  [[docs/design/caller-owned-decision-cadence]],
  [[docs/design/market-clock-decision-anchors]], and
  [[docs/design/research-program-orchestration]].
- Field matrix: [[docs/trading-request-field-trials]].

## Outcome

Let an AutoQuant coworker receive one caller-style diversified ETF allocation
question, preserve a true calendar-month review schedule, and return either a
verified Factor-to-Portfolio target-weight handoff or an explicit evidence
gate without silently translating “monthly” into an arbitrary count of bars.

## Context

Representative request:

> 我想拿美股、海外、债券、黄金和商品 ETF 做个省心组合，每月看一次，
> 年化波动尽量压在 10%，单个不超过 30%，现在怎么配？

AutoQuant has real-data evidence for cross-sectional selection and for
Portfolio mechanics, but no completed real-data request has progressed from a
clarified diversified-allocation question through Factor qualification into a
current governed target-weight handoff. The current request contract expresses
only every-N-bars cadence. That is not equivalent to the last observed market
session of each calendar month and can drift through the calendar depending on
dataset start.

## Scope

### In scope

- Freeze the exact ETF universe, long/cash authority, primary horizon,
  benchmark, calendar-month review rule, volatility ceiling, caps, costs,
  no-trade band, and reference capital before data retrieval.
- Use provider-adjusted daily OHLCV on a verified XNYS session calendar and
  preserve ETF/fund asset class.
- Reproduce the current public request/intake boundary without approximating
  calendar months as 21 bars.
- If proven necessary, replace the pre-1.0 every-bars-only request cadence
  contract with one small discriminated schedule contract shared by Portfolio
  and governed RL.
- Run bounded Factor research first; enter Portfolio only if frozen
  qualification permits it.
- Expose the latest historical scheduled/held state and target-weight evidence
  without claiming account or trading authority.

### Out of scope

- Fundamental ETF holdings, fees, taxes, FX conversion, bid/ask impact,
  distributions beyond provider-adjusted price claims, or live account state.
- Optimizing the universe, risk target, cap, cadence, or cost assumptions after
  inspecting results.
- Forcing a positive Factor result merely to exercise Portfolio.
- Orders, TPSL, Broker integration, or authenticated OpenAlice UTA actions.
- A general cron/calendar expression language.

## Acceptance

- [ ] An English Project brief freezes caller-owned meaning before retrieval or
  execution.
- [ ] The current public route is reproduced and refuses any cadence or asset
  semantics it cannot represent exactly.
- [ ] Any Workbench change implements the smallest general calendar-month
  schedule contract across request, Mandate, Portfolio/RL execution, evidence,
  CLI, and Studio.
- [ ] A bounded real-data Project terminates with verified Factor/Portfolio
  evidence or a scientifically useful gate.
- [ ] Tests, docs, package smoke, versioning, commit/push, and repository
  cleanliness pass in proportion to the change.

## Work

- [ ] Create and clarify the representative Project.
- [ ] Acquire and audit one bounded provider snapshot.
- [ ] Reproduce the current public boundary.
- [ ] Implement only field-proven reusable changes.
- [ ] Execute and interpret the clean field trial.
- [ ] Complete release or explicit-boundary audit and close the plan.

## Findings and decisions

- 2026-07-29 — “Monthly” is fixed as the final observed XNYS session in each
  calendar month. It is caller-owned decision timing, not permission for the
  researcher to substitute every 21 rows from an arbitrary start.
- 2026-07-29 — The representative universe is SPY, QQQ, IWM, EFA, EEM, TLT,
  IEF, GLD, and DBC. Every asset is a long-only ETF research leg; cash is
  allowed. The question does not authorize hidden security selection.

## Verification

Pending.

## Progress log

- 2026-07-29 — Plan created after the `v0.8.2` observed-hourly Factor release.

## Completion

Pending.
