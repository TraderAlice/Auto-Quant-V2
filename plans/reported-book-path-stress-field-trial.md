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

- [x] A fresh worker begins with zero staged OHLCV, writes the exact English
      brief first, and acquires one complete task-local package plus independent
      provider evidence without consulting prior Projects or trials.
- [x] The worker preserves reported-position truth, fixed opening weights,
      20-following-session timing, buy-and-hold drift, cash, adjustment meaning,
      non-overlap rule, requested history, and no-trading authority.
- [x] Exactly one appropriate Project and one fixed immutable Run answer the
      task, or the baseline stops with a useful explicit capability boundary;
      no generic editable factor or parameter-search Session is manufactured.
- [x] Final evidence enumerates all eligible windows, the five deterministic
      episodes, terminal and worst-interim book losses, exact per-holding
      contributions, reconciliation, dominant holding, and cross-episode
      dominance conclusion.
- [x] Strict CLI and Studio projection independently reject altered authority,
      episode selection, returns, attribution, or artifact inventory.
- [x] Every material baseline failure is retained and classified; only a
      reproduced reusable Workbench defect enters the candidate release.
- [x] A fresh candidate worker completes the unchanged assignment without
      source/private-trial access, manual post-Run quantitative authority, or
      trading overclaim.
- [ ] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and no-local-override clean-clone smokes pass
      before publication.

## Work

- [x] Define and index the fixed historical path-stress assignment.
- [x] Build an isolated installed-`0.9.14` baseline desk with zero staged data.
- [x] Run and audit one fresh baseline worker without coaching.
- [x] Admit and implement only reproduced reusable product friction.
- [x] Replay the unchanged task with a fresh candidate-wheel worker.
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
- 2026-08-01 — Baseline session
  `019fbbf2-fcc4-75c1-ba13-b9caa87d559e` independently stopped at a useful
  boundary with zero OHLCV, Projects, Studies, Sessions, Runs, or Reports. It
  preserved the brief first and refused to relabel ad hoc pandas arithmetic as
  immutable Workbench evidence.
- 2026-08-01 — The exact installed `0.9.14` surfaces reproduce one coherent
  method gap. Book Risk uses daily constant-weight trailing paths and covariance
  risk contribution; the caller requires window-start fixed units, exhaustive
  historical 20-following-session endpoints, greedy non-overlap selection,
  terminal-loss ranking, and return contribution. Changing Book Risk lookbacks
  cannot make those contracts equivalent.
- 2026-08-01 — Admit one narrow fixed `ohlcv-book-path-stress-lab`, not a
  generic scenario engine. The caller must freeze weights, history, horizon,
  episode count, overlap policy, calendar, and adjustment meaning before the
  Run. Core owns deterministic enumeration, selection, attribution,
  reconciliation, immutable artifacts, strict inspection, and projection.
- 2026-08-01 — Candidate Core now freezes `positionSnapshot` plus the narrow
  `pathStressPolicy`, requires split-adjusted daily intake, and creates a
  no-edit/no-Session `ohlcv-book-path-stress` Study. Its Judge emits exactly
  five artifacts covering all complete windows, selected episodes, terminal
  attribution, full selected paths, and the bounded report.
- 2026-08-01 — `aq run book-path-stress` independently reconstructs greedy
  selection, every path return, cash, contribution, dominant holding, report,
  and metrics. A semantic tamper remains rejected even after the attacker
  recomputes the ordinary Run file manifest. Orientation and Studio expose the
  same strict read model and terminal historical-only boundary.
- 2026-08-01 — Candidate session
  `019fbc15-55e6-7740-966e-9ee1f1b7d007` completed the unchanged assignment
  from the exact candidate wheel without source or prior-trial access. Its
  English brief preceded retrieval; it created one Project, one fixed Study,
  one successful Run, one Report, no Session, and one caller-facing outward
  Markdown handoff.
- 2026-08-01 — The worker preserved a failed full-history Nasdaq attempt as
  evidence, then acquired a bounded 2020–2026 Nasdaq overlap package while
  retaining Yahoo's complete 2010–2026 split-adjusted panel as formal
  authority. Provider limitations therefore did not narrow or silently alter
  the task.
- 2026-08-01 — The verified Run enumerated 4,149 complete windows. The worst
  selected episode was 2020-02-19 through 2020-03-18 at `-19.2415703%`, with
  QQQ as dominant loss contributor. NVDA dominated the remaining four, so the
  same holding did not dominate all five.
- 2026-08-01 — The first 395-test release run exposed one repository-wide
  template invariant missed by focused tests: the new Path Stress
  `research.md` lacked the standard `Research brief and clarification` start
  gate. Add the same clarification-first instruction used by every built-in
  Lab and retain the universal template test as the regression contract. This
  repair changes no Study arithmetic or candidate evidence.

## Verification

Baseline trial:
`/Users/ame/autoquant-v0915-path-stress-baseline`. The exact released wheel
SHA-256 is
`d21d3cc3b86eebc18d4a3805a71507f316c7eef8a15bf4e70bbcf096d11af553`;
Python is 3.11.14 and the installed CLI reports `aq 0.9.14`. The 262-line
transcript, assignment, English brief, copied public-contract evidence, and
caller-facing boundary handoff are preserved in that directory.

The baseline created no market-data package or quantitative object. Its
handoff accurately distinguishes the exact five unsupported semantics and
does not claim loss numbers, future stress, authentication, optimization, an
Order, or trading authority.

Candidate trial:
`/Users/ame/autoquant-v0915-path-stress-candidate`. The exact candidate wheel
SHA-256 is
`acbecffeb66c1258ed0dcd448e71dfee7f7545291da041a8f1e48ed887d0e4c1`;
Python is 3.11.14 and the installed CLI reports `aq 0.9.15`. The 355-line
transcript is preserved as `candidate-transcript.md`. Project
`reported-book-path-stress`, Run
`run-20260801T065155286429Z-a0c2c8b422f0`, and Report
`report-20260801T065229961283Z-33608d0b11d2` all pass installed-wheel
validation, strict Explorer reconstruction, Orientation, and Studio snapshot.
The research brief timestamp precedes provider retrieval and Project intake.

## Progress log

- 2026-08-01 — Plan activated from clean released `v0.9.14`; OpenAlice remains
  independently pinned to `v0.8.31`.
- 2026-08-01 — Released-wheel baseline completed without coaching in three
  minutes. Its useful unsupported boundary authorizes the narrow fixed method
  described above; implementation now begins.
- 2026-08-01 — Candidate implementation smoke enumerated 300 complete
  synthetic windows, selected five inclusive-non-overlapping episodes, and
  reconciled 105 path points plus every holding/cash terminal contribution.
  Four dedicated method/tamper/intake tests and focused CLI, repository,
  version, lock, Python, JavaScript, and 1,356-link checks pass. Candidate
  installed-wheel replay is next.
- 2026-08-01 — Fresh candidate replay completed in four minutes. It acquired
  4,169 aligned formal sessions, independently retained Nasdaq coverage and
  failure evidence, enumerated 4,149 eligible windows, published one verified
  immutable Run and one direct Report, and stopped with no editable Session or
  trading overclaim. Full release verification is now running.
- 2026-08-01 — The first full suite ran all 395 tests in 1,350.614 seconds and
  failed only the shared research-start-gate invariant for the new template.
  The repaired template and four Path Stress tests now pass together; a clean
  full-suite rerun is required before release.
- 2026-08-01 — The clean rerun passed all 395 tests in 1,103.490 seconds. Lock
  validation, Python compile, Studio JavaScript syntax, diff hygiene, and all
  1,359 documentation links also pass. Final build/install/clone publication
  smokes remain.

## Completion

Complete this section only after every acceptance item is independently
verified and the release, if any, is published.
