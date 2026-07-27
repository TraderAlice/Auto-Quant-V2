# Executed-book risk compliance

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]],
[[docs/design/portfolio-risk-governor]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]],
[[docs/design/portfolio-decision-explorer]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the causal risk-compliance decision applied after portfolio
drift and before a book earns its next return. It covers forecast availability,
the no-trade override, proportional risk repair, exact daily evidence, split
compliance diagnostics, and Portfolio/RL parity.

It does not own the request-derived ceiling, covariance estimator, raw target
construction, live orders, Broker/UTA state, account capital, or intraday risk.

## Why target governance is not enough

The signal policy first produces a covariance-governed target. Accounting then
drifts the prior book through the return ending at close `t` and may retain that
book when the proposed trade is inside the no-trade band. The retained book is
not the target the first governor checked.

The authoritative compliance object must be the final weight vector that earns
`close(t) → close(t+1)`.

## Fixed execution decision

At decision close `t`:

```text
prior executed book
→ drift through return ending at t
→ causally forecast drifted-book volatility from returns through t
→ causally recheck the proposed target under the same covariance policy
→ ordinary target/no-trade decision
→ if the chosen book breaches the ceiling:
     scale that chosen book proportionally by ceiling / forecast
→ record the final executed-book forecast
→ earn only the next close-to-close return
```

The risk repair is one-sided. It may reduce absolute positions but never scale
them up. When the ordinary no-trade decision would retain an excessive drifted
book, risk compliance bypasses the band and trades only the proportional
difference between the drifted and repaired book. It does not force unrelated
signal changes from the proposed target.

If covariance history is unavailable or invalid, the fixed policy remains
fail-flat, matching target construction. Legacy mandates without a risk policy
retain their historical behavior and make no compliance claim.

## Evidence

Every new daily Portfolio row records:

- execution-risk status and forecast observations;
- drifted/pretrade annualized forecast;
- proposed-target annualized forecast after the runtime recheck;
- final executed annualized forecast and declared ceiling;
- ordinary proposed turnover, risk repair scale, override flag, and execution
  reason.

The per-asset decision ledger repeats date-level authority fields beside exact
weights and trades. Governed RL action rows publish the same execution-risk
fields for every declared fold and seed.

Split summaries expose:

- eligible and unavailable dates;
- drifted-book breach count/rate;
- risk-only override count/rate;
- executed-book breach count/rate;
- mean and maximum executed forecast;
- maximum ceiling error.

Any available executed breach beyond numeric tolerance fails the Judge rather
than becoming a warning.

## Selection and authority

Executed-book compliance is an invariant, not alpha. Its Session descriptors
use context preference and cannot affect KEEP/REVERT or non-dominance. Reports,
Dossiers, and Studio may explain how often risk governance changed the
mechanical path, but zero breaches do not make one candidate better than
another.

All resulting weights remain historical target-weight research evidence.
Nothing in this contract authorizes live orders, authenticated capital
allocation, or external trading-account mutation.

## Legacy evidence

Older immutable Portfolio and RL Runs without execution-risk columns remain
readable. Their projections explicitly mark executed-book compliance
unavailable instead of inferring it from target-level risk fields.

## Invariants

1. Every forecast at close `t` uses no return after `t`.
2. The final executed book is the object compared with the ceiling.
3. A risk repair is proportional, scale-down-only, and no larger than needed.
4. Risk compliance outranks the no-trade band but does not alter signal intent.
5. Portfolio and RL call the same Core decision primitive.
6. Available executed breaches fail fixed evaluation.
7. Compliance never enters candidate selection or live-trading authority.

## Change checklist

- Prove prefix causality and exact quadratic forecast reconciliation.
- Test safe no-trade, risk-only override, unavailable history, and legacy
  mandate behavior.
- Reconcile every redundant RunResult, report, daily, decision, and RL action
  field before projection.
- Update CLI, Reports, Dossiers, Studio, schemas, templates, and wheel assets
  together.
- Run repository-required documentation and full test suites.
