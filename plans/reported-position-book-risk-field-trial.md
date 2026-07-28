# Reported-position Book Risk field trial

- Status: `active`
- Updated: `2026-07-28`
- Design: [[docs/design/reported-position-book-risk]]
- Field matrix: [[docs/trading-request-field-trials]]

## Outcome

Prove that AutoQuant can receive a caller-supplied existing-book question,
preserve the difference between reported holdings and model targets, and
return useful crowding and reduction-sensitivity evidence without claiming
live account or execution authority.

## Acceptance

- [x] The strict request can carry one funded reported or hypothetical weight
  snapshot with timestamp and provenance.
- [x] A dedicated fixed Lab uses content-locked closed OHLCV and does not
  disguise the snapshot as a Factor or Portfolio target.
- [x] RunResult and a strict Explorer reconcile covariance, component risk,
  effective bets, PCA crowding, pair correlations, standardized reductions,
  and rolling evidence.
- [x] Agent orientation closes the descriptive audit without inventing an
  iterative research agenda.
- [x] Studio exposes the same immutable evidence and authority boundary.
- [x] AutoQuant `0.6.0` passes full regression and package installation smoke.
- [ ] A clean-commit Yahoo field Run reproduces the AAPL/MSFT/NVDA/QQQ
  conclusion and is recorded in the field-trial matrix.
- [ ] Implementation and field evidence are committed and pushed.

## Work

- [x] Add `request.positionSnapshot` normalization and request/dataset checks.
- [x] Add the derived position-snapshot dependency and Book Risk template.
- [x] Add the fixed Judge, artifacts, strict Explorer, CLI, orientation, and
  Studio lane.
- [x] Add deterministic success and adversarial cross-artifact tests.
- [x] Verify the Studio page with an executable synthetic Project.
- [x] Complete full tests, source/wheel build, and fresh-wheel Run smoke.
- [ ] Commit and push the `0.6.0` implementation.
- [ ] Recreate and run the real Yahoo Project from the clean commit.
- [ ] Record the final evidence and close this plan.

## Findings

- 2026-07-28 — Existing Portfolio Explorer evidence is model-target evidence
  and cannot answer a current-holdings question without changing its meaning.
- 2026-07-28 — One external-reported, unauthenticated weight snapshot is the
  minimum useful boundary. AutoQuant can bind and audit it while OpenAlice/UTA
  retains live account truth.
- 2026-07-28 — A first real dirty Run found 3.153 effective risk bets across
  four holdings, a 50.95% first-PC share, NVDA at 46.62% of absolute component
  risk, and NVDA/QQQ correlation of 0.692. NVDA ranked first for a standardized
  one-percentage-point reduction. This must be reproduced from clean `0.6.0`
  before becoming release evidence.
- 2026-07-28 — The first Studio render exposed contradictory sidebar state:
  the Book Risk Run was visible in the evidence lane but absent from current
  context because old focus selection required Factor/Portfolio/RL metric
  layers. The descriptive Run is now a first-class focus Run.
- 2026-07-28 — A completed descriptive audit must not say
  `waiting-evidence` or propose candidate optimization. Orientation now emits
  an explicit closed descriptive agenda with no selection or trading
  authority.
- 2026-07-28 — Clean-Project preparation exposed a lifecycle contradiction:
  intake advertised `ready-for-session` and returned `session.start`, while
  Core correctly rejects Sessions for this descriptive Lab. Book Risk intake
  now records `ready-for-run`; CLI and Studio expose only the fixed
  `run.execute` route. The preserved
  `us-megacap-book-crowding-v060` Project remains the failure reproduction.

## Verification

- Targeted Book Risk, orientation, research-agenda, Studio, CLI, and Workspace
  tests pass.
- `node --check autoquant/studio_assets/studio.js` passes.
- An executable synthetic Project produced a successful Book Risk Run in
  272 ms; the browser render showed the complete evidence lane with no console
  errors after the current-Run focus repair.
- Full regression passed all 247 tests in 1,503.679 seconds.
- AutoQuant `0.6.0` source and wheel distributions built successfully. A
  fresh Python 3.11 wheel environment discovered `run.book-risk`, created the
  synthetic Lab, executed a successful Run, and reported `dirty: false`.
