# Caller-owned Factor outcomes

- Status: `active`
- Updated: `2026-08-02`
- Target release: `0.9.28`
- Related design: [[docs/design/ohlcv-factor-lab]],
  [[docs/design/factor-diagnostics]],
  [[docs/design/factor-qualification-funnel]], and
  [[docs/design/cross-study-factor-dependencies]].

## Outcome

Let a delegated Factor question bind the behavior it is trying to predict
instead of silently converting every OHLCV hypothesis into future return.
The first additional outcome is fixed forward realized volatility: a coding
Agent can investigate whether causal price/volume information predicts future
risk, receive the same purged validation, fold, HAC, component, artifact, CLI,
and Studio evidence as a return Factor, and hand off a truthful risk-model
conclusion without manufacturing Portfolio, RL, or trading authority.

## Context

Factor Lab currently hard-codes every target panel to close-to-close forward
return. That is correct for alpha and target-weight research but cannot express
a normal quantitative question such as “which causal OHLCV features predict
next-month cross-sectional realized volatility?” An Agent can write a trailing
volatility factor, but the fixed Judge will still score it against future
return and describe quantile values as returns. The workbench therefore
misstates the research question before candidate quality is considered.

Most of the scientific machinery is target-agnostic: fixed chronological
60/20/20 partitions, horizon-specific purge, rank/Pearson association,
dependence-aware inference, chronological folds, causal regimes, style overlap,
component ablation, and visible-test discipline all remain useful. Portfolio
and governed RL are not target-agnostic: they currently interpret factor rank
as expected-return conviction. This release reuses the former while explicitly
refusing to grant the latter meaning to a risk forecast.

## Scope

### In scope

- Extend caller `factorPolicy` with an explicit outcome chosen from
  `forward-return` and `forward-realized-volatility`; omission in preserved
  historical requests and claims continues to mean forward return.
- Define horizon `h` forward realized volatility at signal close `t` as the
  unannualized square root of the sum of squared close-to-close log returns for
  the next `h` observed base bars, from `t -> t+1` through `t+h-1 -> t+h`.
  Every constituent return must be finite; there is no fill or annualization.
- Support the risk outcome for one request-bound temporal prediction asset and
  four-or-more-asset cross-sectional prediction populations.
- Preserve positive score direction: a larger factor value predicts a larger
  future outcome. For the risk outcome this means higher future realized risk,
  not higher expected return.
- Carry exact outcome identity and semantics through the fixed claim, Judge,
  immutable Run metrics/artifacts, Explorer verification, Reports/Dossiers,
  research agenda, CLI JSON/human output, Studio, schemas, capabilities,
  templates, Skills, and documentation.
- Make a scientifically positive risk forecast terminal for in-sample Factor
  work while explicitly withholding Factor-to-Portfolio and Factor-to-RL
  admission.
- Preserve existing immutable return Runs under their recorded contract and
  derive their implicit outcome only in read models; do not rewrite history.
- Prove the route with a fresh installed-wheel Grok coworker given a fixed
  risk-forecast request and OHLCV package but no repository-internal coaching.

### Out of scope

- A universal target expression language, arbitrary labels, supervised-ML
  dataset API, custom loss functions, or caller-supplied target code.
- Annualized volatility, volatility scaling across frequencies, implied
  volatility, covariance, beta, drawdown, tail loss, or event labels.
- Two-asset relative-value risk contrasts, three-asset baskets, or custom
  contrast weights.
- Treating high predicted risk as a long/short return signal, automatically
  inverting it, building target weights, admitting governed RL, or creating
  Broker, Order, TP/SL, or trading authority.
- Rewriting historical Runs, changing OpenAlice's pinned `0.8.31` desk, or
  adding a Workspace upgrade framework.

## Acceptance

- [ ] A strict caller request can select either supported outcome, and invalid
  or misplaced outcome authority fails before Project construction with a
  precise diagnostic.
- [ ] Deterministic unit evidence proves exact forward realized-volatility
  alignment, complete-window missingness, horizon-specific purge, temporal and
  cross-sectional evaluation, and no target leakage into style selection or
  neutralization.
- [ ] New Runs bind and disclose one outcome consistently across metrics,
  artifacts, Explorer, Report/Dossier support, CLI, Studio, schemas,
  capabilities, templates, and Agent instructions.
- [ ] A positive risk forecast stops further in-sample tuning but cannot open
  Portfolio or RL gates; a return outcome retains the existing monetization
  route unchanged.
- [ ] Existing checked-in sample evidence validates and projects without
  mutation under its implicit historical forward-return identity.
- [ ] A fresh installed-wheel Grok coworker can construct, execute, inspect,
  and report one bounded risk-forecast Study without private Core inspection
  or a framework workaround.
- [ ] Focused tests, full regression, documentation links, build, installed
  smoke, clean-clone smoke, and remote branch/tag identity pass for `v0.9.28`.

## Work

- [ ] Add the strict request/claim outcome contract and intake compatibility
  gates.
- [ ] Generalize the fixed Factor target panels, evidence vocabulary, and
  independent Explorer reconciliation around one bound outcome.
- [ ] Complete downstream gate, agenda, Report/Dossier, CLI, Studio, schema,
  template, Skill, and design-document parity.
- [ ] Run focused deterministic tests and a fresh installed-wheel Grok field
  assignment; repair reusable Agent friction only.
- [ ] Advance version and release records, run the complete audit, publish the
  commit/tag, and verify remote identity.

## Findings and decisions

- 2026-08-02 — The gap is not missing factor expressiveness: an Agent can
  already author trailing volatility, range, and volume features. The missing
  authority is the fixed Judge's outcome, which remains future return
  regardless of the caller's question.
- 2026-08-02 — Use standard unannualized realized volatility from squared log
  returns. Rank association does not need an annualization convention, and
  omitting one avoids fabricating a market calendar or bar-frequency scale.
- 2026-08-02 — Risk prediction reuses the Factor evidence funnel but not the
  return-to-weight bridge. Supporting risk inside Portfolio/RL before defining
  a risk-budget consumption contract would silently assign the wrong economic
  sign.
- 2026-08-02 — Historical requests and immutable claims without an outcome
  remain exactly as stored and are read as forward return. New risk research
  must state the outcome explicitly; evidence is never rewritten merely to
  look current.

## Verification

Pending.

## Progress log

- 2026-08-02 — Plan activated from clean released `v0.9.27` after auditing
  unresolved framework-needs records and confirming that earlier candidate
  gaps had already been repaired. The hard-coded future-return target remains
  a current executable limitation.

## Completion

Pending.
