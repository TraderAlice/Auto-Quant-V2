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

- [x] An English Project brief freezes caller-owned meaning before retrieval or
  execution.
- [x] The current public route is reproduced and refuses any cadence or asset
  semantics it cannot represent exactly.
- [x] Any Workbench change implements the smallest general calendar-month
  schedule contract across request, Mandate, Portfolio/RL execution, evidence,
  CLI, and Studio.
- [x] A bounded real-data Project terminates with verified Factor/Portfolio
  evidence or a scientifically useful gate.
- [ ] Tests, docs, package smoke, versioning, commit/push, and repository
  cleanliness pass in proportion to the change.

## Work

- [x] Create and clarify the representative Project.
- [x] Acquire and audit one bounded provider snapshot.
- [x] Reproduce the current public boundary.
- [x] Implement only field-proven reusable changes.
- [x] Execute and interpret the field trial before the clean release replay.
- [ ] Complete release or explicit-boundary audit and close the plan.

## Findings and decisions

- 2026-07-29 — “Monthly” is fixed as the final observed XNYS session in each
  calendar month. It is caller-owned decision timing, not permission for the
  researcher to substitute every 21 rows from an arbitrary start.
- 2026-07-29 — The representative universe is SPY, QQQ, IWM, EFA, EEM, TLT,
  IEF, GLD, and DBC. Every asset is a long-only ETF research leg; cash is
  allowed. The question does not authorize hidden security selection.
- 2026-07-29 — Yahoo returned all nine symbols as `ETF`, with 4,922 exact
  common observed dates from 2007-01-03 through 2026-07-28 and no zero-volume
  rows. The package preserves provider-adjusted OHLC and provider-reported
  volume under XNYS session authority.
- 2026-07-29 — The unchanged `0.8.2` public intake rejected only the honest
  calendar schedule surface: `decisionSchedule` is unknown while
  `decisionEveryBars` and `decisionAnchor` are required. The operation left no
  partial Project. Data and fund asset-class semantics did not need to be
  weakened to reproduce the gap.
- 2026-07-29 — `decisionSchedule` is now one discriminated object:
  `every-bars` retains bounded dataset/session anchors and
  `calendar-month-end` uses official XNYS daily sessions. The Mandate,
  Portfolio, governed RL, CSV evidence, Explorers, CLI, Studio, Reports, and
  Dossiers share the exact schedule. Calendar rows leave flat bars/anchor
  details empty rather than using a fake `21`.
- 2026-07-29 — The real Portfolio decision ledger contained 44,298 asset rows
  and was about 34 MiB. The successful Run exposed the former 32 MiB Explorer
  byte ceiling as too small for a legitimate bounded panel. Portfolio Explorer
  now permits at most 64 MiB while preserving row, hash, and reconciliation
  limits.
- 2026-07-29 — Off-schedule proposed-target risk evidence explicitly marks its
  governor `diagnostic_disabled`; final execution can still perform the
  mandatory scale-down-only risk repair. Explorer now exempts only that
  explicit proposed diagnostic from the ceiling assertion and continues to
  reconcile final executed-book risk.
- 2026-07-29 — The full nine-asset, 4,922-session governed RL lane reached its
  fixed 120-second timeout and terminated with `judge.timeout`. The budget is
  not widened again: RL is optional here and the successful Factor-to-Portfolio
  handoff remains the supported interactive route.
- 2026-07-29 — The first clean `0.8.3` Portfolio report exposed one more
  deterministic boundary: its non-alphabetical effective-cap map rendered in
  universe order before JSON persistence and alphabetical order after the
  canonical `sort_keys` round trip. `0.8.4` sorts named cap/role maps in the
  renderer and adds a direct order-invariance regression test.

## Verification

- Provider audit: nine Yahoo `ETF` series, 4,922 aligned daily observations,
  2007-01-03 through 2026-07-28, zero zero-volume rows.
- Public `aq project intake ... --template ohlcv-research-desk --json`
  returned `validation.failed` for the exact calendar schedule fields and
  created no Project directory.
- Upgraded public intake created
  `global-etf-calendar-month-allocation-v083` with the exact schedule.
- Factor Run `run-20260728T214548865583Z-6d94dc9a5d0f` completed in 53,866 ms
  with primary validation IC `0.031360`.
- Portfolio Run `run-20260728T214656702102Z-02e5fa470a22` completed in
  123,955 ms with validation net Sharpe `0.618792`; strict Explorer confirms
  234 eligible rows, latest eligible 2026-06-30, and an ineligible July
  endpoint.
- Latest accountable 2026-07-27 book: IWM `0.297353`, TLT `0.297400`, IEF
  `0.299379`, cash `0.105867`; scheduled target remains 30%/30%/30%/10% and
  no ordinary rebalance is due.
- Governed RL Run `run-20260728T215047604954Z-f5cb1ac946d0` terminated at the
  exact 120-second budget with a structured timeout.
- Focused verification so far: Mandate/calendar tests 12/12; Portfolio Lab
  16/16; Portfolio Explorer 21/21; RL Explorer 2/2; Report/Dossier/CLI 34/34;
  Studio 7/7; every-bars daily/intraday and calendar intake end-to-end checks
  pass.
- Full regression after the final assertion update: 265/265 in 1,470.892 s.
- Fresh Python 3.11 wheel smoke: `auto-quant==0.8.3`, 48 public commands,
  both schedule variants visible in the public request schema, and the official
  month-end mask returns June 30 eligible / July 28 ineligible under Pandas 3.
- Report-fix verification: direct non-alphabetical mapping-order regression,
  complete Report tests, Dossier tests, and caller-owned
  Portfolio/RL/Report end-to-end flow pass (24 tests in 196.943 s).
- Final `0.8.4` full regression: 266/266 in 1,453.832 s.
- Fresh `0.8.4` Python 3.11 wheel smoke: 48 public commands, both schedule
  variants in the request schema, and June-eligible/July-incomplete mask
  behavior under Pandas 3.

## Progress log

- 2026-07-29 — Plan created after the `v0.8.2` observed-hourly Factor release.
- 2026-07-29 — Created a blank Project and froze the exact English allocation,
  cadence, risk, data, evidence, and no-trading contract before retrieval.
- 2026-07-29 — Retrieved and hashed the adjusted Yahoo snapshot, then
  reproduced the every-bars-only intake boundary without approximating
  calendar months.
- 2026-07-29 — Implemented and field-ran official XNYS calendar-month
  scheduling. Raised one evidence byte limit and corrected one
  diagnostic-versus-executed-risk Explorer assumption only after the real Run
  demonstrated each need.
- 2026-07-29 — Published a Factor handoff from the dirty development Harness.
  A later Portfolio report-rendering fix correctly made the open Session
  Harness-stale. Final Reports/Dossier will therefore be replayed only after
  the `0.8.3` code is tested and committed cleanly.

## Completion

Pending.
