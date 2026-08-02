# Factor evidence-to-Report handoff

- Status: `active`
- Target release: `0.9.31`
- Updated: `2026-08-02`
- Related design: [[docs/design/factor-evidence-explorer]],
  [[docs/design/agent-operator-experience]], and
  [[docs/design/run-bound-research-reports]].

## Outcome

Let a fresh coding Agent interpret a temporal Factor result and move from the
verified leader evidence to an immutable Report without mistaking protocol-null
quantiles for failed science, overlooking a material train/validation contrast,
or manually reconstructing strict Report evidence identities.

## Context

The clean installed-build NVDA forward-risk trial for `0.9.30` completed one
correct Factor-only workflow, but its canonical Project
`framework-needs.md` recorded three concrete handoff costs. The Factor Explorer
returned nine null quantile summary rows even though the immutable Factor
report already declared temporal tertiles unavailable. The compact Work Brief
correctly froze the positive validation result but did not expose the primary
train IC beside it. Finally, the worker copied the generic Report schema and
manually replaced the leader Run and artifact identities before publication.

These are one boundary: a verified Factor result must say which diagnostics
apply, surface material split tension without changing selection authority,
and offer a safe transition into Agent-authored interpretation.

## Scope

### In scope

- Project a strict quantile-evidence status from the already immutable Factor
  protocol, including an explicit temporal reason and artifact row count.
- Make CLI and Studio render protocol-unavailable temporal quantiles as such,
  rather than as generic empty evidence.
- Add one validation-only visibility contrast when the current Factor leader's
  primary train/validation mean rank-IC gap meets a fixed disclosed threshold.
- Add optional `aq report draft` for Session and direct-Run anchors. It writes
  a confined, non-overwriting, schema-valid authoring draft with the exact
  leader Run and all declared Run artifact paths.
- Give Report analysis an explicit optional authoring state. Historical
  analyses remain readable; publication rejects `draft` state and reserved
  placeholder prose until the Agent deliberately completes it.
- Expose the draft command through capabilities, Work Brief supporting action,
  CLI/Studio guidance, operator docs, and deterministic tests.
- Prove the finished candidate with a fresh installed-build Grok assignment.

### Out of scope

- Automatic Report prose generation, evidence interpretation, confidence
  selection, recommendations, or OpenAlice delivery.
- New temporal binning, one-asset pseudo-tertiles, or changing any Factor
  objective, qualification, test, Portfolio, RL, or trading authority.
- Treating train/validation divergence as a rejection threshold or selection
  rule.
- Rewriting historical immutable Runs or Reports.

## Acceptance

- [ ] Cross-sectional Factor evidence declares fixed tertiles available;
  single-asset and two-asset temporal evidence declares
  `protocol-unavailable` with a stable reason, zero artifact rows, and no
  fabricated group values.
- [ ] Factor CLI and Studio show that exact availability contract and prevent
  a temporal Quantiles tab from looking like a missing-data failure.
- [ ] The Agent Work Brief contains a nullable strict Factor split contrast;
  it appears only at or above the disclosed absolute `0.20` rank-IC gap,
  identifies the exact Run/horizon/values, and states that validation remains
  the sole selection split.
- [ ] Ordinary terminal output and Studio show the same material contrast
  without using it as a gate, verdict, or test claim.
- [ ] `aq report draft` supports exactly one Session or direct-Run anchor,
  writes only a new confined Project-local file, pre-fills the exact leader
  Run and declared artifact paths, and refuses overwrite, escape, stale,
  unreportable, or ambiguous anchors.
- [ ] The emitted object validates against the public Report-analysis schema
  as `authoringState: draft`; all publication APIs reject it until the state
  and reserved placeholders are completed, while historical analyses without
  the optional field remain readable.
- [ ] Capability/schema discovery, Work Brief actions, CLI, Studio, operator
  guidance, templates where relevant, and design documents agree.
- [ ] Focused tests, documentation links, complete unit tests, build/install
  identity smoke, clean-clone Workspace smoke, and one fresh Grok trial pass
  before `v0.9.31` is tagged and pushed.

## Work

- [x] Reproduce and trace the three canonical field-trial needs to immutable
  Factor semantics, Work Brief construction, and Report publication.
- [ ] Implement the Factor quantile and split-contrast read contracts.
- [ ] Implement safe Report draft materialization and publication guards.
- [ ] Update CLI, Studio, capabilities, schemas, templates, and durable docs.
- [ ] Run focused verification and one isolated installed-build Grok trial.
- [ ] Complete the release audit, version bump, final artifact replay,
  annotated tag, and canonical push.

## Findings and decisions

- 2026-08-02 — The temporal Judge already records
  `unavailable-for-temporal-evaluation-v1`; no Run or Judge regeneration is
  needed. The missing product behavior is a verified read-model label.
- 2026-08-02 — The fixed visibility threshold is absolute primary-horizon
  train/validation mean rank-IC gap `0.20`. It changes orientation only; it is
  not a qualification, promotion, or admission threshold.
- 2026-08-02 — Blank strings cannot satisfy the existing strict Report
  schema. A safe scaffold therefore uses unmistakable non-empty placeholders
  plus `authoringState: draft`; publication rejects both until the Agent
  explicitly completes them. This is safer than creating an accidentally
  publishable generic Report.

## Verification

- Pending.

## Progress log

- 2026-08-02 — Plan activated from clean published `v0.9.30` using the exact
  three needs recorded by the isolated NVDA forward-risk coworker.

## Completion

Pending.
