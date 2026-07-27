# Market-clock decision anchors

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/market-clock-decision-anchors]],
  [[docs/design/caller-owned-decision-cadence]], and
  [[docs/design/configurable-session-interval-inputs]].

## Outcome

Let a collaborating workbench choose whether every-N-base-bar Portfolio/RL
decisions remain anchored to the complete dataset or restart at each verified
market session, without changing the continuous every-bar risk contract.

## Context

XNYS regular sessions contain 26 fifteen-minute bars and scheduled early-close
sessions contain 14. A global four-bar modulo therefore moves the first
eligible decision across days. That is deterministic, but it does not express
the common research assumption “restart this intraday schedule each session.”

## Scope

### In scope

- Require a strict caller `decisionAnchor` beside `decisionEveryBars`.
- Support `dataset-start` for every locked input and `session-start` only for
  verified intraday XNYS V3 packages.
- Reset the eligible-bar ordinal at each complete XNYS session while retaining
  one identical mask across splits, Portfolio, RL, and replay.
- Disclose anchor and per-bar session identity through evidence and handoff.
- Prove regular-session, early-close, and cross-split behavior.

### Out of scope

- Arbitrary wall-clock times, weekdays, session-close-only policies, auctions,
  extended hours, halts, events, orders, TPSL, or OpenAlice UTA scheduling.

## Acceptance

- [x] Request, Mandate, and schema validation reject missing, unknown, or
  tampered anchors.
- [x] Intake rejects `session-start` unless the locked package is V3 intraday
  XNYS regular-session data.
- [x] `dataset-start` preserves one global modulo; `session-start` makes the
  first complete base bar and each Nth following base bar eligible per session.
- [x] Signal, ordinary execution, RL choice/bootstrap, diagnostics, Studio,
  Report, Dossier, and CLI use and disclose the same anchored mask.
- [x] A deterministic 15-minute fixture proves every session restarts at its
  first bar across normal sessions and a scheduled early close.
- [x] Full regression, documentation links, package build, commit, and push
  pass.

## Work

- [x] Audit global-modulo behavior against XNYS bar counts.
- [x] Define caller/Core authority and the bounded two-anchor contract.
- [x] Implement contracts and intake compatibility validation.
- [x] Apply and disclose one anchor-aware mask in Portfolio and RL.
- [x] Complete verification, commit, and push.

## Findings and decisions

- 2026-07-27 — Data cadence, decision spacing, and decision anchor are three
  separate assumptions.
- 2026-07-27 — V1 deliberately supports only dataset-start and XNYS
  session-start. Generic market-session inference would overstate current
  calendar authority.
- 2026-07-27 — The first completed base bar is eligible after each
  session-start reset; clock-offset and close-only schedules remain separate
  future contracts.

## Verification

- `uv run python -m unittest -v tests.test_mandates
  tests.test_intake.RequestDrivenIntakeTests.test_session_start_anchor_requires_xnys_intraday_input`
  — 11 passed.
- `uv run python -m unittest -v
  tests.test_intake.RequestDrivenIntakeTests.test_v3_xnys_fifteen_minute_caller_cadence_governs_portfolio_and_rl`
  — passed.
- `uv run python -m unittest -v tests.test_portfolio_explorer
  tests.test_rl_explorer` — 23 passed after one schema placement fix.
- `uv run python -m unittest -v tests.test_reports tests.test_dossiers
  tests.test_research_program` — 24 passed.
- `uv run python -m unittest discover -s tests -v` — 221 passed.
- `uv build` — wheel and source distribution built.
- `uv run python scripts/check_doc_links.py` — 829 links resolved.
- `uv run python -m compileall -q autoquant tests`
- `node --check autoquant/studio_assets/studio.js`
- `git diff --check`

## Completion

AutoQuant now binds every-N-bar decisions to either one complete-dataset
ordinal or a verified XNYS session-reset ordinal. Portfolio, governed RL,
evidence verifiers, Studio, Reports, Dossiers, and CLI share and disclose the
exact anchor while every-bar risk-only repair remains unchanged.
