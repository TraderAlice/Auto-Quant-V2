# AutoQuant V2 contributor guide

AutoQuant V2 is a pre-alpha, AI-native quantitative research workbench. Domain
correctness, reproducible evidence, and a coherent project model take priority
over backward compatibility while V2 is taking shape. Preserve the archived
V0 experiments as historical evidence; do not silently reinterpret them under
new Harness semantics.

Use Python 3.11 and `uv` for repository code and scripts. Keep projects
self-contained: a Workspace owns project discovery and a standardized Harness,
while each Project owns its research question, source inputs, strategies or
models, Runs, and durable artifacts.

## Plan workflow

Read [[PLANS]] before starting non-trivial work. A plan is required when work
crosses packages or public surfaces, changes a domain model, contains meaningful
unknowns, or needs multiple implementation steps. Small, local fixes can
proceed without one.

For planned work:

1. Copy [[plans/_template]] to a stable kebab-case filename and register it in
   the matching status section of [[PLANS]] before implementation.
2. Treat the plan as the live coordination record. Update its checklist,
   findings, decisions, verification evidence, and date as work evolves; do not
   reconstruct them only at the end.
3. Keep durable system truth in the relevant `docs/design/` document. A plan
   may link to design intent but must not become a second source of current
   invariants.
4. Before marking a plan `completed`, audit every acceptance item against
   executable or manual evidence. Move the index entry to the completed section
   and preserve the plan as a concise record.
5. If a plan is replaced, mark it `superseded` and link its replacement. If
   follow-up work remains after completion, create and index a separate plan
   rather than leaving unchecked work in a completed plan.

Plan structure, lifecycle, and its boundary with design documentation are
defined in [[docs/design/documentation-system]].

## Design map

Read the relevant linked document before changing a subsystem:

- Documentation ownership and update protocol:
  [[docs/design/documentation-system]]
- System direction, Workspace/Project ownership, and runtime boundaries:
  [[docs/ARCHITECTURE]]
- Workspace discovery, Project identity, self-contained construction, and path
  confinement: [[docs/design/workspace-project-boundaries]]
- Versioned CLI envelopes, capability discovery, operation effects, artifacts,
  and next actions: [[docs/design/agent-cli-contract]]
- AI-primary operator, human-reviewer roles, compact Agent Work Brief,
  filesystem authority, and CLI/Studio orientation parity:
  [[docs/design/agent-operator-experience]]
- Verified Factor/Portfolio/RL evidence translated into bounded experiment
  briefs without automatic execution, promotion, or trading authority:
  [[docs/design/evidence-driven-research-agenda]]
- Exact Dossier leaders frozen into a strictly later compatible Project for
  one non-iterative external-period challenge:
  [[docs/design/frozen-external-holdout-challenge]]
- Configurable decision-bar intervals and calendar-verified XNYS regular
  sessions:
  [[docs/design/configurable-session-interval-inputs]]
- Fixed seconds-scale candidate checks, immutable non-selection diagnostics,
  and edit/check/evaluate routing:
  [[docs/design/candidate-preflight-feedback]]
- Fixed Study authority, editable/Judge source closures, bounded execution, and
  immutable RunResult evidence: [[docs/design/study-run-evidence]]
- Transactional reference-Project construction, ordinary pandas factor API,
  deterministic OHLCV fixture, and fixed no-lookahead factor Judge:
  [[docs/design/ohlcv-factor-lab]]
- Causal signal ranking, constrained target weights, drift-aware accounting,
  costs, risk/implementation metrics, and portfolio stress evidence:
  [[docs/design/portfolio-construction-lab]]
- Predeclared local entry/exit and no-trade parameter stability without
  parameter-selection authority:
  [[docs/design/portfolio-parameter-neighborhood]]
- Governed causal state encoding, fixed factor-mixture actions, RL reward,
  seeds/folds/baselines, and policy evidence:
  [[docs/design/rl-factor-policy-lab]]
- Governed RL action persistence and exact chosen-versus-runner-up linear
  decision rationale:
  [[docs/design/rl-policy-behavior-rationale]]
- Same-pretrade one-step governed factor opportunities, realized selection
  regret, and ex-post oracle authority boundaries:
  [[docs/design/rl-factor-opportunity-audit]]
- Verified governed RL artifacts, bounded fold/seed, training, baseline, and
  fixed-action Studio projection:
  [[docs/design/rl-policy-evidence-explorer]]
- Validation-only candidate selection, visible-test limitations, trial counts,
  and shared Session/Report/Studio integrity evidence:
  [[docs/design/research-selection-integrity]]
- Project-wide research families, multiple-testing correction, and
  selection-adjusted Factor/Portfolio evidence:
  [[docs/design/selection-adjusted-research-evidence]]
- Purged forward horizons, factor significance/decay/quantiles, fixed style
  overlap, and asset/fold/causal-regime stability:
  [[docs/design/factor-diagnostics]]
- Verified Factor artifacts, bounded IC/quantile paths, horizon profile, and
  Studio tear-sheet projection:
  [[docs/design/factor-evidence-explorer]]
- Mechanical signal state, hysteresis, conviction/risk sizing, execution
  reasons, and portfolio contribution reconciliation:
  [[docs/design/signal-policy-and-attribution]]
- Split-bounded executed-position episodes, holding periods, entry/exit cost,
  contribution excursions, and signal/execution mismatch:
  [[docs/design/mechanical-position-lifecycle-evidence]]
- Causal covariance forecast, one-sided portfolio-volatility ceiling, shared
  Portfolio/RL risk policy, and pre/post sizing evidence:
  [[docs/design/portfolio-risk-governor]]
- Post-drift executed-book volatility compliance, no-trade risk overrides,
  proportional repairs, and shared Portfolio/RL execution evidence:
  [[docs/design/executed-book-risk-compliance]]
- Causal OHLCV dollar-volume capacity envelopes, exact trade-path
  reconciliation, binding assets, and no-impact interpretation:
  [[docs/design/portfolio-liquidity-capacity]]
- Request-derived tradable/context universes, directional construction,
  cash, benchmarks, and shared Portfolio/RL position authority:
  [[docs/design/request-bound-portfolio-mandates]]
- Bounded verified Portfolio Run projection, sampled performance/exposure
  series, current mechanical book, transitions, and contribution explorer:
  [[docs/design/portfolio-decision-explorer]]
- Verified baseline/candidate/leader comparison, metric preferences,
  validation-only non-dominance, and Studio decision matrix:
  [[docs/design/session-decision-matrix]]
- Request-driven Project construction, external OHLCV package validation,
  normalized dataset snapshots, and pre-Session intake state:
  [[docs/design/research-intake-and-dataset-snapshots]]
- Completed-bar multi-interval aggregation, causal as-of alignment, ordinary
  pandas candidate surface, and shared Factor/Portfolio/RL input authority:
  [[docs/design/causal-multi-interval-factor-inputs]]
- Explicit candidate component declarations, causal contract checks,
  component redundancy/incremental diagnostics, and fixed-blend attribution:
  [[docs/design/factor-component-attribution]]
- One-request/multi-Study orchestration, shared factor-source sequencing, lane
  currentness, and research-program status:
  [[docs/design/research-program-orchestration]]
- Read-only cross-Study source dependencies and governed Factor-to-RL fusion:
  [[docs/design/cross-study-factor-dependencies]]
- Resumable Agent worktrees, KEEP/REVERT/CRASH Experiments, and guarded source
  promotion: [[docs/design/research-session-loop]]
- Provider-neutral external Researcher turns, budgets, restoration, and
  immutable Campaign evidence: [[docs/design/external-researcher-driver]]
- Read-only Workspace observation, local HTTP, browser presentation, and
  mutable-versus-immutable research state:
  [[docs/design/studio-observation-surface]]
- OpenAlice request/report collaboration, professional quantitative evidence,
  causal portfolio construction, governed RL, and human/Agent interaction:
  [[docs/design/quant-research-lifecycle]]
- Project-level synthesis of verified lane Reports into one immutable
  OpenAlice handoff: [[docs/design/program-research-dossiers]]
- Studio operator and public read-model guide: [[docs/STUDIO]]
- Canonical Workspace and Project file schemas: [[docs/PROJECT_FORMAT]]
- Human and machine-readable command behavior: [[docs/CLI]]
- Current Freqtrade/OHLCV Harness manifest and profile contract:
  [[docs/harness]]
- Historical research snapshots: [[versions/README]]

Add new active design documents to this map when a subsystem gains its own
invariants. Keep this list as a routing surface, not a historical catalog.

## Required change loop

1. Read [[PLANS]], the active plan when one exists, and the relevant design
   document(s); identify the current invariant being changed.
2. Make the smallest coherent source, schema, fixture, and project changes.
3. Update every affected design document in the same change. If the concept has
   no document, create one under `docs/design/` and add it to the design map.
4. Exercise the affected public CLI or Python boundary with bounded inputs.
5. Run:

   ```bash
   uv run python scripts/check_doc_links.py
   uv run python -m unittest discover -s tests -v
   ```

6. If evaluation semantics, dataset identity, or result hashes changed,
   explicitly record which checked-in fixtures or immutable Runs were
   regenerated and why.
7. If a locked benchmark or Judge contract changed, relock it deliberately and
   prove both an unchanged candidate and a known-improvement path.

Do not launch the autonomous NEVER STOP loop, download large datasets, or run a
long multi-year backtest as routine validation. Use fast deterministic tests
and bounded smoke fixtures unless the active plan explicitly requires a larger
run and records its budget.

Tests prove executable behavior; design documents explain why the behavior
exists and which invariants future changes must preserve. Neither substitutes
for the other.
