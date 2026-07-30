# Make post-trial research agendas explicitly optional

- Status: `completed`
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

- [x] A post-Experiment review with no primary action labels every agenda move
      optional and never describes another edit as required.
- [x] Active pre-Experiment candidate-edit routing remains unchanged.
- [x] CLI, Studio, docs, and a fresh Agent replay agree.

## Work

- [x] Audit agenda status/priority fields against Work Brief phases.
- [x] Add the smallest explicit optionality contract and regressions.
- [x] Retest the originating one-Experiment negative assignment.

## Findings and decisions

- 2026-07-30 — Proposal preserves unstructured English research briefs; Core
  will not guess a numerical budget from caller prose.
- 2026-07-30 — A second materially different installed-wheel worker reproduced
  the ambiguity after a REVERTed sector Factor trial was reported and
  completed. Orientation correctly had no primary action and made
  `session.start` optional, but the agenda still presented its first move as
  `Experiment 1`/priority 1 without a machine-readable post-trial role. This
  satisfies the employability plan's two-assignment recurrence rule.
- 2026-07-30 — The smallest contract is a Work-Brief-level agenda presentation
  role derived from lifecycle state, not prose parsing or removal of useful
  evidence. CLI and Studio must consume that exact role rather than inferring
  optionality independently.
- 2026-07-30 — `researchAgenda.moveRole` uses exactly three states:
  `current-research-guidance`, `optional-follow-up`, and `unavailable`.
  Available moves become optional when immutable trial history exists and
  there is no primary action, or when required research is terminally
  complete. An active pre-trial edit retains current guidance.

## Verification

- Focused agenda/orientation/Check/CLI/Studio regression: 56 tests passed in
  84.657 seconds.
- The preserved sector trial projected `moveRole: optional-follow-up`,
  `primaryAction: null`, terminal text `Optional follow-up 1`, and the same
  role in Studio under the changed development Harness. Studio correctly
  marked the old Session Harness stale rather than treating new source as its
  historical `0.8.28` runtime.
- Fresh isolated Grok Build replay used the exact `0.8.29` wheel
  (`1d1e37a…307fcc`) from clean commit `d45b100`. It independently adopted
  the unchanged staged task, created one Project, wrote the brief before Runs,
  passed one Check, and spent one Experiment. Its candidate KEEP improved
  validation mean IC from `-0.119921` to `-0.097214` but remained
  `raw-predictive-edge-absent`; the worker correctly published, promoted,
  stopped, and made no Portfolio/RL/Order claim.
- Final installed-wheel orientation returned method v10,
  `required-research-complete`, `primaryAction: null`, and
  `moveRole: optional-follow-up`. Studio was valid with zero diagnostics and
  projected the same role. All staged input hashes remained unchanged.
- Full repository regression: 326 tests passed in 851.125 seconds.
- Documentation graph: all 1,162 links resolve. Python compilation, Studio
  JavaScript syntax, lock check, diff check, source/wheel build, fresh Python
  3.11 wheel install, public version discovery, strict Explorer, Report,
  promotion, Project validation, and Studio smoke passed.

## Progress log

- 2026-07-30 — Proposed from the zero-retry `0.8.28` installed-wheel field
  trial.
- 2026-07-30 — Activated after
  `cohort-01-sector-factor-portfolio` independently reproduced the same
  post-trial presentation ambiguity.
- 2026-07-30 — Implemented the shared move-role contract and its CLI/Studio
  presentation; focused regression and preserved-Project projection pass.
- 2026-07-30 — The fresh installed-wheel worker stopped at the correct
  terminal boundary on a KEEP-but-scientifically-negative result. Independent
  replay reconciled every material claim and the optional role.

## Completion

Completed. Post-trial hypotheses remain inspectable without being presented as
unfinished required work, and active pre-trial routing is unchanged.
