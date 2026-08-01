# Post-drawdown recovery continuation field trial

- Status: `complete`
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

- [x] A fresh worker begins with no source checkout or original conversation,
      reads the current corrected handoff through public installed surfaces,
      and distinguishes it from the superseded Report and governing Review.
- [x] The worker recognizes the request as a related new Study in the same
      Project, not a new Project, Report correction, editable Session, or
      continuation of the old evaluation objective.
- [x] Every prior Run, Report, Review, and correction byte remains unchanged;
      only authorized new task data, Study/source, Run, Report, and durable
      research-brief state are added.
- [x] The new Run binds the exact prior episode identity and complete new
      task-local OHLCV identity without relying on prose or ambient inventory.
- [x] The fixed arithmetic independently reconstructs five episodes, 60 XNYS
      sessions, recovery/censoring, peak/trough/terminal book paths, and exact
      reconciled per-holding contributions.
- [x] The new Report cites only bound Run evidence, remains independent of the
      old correction chain, and grants no forecast, Order, or trading authority.
- [x] Public CLI, Orientation, and Studio expose the relation between the new
      Study and prior evidence without implying correction or supersession.
- [x] Every material baseline failure is retained and classified; only a
      reproduced reusable Workbench defect enters the candidate release.
- [x] A fresh candidate worker completes the unchanged assignment using only
      installed public surfaces and independently acquired task data.
- [x] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and clean-clone smokes pass before publication.

## Work

- [x] Define and index the long-lived Project continuation assignment.
- [x] Build an isolated installed-`0.9.17` desk from the corrected evidence.
- [x] Run and audit one fresh worker without coaching.
- [x] Admit and implement only reproduced reusable product friction.
- [x] Replay the unchanged task with a fresh candidate-wheel worker.
- [x] Complete the release audit and publish `v0.9.18` if warranted.

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
- 2026-08-01 — The untouched `0.9.17` worker completed the quantitative task,
  but Core had no first-class prior-Run input. It copied the selected episode
  rows into a fixed strategy JSON whose prose records the source Run and
  artifact hashes. The new Run freezes only that copied file; public Study,
  Run, Report, Orientation, and Studio contracts cannot mechanically prove the
  declared source relationship.
- 2026-08-01 — Run-bound Report request selection is coupled to the Book Risk
  implementation directory. A custom fixed Study request under
  `strategies/ohlcv-book-path-recovery/` silently fell back to the Project-root
  Path Stress request and produced one immutable but non-authoritative Report.
  The worker detected the mismatch, moved the same files beneath
  `strategies/book-risk-studies/<study-id>/`, reran, and published the correct
  Report. Study request ownership needs an explicit general contract rather
  than a path-name heuristic.
- 2026-08-01 — Two related fixed descriptive Studies without the specialized
  Factor/Portfolio/RL research program leave `aq orient` at
  `study-selection-required`, even when the second Study is the unique derived
  continuation and already has a current Report. The same explicit upstream
  relation should select and disclose that terminal continuation without
  inventing desk lanes or a universal research DAG.
- 2026-08-01 — The candidate repair is deliberately narrow: one optional
  upstream immutable Run with one or more exact declared artifacts, one
  explicit Study-owned Research Request binding, and terminal-continuation
  orientation derived from that relation. It will not add shared data,
  automatic data reuse, arbitrary multi-Run synthesis, or trading semantics.
- 2026-08-01 — The candidate now implements that narrow contract. Study load
  verifies a strict exact request, optional matching position snapshot, one
  prior immutable Run, and selected declared artifact hashes. Runs freeze the
  binding and bytes, Report publication follows the Run-owned request instead
  of a directory convention, and Orientation/Studio expose a unique terminal
  single-parent continuation. Legacy Studies omit all new fields and preserve
  their serialization and input identity.
- 2026-08-01 — Release process knowledge no longer belongs in an ever-growing
  README. [[docs/design/versioning-and-release]] now owns increment semantics,
  compatibility limits, audit, tagging, and host-pin independence; [[AGENTS]]
  routes contributors there, [[docs/STATUS]] retains release evidence, and
  README has been reduced to product orientation, current version, quick start,
  and links.
- 2026-08-01 — The first installed-`0.9.18` candidate worker completed the
  continuation and preserved old immutable bytes, but it exposed two final
  ergonomics defects rather than satisfying the requested one-Run shape. The
  generic CLI required a non-empty `--editable`, so the worker dropped to the
  installed Python API to create a fixed Study. It then retained one stale
  successful Run and one failed Run before the authoritative Run. After the
  authoritative Run-bound Report, Orientation also suggested `session start`
  even though the Study's declared editable closure was empty. These are
  reusable Workbench defects, not scientific failures or reasons to delete the
  immutable attempts.
- 2026-08-01 — The candidate now provides mutually exclusive `--editable` and
  `--no-editable` construction. Any successful fixed Study with an empty
  editable closure routes to generic immutable Run review, and its reported
  terminal state exposes only `report show`; it never advertises impossible
  Session authority. The installed-candidate Project re-oriented under the
  repaired source with `review.status=complete`, no primary action, one
  `report.show` supporting action, and the exact continuation binding.

## Verification

Baseline evidence:

- release wheel:
  `auto_quant-0.9.17-py3-none-any.whl`, SHA-256
  `0414bd960f1f4c51499ac9c1373d2a8c381ac7a48a8ebfc88ed507be53b7e9b7`;
- isolated root: `/Users/ame/autoquant-v0918-recovery-baseline`;
- fresh Grok 4.5 session:
  `019fbcce-ff36-7c52-9213-fe3a0f76d478`, exported as
  `baseline-transcript.md` beside the desk;
- authoritative new Run:
  `run-20260801T102031571809Z-68a31fdbc99d`; authoritative new Report:
  `report-20260801T102039968406Z-b8ca3dc6a2f7`;
- public `study list`, `run list`, `report list`, `orient`, `studio snapshot`,
  and `validate` succeeded; `aq session list` remained empty;
- `diff -qr` proved every pre-existing Run, Report, Review, and correction
  package unchanged. Only the new task-local dataset, Study/Judge/source, two
  Runs, two Reports, and maintained Markdown changed. The first Run/Report is
  retained evidence of the request-binding miss;
- independent standard-library recomputation over the frozen OHLCV reproduced
  all five 60-session paths, recovery dates, peak/trough/terminal values, and
  per-asset contribution reconciliation within `1.2e-16`. Rank 1 recovered on
  2020-05-08 after 36 sessions; ranks 2–5 were right-censored.

Record candidate replay, focused/full tests, builds, and installed/clean-clone
smokes below as they are produced.

First candidate replay evidence:

- wheel: `auto_quant-0.9.18-py3-none-any.whl`, SHA-256
  `bf113ea3b665098c97bc27d254eebb3c7a2dcb76edb0d9ed2ae2a02ebfc972b1`;
- isolated root: `/Users/ame/autoquant-v0918-recovery-candidate`;
- Grok 4.5 session: `019fbcff-aa60-7f10-94f1-a69897f37ee9`, exported as
  `candidate-transcript.md` beside the desk;
- authoritative Run: `run-20260801T111139428486Z-14b79eebcaea`; Report:
  `report-20260801T111215023163Z-13aa09b21783`; zero Sessions;
- the prior Study, Run, original Report, and corrected Report are byte-for-byte
  unchanged. The candidate added one Study, three immutable attempts (two
  successful with the first made stale by the corrected Study definition and
  one failed for a fixed dependency-path miss), one current Report, task-local
  data/source, and maintained Markdown;
- public validation, orientation, Study/Run/Report/Session lists, and Studio
  snapshot succeeded. The authoritative Run freezes the exact upstream Run,
  result/input hashes, selected artifact hashes and bytes, explicit request and
  position snapshot, and complete task-local dataset identity;
- independent standard-library recomputation reproduced all five outcomes:
  rank 1 recovered on `2020-05-08` after 36 sessions with terminal book value
  `1.055031875800815`; ranks 2–5 remained censored with terminal values
  `0.8016736733179449`, `0.900193418584245`, `0.827026512586498`, and
  `0.80653455214537`. Maximum contribution residual was
  `1.1796119636642288e-16`.

Final candidate replay evidence:

- wheel: `auto_quant-0.9.18-py3-none-any.whl`, SHA-256
  `85838bcdc2d85251b1cc1ab0d943426bd6578a6dfd7fa5b8a700aedf6e65bc43`;
- isolated root: `/Users/ame/autoquant-v0918-recovery-final-candidate`;
- fresh Grok 4.5 session: `019fbd14-3acb-7120-b69b-c6d58dd67d23`,
  exported as `final-candidate-transcript.md` beside the desk;
- the unchanged assignment completed with exactly one new fixed Study
  (`ohlcv-book-path-recovery`), one successful Run
  (`run-20260801T113412099979Z-5b156acfd245`), one independent current Report
  (`report-20260801T113445204292Z-5cbd86fd7828`), and zero Sessions;
- every pre-existing file except the explicitly maintained `research.md` is
  byte-identical. Recursive hashes separately prove the original Study, Run,
  original Report, corrected Report, and its embedded governing Review are
  unchanged;
- installed public `validate`, `orient`, Study/Run/Report/Session lists,
  `study inspect`, and Studio snapshot all pass. Orientation selects the
  recovery Study, exposes the exact upstream binding, reports complete, and
  offers only `report.show`—no impossible Session action;
- the new Run records installed Harness `0.9.18`, Python `3.11.14`,
  `dirty=false`, request SHA-256
  `1d727441a762b8423e3dae3d869d28455e3a695a8021605e27958a53171564d5`,
  upstream episode SHA-256
  `5aae52ecefb84a2db8557bd9e8a96325032972896fa5c874c8cb3480b31dca14`,
  exact prior result/Study-input identities, and complete task-local Yahoo
  package identity. The Report projects the same Run-owned request/upstream
  evidence and has `correction: null`;
- independent standard-library recomputation again reproduced the exact five
  recovery outcomes and a maximum contribution residual of
  `1.1796119636642288e-16`.

## Progress log

- 2026-08-01 — Plan activated from clean released `v0.9.17`; OpenAlice remains
  independently pinned to `v0.8.31`.
- 2026-08-01 — Untouched installed-wheel baseline completed in 11m02s. It
  produced scientifically correct evidence while preserving every old byte,
  and retained three concrete long-lived-Project contract failures for the
  `0.9.18` candidate rather than hiding them.
- 2026-08-01 — Implemented the three reproduced contract repairs and added
  focused Study, Run, CLI, Report, Orientation, and Studio projections. Six
  new focused public-boundary tests pass; the complete affected four-module
  regression passes 44 tests in 66.572 seconds. Documentation links resolve
  after extracting the release policy from README.
- 2026-08-01 — First installed-candidate replay completed in the same long-lived
  Project and proved the new request/upstream binding end to end. Its retained
  intermediate Runs exposed the missing fixed-Study CLI form and impossible
  Session suggestion. Added `--no-editable`, generic fixed-Run orientation,
  terminal fixed-Report orientation, and focused regressions before scheduling
  one final candidate replay.
- 2026-08-01 — The complete affected Study/Run/Session/Run-Report/Orientation/
  CLI/repository regression passes 85 tests in 123.288 seconds after the final
  fixed-Study repair. `uv lock --check`, Python compilation, capability/help
  discovery, diff checks, and all 1,380 documentation links also pass.
- 2026-08-01 — Final installed-candidate Grok replay completed the unchanged
  assignment with the requested one-Study/one-Run/one-Report/zero-Session shape.
  The worker used `--no-editable`; every immutable predecessor remained exact;
  installed Orientation terminated at Report inspection without Session
  authority; independent arithmetic and public CLI/Studio audits passed.
- 2026-08-01 — Installed capability smoke found that `study.create` help and
  behavior exposed request/upstream binding while the machine-readable
  capability descriptor still omitted those four options. Added exact
  `request-path`, `position-snapshot-path`, `upstream-run`, and
  `upstream-artifact` arguments plus a capability regression. This is a
  disclosure-only repair after the successful replay, not a change to its
  executed semantics.
- 2026-08-01 — Final release audit passed 409 tests in 1,016.375 seconds,
  1,380 documentation links, lock/diff/Python/Studio syntax, and focused
  post-audit capability checks. The final source distribution and wheel built
  successfully; wheel SHA-256 is
  `80da774d7968fc5efa5e1e7909dd031b5815e2954b2c7d3c158c8b977ddc8817`.
  A fresh Python 3.11.14 environment installed that exact wheel and disclosed
  all 57 commands, the six fixed/continuation Study arguments, and changed
  Study/RunResult/Agent Work Brief/Session schemas. A no-hardlink clean clone
  with no local override loaded only `sample-research-desk`, then passed root
  Project listing, validation, orientation, and Studio snapshot through the
  installed wheel.

## Completion

All acceptance checks are independently satisfied. The released behavior was
proved first against the untouched `0.9.17` baseline, then twice from installed
`0.9.18` wheels without a source checkout. The final replay preserved the
long-lived Project and every prior immutable byte while completing one related
Study through one evidence-bound Run and Report. `v0.9.18` is ready to tag and
publish; OpenAlice remains independently pinned to `v0.8.31`.
