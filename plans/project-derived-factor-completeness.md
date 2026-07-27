# Project-derived factor completeness

- Status: `completed`
- Updated: `2026-07-28`
- Related design: [[docs/design/project-derived-workbench-needs]],
  [[docs/design/factor-component-attribution]],
  [[docs/design/factor-qualification-funnel]], and
  [[docs/design/research-session-loop]].

## Outcome

Make the Factor workbench faithfully support the two research intents exposed
by a real US cross-sectional Project: discovering information distinct from
known styles and validating one explicitly declared known style. Give
cross-section-constant market context first-class diagnostics, and make every
delegated improved-source promotion preserve an exact immutable Report.

## Context

The `us-large-cap-cross-section` Project successfully expressed a causal
six-component panel factor, but exposed three reusable contract gaps:

1. qualification always interpreted a candidate as a novel-factor claim, so
   an intentional `reversal_5` validation was mechanically rejected for
   having zero style-neutral residual;
2. market breadth and return dispersion were valid timestamp context but were
   misleadingly evaluated as asset-ranking components; and
3. the CLI allowed source promotion before Report publication, closing the
   Session and forcing a duplicate baseline Session solely to publish the
   handoff.

These are Project-observed needs recorded in that Project's
`framework-needs.md`. They affect Core, immutable evidence, CLI, Studio, and
Agent instructions, so they require one coordinated plan.

## Scope

### In scope

- Add one request-bound Factor claim contract distinguishing
  `novel-factor` from `known-style-validation`, with an explicitly named known
  style for the latter.
- Preserve the existing style-neutral funnel for novel-factor discovery while
  giving known-style validation its own identity, raw evidence, temporal
  stability, and statistical diagnosis.
- Add explicit `cross-sectional-score` and `timestamp-context` component roles.
- Give timestamp context train-fixed state thresholds, split occupancy,
  transitions, and conditional final-factor IC rather than fake standalone
  cross-sectional IC.
- Require a delegated KEEP promotion to bind a Report over the exact complete
  current Session prefix.
- Project the new contracts consistently through immutable evidence, CLI,
  Studio, Reports, Dossiers, templates, and Agent documentation.
- Migrate and rerun the originating real Project as acceptance evidence.

### Out of scope

- New data vendors, point-in-time universe construction, sector metadata, or
  corporate-action authentication.
- Automatic strategy search, target-weight construction, RL changes, Broker
  authority, Orders, or live trading.
- Relaxing the fixed HAC threshold or using visible test evidence for
  selection.

## Acceptance

- [x] One strict request can declare either a novel-factor claim or one
  supported known-style validation, and the exact claim is content-locked into
  the Factor Study and Run.
- [x] Novel-factor Runs retain the current raw → residual → blend → stability
  funnel without weakened admission.
- [x] Known-style Runs verify candidate/style identity and use raw
  statistical and chronological stability evidence without requiring a
  nonsensical non-style residual.
- [x] Component evidence distinguishes score and context roles; context
  components receive causal state diagnostics and never enter score-only
  pairwise, residual, or fixed-blend claims.
- [x] A delegated improved Session cannot promote without an exact current
  Report, and the promotion receipt content-locks that Report.
- [x] CLI JSON/human output and Studio render the same verified claim, context,
  and terminal workflow semantics.
- [x] Fast unit tests, full regression, documentation checks, package build,
  and a migrated real-Project rerun pass deterministically.

## Work

- [x] Reproduce the Project-derived needs and reject the false intake-staleness
  hypothesis after tracing the actual promoted-source hash.
- [x] Implement and test the request-bound Factor claim contract.
- [x] Implement and test role-aware component evidence.
- [x] Implement and test Report-bound delegated promotion.
- [x] Update Studio, CLI, templates, and durable design documentation.
- [x] Migrate and rerun the originating Project.
- [x] Complete the requirement-by-requirement audit, commit, and push.

## Findings and decisions

- 2026-07-28 — `study.current: false` in the originating Project is expected:
  its promoted candidate source differs from the original intake source. The
  Project remains valid and its Dossier current, so intake finalization is not
  part of this plan.
- 2026-07-28 — Research intent belongs to fixed request-derived authority, not
  mutable candidate metadata. Candidate declarations may describe components,
  but they cannot choose the qualification claim that judges them.
- 2026-07-28 — Timestamp context is causal explanatory state, not an
  asset-ranking score. It must not be forced through cross-sectional rank
  correlation merely to reuse an existing artifact shape.
- 2026-07-28 — A failed promotion may leave a valid immutable Report while the
  Session remains active; that is safer and retryable. Source mutation must
  remain guarded and occur only after the selected Report is verified current.

## Verification

- Real migrated Project:
  `quant-workspace/projects/us-large-cap-known-reversal`.
- Acceptance Run:
  `run-20260727T184613912771Z-f6aa94a43146`.
- Request-bound claim: `known-style-validation / reversal_5`.
- Train candidate/style rank identity: `1.0`.
- Five-session validation rank IC / HAC t / p:
  `0.074836 / 1.731962 / 0.083280`.
- Both fixed validation folds remained positive:
  `0.042906` and `0.074592`.
- Role-aware evidence materialized four cross-sectional scores, two timestamp
  contexts, and six score-only pairs. Breadth validation states had
  low/middle/high occupancy `33 / 49 / 42`, transition rate `0.235772`, and
  conditional five-session factor IC `0.178004 / 0.041958 / 0.032135`.
- Core correctly kept Portfolio blocked at
  `raw-statistical-evidence-weak`, ignored visible-test strength for
  progression, and revised the Agent agenda to
  `factor-freeze-and-independent-sample` with no editable paths.
- Focused regression: 71 Factor/agenda/program/Session/Report/CLI tests passed
  in 162.629 seconds; the final post-fix subset of 15 tests passed in 98.849
  seconds.
- `uv run python -m unittest discover -s tests -q`
  - all 229 bounded repository tests passed in 1627.965 seconds.
- `uv run python scripts/check_doc_links.py`
  - all 923 documentation double-links resolved.
- `uv run python -m compileall -q autoquant tests`
  - passed.
- `uv run aq validate
  /Users/ame/2607AutoQuant/quant-workspace/projects/us-large-cap-known-reversal
  --json`
  - returned `ok: true` and `valid: true`.
- `git diff --check`
  - passed.
- `uv build`
  - source distribution and wheel built successfully.

## Progress log

- 2026-07-28 — Plan created from one completed real cross-sectional Project and
  indexed as active before Core implementation.
- 2026-07-28 — Migrated the same locked Yahoo panel into a new request-bound
  known-style Project, ran one six-component Factor evaluation, and used its
  first Agent agenda to remove a redundant/contradictory in-sample suggestion.
- 2026-07-28 — Completed the requirement audit, full repository regression,
  documentation-link validation, bytecode compilation, package build, and
  real-Project validation; committed and pushed the milestone.

## Completion

AutoQuant now treats Factor intent as request-derived authority: novel-factor
discovery preserves the strict style-neutral funnel, while known-style
validation proves candidate identity and evaluates the declared style without
neutralizing it against itself. Score and context components have distinct
causal evidence contracts, delegated promotion is bound to an exact immutable
Report, and the real migrated Project demonstrated both a useful positive
cross-sectional signal and an honest statistical stop before Portfolio work.
