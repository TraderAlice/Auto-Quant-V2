# Nikkei asset file

Use a non-empty JSON array with exactly:

```json
{
  "symbol": "7203",
  "providerCode": "7203",
  "providerMarket": "1",
  "venue": "XTKS",
  "currency": "JPY",
  "assetClass": "equity"
}
```

- `providerMarket=1` is the observed Nikkei selector for the TSE primary
  listing on the field-trial assets.
- Verify code, issuer, primary listing, and market independently.
- This Skill accepts only four-digit named `XTKS` equities in JPY.
