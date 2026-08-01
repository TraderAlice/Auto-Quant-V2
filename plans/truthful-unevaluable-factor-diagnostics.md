# Truthful unevaluable Factor diagnostics

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.21`
- Related design: [[docs/design/ohlcv-factor-lab]],
  [[docs/design/factor-diagnostics]],
  [[docs/design/ohlcv-price-event-study]], and
  [[docs/design/project-derived-workbench-needs]].

## Outcome

Make a Factor Run that cannot produce the fixed primary validation score fail
with a stable research diagnostic instead of a Python conversion exception or
an ambiguous generic population error. A fresh coworker should be able to tell
whether the fixed temporal evaluation has too few paired observations, no
candidate variation, or no target variation, and should route a conditional
price-event question to Event Study rather than treating a sparse binary event
indicator as an ordinary continuous Factor.

This release does not add event-selection semantics to Factor, reinterpret
missing scores as observed zero, or make a failed Run promotable evidence.

## Baseline evidence

Project-derived need `FN-2` in
`../quant-workspace/projects/nvda-gap-factor-route-repro/framework-needs.md`
preserves the original failure. Immutable Run
`run-20260728T172110652639Z-d0e06d7c91ac` encoded a fixed NVDA opening-gap
request as a sparse binary single-asset temporal candidate. Its validation
correlation was unavailable, after which the Judge executed `float(None)` and
reported `factor.exception: TypeError`.

The semantic event-study need from the same reproduction is already resolved:
`ohlcv-event-study-lab` owns event selection, delayed entry/exit alignment,
overlap, references, uncertainty, and the immutable event ledger. The remaining
Factor defect is diagnostic truthfulness, not missing event functionality.

## Public contract

- Before converting the primary temporal validation objective to a float,
  inspect the exact purged candidate/target population selected by Core.
- Return distinct stable failures for fewer than the fixed minimum paired
  observations, fewer than two finite candidate values, and fewer than two
  finite forward-return values.
- Name the evaluation mode, split, primary horizon, paired observations,
  distinct candidate values, distinct target values, and required minimum in
  the human-readable error.
- Preserve ordinary missing Factor values as unavailable observations; do not
  coerce them to zero or invent an eligibility mask.
- Keep visible test evidence non-selective. Primary validation is the required
  objective gate; train-only style qualification may retain its own explicit
  failure when the candidate cannot support that separate diagnostic.
- Document that a binary Factor still asks an association question. A caller
  asking for a frozen event population and conditional outcome distribution
  belongs in `ohlcv-event-study-lab`.

## Scope

### In scope

- Single-asset temporal and two-asset relative-value primary validation
  preflight.
- Stable error codes/messages, deterministic regression tests, and Agent-facing
  Factor/Event routing guidance.
- A bounded installed-wheel coworker trial that intentionally submits one
  unevaluable temporal candidate and leaves a truthful failed Run.

### Out of scope

- A sparse-event Factor API, candidate-defined eligibility mask, target-weight
  behavior on event dates, new event types, or Event Study changes.
- Turning failures into successful Runs with null objectives.
- Cross-sectional Factor redesign, Portfolio/RL changes, Orders/TPSL, OpenAlice
  pin changes, or Workspace migration.

## Acceptance

- [x] A temporal candidate with no validation variation fails with a stable
      candidate-variation code, exact population counts, and no `TypeError`.
- [x] A temporal candidate with too few finite validation pairs fails with a
      separate observation-count code.
- [x] A temporal target with no validation variation fails with a separate
      target-variation code.
- [x] The two-asset relative-value path receives the same exact preflight after
      Core constructs the authorized spread.
- [x] Existing evaluable Factor fixtures and successful Project Runs preserve
      their numerical objectives and evidence shape.
- [x] Public Agent guidance distinguishes association Factor questions from
      fixed conditional price-event questions without adding an event disguise
      to the candidate API.
- [x] A fresh installed-wheel coworker reaches and explains the intended
      structured failure without source inspection or framework repair.
- [ ] Focused/full tests, documentation links, lock/syntax, build/install,
      root Workspace, and clean-clone smokes pass before publication.

## Work

- [x] Audit the Project-derived reproduction and separate the already-resolved
      Event Study need from the remaining Factor diagnostic defect.
- [x] Add a fixed temporal primary-population preflight and regression fixtures.
- [x] Update durable Factor diagnostics and Agent-facing routing documentation.
- [x] Build an isolated `0.9.21` candidate and run a fresh-worker failure trial.
- [ ] Complete release verification, publish `v0.9.21`, and leave OpenAlice
      independently pinned to `v0.8.31`.

## Findings and decisions

- 2026-08-01 — `ohlcv-event-study-lab` already resolves the original request's
  event ledger, delayed return, matched reference, overlap, and uncertainty
  requirements. Reintroducing those semantics through Factor would duplicate
  authority and make Project routing less clear.
- 2026-08-01 — Missing input, an observed neutral zero, and a candidate with no
  variation are different states. The `0.9.20` missing-data rule remains
  unchanged; `0.9.21` diagnoses the resulting evaluation population rather
  than coercing one state into another.
- 2026-08-01 — The stable failure belongs before objective conversion and
  before downstream qualification. It should describe Core's exact purged
  primary validation population, not infer the candidate author's intent.
- 2026-08-01 — The same preflight runs after the authorized relative-value
  spread is constructed, so its distinct-value counts describe the actual
  evaluated contrast rather than either raw asset score.
- 2026-08-01 — Fresh Grok 4.5 session
  `019fbdf4-1f4e-7af3-85b5-f92eff52b712` used only the installed candidate
  wheel, one staged request, and a two-asset Yahoo package. It created one
  Project, wrote the English brief, executed the fixed candidate exactly once,
  preserved failed Run `run-20260801T153353232744Z-688e2dbc691e`, and stopped
  with zero Sessions, Reports, Dossiers, Portfolio, or RL work. It accurately
  explained `factor.temporal-primary-candidate-variation` rather than changing
  missing values or the Judge.
- 2026-08-01 — Independent reconstruction reproduced 643 NVDA rows, five gap
  events, five emitted ones, three warm-up missing values, and the exact purged
  validation population: 124 finite pairs, one candidate value, 124 target
  values, and zero validation events. Installed CLI validation and Studio were
  valid with zero diagnostics.
- 2026-08-01 — The field trial exposed a separate lifecycle question: after a
  preserved failed baseline, Orientation still says baseline evidence is
  missing and proposes another execution. This release does not broaden into
  failure-handoff policy; treat that as a candidate follow-up topic derived
  from the trial.

## Verification evidence

Candidate evidence:

- candidate commit `34be35a1c530a96e02cdec11159a6d4dc5f994fb`;
- wheel SHA-256
  `d86daebb50e921b28ea6654d71664b03822d46a6f4ea746fac865327fb948d1f`;
- isolated field root
  `/Users/ame/autoquant-v0921-unevaluable-factor-field`;
- transcript
  `/Users/ame/autoquant-v0921-unevaluable-factor-field/grok-transcript.md`;
- installed Python 3.11.14 and Pandas 3.0.5;
- focused Factor/Intake regression: 62 tests passed in 243.503 seconds;
- documentation links: 1,401 resolved at candidate implementation.

Final release audit pending.
