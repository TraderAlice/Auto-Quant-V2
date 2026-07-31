# Relative-value monetization intent parity

- Status: `completed`
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

- [x] An active explicit relative-value pair receives normalized intent equal
  to the capped complementary pair, even when both legs leave gross budget in
  Cash.
- [x] Relative-value equal intent and pre-governor sizing reconcile when the
  fixed pair constructor has no separate conviction allocation stage.
- [x] Ordinary cross-sectional dollar-neutral intent retains its full-side-
  breadth rule and context-only assets remain exactly zero.
- [x] Explorer semantics disclose evaluation mode and intent construction;
  schema, CLI, Studio, Reports/Dossiers, and durable docs agree.
- [x] Validation-only diagnosis and research agenda identify the true first
  failing layer; visible test and descriptive profile performance remain
  non-selective.
- [x] Focused tests, full regression, docs/build/install/clean-clone smoke,
  and a fresh non-baseline-factor Grok field trial pass before `v0.9.4`.

## Work

- [x] Reproduce the contradictory `v0.9.3` field evidence and locate the
  cross-sectional side-capacity assumption in the Explorer bridge.
- [x] Implement prediction-mode-aware intent construction and strict public
  projection.
- [x] Update downstream human/Agent surfaces, docs, and regression evidence.
- [x] Run the fresh worker and complete the release audit.

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
- 2026-08-01 — The first fresh non-baseline trial deliberately doubled the
  centered score without changing ranks. Check passed, Experiment returned
  `REVERT` with improvement `0.0`, and the extra trial caused adjusted Factor
  evidence to block Portfolio. The worker correctly returned no weights. This
  is not a failed acceptance test; it proves selection authority cannot be
  bypassed merely to reach a desired downstream screen.
- 2026-08-01 — A second frozen-factor worker then isolated downstream
  acceptance without spending selection budget. Its installed-wheel Portfolio
  Explorer reported 75 normalized-intent active dates for 75 raw-target dates,
  exact pair-target error `0.0`, zero context intent, and trading cost as the
  true largest adverse layer.

## Verification

- Focused Portfolio/intake/Report/Dossier/agenda/Studio regression: 101 tests
  passed in 451.431 seconds.
- Repository-sample regression: 4 tests passed, including strict projection
  of the clean `0.9.4` Run bound to commit `f17d261`.
- Source-level reproduction against the accepted `0.9.3` field Run changed
  normalized intent from 0/103 active dates to 75/103, equal to raw targets;
  normalized-intent and pre-governor annualized contribution both became
  `0.10636426185891273` with exact pair parity.
- Two isolated installed-wheel Grok 4.5 trials completed: one correct negative
  adjusted-gate result and one accepted Factor-to-Portfolio/Dossier handoff.
  The latter reported current NVDA/QQQ targets `-0.30/+0.30`, context zero,
  pair-target error `0.0`, and `stable-target-path`.
- Full regression passed all 361 tests in 1066.637 seconds. All 1,253
  documentation double-links, Studio JavaScript syntax, and lock validation
  passed.
- Clean sdist and wheel builds passed. The wheel installed into fresh Python
  3.11, reported `aq 0.9.4`, and exposed all 50 public commands through the
  capability manifest.
- A no-hardlink clone without the ignored local override selected
  `sample-research-desk` from the committed Workspace manifest. Installed-
  wheel orientation, validation, Project listing, and Studio snapshot passed;
  Studio projected all 7 Runs and the cross-sectional
  `mandate-equal-active-side-budget` intent construction.

## Progress log

- 2026-08-01 — Plan created from the first post-`v0.9.3` field-evidence
  audit.
- 2026-08-01 — Core implementation, strict schema, CLI/Studio/Report surfaces,
  docs, and focused regression committed as `f17d261`.
- 2026-08-01 — Clean current sample Portfolio evidence committed as `d4a9920`.
- 2026-08-01 — Fresh workers completed the rank-invariant negative gate and
  frozen-factor positive downstream acceptance cases.

## Completion

`v0.9.4` replaces the misleading cross-sectional fallback for explicit
relative-value intent with the same capped complementary pair used by actual
construction. Diagnostics now identify the real first adverse layer without
changing immutable Runs, target weights, performance, or trading authority.
