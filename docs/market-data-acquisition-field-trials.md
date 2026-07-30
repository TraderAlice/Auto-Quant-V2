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
| `us-yahoo-v1` | U.S. split-and-dividend-adjusted Yahoo Chart → V1 aligned package → Factor Project | passed | superseded single-source development proof |
| `us-dual-source-v3` | U.S. split-adjusted daily Nasdaq.com + Yahoo → comparison → selected Yahoo V4 → Factor Project | passed with disclosed volume anomalies | same-semantics dual-source and strict intake pass; fresh-worker handoff remains |
| `cn-dual-source-v1` | XSHG/XSHE raw Tencent + Yahoo quote-history diagnostic → selected Tencent V4 → Factor Project | superseded comparison semantics | strict Tencent intake is valid, but Yahoo was later identified as split-adjusted; no raw cross-source agreement claim remains |
| `cn-dual-source-v3` | XSHG/XSHE/XBSE raw Sina + Sohu → comparison → selected Sina V4 → Factor Project | passed with disclosed XBSE volume differences | six-asset same-semantics price comparison and strict intake pass; fresh-worker handoff remains |
| `cn-eastmoney-v1` | Eastmoney observable historical K-line | degraded | five retries ended in remote connection closure; no package or coverage claim |
| `tw-dual-source-v1` | official TWSE raw + FinMind raw → exact comparison → selected FinMind V4 → Factor Project; Yahoo diagnostic | passed with authority and aggregator boundaries | official-first same-semantics overlap and strict intake pass; TPEx and fresh-worker handoff remain |
| `kr-dual-source-v1` | XKRX raw Naver + Daum → comparison → selected Daum V4 → Factor Project | passed with material volume disagreement | same-semantics price comparison and strict intake pass; KRX authority and fresh-worker handoff remain |
| `jp-dual-source-v1` | recent raw Nikkei + split-adjusted Yahoo → selected research-length Yahoo V4 → Factor Project | passed with distinct history/adjustment contracts | two routes and strict intake pass; JPX authority and fresh-worker handoff remain |
| `vn-dual-source-v1` | VNDIRECT raw + Yahoo split-adjusted → selected VNDIRECT V4 → Factor Project | passed with distinct contracts and disclosed provider anomalies | two routes and strict intake pass; venue authority and fresh-worker handoff remain |
| `xpar-dual-source-v1` | official Euronext XPAR raw + Yahoo split-adjusted → selected Euronext V4 → Factor Project | passed for named XPAR venue | two routes and strict official intake pass; other EU venues and fresh-worker handoff remain |
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
- transformation: Yahoo adjusted-close/quote-close ratio applied to already
  split-adjusted quote OHLC, producing split-and-dividend-adjusted history;
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
- the old package used the historical label `provider-adjusted`; the current
  Skill replaces that ambiguous label with
  `split-and-dividend-adjusted`;
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
- Yahoo quote-history route (later identified as split-adjusted):
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

The diagnostic exposed isolated Yahoo anomalies rather than suppressing them.
On 2024-07-05, Yahoo reported zero volume and a flat price for 600519,
601318, and 600036 while Tencent retained ordinary OHLCV; on 2024-03-29,
Yahoo volume differed materially for all five assets. Ordinary rows visually
matched over much of the bounded period, including the expected sub-100-share
difference from Tencent's lot quantization. However, the current Yahoo
semantic audit establishes that Chart quote OHLC is split-adjusted, while the
Tencent package is raw. The old comparison therefore cannot support a
same-semantics price-agreement claim. Tencent remains the valid selected raw
package for intake; the comparison is retained as historical diagnostic
evidence.

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
no XBSE symbol proof, no second proved raw route, and neither observable route
is exchange authority.

### `cn-dual-source-v3`

Sina and Sohu independently acquired the same six raw daily equities:
600519, 601318, and 600036 on XSHG; 000001 and 000858 on XSHE; and
post-migration 920019 on XBSE. Across 439 common sessions from 2024-10-11
through 2026-07-30, every open, high, low, and close value matched exactly.
Shanghai and Shenzhen volume differed by at most 64 shares and passed the
configured lot-rounding tolerance. The XBSE series retained three material
volume differences, including a maximum `1,350,001` shares, so only price
agreement is claimed.

- selected Sina package hash:
  `ec9cd6aff3442a33d880a4006f4fa2314ba77e5d8cbb831a65d6dd19f4b2d7cc`;
- independent Sohu package hash:
  `d7c30179c7231a31b7c738d66610d8e7883433fe7286ba9fcad3713a93b07b8f`;
- comparison hash:
  `eddfc66ce171cb7be2983d6f5a840518ec20f72c1614500f44af6870c031171f`;
- Project: `cn-dual-source-raw-v3`;
- request hash:
  `dffd60dc273318c956ac1860036f9dd717badbf2feab90ba57f09f715e68571f`;
- snapshot hash:
  `fed51691d6f15fbd871ecfa69c9772fa0eef99346c28a5798bb2336c9cd17d57`.

`aq validate` returned `valid: true`. Sohu converts its displayed
100-share lots to shares and checks the reported ten-thousand-CNY traded
value; both routes remain observable providers rather than exchange
authority. This supersedes the earlier “XBSE has one route” limitation.

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

The first official TWSE attempts exposed two reusable CDN constraints: the
newer `/rwd` path returned an incomplete 307 security response, and the
working official `/exchangeReport/STOCK_DAY` route was sensitive to query
parameter order and bursty access. The Skill now preserves the observed
`response=json`, `stockNo`, `date` order, defaults to a three-second delay, and
audits exact request URIs. It also records and omits rows whose official OHLC
fields are `--` rather than filling them.

The corrected route acquired 61 official raw daily observations from
2026-05-04 through 2026-07-29 for TWSE-listed 2330, 2317, 2454, 2881, and
2308. The package hash is
`7945d36dd01416de6a3f04a4b90fb1774255fa30e570bbe5a3486c184692d9bb`.
FinMind independently acquired a research-length raw panel from 2024-01-02
through 2026-07-30. Across the 61-date official overlap, every OHLC and volume
value matched exactly for all five assets:

- FinMind package hash:
  `98f8b2756737301b7ee46ccd5237b5ded3691341bf1ae58c16c463ea83023151`;
- TWSE/FinMind comparison hash:
  `5ef2c66e93719f67099b7f1e0e5319be3364ae7bd57ed82ace90a3ded3d76713`;
- selected Project: `tw-raw-v1`;
- request hash:
  `c82aadcbf25ed391deaf5c8c53e51f7a1f81a705da26e5594ba5a29fa6e2169e`;
- snapshot hash:
  `cb53ab84073d99425a908808c8ba20744b18de24a0ea2e968677027be30afc56`.

Strict intake and `aq validate` passed. FinMind remains an aggregator rather
than exchange authority. Its audit omits one explicit all-zero no-trade
placeholder for 2317 and records five dates where `Trading_money / volume`
falls outside displayed OHLC, plausibly because the money field covers a
broader trade scope. None is repaired or hidden.

Yahoo remains a third, different-semantics route. Its short overlap package
contained a flat zero-volume 2026-07-10 row for every asset; its longer
2024-2026 package was correctly rejected by strict intake for a zero-volume
row. Official TWSE is therefore first for authority, FinMind supplies the
independently executable raw research panel, and Yahoo remains a
split-adjusted diagnostic. A burst-sensitive attempt to extend official
history ended in a 307 security response and was not silently substituted.
TPEx and the fresh-worker handoff remain open.

### U.S. dual-source development comparison

Nasdaq.com and Yahoo both returned split-adjusted daily AAPL, MSFT, NVDA, QQQ,
and SPY history from 2024-01-02 through 2026-07-29. Four assets had 645 observations
from each source. Nasdaq omitted one unusable SPY row containing display
`N/A`, leaving 644 SPY observations; the Skill retained the raw response and
counted the complete-row omission rather than coercing volume to zero.

- Nasdaq package hash:
  `7d90e35144b3821f5524898f303d7008598cdde4f63b18c6dbffa4be1aad4342`;
- Yahoo package hash:
  `28e13d5c6ca707789079608de078a9d280efbe24d2b1bcaa0fc673ac9c80bb02`;
- comparison audit hash:
  `6bf597d88a3afed357c2d00488618ccb4c2714a9b64eb0f1ab16ec1d6d5c87e9`;
- 644 dates were common to the full five-asset panel;
- every split-adjusted OHLC comparison passed the configured price tolerance;
- median volume ratios were exactly `1.0`, but isolated volume differences
  remained, including a suspicious Nasdaq SPY value of `9,999,999` on
  2026-04-17 versus Yahoo `70,661,900`.

Yahoo is the selected package for this sample because its panel is complete
and Nasdaq contains the disclosed placeholder-like volume. Strict intake
created Project `us-dual-source-split-v3` with request hash
`68ea6ecd8f18cbd2e4a23c238b30ec92b65624e9a0b1e247789d59e9135ed2a6`
and snapshot hash
`1724d188aadc34061db37da522aa4013b649fd07f44cc1d5246be6f015a02ec8`;
`aq validate` returned `valid: true` with no diagnostics. U.S. coverage still
needs the required fresh-worker handoff.

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
and audits removed rows. The later semantic correction also establishes that
Yahoo quote OHLC is split-adjusted, so the prior Naver/Yahoo artifact is a
cross-route diagnostic rather than a same-semantics comparison.

Daum then supplied the second raw route. Naver and Daum covered 382 common
sessions for all five assets from 2025-01-02 through 2026-07-29, with every
OHLC value matching exactly. Daum also supplied the 2026-07-30 session.
Reported volume differed on most dates and materially on isolated sessions,
so the accepted claim is raw price consistency, not volume equivalence.

- Daum package hash:
  `42e9a8a50ae054ee8afac7123bbce5114da9e361bacb42c790979f9b524d6346`;
- Naver/Daum comparison hash:
  `7f0303f7fdd31c5280659d4ebbf2db69d4451bc32628ff66f7d878569088c495`;
- Project: `kr-dual-source-raw-v1`;
- request hash:
  `ba7b6dd55ea194b4327223eb574f8fd6bf38751e9cad1956e8307fc4ec98f1b1`;
- snapshot hash:
  `39e7aa508e8e6323b6b4e5e8d55d7c3875c1bd5445c068f33aa5664f6892c210`.

Daum was selected because its accumulated traded value permits a per-row
consistency check. Strict intake and `aq validate` passed. Neither raw route
is KRX authority, and the fresh-worker handoff remains open.

### Vietnam dual-route development evidence

VNDIRECT acquired VCB, VNM, FPT, HPG, and VIC across named HOSE listings from
2025-01-02 through 2026-07-29. Its raw route converts the provider's
thousand-VND price unit to VND, preserves `nmVolume` as shares, and checks the
reported `nmValue / nmVolume` scale. One VNM row had internally contradictory
OHLC bounds; the Skill retained it in the provider audit and excluded it from
the package without repair. The VNDIRECT raw package hash is
`5ed799a5754a502c5dc8dfb77587c0b2a062fb362627c37f51bff765897bfaa0`.

Yahoo independently acquired the same named assets and exposed additional
flat zero-volume rows. Its corrected package is split-adjusted, with hash
`d1e81eaa85726c626880a13cd552d5cd92bf8dc2207062ceed180d7b23b719ed`.
The large historical price differences are expected from unlike corporate
action contracts and do not support a price-equivalence claim. Vietnam now
has two executable provider routes. The VNDIRECT package was strictly bound
to Project `vn-raw-v1`; request hash
`98de9755c38895195a204cff823c22083e79b12bda3fb7498b99716e91cf1b39`,
snapshot hash
`596da6b3413b286eb838eaca97d37a5896992a3bcdebccfa011d3ffef2d7a32c`,
and `aq validate` returned `valid: true`. A venue-authoritative route or an
explicit provider-only acceptance decision, plus the fresh-worker handoff,
remain open.

### Japan dual-route development evidence

Nikkei's displayed one-month history independently acquired raw daily OHLCV
for 7203, 6758, 9984, 8306, and 6861 from 2026-07-01 through 2026-07-30.
Yahoo acquired the same recent sample with a split-adjusted contract. Every
recent close and volume value happened to match, but unlike adjustment
contracts are not promoted to semantic equivalence.

- Nikkei recent raw package hash:
  `0d7136dc1f82aa6a03c4bbb018a95641399b7e6d140f207401f22c94b50451aa`;
- Yahoo research-length split-adjusted package hash:
  `110c1aae3f65e4af9687d8e4e181df9c5ee56a6d54f2146649d9e7dc7e015a91`;
- selected Project: `jp-split-v1`;
- request hash:
  `7f560bfdcc586705b3c5b3e7715c83fe8bbede626f78236a61e2c460387141f0`;
- snapshot hash:
  `d31862f6c2e116fac8aa9ebe12c8ee0d0d3a58f2c666338d4169f68663ff1040`.

Nikkei is useful as a recent independent freshness route but deliberately too
short for Factor intake. Yahoo's 2024-01-04 through 2026-07-30 panel was
therefore selected for strict intake, which passed validation. Neither route
is JPX authority. Credentialed J-Quants remains a documented future
authoritative option, and the fresh-worker handoff remains open.

### Euronext Paris dual-route development evidence

Official Euronext Live acquired raw daily XPAR history for MC, TTE, SAN, SU,
and AI from 2025-01-02 through 2026-07-29. Yahoo independently acquired the
same named assets under its split-adjusted contract. The two sources prove
route plurality but are not numerically compared as equivalent.

- official Euronext package hash:
  `aeb75b386fdd455a10c368e84d2bed45da20ee3f3cbe25c3924d398558f581e0`;
- Yahoo package hash:
  `ccdbf375c07b83d796e284a33420a30d93a2d3c4a487f2356d6faae4b1fc0dda`;
- selected Project: `xpar-official-raw-v1`;
- request hash:
  `74f10ba5d7186970278aa4e8e523a4fc5fc88bbc6cbf143fbd6e71afaf87c347`;
- snapshot hash:
  `5aa4dc9b409d5556557e7173decdc5f0165ae30b7e3ddee6ffe3d07e6437fea2`.

The official raw package passed strict intake and `aq validate`. This proves
only the explicitly named XPAR venue; “EU equities” is not treated as one
calendar, venue, or data contract. Other named European venues and the
fresh-worker handoff remain open.

### Binance executable smoke

The Binance provider Skill acquired 24 exact continuous UTC hourly closes for
BTCUSDT and ETHUSDT from 2026-07-29T12:00Z through 2026-07-30T11:00Z. The V2
package hash is
`3a6fe25a9129a3dbbe10960378ca85a9086e6777f2c68f16834f9a844d740158`;
the package audit confirmed a 3,600-second grid, no missing rows, and no
zero-volume observations.
