# Relative-value monetization intent parity

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.4`
- Related design: [[docs/design/prediction-mode-target-weight-translation]],
  [[docs/design/signal-policy-and-attribution]],
  [[docs/design/portfolio-decision-explorer]], and
  [[plans/target-translation-robustness-and-loss-attribution]].

## Outcome

Make the normalized signal-intent stage use the same explicit two-asset
relative-value population and capped complementary-pair semantics as fixed
Portfolio construction, so loss attribution cannot call a profitable active
pair `signal-intent-negative` merely because its two legs intentionally leave
unused gross budget in Cash.

## Context

`v0.9.1` repaired explicit two-sided relative-value construction: exactly two
prediction assets form a complementary zero-net pair, their shared absolute
weight is bounded by the fixed side budget and both asset caps, and unused
capacity remains Cash. Context-only assets never become position legs.

The older signal-monetization bridge still normalizes every dollar-neutral
mode through the cross-sectional side-breadth rule. It requires each side to
fill the entire half-gross budget or returns a flat equal-intent book. In the
accepted `v0.9.3` NVDA/QQQ field Run, each leg was capped at `0.30` while each
full side budget was `0.50`. The real fixed pair therefore held
`-0.30/+0.30`, but equal intent was incorrectly flat on every validation date.
This produced `signal-intent-negative` beside positive pre-governor, governed,
executed-gross, and executed-net contributions.

The mismatch is a diagnostic contract defect. It can misstate the first
failing stage and route an Agent toward factor direction or breadth when the
actual pair intent is positive. Breaking changes are allowed, so this plan
replaces the bridge method directly rather than retaining the misleading
read-model behavior.

## Scope

### In scope

- Prediction-mode-aware normalized intent in the strict Portfolio Explorer.
- Exact capped complementary intent for `two-asset-relative-value`, including
  intentional Cash when either leg cap is below the fixed side budget.
- The existing fully funded side-breadth rule for ordinary cross-sectional
  dollar-neutral construction.
- Explicit read-model semantics naming the evaluation mode and normalized
  intent construction used by every Run.
- Correct validation-only outcome, largest adverse transformation, research
  agenda, CLI, Studio, Report/Dossier, and documentation language.
- End-to-end regression against the deterministic relative-value intake and
  the accepted `v0.9.3` field-Run shape.
- One fresh installed-wheel Grok relative-value assignment whose supplied
  caller factor is not byte-identical to the materialized baseline, so Check
  and one formal Experiment are genuinely exercised.

### Out of scope

- Changing target weights, signal thresholds, risk governance, execution,
  costs, or Portfolio performance.
- Optimizing gross budget, caps, translation windows, or factor parameters.
- A generic pair/spread DSL, Orders/TPSL, Broker behavior, shared data
  inventory, or OpenAlice integration changes.
- Retrofitting historical immutable Run bytes. The strict read model derives
  corrected attribution from their existing verified ledgers.

## Acceptance

- [ ] An active explicit relative-value pair receives normalized intent equal
  to the capped complementary pair, even when both legs leave gross budget in
  Cash.
- [ ] Relative-value equal intent and pre-governor sizing reconcile when the
  fixed pair constructor has no separate conviction allocation stage.
- [ ] Ordinary cross-sectional dollar-neutral intent retains its full-side-
  breadth rule and context-only assets remain exactly zero.
- [ ] Explorer semantics disclose evaluation mode and intent construction;
  schema, CLI, Studio, Reports/Dossiers, and durable docs agree.
- [ ] Validation-only diagnosis and research agenda identify the true first
  failing layer; visible test and descriptive profile performance remain
  non-selective.
- [ ] Focused tests, full regression, docs/build/install/clean-clone smoke,
  and a fresh non-baseline-factor Grok field trial pass before `v0.9.4`.

## Work

- [x] Reproduce the contradictory `v0.9.3` field evidence and locate the
  cross-sectional side-capacity assumption in the Explorer bridge.
- [ ] Implement prediction-mode-aware intent construction and strict public
  projection.
- [ ] Update downstream human/Agent surfaces, docs, and regression evidence.
- [ ] Run the fresh worker and complete the release audit.

## Findings and decisions

- 2026-08-01 — Accepted field Run
  `run-20260731T163146284864Z-978fe85b8e63` has 75 validation dates with real
  raw targets and zero equal-intent active dates. Normalized intent is `0.0`,
  while pre-governor contribution is `0.0434743` total / `0.1063643`
  annualized. This directly contradicts the explicit pair construction.
- 2026-08-01 — The fix belongs in the strict Explorer read model. Immutable
  Run decisions already contain evaluation mode, verified pair scores,
  signal states, target weights, returns, and caps; no Judge rerun or history
  rewrite is necessary.
- 2026-08-01 — A two-asset relative-value pair is not a small cross-section.
  Its normalized intent is the exact complementary pair bounded by the lesser
  side budget and both leg caps. Cross-sectional side breadth remains a
  separate construction.

## Verification

Pending.

## Progress log

- 2026-08-01 — Plan created from the first post-`v0.9.3` field-evidence
  audit.

## Completion

Pending.
