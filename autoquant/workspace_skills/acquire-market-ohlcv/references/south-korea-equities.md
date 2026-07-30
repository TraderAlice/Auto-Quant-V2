# South Korea listed equities

- Preserve the exact KRX market/board and provider symbol separately.
- Use `Asia/Seoul`; verify session dates and suspended observations.
- Confirm price adjustment, share/lot volume units, and currency.
- Do not infer delisting coverage or historical index membership from a
  successful current symbol lookup.

## Routes

- Naver Finance: independent raw route through `$fetch-naver-ohlcv`; verify
  the six-digit code and board identity outside the response.
- Yahoo: broad route through `$fetch-yahoo-ohlcv`; verify `.KS` versus `.KQ`,
  history, freshness, currency, and adjustment on the same sample.

Neither route is KRX authority. Preserve that limitation even when they agree.
