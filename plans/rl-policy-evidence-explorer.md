# Build a verified RL policy evidence explorer

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/rl-factor-policy-lab]] and
  [[docs/design/rl-policy-evidence-explorer]].

## Outcome

AutoQuant can project one immutable governed RL Run into a bounded,
reconciled evidence surface for Agents and Studio, with simple-baseline
comparison, fold/seed dispersion, training behavior, action allocation, and
implementation cost visible together.

## Scope

### In scope

- Verify the fixed RL report, models, training history, and action ledger
  against the immutable Run identity and metrics.
- Add one versioned `aq run rl` read model and JSON Schema.
- Show validation selection separately from visible test audit evidence.
- Show every fold/seed trial, the validation-selected baseline, RL advantage,
  training episodes, fixed-action allocation, turnover, cost, and failures.
- Add a read-only Studio explorer whose rendering contains no research or
  selection logic.
- Add fast deterministic tests, full regression, wheel checks, and browser QA.

### Out of scope

- Training, seed selection, policy promotion, or candidate mutation in Studio.
- A generic deep-RL observability platform.
- Inventing state/regime explanations that are not present in immutable
  artifacts.
- Live trading authority or Broker/UTA integration.

## Acceptance

- [x] Corrupt or inconsistent RL artifacts fail before a projection is shown.
- [x] Every declared fold and seed is represented; failures cannot disappear.
- [x] The read model reconciles action frequency, rewards, observations,
      training budgets, and model dimensions with Run metrics/configuration.
- [x] Validation/test roles and baseline selection semantics remain explicit.
- [x] CLI capabilities, schema discovery, Studio snapshot, and UI agree.
- [x] UI exposes performance, training, and action/implementation evidence
      without recomputing authority in JavaScript.
- [x] Focused tests, complete bounded tests, wheel contents, and browser checks
      pass.

## Work

- [x] Audit the existing RL Run and artifact contracts.
- [x] Define the evidence questions and no-authority UI boundary.
- [x] Implement the verified bounded Core projection.
- [x] Add CLI/schema/capability discovery.
- [x] Add Studio projection and interaction.
- [x] Verify determinism, corruption failure, packaging, and browser behavior.

## Findings and decisions

- 2026-07-24 — The existing Judge already persists sufficient V1 evidence:
  complete fold/seed metrics, fixed and contextual-ridge baselines, exact model
  weights, every training episode, and timestamped validation/test actions.
  This milestone does not change Judge evaluation semantics.
- 2026-07-24 — State-conditional action interpretation is excluded because the
  action ledger does not persist encoded state. The explorer will show only
  evidence it can verify: action allocation, transitions, realized reward,
  turnover, and cost.
- 2026-07-24 — Studio will lead with RL-minus-best-baseline, not raw Sharpe.
  A profitable adaptive policy that loses to a simple baseline is negative RL
  value-add evidence.

## Verification

- `git diff --check`
- `uv run python -m compileall -q autoquant tests/test_rl_explorer.py`
- `node --check autoquant/studio_assets/studio.js`
- `uv run python scripts/check_doc_links.py` — 313 links.
- `uv run python -m unittest tests.test_rl_explorer -v` — 2 tests in
  24.591s.
- `uv run python -m unittest discover -s tests` — 115 tests in 347.164s.
- `uv build --wheel --out-dir /tmp/autoquant-rl-wheel-20260724` — wheel
  contains `rl_explorer.py`, Studio assets, and the governed RL Judge/Core.
- Real reference Run: 6/6 trials reconciled across 780 action rows and 24
  training episodes. Validation mean net Sharpe was `8.967443`, while mean
  validation advantage versus the fixed selected baseline was `-29.261027`.
- Rehashed action-ledger truncation failed the Core projection and Studio
  removed only the invalid RL explorer claim while preserving diagnostics.
- Browser QA at `http://127.0.0.1:8769/` verified Performance, Training,
  Actions, Validation, and Test-audit controls plus semantic roles and
  no-trading disclosure.

## Progress log

- 2026-07-24 — Activated after the Factor Evidence Explorer milestone.
- 2026-07-24 — Completed Core reconciliation, CLI/schema discovery, Studio
  evidence views, corruption tests, full regression, packaging, and browser
  QA.

## Completion

One immutable governed RL Run now has a professional evidence surface shared
by Agents and humans. It makes negative value-add impossible to hide behind a
high absolute Sharpe, preserves every fixed fold/seed and episode, and keeps
actions subordinate to governed factor sleeves with no trading authority.
