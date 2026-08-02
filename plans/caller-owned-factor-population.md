# Caller-owned Factor population

- Status: `active`
- Target release: `0.9.30`
- Updated: `2026-08-02`
- Related design: [[docs/design/caller-owned-factor-outcomes]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/ohlcv-factor-lab]],
  [[docs/design/cross-study-factor-dependencies]], and
  [[docs/design/research-intake-and-dataset-snapshots]].

## Outcome

Make Factor evaluation population an explicit caller-owned, content-locked
contract that is independent of Portfolio construction authority. A standalone
Factor Project must be able to predict future return or risk without
materializing a Portfolio Mandate, while Portfolio and governed RL must bind
and reconcile both the Factor population and their separately authorized
position mandate.

## Context

The final `0.9.28` forward-risk field trial correctly stopped after Factor
evidence, but its standalone `ohlcv-factor-lab` still contained
`strategies/portfolio-mandate.json`. Core also derived a `decision-signal`
prediction population from that mandate's `tradableAssets` and projected
position roles into Factor evidence. The file says it has no trading authority,
yet its name and construction fields imply a position decision that risk-only
research explicitly does not possess.

Prediction eligibility and position eligibility often coincide for a return
research desk, but they are different authorities. Continuing to derive one
from the other makes Factor-only work harder for Agents to interpret and makes
future non-return outcomes inherit accidental Portfolio semantics.

## Scope

### In scope

- Add strict caller-owned `factorPolicy.predictionAssets` for
  `decision-signal` requests and derive full-universe populations for
  `novel-factor` and `known-style-validation` claims.
- Materialize one content-addressed `strategies/factor-population.json` with
  research, prediction, and context assets, evaluation mode, Factor-only
  roles, relative-value contrast when applicable, and explicit no-Portfolio /
  no-trading authority.
- Make every Factor Study bind that manifest and make the Factor Judge,
  preflight, Explorer, CLI, Studio, Reports, and schemas consume the same
  contract without Portfolio position fields.
- Stop standalone `ohlcv-factor-lab` construction and validation from writing
  or requiring `portfolio-mandate.json`.
- Keep Portfolio and governed-RL Studies dependent on their separately derived
  mandate. A decision-signal mandate must match the Factor prediction assets;
  a complete-universe novel/known-style Factor may feed a mandate subset.
- Replace observed-only V5/V6 temporal target selection based on
  `positionRole` with the Factor population authority.
- Migrate current templates, checked-in sample state, tests, and public
  documentation to the new pre-1.0 contract while retaining immutable
  historical Runs byte-for-byte.
- Prove the Agent experience with a fresh installed-build Grok assignment that
  includes prediction and context assets and demonstrates that Factor-only
  evidence contains no Portfolio Mandate.

### Out of scope

- Automatic migration of arbitrary historical Workspaces or an `aq upgrade`
  command.
- New prediction outcomes, arbitrary weighted multi-asset contrasts, or
  three-asset relative baskets.
- Consuming risk forecasts inside Portfolio or governed RL.
- Order, Broker, TPSL, live-account, or trading authority.
- Compact Factor Explorer output; that separate field-trial need remains a
  candidate for a later patch.

## Acceptance

- [ ] A normalized `decision-signal` request names unique requested
  `predictionAssets`; missing, duplicate, unrequested, unsupported-size, or
  outcome-incompatible populations fail before Project construction.
- [ ] Novel-factor and known-style claims deterministically use the complete
  research universe and cannot smuggle in a narrower prediction population.
- [ ] Every new Factor Study binds a strict, content-addressed Factor
  Population whose metrics and read models contain Factor roles and explicit
  evaluation-only authority, never Portfolio position roles.
- [ ] A standalone Factor Lab creates, validates, runs, reports, and appears in
  Studio without any `portfolio-mandate.json`.
- [ ] Portfolio and governed RL independently require a forward-return Factor
  Population plus a compatible Portfolio Mandate; tampering either dependency
  fails deterministically.
- [ ] Observed-only temporal intake takes its target clock from the explicit
  Factor population rather than from position permission.
- [ ] CLI schema/capability discovery, Project format, operator/Agent guidance,
  architecture/design documentation, templates, and sample state agree on one
  authority boundary.
- [ ] Existing immutable sample Runs are not rewritten or relabelled; any new
  checked-in evidence records its true candidate Harness identity.
- [ ] Focused tests, documentation links, complete unit tests, build/install
  identity smoke, clean-clone Workspace smoke, and a fresh Grok field trial all
  pass before `v0.9.30` is tagged and pushed.

## Work

- [x] Reproduce the field-trial confusion and audit every current population /
  mandate consumer.
- [x] Implement and test request normalization plus the strict Factor
  Population builder, loader, validator, schema, and compatibility check.
- [x] Rewire intake, templates, Judges, preflight, read models, CLI, Studio,
  Reports, and program orchestration to the separated authorities.
- [x] Migrate the current sample/template source and update durable design and
  operator documentation.
- [ ] Build the candidate and run one isolated fresh Grok assignment.
- [ ] Complete the release audit, version bump, final artifact rebuild,
  annotated tag, and canonical push.

## Findings and decisions

- 2026-08-02 — The `0.9.28` forward-risk worker recorded that standalone
  Factor intake still emitted a full Portfolio Mandate and used its tradable
  assets as prediction authority. This is observed research friction, not a
  speculative feature request.
- 2026-08-02 — Chosen boundary: `factorPolicy.predictionAssets` owns a
  decision-signal population; `factor-population.json` owns fixed evaluation
  semantics; `portfolio-mandate.json` alone owns position construction. A
  return-oriented Research Desk binds both and proves compatibility instead of
  deriving either authority from the other.
- 2026-08-02 — A two-asset Factor population is an ordered caller-owned
  relative-value contrast and is supported only for forward return. The
  separate Portfolio Mandate must still prove symmetric two-sided
  dollar-neutral construction before monetization.
- 2026-08-02 — Pre-1.0 callers must adopt the explicit field for new
  decision-signal intake. Historical immutable evidence is preserved, but no
  compatibility fallback will keep position roles as current Factor authority.
- 2026-08-02 — Compatibility is intentionally claim-aware. A decision-signal
  population is the exact caller-selected decision surface and therefore must
  equal Mandate tradable assets. Novel/known-style evaluation covers the full
  universe, so downstream Portfolio authorization may conservatively select a
  subset without changing what the Factor claim evaluated.

## Verification

- Request/schema/population unit tests and the focused intake, Factor,
  Portfolio, Research Program, CLI, and Studio suite exercised 136 tests. The
  only two failures were the intentional sample-currentness gap after replacing
  current Study dependencies while preserving all 17 historical Runs.
- Fresh-template parity, documentation links, Factor Population schema
  discovery, Python compilation, sample validation, and program projection
  pass. Candidate sample Runs, full-suite/build/install checks, and the fresh
  Grok trial remain pending.

## Progress log

- 2026-08-02 — Plan created from clean published `v0.9.29` after tracing the
  request, template, intake, Judge, preflight, Explorer, Portfolio, RL, sample,
  CLI, Studio, and documentation surfaces that currently share the Mandate.
- 2026-08-02 — Implemented the strict Factor Population contract across request
  normalization, template construction, intake reload, Judges, preflight,
  Explorers, schemas, CLI/Studio projections, sample source, and durable docs.
  Historical sample Runs remain byte-for-byte untouched and are correctly
  stale until candidate evidence is generated.

## Completion

Pending.
