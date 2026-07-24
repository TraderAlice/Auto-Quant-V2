# Governed Factor-to-RL fusion

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/cross-study-factor-dependencies]] and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

The governed RL Study consumes the current Project candidate factor through a
read-only, content-locked dependency instead of operating only on unrelated
reference sleeves. Every Run can prove which factor bytes it used and whether
adaptive switching added validation value beyond simply holding that factor.

## Context

The multi-Study Research Desk coordinates Factor, Portfolio, and RL lanes, but
its first version explicitly leaves RL on fixed activity/intraday/reversal
sleeves. Physical colocation is not model integration. A real research desk
needs an exact causal and identity-preserving handoff from factor research into
the adaptive-policy challenge.

Putting `factors/**` in the RL editable closure would let one Session change
both the factor and representation, destroying attribution. Putting the factor
under `judge.paths` would falsely label research source as evaluator authority.
A distinct fixed dependency surface is required.

## Scope

### In scope

- Optional Study `dependencies.paths` with strict path confinement, hashes,
  Run freezing, execution materialization, Session locks, and stale detection.
- RL dependency on the `factors/**` source closure while `models/**` remains
  its only editable surface.
- Full candidate-factor API and prefix-causality audit inside the fixed RL
  Judge.
- A `candidate` factor sleeve available to fixed baselines, contextual ridge,
  and Q policy.
- Validation/test evidence for RL versus the candidate factor, candidate
  action usage, and exact dependency identity.
- Core CLI/Studio projections and Research Program integration/conflict state.
- Bounded deterministic tests and installed-wheel/browser verification.

### Out of scope

- Jointly optimizing the factor and RL encoder in one Session.
- Treating an upstream Factor Report as automatic model approval.
- Continuous actions, deep RL, live orders, or Broker/UTA integration.
- Cross-Project dependency registries.

## Acceptance

- [x] Existing Studies without dependencies preserve their manifests and
      identity behavior.
- [x] Changing one dependency byte changes Study/Run identity without changing
      the RL editable source hash.
- [x] Dependency files are available to the Judge but immutable inside an RL
      Session.
- [x] The RL Judge independently verifies factor API, purity, numeric shape,
      alignment, and prefix causality.
- [x] Candidate factor is one declared governed action and one fixed baseline.
- [x] Metrics reconcile RL lift versus the candidate factor and candidate
      action frequency across every fold/seed.
- [x] Research Program proves the RL dependency equals the current Factor
      source and detects unsafe concurrent editing.
- [x] CLI, Studio, schemas, docs, wheel, focused/full tests, and browser QA
      agree.

## Work

- [x] Audit existing Factor, Portfolio, RL, Study, Run, Session, and explorer
      boundaries.
- [x] Choose a read-only Study dependency rather than widening editable or
      Judge authority.
- [x] Implement dependency identity through Core lifecycle.
- [x] Integrate and audit the candidate factor in the RL environment.
- [x] Reconcile and project factor-fusion evidence.
- [x] Verify, document, commit, and push.

## Findings and decisions

- 2026-07-24 — Factor-to-RL integration is a source dependency, not a new
  evaluator and not an RL-editable input.
- 2026-07-24 — The adaptive claim must be challenged by a fixed candidate-only
  baseline; raw RL Sharpe is insufficient.
- 2026-07-24 — A changed factor invalidates existing RL evidence and active RL
  Session authority by exact hash, even when the model encoder is unchanged.
- 2026-07-24 — RL may consume current candidate bytes before an upstream Report
  exists, but the Research Program continues to recommend sequential Factor →
  Portfolio → RL evidence and discloses readiness separately.
- 2026-07-24 — RL binds `factors/**`, not only the entrypoint, so future helper
  modules remain part of the exact Factor-source/RL-dependency identity.
- 2026-07-24 — Old reference-only RL Runs remain readable as
  `legacy-reference-only`; only new candidate-fusion Runs make the stronger
  RL-versus-candidate claim.

## Verification

- `python -m unittest discover -s tests` — 122 tests passed in 249.977 seconds.
- Focused post-copy regression — 14 Research Program, RL, Explorer, Studio, and
  documentation tests passed in 103.290 seconds.
- `python scripts/check_doc_links.py` — 336 double-links resolved.
- `uv build --wheel` and an isolated 161-package wheel installation succeeded;
  packaged schemas, templates, and Studio assets were imported outside the
  repository checkout.
- An installed-wheel Research Desk produced three successful Runs. Core proved
  RL dependency hash equals Factor source hash, projected five actions,
  fourteen baselines, six fold/seed trials, and complete factor-fusion
  evidence.
- A real pre-fusion Run from commit `5bde9a7` loaded as
  `legacy-reference-only`.
- In-app browser QA covered program lanes, candidate-fusion cards, baseline
  ladder, Actions, Test audit, candidate legend, and zero console errors.

## Progress log

- 2026-07-24 — Activated after the multi-Study Research Desk made the missing
  causal artifact dependency explicit.
- 2026-07-24 — Completed the content-locked dependency lifecycle, governed
  candidate sleeve, evidence reconciliation, compatibility projection, and
  human/Agent observation surfaces.
