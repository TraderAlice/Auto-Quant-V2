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

The repository currently contains the V0.5 development Harness inherited from
Auto-Quant Classic:

- `harness.json` declares Freqtrade 2026.3 and two OHLCV asset profiles;
- `autoquant/`, `prepare.py`, and `run.py` adapt data and execution;
- `user_data/strategies/` is the current Agent-editable research surface;
- `versions/` preserves completed historical experiments;
- repository-local `data/`, `results.tsv`, and `run.log` are ignored state.

This is a compatibility implementation, not yet the target Workspace/Project
layout. Its active contract is documented in [[docs/harness]]. Structural V2
work must migrate it through explicit plans rather than pretending the target
layout already exists.

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

- Workspace and Project manifests are not implemented.
- Structured immutable RunResult publication is not implemented.
- Study, Session, Candidate review, and promotion lifecycles are not
  implemented.
- The cross-project Studio does not exist.
- ML is a supported architectural direction but has no execution contract yet.
