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

- [x] Cross-sectional Factor evidence declares fixed tertiles available;
  single-asset and two-asset temporal evidence declares
  `protocol-unavailable` with a stable reason, zero artifact rows, and no
  fabricated group values.
- [x] Factor CLI and Studio show that exact availability contract and prevent
  a temporal Quantiles tab from looking like a missing-data failure.
- [x] The Agent Work Brief contains a nullable strict Factor split contrast;
  it appears only at or above the disclosed absolute `0.20` rank-IC gap,
  identifies the exact Run/horizon/values, and states that validation remains
  the sole selection split.
- [x] Ordinary terminal output and Studio show the same material contrast
  without using it as a gate, verdict, or test claim.
- [x] `aq report draft` supports exactly one Session or direct-Run anchor,
  writes only a new confined Project-local file, pre-fills the exact leader
  Run and declared artifact paths, and refuses overwrite, escape, stale,
  unreportable, or ambiguous anchors.
- [x] The emitted object validates against the public Report-analysis schema
  as `authoringState: draft`; all publication APIs reject it until the state
  and reserved placeholders are completed, while historical analyses without
  the optional field remain readable.
- [x] Capability/schema discovery, Work Brief actions, CLI, Studio, operator
  guidance, templates where relevant, and design documents agree.
- [ ] Focused tests, documentation links, complete unit tests, build/install
  identity smoke, clean-clone Workspace smoke, and one fresh Grok trial pass
  before `v0.9.31` is tagged and pushed.

## Work

- [x] Reproduce and trace the three canonical field-trial needs to immutable
  Factor semantics, Work Brief construction, and Report publication.
- [x] Implement the Factor quantile and split-contrast read contracts.
- [x] Implement safe Report draft materialization and publication guards.
- [x] Update CLI, Studio, capabilities, schemas, Agent guidance, and durable
  docs; no Project template carries a duplicated Report workflow.
- [x] Run focused verification and one isolated installed-build Grok trial.
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

- Focused Core/CLI/Studio/documentation suites passed across every changed
  path. JavaScript syntax, Python compilation, diff hygiene, and all
  1,551 documentation links pass.
- The complete candidate source suite passed all 454 tests in 1,202.824
  seconds.
- Clean candidate commit `170d53b` built wheel
  `3a3524046e34e83167e81e484c38dbac63cceabe42bb8888f85618125c78994e`
  and sdist
  `b0e404a5ec2b9d3d61c7c23b5771f3abb4858492e4b9b1bdc400a3f94f90a133`.
  The isolated Python 3.11 install reported embedded, clean commit
  `170d53b0b515e588b5169f0bcea9c24811c7bbdf` and source hash
  `4c010b8d888052dd864a122797694670ba8ecc3bf1a70d5501d34ae98c9ffade`.
- Fresh no-memory/no-web/no-subagent Grok `4.5` high reasoning completed the
  uncoached field assignment at
  `/Users/ame/2607AutoQuant/grok-field-trials/cohort-46-factor-handoff-v0931-candidate`.
  It independently discovered `aq report draft` from public surfaces,
  generated all six exact prefilled Run artifact references and cited exact
  subsets in its final analysis, interpreted temporal
  quantiles as `protocol-unavailable`, surfaced train IC `-0.1072916034`
  versus validation IC `0.1744431644` and absolute gap `0.2817347678`,
  published Report `report-20260802T044639997251Z-17eb26bf2441`, and completed
  Session `session-20260802T044527696066Z-f6687bd76ab3` with one Run, zero
  Experiments, one Report, no Portfolio Mandate, and no new Workbench need.
- Independent `verify_field.py` replay accepted the immutable Project, exact
  evidence, installed identity, command counts, transcript restrictions,
  draft/final publication boundary, final orientation, and Studio snapshot.
  Assignment, transcript, and event hashes are respectively
  `828a6e1d5b521263c5697bfc16e51903a1b5ebe3e67e7cc5b3ea3b712023aaa3`,
  `9a4d2f29c8a7675c197a87c30f74f53823bade49666836e9bc9a444d915a3026`,
  and `7f1f24642808c1e6c1efca612179bd5da8bd248d9134e5cdc01bbb2351751853`.

## Progress log

- 2026-08-02 — Plan activated from clean published `v0.9.30` using the exact
  three needs recorded by the isolated NVDA forward-risk coworker.
- 2026-08-02 — Core, CLI, capability, Studio, schema, and publication guards
  now implement the three handoff contracts. Focused Report, orientation,
  Factor, intake, and CLI suites pass 130 tests; durable documentation and the
  installed-build coworker trial remain.
- 2026-08-02 — Repository audit confirmed that version policy already has one
  dedicated authority in [[docs/design/versioning-and-release]], AGENTS routes
  there without duplicating the procedure, and README has an enforced
  220-line entrance budget. This release will preserve that boundary rather
  than adding another release section to README.
- 2026-08-02 — The owning Factor, Agent-experience, Report, CLI, Operator, and
  Studio documents now describe the candidate contract. Documentation links,
  JavaScript syntax, 58 cross-surface tests, and two exact temporal/report
  regressions pass; README remains unchanged at 154 lines.
- 2026-08-02 — The isolated cohort 46 coworker completed the entire assignment
  without retries or framework-needs. The research result was correctly
  negative rather than cosmetically positive: validation HAC and one fixed
  fold were weak, so the worker stopped after one Run while still using every
  new evidence-to-Report handoff surface correctly.

## Completion

Pending.
