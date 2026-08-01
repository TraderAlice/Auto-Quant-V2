# First-baseline candidate preflight

- Status: `completed`
- Updated: `2026-08-02`
- Target release: `0.9.27`
- Related design: [[docs/design/candidate-preflight-feedback]],
  [[docs/design/research-session-loop]],
  [[docs/design/agent-cli-contract]], and
  [[plans/multi-source-observed-factor-packaging]].

## Outcome

Make the first caller-relevant editable candidate pass its fixed seconds-scale
preflight before AutoQuant spends a complete baseline Run, while preserving
the existing rule that only the full Judge can create selection evidence.
Invalid first candidates must leave no Run, Session, partial directory, or
invented scientific result; valid candidates must enter the ordinary governed
Session with exact preflight provenance discoverable by a replacement Agent.

## Context

The original candidate-preflight release correctly governs edits inside an
active Session. It deliberately rejects an unchanged Session leader. A later
research-integrity improvement established a different first-candidate rule:
the template candidate is only an API demonstrator, so an Agent must replace it
with one predeclared caller-relevant candidate before `session start` creates
the baseline.

Those two correct rules now leave a lifecycle gap. `session start` immediately
executes or reuses the complete baseline, whereas `session check` exists only
after Session creation and requires a post-baseline edit. Both independent
`0.9.26` Grok coworkers therefore attempted an unchanged Check after the one
formal baseline Run while trying to obey a request for preflight-first work.
The CLI rejected the redundant Check safely, but the first complete evaluation
had already happened without the fast guard.

This release closes that narrow gap. It does not add a second evaluator or
require Agents to manufacture a candidate edit merely to obtain a Check.

## Scope

### In scope

- When no exact successful baseline is reusable and the Study has a fixed
  preflight, make `session start` execute that contract against the canonical
  Project candidate before `execute_study`.
- Use the same isolated workspace, exact candidate/data/Study/preflight/Harness
  identity, timeout, structured output, and no-selection authority as ordinary
  Session Checks.
- Fail `session start` structurally on a failed or malformed preflight without
  creating a Run, Session, check history, or partial Session directory.
- On success, create the ordinary baseline and Session, then retain an exact
  immutable baseline-preflight receipt inside the Session. Validate it on
  every load and project it through CLI JSON, human output, orientation, and
  Studio.
- When an exact successful baseline is reused, disclose that the full verified
  Run—not a newly executed preflight—is the reuse authority. Do not rerun an
  operational guard merely to decorate old evidence.
- Keep post-edit `session check` unchanged: it remains a distinct immutable
  diagnostic bound to a changed worktree candidate.
- Add deterministic Factor, Portfolio, RL, legacy-no-preflight, reusable-
  baseline, tamper, timeout/malformed-output, atomic failure, CLI, orientation,
  Studio, and installed-package tests.
- Prove the route with a fresh installed-wheel coworker that authors one bad
  first candidate, receives a fast pre-baseline rejection with zero Runs and
  Sessions, repairs it, then completes one bounded scientific baseline and
  truthful handoff.

### Out of scope

- Giving preflight any metric, KEEP/REVERT verdict, trial-family role,
  qualification, downstream admission, promotion, or trading authority.
- Replacing or weakening the complete Judge, making post-edit Checks mandatory,
  or blocking direct explicit `run execute`.
- Persisting failed preflight attempts as Runs, Experiments, Sessions, or
  research evidence.
- Automatically repairing candidates, editing canonical source inside
  `session start`, or adding a general lint framework.
- Changing fixed Studies, historical Run identity, or host upgrade behavior.

## Acceptance

- [x] A fresh invalid first candidate fails before any full Run or Session and
  leaves the Project lifecycle count and filesystem free of partial artifacts.
- [x] A valid first candidate passes the exact fixed guard, creates one
  baseline and Session, and retains tamper-checked baseline-preflight
  provenance with explicit no-selection/no-trading authority.
- [x] Exact reusable baselines and Studies without preflight preserve their
  established behavior and disclose why no new guard ran.
- [x] CLI, JSON, orientation, Studio, schemas, capabilities, generated Skills,
  and Agent documentation describe the same first-candidate route.
- [x] A fresh installed-wheel coworker independently recovers from one rejected
  first candidate and produces exactly one formal scientific Run after repair.
- [x] Focused tests, full regression, documentation links, build, installed
  smoke, clean-clone smoke, and remote branch/tag identity pass for `v0.9.27`.

## Work

- [x] Define the reusable preflight executor and baseline receipt contract.
- [x] Integrate atomic pre-baseline gating into Session start and strict load.
- [x] Complete CLI/orientation/Studio/schema/capability surfaces and tests.
- [x] Advance version and public documentation; run a fresh coworker field
  assignment from a clean installed wheel.
- [x] Complete release verification, tag, push, and remote identity audit.

## Findings and decisions

- 2026-08-02 — The two final `0.9.26` workers independently reached the same
  safe-but-confusing unchanged-Check rejection after their only baseline. The
  repeated behavior is treated as a missing lifecycle affordance, not an Agent
  prompt defect.
- 2026-08-02 — The first guard belongs inside `session start`, because that is
  already the public operation that owns fresh baseline creation. A separate
  command would make Agents coordinate another transient state and could race
  source changes between guard and Run.
- 2026-08-02 — Failed guards are operational feedback, not research evidence.
  They must be returned structurally but must not consume Run, Experiment, or
  Session identity. Successful provenance becomes durable only with the
  Session whose baseline it guarded.

## Verification

- Focused Core, Session, CLI, orientation, Studio, template, and repository
  tests passed, including atomic failed/malformed/timed-out guards, exact
  successful receipt validation, no-preflight Studies, reusable baselines, and
  tamper rejection. Python compilation passed and all 1,465 documentation
  double-links resolved.
- The complete deterministic suite passed: `442` tests in `1072.298s`.
- Candidate build audit at commit `65b030e` produced wheel SHA-256
  `f5e885a3db86876417e20b4f241675f714026ee579459845768ccfb207af1524`
  and sdist SHA-256
  `e6e4f79bb6ed8406759db2ff7e0117c201d383d07ed390042bfc59e5e907509d`.
  A fresh Python 3.11 install reported exact clean embedded provenance, exposed
  all three `baselineGuard` modes in the public Session schema, and passed
  root orientation, validation, Project discovery, and Studio snapshot in a
  `git clone --no-local` checkout without local override.
- Fresh Grok 4.5 field trial:
  `/Users/ame/2607AutoQuant/grok-field-trials/cohort-40-first-baseline-preflight-v0927`.
  The isolated installed wheel at candidate commit `246a43e` has SHA-256
  `bec31ede775160f3e03cd5fccd921e503e828fe04dc8a6f6838cd95aed2dbc70`;
  Grok Session `019fbf8e-41f4-7802-bfc1-0865651853c1` and transcript SHA-256
  `bd1c49b755562dffa0942ac7e7ffc86b1682d9a8ec0c2051b6c10b565a4bf4ec`
  preserve the independent route.
- The coworker authored the requested type-invalid first candidate, received
  `session.baseline-preflight-failed` plus `session.factor.type`, and verified
  zero Runs and Sessions. It repaired only the output contract, then created
  exactly Run `run-20260801T230149722345Z-73c382029b18`, completed Session
  `session-20260801T230201616729Z-77392a101e3a`, and published Report
  `report-20260801T230357510388Z-635a46928d5a`. Receipt
  `b0d5782c01646e7f7d82742ba60393f60e6df45927a27fed21a95dd5ea713242`
  retained explicit no-selection/no-promotion/no-trading authority. There were
  zero CandidateChecks and zero Experiments; the negative Factor result was
  reported without tuning. Independent `verify_field.py` passed.

## Progress log

- 2026-08-02 — Plan created immediately after publishing `v0.9.26`, from the
  common lifecycle friction retained by both installed-wheel field trials.
- 2026-08-02 — Core made `session start` the atomic owner of fresh candidate
  preflight plus baseline creation; public orientation, Studio, schemas,
  capabilities, templates, and documentation converged on that route.
- 2026-08-02 — A fresh installed Grok coworker recovered from the intentional
  zero-artifact guard failure, created exactly one formal Run, retained a
  verifiable no-authority receipt, reported a negative result, and stopped.
- 2026-08-02 — Full regression, documentation, build, installed-runtime, and
  clean-clone audits passed for the release candidate.

## Completion

Completed for `v0.9.27`. The first caller-relevant candidate now has a real
fast feedback path before complete evaluation, while the fixed Judge remains
the sole source of scientific metrics and selection evidence. Failed guards
leave no lifecycle artifacts; passed guard provenance is durable, exact, and
explicitly powerless. The independent coworker required no source inspection
or framework workaround.
