# Agent route discovery and Run-bound Reports

- Status: `completed`
- Updated: `2026-08-01`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/research-program-orchestration]], and
  [[docs/design/run-bound-research-reports]].

## Outcome

Let a fresh coding Agent select the correct Project construction before intake
and publish analysis over an already immutable delegated Run without creating
an empty editable Session. A coordinated Factor-to-Portfolio assignment should
therefore move from intake to Dossier through truthful objects on its first
route.

## Context

The clean `0.9.4` relative-value Portfolio field trial completed correctly but
exposed two reusable Workbench gaps. The worker first selected
`ohlcv-portfolio-lab`, discovered only after a successful baseline that this
single-lane Lab could not coordinate Factor-to-Portfolio admission, removed
the pristine attempt, and repeated intake as `ohlcv-research-desk`. It then had
to start two delegated Sessions solely to publish Factor and Portfolio Reports
over byte-identical frozen baselines, despite being instructed not to edit or
experiment.

Both gaps are visible in the trial Project's `framework-needs.md`. Template ids
are currently choices without public fit/anti-fit contracts, and Research
Reports are physically and semantically owned only by Sessions even though a
Run is already immutable evidence. Session means bounded editable
investigation; using it as a generic report folder creates false research
activity and makes Agent instructions contradictory.

## Scope

### In scope

- Add one public CLI/JSON template route catalog with purpose, required lanes,
  positive fit, anti-fit, and an exact recommendation rule.
- Surface the route catalog from project creation/intake help and capability
  discovery; make the coordinated Research Desk unmistakable whenever Factor
  evidence must feed Portfolio or RL in one Project.
- Add an immutable Project-owned Report route bound directly to one successful
  current Study Run and the verified Project intake request.
- Preserve Session-bound Reports for actual editable investigation while
  projecting both report anchors consistently through CLI, orientation,
  Research Program, Dossier, Studio, validation, and Markdown.
- Make a current Run-bound lane Report satisfy coordinated Dossier admission
  without manufacturing a Session, Check, Experiment, or completion receipt.
- Prove the behavior with a fresh installed-wheel coworker on a genuinely
  coordinated delegated assignment.

### Out of scope

- Automatic natural-language template classification or a universal task DSL.
- Changing Factor, Portfolio, RL, Judge, qualification, or selection rules.
- Making Reports mandatory for fixed single-lane Labs.
- OpenAlice version changes, Inbox publication, Broker, Order, or trading
  authority.
- Compatibility shims for unpublished historical report layouts outside the
  repository.

## Acceptance

- [x] `aq project templates` returns a strict human/JSON route catalog and
  explicitly routes Factor-to-Portfolio, Factor-to-RL, and multi-Study work to
  `ohlcv-research-desk` before Project creation.
- [x] `aq report publish --study ... --run ...` accepts exactly one successful
  current Run for a request-bound Project, verifies analysis references, and
  writes an immutable Project-owned Report with no Session identity.
- [x] Run-bound and Session-bound Reports expose an explicit anchor kind and
  retain exact request, Study, Run, Harness, dataset, selection-integrity, and
  decision-support evidence.
- [x] Coordinated program, Dossier, orientation, CLI, and Studio accept the
  current Run-bound Report and show zero Sessions/Experiments for a frozen
  baseline lane.
- [x] Invalid/stale/wrong-Study/failed/non-request-bound Runs, mixed selectors,
  forged reports, symlinks, and evidence references fail explicitly.
- [x] Focused tests, complete regression, doc links, JavaScript syntax, build,
  installed-wheel smoke, and clean-clone checks pass.
- [x] A fresh uncoached coworker selects the Research Desk on the first attempt
  and publishes coordinated evidence without report-only Sessions.

## Work

- [x] Reproduce both Project-derived gaps from the preserved `0.9.4` field
  trial and choose a truthful domain model.
- [x] Implement and test the public Project-template route catalog.
- [x] Implement Project-owned Run-bound Report publication, loading, listing,
  verification, and shared anchor projection.
- [x] Integrate Run-bound Reports with Research Program, Dossier, orientation,
  CLI, Studio, schemas, and validation.
- [x] Update Agent guidance, lifecycle/design docs, README, STATUS, and sample
  evidence where applicable.
- [x] Complete installed-wheel coworker acceptance and final release audit.

## Findings and decisions

- 2026-08-01 — A Session is an editable investigation, not a mandatory wrapper
  around analysis. The new path will bind a Report directly to an immutable
  current Run instead of naming an empty Session a special report-only mode.
- 2026-08-01 — Route selection remains Agent judgment. Core will publish a
  small explicit catalog and deterministic composition rules, not infer a lane
  from arbitrary prose.
- 2026-08-01 — Existing Session Reports remain valid research objects because
  their Experiment prefix is meaningful. Run-bound Reports are a second honest
  anchor, not a replacement for editable-session provenance.
- 2026-08-01 — The installed-wheel worker selected the Research Desk on its
  first attempt and completed Factor-to-Portfolio with two Runs, two Run-bound
  Reports, one Dossier, and zero Sessions/Checks/Experiments. Its only reusable
  friction was Orientation preferring `session.start` before a frozen Run
  Report; final source now promotes `report.publish` only when the verified
  agenda freezes in-sample work and has no editable target.

## Verification

- Focused Report, Dossier, Program, Orientation, Studio, CLI, and Session
  regression passed all 79 tests in 234.171 seconds after the worker-derived
  Orientation refinement.
- The final complete regression passed all 368 tests in 929.173 seconds.
- Documentation resolution passed all 1,271 links; Studio JavaScript syntax,
  compilation, diff whitespace, lock refresh, source/wheel build, and fresh
  Python 3.11 installed `aq 0.9.5` capability/template smoke passed.
- Fresh Grok 4.5 cohort 09 used only the installed wheel, selected
  `ohlcv-research-desk` on its first attempt, executed one Factor and one
  Portfolio Run, published both without a Session, and returned a verified
  Dossier with zero Check/Experiment history. Trial evidence lives outside the
  repository under `grok-field-trials/cohort-09-route-run-report-v095/`.

## Progress log

- 2026-08-01 — Plan created from the clean `0.9.4` installed-wheel Grok trial
  and indexed before implementation.
- 2026-08-01 — Public route catalog, Project-owned Run Reports, explicit
  anchors, precedence, Program/Dossier/Orientation/Studio projection, and
  adversarial regressions implemented.
- 2026-08-01 — Installed-wheel cohort 09 satisfied the route and zero-Session
  acceptance; its Orientation note produced one bounded final guidance fix.

## Completion

AutoQuant `0.9.5` now gives a fresh Agent one truthful route before intake and
two truthful Report anchors after execution. Frozen delegated evidence can
reach a coordinated Dossier without false Session activity, while any real
Session history remains mandatory provenance and takes precedence. The final
Grok trial selected the right desk on its first attempt and completed the
Factor-to-Portfolio handoff with zero editable-research objects.
