# Reported-book reallocation scenario field trial

- Status: `active`
- Updated: `2026-07-28`
- Related design: [[docs/design/reported-position-book-risk]] and
  [[docs/design/research-intake-and-dataset-snapshots]].
- Field matrix: [[docs/trading-request-field-trials]].

## Outcome

Let an AutoQuant coworker preserve one caller-reported current book and compare
a bounded set of caller-specified, fully funded hypothetical reallocation books
under the same fixed historical risk model, so the user can ask “which proposed
transfer diversifies better?” without turning the Workbench into an optimizer
or order system.

## Context

AutoQuant `0.6.0` can audit one reported or hypothetical funded weight snapshot
and rank equal one-percentage-point reductions toward cash. A common next
question is conditional rather than open-ended:

> 我现在 AAPL 20%、MSFT 25%、NVDA 30%、QQQ 25%。想拿 10% 去加 TSLA：从 NVDA
> 减还是从 QQQ 减，更能分散？先别考虑税和下单。

The existing Lab can answer the current-book concentration but cannot bind and
reconcile both proposed funded transfers in one immutable Run. Running
unrelated Projects with silently edited snapshots would lose the shared
baseline/scenario identity and make comparison easier to misstate.

The existing twelve-asset Yahoo XNYS package already contains TSLA, so this
trial requires no new data class, provider, or service. It tests whether the
workbench can express a more useful decision while retaining the price/volume
and descriptive-authority boundary.

## Scope

### In scope

- Preserve one external-reported baseline snapshot and a small bounded list of
  caller-specified hypothetical fully funded snapshots.
- Require the same as-of time, base currency, dataset, held/requested asset
  authority, and fixed 63/126/252-session method across baseline and scenarios.
- Compare annualized volatility, component-risk concentration, effective risk
  bets, per-asset risk contributions, and explicit deltas versus the baseline.
- Make the Run, strict Explorer, orientation, Studio, schemas, CLI, and
  documentation agree on scenario identity and ranking.
- Reproduce the NVDA-to-TSLA versus QQQ-to-TSLA question from a clean Harness
  commit and preserve a useful conclusion even if neither proposal improves
  the modeled book.

### Out of scope

- Searching or optimizing weights, generating scenarios from the data, or
  assigning scenario probabilities.
- Tax lots, realized gains, replacement suitability, transaction costs, live
  holdings, approvals, or order construction.
- Different scenario timestamps, currencies, leverage policies, datasets, or
  covariance methods within one comparison.
- General portfolio optimization or a universal scenario DSL.

## Acceptance

- [ ] A strict request can bind one reported baseline plus two or more
  explicitly named hypothetical funded books without ambiguous delta
  interpretation.
- [ ] Intake rejects scenario assets outside request/data authority, mismatched
  timestamps/currencies, duplicate ids, incomplete funding, and hidden
  optimization semantics.
- [ ] One immutable fixed Run and strict Explorer reconcile every scenario
  metric and delta against the exact baseline using the same covariance
  windows.
- [ ] Agent orientation and Studio expose a closed descriptive comparison with
  no Session, automatic selection, trading, or order authority.
- [ ] A clean Yahoo field Run answers the NVDA-versus-QQQ funded TSLA transfer,
  and the Project records the raw request, assumptions, framework gap, Harness
  identity, and evidence.
- [ ] Focused/full regression, package smoke, documentation, commit, push, and
  repository cleanliness pass.

## Work

- [x] Preserve a `0.6.0` failure reproduction showing the current single-book
  Lab cannot answer the bounded comparison.
- [x] Define the smallest strict request and derived snapshot/scenario contract.
- [x] Implement fixed Judge artifacts, Run schema, strict Explorer, CLI,
  orientation, and Studio projection.
- [x] Add deterministic success, malformed-input, tamper, and authority tests.
- [ ] Execute and interpret the clean real Yahoo field trial.
- [ ] Complete release audit, record evidence, commit, push, and close the plan.

## Findings and decisions

- 2026-07-28 — A proposed transfer is not an Order. The useful quantitative
  object is a caller-authored hypothetical funded book compared under one
  historical model; OpenAlice and the user retain whether and how to execute.
- 2026-07-28 — Complete target snapshots are preferred over sparse weight
  deltas at the public boundary. They avoid ambiguous residual cash,
  renormalization, and which leg funds which addition.
- 2026-07-28 — The Workbench may rank only the caller-supplied scenarios by
  declared descriptive metrics. It must not search nearby weights or relabel
  the result as an optimum.
- 2026-07-28 — Project `us-megacap-book-reallocation-v060-gap` validates and
  authorizes AAPL, MSFT, NVDA, QQQ, and TSLA, but its derived position snapshot
  contains only the four-asset reported baseline and no scenario field.
  Orientation therefore offers a baseline Run that cannot answer the actual
  two-proposal question. The Agent correctly stopped before manufacturing a
  successful but irrelevant result.
- 2026-07-28 — The `0.7.0` contract accepts one to eight named complete
  `hypothetical-weights` books, not sparse transfers. Each book shares the
  baseline timestamp/currency, remains within requested non-context authority,
  is independently funded, and is frozen with explicit
  `caller-hypothetical-not-authenticated` / no-trading authority.
- 2026-07-28 — Scenario comparison uses the ordered union of baseline and
  supplied assets and one common return panel for every book. The fixed Judge
  emits three-window volatility/HHI/effective-bet deltas and ranks only the
  supplied books; primary-window per-asset contribution changes make the
  result explainable without granting optimization authority.
- 2026-07-28 — The strict Explorer reconciles frozen books, scenario ranks and
  deltas, CSV/report identity, weight deltas, component-variance sums,
  risk-share sums/HHI, and largest-contributor identity. Rehashed semantic
  tampering is rejected even when the Run manifest is recomputed.

## Verification

- AutoQuant `0.6.0` public intake created
  `us-megacap-book-reallocation-v060-gap` with
  `status: ready-for-run`, requested TSLA authority, and no diagnostics.
- `aq validate` succeeds and `aq orient` preserves the exact delegated
  reallocation question plus fixed descriptive/no-trading authority.
- `strategies/position-snapshot.json` contains only the reported baseline and
  no scenarios, proving the current Run cannot bind either caller-specified
  funded book.
- The Project's English `research.md` records complete baseline and scenario
  weights; `framework-needs.md` records the missing contract and rejects
  unrelated-Project comparison as an unaudited workaround.
- `uv run python -m compileall -q autoquant tests`,
  `node --check autoquant/studio_assets/studio.js`, and
  `uv run python -m unittest tests.test_book_risk_lab` pass with eight focused
  baseline, success, malformed-input, authority, lifecycle, and rehashed
  tamper tests.
- `uv run python -m unittest tests.test_book_risk_lab tests.test_intake
  tests.test_cli tests.test_orientation tests.test_studio tests.test_version`
  passes all 62 cross-boundary tests in 386.866 seconds. Research,
  documentation, and version tests pass seven additional checks; all 959
  documentation double-links resolve.

## Progress log

- 2026-07-28 — Plan created after the clean reported-book field trial proved
  the baseline audit and exposed the next practical current-book question.
- 2026-07-28 — Preserved the `0.6.0` failure reproduction and stopped before
  running a baseline-only Study that would not answer the delegated question.
- 2026-07-28 — Implemented the strict `0.7.0` complete-book scenario contract,
  fixed Judge evidence, Explorer reconciliation, CLI/Studio projection, and
  focused tests. Clean Yahoo field execution and release audit remain.

## Completion

Pending.
