# Build a causal signal-to-portfolio laboratory

- Status: `proposed`
- Updated: `2026-07-24`
- Related design: [[docs/design/quant-research-lifecycle]].

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

- Signal normalization and ranking, volatility scaling, long-only and
  long-short budgets, caps, gross/net constraints, tolerance bands, lagged
  rebalance, and deterministic OHLCV cost assumptions.
- Factor, portfolio, risk, implementation, and robustness metric families.
- Chronological validation, one-bar-delay and cost stress, parameter stability,
  and declared trial-count evidence.
- A fast deterministic multi-asset reference Project and Studio projections.

### Out of scope

- Broker/order routing, tick or L2 simulation, and live account state.
- Optimistic capacity claims without volume/market-impact inputs.
- Asset-specific execution engines selected by an Agent.

## Acceptance

- [ ] A fixed Judge causally maps one factor frame to target weights and net
      portfolio returns with no same-bar lookahead.
- [ ] Evidence separates factor quality, portfolio performance, risk,
      implementation costs, and robustness.
- [ ] Tests prove deterministic accounting, constraints, delay, costs, and
      known failure/improvement cases on bounded fixtures.

## Work

- [ ] Specify the portfolio contract and metric taxonomy.
- [ ] Implement fixed portfolio construction/accounting primitives.
- [ ] Ship the reference Project, CLI/Studio evidence, and tests.
- [ ] Audit documentation and reproducibility.

## Findings and decisions

- 2026-07-24 — Target weights, not broker orders, are the correct AutoQuant
  boundary. Forward execution belongs to OpenAlice's trading authority.

## Verification

- Pending.

## Progress log

- 2026-07-24 — Proposed after the research-handoff design established the
  external decision-support boundary.

## Completion

Pending.
