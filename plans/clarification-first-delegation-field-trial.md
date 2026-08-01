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
- [x] Build an isolated installed-`0.9.13` baseline Workspace.
- [x] Run phase one and audit whether the worker stops before authority.
- [x] Resume the same conversation with the caller clarification.
- [x] Audit the completed research and classify every friction item.
- [x] Implement and replay only reproduced reusable defects, if any.
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
- 2026-08-01 — The exact installed `0.9.13` phase-one worker behaved as
  intended. It wrote and hashed a durable English `research.md`, asked five
  material caller-owned questions, and stopped with zero network access,
  staged files, Projects, Studies, Sessions, Runs, Reports, or quantitative
  authority. Clarification-first delegation therefore needs no intake wizard
  or structured questionnaire repair.
- 2026-08-01 — The same worker resumed correctly after clarification and
  acquired a complete task-local Yahoo package plus independent Nasdaq
  evidence. This reinforces the durable data invariant: the clarified question
  owns a complete local package; existing inventory is neither a research
  boundary nor selection authority, and deduplication may only be an invisible
  storage optimization.
- 2026-08-01 — The released Book Risk contract then failed the exact clarified
  question. Although Core accepts an absent entry asset, the fixed Judge
  rejected the honest one-holding baseline and required at least two non-zero
  reported weights. The worker worked around that contradiction with a fake
  `1e-9` NVDA holding and a second Study. The sizing path also ignored the
  caller's `20%` candidate cap, spent the full `30%` cash, and left the actual
  `20%` answer as an out-of-Run manual derivation. This is a reusable fixed-
  authority defect, not worker-specific friction.
- 2026-08-01 — The bounded repair will make direction-specific resulting-
  weight authority explicit in `positionSizing`, admit an honestly absent
  increase asset through the Judge, and report whether volatility, the caller
  weight boundary, or available funding binds. The candidate replay must end
  with one Project, one Study, one successful Run, and one Report.
- 2026-08-01 — Candidate cohort 32 proved the central repair. A fresh worker
  bound `maximumWeight: 0.20`, preserved baseline weights as exactly
  `{QQQ: 0.70}`, and the fixed Run returned `maximum-weight-compliant`, target
  NVDA `20%`, cash `10%`, governing volatility `19.29%`, and
  `bindingConstraint: caller-weight-bound`. It created one final Project, one
  Study, one successful Run, one Report, and no Session or fabricated holding.
- 2026-08-01 — The same replay exposed two directly related evidence-surface
  gaps before final qualification. The worker reasonably mapped the caller's
  “at least 126 observations” into the method's `minimumObservations`, but the
  Judge unnecessarily limited that rolling-diagnostic floor to the shortest
  63-bar lookback and produced one failed Run before accepting the scaffold's
  40. The fixed method still requires every complete lookback, so the supported
  floor can truthfully extend through the largest declared lookback. The Run
  also omitted target-book pairwise correlation and maximum drawdown, forcing
  the worker to derive the former from quadratic coefficients and disclose the
  latter as unavailable. Both belong in the same fixed sizing evidence rather
  than post-Run arithmetic.
- 2026-08-01 — Candidate cohort 33 produced the complete intended answer in
  one Project, Study, successful Run, Report, and no Session. Its installed
  `aq run book-risk` consumer nevertheless raised `list index out of range`
  because the human summary still indexed the first baseline correlation even
  when the reported book truthfully held only QQQ. The strict diagnostics were
  valid; the presentation path was not. Empty baseline pairwise correlation
  is now an explicit one-asset state in human and JSON CLI regression coverage.
- 2026-08-01 — Cohort 34 was rejected as release evidence after the worker
  searched adjacent field-trial directories and read prior cohort material.
  This was an isolation failure, not a research result. Final qualification
  moved to a standalone audit directory, supplied the installed CLI path
  explicitly, and prohibited all other AutoQuant installations and trials.
- 2026-08-01 — Final isolated cohort 35 passed. It began with zero staged
  OHLCV, wrote the brief first, acquired independent Yahoo and Nasdaq packages,
  preserved the honest `{QQQ: 0.70}` baseline, and created exactly one Project,
  one fixed Study, one successful Run, one Report, and no Session. The immutable
  answer is NVDA 20%, cash 10%, 19.29% governing volatility, 0.692 correlation,
  -12.49% sized-book maximum drawdown, with `caller-weight-bound` binding.

## Verification

Baseline cohort:
`/Users/ame/2607AutoQuant/grok-field-trials/cohort-31-clarification-first-book-risk-v0913`.
The exact wheel SHA-256 is
`8657e6a0b6d3a232a19cb861ca6eb053060ef7827ca427f5624a546faddcd0e4`;
the two-phase Grok session is
`019fbba7-750e-7233-9b59-e4b2e07d3101`, preserved in
`grok-transcript.md`.

Candidate cohort 32:
`/Users/ame/2607AutoQuant/grok-field-trials/cohort-32-clarification-book-risk-v0914-candidate`.
It proved the caller-bound result but exposed the observation-floor,
correlation, and target-book drawdown gaps described above.

Candidate cohort 33:
`/Users/ame/2607AutoQuant/grok-field-trials/cohort-33-clarification-book-risk-v0914-final`.
Its single successful Run proved the new evidence but reproduced the empty-
baseline-correlation CLI failure.

Final isolated release audit:
`/Users/ame/autoquant-v0914-release-audit`. The exact wheel SHA-256 is
`d9e346234a1a8fa7c6e4dac4e70d0e91c505938dca18aef2d12192e7634b6355`;
Grok session `019fbbd5-ca4a-7b01-ac69-7ac0a3419bf6` is preserved in
`grok-transcript.md`. Installed-wheel `aq validate` and strict
`aq run book-risk --json` both passed for Project
`nvda-cash-size-vol-ceiling`, Run
`run-20260801T054228037779Z-c9f31536b860`, and Report
`report-20260801T054310758003Z-cc8455716151`.

Repository audit:

- `uv run python -m unittest tests.test_book_risk_lab` passed all 22 focused
  tests in 14.701 seconds, including human and JSON CLI coverage for an empty
  one-asset baseline correlation set.
- `uv run python -m unittest discover -s tests` passed all 391 tests in
  965.751 seconds.
- `uv run python scripts/check_doc_links.py` resolved all 1,342 documentation
  links.
- `uv lock --check`, `uv run python -m compileall -q autoquant tests`,
  `node --check autoquant/studio_assets/studio.js`, and `git diff --check`
  passed.
- Final source and wheel builds passed. The release wheel SHA-256 is
  `d21d3cc3b86eebc18d4a3805a71507f316c7eef8a15bf4e70bbcf096d11af553`;
  the source archive SHA-256 is
  `3e06c793e394d2f408ff0df2613f7e179a0554448bad514981cd3040ad12d908`.
- A fresh Python 3.11.14 installation reported `aq 0.9.14`, exposed all 53
  public commands and 42 schemas, and used the final wheel to validate,
  strictly inspect, and project the isolated one-Project release audit.

## Progress log

- 2026-08-01 — Plan activated immediately after the verified `v0.9.13`
  provider-semantics release. No implementation change is authorized before
  the released baseline completes phase one.
- 2026-08-01 — Baseline dialogue completed. Phase one passed without product
  friction; phase two reproduced an absent-candidate Judge contradiction and
  missing caller-weight-bound authority. Implementation is now authorized.
- 2026-08-01 — Two candidate replays closed the fixed-authority and evidence
  gaps, then reproduced one empty-correlation CLI consumer defect. A third
  attempted replay was rejected for cross-cohort contamination.
- 2026-08-01 — The standalone installed-wheel replay completed without source
  or prior-trial access and passed the exact strict Explorer path. Repository
  release verification and publication remain before closure.

## Completion

Complete this section only when status becomes `completed`.
