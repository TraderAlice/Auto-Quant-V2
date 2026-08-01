# First-baseline candidate preflight

- Status: `active`
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

- [ ] A fresh invalid first candidate fails before any full Run or Session and
  leaves the Project lifecycle count and filesystem free of partial artifacts.
- [ ] A valid first candidate passes the exact fixed guard, creates one
  baseline and Session, and retains tamper-checked baseline-preflight
  provenance with explicit no-selection/no-trading authority.
- [ ] Exact reusable baselines and Studies without preflight preserve their
  established behavior and disclose why no new guard ran.
- [ ] CLI, JSON, orientation, Studio, schemas, capabilities, generated Skills,
  and Agent documentation describe the same first-candidate route.
- [ ] A fresh installed-wheel coworker independently recovers from one rejected
  first candidate and produces exactly one formal scientific Run after repair.
- [ ] Focused tests, full regression, documentation links, build, installed
  smoke, clean-clone smoke, and remote branch/tag identity pass for `v0.9.27`.

## Work

- [ ] Define the reusable preflight executor and baseline receipt contract.
- [ ] Integrate atomic pre-baseline gating into Session start and strict load.
- [ ] Complete CLI/orientation/Studio/schema/capability surfaces and tests.
- [ ] Advance version and public documentation; run a fresh coworker field
  assignment from a clean installed wheel.
- [ ] Complete release verification, tag, push, and remote identity audit.

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

Pending.

## Progress log

- 2026-08-02 — Plan created immediately after publishing `v0.9.26`, from the
  common lifecycle friction retained by both installed-wheel field trials.

## Completion

Pending.
