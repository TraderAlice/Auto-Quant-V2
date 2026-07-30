# Market-data acquisition Skill field trials

Status: active development evidence.

Related: [[plans/market-data-acquisition-skills]],
[[docs/design/research-intake-and-dataset-snapshots]], and
[[docs/design/workspace-project-boundaries]].

## Evidence rule

A successful network request is not accepted market coverage. A coverage row
requires the two-source, market-semantic, packaging, strict-intake, and
fresh-worker evidence defined by [[plans/market-data-acquisition-skills]].
Development trials remain visible because they expose reusable Skill and Core
friction, but they do not silently satisfy that gate.

## Development trials

| Trial | Route | Result | Coverage authority |
| --- | --- | --- | --- |
| `us-yahoo-v1` | U.S. daily Yahoo Chart → V1 aligned package → Factor Project | passed | development-only; no independent second source or fresh worker |
| `cn-dual-source-v1` | XSHG/XSHE raw daily Tencent + Yahoo comparison → selected Tencent V4 → Factor Project | passed with disclosed provider anomalies | development-only; two sources and strict intake pass, but no fresh worker or XBSE proof |
| `cn-eastmoney-v1` | Eastmoney observable historical K-line | degraded | five retries ended in remote connection closure; no package or coverage claim |
| `tw-yahoo-v1` | TWSE-listed raw daily Yahoo → V4 package | passed | development-only; official route unavailable from this host |
| `tw-twse-v1` | official TWSE monthly historical report | degraded | five retries returned a 307 security response without a usable redirect |
| `us-nasdaq-v1` | U.S. raw daily Nasdaq.com + Yahoo comparison | passed with one missing Nasdaq SPY row and disclosed volume anomalies | development-only; no raw dual-source strict intake or fresh worker |
| `kr-naver-v1` | XKRX raw daily Naver + Yahoo comparison | passed with disclosed isolated differences | development-only; no strict intake, KRX authority, or fresh worker |
| `crypto-binance-v1` | Binance Spot exact closed UTC hourly V2 package | passed | executable provider-Skill smoke; crypto is outside the first equity coverage matrix |

### `us-yahoo-v1`

Date: 2026-07-30.

Purpose: prove that Skills materialized by a newly initialized Workspace can
produce and strictly bind one real daily panel without accessing the AutoQuant
source tree during acquisition.

Input and execution:

- Workspace:
  `/Users/ame/2607AutoQuant/market-data-field-trials/us-yahoo-v1/desk`;
- materialized Skill bundle:
  `a1da64d709cee97b88e2bd7e306ed6e729afb394faff9e52b66ba23c8a20d413`;
- Harness version reported by the candidate Workspace: `0.8.30`;
- provider route: `fetch-yahoo-ohlcv`;
- assets: AAPL, MSFT, NVDA, QQQ, and SPY;
- requested interval/window: completed daily observations, 2024-01-01 through
  the 2026-07-30 end-exclusive boundary;
- transformation: Yahoo adjusted-close/raw-close ratio applied to OHLC;
  provider volume unchanged;
- panel: exact common observed dates.

Evidence:

- original provider retrieval time:
  `2026-07-30T12:11:39+00:00`;
- normalized rows: 645 per asset, 2024-01-02 through 2026-07-29;
- zero-volume rows: zero in every normalized asset;
- dataset package hash:
  `78032c28f8c14256565260ade5c2616e61e915f7ac34eff57e91a7118aa15790`;
- strict request hash:
  `95a6f2478d7ab6c2368755732f62b081e879244d5141332a764218024ac6c6c0`;
- Project snapshot hash:
  `2be2639a2fc946c06867c879be40fb0703fec0d80a2814dd93a7cc4e44ff134e`;
- Project: `us-yahoo-skill-v1`;
- `aq validate` returned `valid: true` with no diagnostics.

The provider audit preserves each raw JSON and normalized CSV hash. The
separate package audit re-derived 645 union and intersection timestamps and
basic OHLCV invariants before intake.

Observed friction and disposition:

- the host had `python3` but no `python` command; every bundled executable
  example now uses `python3`;
- this was a framework-developer execution, not an isolated fresh-worker
  trial;
- Yahoo remains one broad delayed external provider and does not authenticate
  venue or adjustment claims;
- no second provider was compared, so U.S. coverage remains unaccepted.

### `cn-dual-source-v1`

Date: 2026-07-30.

Purpose: prove that source plurality changes route choice rather than merely
duplicating downloads.

Routes and evidence:

- Tencent raw daily route:
  `fetch-tencent-ohlcv`;
- Yahoo raw daily route:
  `fetch-yahoo-ohlcv`;
- assets: 600519, 601318, and 600036 on XSHG; 000001 and 000858
  on XSHE;
- both routes returned the same 622 session dates from 2024-01-02 through
  2026-07-29 for all five assets;
- Tencent converted observed provider lots to shares by the explicit
  multiplier 100; per-asset median Tencent/Yahoo share-volume ratios ranged
  from `0.9999997559` to `1.0000001442`;
- Tencent package hash:
  `4f103dd066f0b6abf2b8fdecb75a342ec8d88be8269e46fd6ed8246496054d2e`;
- Yahoo package hash:
  `3bed6aa244d5ae881951803a908590387b0e24185aa474ea8987604756a639f2`;
- comparison audit hash:
  `e909d3102788876772460503129e319b96c4633f203e6f53c6d22269f3448fff`.

The comparison exposed isolated Yahoo anomalies rather than suppressing them.
On 2024-07-05, Yahoo reported zero volume and a flat price for 600519,
601318, and 600036 while Tencent retained ordinary OHLCV; on 2024-03-29,
Yahoo volume differed materially for all five assets. Ordinary rows otherwise
matched to provider rounding, including the expected sub-100-share difference
from Tencent's lot quantization. Tencent was therefore selected for intake.

Strict intake evidence:

- materialized candidate Skill bundle:
  `2b8541fa871238ead003f66f78ef51ee0ccc7a42bf35d1604d076ab342bfd0d2`;
- Project: `cn-dual-source-raw-v1`;
- request hash:
  `3717618588a291acd8a24cbe7a7339deca2893ad789d34bb765c229240c0d619`;
- snapshot hash:
  `b0142c5d822e56dcb7444d883a49a2504f7eb86cb4ba5410d7026942de139b2d`;
- `aq validate` returned `valid: true` with no diagnostics.

This is not yet accepted mainland-China coverage. It has no isolated worker,
no XBSE symbol proof, and neither observable route is exchange authority.

### Degraded Eastmoney route

At 2026-07-30 20:21 Asia/Shanghai, the checked-in Eastmoney script attempted
the named five-asset XSHG/XSHE raw request. All five bounded retries for the
first asset ended in `RemoteDisconnected: Remote end closed connection
without response`. No package was created, no alternate endpoint was silently
selected, and the route remains visible as degraded provider-access evidence.

The deterministic parser test still proves that an accepted Eastmoney
response must convert `f56` lots to shares and validate that conversion using
`f57 amount / shares` inside the reported daily low/high range.

### Taiwan development evidence

At 2026-07-30 20:32 Asia/Shanghai, the official TWSE monthly Skill attempted
one completed July 2026 request for 2330. All five retries received the
official host's `307 Temporary Redirect` security response without a usable
`Location`; direct OpenAPI requests from the same host returned an HTML
security block. The Skill stopped without switching providers.

Independently, Yahoo returned 379 common raw daily observations from
2025-01-02 through 2026-07-29 for TWSE-listed 2330, 2317, 2454, 2881, and
1301. Its package hash is
`d86cdc0e04554eb77dcd6a80dc94ef066706bd36b934bbc3ae31bc410d94e959`.
This confirms one broad route only. Taiwan remains unaccepted until the
official route succeeds in a permitted network context, the two packages are
compared, strict intake passes, and a fresh worker completes the handoff.

### U.S. dual-source development comparison

Nasdaq.com and Yahoo both returned raw daily AAPL, MSFT, NVDA, QQQ, and SPY
history from 2024-01-02 through 2026-07-29. Four assets had 645 observations
from each source. Nasdaq omitted one unusable SPY row containing display
`N/A`, leaving 644 SPY observations; the Skill retained the raw response and
counted the complete-row omission rather than coercing volume to zero.

- Nasdaq package hash:
  `de0e908cc47460afdb368e60bbd91737e1a250cdedeb61a7d19bba9ac9c9403a`;
- Yahoo raw package hash:
  `19101f410fb19d400f15346987601fa7af0ca5bef8b2fc7c96f5958d96b4de95`;
- comparison audit hash:
  `72f6d56d269f466258cdc93b7125ab63c34e39cfbdb43d4ed530b4375dabcd3a`;
- 644 dates were common to the full five-asset panel;
- every raw OHLC comparison passed the configured price tolerance;
- median volume ratios were exactly `1.0`, but isolated volume differences
  remained, including a suspicious Nasdaq SPY value of `9,999,999` on
  2026-04-17 versus Yahoo `70,661,900`.

Yahoo is the current preferred package for this sample because its panel is
complete and Nasdaq contains the disclosed placeholder-like volume. This is
not yet accepted U.S. coverage because the selected raw package has not gone
through the dual-source request/intake handoff with a fresh worker.

### South Korea dual-source development comparison

Naver Finance and Yahoo were compared for 005930, 000660, 005380, 035420, and
035720. After the Yahoo Skill's explicit session-date boundary fix:

- Naver returned 382 raw observations per asset from 2025-01-02 through
  2026-07-29;
- Yahoo returned 381 per asset over the same visible endpoints;
- the five-asset common panel contained 381 dates;
- ordinary price and share-volume rows agreed, while each asset retained one
  material volume difference and a small number of isolated price
  discrepancies;
- Naver package hash:
  `c7c8ce1c61d403be34e5390119e50025c52c1c973109fb5ecfd9959a3254e79d`;
- Yahoo package hash:
  `f89403dbdd33a5e0a864e248036fa986e995d64bef187edb22e8b57f52cdac1a`;
- comparison hash:
  `104168b165b174db66b271206de08f0731989dc1ced83eec89d7b1f1f3915404`.

The first Yahoo attempt exposed that provider `period2` is not sufficient to
enforce a non-U.S. session-date end boundary. The reusable Yahoo Skill now
applies the requested Gregorian `[start, end-exclusive)` filter after parsing
and audits removed rows. South Korea remains unaccepted until the route choice
is independently reviewed, strictly ingested, and handed off by a fresh
worker; neither source is KRX authority.

### Binance executable smoke

The Binance provider Skill acquired 24 exact continuous UTC hourly closes for
BTCUSDT and ETHUSDT from 2026-07-29T12:00Z through 2026-07-30T11:00Z. The V2
package hash is
`3a6fe25a9129a3dbbe10960378ca85a9086e6777f2c68f16834f9a844d740158`;
the package audit confirmed a 3,600-second grid, no missing rows, and no
zero-volume observations.
