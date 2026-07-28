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
- [x] Reproduce whether the current public route can or cannot answer the exact
  event-conditional question without a misleading success.
- [x] If a Core gap exists, define the smallest event authority, immutable
  result, strict Explorer, and no-trading boundary.
- [x] Deterministic tests cover timing, forward-return alignment, overlap,
  insufficient events, references, tamper rejection, and authority.
- [x] A clean bounded Yahoo field trial returns a useful positive or negative
  conclusion with sample-size limitations.
- [ ] CLI, orientation, Studio, documentation, full regression, package smoke,
  commit, push, tag, and cleanliness pass.

## Work

- [x] Create and clarify the Project.
- [x] Reproduce the current semantic boundary.
- [x] Promote and implement only the reusable Workbench gap.
- [x] Execute and interpret the clean field trial.
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
- 2026-07-29 — A public `ohlcv-factor-lab` intake accepted the exact request
  and a causal binary `t+2` candidate. Immutable Run
  `run-20260728T172110652639Z-d0e06d7c91ac` then failed because sparse
  validation correlation produced a null objective that the Judge converted
  with `float(None)`. Even a finite correlation would omit the event ledger,
  matched SPY returns, overlap policy, and conditional distribution.
- 2026-07-29 — The reusable gap is a fixed descriptive Study, not a new
  candidate family. `ohlcv-event-study-lab` has an empty editable closure,
  rejects Sessions, and executes one caller-frozen event/timing/reference
  policy directly.
- 2026-07-29 — The first public policy is intentionally narrow:
  adjusted-OHLCV downside opening gaps, delayed close-to-close returns, one
  matched asset, `keep-first-until-exit`, and a minimum useful event count.
  Separate horizon, Factor, Portfolio, and benchmark policies are rejected so
  the Run cannot carry two clocks or references.
- 2026-07-29 — The strict Event Explorer revalidates immutable file hashes,
  authority, artifact inventory, event timing, censoring, overlap eligibility,
  conditional/reference returns, distributions, uncertainty, metrics, and
  conclusion before CLI or Studio projection.
- 2026-07-29 — Researcher-owned method choices were frozen before retrieval:
  `keep-first-until-exit` and at least 12 primary events. Yahoo then supplied
  4,166 aligned adjusted NVDA/SPY sessions from 2010-01-04 through 2026-07-28.
- 2026-07-29 — Clean AutoQuant `0.8.1` Run
  `run-20260728T180552737821Z-6ca9339e863e` at commit `6e7cdcb` found 26
  complete and 22 primary events. Primary NVDA mean was `+3.2500%` versus
  unconditional `+0.9333%`; matched SPY excess averaged `+2.5770%`.
  `observed-advantage` is descriptive only: the absolute mean interval crosses
  zero and the sparse sample contains outcomes from `-17.71%` to `+21.10%`.
- 2026-07-29 — The patch-release cadence is authoritative for this increment:
  the public version is `0.8.1`, not `0.9.0`. The earlier untagged development
  Run remains preserved but is not release evidence.

## Verification

- Synthetic fixture: 6 qualifying events, 5 complete, 4 primary,
  1 overlap-excluded, and 1 right-censored.
- Strict semantic tamper test changes a rehashed entry timestamp and is
  rejected as `event-study.timing`.
- Zero-event input succeeds with `insufficient-events` rather than crashing or
  fabricating a result.
- External intake binds the derived authority, rejects raw OHLCV and parallel
  policy clocks, executes directly, rejects Session creation, and projects
  through CLI, orientation, and Studio.
- Clean field Run records Harness `0.8.1`, commit `6e7cdcb`, `dirty: false`,
  341 ms execution, and the exact dataset and dependency hashes.
- Strict Explorer, orientation, Studio snapshot, desktop browser, and 390px
  browser checks reconcile 26 complete / 22 primary events, expose only the
  read-only Event Explorer command, and produce no page-level horizontal
  overflow after the responsive table fix.

## Progress log

- 2026-07-29 — Selected the first event-conditional trading request after the
  AutoQuant `0.8.0` one-leg Book Risk release.
- 2026-07-29 — Created and clarified the external
  `nvda-gap-reaction-third-day` Project before any data download or Run. The
  brief freezes event `open[t] / adjusted_close[t-1] - 1 <= -5%`, entry at
  `t+2` close, exit at `t+7` close, unconditional NVDA and matched-date SPY
  references, overlap disclosure, and no-trading authority.
- 2026-07-29 — Preserved the exact public-route reproduction and immutable
  failure in sibling Project `nvda-gap-factor-route-repro`; promoted the
  smallest reusable event-study need to both Projects' `framework-needs.md`.
- 2026-07-29 — Implemented the fixed event route and public read surfaces;
  long-history Yahoo evidence and release audit remained pending.
- 2026-07-29 — Completed the long-history `0.8.1` clean field trial and
  human-facing Studio audit. Full regression, package smoke, final commit/push,
  tag, and cleanliness remain pending.

## Completion

Pending.
