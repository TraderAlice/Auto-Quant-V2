# Long-lived cross-market Workspace field trial

- Status: `completed`
- Updated: `2026-08-01`
- Target release: `0.9.7`
- Related design: [[docs/design/workspace-project-boundaries]],
  [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/reported-position-book-risk]],
  [[docs/design/run-bound-research-reports]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that AutoQuant is a long-lived quantitative desk rather than a
single-assignment scaffold. A fresh coworker must enter a Workspace that
already contains one completed mainland-China Event Project, preserve that
Project exactly, accept a materially different U.S. portfolio-risk request,
acquire task-local data from zero supplied bytes, create one sibling Project,
and return fixed immutable evidence without confusing Project, data, request,
or default-selection authority.

## Field assignment

Reuse a file-faithful handoff copy of the completed `0.9.6` CATL Event
Workspace. The new caller reports one hypothetical U.S. mega-cap book:

- `NVDA` 30%, `MSFT` 25%, `AMZN` 15%, `META` 10%, `GOOGL` 10%, Cash 10%;
- XNAS equities, USD, long-only;
- daily split-adjusted observations from `2021-01-01` through the last
  completed XNYS session available at retrieval;
- snapshot `asOf` equal to that final admitted session;
- fixed 126-bar historical covariance lookback and 20% annualized volatility
  ceiling;
- caller authorizes reducing `NVDA` only to Cash, with every other holding
  unchanged;
- answer baseline concentration, volatility, component risk, drawdown, and
  the largest compliant NVDA weight or truthful infeasibility;
- historical quantitative decision support only, with no account, Order,
  Broker, TP/SL, or trading authority.

No U.S. data is supplied. The worker must use installed U.S. acquisition
guidance, attempt at least two peer routes, and create one complete adjusted
package for the new Project. Existing A-share bytes are irrelevant evidence,
not a reason to narrow or reshape the question.

## Scope

### In scope

- Preserve hashes of every pre-existing Project file before and after work.
- Run one isolated installed `0.9.6` Grok baseline with only the new assignment,
  existing Workspace, public `aq`, and materialized Skills.
- Observe Workspace orientation, explicit Project selection, template choice,
  research brief, acquisition, pristine-project hydration, fixed Book Risk
  Run, direct Run Report, validation, Studio multi-Project projection, and
  outward handoff.
- Detect accidental default-Project changes, cross-Project writes, stale data
  reuse, path ambiguity, duplicate Workspace creation, or Session/search work.
- Promote only reproduced reusable friction into `0.9.7`, rerun a fresh
  installed-wheel coworker, and release only after a clean audit.

### Out of scope

- Central dataset discovery, shared mutable caches, deduplication, or automatic
  reuse of prior Project snapshots.
- Live account lookup, holdings authentication, Broker/Order/TPSL execution,
  general portfolio optimization, or changing more than the authorized NVDA
  leg.
- OpenAlice upgrade or host-specific orchestration.
- Migrating, rewriting, or re-running the completed CATL Project.

## Acceptance

- [x] The initial A-share Project tree hash, default Project, Run count, and
  result identity remain byte-for-byte unchanged.
- [x] A fresh installed worker discovers the existing Workspace and creates no
  second Workspace or nested manifest.
- [x] The worker identifies the U.S. request as a new sibling Project and uses
  explicit Project identity for every state-changing multi-Project command.
- [x] The new English brief preserves the exact book, clock, lookback, ceiling,
  authorized leg, acquisition requirement, and no-trading boundary before
  provider work.
- [x] At least two U.S. routes are attempted and audited; one task-complete
  adjusted package reaches strict Book Risk intake without using A-share data
  or a central inventory.
- [x] Exactly one current fixed Book Risk Run and one direct Run Report answer
  baseline risk plus the one-leg NVDA-to-Cash path; no Session, Check,
  Experiment, candidate, Factor, Portfolio, RL, or second Run is created.
- [x] Workspace validation, explicit orientation for both Projects, and one
  Studio snapshot truthfully project two isolated Projects and unchanged
  default selection.
- [x] Every material trial failure becomes a bounded repair with regression or
  an explicit worker/provider/external limitation.
- [x] Complete tests, documentation links, build/install smoke, clean-clone
  checks, and a fresh final worker pass before `v0.9.7` is tagged and pushed.

## Work

- [x] Choose a cross-market, cross-template request that cannot reuse the
  existing Project's data or method.
- [x] Prepare a file-faithful existing-Workspace handoff and immutable baseline
  inventory.
- [x] Run and preserve the installed `0.9.6` coworker baseline.
- [x] Triage real reuse friction and implement the minimum `0.9.7` repairs.
- [x] Run final verification, installed-wheel coworker replay, and release.

## Findings and decisions

- 2026-08-01 — Book Risk was chosen because it changes market, asset set,
  research method, data semantics, and deliverable while remaining fixed and
  fast. It tests Workspace reuse without confounding the result with candidate
  search.
- 2026-08-01 — Project-local duplicate snapshots remain acceptable. This
  trial measures isolation and demand fidelity, not byte deduplication.
- 2026-08-01 — The old Project's default identity is preserved deliberately.
  Creating a sibling Project must not silently reinterpret the desk's default
  or mutate old evidence merely to make the new task convenient.
- 2026-08-01 — The installed `0.9.6` baseline completed with no CLI retry,
  provider retry, Core failure, clarification, Session, or second Run. The old
  Project retained all 30 files at tree hash
  `ddaad48809f5281c35b69f609fbbee172a304a55e81e28ed630bb698240a944c`,
  its sole Run identities, and Workspace-default status.
- 2026-08-01 — The new sibling Project acquired Yahoo and Nasdaq data from
  zero supplied U.S. bytes, admitted the aligned Yahoo package, and published
  one fixed Book Risk Run plus one direct Run Report. The 126-bar governing
  model found the NVDA-to-Cash path feasible at a largest NVDA weight of
  `0.15007817661003228` under the 20% ceiling.
- 2026-08-01 — Promote two bounded repairs. A caller-fixed sizing lookback must
  become the Book Risk primary/current window, and U.S. acquisition guidance
  must direct fixed Labs to aligned provider packages. Do not add speculative
  active-Project process state: explicit Project identity already worked.
- 2026-08-01 — The sizing-window repair exposed a hidden 252-primary
  assumption in drawdown verification. New Runs therefore retain the longest
  fixed equity path as immutable validation evidence while Explorer, CLI, and
  Studio normalize and project only the caller-governing primary path. This
  preserves complete 63/126/252 reconstruction without reverting the caller's
  126-bar current definition.
- 2026-08-01 — Repository-root materialized Skills had not been refreshed
  since `0.9.0`. The release now checks in the exact `0.9.7` bundle and adds a
  regression that verifies the root Workspace snapshot against current
  Harness authority. This is release materialization, not a general Workspace
  upgrade protocol.
- 2026-08-01 — The final installed `0.9.7` worker used aligned V1 packages for
  both Yahoo and Nasdaq on its first provider attempts. It reported 126
  consistently across primary/current/sizing evidence, kept the CATL Project
  byte-identical, and left exactly one new Run, one direct Report, and zero
  Sessions. One accidental probe-Project create/remove was recorded as a
  worker retry rather than hidden or promoted into speculative Core state.

## Verification

- Installed `0.9.6` baseline transcript and compact inventory/triage record:
  `../grok-field-trials/cohort-12-long-lived-us-book-risk-v096/`.
- Focused Book Risk, Skill, and version regression: 40 tests passed.
- Final `uv run python -m unittest discover -s tests -q`: 374 tests passed in
  923.926 seconds.
- `uv run python scripts/check_doc_links.py`: 1,288 links resolved.
- `uv lock --check`, Python compile, Studio JavaScript syntax, and
  `git diff --check`: passed.
- `uv build` produced source and wheel distributions; a fresh Python 3.11.14
  environment installed the wheel, reported `aq 0.9.7`, and exposed 51 public
  commands.
- Final installed-wheel transcript and independent audit:
  `../grok-field-trials/cohort-13-long-lived-us-book-risk-v097/`. Grok session
  `019fb9f8-cc7a-7512-9b02-8a98a0038db7` completed the full two-Project task.
- A no-hardlink local clone at `974026f` contained no local override and passed
  Project list, orientation, validation, Studio snapshot, and current Skill-
  bundle verification with the checked-in sample as default.

## Progress log

- 2026-08-01 — Plan created and indexed from the clean released `v0.9.6`
  baseline before constructing the long-lived Workspace handoff.
- 2026-08-01 — Preserved the installed-worker transcript and a compact trial
  record in `grok-field-trials/cohort-12-long-lived-us-book-risk-v096` after
  auditing both Project trees, Run counts, Workspace manifests, and default
  identity.
- 2026-08-01 — Implemented the two promoted repairs, added strict governing-
  lookback and Agent-guidance regressions, updated the public Book Risk design,
  and advanced the package identity to `0.9.7` without touching OpenAlice.
- 2026-08-01 — Refreshed the checked-in root Workspace Skill snapshot, passed
  the full release audit, accepted the fresh installed `0.9.7` worker with its
  one disclosed Agent retry, and completed the patch without changing
  OpenAlice's `0.8.31` selection.

## Completion

Completed. One retained desk now demonstrates two isolated Projects across
markets and fixed research methods without old-data authority, hidden default
changes, or disposable-Workspace semantics. The caller's governing covariance
window is the ordinary answer surface, provider panel guidance reaches fixed
Labs directly, and remaining worker/provider friction stays explicit rather
than expanding Core without evidence.
