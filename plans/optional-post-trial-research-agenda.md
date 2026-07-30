# Make post-trial research agendas explicitly optional

- Status: `proposed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0828-truthful-first-factor/desk/workspace/projects/grok-price-volume-factor-v0828`
- Related design: [[docs/design/evidence-driven-research-agenda]] and
  [[docs/design/agent-operator-experience]].

## Outcome

When a completed Experiment is awaiting Agent/caller review and orientation has
no required primary action, research-agenda hypotheses remain discoverable but
are unambiguously labeled optional follow-up rather than the default next task.

## Context

The fresh installed-wheel `0.8.28` Grok worker correctly stopped after one
REVERT, published a Report, and completed the Session with no CLI retry. It
nevertheless recorded that the post-trial agenda still prioritized a
`factor-isolate-raw-component` edit even though the Work Brief correctly made
continuation optional and the caller's Markdown assignment allowed only one
Experiment.

Core must not infer a machine trial budget from free-form prose. The smaller
truthful improvement is to align agenda presentation with the existing
`trial-review-required` authority: ideas may be useful, but none is required
until an Agent/caller deliberately chooses another bounded hypothesis.

## Scope

### In scope

- Distinguish required current work from optional next-Session/current-Session
  research ideas in CLI JSON, human orientation, and Studio.
- Preserve evidence-derived diagnoses and candidate hypotheses.

### Out of scope

- Parsing or enforcing budgets from Markdown.
- Automatically suppressing research after REVERT.
- Automatically creating, editing, evaluating, reporting, or completing work.

## Acceptance

- [ ] A post-Experiment review with no primary action labels every agenda move
      optional and never describes another edit as required.
- [ ] Active pre-Experiment candidate-edit routing remains unchanged.
- [ ] CLI, Studio, docs, and a fresh Agent replay agree.

## Work

- [ ] Audit agenda status/priority fields against Work Brief phases.
- [ ] Add the smallest explicit optionality contract and regressions.
- [ ] Retest the originating one-Experiment negative assignment.

## Findings and decisions

- 2026-07-30 — Proposal preserves unstructured English research briefs; Core
  will not guess a numerical budget from caller prose.

## Verification

Pending.

## Progress log

- 2026-07-30 — Proposed from the zero-retry `0.8.28` installed-wheel field
  trial.

## Completion

Pending.
