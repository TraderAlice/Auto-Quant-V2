# AutoQuant V2 contributor guide

AutoQuant V2 is a pre-alpha, Agent-native quantitative research workbench. Its
job is to turn quantitative research into a file-backed, versioned, testable
workflow that coding Agents can operate and humans can inspect.

The same repository must work independently and unchanged as a specialized
Workspace desk inside OpenAlice or another Agent Harness. Host-specific
Session orchestration, communication, provenance, and live trading are optional
surrounding capabilities; they do not define AutoQuant Core.

Domain correctness, reproducible evidence, Agent operability, and a coherent
project model take priority over backward compatibility while V2 is taking
shape. Auto-Quant Classic files were retired from the current tree; Git history
is their archive and current code must not load or reinterpret them under V2
semantics.

Use Python 3.11 and `uv` for repository code and scripts. Keep projects
self-contained: a Workspace owns project discovery and a standardized Harness,
while each Project owns its research question, source inputs, strategies or
models, Runs, and durable artifacts.

Before adding a host integration or public surface, ask:

1. Can a coding Agent use the same capability in a standalone Workspace?
2. Is durable truth recoverable from files, manifests, Git, and immutable
   evidence rather than private conversation context?
3. Does the change preserve one Core contract across CLI, JSON, Studio, and
   any host projection?

## Starting a quantitative assignment

Do not begin with data downloads, candidate edits, model training, or
backtests. First establish the assignment as an English Markdown research
brief that another Agent can recover from the filesystem.

1. Inspect the Workspace and existing Projects. Continue the Project when the
   assignment belongs to its evolving research question; do not create a new
   Project merely because a new coworker or conversation arrived.
2. When the assignment is genuinely new, create its construction site with
   `aq project create <workspace> <project-id>`. Use `--template blank` while
   the appropriate research method is still unclear. Select a specialized
   template only when the understood question already fits that contract.
3. Before quantitative work, read and update the Project-root `research.md`.
   Rewrite the incoming assignment in English and preserve useful source
   context, including a verbatim caller statement when precision requires it.
4. Make the research decision, question, motivation, asset scope, horizon or
   cadence, available evidence, material constraints, evaluation meaning,
   expected deliverable, assumptions, open questions, and proposed bounded
   route clear enough for a replacement Agent to continue.
5. Separate caller-owned intent from researcher-owned method. Use informed
   judgment to choose factors, diagnostics, models, and implementation details.
   Do not invent the decision being supported, risk appetite, universe,
   direction, horizon, benchmark, hard constraints, or what would count as a
   useful answer.
6. If a missing or ambiguous caller-owned fact could materially change the
   study, stop and ask the delegating Agent or user. Record the question and
   answer in `research.md`, then ask again if the answer exposes another
   material ambiguity. Continue until the assignment is bounded, falsifiable,
   and safe to translate into fixed evaluation authority.
7. Only then bind datasets, requests, Studies, Judges, or other strict
   manifests and begin the bounded research loop. Those machine contracts
   freeze an understood question; they do not replace the Markdown brief.

When a caller asks about an existing book, do not substitute historical model
targets for current holdings. If the caller or delegating Agent can supply one
explicit reported or hypothetical funded weight snapshot, the
`ohlcv-book-risk-lab` can perform a fixed descriptive audit. A conditional
question may additionally supply up to eight explicitly named, complete funded
hypothetical books at the same time and currency; never invent or search those
scenarios. A caller may instead authorize one strictly positive held asset to
be reduced only to cash against one fixed historical volatility ceiling; never
add another adjustable leg or turn the resulting target into an Order. Treat
every snapshot as unauthenticated external input, return its verified evidence,
and leave live account reconciliation and execution to OpenAlice/UTA. See
[[docs/design/reported-position-book-risk]].

English is the working language inside the AutoQuant desk: use it for
`research.md`, plans, research notes, code and comments, experiment hypotheses,
and internal Reports or Dossiers. Preserve proper nouns, identifiers, source
quotes, and evidence in their original form when needed. The delegating or
user-facing Agent owns conversation locale and may translate the resulting
evidence for the user; callers are never required to speak English.

## Research work and Workbench work

Keep two connected lines of work distinct:

1. The Project research line answers the assignment. Maintain its question,
   hypotheses, evidence, and progress in `research.md`, candidate source,
   Sessions, Runs, Reports, and Dossiers.
2. The Workbench improvement line changes AutoQuant when real Project work
   exposes a reusable framework gap. Record the observed gap in the
   canonical Project-root `framework-needs.md` before proposing a Core
   solution. During a governed candidate operation, its Session worktree copy
   is protected orientation material; update the canonical note before
   entering or after returning from the operation.

Do not turn `research.md` into a framework backlog, and do not modify fixed
Harness/Judge authority to work around a missing capability. A useful
`framework-needs.md` item states the attempted research, concrete missing or
misleading behavior, evidence, smallest useful Core improvement, and any
temporary workaround plus its scientific cost. Keep speculative feature wishes
out of the file.

When acting as a Workbench developer, reproduce and generalize a Project need,
then promote accepted reusable work into an indexed repository plan and the
appropriate `docs/design/` contract. When the fix lands, preserve the original
Project note and record the version and research retry outcome. See
[[docs/design/project-derived-workbench-needs]].

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

- Product identity, standalone/hosted parity, desk composition, Agent-first
  requirements, and ownership boundaries:
  [[docs/design/agent-native-quant-workbench]]
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
- Project-observed capability gaps and their promotion into Workbench design
  and plans: [[docs/design/project-derived-workbench-needs]]
- Observed-universe ordinary-pandas factor input, aligned/ragged cross-asset
  computation, and shared causality runtime:
  [[docs/design/panel-native-factor-api]]
- Verified Factor/Portfolio/RL evidence translated into bounded experiment
  briefs without automatic execution, promotion, or trading authority:
  [[docs/design/evidence-driven-research-agenda]]
- Exact Dossier leaders frozen into a strictly later compatible Project for
  one non-iterative external-period challenge:
  [[docs/design/frozen-external-holdout-challenge]]
- Configurable decision-bar intervals and calendar-verified XNYS regular
  sessions:
  [[docs/design/configurable-session-interval-inputs]]
- Caller-owned Portfolio risk and implementation assumptions shared by
  Portfolio and governed RL:
  [[docs/design/caller-owned-portfolio-research-policy]]
- Caller-owned per-asset target caps shared by Portfolio and governed RL:
  [[docs/design/caller-owned-asset-position-caps]]
- Caller-owned per-asset long, short, two-sided, and context-only position
  permissions shared by Portfolio and governed RL:
  [[docs/design/caller-owned-asset-position-roles]]
- Caller-owned cash or named-asset benchmark references shared by Portfolio
  and governed RL:
  [[docs/design/caller-owned-benchmark-reference]]
- Caller-owned Portfolio/RL decision cadence, scheduled mechanical holds, and
  continuously available risk-only repair:
  [[docs/design/caller-owned-decision-cadence]]
- Caller-owned dataset/session decision anchors bound to verified market-clock
  authority: [[docs/design/market-clock-decision-anchors]]
- Target-weight portfolio construction, Order/TPSL realization, conservative
  OHLC bar execution, and optional host delivery:
  [[docs/design/order-native-portfolio-decisions]]
- Request-bound numerical forward horizon shared by Factor, Portfolio, and
  governed RL:
  [[docs/design/request-bound-research-horizon]]
- Fixed seconds-scale candidate checks, immutable non-selection diagnostics,
  and edit/check/evaluate routing:
  [[docs/design/candidate-preflight-feedback]]
- Fixed Study authority, editable/Judge source closures, bounded execution, and
  immutable RunResult evidence: [[docs/design/study-run-evidence]]
- Transactional reference-Project construction, ordinary pandas factor API,
  deterministic OHLCV fixture, and fixed no-lookahead factor Judge:
  [[docs/design/ohlcv-factor-lab]]
- Externally reported position snapshots, covariance crowding, component risk,
  standardized reduction sensitivity, and live-account authority boundary:
  [[docs/design/reported-position-book-risk]]
- Caller-fixed downside opening gaps, delayed close-to-close outcomes,
  unconditional/matched references, overlap handling, and no-trading event
  evidence: [[docs/design/ohlcv-price-event-study]]
- Portfolio-native equal-risk-contribution construction, fixed weighted
  reference paths, cap-induced parity disclosure, and no-Session evidence:
  [[docs/design/portfolio-native-allocation-lab]]
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
  overlap, request-bound novel/known-style claims, claim-specific
  qualification, and asset/fold/causal-regime stability:
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
- Request-driven Project construction, aligned or observed-only external OHLCV
  package validation, normalized dataset snapshots, and pre-Session intake
  state:
  [[docs/design/research-intake-and-dataset-snapshots]]
- Completed-bar multi-interval aggregation, causal as-of alignment, ordinary
  pandas candidate surface, and shared Factor/Portfolio/RL input authority:
  [[docs/design/causal-multi-interval-factor-inputs]]
- Explicit score/context component declarations, causal contract checks,
  component redundancy/incremental diagnostics, context-state conditionals,
  and fixed-blend attribution:
  [[docs/design/factor-component-attribution]]
- One-request/multi-Study orchestration, shared factor-source sequencing, lane
  currentness, and research-program status:
  [[docs/design/research-program-orchestration]]
- Read-only cross-Study source dependencies and governed Factor-to-RL fusion:
  [[docs/design/cross-study-factor-dependencies]]
- Resumable Agent worktrees, KEEP/REVERT/CRASH Experiments, and Report-bound
  delegated source promotion: [[docs/design/research-session-loop]]
- Provider-neutral external Researcher turns, budgets, restoration, and
  immutable Campaign evidence: [[docs/design/external-researcher-driver]]
- Read-only Workspace observation, local HTTP, browser presentation, and
  mutable-versus-immutable research state:
  [[docs/design/studio-observation-surface]]
- Agent-native request/report collaboration, professional quantitative
  evidence, causal portfolio construction, governed RL, and human/Agent
  interaction:
  [[docs/design/quant-research-lifecycle]]
- Project-level synthesis of verified lane Reports into one immutable
  deliverable: [[docs/design/program-research-dossiers]]
- Studio operator and public read-model guide: [[docs/STUDIO]]
- Canonical Workspace and Project file schemas: [[docs/PROJECT_FORMAT]]
- Human and machine-readable command behavior: [[docs/CLI]]
- Retired repository-root Freqtrade Harness boundary:
  [[docs/design/retired-flat-freqtrade-harness]]

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
