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
- [ ] Prepare an isolated installed-wheel desk and immutable host inventory.
- [ ] Run the unchanged baseline assignment with a fresh Grok worker.
- [ ] Audit transcript, filesystem, provider evidence, and scientific answer.
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

## Verification

Pending baseline evidence.

## Progress log

- 2026-08-01 — Plan created and indexed from clean released `v0.9.12`. No
  implementation change is authorized until a fresh baseline worker exposes
  concrete reusable friction.

## Completion

Complete this section only when status becomes `completed`.
