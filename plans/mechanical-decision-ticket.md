# Make the current mechanical decision inspectable

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/signal-policy-and-attribution]],
  [[docs/design/portfolio-decision-explorer]], and
  [[docs/design/studio-observation-surface]].

## Outcome

One verified Portfolio Run exposes a current research decision ticket that
shows, in causal order, the signal threshold state, target construction,
portfolio-risk adjustment, and execution gate. A trader or collaborating Agent
can see what would make each asset enter, exit, or reverse, how far its current
cross-sectional percentile is from that boundary, and why the historical book
did or did not rebalance.

## Context

The immutable decision ledger already contains factor percentiles, signal
states, raw and governed targets, drifted weights, risk status, trade weights,
and execution reasons. The bounded Core projection and Studio skip most of the
intermediate decision chain, so the current book is explainable only by
opening raw artifacts. That is the wrong handoff for a quantitative workbench:
weights without trigger and gate context look like unexplained allocation
advice.

## Scope

### In scope

- A deterministic Core projection of state-dependent entry, exit, and reversal
  thresholds from the verified decision ledger and fixed signal parameters.
- Explicit separation of percentile-state triggers, target sizing, the
  covariance risk governor, and the portfolio no-trade/final-risk gate.
- Current per-asset score, trigger distance, target/pretrade/executed weights,
  and research-only action rationale in CLI JSON and Studio.
- Strict schema, tamper, legacy/unavailable-score, browser, and packaging
  regression coverage.

### Out of scope

- Price targets, forecasts of when a rank will cross, Broker orders, TPSL,
  account balances, or OpenAlice UTA mutation.
- Changing the fixed signal policy, portfolio objective, Judge, immutable Run,
  or candidate-selection semantics.
- Caller capital/notional mandates and nonlinear market impact.

## Acceptance

- [x] Every current tradable asset exposes only the state transitions permitted
      by its fixed construction family, with exact comparator and percentile
      threshold.
- [x] Trigger distance is labelled as a same-cross-section percentile buffer,
      never a price target or probability.
- [x] The current decision chain reconciles target sizing, risk scaling,
      proposed one-way turnover, ordinary no-trade, risk override, and final
      execution reason from immutable evidence.
- [x] `aq run portfolio` and Studio consume the same Core object and clearly
      retain `tradingAuthority: none`.
- [x] Bounded tests prove long/cash, short/cash, dollar-neutral, missing-score,
      context-only, schema, and browser behavior.

## Work

- [x] Audit existing ledger, Core projection, and Studio gaps.
- [x] Define and implement the current mechanical-decision contract.
- [x] Add Studio decision-chain and per-asset trigger presentation.
- [x] Update durable design/CLI documentation and bounded regressions.
- [x] Run a real controlled Portfolio Run and complete browser/package audits.

## Findings and decisions

- 2026-07-25 — The existing Judge already publishes every required primitive;
  this is a verified read-model and HCI gap, not a reason to change evaluation
  semantics or regenerate old Runs.
- 2026-07-25 — A trigger distance is the current percentile-point buffer with
  peer ranks held fixed for interpretation. It is not a price distance,
  time-to-trigger estimate, or forecast.
- 2026-07-25 — Signal-state changes and portfolio rebalances are separate
  gates. Target resizing can occur without a state transition, and the
  covariance repair may override the ordinary no-trade band.

## Verification

- A clean affected regression ran 25 tests in `179.231s`: the complete
  Portfolio explorer module, request-driven long/cash intake, public Portfolio
  CLI construction/projection, and Studio HTTP/assets tests all passed.
- Rehashed signal-threshold tampering was rejected even when the altered `0.70`
  long-entry threshold remained structurally valid.
- Historical Yahoo equity Run
  `run-20260724T051917800917Z-9b8d72896b38` projected successfully without
  mutation. On `2026-07-21` it showed two state changes, `20.672043%` proposed
  and actual one-way turnover versus the fixed `5%` band, exact
  AAPL/MSFT/NVDA/QQQ/SPY trigger sets, and `tradingAuthority: none`.
- The same adverse historical Run retained validation net Sharpe
  `-1.467922`, total net return `-50.0884%`, and maximum drawdown
  `-53.8244%`; the new surface did not turn explanatory evidence into a
  favorable verdict.
- Browser QA at 1280 px showed the four-stage chain and complete per-asset
  table with document width `1280`, table scroll/client width `953/953`, and
  no console warnings or errors.
- `uv run python scripts/check_doc_links.py` resolved 552 double-links;
  Python compile, JavaScript syntax, and diff checks passed.
- A fresh wheel contained the Core projection and all three Studio assets.

## Progress log

- 2026-07-25 — Plan activated after the current Studio book was compared with
  the already richer immutable decision ledger.
- 2026-07-25 — Completed after Core/CLI/Studio parity, negative real-data
  compatibility, tamper rejection, browser layout, and wheel audits passed.

## Completion

AutoQuant now exposes one verified, research-only mechanical decision ticket
instead of presenting unexplained weights. The current state machine,
Mandate-permitted next boundaries, risk-governed targets, drifted book,
portfolio execution gate, and final historical action are visible together in
the CLI and Studio. Old immutable Runs remain readable, and no new price,
order, Broker, account, or selection authority was introduced.
