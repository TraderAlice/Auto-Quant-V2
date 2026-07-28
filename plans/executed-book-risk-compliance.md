# Executed-book hard compliance

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/executed-book-risk-compliance]],
  [[docs/design/portfolio-risk-governor]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/rl-factor-policy-lab]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Every Portfolio and governed-RL path proves that the final post-drift,
post-no-trade executed book—not merely its proposed target—obeys both the
complete request-bound Portfolio Mandate and the covariance volatility ceiling
whenever the causal forecast is available.

## Context

The current Core scales proposed targets to the fixed volatility ceiling and
then separately applies a no-trade band during accounting. A retained drifted
book is therefore not the same object the risk governor checked. Governed RL
rollouts repeat the same ordering. The gap can make a valid target-level risk
claim coexist with an unverified final position path.

A real portfolio operator needs the compliance boundary to be the book that
earns the next return. When a drifted book exceeds the ceiling, execution must
override the no-trade band with the smallest proportional risk repair. This
remains target-weight research and creates no Broker or live-trading authority.

## Scope

### In scope

- One causal executed-book hard-compliance decision shared by Portfolio and
  governed RL.
- Deterministic sign, context-only, gross, side, net, and per-asset repair
  after drift and ordinary target/no-trade selection.
- Minimum proportional scale-down when a retained drifted book breaches the
  request-bound ceiling.
- Exact daily/decision evidence, split compliance metrics, and strict
  reconciliation.
- CLI, Reports, Dossiers, decision matrix, and Studio evidence.

### Out of scope

- Scaling risk up, optimizing turnover versus risk, nonlinear impact, intraday
  stops, account capital, orders, or Broker/UTA state.
- Replacing sample covariance or changing the caller-derived risk mandate.
- Treating zero breach rates as candidate-selection advantage.

## Acceptance

- [x] Final executed weights use only returns through decision close and obey
  the complete Mandate plus the declared volatility ceiling whenever the
  forecast is available.
- [x] A drifted per-asset cap breach bypasses no-trade with explicit
  constraint-only evidence and exact repair turnover/cost.
- [x] A risk breach bypasses the no-trade band with an explicit risk-only
  reason and the minimum proportional scale-down; ordinary in-band books
  remain untouched.
- [x] Portfolio and every governed-RL training/evaluation path use the same
  execution-risk primitive and expose pretrade, proposed, and executed risk.
- [x] Split diagnostics reconcile every date and expose forecast coverage,
  pretrade breaches, overrides, executed breaches, and maximum executed risk.
- [x] Capacity, costs, returns, artifacts, explorer, CLI, Reports, Dossiers,
  Studio, and Session context preserve one verified interpretation with no
  trading-authority claim.
- [x] Deterministic tests prove causality, constraint/risk no-trade overrides,
  minimum risk scaling, tamper rejection, RL parity, and unchanged safe paths.

## Work

- [x] Audit target-risk versus executed-book ordering in Portfolio and RL.
- [x] Implement the shared execution-risk decision and aggregate evidence.
- [x] Add verified public projections, documentation, and Studio presentation.
- [x] Run focused/full tests, browser QA, package smoke, and completion audit.

## Findings and decisions

- 2026-07-25 — Target-level governance is insufficient because post-drift
  no-trade retention chooses a different book after the governor runs.
- 2026-07-25 — Risk compliance outranks the turnover band. The repair will
  scale the drifted book proportionally instead of forcing the full proposed
  target, preserving intent with the minimum necessary notional change.
- 2026-07-25 — Executed compliance is a safety invariant and contextual
  diagnostic, not a favorable selection metric.
- 2026-07-28 — A real BTC hourly Run exposed `0.316860` executed weight under
  a `0.30` cap because drift retention was checked only for covariance risk.
  V2 makes the complete Mandate authoritative on the final book, accounts for
  the repair trade, and exposes identical Portfolio/RL evidence.
- 2026-07-25 — Isolated-wheel smoke exposed a pre-existing explorer mismatch:
  liquidity reconciliation included a purged split boundary row. Projection
  now uses the Judge-authoritative `signalEnd`, with a dedicated regression
  test.

## Verification

- `uv run python -m unittest discover -s tests -v` passed all `151` tests in
  `526.816` seconds on the final code state.
- `uv run python scripts/check_doc_links.py` resolved all `478` documentation
  double-links.
- `uv run python -m compileall -q autoquant tests`,
  `node --check autoquant/studio_assets/studio.js`, and `git diff --check`
  passed.
- A wheel installed into a fresh Python 3.11 environment, constructed one
  multi-Study desk, executed Portfolio and governed-RL Runs, and projected
  `100%` validation forecast coverage with zero executed breaches. RL
  reconciled all six declared fold/seed validation paths. Packaged Core,
  explorers, templates, and Studio assets were present.
- In-app browser QA at `http://127.0.0.1:8774/` confirmed Portfolio and RL
  executed-risk readouts, lane switching, no horizontal overflow at
  `1280×720`, and no application console errors.

## Progress log

- 2026-07-25 — Plan created from the professional workflow audit.
- 2026-07-25 — Added the shared final-book decision, Portfolio/RL evidence,
  strict artifact reconciliation, public CLI/Report/Dossier/Studio
  projections, and tamper rejection.
- 2026-07-25 — Completed final full tests, isolated-wheel smoke, documentation
  validation, and visible Studio QA.

## Completion

Completed with every acceptance item backed by executable evidence. The final
implementation commit records the exact repository state.
