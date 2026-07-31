# Demand-led market-data research field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.6`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/ohlcv-price-event-study]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that a fresh quantitative coworker can begin with a caller-owned market
question and no staged OHLCV, acquire one task-complete dataset through the
installed Skill router, preserve two independently attempted source routes,
select truthful semantics, and finish a fixed AutoQuant study. Local data
inventory must remain an implementation detail rather than research scope.

## Field assignment

Use a fixed mainland-China A-share price-event question:

- event asset: CATL (`300750`, `XSHE`);
- matched reference: CSI 300 ETF (`510300`, `XSHG`);
- completed daily bars from `2020-01-01` through the last completed session
  before retrieval;
- downside opening gap at or below `-3%`;
- wait one completed bar, then measure five-bar close-to-close return;
- keep the first non-overlapping event until exit;
- require at least eight primary events;
- quantitative decision support only, with no Order or trading authority.

The caller supplies no data package and names no preferred provider. The
worker must route through the installed A-share acquisition guidance, attempt
at least two independently executable sources, keep raw/audit evidence, and
select an adjusted package because the fixed Event Study rejects raw prices.
Raw and adjusted routes must not be numerically compared or relabelled as
equivalent.

## Scope

### In scope

- Run one isolated installed-wheel Grok trial with only the assignment, public
  `aq`, generated Workspace Skills, and networked provider scripts.
- Observe question clarification, route discovery, two-source behavior,
  provider failures, semantic selection, packaging, intake, Run, Explorer,
  Studio, and outward handoff.
- Record every worker retry, degraded provider, ambiguity, unsupported claim,
  and reusable Workbench need in trial evidence.
- Promote only concrete reusable friction into Core, Skill, CLI, docs, and
  deterministic regressions.
- Re-run a fresh installed-wheel worker after material fixes and release
  `v0.9.6` only when the end-to-end route is honest and repeatable.

### Out of scope

- A central or reusable market-data inventory, automatic cache selection, or
  pre-downloading a broad universe.
- Provider credentials, exchange-authenticated truth, redistribution grants,
  or a universal downloader API in Core.
- Expanding the Event Study DSL, tuning its event threshold, or searching
  assets/horizons after observing results.
- OpenAlice version changes, Broker, Order, TP/SL, or account authority.

## Acceptance

- [ ] A clean installed-wheel worker receives no OHLCV and preserves the full
  caller question before provider selection.
- [ ] The worker discovers the A-share router and attempts at least two source
  routes without treating one as a silent fallback.
- [ ] Raw/adjusted, venue, volume, calendar, freshness, and access differences
  remain explicit; incompatible packages are never numerically compared.
- [ ] One task-complete adjusted, aligned, content-locked package reaches
  `ohlcv-event-study-lab` through strict intake with no global data inventory.
- [ ] Exactly one fixed Event Run is reloaded through the strict Explorer and
  produces an evidence-backed answer, including an honest insufficient or
  negative result when that is what the data show.
- [ ] Project validation, orientation, Studio snapshot, provider/package
  audits, and the final handoff all disclose no trading authority.
- [ ] Every material trial failure becomes either a bounded repair with a
  regression or an explicit provider/external limitation.
- [ ] Focused and complete tests, documentation links, JavaScript syntax,
  build, installed-wheel smoke, clean-clone checks, and a fresh final worker
  pass before `v0.9.6` is tagged and pushed.

## Work

- [x] Choose one materially different real assignment that begins with no
  staged bytes and cannot be answered from data inventory.
- [x] Prepare an isolated installed `0.9.5` baseline trial and capture its full
  transcript and filesystem evidence.
- [ ] Triage observed friction against current Core/Skill authority.
- [ ] Implement the minimum reusable `0.9.6` repairs and regressions.
- [ ] Run a fresh final coworker and complete the release audit.

## Findings and decisions

- 2026-08-01 — Event research was chosen instead of another Factor/Portfolio
  replay because it tests demand-led acquisition, template routing, adjusted
  price semantics, and fixed negative evidence without candidate search.
- 2026-08-01 — Eastmoney/Tencent/Sina/Sohu raw routes can establish independent
  A-share identity/access evidence but cannot satisfy the adjusted Event Study
  contract. Yahoo is currently the broad split-adjusted route. Source diversity
  does not imply semantic equivalence or permission to compare prices.
- 2026-08-01 — Demand owns data scope. Available Workspace bytes, prior
  Projects, and provider convenience must never narrow or reshape the caller's
  research question. A Project may deliberately reacquire and freeze duplicate
  task-coherent bytes; reusable value belongs in routing knowledge, semantic
  checks, and acquisition audits rather than a central inventory.
- 2026-08-01 — The isolated installed `0.9.5` worker completed the fixed CATL
  Event Study from zero staged data on its first research attempt. It attempted
  Yahoo, Eastmoney, and Tencent; selected Yahoo's split-adjusted package;
  retained the raw-route evidence; and published one negative fixed Run with
  24 primary events and no Session, Check, Experiment, Order, or trading claim.
- 2026-08-01 — The baseline exposed bounded reusable friction: one valid Yahoo
  zero-volume row forced scientifically costly date deletion; a descriptive
  Event request could not keep both assets `context-only`; mainland raw Skills
  mislabeled the CSI 300 ETF as equity; incompatible packages lacked a
  coverage-only comparison; and a failed provider lacked a standard audit
  artifact. Yahoo adjusted freshness and the absence of a second adjusted
  mainland route remain explicit provider limitations rather than Core fixes.

## Verification

- Baseline transcript:
  `../grok-field-trials/cohort-10-demand-led-a-share-event-v095/grok-transcript.md`
- Baseline Project:
  `../grok-field-trials/cohort-10-demand-led-a-share-event-v095/desk/workspace/projects/catl-opening-gap-event`
- Baseline result: `no-observed-advantage`; 30 complete events, 24 primary
  non-overlapping events, mean five-bar event return `-0.085%`, matched excess
  versus `510300` `+0.566%`, with confidence intervals including zero.

## Progress log

- 2026-08-01 — Plan created and indexed from the released clean `v0.9.5`
  baseline before field-trial setup.
- 2026-08-01 — Completed and preserved the installed `0.9.5` baseline, then
  began the minimum repair pass without changing the caller-fixed Event design
  or touching OpenAlice's `0.8.31` installation.

## Completion

Pending.
