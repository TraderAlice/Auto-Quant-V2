# Build a causal signal-to-portfolio laboratory

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/quant-research-lifecycle]] and
  [[docs/design/portfolio-construction-lab]].

## Outcome

AutoQuant can evaluate whether cross-asset factor signals remain useful after
they are mechanically translated into lagged target positions, constrained
portfolio weights, turnover, costs, and portfolio risk rather than judging
signal correlation alone.

## Context

The first OHLCV Factor Lab measures causal factor quality, but a real
quantitative decision also needs to know whether the signal can become an
implementable portfolio. That translation must be fixed Judge authority so an
Agent cannot improve a candidate by weakening costs, delays, or constraints.

## Scope

### In scope

- Signal normalization and ranking, volatility scaling, fixed long-short
  budgets, caps, gross/net constraints, tolerance bands, lagged
  rebalance, and deterministic OHLCV cost assumptions.
- Factor, portfolio, risk, implementation, and robustness metric families.
- Chronological validation, one-bar-delay and cost stress, and per-asset
  contribution evidence. Parameter-neighborhood and selection-adjusted
  statistics remain explicit follow-up work.
- A fast deterministic multi-asset reference Project and Studio projections.

### Out of scope

- Broker/order routing, tick or L2 simulation, and live account state.
- Optimistic capacity claims without volume/market-impact inputs.
- Asset-specific execution engines selected by an Agent.

## Acceptance

- [x] A fixed Judge causally maps one factor frame to target weights and net
      portfolio returns with no same-bar lookahead.
- [x] Evidence separates factor quality, portfolio performance, risk,
      implementation costs, and robustness.
- [x] Target construction enforces declared long/short budgets, gross/net and
      per-asset caps; accounting models drift, no-trade bands, traded notional,
      one-way turnover, costs, and volume participation without Broker claims.
- [x] Chronological train/validation/test evidence includes a benchmark,
      per-asset contributions, cost stress, and an extra-delay stress.
- [x] The ordinary pandas candidate API remains Agent-editable while all
      targets, returns, costs, splits, metrics, and promotion scores remain
      fixed Judge authority.
- [x] A self-contained `ohlcv-portfolio-lab` Project runs through CLI,
      Session/Experiment/Campaign/Studio and emits machine-inspectable
      portfolio artifacts.
- [x] Tests prove deterministic accounting, constraints, delay, costs, and
      known failure/improvement cases on bounded fixtures.
- [x] CLI capabilities, template discovery, canonical docs, wheel contents,
      full bounded tests, and documentation links agree.

## Work

- [x] Specify the portfolio contract, timing, cost, benchmark, risk, and metric
      taxonomy.
- [x] Implement fixed target construction, drift-aware accounting, stress, and
      metric primitives.
- [x] Ship the self-contained reference Project and public template discovery.
- [x] Prove baseline, known improvement, lookahead rejection, Campaign, Studio,
      and artifact behavior.
- [x] Audit documentation, package contents, reproducibility, and completion.

## Findings and decisions

- 2026-07-24 — Target weights, not broker orders, are the correct AutoQuant
  boundary. Forward execution belongs to OpenAlice's trading authority.
- 2026-07-24 — The first portfolio lane is a dollar-neutral, gross-one,
  end-of-bar target-weight simulation. The fixed Judge converts causal signals;
  candidate code cannot choose sizing, delay, costs, or constraints.
- 2026-07-24 — One-way turnover is half absolute target change, while estimated
  cost uses full absolute traded notional at a declared one-way basis-point
  rate. Reports expose both to avoid a hidden factor-of-two convention.

## Verification

- `git diff --check`
- `uv run python -m compileall -q autoquant tests/test_portfolio_lab.py`
- `node --check autoquant/studio_assets/studio.js`
- `uv run python scripts/check_doc_links.py` — 165 links.
- `uv run python -m unittest discover -s tests -v` — 77 tests.
- `uv build --wheel --out-dir <temporary-directory>` — wheel built and all
  six `ohlcv_portfolio_lab` assets were present.
- Bounded synthetic smoke: momentum baseline produced finite layered evidence;
  the known relative-volume candidate improved robust net Sharpe from
  `2.642102` to `31.914606`; negative-shift lookahead was rejected.

## Progress log

- 2026-07-24 — Proposed after the research-handoff design established the
  external decision-support boundary.
- 2026-07-24 — Activated after commit `5bc6161` fixed the preceding OpenAlice
  request/report milestone.
- 2026-07-24 — Completed the fixed accounting Core, self-contained template,
  CLI/Studio projections, Campaign path, artifacts, and bounded verification.

## Completion

The V1 lab is a causal, dollar-neutral target-weight research lane with fixed
portfolio authority and no Broker surface. More portfolio families,
selection-adjusted evidence, nonlinear market impact, and production asset
data remain separate follow-up work rather than hidden V1 assumptions.
