# Japan listed equities

- Name the exact Tokyo listing and provider symbol. A numeric code plus suffix
  is a provider convention, not venue proof.
- Use `Asia/Tokyo` and verify completed session dates, holidays, and any
  historical session-structure change relevant to intraday work.
- Verify split adjustment and volume units independently.
- Do not treat a current TOPIX or Nikkei constituent list as historical
  membership.

## Routes

- Nikkei recent displayed history: use `$fetch-nikkei-ohlcv` for a bounded
  recent raw OHLCV overlap. It is useful for freshness checks but exposes only
  about one month and is not JPX authority.
- Yahoo: use `$fetch-yahoo-ohlcv` for broader split-adjusted or
  split-and-dividend-adjusted history through `.T` symbols.
- JPX/J-Quants: prefer this credentialed official route when the caller has a
  suitable individual or corporate access contract. It supplies adjusted and
  unadjusted OHLC, but no unauthenticated executable route is claimed by this
  bundle.

Nikkei raw and Yahoo split-adjusted are two independently executable routes
with distinct price contracts. A current overlap can expose freshness,
missing-session, and volume differences; it does not prove same-semantics
historical equivalence.
