# Frozen external holdout challenge

- Status: `completed`
- Updated: `2026-07-26`
- Related design: [[docs/design/frozen-external-holdout-challenge]],
  [[docs/design/research-selection-integrity]],
  [[docs/design/program-research-dossiers]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Let a completed AutoQuant research desk freeze the exact candidate sources
named by one current immutable Dossier, bind them to a strictly later
caller-supplied OHLCV Project, and execute one non-iterative external-period
challenge whose result is content-locked, auditable, and explicitly lacks
trading or automatic-promotion authority.

## Context

Core already warns that repeated inspection of the visible test split consumes
its holdout value, and the evidence-driven agenda correctly stops positive
lanes with a request for fresh external evidence. That request is currently
only prose. An Agent can create another ordinary Project and accidentally
resume selection, edit the candidate, or lose the exact relationship between
the original Dossier and the later data.

The missing object is not another backtest engine. It is a governed
cross-Project evidence transition:

```text
current source Dossier + frozen leader sources
→ fresh later intake Project
→ immutable holdout binding
→ no Session / no candidate edits
→ one bounded Run per included lane
→ immutable challenge result
```

## Scope

### In scope

- Bind a current completed `ohlcv-research-desk` Dossier to a separate,
  newly-intaken compatible research-desk Project.
- Require exact request, asset universe, asset class, interval surface, and
  strictly later non-overlapping dataset coverage.
- Import the exact Factor and optional RL leader source bytes frozen by the
  source Runs; retain their hashes and Dossier evidence in a self-contained
  target binding.
- Fail closed if target data, Study/Judge authority, imported source, request,
  or binding evidence changes.
- Prohibit governed Sessions and external Researcher Campaigns in a bound
  holdout Project.
- Execute every Dossier-included lane once through the existing fixed Judges
  and publish one immutable result that compares original and external-period
  objective evidence without granting selection, promotion, or trading
  authority.
- Expose binding/result state through Core, JSON Schema, CLI, Agent
  orientation, and Studio.

### Out of scope

- Blind/encrypted datasets, one-time secret reveal, vendor authentication, or
  automatic data acquisition.
- Claiming that one later historical period proves future returns or live
  execution quality.
- Retuning candidates, opening fixed Judge parameters, or carrying forward
  OpenAlice Broker/account authority.
- General cross-repository model registries or arbitrary Study graph imports.

## Acceptance

- [x] Binding rejects overlapping/earlier data, incompatible requests,
  universes, intervals, non-empty target research history, stale source
  Dossiers, or source-byte disagreement across required lanes.
- [x] The target contains a portable immutable binding and exact imported
  source bytes; it remains verifiable after the source Project is unavailable.
- [x] Bound Projects reject Session/Campaign creation and any source or fixed
  authority mutation before execution.
- [x] One command executes each included lane at most once and publishes a
  schema-valid immutable result with source/target dataset identity,
  per-lane source and holdout Run identity/objectives, deltas, and explicit
  external-audit authority.
- [x] `aq orient --json`, concise CLI output, and Studio expose the same Core
  holdout state without inventing pass/fail or trading recommendations.
- [x] Compatibility, tamper, one-shot, CLI, Studio, and bounded real-lane tests
  pass with the complete repository regression and package build.

## Work

- [x] Audit the selection-integrity warning, Dossier evidence, frozen Run
  inputs, intake identity, Session authority, and Studio orientation.
- [x] Define source/target compatibility, portability, one-shot execution, and
  authority boundaries.
- [x] Implement binding/result contracts, import verification, and lane
  execution.
- [x] Enforce frozen Project behavior across Session/Campaign entry points.
- [x] Add CLI/schema/orientation/Studio surfaces and canonical documentation.
- [x] Exercise negative/tamper states and the real Factor/Portfolio/RL path.
- [x] Run browser acceptance, full regression, documentation links, builds,
  then complete, commit, and push.

## Findings and decisions

- 2026-07-26 — The source of candidate truth is each Dossier lane's immutable
  leader Run `sources/` closure, not the mutable current Project tree.
- 2026-07-26 — A holdout Project must be a separate fresh intake identity.
  Mutating the original Study dataset would stale its evidence and erase the
  distinction between research selection and later audit.
- 2026-07-26 — The challenge freezes source code but reuses the exact existing
  Judges. Governed RL may retrain its fixed learning algorithm on the later
  period; only its Agent-authored encoder is imported and frozen.
- 2026-07-26 — V1 requires a strictly later, non-overlapping period and exact
  request/universe/interval compatibility. Broader transfer tests should be a
  separate protocol, not silently called a holdout.

## Verification

- `uv run python -m unittest discover -s tests -v` — 201 tests passed in
  1307.238 seconds on the final integrated source before the additive
  per-lane Harness identity projection; the focused real-lane test was then
  rerun on the exact final contract.
- `uv run python -m unittest tests.test_holdouts
  tests.test_orientation tests.test_studio tests.test_cli` — 26 focused Core,
  CLI, orientation, Studio, portability, tamper, and real
  Factor/Portfolio/RL tests passed in 196.424 seconds on the exact final
  contract.
- `uv run python scripts/check_doc_links.py` — all 717 documentation
  double-links resolve.
- `uv build --out-dir <temporary-directory>` — source and wheel packages
  built; direct archive inspection confirmed `autoquant/holdouts.py` and all
  Studio assets are included.
- `node --check autoquant/studio_assets/studio.js`, Python compile checks, and
  `git diff --check` passed.
- Browser acceptance used a real completed three-lane holdout Project at
  1280×720 and 390×844. The frozen handoff, research chain, Session empty
  state, and inspector exposed no iterative Session command; holdout commands
  were complete, both layouts had no horizontal overflow, and browser logs
  were empty.

## Progress log

- 2026-07-26 — Plan created from the completion audit after evidence-driven
  research agendas made the missing external-holdout operation explicit.
- 2026-07-26 — Added portable Dossier/source binding, one-shot Run/result
  publication, strict target compatibility, frozen Session/Run governance,
  public schemas, CLI, Agent orientation, Studio, and documentation.
- 2026-07-26 — Browser acceptance found and removed stale `session.start`
  suggestions from Dossier, handoff, inspector, and empty-state projections;
  Core and Studio now advertise only holdout execution/show plus read-only
  evidence inspection.

## Completion

Completed on 2026-07-26. AutoQuant can now turn a current Dossier into one
portable, strictly later external-period challenge without reopening candidate
selection or granting trading authority.
