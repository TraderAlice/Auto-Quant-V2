# U.S. listed equities

- Name the listing venue (`XNYS`, `XNAS`, `ARCX`, or another exact venue)
  rather than using “U.S.” as a calendar.
- For ordinary consolidated daily research, use `America/New_York` and verify
  the requested session calendar against the actual instruments.
- Distinguish raw, split-adjusted, and dividend-adjusted history. Never adjust
  only close while leaving raw OHLC.
- Preserve zero-volume observations for investigation; do not assume every
  listed instrument trades every session.
- Treat current index/ETF constituents as a current-universe sample, not a
  survivorship-free historical universe.

## Routes

- `$fetch-nasdaq-ohlcv`: independent raw display-history route for named
  equities and ETFs. It does not authenticate primary venue and is distinct
  from credentialed Nasdaq Data Link Bars.
- `$fetch-yahoo-ohlcv`: broad raw or provider-adjusted historical Chart route;
  adjustment and venue metadata remain external claims.
- Compare the same raw assets and dates before route selection. Credentialed
  alternatives may still be preferable for freshness, adjustment, or
  entitlement.
