# Explain how mechanical signals become unequal asset weights

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/portfolio-construction-lab]],
  [[docs/design/signal-policy-and-attribution]],
  [[docs/design/portfolio-decision-explorer]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

One verified Portfolio Run exposes a point-in-time sizing anatomy that explains
how each asset's percentile signal becomes conviction, inverse-volatility
strength, uncapped side budget, capped/water-filled raw weight,
covariance-governed target, and final executed risk contribution. A trader or
collaborating workbench can distinguish signal conviction from portfolio
allocation and risk concentration without opening raw CSV artifacts.

## Context

The fixed Judge already owns a professional causal allocator, and the decision
ledger records its primitives. Studio currently jumps from signal state to
target weight. Unequal weights therefore look arbitrary even though they are
produced by a fixed conviction/inverse-volatility water-fill and covariance
risk governor. This is a decision-read-model and handoff gap, not a reason to
change historical Runs or candidate authority.

## Scope

### In scope

- Core reconstruction of current side budget, active breadth, strength share,
  uncapped weight, cap/water-fill redistribution, governed weight, diagonal
  risk share, and covariance component-risk share.
- Exact reconciliation against the existing immutable decision ledger and
  Portfolio Mandate.
- Bounded CLI/Studio/Report visibility with explicit historical,
  decision-support-only authority.
- Long/cash, short/cash, dollar-neutral, context-only, cap-binding, legacy,
  tamper, browser, and package regression evidence.

### Out of scope

- Changing the fixed allocator, factor, signal state machine, historical Run,
  KEEP/REVERT objective, or Portfolio Mandate.
- Optimizing weights from visible test evidence, adding a universal optimizer,
  or granting Broker/account/order authority.
- Claiming diagonal risk budget is covariance component risk, or that either
  is a forecast of realized P&L.

## Acceptance

- [x] Every current asset shows signal conviction, causal trailing volatility,
      risk strength, same-side strength share, uncapped signed weight, cap
      binding/redistribution, raw/governed/executed weight, and component risk.
- [x] Side summaries reconcile funded budget, active breadth, capped names,
      cash/underfunding, and raw target sums for all three construction
      families.
- [x] Core rejects arithmetic, Mandate, or artifact tampering rather than
      rendering plausible browser data.
- [x] CLI, Studio, and frozen Portfolio Report use the same Core sizing object
      and retain `tradingAuthority: none`.
- [x] Legacy immutable Runs remain readable without invented sizing evidence.
- [x] Controlled and real-data browser/package verification passes.

## Work

- [x] Audit the fixed allocator, ledger, Core projection, Studio, and Report.
- [x] Implement and schema the verified current sizing-anatomy projection.
- [x] Render the same evidence in Portfolio Studio and immutable Reports.
- [x] Add bounded reconstruction, legacy, tamper, and UI regression coverage.
- [x] Complete controlled/real verification, documentation, commit, and push.

## Findings and decisions

- 2026-07-25 — Base raw sizing is already fixed as percentile-distance
  conviction divided by trailing realized volatility, then capped water-fill
  within the Mandate's permitted side budget.
- 2026-07-25 — `diagonal_risk_budget_share` is a sizing heuristic
  (`abs(weight) × own volatility`); `variance_contribution_share` is the
  covariance-aware executed-book decomposition. They must remain separately
  labelled.
- 2026-07-25 — The new surface reconstructs historical evidence only. It does
  not select an allocator or recommend a live account weight.
- 2026-07-25 — On the Yahoo AAPL/NVDA/QQQ/SPY Run, AAPL's 100th-percentile
  signal and 2.3006% trailing volatility imply a 33.4946% proportional long
  weight. The 30% cap binds, so deterministic water-fill moves 3.4946% to
  NVDA; the long side still funds its exact 50% budget.
- 2026-07-25 — The same executed book gives AAPL 39.9815% of the diagonal
  sizing heuristic but 57.9265% of covariance component risk. The UI must show
  both because the latter reveals portfolio interaction hidden by own-vol
  sizing alone.

## Verification

- `uv run python -m unittest tests.test_portfolio_explorer tests.test_intake tests.test_reports -v`
  — 36 deterministic tests passed.
- `uv run python -m unittest tests.test_dossiers tests.test_studio tests.test_cli -v`
  — 22 deterministic tests passed.
- A fresh Yahoo daily-OHLCV Portfolio Run
  `run-20260725T023618422447Z-7316788ab822` was frozen into Report
  `report-20260725T023647316193Z-240bfd5d1793`, then its delegated Session
  completed successfully.
- Browser verification at 1280px showed no document-level horizontal
  overflow; the dense anatomy table stays inside its own bounded scroll area.
- A Report created before sizing anatomy remained loadable, and explicit
  compatibility tests cover prior and fully legacy Report shapes.
- Final compile, JavaScript syntax, documentation-link, wheel-build, diff, and
  browser handoff checks passed before publication.

## Progress log

- 2026-07-25 — Plan activated after comparing the existing allocator and
  decision ledger with the current unexplained-weight Studio presentation.
- 2026-07-25 — Core reconstruction, strict schema/tamper checks, CLI, Studio,
  Report/Dossier freezing, real Yahoo evidence, responsive browser audit, and
  backward compatibility completed.

## Completion

Completed: the same verified sizing anatomy is available through Core JSON,
CLI, Studio, and immutable Report/Dossier handoff, with reconciliation/tamper,
legacy, real-data, responsive-browser, and package evidence.
