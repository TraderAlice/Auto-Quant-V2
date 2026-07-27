# Caller-owned per-asset position caps

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/caller-owned-asset-position-caps]],
  [[docs/design/caller-owned-portfolio-research-policy]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/portfolio-construction-lab]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Let an OpenAlice or local caller state that different requested assets have
different maximum research weights, then make Portfolio and governed RL use,
audit, explain, and hand off those exact limits without turning them into
candidate-tunable strategy parameters or live account permissions.

## Context

AutoQuant already turns each asset's signal percentile, conviction, and
trailing volatility into a different target weight. The request contract,
however, has only one global `maxAbsWeight`. A caller cannot say that a broad
ETF may carry 25% while one volatile single name may carry only 8%.

That omission matters in a quantitative-support workbench: the collaborating
workbench owns intended risk constraints, while AutoQuant owns reproducible
mechanical allocation under them. Silently forcing one cap onto every asset
either overstates constrained names or needlessly restricts permitted ones.

## Scope

### In scope

- Add a strict `assetMaxAbsWeights` override map to the complete optional
  Research Request `portfolioPolicy`.
- Require every override to name a requested asset and remain positive and no
  greater than the global cap.
- Derive a complete per-universe cap map in the immutable Portfolio Mandate:
  tradable assets receive their override or the global default; context-only
  assets receive zero.
- Generalize deterministic capped water-filling, directional cash retention,
  dollar-neutral feasibility, target constraint audit, sizing anatomy, and
  mechanical decision evidence.
- Make governed RL use the same exact cap vector for every action sleeve,
  baseline, opportunity audit, and final book.
- Preserve the policy through CLI schemas, Studio, Reports, Dossiers, and
  Agent-facing documentation.

### Out of scope

- Minimum weights, forced holdings, named hedges, sector/factor constraints,
  current UTA holdings, borrow, margin, or order placement.
- Inferring caps from volatility, liquidity, market capitalization, prose, or
  Broker state.
- Allowing the research Agent to tune caps.

## Acceptance

- [x] Strict request and Mandate validation reject unknown, non-requested,
  non-finite, non-positive, above-global, or tampered per-asset caps.
- [x] Mechanical allocation water-fills against each active asset's own cap,
  retains cash for directional mandates, and stays flat when a
  dollar-neutral side cannot fund its budget.
- [x] Constraint evidence proves every target obeys its exact named cap rather
  than only the global maximum.
- [x] Portfolio sizing anatomy and current decision rows disclose the cap
  applied to each asset and whether it bound.
- [x] Governed RL action sleeves and constraint audits consume the identical
  Mandate cap vector.
- [x] Custom asymmetric-cap Portfolio/RL fixtures, schemas, Studio, Reports,
  Dossiers, full regression, static checks, and package build pass.

## Work

- [x] Audit request, Mandate, allocator, Portfolio Explorer, RL, and handoff
  paths for hidden scalar-cap assumptions.
- [x] Define caller/Core/Agent authority and exact override/default semantics.
- [x] Implement strict request and content-derived Mandate contracts.
- [x] Generalize shared Portfolio/RL allocation and constraint evidence.
- [x] Update bounded read models, Studio, Reports, Dossiers, and docs.
- [x] Complete focused/full verification, commit, and push.

## Findings and decisions

- 2026-07-27 — Signal conviction and inverse volatility remain Harness-owned
  sizing evidence. Per-asset caps are caller-owned constraints, not forecasts.
- 2026-07-27 — Overrides are bounded by the global cap. The global value stays
  a readable fallback and upper envelope; the Mandate materializes one exact
  cap for every universe asset.
- 2026-07-27 — Context-only assets receive cap zero because their position
  authority is zero. This is explicit in the complete map rather than inferred
  by consumers.
- 2026-07-27 — No compatibility shim is required during this pre-alpha
  breaking-change phase: a supplied `portfolioPolicy` is a complete contract
  and now includes `assetMaxAbsWeights`, which may be `{}`.

## Verification

- `uv run python -m unittest tests.test_mandates
  tests.test_intake.RequestDrivenIntakeTests.test_caller_portfolio_policy_governs_portfolio_and_rl
  -v` — passed.
- `uv run python -m unittest tests.test_portfolio_lab
  tests.test_portfolio_explorer tests.test_rl_explorer tests.test_studio -v`
  — 45 tests passed.
- `uv run python -m unittest tests.test_reports tests.test_dossiers -v` —
  19 tests passed.
- `uv run python -m unittest discover -s tests -v` — 216 tests passed in
  1434.705 seconds.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `uv run python -m compileall -q autoquant tests` — passed.
- `git diff --check` — passed.
- `uv build --out-dir /tmp/autoquant-v2-dist-20260727-caps` — wheel and
  source distribution built.
- Ruff is not a pinned Project dependency. An exploratory Ruff 0.16.0 check
  reports repository-wide pre-existing formatting/rule differences, so it was
  not treated as a release gate or used for a bulk rewrite.

## Progress log

- 2026-07-27 — Plan activated after tracing the current scalar
  `maxAbsWeight` through request validation, Mandate identity, water-filling,
  constraint audit, Portfolio/RL Judges, Explorer, Studio, and handoff.
- 2026-07-27 — Added the strict requested-asset override map, complete
  Mandate cap vector, variable-cap water-fill, constraint evidence, and
  asymmetric AAPL/MSFT Portfolio/RL regression.
- 2026-07-27 — Updated sizing anatomy, monetization baseline, Studio, Reports,
  Dossiers, CLI/docs, and completed the full repository regression and build.

## Completion

The caller can now set different maximum research weights for requested
assets. Core content-locks a complete cap vector, Portfolio and every governed
RL sleeve use the same variable-cap allocator and audit, and human/Agent
surfaces distinguish the default cap from named overrides without granting
trading authority.
