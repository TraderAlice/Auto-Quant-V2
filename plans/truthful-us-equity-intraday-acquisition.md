# Truthful U.S. equity intraday acquisition

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.20`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/configurable-session-interval-inputs]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/agent-employability-validation]].

## Outcome

Let a fresh quantitative coworker turn a caller-fixed U.S.-listed equity or
ETF `1h` request into either:

1. one auditable, exact XNYS V3 package whose provider bucket labels have been
   converted to canonical completed bar-close timestamps and whose complete
   regular sessions pass the same Core contract used by Factor, Portfolio, and
   governed RL; or
2. one durable machine-readable provider-gap result that identifies the exact
   unavailable range, null/zero/noncanonical observations, and incomplete
   sessions without creating false dataset authority.

The installed Skill must own provider-specific acquisition and normalization.
Core remains provider-neutral, and neither path may silently fill bars, drop
sessions, narrow the request, change interval, or relabel observed-only data as
an aligned V3 panel.

## Baseline evidence

A fresh coworker using only the released `0.9.19` wheel received a fixed
two-year hourly reversal question over `SPY`, `QQQ`, `IWM`, `TLT`, and `GLD`.
It correctly created an `ohlcv-research-desk`, wrote the English research
brief, inspected public Skills, and stopped before Factor/Portfolio execution.
The installed U.S. routes exposed only Yahoo and Nasdaq daily scripts; the only
hourly script was continuous Binance Spot. The worker left no task intake,
Run, Session, Report, or Dossier and recorded need `FN-001` plus structured
route evidence.

Authoritative baseline:

- Grok session `255af841-8e51-41bf-80c2-385d503c26d1`;
- field root `/Users/ame/autoquant-v0919-multiinterval-baseline`;
- Project `hourly-reversal-desk` under `desk/workspace`;
- exact fixed window `2024-08-01` through `2026-07-31` on XNYS regular
  sessions, with `1h` base and completed prior-session `1d` context;
- zero task-owned data snapshots and zero quantitative evidence objects.

Independent live probes then established the provider boundary rather than
assuming Yahoo coverage:

- Yahoo Chart accepted `interval=1h` only when the request began within the
  trailing 730 days and returned HTTP 422 outside that window;
- Yahoo timestamps label provider bucket starts, while AutoQuant V3 requires
  canonical completed bar closes, including the short terminal bucket at the
  scheduled XNYS close;
- the fixed SPY response contained 3,498 timestamp slots versus 3,492 expected
  XNYS bars across 501 sessions, but only 3,475 non-zero valid quote rows;
- early-close terminal buckets appeared as null rows plus a zero-volume
  session-wide close marker, not valid final half-hour OHLCV;
- ordinary-session null gaps also occurred, and narrow-window refetches
  reproduced them;
- the same fixed five-ETF panel had incomplete sessions for every asset, so it
  cannot truthfully become aligned V3 authority;
- a separately bounded April 2026 five-ETF window had complete provider bars
  and is suitable for proving the successful path without weakening the
  original negative case.

## Public contract

Extend `$fetch-yahoo-ohlcv` with an explicit intraday procedure rather than
turning acquisition into an `aq` Core downloader. The public script must:

- accept a bounded asset list, `[start, end-exclusive)` session-date request,
  XNYS/America-New_York authority, `1h`, split-adjusted semantics, caller terms,
  and an explicit aligned-panel contract;
- calculate and disclose Yahoo's current 730-day eligibility before retrieval,
  while treating the provider response as final authority;
- preserve exact raw JSON, response metadata, split/dividend events, request
  parameters, retrieval time, hashes, and per-asset transformation audit;
- filter response rows back to the caller's local session-date boundary;
- reject extended-hours, current-price marker, null, impossible OHLC, negative
  volume, duplicate, off-grid, missing, or extra observations;
- map provider bucket starts to the exact XNYS regular-session closes defined
  by the pinned calendar, including DST, early close, and the terminal partial
  bucket, without modifying OHLCV values;
- emit schema V3 with `baseInterval: 1h`, caller-declared higher feature
  intervals, canonical XNYS aggregation fields, and one aligned timestamp panel
  only after every asset is complete;
- on an unavailable or incomplete request, retain a structured failed-route
  audit and no `dataset-package.json`, then return nonzero;
- support only split-adjusted intraday price meaning because Yahoo does not
  expose intraday adjusted close. Provider-reported volume remains unchanged.

The market router and packaging Skill must route an Agent to this procedure,
explain the successful and failed artifacts, and state that Nasdaq remains a
daily peer rather than pretending it independently verifies historical hourly
bars.

## Scope

### In scope

- One narrow Yahoo Chart `1h` XNYS equity/ETF acquisition procedure.
- Exact provider-start to canonical-bar-close transformation and strict
  session/panel validation.
- Successful V3 package output and durable failed-route output.
- Public Skill/router/package guidance, capability-adjacent documentation, and
  installed Workspace Skill materialization.
- Deterministic payload/calendar tests, bounded live provider smoke, and fresh
  installed-wheel Grok trials for both the fixed negative panel and one
  predeclared complete bounded panel.

### Out of scope

- A central Core downloader, shared data inventory, automatic cache reuse, or
  automatic research-question narrowing.
- Reconstructing missing Yahoo bars, forward filling, deleting incomplete
  sessions, or weakening V3's exact-session contract.
- Claiming an independent historical hourly peer route when none is bundled.
- Credentialed Alpha Vantage, Alpaca, Polygon, or another paid/authenticated
  provider; that requires separate demand-led evidence and a later plan.
- Yahoo intervals below `1h`, continuous/extended-hours input, non-XNYS
  calendars, dividend-adjusted intraday OHLC, or V5 observed-only fallback.
- Orders, TPSL, live trading, OpenAlice pin changes, or migration promises.

## Acceptance

- [x] Public installed Skills lead a fresh Agent from a U.S. `1h` need to the
      exact Yahoo intraday procedure without implementation-source inspection.
- [x] A deterministic complete regular/early-close fixture maps provider bucket
      starts to all expected canonical V3 closes and emits an auditable package
      accepted by `aq study create --request --dataset`.
- [x] The package derives requested completed `1d` context through existing
      Core aggregation and executes a bounded Factor Run without lookahead.
- [x] Null rows, zero-volume close markers, missing terminal buckets, ordinary
      intraday gaps, off-session rows, duplicate starts, wrong metadata, and
      requests outside the provider range each fail closed with exact durable
      evidence and no package.
- [x] Multi-asset aligned output requires identical complete canonical panels;
      one deficient asset prevents authority for the whole fixed request.
- [x] The unchanged two-year five-ETF baseline is replayed from an installed
      candidate and produces a truthful structured provider blocker with no
      quantitative Run rather than a substituted question.
- [x] A second fresh worker receives a predeclared complete bounded five-ETF
      question, acquires and intakes live `1h` data, and produces immutable
      Factor evidence plus an honest downstream admission decision.
- [x] CLI validation, Orientation, inspect/Report/Studio projections remain
      consistent for the successful trial; the failed acquisition remains
      staging evidence and never appears as quantitative authority.
- [ ] Focused/full tests, documentation links, syntax/lock, build/install,
      root Workspace, installed capability, and clean-clone smokes pass before
      publication.

## Work

- [x] Reproduce the `0.9.19` zero-data coworker gap and preserve its terminal
      handoff, files, and transcript.
- [x] Probe Yahoo's current `1h` range, timestamp, adjustment, early-close,
      null, zero-volume, and multi-asset completeness behavior independently.
- [x] Implement the transactional intraday acquisition and exact failure audit.
- [x] Update router/package Skills, durable design docs, Agent guidance, and
      deterministic tests; re-materialize the checked-in Workspace bundle.
- [x] Build an isolated `0.9.20` candidate and run both fresh-worker field
      trials without source access or prior-trial knowledge.
- [ ] Audit exact evidence, complete all release gates, publish `v0.9.20`, and
      leave OpenAlice independently pinned to `v0.8.31`.

## Findings and decisions

- 2026-08-01 — The original blocker is acquisition coverage, not the V3
  interval surface. Existing Core already verifies XNYS sessions, derives
  completed daily context, and exposes ordinary pandas multi-interval columns.
- 2026-08-01 — Yahoo's historical `1h` response is useful provider evidence
  but is not inherently a valid XNYS panel. Package creation must be a result
  of validation, never an assumption derived from HTTP success.
- 2026-08-01 — The source timestamp cannot be copied into V3. It labels a
  provider bucket start; the normalized timestamp is the matching scheduled
  bucket close, and this semantic transformation must be visible in the audit.
- 2026-08-01 — A zero-volume session-close marker on an early close contains
  session-wide-looking OHLC and cannot be relabelled as the missing final
  half-hour. Reconstruction is scientifically unsupported and remains refused.
- 2026-08-01 — An honest negative provider trial and a successful bounded
  acquisition trial prove different things; both are required before release.
- 2026-08-01 — A first successful April probe exposed zero volume in every
  asset's first bucket when `period1` equalled the first session open. Moving
  the provider query start one hour earlier restored the exact first-bucket
  volume while leaving normalized coverage unchanged. The warmup is therefore
  mandatory and consumes one hour of the 730-day provider window.
- 2026-08-01 — The first installed `0.9.20` candidate was not release-ready.
  Fresh Grok session `019fbd8f-76e6-76f2-a7d6-ff4b7af75bd5` acquired an exact
  287-row, 41-session, five-ETF package, but Pandas 3.0.5 parsed its ISO CSV
  timestamps as `datetime64[us, UTC]` while the pinned XNYS calendar exposed
  `datetime64[ns, UTC]`. `DatetimeIndex.equals` treated the storage unit as
  data even though ordered instants, missing bars, and extra bars were exactly
  identical. Intake therefore reported the false `interval.session-panel`
  blocker.
- 2026-08-01 — The coworker independently isolated the false failure and
  eventually completed the research by re-encoding both source and
  materialized timestamps plus their content locks. That trial is valuable
  defect and employability evidence, but its Run, Report, Dossier, and negative
  Factor conclusion are not release acceptance: the workaround forced the
  worker to repair Harness-owned dataset bytes and hashes outside the intended
  one-command public path. A clean candidate and fresh worker must replay the
  unchanged question without that workaround.
- 2026-08-01 — Core timestamp identity now normalizes both indexes to
  nanosecond storage before exact ordered comparison. This preserves the
  strict calendar contract while making an in-memory Pandas unit irrelevant.
  The same normalization protects continuous-grid and materialized-feature
  reconciliation plus the Binance producer's exact-grid audit. A direct
  microsecond-resolution XNYS regression and the existing full research-desk
  XNYS Intake/Run path pass from source; an installed Pandas 3 replay remains
  a required candidate gate.
- 2026-08-01 — The second installed candidate proved that repair in a clean
  Pandas 3.0.5 environment and fresh Grok session
  `019fbda4-3aa8-71d2-a24a-9a14cc8ddfd3`: the original Skill CSV intook
  directly, and the worker completed acquisition, one Factor Run, Report,
  Dossier, and terminal handoff in 6m58s without Harness repair. Independent
  semantic audit nevertheless rejected the research artifact because
  `plain.where(daily > 0, other=0)` converted unavailable five-session daily
  warm-up state into a zero factor. Artifact coverage was therefore 100%
  while the required daily component was available for only 85.7% of each
  asset. Validation IC happened to be unchanged because the defect fell in
  train, but accidental metric invariance is not contract compliance.
- 2026-08-01 — The Factor program now states the reusable rule explicitly:
  missing required input is neither an observed false regime nor a neutral
  score; gated candidates must restore `NaN` for unavailable predicates and
  reconcile candidate coverage against required-component coverage. The
  second trial remains negative employability evidence, not release proof; a
  third clean worker must implement the unchanged question from the revised
  public program.
- 2026-08-01 — The third installed candidate closed both defects without
  coaching. Fresh Grok session `019fbdae-2611-7870-b313-2c3e0a97d5a7`
  received only candidate wheel
  `c27999af29517c5829b206052013bef6431a4053150f0fb8968d8ef796a7785a`,
  public CLI/Skills, one assignment, network access, and zero initial data. In
  Python 3.11 with Pandas 3.0.5 it created exactly one Project, acquired and
  intook the original 287-row-per-asset hourly panel plus 41 completed daily
  bars, and executed exactly one fixed Factor Run without changing Harness or
  materialized dataset bytes.
- 2026-08-01 — The clean candidate preserved unavailable gate state as `NaN`.
  Final-factor coverage was exactly `0.8571428571` for every ETF, identical to
  the required completed-daily component, with no finite/missing mismatch.
  Run `run-20260801T141917043136Z-de42b2037d16` reported validation primary
  rank IC `-0.08449258433998387` versus plain reversal
  `-0.1584905660377358`. The gate mitigated a harmful score but did not create
  positive edge; the worker correctly published one Factor Report and one
  Factor-only Dossier while refusing Portfolio and RL.
- 2026-08-01 — Independent replay reconstructed the combined purged validation
  target from frozen closes and reproduced all 53 cross-sectional observations
  and the reported candidate IC with zero residual. Prefix recomputation at
  three assignment-fixed cuts (`2026-04-30T17:30Z`,
  `2026-05-14T19:30Z`, and `2026-05-29T19:30Z`) reproduced 720, 1,080, and
  1,430 candidate rows exactly, establishing that neither the hourly score nor
  completed-daily gate depends on future input.

## Verification

Candidate and field verification complete:

- deterministic intraday, Skill materialization, repository-Workspace, and
  interval regressions passed, including the exact XNYS Research Desk
  Intake/Run path and a direct `datetime64[us, UTC]` versus
  `datetime64[ns, UTC]` comparison;
- the installed-candidate Pandas 3 smoke intook the original Skill CSVs with no
  timestamp re-encoding or hash repair;
- the fixed two-year negative replay retained
  `provider.range-preflight`, exact requested 501 sessions and 3,492 expected
  rows per asset, no package, and zero quantitative evidence;
- clean positive replay Project `intraday-reversal-regime` contains one Run,
  zero Sessions, one Report
  `report-20260801T142040284809Z-5e309e4c7c69`, and one Dossier
  `dossier-20260801T142131800692Z-cb82202afa85`;
- public `aq validate` returned `ok=true`, Orientation returned
  `required-research-complete` with `tradingAuthority: none`, and the Studio
  snapshot was valid; the worker preserved all three JSON handoff envelopes;
- transcript audit found no source-checkout, prior-trial, or implementation
  access.

Full regression, final rebuilt artifact hashes, installed-final-wheel smoke,
and no-local-override clean-clone verification remain the publication gate.

## Progress log

- 2026-08-01 — Plan created from released-wheel Grok baseline plus independent
  live Yahoo/Nasdaq provider probes.
- 2026-08-01 — Canonical acquisition code and deterministic contracts now map
  regular/early-close bucket starts, reject response defects, emit intake-ready
  V3 on success, and retain no-package failure evidence. A live five-ETF April
  2026 smoke produced 147 aligned rows per asset across 21 sessions with no
  zero-volume rows after the one-hour warmup; the fixed two-year request failed
  preflight because its required provider start fell outside 730 days.
- 2026-08-01 — First candidate negative replay session
  `019fbd8e-57c1-7352-a3e0-445b23bdf1bf` preserved the unchanged two-year
  request as a structured `provider.range-preflight` failure with zero task
  quantitative Runs, Sessions, Reports, or Dossiers. First candidate positive
  replay session `019fbd8f-76e6-76f2-a7d6-ff4b7af75bd5` discovered the new
  Skill and acquired the exact bounded panel, then exposed the Pandas storage-
  resolution Intake defect. Its later timestamp/hash workaround is retained
  as evidence and explicitly excluded from release proof.
- 2026-08-01 — Second candidate replay session
  `019fbda4-3aa8-71d2-a24a-9a14cc8ddfd3` proved the fixed installed Intake but
  exposed a second, research-semantic defect: an Agent can accidentally encode
  missing gate history as zero with ordinary Pandas `where` syntax. Its single
  Run and downstream publications are preserved but excluded from acceptance.
- 2026-08-01 — Third candidate replay session
  `019fbdae-2611-7870-b313-2c3e0a97d5a7` completed the unchanged positive
  assignment in 7m4s with one Project, one correct Factor Run, zero Sessions,
  one Report, one Dossier, no source access, no Harness repair, and no
  downstream overclaim. Independent coverage, target, IC, and prefix-causality
  reconstruction accepted this trial as the successful field proof.

## Completion

Pending.
