# Make primary horizons and terminal Sessions Agent-native

- Status: `active`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0826-price-volume-factor/desk/workspace/projects/grok-price-volume-factor-v0826`
- Related design: [[docs/design/request-bound-research-horizon]],
  [[docs/design/agent-operator-experience]], and
  [[docs/design/research-session-loop]].

## Outcome

A Coding Agent can state one primary forward horizon plus only the additional
diagnostic horizons it wants, and a valid Report-bound completion or promotion
becomes a truthful terminal handoff with its exact Report visible and another
Session available only as an explicit optional continuation.

## Context

A fresh Grok Build coworker used only the installed `0.8.26` wheel, nine
caller-staged Yahoo daily OHLCV files, and one bounded Factor assignment. It
created one Project, one baseline Run, one governed Session, one passing Check,
one REVERT Experiment, one immutable Report, and one baseline-retaining
completion. The negative price-trend plus dollar-volume result was
scientifically coherent, all edit/data/trading boundaries held, and no second
Experiment or downstream lane was created.

The worker nevertheless hit two public-contract defects:

- intake rejected primary `20` with diagnostics `[5, 60]` because the primary
  value had to be repeated inside `diagnosticForwardBars`;
- after the exact Report-bound completion, orientation still labeled a new
  Session `SESSION REQUIRED` and omitted the completed Report id.

Neither defect requires Core to infer the assignment's one-trial budget.
Primary evaluation is already mandatory by definition, and `completion.json`
is already an explicit immutable terminal decision for its Session.

## Scope

### In scope

- Canonicalize caller horizon policy as the sorted union of the primary horizon
  and the supplied additional diagnostic horizons.
- Preserve strict integer, range, count, uniqueness/order, capacity, hashing,
  and normalized derived-horizon contracts.
- Make a current, authority-valid completed Session whose retained leader is
  the current Run a terminal evidence-ready Work Brief.
- Apply the same terminal handoff to a current, authority-valid promotion;
  source preservation still does not assert scientific qualification.
- Surface the exact Report bound by the validated completion receipt.
- Keep `session.show` and a deliberately optional `session.start` as supporting
  actions without automatic continuation.
- Preserve CLI JSON, human output, Studio, schema, documentation, and installed
  package agreement.

### Out of scope

- Inferring trial budgets or stopping rules from request prose.
- Automatically publishing Reports, completing Sessions, or opening another
  Session.
- Changing Experiment verdict, qualification, promotion, or trading authority.
- Treating a stale completed Session as current after Study/source authority
  changes.
- Renaming the backwards-compatible `diagnosticForwardBars` field.

## Acceptance

- [x] A request with primary `20` and diagnostics `[5, 60]` validates and
      canonically records `[5, 20, 60]`; malformed, unsorted, duplicate, or
      over-capacity input remains rejected.
- [x] A valid current baseline-retaining completion has no primary action,
      reports `required-research-complete`, exposes its exact Report id, and
      offers inspect/optional-continue supporting actions.
- [x] A valid current Report-bound promotion has the same terminal handoff
      while explicitly withholding scientific qualification.
- [x] Active, stale, missing-baseline, pre-promotion, fixed-Study, multi-lane,
      and explicit fresh-Session routes retain their existing semantics.
- [x] CLI and Studio project the same strict Work Brief and human output no
      longer says `SESSION REQUIRED` for the completed branch.
- [ ] Focused/full tests, docs, build/install smoke, clean clone, and a fresh
      installed-wheel Grok replay agree before `0.8.27`.

## Work

- [x] Reproduce and independently audit the `0.8.26` worker's request retry,
      immutable evidence, source restoration, completion, and final Work Brief.
- [x] Implement canonical primary-horizon union and public discovery wording.
- [x] Implement validated completed-Session terminal orientation and exact
      completion Report projection.
- [x] Extend the same handoff to Report-bound promotion after the final worker
      reproduced the same false required action.
- [x] Add regression coverage and update public/design/status documentation.
- [ ] Run a fresh installed-wheel Grok replay and complete release verification.

## Findings and decisions

- 2026-07-30 — The worker's candidate correctly used both predeclared causal
  components, worsened validation mean IC from `-0.119921` to `-0.128426`,
  REVERTed, restored the Project source, and returned a useful negative answer.
- 2026-07-30 — Core will not infer “one Session” from prose. The terminal signal
  is the existing validated completion receipt; a new Session remains possible
  only by explicit choice.
- 2026-07-30 — `diagnosticForwardBars` remains the canonical complete evaluated
  set. Caller input may omit the separately declared primary value because Core
  can add it deterministically without inventing research authority.
- 2026-07-30 — The first `0.8.27` worker completed the negative REVERT branch
  and proved both target fixes, then exposed one missing complete Report
  analysis example. A complete copyable schema example removed that retry.
- 2026-07-30 — The final worker published its Report on the first attempt and
  promoted a KEEP whose scientific qualification still failed. Its post-
  promotion `SESSION REQUIRED` reproduced the same terminal-handoff defect, so
  completion and promotion now share optional-continuation semantics.

## Verification

- Originating installed-wheel Project validation, strict Factor Explorer,
  Studio snapshot, object counts, edit authority, and source restoration passed.
- Focused horizon, orientation, CLI, Report, research-program, and intake
  regression passed 103 tests after terminal-promotion expectations were
  updated.
- Full repository regression passed 325/325 tests in 959.906 seconds.
- Documentation validation resolved 1,129/1,129 double-links.
- First installed `0.8.27` worker:
  - supplied primary `20` and only additional diagnostics `[5, 60]`; intake
    succeeded first attempt and canonicalized `[5, 20, 60]`;
  - produced one Project, two Runs, one Session, one Check, one REVERT
    Experiment, one Report, and one completion;
  - finished at `required-research-complete` with the exact Report id and no
    false required Session;
  - exposed one first-attempt Report recommendation-field retry, now resolved
    by a complete copyable public schema example.
- Final installed `0.8.27` worker:
  - completed the same unchanged assignment with no CLI failures and published
    its Report on the first attempt;
  - produced one KEEP, then correctly promoted without claiming scientific
    qualification;
  - reproduced a false post-promotion `SESSION REQUIRED`, which is now covered
    by deterministic terminal-handoff tests;
  - left two separately indexed proposed follow-ups:
    [[plans/daily-factor-baseline-surface]] and
    [[plans/test-visibility-integrity-state]].
- Final distribution, fresh install, and exact clean-clone smoke pending.

## Progress log

- 2026-07-30 — Plan activated from the isolated `0.8.26` price/volume Factor
  trial after both public-contract failures were independently reproduced.
- 2026-07-30 — Two fresh installed `0.8.27` Grok workers exercised REVERT /
  completion and KEEP / promotion branches; their reproducible public-surface
  friction was either fixed here or indexed as explicit follow-up.

## Completion

Pending.
