# Governed factor-component evidence

- Status: `completed`
- Updated: `2026-07-26`
- Related design: [[docs/design/factor-component-attribution]],
  [[docs/design/causal-multi-interval-factor-inputs]],
  [[docs/design/factor-diagnostics]], and
  [[docs/design/factor-evidence-explorer]].

## Outcome

Let an AI researcher explicitly declare the causal components behind a factor
candidate and receive bounded, immutable evidence about each component's
predictive quality, redundancy, and value inside a fixed diagnostic blend,
without pretending to infer arbitrary pandas semantics or changing the
Portfolio/RL decision contract.

## Context

AutoQuant now supplies completed 1h/3h/4h/6h/12h/1d data through one ordinary
pandas frame, but the evidence loop sees only the final factor Series. A
researcher can combine several horizons yet cannot answer which declared
source carries validation information, which merely repeats another source, or
which degrades a simple component blend. That is a material iteration gap for
both AI operators and human reviewers.

Source inspection cannot recover those semantics reliably. A component can be
renamed, transformed, conditionally applied, or hidden behind arbitrary Python.
The next contract therefore makes component disclosure explicit and optional.
Legacy candidates remain valid and historical Runs remain readable.

## Scope

### In scope

- Add an optional, ordinary-pandas component function and bounded metadata
  declaration beside `compute_factor(frame)`.
- Check component immutability, alignment, numeric shape, determinism, names,
  metadata, and prefix causality in preflight and the fixed Factor Judge.
- Record fixed train/validation/test component IC, final-factor association,
  pairwise redundancy, train-selected nearest-peer residual IC, and
  equal-rank diagnostic-blend leave-one-out evidence.
- Publish one immutable component artifact and reconcile it in the Factor
  Explorer before CLI/Studio projection.
- Freeze the bounded component diagnosis in Factor Reports and Project
  Dossiers for OpenAlice handoff.
- Update the reference multi-interval candidate to declare its actual
  components while retaining daily compatibility.

### Out of scope

- Inferring column use or semantic provenance from Python source.
- Claiming that declared components exhaustively reconstruct the final factor.
- Letting candidate components alter fixed Portfolio sizing, RL state, RL
  actions, promotion gates, or trading authority.
- Hidden component selection, parameter search, or test-driven ablation.
- Session-market interval support or a second execution engine.

## Acceptance

- [x] A legacy `compute_factor(frame) -> Series` candidate still evaluates and
  projects component evidence as explicitly unavailable.
- [x] A declaring candidate receives the same bounded component contract in
  seconds-scale preflight and complete Judge evaluation; malformed,
  nondeterministic, mutating, misaligned, or look-ahead components fail with
  stable error codes.
- [x] Successful Factor Runs publish hash-verified component evidence whose
  validation diagnosis and visible-test audit reconcile through the same Core
  object consumed by `aq run factor` and Studio.
- [x] Component diagnostics never change `validation_mean_ic`, Factor
  promotion authority, Portfolio mechanics, or the governed RL action set.
- [x] Factor leader Reports and Project Dossiers freeze the same bounded
  component diagnosis and hash used by the Explorer.
- [x] Deterministic fixture, negative-contract, artifact-tamper, legacy, CLI,
  Studio, Report, and Dossier tests pass without a long backtest.

## Work

- [x] Audit current factor, Portfolio/RL, multi-interval, Report/Dossier, and
  OpenAlice collaboration boundaries.
- [x] Define the explicit component authority and non-inference rules.
- [x] Implement shared candidate-component validation in preflight and Factor
  Judge, then update the reference candidate.
- [x] Produce fixed component metrics and an immutable artifact.
- [x] Verify and project the evidence through Factor Explorer, CLI, Studio,
  Report, and Dossier.
- [x] Exercise negative and compatibility paths, then run the complete
  documentation and regression suites.
- [x] Audit every acceptance item, complete the plan, commit, and push.

## Findings and decisions

- 2026-07-26 — The current OpenAlice checkout still exposes the historical
  per-workspace clone template. AutoQuant V2 must retain its provider-neutral
  Project/Dossier handoff instead of coupling this change to Launcher internals.
- 2026-07-26 — Arbitrary pandas source use is not mechanically inferable.
  Component evidence is candidate-declared and the output must say so.
- 2026-07-26 — A true leave-one-out of an arbitrary final factor is impossible
  without owning its composition. The Judge will instead ablate a fixed
  equal-rank diagnostic blend and label it separately from the candidate.
- 2026-07-26 — Component evidence is a Factor diagnostic. The downstream
  Portfolio and RL lanes continue to consume only the content-locked final
  factor, and RL keeps its fixed governed actions.
- 2026-07-26 — Sparse or constant declared components remain visible as
  insufficient evidence without invalidating an otherwise valid final factor.
- 2026-07-26 — Mobile Studio renders each component as a labeled evidence card
  instead of compressing six diagnostic columns below readable size.

## Verification

- `uv run python -m unittest discover -s tests -v` — 194 tests passed.
- `uv run python -m unittest tests.test_studio -v` — 7 focused Studio tests
  passed after the responsive evidence-card change.
- `uv run python scripts/check_doc_links.py` — 683 documentation double-links
  resolved.
- `uv run python -m compileall -q autoquant` — passed.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `git diff --check` — passed.
- `uv build --out-dir <temporary-directory>` — source distribution and wheel
  built successfully.
- Browser acceptance at 1280×720 and 390×844 verified the component panel,
  responsive card layout, zero document-width overflow, and no console
  warnings or errors.

## Progress log

- 2026-07-26 — Plan created after the causal multi-interval input milestone and
  a full quant-workflow gap audit.
- 2026-07-26 — Added the optional candidate component contract, fixed Judge
  diagnostics, immutable artifact, verified Explorer projection, and frozen
  Report/Dossier handoff.
- 2026-07-26 — Completed bounded browser acceptance, packaging, documentation
  validation, and the 194-test regression suite.

## Completion

Completed on 2026-07-26. AutoQuant can now explain which explicitly declared
multi-interval inputs carry validation evidence, repeat a peer, or weaken a
fixed diagnostic blend without inferring source semantics or expanding
Portfolio, RL, order, account, or trading authority.
