# Yahoo asset inventory

Provide a JSON array:

```json
[
  {
    "symbol": "AAPL",
    "providerSymbol": "AAPL",
    "venue": "XNAS",
    "currency": "USD",
    "assetClass": "equity"
  }
]
```

- `symbol` is the path-safe AutoQuant research identifier.
- `providerSymbol` is sent to Yahoo and may contain a venue suffix.
- `venue`, `currency`, and `assetClass` are caller/researcher claims checked
  against independent market evidence; Yahoo metadata does not authenticate
  them.
- Use unique values for both `symbol` and `providerSymbol`.
- Supported first-pass output is completed daily data only.
