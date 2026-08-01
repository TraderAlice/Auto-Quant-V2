# Clarification-first delegation field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.14`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/reported-position-book-risk]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove whether a fresh quantitative coworker can receive one ordinary but
materially underspecified portfolio question, preserve it in English, identify
the caller-owned facts that would change the research contract, and stop
before data acquisition or quantitative authority. After the delegating Agent
answers in the same conversation, the coworker must resume from that durable
brief and complete exactly one bounded historical sizing study without
inventing execution or trading authority.

The released `0.9.13` wheel is the baseline. `0.9.14` will contain only
reusable friction reproduced across the two-phase dialogue. A clean baseline
with no framework defect is a valid field result; do not manufacture a release
change merely to increment the version.

## Two-phase assignment

### Phase one: deliberately incomplete request

Delegate only this meaning:

> The user's portfolio is already technology-heavy and they are considering
> adding NVDA. Use historical quantitative evidence to tell them whether they
> should add it and how much would be appropriate.

Do not supply the current holdings, cash, NAV, as-of date, risk definition,
weight cap, estimation window, history, data authority, or whether existing
positions may be resized. The worker must not infer any of them from examples,
templates, local data, or market convention.

### Phase two: caller clarification

If the worker asks a bounded sufficient clarification, answer in the same
session with this fixed contract:

- Current book as of `2026-07-31`: `70% QQQ`, `30% USD cash`, no other
  holdings, and no current NVDA position; research reference NAV is
  `USD 100,000`.
- Candidate action: fund NVDA from cash only. Keep QQQ unchanged and do not
  use leverage, shorting, or proportional rescaling.
- Sizing objective: find the largest NVDA target weight up to `20%` for which
  the post-entry static book's historical annualized volatility is no greater
  than `25%`.
- Risk estimation: completed daily close-to-close returns, trailing `252`
  observations with at least `126`, as of the final completed session.
- Evidence window: completed daily observations from `2020-01-01` through
  `2026-07-31`; disclose the actual final completed provider session.
- Data authority: Yahoo split-adjusted history may be the formal aligned
  package; Nasdaq.com is the independent split-adjusted coverage route. Begin
  with zero staged OHLCV and keep the package task-local.
- Required evidence: current versus sized book volatility, covariance/risk
  contribution, correlation, maximum drawdown, exact funded weight changes,
  and whether the fixed risk ceiling or candidate cap binds.
- Historical quantitative decision support only. No valuation claim, live
  account access, Order, TP/SL, tax advice, or trading recommendation.

## Scope

### In scope

- One isolated fresh Grok 4.5 conversation using the exact installed `0.9.13`
  wheel, a new empty Workspace, generated Skills, public CLI/schema surfaces,
  and provider networking only after clarification.
- The same session across both phases, with exact transcript, filesystem,
  provider, retry, Project, Study, Run, Report, and Session inventories.
- Clarification quality, durable brief revision, fixed Book Risk construction,
  demand-led acquisition, strict evidence, final handoff, and stop behavior.
- The smallest coherent Core, Skill, template, CLI, Studio, or documentation
  repair for each reproduced material Workbench defect.
- A fresh candidate replay and complete release audit only when a real product
  change is admitted.

### Out of scope

- Predicting NVDA returns, valuation/fundamental analysis, sentiment or news,
  changing QQQ, searching risk budgets or caps, optimization across alternate
  books, live account access, Broker, Order, TP/SL, or OpenAlice changes.
- A structured universal request extractor, mandatory questionnaire, generic
  natural-language parser, central data inventory, or automatic downloader.
- Treating the first-phase lack of authority as an error. Truthful
  clarification is the intended first handoff.

## Acceptance

- [ ] Phase one writes a durable English brief before any retrieval or Project
      creation and preserves the user's actual intent without filling gaps.
- [ ] Phase one asks only caller-owned questions that materially change the
      research contract and stops with zero staged OHLCV, Projects, Studies,
      Sessions, Runs, and Reports.
- [ ] Phase two updates the same brief with explicit answers and does not
      silently change any supplied holding, risk, sizing, clock, or data term.
- [ ] The worker discovers the exact fixed Book Risk route, acquires one
      task-complete aligned package plus independent provider evidence, and
      creates exactly one Project and one successful fixed Run.
- [ ] Strict Explorer and a durable evidence-bound Report answer the maximum
      funded NVDA weight, binding constraint, current/post-entry risk, and
      limitations without a Session or parameter-search loop.
- [ ] Final orientation and Studio expose a complete historical handoff with
      `tradingAuthority=none` and no writable research continuation required.
- [ ] Every material retry or failure becomes deterministic regression
      coverage and a bounded repair or remains an explicit limitation.
- [ ] If a release change is admitted, final replay, tests, documentation,
      build/install, and clean-clone smoke pass before publication.

## Work

- [x] Define the deliberately incomplete request and fixed second-phase answer.
- [ ] Build an isolated installed-`0.9.13` baseline Workspace.
- [ ] Run phase one and audit whether the worker stops before authority.
- [ ] Resume the same conversation with the caller clarification.
- [ ] Audit the completed research and classify every friction item.
- [ ] Implement and replay only reproduced reusable defects, if any.
- [ ] Close as a no-change proof or publish a verified `v0.9.14`.

## Findings and decisions

- 2026-08-01 — The next employability risk is requirement negotiation, not
  another model or provider feature. Earlier field workers received unusually
  complete assignments and therefore did not prove they would resist filling
  caller-owned gaps in an ordinary delegation.
- 2026-08-01 — A funded one-asset Book Risk question was selected because
  holdings, cash, constraints, and risk definitions are economically material
  and already have a fixed non-trading Lab. The trial can therefore isolate
  clarification behavior from new quantitative-engine work.
- 2026-08-01 — Markdown remains the coordination surface. This trial does not
  authorize a schema-first intake wizard: the worker should write and revise
  `research.md`, ask the delegating Agent, and use strict schemas only after
  the question is sufficiently fixed.
- 2026-08-01 — Data remains demand-led. Phase one has no authority to acquire
  any; phase two owns a new task-complete package even if similar bytes exist
  elsewhere. Inventory is neither a source of missing requirements nor a
  reason to narrow the question.
- 2026-08-01 — OpenAlice remains pinned to `v0.8.31` throughout this topic.

## Verification

Pending baseline dialogue.

## Progress log

- 2026-08-01 — Plan activated immediately after the verified `v0.9.13`
  provider-semantics release. No implementation change is authorized before
  the released baseline completes phase one.

## Completion

Complete this section only when status becomes `completed`.
