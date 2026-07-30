# AutoQuant OHLCV package selection

| Version | Use |
| --- | --- |
| V1 | Common aligned daily session observations for fixed or multi-lane research |
| V2 | Complete continuous UTC 1h bars with declared derived intervals |
| V3 | Configurable continuous or calendar-verified XNYS intraday base |
| V4 | Ragged observed-only daily Factor panel; never fixed Portfolio/RL |
| V5 | Observed-only intraday mixed-class Factor panel |

## Required daily checks

- Conventional date/open/high/low/close/volume columns.
- Parseable ordered unique dates.
- Nonnegative volume and consistent OHLC bounds.
- Exact per-asset observed range and row count.
- Union/intersection coverage and missing-observation policy.
- Explicit market, calendar, timezone, venue, currency, and asset class.
- Explicit raw/split/dividend/provider adjustment claim.

## Required intraday checks

Additionally prove timezone-aware bar-close timestamps, base-grid
completeness or observed-only authority, session boundaries, DST/early-close
behavior where applicable, terminal partial-bucket policy, and causal
completed aggregation.

Never select a richer version simply because it accepts more fields.
