---
name: fetch-twse-ohlcv
description: Acquire bounded raw completed daily OHLCV for named TWSE-listed equities from the official TWSE monthly historical report, preserve every exact response, normalize ROC dates and numeric separators, and emit an auditable AutoQuant staging package. Use as the venue-authoritative Taiwan route before comparing the same assets with an independent broad provider such as Yahoo.
---

# Fetch TWSE OHLCV

Use the official TWSE historical report for `TWSE`-listed equities. This Skill
does not cover TPEx, real-time data, a redistribution licence, or corporate
action adjustment.

## Workflow

1. Read `$acquire-market-ohlcv` and its Taiwan reference.
2. Prepare [assets-format.md](references/assets-format.md).
3. Choose completed daily sessions and obtain the applicable TWSE data-use
   basis.
4. Run:

```bash
python3 scripts/fetch_twse_daily.py \
  --output <workspace>/staging/market-data/<dataset-id> \
  --assets /absolute/path/assets.json \
  --dataset-id <dataset-id> \
  --start YYYY-MM-DD \
  --end-exclusive YYYY-MM-DD \
  --panel observed-only \
  --terms "caller-authorized research retrieval; TWSE terms apply"
```

The script makes one official monthly request per asset/month, preserves each
response, converts ROC calendar dates to Gregorian dates, and retains official
trade volume as shares. It fails on HTML security pages, response-shape
changes, ambiguous fields, or suspected range truncation.

## Verify

- Inspect all monthly response hashes, field declarations, missing months,
  date conversion, price/volume invariants, and final CSV hashes.
- Compare the same raw sessions with `$fetch-yahoo-ohlcv`. Record freshness,
  price differences, volume agreement, and missing observations.
- Run `$package-autoquant-ohlcv` and strict intake.
- Keep `TWSE` explicit. Never claim that this route covers `TPEx`.

## Stop conditions

Record the official route as degraded when TWSE returns its security block,
throttles the caller, or omits the requested history. Do not proxy through an
unidentified mirror or silently replace it with Yahoo.
