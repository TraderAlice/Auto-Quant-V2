# Panel-native factor system

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/panel-native-factor-api]],
  [[docs/design/project-derived-workbench-needs]],
  [[docs/design/ohlcv-factor-lab]], and
  [[docs/design/agent-native-quant-workbench]].

## Outcome

Give Quant Agents one ordinary-pandas factor surface that can express causal
time-series and cross-asset OHLCV hypotheses over the complete research
universe, and give every Project a durable English Markdown surface for
recording real workbench capability gaps that framework development can
promote into implementation plans.

## Context

The current `compute_factor(frame)` API receives one asset at a time. Candidate
code can express sophisticated causal transformations but cannot naturally
express relative strength, cross-sectional normalization, breadth, pairs, or
market-context gates. Factor, Portfolio, governed RL, and candidate preflight
also duplicate their own candidate execution and causality checks.

AutoQuant is still pre-alpha and does not need a legacy per-asset compatibility
layer. The correct upgrade is one panel-native contract shared by every
research lane. Separately, real Quant Agents need a lightweight place to
record missing workbench capabilities without turning research briefs into
framework issue trackers or requiring a rigid external intake schema.

## Scope

### In scope

- Replace the per-asset factor API with one long-form panel pandas API.
- Permit causal contemporaneous cross-asset computation while rejecting
  future-time dependence.
- Centralize candidate execution, determinism, alignment, mutation, numeric,
  panel identity, and prefix-causality validation.
- Make Factor, Portfolio, governed RL, and preflight consume the same runtime.
- Keep optional declared component evidence panel-native.
- Migrate built-in candidates and examples to the new contract.
- Create a Project-root English `framework-needs.md` feedback surface and
  document how research Agents feed verified gaps into Workbench plans.
- Add bounded tests that prove real cross-asset behavior and all-lane parity.

### Out of scope

- Add fundamental, news, options, tick, L2, or alternative-data schemas.
- Add a factor DSL or indicator registry.
- Add an automatic issue classifier or framework-needs parser.
- Turn factor output into Broker orders or live execution authority.
- Preserve execution of legacy per-asset candidate source.

## Acceptance

- [x] Candidate code receives one immutable long-form pandas DataFrame with
  `asset`, `timestamp`, base OHLCV, and available completed higher-interval
  columns for the complete Study universe.
- [x] Candidate code returns one numeric Series on the exact panel index;
  contemporaneous cross-asset operations work in ordinary pandas.
- [x] One shared runtime validates Factor, Portfolio, governed RL, and
  preflight candidates with deterministic panel-time prefix causality.
- [x] Optional 1–12 declared components use the same panel index and retain
  fixed diagnostic evidence.
- [x] Built-in candidates demonstrate both within-asset rolling computation
  and a cross-sectional transformation without changing target authority.
- [x] Tests reject mutation, non-determinism, misalignment, missing panel
  identity, and future-panel leakage.
- [x] A cross-asset candidate produces valid Factor, Portfolio, and governed-RL
  evidence from the same source.
- [x] Every newly created Project includes an Agent-maintained English
  `framework-needs.md`; CLI output makes it discoverable.
- [x] Agent and design documentation keep research work and Workbench
  improvement as separate but connected lines.
- [x] Bounded tests, documentation links, build, and package-content checks
  pass.

## Work

- [x] Audit duplicated factor execution and existing Project feedback
  surfaces.
- [x] Define the panel and Project-feedback contracts.
- [x] Implement the shared panel factor runtime.
- [x] Migrate preflight and all three research lanes.
- [x] Migrate templates, fixtures, and candidate-source tests.
- [x] Add Project workbench-needs scaffolding and CLI projection.
- [x] Update durable documentation and Agent guidance.
- [x] Run cross-lane verification and complete the acceptance audit.
- [x] Commit and push the milestone.

## Findings and decisions

- 2026-07-27 — Formula complexity is not the current bottleneck. The
  per-asset input topology prevents genuine cross-sectional research.
- 2026-07-27 — Factor, Portfolio, governed RL, and preflight currently maintain
  four similar candidate-execution paths. A shared runtime is required before
  expanding the API.
- 2026-07-27 — The new candidate input will be one long-form DataFrame rather
  than a dict of frames or a custom object. This keeps time-series rolling,
  timestamp grouping, pair joins, and inspection inside ordinary pandas.
- 2026-07-27 — Cross-asset values at the same timestamp are causal inputs.
  Causality is audited by truncating the entire panel at timestamp boundaries,
  never by truncating one asset in isolation.
- 2026-07-27 — The old per-asset API is intentionally retired rather than
  auto-detected. A compatibility branch would make Agent-visible authority
  ambiguous during pre-alpha development.
- 2026-07-27 — Framework needs remain flexible Project Markdown. Verified
  recurring needs may be promoted manually into repository plans; no parser or
  automatic framework mutation is introduced.

## Verification

- `uv run python -m unittest discover -s tests -v`
  - 222 bounded repository tests passed in 1788.529 seconds.
- `uv run python -m unittest -v tests.test_factor_runtime`
  - all 6 focused panel runtime tests passed after the final identity/order
    hardening.
- `uv run python scripts/check_doc_links.py`
  - 918 documentation links resolved.
- `git diff --check`
  - passed.
- `uv run python -m compileall -q autoquant tests`
  - passed.
- `uv build --out-dir /tmp/autoquant-panel-build.SviZPb`
  - source distribution and wheel built successfully.
- package-content inspection
  - wheel and source distribution contain the shared runtime and all migrated
    Factor, Portfolio, RL, and preflight template entry points.

## Progress log

- 2026-07-27 — Plan activated after auditing the current factor call sites and
  Project construction flow.
- 2026-07-27 — Added `autoquant.factor_runtime`, migrated candidate preflight
  plus all three research lanes, and froze identical `panel-v1` RunResult
  contract evidence across Factor, Portfolio, and governed RL.
- 2026-07-27 — Added required Project-root `framework-needs.md`, CLI discovery,
  Session orientation-copy semantics, Agent guidance, and the manual promotion
  boundary into repository designs and plans.
- 2026-07-27 — Completed bounded repository regression, documentation,
  compilation, build, and package-content verification.

## Completion

AutoQuant now gives candidate factors the complete Study universe as one
ordinary long-form pandas panel, permits causal same-timestamp cross-asset
research, and rejects future-panel dependence through one shared runtime used
by preflight, Factor, Portfolio, and governed RL. Every new Project also owns a
separate English Workbench-needs note so real research can inform Core
development without polluting the research brief or bypassing fixed authority.
