# Make completed trial evidence a first-class Session handoff

- Status: `completed`
- Updated: `2026-07-29`
- Originating Project:
  `/Users/ame/2607AutoQuant/quant-workspace/projects/grok-build-real-multiinterval-v0815`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]], and
  [[docs/design/evidence-driven-research-agenda]].

## Outcome

After an immutable Experiment restores the Session leader, a Coding Agent sees
one truthful trial-review handoff instead of an unconditional demand for
another edit. The Work Brief separately projects the current candidate Check
and the latest Experiment's exact verdict, Run, and preflight Check, retaining
that historical link after Report publication and Session completion.

## Context

A fresh Grok Build coworker used only an installed AutoQuant `0.8.15` CLI and
an unchanged OpenAlice-style request plus content-locked V2 hourly package. It
independently selected `ohlcv-research-desk`, read the exact
`1h + 3h/4h/6h/12h/1d` candidate contract, implemented one causal
pullback-by-completed-12h-breadth candidate with legal
`cross-sectional-score` / `timestamp-context` roles, passed preflight, and
completed one REVERT Experiment.

The Experiment correctly restored the baseline. Before Report publication,
orientation nevertheless labeled the unchanged worktree `CANDIDATE EDIT
REQUIRED`. The Agent had to prefer its external one-trial boundary and discover
`report.publish` from another command response. After publishing and completing
the Session, the Work Brief kept the Session/Report but exposed neither the
latest Experiment nor its exact passed Check.

## Scope

### In scope

- Detect an active Session whose worktree matches its leader and which has at
  least one immutable Experiment.
- Replace unconditional edit language with an explicit trial-review choice:
  publish/complete current evidence when delegated, or deliberately declare a
  new bounded hypothesis.
- Keep Report publication and read-only Session inspection available as
  supporting commands without automatically closing the Session.
- Add a strict nullable latest-Experiment projection containing Experiment id,
  verdict, candidate Run id/source hash, and the latest matching pre-Experiment
  Check id/status.
- Preserve this projection for active and completed Sessions through CLI,
  JSON schema, human orientation, and Studio.
- Keep `candidateCheckId` / `candidateCheckStatus` scoped to the exact current
  candidate rather than silently changing their meaning.

### Out of scope

- Inferring a trial budget from ordinary prose or automatically stopping after
  one Experiment.
- Automatically publishing a Report, completing a Session, starting another
  Session, or promoting source.
- Treating a Check as selection evidence or making Experiment verdicts
  scientific qualification.
- Rewriting immutable `0.8.15` Experiment, Check, Report, or Session artifacts.

## Acceptance

- [x] An active baseline-restored Session with Experiment history no longer
      says another candidate edit is required.
- [x] Delegated trial review exposes `report.publish` and `session.show`
      supporting actions while keeping the Agent/caller in control.
- [x] A strict `latestExperiment` projection identifies the last immutable
      verdict and candidate Run for active and completed Sessions.
- [x] When a passing Check preceded that exact candidate Experiment, its id and
      status remain attached after REVERT/CRASH restore and Session completion.
- [x] Initial edit, changed candidate, failed/passed Check, settled KEEP,
      Report gate, promotion, and freeze-agenda routes remain unchanged.
- [x] CLI, schema, human output, Studio, tests, docs, build/install smoke, and
      an installed-state replay all agree.

## Work

- [x] Reproduce the multi-interval worker's intake, Check, REVERT, Report,
      completion, final Work Brief, and immutable evidence.
- [x] Separate current-candidate Check semantics from historical trial
      traceability.
- [x] Implement trial-review orientation and latest-Experiment projection.
- [x] Add regression coverage and update public contracts/docs.
- [x] Complete installed-state replay and release verification.

## Findings and decisions

- 2026-07-29 — The worker's one-trial limit belongs to its delegated
  assignment, not Core. Core must expose the choice faithfully without
  inventing automatic stop/continue authority.
- 2026-07-29 — `candidateCheckId` is intentionally current-candidate evidence.
  Historical trial evidence needs a separate typed projection rather than a
  semantic overload.
- 2026-07-29 — Matching a Check to an Experiment requires the same candidate
  source hash and a Check completion time no later than Experiment start.
  A later rerun of the same source cannot be retroactively attributed.

## Verification

- Focused high-risk Check, orientation, CLI, Report, and research-program
  regression passed 64 tests in 118.370 seconds.
- The exact repository suite passed 306/306 tests in 886.197 seconds.
- The documentation graph resolved 1,069/1,069 checked links; JavaScript syntax
  and repository diff checks passed.
- A fresh Python 3.11 environment installed the `0.8.16` wheel and reproduced
  one passing Check, one REVERT, explicit trial review, Report-bound
  completion, persistent Experiment/Run/Check projection, Project validation,
  and exact CLI/Studio Work Brief parity using public commands only.

## Progress log

- 2026-07-29 — Originating Experiment
  `exp-0001-096c849038b4` REVERTed candidate Run
  `run-20260729T153819638110Z-500559f45737`; passed Check
  `check-20260729T153814029674Z-b87f8d42b5aa` preceded it. Report
  `report-20260729T153933853847Z-e334ccf7fb50` completed the baseline-retaining
  Session with no promotion or downstream lane.
- 2026-07-29 — Installed `0.8.16` public replay Project
  `installed-trial-handoff-v0816` passed its Check, REVERTed one Experiment,
  exposed explicit trial review, made completion primary after Report
  publication, retained the Experiment/Run/Check link after completion, and
  matched CLI with Studio exactly.

## Completion

Completed on 2026-07-29. The originating worker's two low-severity
observations are resolved without inferring prose trial budgets, automatically
mutating research state, weakening immutable evidence, or changing the meaning
of the current-candidate Check pointer.
