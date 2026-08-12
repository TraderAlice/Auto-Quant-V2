# AutoResearch factor and strategy Studio

- Status: `completed`
- Updated: `2026-08-03`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/research-program-orchestration]], and
  [[docs/design/studio-observation-surface]].

## Outcome

The connected Next Studio exposes the existing verified Research Program as
two operator-facing workbenches: Factor Research manages definitions,
dependencies, evidence, Sessions, Campaigns, and status; Strategy Research
manages factor-to-portfolio composition, governed RL policy evidence,
validation, cost, risk, artifacts, and the next bounded research action.

## Context

Core already owns Studies, immutable Runs, Sessions, Experiments, Campaigns,
Research Reports, Dossiers, Factor diagnostics, Portfolio evidence, governed
RL evidence, and progression gates. The Next Studio currently scatters those
objects across detail pages and does not give a human or Agent one truthful
management view for Factor research or Strategy research. This work projects
the existing snapshot; it does not create a second research engine or a
browser-side evaluator.

## Scope

### In scope

- Add connected Factor Research and Strategy Research routes.
- Derive display state only from the versioned Core Studio snapshot.
- Show current evidence, mutable research activity, blockers, and exact Core
  next actions without inventing missing records.
- Reuse Mantine 9.5.1, AutoQuant tokens, and existing Studio components.

### Out of scope

- A new Campaign engine, model-provider adapter, or arbitrary shell endpoint.
- Browser-side metric computation, verdicts, promotion, or report authorship.
- Replacing the existing Factor, Portfolio, RL, Replay, data, job, or audit
  detail surfaces.

## Acceptance

- [x] Connected Factor Research distinguishes definitions/dependencies,
  immutable evidence, mutable Sessions/Campaigns, and missing evidence.
- [x] Connected Strategy Research keeps Portfolio and governed RL as related
  but distinct validation lanes, including progression gates and artifacts.
- [x] Both routes show only Core-projected records and remain useful for empty,
  partial, active, reported, stale, and failed research states.
- [x] Existing routes remain available and the navigation clearly separates
  management from evidence detail.
- [x] Projection logic has runnable Node tests; Studio lint, boundary check,
  tests, and production build pass.
- [x] Repository documentation and the existing Designer Pipeline handoff,
  tasks, QA, state, and events record the shipped behavior.

## Work

- [x] Freeze shared snapshot projection and assign non-overlapping Factor and
  Strategy implementation slices.
- [x] Implement and test the Factor Research management surface.
- [x] Implement and test the Strategy Research management surface.
- [x] Integrate navigation and shared presentation with the smallest coherent
  diff.
- [x] Update documentation and Designer Pipeline evidence.
- [x] Run the final completion audit.

## Findings and decisions

- 2026-08-03 — Reuse the existing Core Research Program, Sessions, Campaigns,
  explorers, and commands. Do not build a parallel AutoResearch backend.
- 2026-08-03 — Factor management owns FactorDefinition/version/passport/data
  dependencies/cohorts/tests/evidence/status. Strategy management consumes
  factor evidence and owns portfolio/rules/model-policy validation evidence.
- 2026-08-03 — Provider execution remains Agent/CLI orchestration until a
  provider-neutral bounded adapter is separately designed; the Studio first
  exposes truthful status and fixed Study execution.

## Verification

- `npm test`: 28/28 passed.
- `npm run lint`: passed.
- `npm run check:boundary`: passed.
- `npm run build`: passed; `/factors` and `/strategies` were generated.

## Progress log

- 2026-08-03 — Plan created and registered as active.
- 2026-08-03 — MiniMax Factor slice accepted after contract corrections;
  DeepSeek Strategy UI skeleton retained while its speculative projection was
  replaced with the repository-owned Core contract.
- 2026-08-03 — Connected routes, management projections, tests, docs, and
  production build completed without changing Git or remote systems.

## Completion

The Next Studio now has truthful connected Factor Research and Strategy
Research management surfaces over the existing Core snapshot. Missing Program,
Explorer, model, holdout, or Dossier evidence remains explicitly absent.
