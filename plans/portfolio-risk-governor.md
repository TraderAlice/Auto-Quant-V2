# Causal portfolio risk governor

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/portfolio-risk-governor]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/request-bound-portfolio-mandates]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Every new request-bound Portfolio and governed-RL sleeve uses the same fixed,
causal portfolio-volatility ceiling after signal allocation. A trader or Agent
can see the pre-governor target, covariance forecast, scale decision, resulting
weight, and validation/test effect without confusing historical target-weight
evidence with live account risk.

## Context

The current mechanical policy explains signal state, conviction,
inverse-volatility strength, caps, drift, costs, and realized component risk.
It still allocates under diagonal risk assumptions and can issue the same gross
target when correlations make total portfolio risk materially different.
Governed RL inherits those sleeves, so it also lacks a shared portfolio-level
pre-trade risk control.

The first governor should reduce risk without becoming a universal optimizer:
use trailing covariance through the decision close, apply a fixed annualized
volatility ceiling, never scale exposure above the signal target, and keep
request direction, context-asset, gross, net, and cap authority unchanged.

## Scope

### In scope

- Add a content-locked risk policy to every newly built Portfolio Mandate.
- Scale signal-policy targets down when causal trailing covariance forecasts
  annualized portfolio volatility above the fixed ceiling.
- Preserve legacy implicit-neutral Projects without reinterpretation.
- Make Portfolio and governed-RL action sleeves share the exact policy.
- Publish per-date and split-level governor evidence plus an ungoverned
  diagnostic comparison.
- Project the same verified risk contract through Reports, Dossiers, CLI
  explorers, and Studio.

### Out of scope

- Leverage or scale-up below the ceiling.
- Expected-return optimization, equal-risk-contribution solving, sector
  constraints, borrow, margin, funding, or live OpenAlice UTA state.
- Caller-selectable risk tolerance or a generic optimizer DSL.

## Acceptance

- [x] New mandates strictly bind method, ceiling, lookback, minimum history,
  annualization, and `scaleUp: false`; tampering changes identity or fails.
- [x] Every governed target forecast uses only returns through decision close,
  scales monotonically in `[0, 1]`, and preserves mandate constraints.
- [x] Portfolio artifacts reconcile pre-governor weights, post-governor
  weights, forecast volatility, scale, and status for every asset/date.
- [x] Portfolio metrics disclose governed versus ungoverned validation/test
  behavior without letting the diagnostic comparison enter selection.
- [x] Governed RL actions use the identical mandate risk policy and cannot
  bypass it through the editable encoder.
- [x] CLI, Reports, Dossiers, and Studio expose the verified policy and current
  governor evidence with no trading-authority claim.
- [x] Deterministic tests prove activation, no scale-up, no lookahead,
  constraint preservation, tamper rejection, RL inheritance, and legacy
  compatibility.

## Work

- [x] Audit current sizing, covariance attribution, mandate, RL sleeve, and
  explorer boundaries.
- [x] Implement and validate the mandate and fixed construction contract.
- [x] Add immutable Portfolio/RL evidence and bounded Core projections.
- [x] Update public documentation and Studio presentation.
- [x] Run focused and full verification, browser QA, and completion audit.

## Findings and decisions

- 2026-07-24 — Existing inverse-volatility sizing is asset-local; trailing
  covariance is currently calculated only after execution for attribution.
  Reuse its causal 60/20 convention for the pre-trade forecast.
- 2026-07-24 — The governor is a ceiling, not a target: it may reduce exposure
  but never lever a weak signal up. This preserves caller direction and avoids
  inventing risk appetite that OpenAlice did not provide.
- 2026-07-24 — Legacy mandate-free evidence stays ungoverned and explicitly
  legacy rather than being silently reinterpreted.
- 2026-07-25 — Governor activation and scale are contextual comparison
  evidence, not universally favorable metrics. They remain excluded from
  candidate dominance because frequent scaling can mean either useful
  protection or an unstable raw signal.

## Verification

- `uv run python scripts/check_doc_links.py`
- `node --check autoquant/studio_assets/studio.js`
- `uv run python -m compileall -q autoquant`
- `git diff --check`
- Focused mandate, Portfolio, explorer, RL, and decision-matrix suite:
  `32` tests passed.
- `uv run python -m unittest discover -s tests -v`: `144` tests passed.
- Built the wheel, installed it into an isolated Python 3.11 environment, and
  verified packaged mandate, explorer, construction, RL, and Studio assets plus
  the installed `portfolio-mandate` schema.
- Browser QA used a deterministic high-volatility request fixture. The
  validation governor activated on `54.902%` of decisions, reduced active
  targets to `69.5632%` on average, and capped the maximum forecast from
  `38.8644%` to exactly `15%`. Studio had no horizontal overflow, busy state,
  or application console errors.

## Progress log

- 2026-07-24 — Plan created after the post-selection-integrity gap audit.
- 2026-07-25 — Added the fixed mandate policy, causal scale-down path,
  reconciled decision-ledger evidence, governed/ungoverned diagnostic,
  Portfolio/RL inheritance, CLI/Report/Dossier projections, Studio readout,
  and professional Session comparison fields.
- 2026-07-25 — Passed the focused and full deterministic suites, isolated-wheel
  smoke test, documentation validation, and activated high-volatility Studio
  browser QA.

## Completion

Completed on 2026-07-25 with every acceptance item backed by executable
evidence. The final commit was pushed to `origin/main`.
