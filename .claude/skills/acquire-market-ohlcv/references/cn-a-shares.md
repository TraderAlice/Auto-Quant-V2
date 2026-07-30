# Mainland China A shares

- Preserve `XSHG`, `XSHE`, or `XBSE` explicitly and keep the research symbol
  separate from each provider's prefixed/suffixed code.
- Use `Asia/Shanghai`; verify closures and suspensions without filling missing
  bars.
- State whether prices are raw, forward-adjusted, or backward-adjusted and
  freeze the provider's exact algorithm claim. These series answer different
  research questions.
- Verify whether volume is shares, lots, or another unit and whether amount is
  being substituted for volume.
- Keep price-limit and suspension observations; they are market behavior, not
  generic bad rows.

## Routes

- Eastmoney: observable route through `$fetch-eastmoney-ohlcv`. It preserves
  amount evidence for a strong lot-to-share audit, but connection closures or
  throttling must be recorded as degraded behavior.
- Tencent Finance: independent observable raw route through
  `$fetch-tencent-ohlcv`; compare its explicit lot-to-share conversion before
  accepting it.
- Yahoo: broad independent route through `$fetch-yahoo-ohlcv`; prove its
  symbol, freshness, adjustment, suspension, and history behavior on the same
  sample before acceptance.

No one of these is silently substituted for another. Route selection must
name the required adjustment, history, freshness, access behavior, and
evidence quality.
