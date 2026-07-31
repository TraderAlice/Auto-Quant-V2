# Prediction-mode target-weight translation

- Status: `active`
- Updated: `2026-07-31`
- Target release: `0.9.2`
- Related design: [[docs/design/factor-evidence-explorer]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/mechanical-signal-policy-and-attribution]], and
  [[plans/temporal-factor-component-diagnostics]].

## Outcome

Give every Factor prediction mode one causal, request-bound translation into
mechanical target-weight research, so a coding Agent can carry a qualified
cross-sectional, single-asset temporal, or two-asset relative-value signal
into Portfolio and governed-RL evidence without context assets silently
changing the decision score.

## Context

`v0.9.1` makes Factor evaluation and component diagnosis prediction-mode
aware. Portfolio and governed RL still use one older construction rule: rank
every research asset at each timestamp and require at least four valid factor
values. That rule is correct only for cross-sectional research.

The mismatch is observable in retained BTC timing evidence. BTC was the only
tradable prediction asset, but its `percentile_score` was its same-time rank
against four context-only Crypto assets. The Run could open a BTC position only
because context assets supplied a synthetic cross-section. Removing or
changing an explicitly non-target context series could therefore change the
historical target weights while the Factor claim remained BTC-only.

For a two-asset relative-value claim the defect is more severe: ranking both
legs independently against context can put them on the same side or make
allocation depend on a third asset. Factor evaluation instead measures the
caller-ordered first-minus-second contrast through time. Portfolio must carry
that same contrast forward.

AutoQuant is pre-1.0. This milestone replaces the obsolete translation
contract directly; it does not preserve old mutable Workspace behavior.
Immutable old Runs retain their original Harness identity.

## Fixed translation contract

### Cross-sectional

- Use the exact Factor prediction population, not arbitrary context assets.
- Rank factor values at timestamp `t` into `[0, 1]` within that population.
- Require at least four valid prediction assets and two distinct values.
- Context-only assets receive no score and remain flat.

### Single-asset temporal

- Use only the one request-authorized prediction asset's factor history.
- At timestamp `t`, compute its empirical percentile within the latest 60
  observed factor values through and including `t`, with at least 20 values.
- No future, split-global fit, expanding test refit, or context-asset factor
  value may enter the score.
- The existing request-bound direction, hysteresis, volatility sizing, caps,
  cash, cadence, risk governor, drift, costs, and benchmark remain fixed.

### Two-asset relative value

- Preserve the caller/mandate order as `first - second`.
- Compute the causal 60-observation empirical percentile of that factor
  contrast through `t`, with at least 20 observations.
- Give the first leg percentile `p` and the second leg `1 - p`; context assets
  receive no score.
- A long state in one leg is therefore paired with a short state in the other,
  or both remain flat under the symmetric thresholds. The fixed Mandate still
  owns exact funded sides, caps, gross/net, and cash.

The rolling percentile is a fixed mechanical translation, not a learned
factor, promotion criterion, Order, or trading instruction.

## Scope

### In scope

- One shared strict prediction-population resolver for Factor, Portfolio, and
  governed RL.
- Factor-claim dependency binding for Portfolio and RL Studies.
- Prediction-mode-aware score construction shared by ordinary Portfolio,
  robustness profiles, and every governed-RL action sleeve.
- Immutable translation semantics and coverage in RunResult, Portfolio
  artifacts, Explorer JSON, research agenda, CLI, Reports/Dossiers, and
  Studio.
- Strict recomputation that rejects rehashed score, pair-order, context-role,
  or method tampering.
- Prefix-causality, context-invariance, pair-complement, constraint,
  accounting, and end-to-end intake tests.
- One fresh installed-wheel Grok 4.5 assignment that begins with a temporal or
  relative-value Factor conclusion and must answer a target-weight question.

### Out of scope

- Orders, Broker fills, TPSL, execution scheduling, or live account mutation.
- Optimizing the 60/20 translation window from validation or test.
- Caller-defined arbitrary basket contrasts; three-asset relative-value still
  requires a future explicit contrast-weight contract.
- Cross-Project data reuse or a universal market-data downloader.
- Compatibility adapters for old candidate or artifact schemas.

## Acceptance

- [ ] Factor, Portfolio, and RL derive one identical prediction population,
  evaluation mode, context set, and relative-value pair identity.
- [ ] Single-asset temporal weights are invariant to every context-only factor
  value and become available from causal target history alone.
- [ ] Relative-value scores are exact complements of the causal ordered spread
  percentile; non-flat targets remain opposite-sided and zero-net before the
  existing risk/cost machinery.
- [ ] Cross-sectional scores exclude context-only assets while retaining the
  established breadth and ranking semantics.
- [ ] Every Portfolio/RL variant and robustness path uses the same frozen
  translation contract; no private alternate rank path remains.
- [ ] RunResult, decision ledger, Explorer, agenda, CLI, Studio, Report, and
  Dossier disclose and reconcile method, mode, population, window, coverage,
  pair order, and no-trading authority.
- [ ] Fast focused tests, full regression, documentation/build/install smoke,
  and repository-root clean-clone smoke pass.
- [ ] A fresh Grok 4.5 worker completes a realistic target-weight handoff using
  only the installed release candidate and public Workbench surfaces.
- [ ] The audited state is published as `v0.9.2`.

## Work

- [ ] Centralize and bind prediction-mode authority.
- [ ] Replace the cross-section-only target-score implementation.
- [ ] Publish and strictly project immutable translation evidence.
- [ ] Update templates, operator/design documentation, and sample evidence if
  its fixed contract changes.
- [ ] Run a fresh Grok 4.5 field trial and repair reusable friction.
- [ ] Complete release audit, publish `v0.9.2`, and close the plan.

## Findings and decisions

- 2026-07-31 — Retained BTC Portfolio Run
  `run-20260728T100043368147Z-bf56b58eeef7` confirms the mismatch: BTC is the
  only tradable prediction asset, but all five research assets have non-null
  percentile scores. BTC opened 3,085 active rows only by ranking against four
  context-only assets; the ledger labels just 71 early rows insufficient.
- 2026-07-31 — Target weights remain the right AutoQuant boundary. This
  milestone repairs how a causal factor becomes a mechanical portfolio; it
  does not revive Order/TPSL simulation or account execution.
- 2026-07-31 — The dataset principle remains demand-led. The field worker will
  acquire one task-coherent snapshot and will not select its question from a
  shared inventory merely because those files already exist.

## Verification

Pending.

## Progress log

- 2026-07-31 — Plan created after auditing the newly complete temporal Factor
  contract against the older Portfolio/RL target-score implementation.

## Completion

Pending.
