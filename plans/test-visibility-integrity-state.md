# Distinguish visible test audit from test-guided iteration

- Status: `proposed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0827-final-price-volume/desk/workspace/projects/grok-price-volume-factor-v0827-final`
- Related design: [[docs/design/research-selection-integrity]] and
  [[docs/design/frozen-external-holdout-challenge]].

## Outcome

Selection-integrity evidence distinguishes a first formal evaluation that
merely reveals visible test audit from a later candidate edit that could have
used that knowledge, without weakening the requirement for fresh external
evidence before a production-grade claim.

## Context

After exactly one formal Experiment and no post-test edit, the final `0.8.27`
worker saw `externalHoldoutRequired: true` with
`required-after-test-guided-iteration`. The conservative production boundary
is useful, but the label overstates the actual history: test became visible;
no test-guided candidate iteration occurred.

## Scope

### In scope

- Model and project visible-test exposure separately from a subsequent source
  change.
- Preserve conservative production-claim and external-holdout guidance.

### Out of scope

- Hiding test evidence, allowing test to select, or weakening family-wise
  adjustment.

## Acceptance

- [ ] First evaluation and post-visibility edit have distinct truthful states.
- [ ] Report, Session, Dossier, CLI, and Studio preserve the distinction.
- [ ] Existing no-test-selection and external-holdout safety remain intact.

## Work

- [ ] Audit immutable timestamps/source hashes needed to reconstruct exposure
      and later edit.
- [ ] Define the smallest backward-readable state model before implementation.

## Findings and decisions

- 2026-07-30 — Proposal recorded without assuming that a one-Experiment
  assignment grants production authority.

## Verification

- Pending.

## Progress log

- 2026-07-30 — Proposed from the `0.8.27` final Factor field trial.

## Completion

Pending.
