# Reported-book cash entry sizing field trial

- Status: `active`
- Updated: `2026-07-29`
- Related design: [[docs/design/reported-position-book-risk]] and
  [[docs/design/research-intake-and-dataset-snapshots]].
- Field matrix: [[docs/trading-request-field-trials]].

## Outcome

Let an AutoQuant coworker answer one common target-position question: given a
caller-reported funded book, positive cash, one caller-authorized asset, one
fixed historical covariance window, and a maximum annualized-volatility
budget, find the largest cash-funded asset weight that satisfies the budget or
prove that the permitted path has no compliant point.

## Context

Representative request:

> 我现在 AAPL 15%、MSFT 15%、QQQ 20%，还有 50% 现金，想开 NVDA。按最近一年的
> 波动，组合年化波动别超过 15%，其他仓位不动，NVDA 最多开到多少？先别考虑税和
> 下单。

AutoQuant `0.8.4` can solve the opposite one-dimensional path: reduce one
strictly positive holding to cash until a fixed historical volatility ceiling
is met. Its request, frozen authority, Judge, Explorer, CLI, and Studio encode
that direction implicitly. The existing model cannot bind a zero-weight
requested asset, authorize cash as the only funding source, or select the
largest compliant weight.

This is not a general portfolio optimizer. The caller fixes every unchanged
holding, the adjustable asset, cash funding, covariance window, ceiling, and
maximum-weight objective. Only one scalar remains to solve.

## Scope

### In scope

- Preserve one external-reported funded baseline and one requested,
  non-context adjustable asset that may begin absent from the book.
- Generalize one-leg sizing into an explicit asset/cash direction:
  `decrease` retains the smallest-compliant-reduction meaning and `increase`
  adds the largest-compliant-cash-funded meaning.
- Bind one annualized-volatility ceiling and one fixed 63/126/252-bar
  covariance window.
- Solve the exact bounded quadratic over the authorized interval, including
  unchanged, fully funded, boundary-sized, and infeasible semantics.
- Return the complete target book, cash, modeled risk, concentration,
  contributions, and cross-lookback diagnostics.
- Preserve no-account, no-tax, no-order, and no-trading authority through Run,
  strict Explorer, orientation, CLI, Studio, and handoff.

### Out of scope

- Choosing the asset, funding from another risky leg, changing multiple
  holdings, expected-return optimization, leverage, shorts, or scenario
  generation.
- Taxes, costs, liquidity, suitability, Order/TPSL construction, or execution.
- Treating one historical covariance window as a future-volatility guarantee.

## Acceptance

- [x] Preserve a strict `0.8.4` public failure reproduction for the cash-entry
  request without fabricating scenarios or a non-zero baseline position.
- [x] One explicit direction-aware request and frozen policy represent both
  asset-to-cash and cash-to-asset paths without hidden defaults.
- [x] Deterministic evidence covers boundary-sized, fully funded, unchanged,
  and infeasible states plus malformed/tampered authority.
- [x] Judge, strict Explorer, CLI, orientation, and Studio agree on
  the exact complete target book and no-trading boundary.
- [ ] One clean real-Yahoo Project answers the representative request.
- [ ] Focused/full tests, docs, package smoke, patch version, commit/push, tag,
  and repository cleanliness pass.

## Work

- [x] Create the English Project brief and reproduce the current contract gap.
- [x] Generalize and document the one-leg asset/cash sizing contract.
- [x] Implement exact Judge and independent Explorer reconciliation.
- [x] Update Agent and human surfaces with bounded tests.
- [ ] Complete the clean real-data trial and release audit.

## Findings and decisions

- 2026-07-29 — This request is target-position research, not execution. The
  scalar path is caller-owned; AutoQuant may solve its historical-risk
  boundary while OpenAlice retains authenticated holdings, suitability,
  timing, and Order authority.
- 2026-07-29 — A zero baseline weight is meaningful for the adjustable entry
  asset but should not be falsified into `positionSnapshot.weights`. The
  requested universe supplies its market-data authority; the frozen sizing
  policy supplies its only permitted target-book role.
- 2026-07-29 — The exact `0.8.4` public intake rejects the proposed request
  because the old `destination` is missing, `direction` is unknown, the kind
  is fixed to reduction, and NVDA is not a positive baseline holding. The
  transactional command leaves no partial Project.
- 2026-07-29 — The pre-1.0 request contract is intentionally replaced by
  `one-asset-against-cash-for-volatility-ceiling` plus explicit
  `direction: increase|decrease`; no compatibility alias or silent migration
  is added.
- 2026-07-29 — Increase data authority is the ordered union of baseline
  holdings and the one sizing asset. It does not contaminate the separately
  frozen caller-scenario comparison universe.
- 2026-07-29 — The real Yahoo development Run returns a strict boundary, not
  a fully funded endpoint: NVDA `0 → 0.2440994362`, cash
  `0.50 → 0.2559005638`, and governing modeled volatility exactly `0.15`.
  The same book breaches the diagnostic ceiling at 63 and 126 sessions.

## Verification

- AutoQuant `0.8.4` public `aq project intake` returned
  `validation.failed` for the honest direction-aware request and created no
  `us-megacap-nvda-cash-entry-v084-intake-attempt` directory.
- Development Project `us-megacap-nvda-cash-entry-v085-dev` intake, strict
  validation, Run `run-20260729T003942383034Z-f63f7b77db6c`, Book Risk
  Explorer, orientation, CLI, and Studio all pass. The Run completed in
  264 ms; Studio reports `valid: true` with no diagnostics.
- The 252-session baseline modeled volatility is `0.08383245`. The exact
  largest compliant NVDA weight is `0.2440994362`, leaving cash
  `0.2559005638`; 63/126-session diagnostics are `0.15955461` and
  `0.16565359`.
- Focused Book Risk, Studio, orientation, and Report tests pass 44/44 in
  16.433 s. Separate CLI/intake coverage passes 44/44 in 405.991 s.
- Documentation validation resolves 992 double-links.
- Final source-tree regression passes 268/268 in 1,455.619 s.
- `uv build` produces `auto_quant-0.8.5.tar.gz` and the matching universal
  wheel. A fresh Python 3.11/Pandas 3 environment installs only that wheel,
  reports `aq 0.8.5`, performs the real Yahoo intake and Run in 248 ms,
  rederives the exact `0.2440994362` NVDA result through strict Explorer, and
  returns a valid Studio snapshot with no diagnostics.

## Progress log

- 2026-07-29 — Selected cash-funded one-asset entry sizing as the next real
  trading-request field trial after completing calendar-month ETF allocation.
- 2026-07-29 — Wrote the English brief in
  `us-megacap-nvda-cash-entry-v084-gap`, then reproduced the exact public
  schema/authority gap against the existing content-locked Yahoo package.
- 2026-07-29 — Implemented and field-ran the direction-aware contract. The
  strict Explorer independently rederived the domain, ceiling root, signed
  asset/cash changes, complete funded book, contribution ledger, and
  cross-lookback status.

## Completion

Pending.
