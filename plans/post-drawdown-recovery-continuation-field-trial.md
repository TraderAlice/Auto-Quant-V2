# Post-drawdown recovery continuation field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.18`
- Related design: [[docs/design/study-run-evidence]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/run-bound-research-reports]], and
  [[docs/design/agent-native-quant-workbench]].

## Outcome

Prove whether a fresh quantitative coworker can enter one long-lived Project
whose current handoff is already a verified correction, preserve that history,
and answer a related but scientifically distinct follow-up through one new
task-complete data package, fixed descriptive Study, immutable Run, and
evidence-bound Report.

The exact released `0.9.17` wheel is the untouched baseline. `0.9.18` will
contain only reusable Workbench repairs reproduced by the trial. Breaking
replacement is allowed when an existing abstraction is wrong; no compatibility
layer or OpenAlice migration is required.

## Research assignment

Give a fresh coworker:

- a byte-for-byte copy of the completed `reported-book-path-stress` Project,
  including its original Run and Report, strict Independent Review, and current
  corrected Report;
- the exact installed released `0.9.17` wheel and materialized Skills;
- no original conversation, implementation checkout, or private construction
  notes;
- no new task data beyond whatever happens to remain visible in the long-lived
  Project.

The coworker receives this caller request:

> Continue the existing reported-book research without rewriting its history.
> The current corrected handoff identified five fixed non-overlapping worst
> 20-session loss episodes for the reported 40% QQQ, 25% NVDA, 20% TLT, and
> 15% flat-cash book. For each exact selected episode, determine whether the
> same fixed opening units recovered the episode-start book value during the
> next 60 complete XNYS sessions after the loss-window end. Report the first
> recovery session and sessions-to-recovery, or right-censor it at 60; the
> post-window peak and trough book values; the 60-session terminal book value;
> and exact per-holding contribution from the loss-window end through the
> 60-session terminal date. Contributions must reconcile to the book-value
> change. Preserve the selected episode identity from the prior immutable Run,
> but acquire and bind a complete task-local split-adjusted daily OHLCV package
> for this follow-up rather than treating visible inventory as automatic data
> authority. Keep provider routes and failures explicit. This is descriptive
> historical risk support only: do not optimize, forecast, create Orders, or
> grant trading authority. Leave one fixed Study, one immutable Run, one
> evidence-bound Report, and no editable Session. Make it obvious to the next
> coworker how the new conclusion relates to—but does not correct or supersede—
> the existing Path Stress correction lineage.

The scientific arithmetic is fixed by the caller's existing book meaning:

- for episode start `s`, fixed units are `u_i = w_i / P_i(s)` and cash remains
  `0.15`;
- book value is `V_t = 0.15 + sum_i u_i P_i(t)`;
- the recovery threshold is `V_t >= 1.0` on the first of the next 60 complete
  XNYS sessions after the episode end;
- post-window holding contribution at terminal date `T` is
  `u_i * (P_i(T) - P_i(end))`, and the sum must equal `V_T - V_end` within a
  declared fixed tolerance;
- episode dates and selection are inherited evidence, not reselected or
  optimized by the follow-up.

The baseline may use the best truthful installed public representation. It
must not be coached toward a presumed cross-Run dependency, derived-Study,
dataset-reuse, lineage, or synthesis implementation. Any copied prior artifact,
unbound prose dependency, ambiguous relationship, accidental correction,
private filesystem inference, or inability to express the work is retained as
product evidence rather than hidden.

## Scope

### In scope

- One isolated fresh Grok 4.5 worker using the exact installed `0.9.17`
  release wheel and a copied long-lived Project.
- Public orientation, current-versus-superseded Report discovery, demand-led
  market-data acquisition, fixed Study construction, bounded execution,
  evidence-bound Report publication, and Studio projection.
- Exact preservation of every existing immutable Run, Report, Review, and
  correction relationship.
- Exact provenance from the prior selected episodes into the new Study/Run,
  plus independent content identity for the new task-local OHLCV.
- The smallest reusable Core, CLI, Studio, schema, Agent-guidance, or
  documentation repair for each reproduced defect.
- Fresh candidate-wheel replay and complete release audit before tagging
  `v0.9.18` when a product change is warranted.

### Out of scope

- Reselecting loss episodes, changing the reported book, authenticating an
  account, optimizing a recovery rule, forecasting, Orders, TPSL, execution,
  or trading advice.
- Treating existing Project data as authority merely because it is visible, or
  building a central reusable data inventory.
- Mutating any prior immutable object, converting the follow-up into a
  correction of the existing Report, or flattening distinct Studies into one
  universal schema.
- OpenAlice version changes. OpenAlice remains on `0.8.31`.

## Acceptance

- [ ] A fresh worker begins with no source checkout or original conversation,
      reads the current corrected handoff through public installed surfaces,
      and distinguishes it from the superseded Report and governing Review.
- [ ] The worker recognizes the request as a related new Study in the same
      Project, not a new Project, Report correction, editable Session, or
      continuation of the old evaluation objective.
- [ ] Every prior Run, Report, Review, and correction byte remains unchanged;
      only authorized new task data, Study/source, Run, Report, and durable
      research-brief state are added.
- [ ] The new Run binds the exact prior episode identity and complete new
      task-local OHLCV identity without relying on prose or ambient inventory.
- [ ] The fixed arithmetic independently reconstructs five episodes, 60 XNYS
      sessions, recovery/censoring, peak/trough/terminal book paths, and exact
      reconciled per-holding contributions.
- [ ] The new Report cites only bound Run evidence, remains independent of the
      old correction chain, and grants no forecast, Order, or trading authority.
- [ ] Public CLI, Orientation, and Studio expose the relation between the new
      Study and prior evidence without implying correction or supersession.
- [ ] Every material baseline failure is retained and classified; only a
      reproduced reusable Workbench defect enters the candidate release.
- [ ] A fresh candidate worker completes the unchanged assignment using only
      installed public surfaces and independently acquired task data.
- [ ] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and clean-clone smokes pass before publication.

## Work

- [x] Define and index the long-lived Project continuation assignment.
- [ ] Build an isolated installed-`0.9.17` desk from the corrected evidence.
- [ ] Run and audit one fresh worker without coaching.
- [ ] Admit and implement only reproduced reusable product friction.
- [ ] Replay the unchanged task with a fresh candidate-wheel worker.
- [ ] Complete the release audit and publish `v0.9.18` if warranted.

## Findings and decisions

- 2026-08-01 — Existing data may remain visible in a long-lived Project, but
  visibility is not authority. The follow-up owns a complete content-locked
  package selected from its question; duplicated bytes remain acceptable
  evidence isolation.
- 2026-08-01 — A related follow-up belongs in the same Project when it keeps
  the reported book and research body but asks a distinct fixed question. A
  new Study and Run must not masquerade as a correction of the old Report.
- 2026-08-01 — The prior five episode identities are legitimate upstream
  evidence. The trial will test whether that exact derived input can enter the
  new immutable Study/Run without copy-and-paste authority or private
  filesystem inference.

## Verification

Record exact wheel hashes, isolated roots, Agent sessions/transcripts, public
commands, mutation inventories, quantitative reconstruction, focused/full
tests, builds, and installed/clean-clone smokes here as evidence is produced.

## Progress log

- 2026-08-01 — Plan activated from clean released `v0.9.17`; OpenAlice remains
  independently pinned to `v0.8.31`.

## Completion

Complete this section only after every acceptance item is independently
verified and the release, if any, is published.
