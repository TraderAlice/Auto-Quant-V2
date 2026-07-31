# Same-Project data-vintage refresh field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.10`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that a long-lived AutoQuant Project can revisit the same quantitative
question on a newer task-specific market-data vintage without overwriting its
old request, dataset snapshot, Study, immutable Run, or Report. The refreshed
evidence must have its own caller-owned as-of boundary, content-locked dataset
identity, fixed Study, Run, and Report while remaining recognizably part of the
same evolving body of research.

## Context

AutoQuant already proves two orthogonal forms of Workspace reuse:

- one completed Workspace can accept an unrelated market and method in a
  sibling Project;
- one completed Project can accept a related second fixed question over the
  exact retained dataset.

The missing lifecycle is ordinary quantitative maintenance. A user may ask
the same question again after another market session or after acquiring a new
provider vintage. Current strict intake owns one Project-root `request.json`,
`intake.json`, and `data/ohlcv/**`; every construction Study binds that single
closure. Replacing those bytes would change the current Study dataset hash and
can stale or invalidate prior evidence. Creating a duplicate Project would
hide that both answers belong to one research lineage.

This is not a request for a shared mutable latest-data cache. The caller's
question still determines each complete task-local snapshot. Duplicate bytes
across immutable vintages are acceptable when they preserve coherent
evidence.

## Field assignment

Prepare one completed installed-`0.9.9` U.S. mega-cap Book Risk Project using
split-adjusted completed daily observations through `2026-07-30`. It asks
whether a fixed hypothetical NVDA/MSFT/AMZN/META/GOOGL/Cash book is crowded
under one caller-fixed covariance lookback and whether reducing NVDA alone to
Cash satisfies one fixed historical volatility ceiling.

Give a fresh worker a follow-up request to update that exact research question
through the latest completed XNYS session, expected `2026-07-31`. Require fresh
task-specific acquisition and peer-route audit, preservation of all previous
fixed evidence, one new explicit data-vintage identity, one new fixed Study,
one Run, one direct Report, and a concise comparison of whether the answer
materially changed. No factor search, Portfolio/RL lane, Session, execution,
or trading authority is requested.

## Scope

### In scope

- Start from the exact released `v0.9.9` wheel and one independently verified
  completed Project whose initial cutoff precedes the available final session.
- Observe whether a fresh worker recognizes this as the same Project and a new
  immutable evidence vintage rather than a new Project or in-place mutation.
- Acquire the exact requested panel through materialized market-data Skills;
  preserve provider and package evidence outside quantitative authority until
  strict intake succeeds.
- Make every refreshed request, snapshot, Study input, Run, and Report
  independently loadable and content-bound.
- Preserve all prior fixed-authority and immutable-evidence files byte-for-byte;
  only explicitly longitudinal narrative notes may append.
- Promote only independently reproduced Core/CLI/Skill/Studio friction needed
  to make this common maintenance route truthful and Agent-operable.

### Out of scope

- A central market-data inventory, mutable latest-data directory, automatic
  provider polling, background refresh, deduplication store, or redistribution
  promise.
- Rewriting old snapshots, Runs, Reports, or Harness identities to the new
  release or data vintage.
- General migration machinery for arbitrary obsolete Project schemas.
- Factor optimization, Portfolio construction, RL, Broker, Order, TP/SL,
  account, execution, suitability, or trading authority.
- Treating a provider revision with no new completed session as proof of a
  meaningful market update.

## Acceptance

- [x] The baseline uses the exact released `v0.9.9` wheel, public CLI/Skills,
  a real split-adjusted five-asset panel ending `2026-07-30`, and one verified
  fixed Book Risk Study/Run/Report.
- [ ] The follow-up request fixes the same universe, weights, method, ceiling,
  and research-only authority while moving only the completed-session as-of
  boundary to `2026-07-31`.
- [ ] A fresh worker uses public installed Workbench surfaces, keeps one
  Project, and does not inspect repository or private package implementation.
- [ ] Fresh acquisition and package evidence satisfy the complete updated
  request before quantitative intake; local inventory never narrows the task.
- [ ] The new request, dataset snapshot, fixed Study, Run, and Report have
  explicit independent identities and remain loadable beside the original.
- [ ] Every original fixed-authority and immutable-evidence file remains
  byte-identical; any allowed `research.md` append is separately disclosed.
- [ ] The refreshed handoff compares old and new findings without treating
  historical-model changes as forecasts, orders, or live-account authority.
- [ ] Every material baseline failure is either repaired with deterministic
  regression coverage or recorded as an explicit worker/provider limitation.
- [ ] Final wheel replay, complete tests, documentation links, build/install,
  and clean-clone Workspace smoke pass before `v0.9.10` is tagged and pushed.

## Work

- [x] Audit the singleton Project intake and dataset closure in released
  `v0.9.9`.
- [x] Prepare and independently verify the historical-cutoff baseline Project.
- [ ] Run and review the fresh `0.9.9` follow-up worker.
- [ ] Implement only reproduced reusable friction and rerun the assignment.
- [ ] Complete release documentation and final verification, tag, and push.

## Findings and decisions

- 2026-08-01 — A data vintage is immutable quantitative evidence, not a cache
  entry. The same provider may legitimately supply multiple task-specific
  snapshots; each must retain exact retrieval and content identity.
- 2026-08-01 — Same-Project lineage matters because the caller is revisiting
  one question. A sibling Project is appropriate for a different research
  problem, not merely for avoiding a singleton intake limitation.
- 2026-08-01 — Project-root intake remains the initial construction record.
  The field trial will determine whether a later Study-owned request plus
  Study-owned dataset closure is the smallest truthful extension; it will not
  assume that implementation before the baseline worker encounters the gap.
- 2026-08-01 — The released-wheel baseline selected Yahoo only after an
  independent Nasdaq.com peer package covered the same five assets and all
  1,399 sessions through `2026-07-30`; bounded comparison found no OHLC
  mismatch under the fixed tolerance and retained provider volume differences.
  Strict intake, fixed Book Risk Run, direct Report, validation, orientation,
  and public Report loading all passed.

## Verification

Pending.

## Progress log

- 2026-08-01 — Created the `0.9.10` field plan from clean released `v0.9.9`
  after verifying that current strict intake and every primary construction
  Study bind the singleton `data/ohlcv/**` closure.
- 2026-08-01 — Prepared `cohort-19-same-project-data-refresh-v099` from wheel
  SHA-256
  `049369a2178cab7b4efdf92c8d89615912c695cf233ecb38701141e7e6599c6d`.
  Its sole Project contains 45 files, one `2026-07-30` snapshot, Run
  `run-20260731T233720467155Z-1a227c68d6c1`, and Report
  `report-20260731T233804152663Z-e0f3a05e93d6`; a pristine Project copy and
  exact tree hashes are retained for host-side preservation review.

## Completion

Pending.
