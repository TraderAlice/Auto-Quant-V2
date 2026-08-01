# AutoQuant OHLCV package selection

| Version | Use |
| --- | --- |
| V1 | Common aligned daily session observations for fixed or multi-lane research |
| V2 | Complete continuous UTC 1h bars with declared derived intervals |
| V3 | Configurable continuous or calendar-verified XNYS intraday base |
| V4 | Ragged observed-only daily Factor panel; never fixed Portfolio/RL |
| V5 | Close-time-aware observed base-bar Factor panel through `1d` |

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

A provider's timestamp may label bucket start rather than completed bar close.
That provider Skill must preserve the raw label and prove an exact calendar
mapping before it emits V3. Packaging never fixes labels by adding one nominal
duration blindly: XNYS's terminal bucket may be shorter, and a provider close
marker may not be the missing bucket's OHLCV.

Never select a richer version simply because it accepts more fields.

## Required V5 cross-market checks

- Preserve an exact timezone-aware completed close timestamp for every row,
  including daily rows; a civil date is insufficient authority.
- Disclose how date-only provider data was mapped to exchange close instants.
- Keep later same-date market closes unavailable to an earlier target close.
- Preserve absent rows without fill; candidate code owns any explicit backward
  as-of use of already completed context.
