# Reported-position Book Risk

Status: implemented in AutoQuant `0.6.0`.

Related contracts: [[docs/design/agent-native-quant-workbench]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/study-run-evidence]], and
[[docs/design/studio-observation-surface]].

## Problem

A common OpenAlice handoff is not “find a factor.” It is:

> I mainly hold AAPL, MSFT, NVDA, and QQQ. Are these really one trade? If I
> want less risk, what should I reduce first?

The existing Portfolio lane cannot answer this honestly. Its weights are
model-generated historical targets, not the caller's current book. Substituting
those targets would silently change the question. AutoQuant also must not query
or impersonate OpenAlice Unified Trading Account authority.

The `ohlcv-book-risk-lab` therefore accepts one explicit reported or
hypothetical weight snapshot and performs a fixed descriptive covariance
audit. It is a separate evidence route, not a Portfolio optimizer and not a
Broker adapter.

## Authority boundary

`request.positionSnapshot` contains:

- `kind`: `reported-weights` or `hypothetical-weights`;
- timezone-aware `asOf`;
- `baseCurrency`;
- non-zero asset `weights`;
- `cashWeight`.

Weights plus cash must sum to one. Gross exposure is bounded at four, each
absolute asset weight at two, and every held asset must be a requested,
non-context asset in the content-locked dataset.

Core derives `strategies/position-snapshot.json` from the normalized request.
That file records the request hash and source provenance and is a fixed Study
dependency. It always declares:

```json
{
  "positionTruth": "external-reported-not-authenticated",
  "tradingAuthority": "none"
}
```

OpenAlice/UTA remains authoritative for authenticated current positions,
lots, tax state, venue capabilities, and execution. AutoQuant does not claim
that the supplied snapshot is still live.

## Fixed analysis

The default bounded method uses 63, 126, and 252 closed-bar lookbacks, with 252
as the primary window. The snapshot `asOf` must lie inside the closed dataset
range. Held-asset closes are inner-aligned and converted to simple returns.

For annualized covariance matrix \(\Sigma\) and reported weights \(w\):

```text
portfolio variance      = w' Σ w
marginal variance       = Σ w
component variance      = w ⊙ (Σ w)
signed risk share       = component variance / portfolio variance
absolute risk share     = |component variance| / Σ|component variance|
component-risk HHI      = Σ absolute risk share²
effective risk bets     = 1 / component-risk HHI
```

The first principal-component share is calculated from the held-asset
correlation matrix. It describes common-movement crowding; it is not a claim
that the holdings are literally one economic trade.

For each asset the Judge moves one percentage point of absolute position
toward cash, or the whole position when smaller, while holding every other
weight fixed. It ranks the resulting annualized-volatility reduction per unit
weight. This is a standardized historical sensitivity. It is not a tax-aware
recommendation, replacement portfolio, or executable order.

## Immutable evidence

One successful Run publishes:

- `book-risk-report.json`;
- `book-risk-contributions.csv`;
- `book-risk-reductions.csv`;
- `book-risk-correlations.csv`;
- `book-risk-path.csv`.

`aq run book-risk` revalidates Run hashes, the frozen position snapshot, exact
method and dataset description, metric reconciliation, contribution and
reduction ordering, pair counts, rolling summaries, and cross-artifact
identity before returning the bounded `book-risk-diagnostics` read model.

Studio exposes the same verified evidence as a Book Risk lane:

- current volatility, effective risk bets, first-PC share, and HHI;
- the contributor and reduction leader;
- lookback stability;
- component-risk tables;
- pairwise correlations;
- rolling crowding context and the authority warning.

## Agent lifecycle

The Quant Agent first writes the English `research.md` and clarifies whether
weights are reported or hypothetical, the as-of time, the meaning of “reduce
first,” and any tax, lot, replacement, or horizon constraints that would
change interpretation.

After the fixed Run, `aq orient` reports
`descriptive-audit-complete`, points to the read-only
`aq run book-risk ... --json` command, and creates no experiment agenda.
The evidence should be explained and returned to the delegating Agent. It
must not be converted into an optimization Session merely because AutoQuant
also supports iterative Factor, Portfolio, and RL research.

## Explicit limitations

The first contract intentionally excludes:

- authenticated account reconciliation;
- point-in-time fundamentals, exposures, sectors, or options Greeks;
- tax lots, borrow, financing, replacement selection, and transaction costs;
- covariance shrinkage or factor-model estimation;
- portfolio optimization and target-weight generation;
- orders, TPSL, approval, or execution.

Those require either another bounded research question or OpenAlice's existing
account and execution surfaces. They must not be inferred from this audit.
