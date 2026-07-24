# AutoQuant V2 architecture

Status: active, pre-alpha.

## Purpose

AutoQuant V2 is a standardized quantitative-research Harness organized as a
long-lived Workspace containing self-contained Projects. When AutoQuant
receives a research request, work begins in a Project rather than by cloning
and mutating the Harness itself.

The target model is:

```text
Workspace
├── Harness runtime, schemas, CLI, and project discovery
└── projects/
    └── <project-id>/
        ├── research question and configuration
        ├── project-local datasets or dataset identities
        ├── factors, strategies, features, and models
        ├── Studies and Sessions
        └── immutable Runs and artifacts
```

The Workspace is the stable quantitative workbench. A Project is the concrete
construction site for one evolving body of research. A Run is a bounded,
immutable execution under pinned Project and Harness inputs.

## Current implementation state

The V2 foundation now implements:

- strict `autoquant-workspace.json` and `autoquant.json` manifests;
- self-contained blank or reference-template Project creation and one-level
  Workspace discovery;
- transactional request-driven Project intake from strict caller-supplied
  daily-OHLCV packages, with normalized local bytes, explicit provider and
  adjustment claims, source/snapshot hashes, and exact Study identity;
- one canonical request-driven research desk that coordinates Factor,
  Portfolio, and governed RL Studies over the same dataset, exposes exact lane
  currentness/conflicts/next actions, and keeps method choice inside AutoQuant;
- default or explicit Project resolution with root confinement and symlink
  rejection;
- a packaged `aq` CLI with versioned JSON envelopes, capability discovery,
  artifacts, next actions, validation, and inspection.
- strict Project-local Study contracts with separate human program, fixed
  Python Judge closure, Agent-editable strategy/factor/model closure, objective,
  and declarative or content-locked dataset identity;
- bounded isolated Judge execution and atomically published immutable
  RunResults with full-file tamper verification.
- resumable Project-local Research Sessions with disposable candidate
  worktrees, fixed authority locks, immutable KEEP/REVERT/CRASH Experiments,
  exact leader restoration, and stale-safe rollback-capable promotion.
- provider-neutral external Researcher Campaigns with strict briefs/responses,
  aggregate and per-turn budgets, failure recovery, and immutable turn
  evidence.
- strict delegated Research Requests, Session-derived Briefs, and immutable
  evidence-bound JSON/Markdown Research Reports with no trading authority.
- one packaged local read-only Studio with a shared versioned snapshot,
  Workspace/Project overview, request → evidence → report handoff, exact
  copyable CLI commands, explicit mutable Campaign progress, defensive HTTP
  boundary, bounded verified Portfolio decision exploration, and responsive
  research-first presentation.
- one self-contained OHLCV Factor Lab reference Project with ordinary pandas
  factor code, deterministic local data, dataset-fixed purged horizons, a
  professional factor tear sheet, and a fixed no-lookahead audit.
- one bounded Factor evidence projection that reconciles immutable daily IC
  and quantile artifacts before exposing horizon, stability, style, coverage,
  and turnover evidence to CLI and Studio.
- one self-contained OHLCV Portfolio Lab reference Project that mechanically
  translates the same causal factor API through explicit signal state into
  capped target weights, drift-aware execution, reconciled contribution/risk
  attribution, and policy/cost/delay stresses without trading authority.
- one governed RL Factor-Policy Lab that confines Agent changes to a causal
  state encoder while the Judge fixes factor-mixture actions, Q-learning,
  rewards, portfolio accounting, folds, seeds, baselines, and model evidence.
- one shared research-selection integrity projection that keeps reference
  promotion validation-only and freezes trial/test-reuse disclosure through
  Sessions, Reports, and Studio.
- one bounded Session Decision Matrix that verifies the immutable trial chain,
  applies fixed family-specific metric semantics, and separates validation
  comparison from test audit and contextual evidence.

The canonical contracts are [[docs/PROJECT_FORMAT]] and [[docs/CLI]]. The
boundary designs are [[docs/design/workspace-project-boundaries]] and
[[docs/design/agent-cli-contract]]. Study/Run authority and evidence are defined
in [[docs/design/study-run-evidence]]; governed source research is defined in
[[docs/design/research-session-loop]]; external orchestration is defined in
[[docs/design/external-researcher-driver]]; Studio observation is defined in
[[docs/design/studio-observation-surface]]; the first quantitative reference
Project is defined in [[docs/design/ohlcv-factor-lab]]; causal target-weight
construction is defined in [[docs/design/portfolio-construction-lab]]. The
governed RL lane is defined in [[docs/design/rl-factor-policy-lab]]. The
factor tear-sheet protocol is defined in [[docs/design/factor-diagnostics]].
Bounded immutable Factor artifact projection is defined in
[[docs/design/factor-evidence-explorer]].
Mechanical signal state and attribution are defined in
[[docs/design/signal-policy-and-attribution]].
Bounded immutable Portfolio artifact projection is defined in
[[docs/design/portfolio-decision-explorer]].
Bounded governed RL artifact projection is defined in
[[docs/design/rl-policy-evidence-explorer]].
Session-level professional evidence comparison is defined in
[[docs/design/session-decision-matrix]].
Request-driven construction and external dataset snapshots are defined in
[[docs/design/research-intake-and-dataset-snapshots]].
Multi-Study Project coordination and lane currentness are defined in
[[docs/design/research-program-orchestration]].
The end-to-end OpenAlice handoff, professional evidence stack, and HCI
boundary are defined in [[docs/design/quant-research-lifecycle]].

The implementation boundary for Session comparison is
`autoquant/decision_matrix.py`; CLI and Studio consume that Core read model
without reimplementing metric choice or verdict semantics.

The repository also contains the V0.5 development Harness inherited from
Auto-Quant Classic:

- `harness.json` declares Freqtrade 2026.3 and two OHLCV asset profiles;
- `autoquant/`, `prepare.py`, and `run.py` adapt data and execution;
- `user_data/strategies/` is the current Agent-editable research surface;
- `versions/` preserves completed historical experiments;
- repository-local `data/`, `results.tsv`, and `run.log` are ignored state.

This flat arena is a compatibility implementation, not a V2 Project. Its active
contract is documented in [[docs/harness]]. Structural V2 work must migrate it
through explicit plans while preserving historical evidence.

## Ownership boundaries

### Workspace and Harness own

- project discovery, identity, and root confinement;
- versioned schemas and machine-readable operations;
- data preparation and validation contracts;
- bounded execution and evaluation entry points;
- immutable artifact publication and result identity;
- cross-project inspection surfaces for CLI and the future Studio;
- dependency and runtime versions.

### Project owns

- the research question, hypotheses, and acceptance criteria;
- universe and dataset selection or pinned dataset identity;
- factors, features, strategies, models, and project-local research code;
- Study and Session history;
- immutable Researcher Campaign evidence;
- exact delegated request/Brief context and immutable Research Reports;
- immutable Run evidence and reviewed candidates;
- project-specific notebooks, reports, and presentation assets.

A Workspace discovers Projects but does not provide mutable shared research
assets whose changes silently alter multiple Projects. Disposable caches may
be shared only when their content identity is explicit and Projects remain
reproducible without treating the cache as authoritative state.

## Execution flow

The intended public loop is:

```text
files
→ strict validation
→ pinned Project + Harness identity
→ bounded prepare
→ execute
→ structured metrics and artifacts
→ review
→ keep, revert, branch, or promote
→ evidence-bound decision-support report
```

Backtesting, factor discovery, and ML experiments are different Project
programs over this same lifecycle. They do not require separate Workspace
models. Domain runtimes such as Freqtrade are implementation dependencies
behind the Harness contract, not the owner of Workspace or Project semantics.

## Invariants

- A Run records the exact Harness version, Project inputs, asset universe,
  dataset identity or time range, strategy/factor/model identity, metrics,
  artifacts, status, and errors.
- Completed Run evidence is immutable. A new interpretation produces a new
  Run or derived artifact rather than mutating the old result.
- Project paths are confined to their declared root; symlink or traversal
  escapes must be rejected.
- Evaluation contracts are locked for a comparison. Candidate code cannot
  silently edit its Judge, benchmark, dataset split, costs, or acceptance
  floors.
- CLI and Studio are projections of the same Core operations and evidence.
  The Studio must not become a second evaluator.
- The Harness has no live Broker or trading-account authority. Forward
  execution remains outside AutoQuant.
- Routine validation is fast, deterministic, and bounded. Long research loops
  and large backtests require explicit budgets in an active plan.

## Non-goals

- A universal strategy DSL.
- Choosing a different backtest engine for every asset class.
- Live order routing or replacing OpenAlice's trading-account abstractions.
- A mutable global dataset directory that makes Project results
  non-reproducible.
- A generic plugin marketplace, distributed workflow scheduler, or ML
  platform before concrete Projects require those capabilities.

## Authoritative locations

- Current executable Harness manifest: `harness.json`
- Current Harness code: `autoquant/`, `prepare.py`, and `run.py`
- Workspace/Project implementation: `autoquant/workspace.py`
- Agent CLI implementation: `autoquant/cli.py`, `autoquant/cli_contract.py`,
  and `autoquant/capabilities.py`
- Study identity and source closures: `autoquant/studies.py`
- Bounded execution and immutable evidence: `autoquant/runs.py`
- Governed Session/Experiment research and promotion:
  `autoquant/sessions.py`
- Bounded external Researcher orchestration and Campaign evidence:
  `autoquant/research.py`
- Delegated request and derived Brief contracts: `autoquant/briefs.py`
- Immutable Research Report publication and verification:
  `autoquant/reports.py`
- Verified Studio snapshot and local HTTP server: `autoquant/studio.py`
- Verified Portfolio Run diagnostic projection:
  `autoquant/portfolio_explorer.py`
- Packaged browser presentation: `autoquant/studio_assets/`
- Project template construction: `autoquant/templates.py` and
  `autoquant/project_templates/`
- Request-driven dataset intake and Project snapshot verification:
  `autoquant/intake.py`
- Canonical Workspace/Project format: [[docs/PROJECT_FORMAT]]
- Canonical CLI contract: [[docs/CLI]]
- Workspace/Project design: [[docs/design/workspace-project-boundaries]]
- Agent CLI design: [[docs/design/agent-cli-contract]]
- Study/Run evidence design: [[docs/design/study-run-evidence]]
- OHLCV Factor Lab design: [[docs/design/ohlcv-factor-lab]]
- Factor evidence explorer design:
  [[docs/design/factor-evidence-explorer]]
- OHLCV Portfolio Lab design: [[docs/design/portfolio-construction-lab]]
- Portfolio decision explorer design:
  [[docs/design/portfolio-decision-explorer]]
- Research intake and dataset snapshot design:
  [[docs/design/research-intake-and-dataset-snapshots]]
- Governed RL Factor-Policy Lab design:
  [[docs/design/rl-factor-policy-lab]]
- Read-only Study source dependencies and governed Factor-to-RL fusion:
  [[docs/design/cross-study-factor-dependencies]]
- Research selection and visible-test integrity:
  [[docs/design/research-selection-integrity]]
- Research Session loop design: [[docs/design/research-session-loop]]
- External Researcher driver design:
  [[docs/design/external-researcher-driver]]
- Studio observation design: [[docs/design/studio-observation-surface]]
- Quantitative research lifecycle and OpenAlice handoff:
  [[docs/design/quant-research-lifecycle]]
- Studio operator guide: [[docs/STUDIO]]
- Current public Harness contract: [[docs/harness]]
- Planning and documentation governance:
  [[docs/design/documentation-system]]
- Historical immutable snapshots: [[versions/README]]

As Workspace/Project schemas and CLI contracts are implemented, their
canonical references must be added here and to `AGENTS.md`.

## Verification

Use the bounded repository checks:

```bash
uv run python scripts/check_doc_links.py
uv run python -m unittest discover -s tests -v
uv run aq capabilities --json
uv run prepare.py --list-profiles
uv run run.py --list-profiles
```

These commands must not start autonomous research or a long backtest.

## Change checklist

- Update this document when Workspace/Project ownership or execution lifecycle
  changes.
- Update [[docs/harness]] when the current manifest, runtime, data, or result
  contract changes.
- Add focused tests for every new schema, confinement rule, identity, or state
  transition.
- Update both CLI and Studio projections when an operation or artifact becomes
  available on both surfaces.
- Preserve or explicitly regenerate affected immutable fixtures and record the
  reason in the active plan.

## Known gaps

- Branching/Pareto search and robust multi-metric promotion gates are not
  implemented.
- Network ingestion, corporate-action computation, exchange-holiday
  verification, and point-in-time universe contracts are not implemented.
- The V0.5 Freqtrade runner is not adapted into the Study/Run contract.
- Studio is read-only and does not yet provide confirmed Core operations.
- ML is a supported architectural direction but has no execution contract yet.
- OpenAlice-side automatic Project creation and Inbox publication are not
  implemented; AutoQuant emits exact report artifacts for that authority.
