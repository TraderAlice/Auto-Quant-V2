# Target-translation robustness and loss attribution

- Status: `active`
- Updated: `2026-07-31`
- Target release: `0.9.3`
- Related design: [[docs/design/prediction-mode-target-weight-translation]],
  [[docs/design/portfolio-parameter-neighborhood]],
  [[docs/design/portfolio-decision-explorer]], and
  [[plans/prediction-mode-target-weight-translation]].

## Outcome

Make temporal and relative-value target-weight conclusions disclose whether
their fixed causal percentile translation survives nearby predeclared history
windows, and carry that evidence into the existing factor-to-net loss
diagnosis without selecting or recommending an alternate window.

## Context

`v0.9.2` correctly translates cross-sectional, single-asset temporal, and
two-asset relative-value Factor claims. Temporal modes intentionally use one
fixed 60-observation causal percentile with a 20-observation minimum. The
current parameter neighborhood varies signal thresholds and no-trade bands,
but not this newly material translation assumption.

The existing Portfolio Explorer already reconciles normalized signal intent,
sizing/caps, covariance governance, historical execution/no-trade retention,
and cost. The missing upstream evidence is whether the signal states and
target weights themselves are stable when the causal history window moves
locally. Without it, an Agent may call a negative result structural when it is
actually translation-sensitive, or report a positive target as robust from
one arbitrary window.

One obsolete `construct_targets` helper still exposes the pre-`v0.9.2`
cross-sectional-only construction mental model despite having no production
caller. AutoQuant is pre-1.0, so this plan removes it directly rather than
preserving a misleading compatibility surface.

## Scope

### In scope

- Fixed `40`, `60`, and `120` observation temporal translation profiles with
  the unchanged 20-observation causal minimum.
- Validation and visible-test diagnostics for score availability, signal-state
  agreement, target-direction/weight agreement, performance, turnover, cost,
  and the current target under every profile.
- Exact immutable evidence and strict Explorer recomputation/reconciliation.
- Validation-only translation-stability diagnosis joined to the existing
  signal-monetization and research-agenda surface.
- Cross-sectional explicit `not-applicable` evidence because that mode has no
  temporal translation window.
- Removal of the obsolete cross-sectional-only `construct_targets` helper.
- One fresh installed-wheel Grok relative-value assignment with at least one
  context-only asset.

### Out of scope

- Selecting, promoting, or recommending a translation window.
- Candidate-defined windows, automatic optimization, or test-based tuning.
- Changing the fixed production 60/20 translation contract.
- New models, Orders/TPSL, Broker behavior, shared market-data inventory, or
  OpenAlice integration changes.

## Acceptance

- [ ] Temporal and relative-value Portfolio Runs expose exact predeclared
  40/60/120 translation evidence while the ordinary policy remains 60/20.
- [ ] Cross-sectional Runs truthfully disclose that temporal-window stress is
  not applicable and do not perform synthetic alternate constructions.
- [ ] Validation alone classifies stable versus translation-sensitive target
  behavior; visible test is audit-only and no profile enters selection.
- [ ] Explorer, agenda, CLI JSON, Studio, Reports/Dossiers, and immutable Run
  evidence agree on the same diagnosis and authority.
- [ ] Rehashed, missing, extra, misordered, non-causal, or numerically
  inconsistent profile evidence is rejected.
- [ ] No executable public or template path retains the obsolete
  cross-sectional-only `construct_targets` helper.
- [ ] Focused tests, full regression, docs/build/install smoke, clean-clone
  smoke, and a fresh Grok relative-value field trial pass before `v0.9.3`.

## Work

- [x] Audit existing translation, parameter-neighborhood, and monetization
  stages; bound the missing evidence.
- [x] Add configurable internal temporal translation and fixed robustness
  evidence without changing the ordinary 60/20 contract.
- [x] Strictly project the evidence through Explorer, agenda, CLI, Studio, and
  downstream handoff surfaces.
- [x] Remove the obsolete construction path and update templates/docs/tests.
- [ ] Run the fresh worker, repair reusable friction, and complete the release
  audit.

## Findings and decisions

- 2026-07-31 — Existing signal monetization already isolates sizing/caps,
  covariance governance, execution/no-trade retention, and cost. `0.9.3` must
  extend that chain upstream rather than duplicate it.
- 2026-07-31 — The existing threshold/no-trade neighborhood remains separate.
  Translation profiles are not crossed with its configurations, avoiding an
  expensive combinatorial pseudo-optimizer.
- 2026-07-31 — The demand-led dataset principle remains unchanged: the fresh
  worker acquires one task-coherent package and no shared inventory constrains
  its research question.

## Verification

- Pending.

## Progress log

- 2026-07-31 — Plan created from the first post-`v0.9.2` architecture audit.
- 2026-07-31 — Judge, immutable artifact, strict Explorer reconstruction,
  research agenda, CLI, Studio, Report, templates, and focused tamper tests now
  share the fixed robustness contract. Cross-sectional evidence is explicitly
  not applicable and the obsolete `construct_targets` path is gone.

## Completion

Pending.
