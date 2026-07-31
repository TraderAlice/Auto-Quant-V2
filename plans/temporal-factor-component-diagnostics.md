# Temporal Factor component diagnostics

- Status: `active`
- Updated: `2026-07-31`
- Target release: `0.9.1`
- Related design: [[docs/design/factor-component-attribution]],
  [[docs/design/factor-evidence-explorer]],
  [[docs/design/causal-multi-interval-factor-inputs]], and
  [[docs/design/research-selection-integrity]].

## Outcome

Make candidate-declared component evidence equally useful for single-asset
temporal and two-asset relative-value Factor research, so a coding Agent can
diagnose which causal multi-interval inputs predict, duplicate, diversify, or
degrade a fixed diagnostic blend without private post-Run computation.

## Context

`v0.9.0` proved causal completed-interval temporal Factor research with fresh
Grok 4.5 coworkers, but the fixed Judge currently emits
`factor-components.json` only for cross-sectional evaluation. Temporal Runs
therefore disclose the composite Factor result while hiding the component
evidence an Agent needs to explain a weak or unstable result. The accepted
real-delegation synthesis records this as an honest product limit.

AutoQuant is pre-1.0 and this milestone does not preserve obsolete component
schemas merely for compatibility. Immutable old Runs retain their original
Harness identity; the checked-in sample may receive new current evidence when
the template contract changes.

## Scope

### In scope

- Single-asset temporal component raw horizon quality, final-Factor
  association, train-selected nearest-peer redundancy, temporal residual
  quality, and fixed temporal rank-blend leave-one-out evidence.
- The same evidence over the caller-authorized first-minus-second signal and
  forward-return contrasts for two-asset relative-value research.
- Temporal context-state occupancy, transitions, and conditional contribution
  evidence using train-fixed thresholds.
- One explicit component-evidence schema with evaluation-mode semantics,
  immutable artifact reconciliation, CLI/JSON projection, research agenda,
  and Studio parity.
- Updated templates, sample evidence, design/status documentation, and a fresh
  isolated Grok 4.5 multi-interval research trial before release.

### Out of scope

- Cross-Project data reuse, universal downloaders, alternative-data features,
  target-weight construction, Broker execution, Order/TPSL, or live trading.
- Treating component diagnostics as Factor promotion authority.
- Inferring arbitrary `compute_factor` composition or claiming leave-one-out
  evidence is exact nonlinear candidate attribution.
- Adding a generic compatibility layer for old mutable Workspaces.

## Acceptance

- [x] Declared score components in both temporal modes publish complete
  train/validation/test-audit evidence at every request-bound horizon.
- [x] Nearest-peer selection and transforms are target-free; validation alone
  drives diagnosis, while test remains visible audit and no component metric
  enters the immutable Factor objective.
- [x] Timestamp context has truthful temporal contribution semantics and never
  masquerades as cross-sectional IC.
- [x] RunResult, immutable component artifact, Explorer JSON, research agenda,
  Studio, and documentation reconcile one bounded contract.
- [x] Cross-sectional behavior remains correct under the new contract;
  obsolete schema behavior may break explicitly rather than silently adapt.
- [ ] Fast focused tests, full regression, documentation/build/install smoke,
  and repository-root clean-clone smoke pass.
- [x] A fresh Grok 4.5 worker completes a realistic causal multi-interval task
  using the installed candidate release and demonstrates whether the new
  evidence is sufficient for a useful handoff.
- [ ] The audited state is published as `v0.9.1`.

## Work

- [x] Define generalized temporal component math and the new evidence schema.
- [x] Implement Judge evidence and deterministic artifact tests.
- [x] Implement strict Core projection, agenda, CLI, and Studio parity.
- [x] Update template/operator/design documentation and current sample evidence.
- [x] Run a fresh Grok 4.5 field trial and repair only observed reusable defects.
- [ ] Complete release audit, publish `v0.9.1`, and close the plan.

## Findings and decisions

- 2026-07-31 — Current source already evaluates temporal composite Factor and
  style qualification with within-split correlation contributions, but gates
  `_component_evidence` on `cross-sectional` evaluation. The missing surface
  is therefore a bounded extension of fixed evidence, not a new Factor API.
- 2026-07-31 — Existing local data does not constrain the trial question. The
  worker will acquire one complete task-coherent snapshot selected by the
  research need under the demand-led dataset principle.

## Verification

- Temporal single-asset, two-asset relative-value, timestamp-context, and
  cross-sectional Explorer focused regression passed.
- Factor Lab and Factor Explorer suites: 20 tests passed in 83.835 seconds.
- Mandate plus temporal intake focused regression: 18 tests passed in 4.816
  seconds.
- Repository sample Run
  `run-20260731T131547748789Z-d99c9e66a888` records clean Harness `0.9.1` at
  `39a2e38`, component method v3, and passes strict Studio projection.
- Full Grok 4.5 trial: 43 turns, approximately 10 minutes, 13,800 Binance Spot
  1h bars per asset, one successful relative-value Run, one completed Session,
  one Report, zero Experiments, and clean worker commit `e4eb0a2`.
- Fresh explicit-role retry: 29 turns, 216 Binance Spot 1h bars per asset,
  strict three-role request preserved through dollar-neutral intake, no Run or
  Session, and clean worker commit `bbf3d72`.
- Full regression, documentation/build/install, clean-clone smoke, and final
  tag verification remain pending.

## Progress log

- 2026-07-31 — Plan created from the accepted `v0.9.0` real-delegation limit
  and activated as the first `0.9.x` patch milestone.
- 2026-07-31 — Generalized the explicit component contract to schema v3.
  Single-asset and two-asset relative-value Runs now publish bounded temporal
  raw, nearest-peer residual, fixed-blend removal, pairwise, and context-state
  contribution evidence with train-only target-free transforms and visible-
  audit test semantics. Strict Explorer projection, research agenda, CLI,
  Studio, Report/Dossier wording, templates, and focused tests now agree on
  evaluation-mode-specific semantics. The preserved v2 sample Run correctly
  fails current Explorer projection and will be superseded, not mutated, by a
  clean v0.9.1 sample execution.
- 2026-07-31 — A fresh isolated Grok 4.5 worker completed a realistic
  LINK-versus-ETH relative-value assignment on 13,800 Binance Spot 1h bars per
  asset. Its one baseline Run materialized four score components, one BTC
  timestamp context, six pairwise comparisons, and useful v3 temporal
  diagnosis; the worker stopped on negative validation evidence, completed a
  Report without an Experiment, and returned a precise Chinese handoff. The
  trial exposed one reusable intake defect: explicit two-sided pair roles plus
  named context produced the generic asset-role mandate and disabled relative-
  value evaluation.
- 2026-07-31 — Repaired mandate derivation so exactly two explicit two-sided
  relative-value assets retain the dollar-neutral zero-net pair family while
  any explicit context-only names remain context. Generic mixed role vectors
  remain asset-role. Added unit, intake, and durable-contract documentation.
- 2026-07-31 — A fresh 29-turn Grok 4.5 retry retained LINK, ETH, and explicit
  context-only BTC in the strict request; public intake produced
  dollar-neutral/zero with only LINK/ETH tradable and caller-supplied role
  provenance. The worker hand-edited no mandate, executed no Study, passed
  validation/orientation, committed durable records only, and left clean Git.

## Completion

Pending.
