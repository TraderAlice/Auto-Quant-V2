# Gold futures and dollar hourly field trial

- Status: `active`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/configurable-session-interval-inputs]],
  [[docs/design/panel-native-factor-api]], and
  [[docs/design/project-derived-workbench-needs]].
- Field matrix: [[docs/trading-request-field-trials]].

## Outcome

Let an AutoQuant coworker receive one caller-style hourly gold-futures timing
question with dollar context, preserve the exact research-series and
market-clock meaning, and return either reproducible quantitative evidence or
an explicit unsupported boundary without substituting equity ETFs, fabricating
closed-market bars, or claiming executable futures contracts.

## Context

Representative request:

> 用小时线看看黄金期货和美元，什么时候适合做多黄金？

Current Research Requests accept `future`, `forex`, and `index` asset classes,
but verified intake supports aligned daily session panels, continuous 24/7 UTC
bars, XNYS regular sessions, or observed-only ragged daily Factor panels. CME
gold and a dollar-index research series are neither Crypto-style 24/7 nor
XNYS. Their hourly provider observations include daily maintenance and weekend
closures; filling those gaps would change returns and multi-interval context.

This trial first uses explicitly named provider-defined continuous research
series. It does not pretend those series identify a tradable contract month,
roll rule, margin requirement, tick value, expiry, venue order, or fill.

## Scope

### In scope

- Clarify one representative question before data retrieval: exact gold and
  dollar research series, one observed-bar horizon, long-only research intent,
  contextual versus position authority, provider, and no-execution boundary.
- Preserve the existing public-route success or failure before changing Core.
- Determine whether the smallest reusable gap is an observed-only intraday
  Factor panel/clock contract or whether the question requires a separate
  contract-chain authority that must remain unsupported.
- If justified, add only the narrow data/intake/runtime boundary needed for
  causal hourly Factor research with absent closed-market observations.
- Use bounded provider data, immutable evidence, strict Explorer/orientation,
  and an English Project brief.

### Out of scope

- Inventing a universal futures/FX calendar, backtest Broker, or roll engine.
- Claiming Yahoo or another provider's continuous symbol is exchange-official
  contract-chain truth.
- Contract selection, expiry, delivery, margin, leverage, funding, tick value,
  spread/fill simulation, order placement, TPSL, or live trading authority.
- Replacing futures/dollar series with GLD/UUP merely to fit XNYS intake.
- Optimizing until the timing hypothesis becomes positive.

## Acceptance

- [x] A strict English Project brief freezes caller-owned meaning before data
  retrieval or execution.
- [x] The current public route is reproduced and any failure names the exact
  clock, alignment, asset-class, or contract-authority boundary.
- [x] Any Core change is the smallest reusable boundary proven by the trial;
  unsupported contract-chain semantics remain explicit.
- [ ] A bounded real-data Project either executes with causal evidence and
  limitations or terminates with a useful machine-readable refusal.
- [ ] CLI, orientation, Studio, documentation, deterministic tests, packaging,
  commit/push, and repository cleanliness pass in proportion to the change.

## Work

- [x] Create and clarify the representative Project.
- [x] Acquire a bounded provider sample only after the research-series contract
  is frozen.
- [x] Reproduce the current public intake/runtime boundary.
- [x] Design and implement only a justified reusable gap.
- [ ] Execute and interpret the clean field trial.
- [ ] Complete release or explicit-boundary audit and close the plan.

## Findings and decisions

- 2026-07-29 — The first trial will not silently translate gold futures and
  dollar context into equity ETFs. Provider-defined continuous series are
  acceptable only as disclosed historical research inputs, not executable
  contract authority.
- 2026-07-29 — Hourly horizon means a fixed count of observed closed bars.
  Calendar hours across maintenance/weekend closures are a different question
  and must not be inferred.
- 2026-07-29 — Bounded Yahoo metadata identifies `GC=F` as `FUTURE / CMX` but
  `DX-Y.NYB` as `INDEX / NYB`. The raw request asked for dollar context, not a
  dollar futures contract; the Project brief now preserves that mixed class
  instead of perpetuating the researcher's mistaken futures label.
- 2026-07-29 — The Factor Judge already supports a single request-bound
  temporal target. The reproduced design gap is narrower: observed-only
  intraday intake, exact mixed dataset classes, and role-aware intake breadth.
  Portfolio/RL and executable futures semantics remain out of scope.
- 2026-07-29 — The unchanged public `aq project intake` route rejected the
  honest proposed package before creating a Project. Its versioned JSON error
  named unsupported V5/hourly/observed-panel fields, per-asset class and volume
  semantics, and the real `GC=F` provider symbol. No supported package contract
  can encode the sample without changing its meaning.
- 2026-07-29 — V5 is intentionally Factor-only and base-only. It adds exact
  per-asset class and volume semantics, observed absent-no-fill timestamps,
  one explicit prediction asset, and prediction-owned horizon/purge timing.
  It does not add a market calendar, higher-interval aggregation, Portfolio,
  RL, contract-chain, margin, or execution authority.
- 2026-07-29 — The first complete regression passed 259 of 263 tests. Its four
  failures shared one cause: governed RL baseline Runs exhausted the existing
  90-second Judge budget under sustained suite contention. Every exact failed
  case passed unchanged in isolation, including the 112.990-second
  reproducibility case and three Explorer/campaign cases in 268.889 seconds.
  The caller explicitly approved a 120-second RL allowance. Only that hard
  timeout changes; Factor/Portfolio budgets and RL seeds, folds, episodes, and
  training logic remain fixed.

## Verification

- 11 focused V5/interval/public-schema tests passed.
- The combined 66-test intake/Factor/interval/CLI run had one V2 Judge timeout
  under load and no semantic failure; the exact isolated V2 case then passed
  end-to-end in 107.719 seconds.
- Public Yahoo V5 smoke Project `gold-dollar-hourly-v5-smoke` completed
  immutable Run `run-20260728T193549738971Z-d51d27ce72cf`. Orientation and
  strict Factor Explorer returned zero diagnostics.
- The first complete 263-test gate finished in 1775.799 seconds with 259
  passes and four governed-RL timeout-chain failures. The exact root
  reproducibility test passed alone in 112.990 seconds, and the remaining
  three cases passed together in 268.889 seconds without a code change.

## Progress log

- 2026-07-29 — Plan created after the `v0.8.1` OHLCV price-event release.
- 2026-07-29 — Created the blank `gold-dollar-hourly-timing` Project and froze
  exact provider series, asset roles, observed-bar horizons, causal evidence
  rules, and the no-contract/no-execution boundary in its English brief before
  retrieving data.
- 2026-07-29 — Retrieved a closed-bar provider audit for 2024-08-01 through
  2026-07-27: 11,373 `GC=F` rows, 11,847 `DX-Y.NYB` rows, and 11,359 exact
  timestamp intersections. Preserved daily maintenance, weekend, DST/anchor,
  and provider irregularities as absence.
- 2026-07-29 — Reproduced the current boundary through public
  `aq project intake ... --template ohlcv-factor-lab --json`; the command
  returned `validation.failed` with no partially created Project.
- 2026-07-29 — The real V5 smoke retained 11,373 target gold observations and
  11,359 exact same-timestamp dollar-index context rows. Its Factor Run used
  `single-asset-temporal`, a 24-gold-bar primary horizon, and
  `per-target-observed-bars` purge authority.

## Completion

Pending.
