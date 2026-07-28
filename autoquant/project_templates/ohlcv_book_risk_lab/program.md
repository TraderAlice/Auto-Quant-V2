# Fixed reported-book covariance and reduction audit

The Judge reads the immutable `request.json` position snapshot and the
researcher-owned `strategies/book-risk-scenarios.json` method declaration. It
uses only closed OHLCV observations at or before the snapshot `asOf` time.

It must report:

- annualized covariance risk through each predeclared lookback;
- signed and absolute component-risk contribution;
- component-risk HHI and effective risk bets;
- first-principal-component share of the held-asset correlation matrix;
- exact pairwise held-asset correlations;
- one standardized, cash-funded reduction of each position, ranked by
  volatility reduction per unit weight;
- a sampled rolling path under the primary lookback.

The reduction table is comparative historical sensitivity, not a tax-aware
recommendation or order. Never silently replace reported weights with a
model-generated target.
