# Caller-owned Portfolio research policy

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/caller-owned-portfolio-research-policy]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/portfolio-construction-lab]],
  [[docs/design/rl-factor-policy-lab]], and
  [[docs/design/program-research-dossiers]].

## Outcome

Let an OpenAlice or local research caller lock the portfolio risk,
implementation-cost, rebalance, and reference-capital assumptions that answer
its decision-support question. Portfolio and governed RL must consume the same
immutable policy, while candidate Agents remain unable to relax those
assumptions during strategy iteration.

## Context

AutoQuant currently derives asset permission and direction from the Research
Request but hardcodes every numeric portfolio assumption:

```text
gross 1.0
single-name cap 0.30
annualized volatility ceiling 0.15
10 bps linear cost
5% one-way no-trade band
USD 1,000,000 reference NAV
```

Those defaults are useful fixtures, not universal answers. A collaborating
workbench asking about a smaller, costlier, or more conservative intended
book receives evidence for AutoQuant's assumptions rather than its own.

## Scope

### In scope

- Add an optional strict `portfolioPolicy` to the Research Request.
- Lock gross limit, global single-name cap, annualized volatility ceiling,
  base linear cost, no-trade band, and reference NAV into the Portfolio
  Mandate.
- Preserve explicit documented defaults when a simple caller omits policy.
- Make Portfolio construction/accounting, cost stress, capacity evidence, and
  governed-RL rollout/opportunity accounting use the same exact policy.
- Project policy through Run metrics, mechanical decisions, Reports,
  Dossiers, CLI schemas, Studio, and OpenAlice handoff evidence.
- Prove that candidate source cannot alter the request-owned policy and that
  changed policy changes Study/Run identity.

### Out of scope

- Live account balances, buying power, margin, borrow, funding, tax, spread,
  nonlinear impact, sector constraints, or per-asset caps.
- Caller-configurable signal thresholds, Portfolio optimizers, RL actions,
  rewards, or learning hyperparameters.
- OpenAlice UTA mutation or any trading authority.

## Acceptance

- [x] Strict request validation rejects unknown, non-finite, out-of-bound, or
  internally inconsistent portfolio-policy values.
- [x] Intake derives one canonical Mandate containing the exact normalized
  caller policy or explicit defaults.
- [x] Portfolio and governed RL use identical gross/cap/risk/cost/no-trade/NAV
  values in construction, execution, reward, capacity, and evidence.
- [x] Cost stress remains centered on the caller base cost rather than a
  hidden fixed 10 bps assumption.
- [x] Run, CLI, Studio, Report, and Dossier surfaces disclose the policy as
  research assumptions with `tradingAuthority: none`.
- [x] Deterministic custom-policy Factor/Portfolio/RL tests, tamper checks,
  full regression, schemas, docs, and package build pass.

## Work

- [x] Audit the Research Request, Mandate, Portfolio, RL, and handoff policy
  flow.
- [x] Define caller authority, bounded fields, defaults, and non-goals.
- [x] Implement request/mandate validation and schemas.
- [x] Make Portfolio and RL accounting consume the locked policy.
- [x] Update evidence projections, docs, and deterministic fixtures.
- [x] Run focused/full/browser/build verification, complete, commit, and push.

## Findings and decisions

- 2026-07-27 — The principal service-design gap is not missing diagnostics;
  it is that AutoQuant answers every caller under one hidden implementation
  and risk profile.
- 2026-07-27 — Policy belongs to the caller-owned request and fixed Mandate,
  never candidate code. That makes stricter or looser assumptions legitimate
  question changes rather than optimizer degrees of freedom.
- 2026-07-27 — Reference NAV is a research participation assumption, not an
  authenticated OpenAlice account balance.
- 2026-07-27 — Per-asset caps, hedges, margin, and nonlinear costs remain
  separate because their mechanics cannot be represented truthfully by a
  single global scalar.

## Verification

- `uv run python -m unittest discover -s tests`
  - 208 tests passed in 1387.623 seconds.
- `node --check autoquant/studio_assets/studio.js`
  - passed.
- `git diff --check`
  - passed.
- `uv build`
  - built `auto_quant-0.1.0.tar.gz` and
    `auto_quant-0.1.0-py3-none-any.whl`.

## Progress log

- 2026-07-27 — Plan activated after auditing the complete OpenAlice request →
  Factor/Portfolio/RL → Dossier path against a real caller's decision inputs.
- 2026-07-27 — Added strict optional `portfolioPolicy`, derived one immutable
  implementation policy, and made Portfolio and governed RL consume it.
- 2026-07-27 — Fixed two audit findings found during integration: RL reward
  semantics no longer claim hidden 10bps cost, and liquidity breach metrics
  use the exact Mandate reference NAV rather than the legacy default.
- 2026-07-27 — Full regression, Studio syntax, static diff, and package build
  passed.

## Completion

AutoQuant now answers Portfolio and governed-RL questions under the caller's
explicit research assumptions. Omitting the policy remains simple but produces
an auditable `reference-default` Mandate. Candidate Agents cannot tune the
policy, and every downstream result/handoff retains `tradingAuthority: none`.
