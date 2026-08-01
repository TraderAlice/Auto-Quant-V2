# Korea delayed-gap Event Study field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.13`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/ohlcv-price-event-study]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove whether a fresh quantitative coworker can begin with one caller-fixed
South Korean price-event question and zero staged OHLCV, preserve raw versus
adjusted provider semantics across a known corporate-action boundary, execute
one immutable Event Study, and return a useful negative, positive, or
insufficient historical answer without private Workbench knowledge or trading
claims.

The released `0.9.12` wheel is the baseline. `0.9.13` will contain only
reusable friction reproduced by that worker. Breaking cleanup is allowed when
the current contract is wrong; compatibility with superseded V2 behavior is
not a release requirement.

## Field assignment

Ask whether large downside opening gaps in Samsung Electronics historically
show useful delayed five-session behavior and advantage relative to a named
Korean semiconductor peer.

- Event asset: Samsung Electronics (`005930.KS`, KOSPI).
- Matched-date reference: SK hynix (`000660.KS`, KOSPI).
- Completed daily observations: `2010-01-01` through `2026-07-31`; disclose
  the actual final completed provider session.
- Event: `open[t] / adjusted_close[t-1] - 1 <= -4%`.
- Wait: one completed bar, so entry is the `t+1` close.
- Outcome: five-bar close-to-close return from entry to `t+6`.
- Primary population: keep the earliest complete event until its exit, then
  admit the next non-overlapping event.
- Minimum useful primary population: ten events, frozen before the Run.
- References: Samsung's unconditional five-bar history and matched-date SK
  hynix five-bar returns.
- Use at least two independently executable Korean provider routes. Yahoo may
  supply the formal split-adjusted package; Naver and Daum are raw routes.
  Raw and adjusted packages may establish identity, access, coverage, and
  observed quality but must not be relabelled as numerically equivalent.
- Historical quantitative decision support only. Do not attribute an event
  to earnings or news and do not create an Order or trading recommendation.

## Scope

### In scope

- One isolated fresh Grok 4.5 worker using the exact installed `0.9.12` wheel,
  a new Workspace, generated Skills, public CLI/schema surfaces, and provider
  networking.
- English brief quality, template choice, demand-led acquisition, provider
  evidence, semantic comparison, strict intake, fixed Event execution,
  Explorer/Report handoff, and stopping behavior.
- Exact retry, failure, mutation, Project, Run, Session, and evidence
  inventories.
- The smallest coherent Core, Skill, template, CLI, Studio, or documentation
  repair for each reproducible material Workbench defect.
- A fresh candidate-wheel replay and complete release audit before tagging
  `v0.9.13`.

### Out of scope

- Earnings/news labels, fundamentals, intraday execution, threshold or timing
  search, event taxonomy expansion, or causal claims.
- KRX-authenticated truth, provider licensing conclusions, historical index
  membership, delisting coverage, or changing the named assets.
- A central data inventory, automatic refresh, cross-Project cache authority,
  Broker, Order, TP/SL, or live account behavior.
- OpenAlice version changes; it remains pinned to `0.8.31`.

## Acceptance

- [ ] A fresh installed-wheel worker preserves the exact English question
      before downloading data or creating quantitative authority.
- [ ] The worker begins with zero OHLCV, discovers the Korean acquisition
      guidance, and preserves at least two independently attempted routes.
- [ ] Raw versus adjusted price meaning, canonical/provider symbols, venue,
      currency, volume, date range, and corporate-action limitations remain
      explicit without false numerical equivalence.
- [ ] Exactly one `ohlcv-event-study-lab` Project and one fixed Event Run
      answer the caller-owned threshold, wait, holding, overlap, minimum-count,
      asset, and reference contract without parameter search.
- [ ] Strict Explorer and durable handoff expose event counts, censoring,
      overlap, both references, uncertainty, and an honest conclusion.
- [ ] No Session, candidate optimization, earnings attribution, Order, or
      trading authority is created.
- [ ] Every material retry or failure becomes either deterministic regression
      coverage and a bounded repair or an explicit provider/research limit.
- [ ] Final replay, full tests, documentation, build/install, Studio, and
      no-hardlink clean-clone smoke pass before `v0.9.13` is tagged and pushed.

## Work

- [x] Define one caller-fixed Korean Event assignment from clean released
      `v0.9.12`.
- [x] Prepare an isolated installed-wheel desk and immutable host inventory.
- [x] Run the unchanged baseline assignment with a fresh Grok worker.
- [x] Audit transcript, filesystem, provider evidence, and scientific answer.
- [ ] Implement only reproduced reusable friction with deterministic tests.
- [ ] Replay with a fresh candidate-wheel worker.
- [ ] Complete the `v0.9.13` release audit and publish the tag.

## Findings and decisions

- 2026-08-01 — Korea was selected because the Workbench has two independent
  raw routes plus one broad adjusted route, while Samsung's 2018 share split
  makes their semantic difference material rather than theoretical.
- 2026-08-01 — Event Study was selected to avoid another cross-sectional
  Factor replay. The caller fixes event, clock, reference, and useful sample
  floor; the worker may choose providers but may not search the question.
- 2026-08-01 — Existing Workspace data never narrows this assignment. The
  worker must acquire one task-complete package even if equivalent bytes exist
  elsewhere, and any duplication is valid evidence isolation rather than a
  reason to introduce shared mutable inventory.
- 2026-08-01 — This is a durable `0.9.x` product principle, not a temporary
  field-trial convenience: provider Skills and audit knowledge are reusable;
  market-data inventory is not research authority. Storage deduplication may
  exist only as an invisible optimization that preserves task-local identity.
- 2026-08-01 — Baseline cohort 28 used the exact released `0.9.12` wheel,
  wrote the English brief before retrieval, attempted Yahoo, Naver, and Daum,
  created exactly one Event Project, one successful fixed Run, one direct
  Report, and no Session. It stopped in read-only `observe` mode without
  parameter search, earnings attribution, environment repair, or trading
  authority.
- 2026-08-01 — Yahoo strict intake first rejected four isolated impossible
  OHLC observations. The worker preserved that attempt and explicitly selected
  the existing bounded `drop-observation` policy. The final aligned
  split-adjusted package disclosed all four rows and retained 4,074 sessions
  per asset from 2010-01-04 through 2026-07-31.
- 2026-08-01 — Naver failed on three Samsung 2018 split-suspension rows with
  zero open/high/low and volume but a positive carried close. These are
  provider no-trade placeholders, not valid OHLCV bars. The reusable repair is
  to omit only that exact shape from normalized observed history while keeping
  every raw row and an exact omission audit; any partial or traded nonpositive
  row must still fail closed.
- 2026-08-01 — Daum failed because 13 Samsung rows had
  `accTradePrice / accTradeVolume` outside the provider's daily OHLC range,
  with maximum distance 2.58% from the nearest bound. The OHLC and share
  volume themselves remained valid. AutoQuant cannot assume these provider
  aggregates share one session scope, so the ratio becomes a retained exact
  diagnostic rather than a hard price-validity gate. No provider value, price,
  or volume is repaired.
- 2026-08-01 — Candidate replay against the retained Naver response exposed a
  second, previously masked provider shape: 11 pre-split Samsung rows place
  close exactly one KRW above high. This is deterministic integer rounding,
  not a usable OHLC bound. Preserve the exact raw row, expand only a bound
  whose violation is at most one KRW, and audit each normalized value; any
  larger or non-bound inconsistency still fails closed.
- 2026-08-01 — No Event Core, template, Report, or Studio defect prevented the
  assignment. The candidate patch is limited to truthful Naver placeholder
  normalization, truthful Daum aggregate diagnostics, their command/audit
  projections, Skill guidance, and deterministic regression coverage.

## Verification

- Baseline wheel SHA-256:
  `0503714efb42ac0593c3e48dd7a9cad54596515edc2df823226a5a427d2e17da`.
  The isolated runtime reported AutoQuant `0.9.12`, Python 3.11.14, and pandas
  3.0.5.
- Baseline Grok session `019fbb72-65d1-7010-80c5-7475e3f8b372` completed in
  28 turns. Its 680-line exported transcript and complete Workspace remain
  under `grok-field-trials/cohort-28-korea-gap-event-v0912-baseline`.
- Project `samsung-gap-event-2010-2026`, Run
  `run-20260801T035349892284Z-db5990bae2ee`, and Report
  `report-20260801T035455403097Z-bbb2edf8dcd1` all reload through strict public
  surfaces. Host validation and Studio snapshot returned `ok`.
- The fixed Run found 29 qualifying events, 28 complete, 20 primary,
  8 overlap-excluded, and 1 right-censored. Primary Samsung mean was
  `+2.8278%`, unconditional Samsung mean `+0.4097%`, and matched SK hynix mean
  `+1.1465%`; matched excess was `+1.6812%`. Both primary and excess 95% normal
  intervals include zero, so the Report correctly limits `observed-advantage`
  to descriptive in-sample association.
- Exact retained provider evidence reproduces three Naver no-trade
  placeholders and 13 Daum value/volume-derived out-of-range observations.
  Naver maximum semantic issue is the 2018 split suspension; Daum maximum
  derived-ratio distance is `2.5796%`. Neither raw route is relabelled as
  adjusted-equivalent to Yahoo.

## Progress log

- 2026-08-01 — Plan created and indexed from clean released `v0.9.12`. No
  implementation change is authorized until a fresh baseline worker exposes
  concrete reusable friction.
- 2026-08-01 — Baseline cohort 28 completed the unchanged assignment and
  proved the Event workflow itself is usable. The two independent Korean raw
  routes exposed bounded provider-normalization defects, so implementation is
  now authorized only on those Skill surfaces.

## Completion

Complete this section only when status becomes `completed`.
