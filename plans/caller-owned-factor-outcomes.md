# Caller-owned Factor outcomes

- Status: `completed`
- Updated: `2026-08-02`
- Target release: `0.9.28`
- Related design: [[docs/design/ohlcv-factor-lab]],
  [[docs/design/caller-owned-factor-outcomes]],
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

- [x] A strict caller request can select either supported outcome, and invalid
  or misplaced outcome authority fails before Project construction with a
  precise diagnostic.
- [x] Deterministic unit evidence proves exact forward realized-volatility
  alignment, complete-window missingness, horizon-specific purge, temporal and
  cross-sectional evaluation, and no target leakage into style selection or
  neutralization.
- [x] New Runs bind and disclose one outcome consistently across metrics,
  artifacts, Explorer, Report/Dossier support, CLI, Studio, schemas,
  capabilities, templates, and Agent instructions.
- [x] A positive risk forecast stops further in-sample tuning but cannot open
  Portfolio or RL gates; a return outcome retains the existing monetization
  route unchanged.
- [x] Existing checked-in sample evidence validates and projects without
  mutation under its implicit historical forward-return identity.
- [x] A fresh installed-wheel Grok coworker can construct, execute, inspect,
  and report one bounded risk-forecast Study without private Core inspection
  or a framework workaround.
- [x] Focused tests, full regression, documentation links, build, installed
  smoke, clean-clone smoke, and remote branch/tag identity pass for `v0.9.28`.

## Work

- [x] Add the strict request/claim outcome contract and intake compatibility
  gates.
- [x] Generalize the fixed Factor target panels, evidence vocabulary, and
  independent Explorer reconciliation around one bound outcome.
- [x] Complete downstream gate, agenda, Report/Dossier, CLI, Studio, schema,
  template, Skill, and design-document parity.
- [x] Run focused deterministic tests and a fresh installed-wheel Grok field
  assignment; repair reusable Agent friction only.
- [x] Advance version and release records, run the complete audit, publish the
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

- Deterministic numerical and end-to-end Factor tests cover complete-window
  realized-volatility alignment, temporal missingness, cross-sectional risk
  scoring, immutable Explorer reconciliation, the risk-positive terminal
  stage, withheld Portfolio/RL authority, agenda, decision support, CLI data,
  and Studio projection.
- The first cross-surface regression ran 144 tests in 547.165 seconds. 143
  passed; the sole expected fixture failure showed that syncing the current
  sample Judge makes its latest older Factor Run stale. The sample must receive
  a truthful new clean-Harness Run rather than weakening the consistency gate
  or relabeling old evidence.
- Python compilation, Studio JavaScript syntax, diff checks, and all 1,489
  documentation links pass at the implementation checkpoint.
- The first installed `0.9.28` wheel field trial used clean embedded commit
  `c9ee7e2`, one five-asset synthetic risk request, and a fresh no-memory,
  no-web, no-subagent Grok coworker. It completed in 18 turns with exactly one
  Run, zero Experiments, one Report, and one completed Session. Validation
  mean rank IC was `0.3269841269841269` with HAC t-statistic
  `3.4507542068719874`; the coworker froze the positive risk forecast and did
  not open Portfolio or RL work.
- The same trial exposed one reusable orientation contradiction: the verified
  agenda said `no-further-in-sample-tuning`, while an active baseline Session
  still rendered `CANDIDATE EDIT REQUIRED` because its worktree was technically
  writable. The candidate now routes this exact `risk-forecast-positive` state
  to baseline-bound Report publication and Session completion. A fresh wheel
  replay remains required before release.
- The final fresh retry used wheel SHA-256
  `95f38406e0d98cf90201d60c116f6bc4b3590d7d2efabe455c702e1e426d6986`
  from clean embedded commit `8a5a9a2`. Grok session
  `019fbfeb-bd0c-7862-b242-48c7c83419bc` again completed in 18 turns with one
  Run, zero Experiments, one Report, and one completed Session. Its distinct
  predeclared vol/range candidate reached validation mean rank IC
  `0.3523029083645743`, HAC t-statistic `4.294484681552545`, and positive
  validation folds. Post-Run orientation returned
  `risk-forecast-report-required` with primary `report.publish`; no candidate-
  edit-required label occurred. Independent `verify_field.py` passed against
  immutable evidence, public CLI loaders, Studio, transcript, and exact hashes.
- Final static and regression gate: `uv lock --check`, Python compilation,
  Studio JavaScript syntax, `git diff --check`, and all 1,490 documentation
  links pass. The complete suite passed all 446 tests in 1090.966 seconds,
  including legacy immutable evidence, return Factor-to-Portfolio/RL paths,
  every intake surface, Reports/Reviews/Dossiers, Studio, Workspace Skills,
  package provenance, and the new risk-outcome stop state.
- The clean final code-candidate build embedded commit `26cd9aa` with
  `dirty=false`
  and source hash
  `3446f2f67f1a7ab3c43cae42e3e62aff66155522e670209b89827fc5764cbc63`.
  A fresh Python environment installed the resulting wheel, discovered
  `0.9.28`, all 58 commands, both request outcomes, and the outcome-aware
  diagnostics schema. Final pre-publication artifact SHA-256 values were
  `9a928e9202b2ef117c3b83d37c244e2a52b14f0f1b2c03c233233ded2531e82f`
  for the wheel and
  `8fb9799322d9d94c3d8949fe7b7eed0d9d008d3767457500412c9d2681f68d19`
  for the sdist.
- A no-hardlink clean clone at commit `26cd9aa` had no local override, selected
  `sample-research-desk` through the checked-in Workspace manifest, and passed
  `orient`, `validate`, `project list`, and `studio snapshot` using the fresh
  installed wheel. Studio independently projected three Studies, seventeen
  immutable Runs, the historical implicit `forward-return` Factor outcome,
  and the Portfolio Explorer from a clean Git worktree.

## Progress log

- 2026-08-02 — Plan activated from clean released `v0.9.27` after auditing
  unresolved framework-needs records and confirming that earlier candidate
  gaps had already been repaired. The hard-coded future-return target remains
  a current executable limitation.
- 2026-08-02 — Implemented caller-bound return/risk outcome contracts across
  intake, fixed evaluation, immutable evidence, independent read models,
  downstream admission, agent surfaces, and documentation. Historical claims
  remain byte-for-byte implicit return identities. Template synchronization
  correctly made the sample's latest older run stale; the next checkpoint is a
  clean-Harness sample replay before installed-wheel field work.
- 2026-08-02 — Refreshed the sample with truthful clean `0.9.27` Factor and
  Portfolio Runs, prepared the `0.9.28` candidate, and completed the first
  installed-wheel Grok risk assignment. The research path succeeded, but its
  durable `framework-needs.md` identified conflicting post-qualification
  orientation. Repaired that reusable stop-state guidance and added a
  deterministic active-Session regression rather than accepting manual Agent
  interpretation as the product contract.
- 2026-08-02 — Final installed-wheel retry independently followed the repaired
  report-and-complete route without any post-test candidate edit. It recorded
  three non-blocking future considerations: an append-only Session research
  log, clearer Factor-only prediction-universe naming than the shared mandate,
  and a compact Factor Explorer projection. The first is an intentional
  evidence-lifecycle tradeoff, the second needs a separate authority design,
  and the third is useful Agent ergonomics for a later patch; none weakens or
  changes this release's verified outcome contract.
- 2026-08-02 — Complete 446-test regression and all static/documentation gates
  passed after the field-trial repair. Clean build/install and root Workspace
  clean-clone verification then passed with exact distribution provenance.
  The final release commit was published as `v0.9.28`, with the remote branch
  and annotated tag verified against the same immutable commit.

## Completion

Completed on 2026-08-02. AutoQuant now evaluates a Factor against the caller's
bound return or realized-risk outcome, preserves historical implicit-return
evidence, and stops a positive risk forecast at a truthful standalone handoff.
Two fresh installed-wheel Grok coworkers completed the new route; the second
proved the repaired terminal orientation without post-test tuning. The full
regression, documentation, distribution, installed-runtime, clean-clone, and
publication gates passed for `v0.9.28`.
