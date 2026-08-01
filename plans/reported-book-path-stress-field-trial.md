# Reported-book historical path-stress field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.15`
- Related design: [[docs/design/reported-position-book-risk]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/agent-native-market-data-acquisition]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove whether a fresh quantitative coworker can turn one explicit reported
portfolio into a fixed historical path-stress answer: identify the worst
non-overlapping 20-session loss episodes, preserve buy-and-hold drift from
each episode's fixed opening weights, attribute every loss exactly to the
named holdings, and return useful descriptive evidence without inventing a
scenario, optimization, Order, or trading recommendation.

The exact released `0.9.14` wheel is the baseline. `0.9.15` will contain only
the smallest coherent reusable repair justified by the untouched assignment.
Breaking replacement is allowed when current V2 semantics are wrong; no
compatibility layer or migration promise is required.

## Field assignment

Delegate this fully bounded caller-style question:

> My reported model book is 40% QQQ, 25% NVDA, 20% TLT, and 15% USD cash as of
> 2026-07-31. Over completed XNYS daily sessions from 2010-01-01 through
> 2026-07-31, find its five worst non-overlapping 20-session historical loss
> episodes. For each episode, start from those exact weights, buy and hold the
> three assets without rebalancing, keep cash flat, and measure close-to-close
> loss through the twentieth following completed session. Tell me how much the
> book lost, which holding contributed most, whether the same holding dominated
> all five episodes, and what the path looked like inside each window. Use
> split-adjusted prices with one independent provider route as coverage
> evidence. This is historical decision support only; do not authenticate the
> account, optimize a replacement book, or create an Order or trading advice.

The research interpretation is frozen before the worker starts:

- An eligible start requires the start close and all 20 following aligned
  completed sessions; the endpoint is therefore exactly `t + 20`.
- Each window initializes the caller weights at its start close. Asset
  contribution is opening weight times the asset's cumulative return from the
  start close; cash contribution is zero. Contributions must reconcile exactly
  to book loss before any ranking.
- The within-window path uses the same fixed opening units and reports the
  worst interim book loss and when it occurred. No daily constant-weight
  rebalancing is allowed.
- Rank all complete windows by terminal book loss, take the worst, then admit
  the next-worst window only when its inclusive `[start, end]` interval does
  not overlap any already admitted episode. Continue until five are selected
  or the history is exhausted. Ties resolve by earlier start date.
- Provider end dates may stop before the requested upper bound; disclose the
  actual final completed common session and never fabricate future bars.

## Scope

### In scope

- One isolated fresh Grok 4.5 worker using the exact installed `0.9.14` wheel,
  a new empty Workspace, generated Skills, public CLI/schema surfaces, and
  provider networking.
- English brief quality, demand-led task-local acquisition, route selection,
  current capability recognition, immutable evidence, attribution accounting,
  final handoff, and stop behavior.
- Exact transcript, filesystem, provider, retry, Project, Study, Session, Run,
  Report, and manual-artifact inventories.
- The smallest fixed Study/Core, strict Explorer, CLI, Studio, Skill, or
  documentation repair for each reproduced material Workbench defect.
- A fresh candidate-wheel replay and complete release audit before tagging
  `v0.9.15` when a product change is justified.

### Out of scope

- Forecasting future stress, causal labels for historical episodes, macro or
  news event attribution, scenario generation, Monte Carlo, expected shortfall,
  changing weights, tax lots, live positions, execution, Orders, or TP/SL.
- Searching window length, episode count, overlap rules, weights, universe, or
  adjustment meaning.
- A central market-data inventory, shared mutable cache authority, automatic
  refresh, or any OpenAlice version change. OpenAlice remains on `0.8.31`.

## Acceptance

- [ ] A fresh worker begins with zero staged OHLCV, writes the exact English
      brief first, and acquires one complete task-local package plus independent
      provider evidence without consulting prior Projects or trials.
- [ ] The worker preserves reported-position truth, fixed opening weights,
      20-following-session timing, buy-and-hold drift, cash, adjustment meaning,
      non-overlap rule, requested history, and no-trading authority.
- [ ] Exactly one appropriate Project and one fixed immutable Run answer the
      task, or the baseline stops with a useful explicit capability boundary;
      no generic editable factor or parameter-search Session is manufactured.
- [ ] Final evidence enumerates all eligible windows, the five deterministic
      episodes, terminal and worst-interim book losses, exact per-holding
      contributions, reconciliation, dominant holding, and cross-episode
      dominance conclusion.
- [ ] Strict CLI and Studio projection independently reject altered authority,
      episode selection, returns, attribution, or artifact inventory.
- [ ] Every material baseline failure is retained and classified; only a
      reproduced reusable Workbench defect enters the candidate release.
- [ ] A fresh candidate worker completes the unchanged assignment without
      source/private-trial access, manual post-Run quantitative authority, or
      trading overclaim.
- [ ] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and no-local-override clean-clone smokes pass
      before publication.

## Work

- [x] Define and index the fixed historical path-stress assignment.
- [ ] Build an isolated installed-`0.9.14` baseline desk with zero staged data.
- [ ] Run and audit one fresh baseline worker without coaching.
- [ ] Admit and implement only reproduced reusable product friction.
- [ ] Replay the unchanged task with a fresh candidate-wheel worker.
- [ ] Complete the `v0.9.15` release audit and publish the tag.

## Findings and decisions

- 2026-08-01 — Price Event research was not selected: `v0.9.13` already
  supplied a fresh zero-data Korean Event trial with a scientifically weak but
  useful conclusion. Historical book-path stress is materially different from
  both that event route and `v0.9.14` covariance sizing.
- 2026-08-01 — The caller fixes every selection degree of freedom. The method
  may enumerate history and select the declared worst windows, but it may not
  tune horizon, count, weights, overlap, assets, or price meaning after seeing
  results.
- 2026-08-01 — Each replay owns a complete task-local package. Existing market
  bytes may not constrain or silently satisfy the assignment; duplicate bytes
  remain acceptable evidence isolation.
- 2026-08-01 — No implementation is authorized before the released baseline
  worker establishes whether public Workbench surfaces already support a
  truthful immutable answer or expose a concrete method gap.

## Verification

Pending baseline worker evidence.

## Progress log

- 2026-08-01 — Plan activated from clean released `v0.9.14`; OpenAlice remains
  independently pinned to `v0.8.31`.

## Completion

Complete this section only after every acceptance item is independently
verified and the release, if any, is published.
