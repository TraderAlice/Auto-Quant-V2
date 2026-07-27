# Caller-owned decision cadence

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/caller-owned-decision-cadence]],
  [[docs/design/configurable-session-interval-inputs]],
  [[docs/design/caller-owned-portfolio-research-policy]],
  [[docs/design/signal-policy-and-attribution]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Let an OpenAlice or local caller choose how many locked base bars separate
Portfolio and governed-RL decisions, then make signal transitions, ordinary
rebalances, RL action availability, evidence, and handoff obey that exact
cadence without weakening continuous risk compliance.

## Context

Configurable V3 input currently makes the base K-line cadence the implicit
Portfolio/RL decision cadence. A 15-minute XNYS package therefore permits a
new mechanical signal, target, rebalance, and RL action every 15 minutes even
when the caller intended hourly decisions.

The no-trade band filters small target differences; it does not define when a
decision is permitted. Hidden every-bar authority changes turnover, costs,
position episodes, RL learning semantics, and the current decision handed
back to another OpenAlice workbench.

## Scope

### In scope

- Add a strict bounded `decisionEveryBars` field to caller Portfolio policy.
- Materialize one dataset-start-anchored schedule inside the immutable
  Portfolio Mandate; keep an explicit every-bar reference default.
- Transition mechanical signal state and recompute target weights only on
  eligible bars.
- Allow ordinary execution only on eligible bars while allowing mandatory
  covariance-risk repair on every bar.
- Let governed RL choose a factor sleeve only on eligible bars, carry the
  selected sleeve between decisions, and use the constrained action set in
  Q-learning and baselines.
- Preserve schedule eligibility and hold reasons through artifacts, Explorer,
  Studio, Reports, Dossiers, and OpenAlice handoff.

### Out of scope

- Exchange-session-close, weekday, wall-clock, event, order, TPSL, and live
  UTA schedules.
- Candidate-selected cadence or optimizing cadence cells.

## Acceptance

- [x] Strict Request and Mandate validation reject non-integer, zero, excessive,
  missing, or tampered cadence fields.
- [x] Omission remains an explicit one-base-bar reference default; caller
  cadence changes Request, Mandate, Study, Session, and Run identity.
- [x] Signal state and proposed targets change only on schedule-eligible bars.
- [x] Ordinary trades occur only on eligible bars; an off-schedule book may
  trade only to repair a binding immutable risk ceiling.
- [x] Governed RL selects among actions only on eligible bars and holds the
  prior action between them; learning bootstraps over that same constrained
  action availability.
- [x] Portfolio/RL artifacts and all verified human/Agent handoff surfaces
  disclose cadence, eligibility, scheduled holds, and risk-only overrides.
- [x] A deterministic 15-minute XNYS fixture with four-bar decisions reconciles
  signals, actions, trades, rewards, schemas, complete regression, and build.

## Work

- [x] Audit the interval, signal, execution, RL, evidence, and handoff paths.
- [x] Define caller/Core/Agent authority and the bounded every-N-bars contract.
- [x] Implement strict Request and content-derived Mandate contracts.
- [x] Apply one shared decision mask to Portfolio and governed RL.
- [x] Update verified Explorer, Studio, Report, Dossier, and CLI surfaces.
- [x] Complete focused/full verification, commit, and push.

## Findings and decisions

- 2026-07-27 — A no-trade band answers “is this proposed trade large enough?”
  while cadence answers “is a new ordinary decision permitted at all?” They
  are independent constraints.
- 2026-07-27 — V1 uses an integer number of base bars anchored to the complete
  locked dataset start. The exact base interval gives the number its meaning.
- 2026-07-27 — Risk compliance outranks cadence. An off-schedule book can only
  scale down or flatten under the existing one-sided covariance governor.
- 2026-07-27 — RL action availability must match execution authority. Between
  decision bars the only permitted action is the previously selected sleeve.

## Verification

- `uv run python -m compileall -q autoquant tests`
- `node --check autoquant/studio_assets/studio.js`
- `git diff --check`
- `uv run python -m unittest -v tests.test_mandates
  tests.test_portfolio_lab tests.test_rl_factor_policy_lab
  tests.test_portfolio_explorer tests.test_rl_explorer` — 53 passed.
- `uv run python -m unittest -v
  tests.test_intake.RequestDrivenIntakeTests.test_caller_portfolio_policy_governs_portfolio_and_rl
  tests.test_intake.RequestDrivenIntakeTests.test_v3_xnys_fifteen_minute_caller_cadence_governs_portfolio_and_rl`
  — 2 passed.
- `uv run python -m unittest -v tests.test_reports tests.test_dossiers
  tests.test_research_program` — 24 passed.
- `uv run python -m unittest discover -s tests -v` — 219 passed.
- `uv build` — wheel and source distribution built.
- `uv run python scripts/check_doc_links.py` — 817 links resolved.

## Progress log

- 2026-07-27 — Plan activated after the caller-to-handoff audit found that V3
  configurable inputs still silently granted every-base-bar decision
  authority.
- 2026-07-27 — Strict caller/Mandate contracts, shared Portfolio/RL schedule,
  risk-only off-schedule repair, verified evidence surfaces, and deterministic
  XNYS 15-minute acceptance are implemented; complete regression is running.
- 2026-07-27 — Complete regression, documentation validation, and distribution
  build passed; the milestone was committed and pushed to `main`.

## Completion

Portfolio and governed RL now distinguish data cadence from caller-owned
decision cadence. One content-locked schedule governs signal transitions,
ordinary execution, RL action availability, evidence, and handoff, while
mandatory risk scale-down remains available on every locked base bar.
