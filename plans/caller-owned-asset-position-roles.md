# Caller-owned asset position roles

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/caller-owned-asset-position-roles]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/caller-owned-asset-position-caps]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Let an OpenAlice or local caller declare which requested assets may be long,
short, two-sided, or context-only, then make Portfolio and governed RL share
and explain that exact position-role contract.

## Context

The current Portfolio Mandate derives one construction family from the global
request direction and applies it to every requested asset. That cannot express
a common research question such as long AAPL/MSFT, permit SPY only as a short
hedge instrument, and retain QQQ as non-position context.

AutoQuant must preserve caller intent without pretending to choose a hedge
ratio, infer beta neutrality, or acquire live trading authority.

## Scope

### In scope

- Add optional strict per-request-asset position roles.
- Require complete role declaration when any requested asset declares one.
- Materialize a complete role vector and deterministic long/short gross-side
  limits inside the immutable Portfolio Mandate.
- Apply the same role vector to mechanical Portfolio and governed-RL sleeves.
- Preserve role source, permissions, and unused side capacity in evidence.

### Out of scope

- Beta, sector, factor, currency, duration, or delta hedge sizing.
- Forced positions, minimum allocations, borrow availability, margin,
  financing, orders, TPSL, Broker, or OpenAlice UTA authority.
- Candidate-selected roles or gross-side limits.

## Acceptance

- [x] Strict Request and Mandate validation reject partial, unknown, or
  tampered role declarations.
- [x] Requests without roles retain the existing direction-derived behavior.
- [x] Explicit roles govern sign permissions, context-only flatness, per-asset
  caps, deterministic side limits, and unused cash.
- [x] Portfolio and governed RL use the same role contract.
- [x] CLI, Studio, Reports, Dossiers, and artifacts disclose roles and limits.
- [x] Focused and complete deterministic regression passes.

## Work

- [x] Audit Request, Mandate, construction, RL, and evidence assumptions.
- [x] Define caller/Core/Agent authority and bounded role semantics.
- [x] Implement strict Request and content-derived Mandate contracts.
- [x] Apply roles to Portfolio and governed-RL target construction.
- [x] Update verified evidence and human/Agent surfaces.
- [x] Complete verification, commit, and push.

## Findings and decisions

- 2026-07-27 — Global direction remains the research-question summary. A
  complete explicit asset-role vector becomes the more precise position
  permission contract.
- 2026-07-27 — With both long-capable and short-capable assets, each side may
  use up to half the gross limit. With only one capable side, that side may use
  the complete gross limit. Unused capacity remains cash and no side is forced.
- 2026-07-27 — `two-sided` permits the mechanical signal to choose either sign;
  it does not authorize simultaneous long and short exposure in one asset.
- 2026-07-27 — A direction-compatible default benchmark uses only assets
  capable of the benchmark sign; a short-only hedge asset never enters an
  implicit equal-weight long reference.

## Verification

- `uv run python -m unittest tests.test_mandates
  tests.test_intake.RequestDrivenIntakeTests.test_caller_asset_roles_are_shared_by_portfolio_and_rl
  tests.test_portfolio_explorer.PortfolioDecisionExplorerTests.test_projection_reconciles_metrics_artifacts_and_mechanical_policy
  tests.test_rl_explorer.RlPolicyEvidenceExplorerTests.test_projection_reconciles_trials_baselines_training_and_actions -v`
  — 14 focused contract and end-to-end tests passed.
- `uv run python -m unittest discover -s tests -v` — all 223 tests passed in
  1707.592 seconds.
- `uv build` — source distribution and wheel built successfully.
- `uv run python scripts/check_doc_links.py` — all 843 documentation
  double-links resolved.
- `node --check autoquant/studio_assets/studio.js` and `git diff --check`
  passed.
- A fresh request-driven mixed-role Project completed Portfolio and governed-RL
  Runs under the same Mandate. The local Studio at `http://127.0.0.1:8766/`
  displayed the complete role vector and long/short side limits.

## Progress log

- 2026-07-27 — Plan activated after the multi-asset mandate audit found that
  one global family still assigned the same position role to every requested
  asset.
- 2026-07-27 — Added strict request roles, a content-derived complete Mandate,
  role-aware benchmark selection, shared Portfolio/RL construction, immutable
  audits, and human/Agent evidence surfaces.
- 2026-07-27 — Focused, complete, packaging, documentation, syntax, and visual
  Studio verification passed.

## Completion

Completed on 2026-07-27. OpenAlice and local callers can now assign explicit
research duties to every requested asset without granting live trading
authority or forcing a hedge. Portfolio and governed RL preserve the same
immutable permissions, caps, side limits, construction, audit, and handoff
evidence.
