# Portfolio decision explorer

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/CLI]], [[docs/STUDIO]],
[[docs/design/study-run-evidence]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/request-bound-portfolio-mandates]],
[[docs/design/signal-policy-and-attribution]],
[[docs/design/executed-book-risk-compliance]],
[[docs/design/portfolio-liquidity-capacity]],
[[docs/design/research-selection-integrity]], and
[[docs/design/studio-observation-surface]].

## Scope

This document owns the read-only projection from one verified immutable
Portfolio Run into a bounded quantitative diagnostics object consumed by
Agents and Studio. It covers fixed artifact recognition, strict parsing,
cross-artifact alignment, derived path semantics, deterministic sampling,
current mechanical book state, transitions, attribution, identity, and
presentation responsibility.

It does not own portfolio evaluation, candidate selection, artifact
publication, research promotion, live account state, orders, or Broker/UTA
authority.

## Authoritative locations

- Immutable Run and artifact verification: `autoquant/runs.py`
- Portfolio diagnostics projection: `autoquant/portfolio_explorer.py`
- CLI/schema/capability projection: `autoquant/cli.py` and
  `autoquant/capabilities.py`
- Latest-Run observation and browser presentation: `autoquant/studio.py` and
  `autoquant/studio_assets/`
- Contract and integration tests: `tests/test_portfolio_explorer.py`,
  `tests/test_cli.py`, and `tests/test_studio.py`

## Authority flow

```text
immutable Run manifest + hashes
→ load_run verifies every byte and RunResult contract
→ fixed artifact kinds and confined paths
→ strict cross-file parser and alignment
→ full-history accounting path
→ deterministic bounded sample + current state + attribution
→ aq run portfolio / latest Studio snapshot
→ dependency-free browser views
```

The browser never opens a Project path, CSV, or artifact endpoint. It formats
and plots only the Core object. Core does not change any Judge value or infer a
trade recommendation.

## Fixed inputs

V1 recognizes one successful Run declaring exactly one each of:

- `portfolio-report`;
- `portfolio-daily`;
- `portfolio-targets`;
- `portfolio-weights`;
- `portfolio-decisions`.

The daily and executed-weight timestamp panels must match exactly. Proposed
targets may include the final decision timestamp whose forward return is not
yet realized; every realized daily row must still have a target and exactly
one decision row per Study-universe asset. Headers, unique dates/assets,
finite numeric values, states, boolean values, and cross-file universe/order
are validated. Files and row counts have explicit upper bounds.

The report JSON remains immutable supporting evidence. RunResult metrics and
the long-form ledger own displayed portfolio/selection/attribution claims;
the projection does not silently repair missing rows or recompute a competing
Judge score.

## Performance path and sampling

Core compounds the complete chronological daily rows before sampling:

```text
gross growth(t) = product(1 + gross return through t)
net growth(t) = product(1 + net return through t)
benchmark growth(t) = product(1 + benchmark return through t)
drawdown(t) = net growth(t) / running max net growth - 1
```

Each point also carries split role, gross/net exposure, one-way turnover,
unused cash budget, cost, rebalance state, executed-book forecast/ceiling,
risk-only override state, and executed weights. The output is
capped by a caller point budget. Sampling is deterministic and must retain
first/last rows, train/validation/test boundaries, maximum drawdown, and
maximum-turnover dates before filling remaining slots evenly. Derived extrema
and totals use the full history, not only sampled rows.

## Mechanical book and attribution

The latest realized decision date exposes, per asset:

- signal state/event and conviction/risk strength;
- mandate tradability, permitted direction, and allocation status;
- pre-governor target, governed proposed target, pre-trade, executed, and
  trade weights;
- covariance observations, pre/post annualized forecast, fixed ceiling,
  scale, and governor status;
- final post-drift forecast, compliance status, proportional repair scale,
  risk-only override, and execution reason;
- causal ADV, reference-NAV participation, 1%/5% asset and portfolio capacity,
  capacity status, and binding-asset identity;
- target/execution actions and execution reason;
- next-bar gross/cost/net return contribution;
- causal regime and component-variance contribution share.

Recent transitions include bounded non-hold signal events and material
execution actions in chronological order. They explain how fixed hysteresis,
conviction/risk sizing, drift, and the no-trade band produced the visible
book.

Validation and visible-test attribution preserve the exact RunResult
per-asset annualized net contribution, average absolute weight, cost,
turnover, and mean variance-contribution share. Negative covariance
contribution is valid and must not be clamped. Test remains diagnostic and is
labelled accordingly.

## Public contract and Studio

The headless operation is:

```text
aq run portfolio <project-or-workspace> --run <run-id> [--points 40..400]
```

It is read-only and returns one versioned `autoquant-portfolio-diagnostics`
object plus the exact immutable Run artifact identities. Studio embeds the
default bounded projection for only the latest successful Portfolio Run in
each Project. Failure to verify this category produces diagnostics and no
portfolio-explorer claims; other verified Project categories remain visible.

The first explorer version provides:

- verified Portfolio Mandate identity, construction, authorized/context-only
  assets, cash/cap, benchmark, and risk policy;
- one current mechanical-decision chain with state-dependent entry,
  exit, and reversal thresholds, same-cross-section percentile buffers,
  raw/governed targets, drifted pretrade weights, proposed versus actual
  trades, and exact no-trade/final-risk decisions;
- net/gross/benchmark growth and net drawdown;
- exposure, unused cash budget, turnover, cost, and split context;
- a strictly reconstructed validation/test mechanical-parameter neighborhood
  projection with no selection or trading authority;
- current target/executed mechanical book;
- validation/test executed-book forecast coverage, pretrade breaches,
  risk-only overrides, final breaches, and latest final-book status;
- validation/test capacity distributions, coverage, reference-NAV breaches,
  and latest rebalance binding asset;
- validation/test contribution and risk views;
- recent signal/execution transitions;
- exact Run identity and audit/selection labels.

## Invariants

1. No diagnostic value is projected before `load_run` verifies every Run byte.
2. Artifact paths are selected by fixed kind and confined below that Run.
3. Full-history accounting is computed before deterministic sampling.
4. Sample limits bound JSON/UI size without changing extrema or totals.
5. Daily, target, weight, decision, universe, and split identities align
   exactly; no fill/intersection repair is allowed.
6. Validation selection and visible-test audit roles remain explicit.
7. Current positions are historical research weights, never live holdings.
8. Browser rendering cannot mutate, evaluate, promote, or read arbitrary
   files.
9. Context-only assets remain visible research context but have zero target
   and executed weight.
10. Capacity values reconcile the complete ledger and remain contextual only.
11. Daily and per-asset executed-risk evidence reconcile exactly; an available
    final-book breach is invalid evidence.
12. Current trigger buffers are percentile-state diagnostics with peer ranks
    held fixed, never price targets, forecasts, probabilities, or orders.
13. Current proposed one-way turnover equals half the absolute
    governed-target-to-pretrade vector before the execution gate is projected.

## Verification and change checklist

- Prove compounding, drawdown, sampling anchors, file/row caps, and
  cross-artifact alignment with deterministic tests.
- Prove current position rows and attribution match the immutable source
  artifacts exactly.
- Update schema, capabilities, CLI, Studio read model/browser, canonical docs,
  and wheel assets together.
- Exercise a negative real-data baseline; adverse evidence must remain visible
  rather than being styled as successful.
- Run the repository-required documentation and full test suites.

## Known limits

- V1 projects fixed long/cash, short/cash, and dollar-neutral mandate families.
- Studio embeds only the latest successful Portfolio Run per Project.
- The chart is a bounded read model, not a tick/order replay.
- Cross-Run comparison, parameter surfaces, covariance matrices, impact, and
  downloadable artifact routes remain future work.
