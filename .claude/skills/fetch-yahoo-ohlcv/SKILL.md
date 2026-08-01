---
name: fetch-yahoo-ohlcv
description: Acquire bounded completed daily OHLCV from Yahoo Finance Chart, preserve raw JSON and metadata, select explicit split-adjusted or split-and-dividend-adjusted semantics, and emit an auditable AutoQuant staging package. Use when the market router selects Yahoo as one broad historical source or when comparing Yahoo against a venue-authoritative provider.
---

# Fetch Yahoo OHLCV

Use Yahoo as one broad, delayed, unauthenticated provider route. Do not treat
successful Chart output as official venue, calendar, adjustment, or
redistribution authority.

## Prepare

1. Read `$acquire-market-ohlcv` and its relevant market reference first.
2. Create an asset file as described in
   [assets-format.md](references/assets-format.md).
3. Choose an end-exclusive date that excludes forming bars.
4. Obtain and preserve the applicable terms/access understanding. Pass it
   explicitly; the script does not invent a legal claim.

## Fetch

Run:

```bash
python3 scripts/fetch_yahoo_daily.py \
  --output <workspace>/staging/market-data/<dataset-id> \
  --assets /absolute/path/assets.json \
  --dataset-id <dataset-id> \
  --start YYYY-MM-DD \
  --end-exclusive YYYY-MM-DD \
  --calendar XNYS \
  --timezone America/New_York \
  --adjustment split-and-dividend-adjusted \
  --panel aligned \
  --terms "caller-authorized research retrieval; Yahoo terms apply"
```

Use the Skill's absolute `scripts/fetch_yahoo_daily.py` path when running from
outside this folder. The output directory must be absent or empty.

Yahoo's `period1`/`period2` behavior is not trusted as the final session-date
boundary outside U.S. timezones. The script always applies the requested
Gregorian `[start, end-exclusive)` filter again after parsing and records any
out-of-range rows it removed.

Session dates are derived only after converting each timestamp to Yahoo's
returned `exchangeTimezoneName`; UTC calendar dates are not treated as local
session dates.

Choose `--panel observed-only` only for a compatible Factor-only V4 intake.
Choose `--adjustment split-adjusted` to preserve Yahoo's historical quote
OHLC. These are not exchange-unadjusted prices: Yahoo back-adjusts historical
quotes for split-like corporate actions. For
`split-and-dividend-adjusted`, the script additionally multiplies every OHLC
field by `adjusted_close / raw_close` and leaves provider volume unchanged.

The default `--invalid-ohlc-policy reject` fails closed if Yahoo returns a row
whose high/low cannot contain its open and close. For price-only research, the
caller may explicitly authorize `--invalid-ohlc-policy drop-observation` when
an isolated provider rounding defect is preferable to abandoning the complete
task panel. That policy never clamps or repairs a price. It retains the raw
JSON and the exact removed date/OHLCV in `provider-audit.json`, and aborts when
the anomaly count exceeds the ceiling of 0.1% of normalized source rows, with
a minimum allowance of one isolated row and a maximum of 10 per asset. With an
aligned panel, inspect the final `outputRows`: removing one asset-date also
removes that date from the common panel for every asset.
The command result and top-level `provider-audit.json.invalidOhlc` projection
summarize every affected canonical asset and removed observation. Use that
projection before drilling into the matching per-asset records; an aligned
panel can lose one shared date even when more than one asset had an invalid
observation on that date.

The separate default `--transient-scale-policy reject` also fails closed when
the provider emits a short one-to-three-row price-scale island: a fivefold or
larger entry jump, the opposite fivefold or larger exit jump, and recovery
within 25% below or one-third above the pre-island close. This catches bounded
temporary decimal/unit discontinuities without pretending that every large
return is bad data. When raw provider evidence and the research contract make
observation removal preferable, explicitly pass
`--transient-scale-policy drop-observation`. It never rescales prices. It
retains every original row in raw JSON and exact OHLCV plus boundary ratios in
top-level `provider-audit.json.transientScale` and the per-asset audit, and it
uses the same 0.1%-of-source, minimum-one, maximum-10 bound per asset. A
persistent split or regime change that does not quickly reverse is not removed
by this policy and still requires separate provider/corporate-action evidence.

## Verify

- Inspect `provider-audit.json`, every raw JSON hash, every CSV hash, returned
  instrument metadata, source/normalized ranges, dropped rows, and alignment.
- If `drop-observation` was selected, disclose why it was authorized and cite
  every item in top-level `invalidOhlc.observations`, then reconcile it with
  the per-asset `invalidOhlcBoundsObservations`; do not describe the resulting
  panel as repaired provider history.
- If transient-scale removal was selected, disclose every item in top-level
  `transientScale.observations`, the entry/exit/recovery ratios, why the route
  was accepted, and the common-panel dates lost. Never describe removal as a
  verified split adjustment or silently replace it with rescaled prices.
- Spot-check provider symbols and venue identity outside the Chart response.
- Compare a bounded overlap against the market's second source.
- Invoke `$package-autoquant-ohlcv`; do not move generated CSVs directly into
  a Project.

## Stop conditions

Stop rather than silently changing the task when Yahoo lacks the requested
history, interval, symbol, adjusted close, completed bar, or credible venue
mapping. Record rate limiting, response errors, or freshness gaps as provider
evidence.
