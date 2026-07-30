# Make the first Factor Session scientifically legible

- Status: `active`
- Updated: `2026-07-30`
- Target release: `0.8.28`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0827-final-price-volume/desk/workspace/projects/grok-price-volume-factor-v0827-final`
- Related design: [[docs/design/panel-native-factor-api]],
  [[docs/design/ohlcv-factor-lab]], and
  [[docs/design/research-selection-integrity]].

## Outcome

A fresh Coding Agent entering a daily Factor Project sees a baseline that uses
only the panel inputs actually available to it, and after evaluation sees a
truthful distinction between first visible-test exposure and a later source
edit that could have used that evidence.

## Context

The final installed-wheel `0.8.27` Grok worker completed a valid bounded daily
price/volume study, but encountered two scientifically misleading descriptions:

- its daily-only baseline declared unavailable `3h` and `12h` components that
  safely no-op at runtime but overstate the comparison actually evaluated;
- immediately after its first Experiment, selection integrity reported
  `required-after-test-guided-iteration` even though test evidence had only
  become visible and no later candidate edit had occurred.

Both defects make a correct workbench harder for an unfamiliar Agent to reason
about. They belong in one first-Session legibility outcome because the baseline
defines what the Agent starts from and selection integrity defines what the
Agent may honestly claim after touching it.

## Scope

### In scope

- Select a Factor baseline whose declared component intervals are a subset of
  the verified dataset surface at intake time.
- Preserve the existing causal feature-aware baseline for packages that
  actually provide those intervals.
- Reconstruct visible-test exposure and subsequent editable-source change from
  immutable Run, Experiment, and source-hash evidence.
- Project the distinction consistently through Session, Report, Dossier, CLI,
  Studio, schemas, and Agent guidance.
- Preserve backward readability for existing Runs and Sessions.

### Out of scope

- Choosing a request-specific null model or changing the fixed Factor Judge.
- Hiding test evidence, allowing test metrics into KEEP/REVERT, or weakening
  family-wise adjustment and external-holdout requirements.
- Claiming that Core knows whether a human or Agent actually read a visible
  field.
- Adding new factor families, models, Portfolio behavior, RL behavior, or
  trading authority.

## Acceptance

- [ ] Daily V1/V4/V5 Factor intake produces a baseline whose source and
      component declarations use only the base interval.
- [ ] Multi-interval Factor intake retains its complete feature-aware baseline,
      with baseline Run and candidate contract in agreement.
- [ ] First formal evaluation records visible-test exposure without claiming a
      later test-informed edit.
- [ ] A source change after that exposure advances to a distinct conservative
      test-guided-iteration-risk state and requires fresh external evidence.
- [ ] Session, Report, Dossier, CLI, Studio, schema, and documentation agree;
      older evidence remains loadable and no test metric enters selection.
- [ ] Focused/full tests, build/install smoke, exact clean-clone validation, and
      a fresh installed-wheel Agent replay pass before `0.8.28`.

## Work

- [ ] Reproduce both `0.8.27` descriptions and identify the smallest baseline
      selection and immutable exposure boundaries.
- [ ] Implement surface-aligned baseline construction without duplicating
      Judge or candidate semantics.
- [ ] Implement a backward-readable selection-integrity state model derived
      from fixed source hashes and Experiment order.
- [ ] Update public schemas, human/JSON/Studio projections, design documents,
      template/sample consistency, and regression fixtures.
- [ ] Run an unchanged fresh Agent assignment, audit its scientific answer and
      retries, then complete release verification.

## Findings and decisions

- 2026-07-30 — Consolidated
  [[plans/daily-factor-baseline-surface]] and
  [[plans/test-visibility-integrity-state]] because both describe whether the
  first editable Factor Session tells a new Agent the truth about its starting
  surface and consumed evidence.
- 2026-07-30 — The safe boundary remains conservative: first exposure consumes
  the internal test's untouched status, while only a later source change earns
  the stronger test-guided-iteration description.

## Verification

Pending.

## Progress log

- 2026-07-30 — Plan activated from the final `0.8.27` installed-wheel field
  trial; implementation audit started.

## Completion

Pending.
