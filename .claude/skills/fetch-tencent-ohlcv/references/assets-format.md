# Tencent A-share asset inventory

```json
[
  {
    "symbol": "600519",
    "providerSymbol": "sh600519",
    "venue": "XSHG",
    "currency": "CNY",
    "assetClass": "equity"
  },
  {
    "symbol": "000001",
    "providerSymbol": "sz000001",
    "venue": "XSHE",
    "currency": "CNY",
    "assetClass": "equity"
  }
]
```

- `providerSymbol` must use the explicit observed `sh` or `sz` prefix plus a
  six-digit code.
- The Skill verifies prefix/declared-venue consistency but not listing truth.
- Initial scope is XSHG/XSHE A-share equity in CNY. XBSE requires separately
  proved symbol semantics.
- Output volume is shares; the observed provider lot value is multiplied by
  100 and retained in the audit.
