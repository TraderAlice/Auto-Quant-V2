# Caller-owned Portfolio research policy

Status: V1 implemented.

Related: [[docs/design/request-bound-portfolio-mandates]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/program-research-dossiers]].

## Purpose

AutoQuant is a quantitative-support workbench. A collaborating OpenAlice
workbench owns the question and may know the intended risk, deployable
research capital, and implementation assumptions. AutoQuant owns fixed,
reproducible evaluation under those supplied assumptions.

The boundary is:

```text
caller Research Request.portfolioPolicy
→ content-derived Portfolio Mandate
→ shared Portfolio and governed-RL mechanics
→ immutable Run / Report / Dossier evidence
```

Candidate Agents cannot edit any link in that chain.

## Request contract

`portfolioPolicy` is optional so a caller that only knows assets and direction
can still request support. When present it contains every field:

```json
{
  "grossLimit": 0.8,
  "maxAbsWeight": 0.2,
  "assetMaxAbsWeights": {
    "AAPL": 0.12,
    "NVDA": 0.08
  },
  "annualizedVolatilityCeiling": 0.12,
  "baseCostBps": 15.0,
  "noTradeOneWay": 0.04,
  "referenceNav": 250000.0,
  "decisionEveryBars": 4
}
```

Bounds are deliberately finite:

- `grossLimit`: `(0, 2]`;
- `maxAbsWeight`: `(0, grossLimit]`, and no more than one side budget for
  dollar-neutral mandates;
- `assetMaxAbsWeights`: a possibly empty map of requested assets to finite
  caps in `(0, maxAbsWeight]`;
- `annualizedVolatilityCeiling`: `(0, 1]`;
- `baseCostBps`: `[0, 1000]`;
- `noTradeOneWay`: `[0, 1]`;
- `referenceNav`: `(0, 1e12]`.
- `decisionEveryBars`: integer `[1, 252]`.

When omitted, Core inserts the documented reference defaults `1.0`, `0.30`,
an empty override map, `0.15`, `10`, `0.05`, `1,000,000`, and `1`.

## Mandate contract

The derived Mandate retains construction fields and adds a strict
`implementationPolicy`:

```json
{
  "baseCostBps": 15.0,
  "noTradeOneWay": 0.04,
  "referenceNav": 250000.0,
  "decisionPolicy": {
    "source": "caller-supplied",
    "kind": "every-bars",
    "bars": 4,
    "anchor": "dataset-start"
  },
  "costModel": "linear-traded-notional-v1",
  "capacityModel": "trailing-dollar-volume-participation-v1"
}
```

The risk ceiling remains inside `construction.riskPolicy`. The request hash,
Mandate id, Study dependency hash, Session locks, and Run input hash all
change when any policy value changes.

## Runtime semantics

Portfolio and governed RL both use:

- gross and cap during deterministic signal-to-target allocation;
- annualized volatility ceiling during proposed and executed-book risk
  governance;
- no-trade band during post-drift rebalance decisions;
- decision cadence during signal-state transitions, target construction,
  ordinary execution, and governed-RL action availability;
- base cost in net return, reward, attribution, and action opportunities;
- reference NAV in participation and capacity evidence.

Portfolio cost stress is anchored at `0`, the exact base cost, and a fixed
adverse `max(25, 2 × base)` bps scenario. The caller base remains the selection
score; stresses stay diagnostic.

## Authority

These are research assumptions, not:

- verified Broker fees or market impact;
- current OpenAlice UTA cash, NAV, buying power, or permissions;
- authorization to trade;
- candidate-tunable hyperparameters.

Reports and Dossiers must describe them as caller-supplied or documented
default assumptions and retain `tradingAuthority: none`.

## Known limits

- Per-asset maximum caps do not express named hedges, minimum allocations, or
  correlated group limits; see
  [[docs/design/caller-owned-asset-position-caps]].
- Linear bps cost is not spread, impact, borrow, funding, or tax.
- Reference NAV only scales OHLCV participation; it does not change percentage
  weights or create account state.
- Signal thresholds and Portfolio/RL algorithms remain fixed Harness
  authority. See [[docs/design/caller-owned-decision-cadence]].
