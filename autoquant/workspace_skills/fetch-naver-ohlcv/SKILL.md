---
name: fetch-naver-ohlcv
description: Acquire bounded raw completed daily OHLCV for named South Korean equities from Naver Finance's observable historical route, preserve exact response text, validate its Korean table schema, and emit an auditable AutoQuant staging package. Use as an independent KRX route when comparing Yahoo .KS or .KQ history.
---

# Fetch Naver OHLCV

Use Naver Finance as an observable South Korean provider route, not KRX venue,
calendar, adjustment, or licensing authority.

## Workflow

1. Read `$acquire-market-ohlcv` and its South Korea reference.
2. Prepare [assets-format.md](references/assets-format.md).
3. Run:

```bash
python3 scripts/fetch_naver_daily.py \
  --output <workspace>/staging/market-data/<dataset-id> \
  --assets /absolute/path/assets.json \
  --dataset-id <dataset-id> \
  --start YYYY-MM-DD \
  --end-exclusive YYYY-MM-DD \
  --panel observed-only \
  --terms "caller-authorized research retrieval; Naver and KRX terms apply"
```

The initial route supports raw KRW equity daily bars and preserves provider
volume as shares.

## Verify

- Inspect exact raw hashes, Korean header mapping, ranges, row counts, and CSV
  hashes.
- Independently verify security/board identity.
- Compare the same raw observations with `$fetch-yahoo-ohlcv`, including
  freshness and suspension gaps.
- Run `$package-autoquant-ohlcv` and strict intake.

Stop rather than changing symbols, adjustments, or sources when the endpoint
blocks, changes its table, truncates history, or returns ambiguous rows.
