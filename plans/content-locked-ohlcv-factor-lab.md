# Content-locked OHLCV Factor Lab

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/study-run-evidence]],
  [[docs/design/research-session-loop]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/ohlcv-factor-lab]].

## Outcome

An Agent can create one self-contained OHLCV Factor Lab Project, edit a
vectorized factor, evaluate it through a fixed no-lookahead Judge, and preserve
the exact local dataset bytes, Runs, Experiments, Campaigns, and Studio
observation as reproducible evidence.

## Context

The generic V2 Core already governs Studies, immutable Runs, resumable Sessions,
bounded external Researcher Campaigns, and a local Studio. It does not yet ship
one real quantitative Project that exercises those layers. Dataset identity is
also declarative only, so changing a CSV does not stale an existing Session or
change the Run input identity.

INM's reference-project pattern demonstrates the useful boundary: construction
copies a complete, independently owned starter rather than making Projects
inherit mutable framework files. AutoQuant needs the same pattern, while
generating a small deterministic dataset during transactional Project creation
so wheel installs do not carry a large market-data fixture.

## Scope

### In scope

- Add optional Project-data-relative file closures to the Study dataset
  contract and bind their SHA-256 inventory into dataset identity.
- Preserve the exact manifest and hash behavior of existing declarative-only
  Studies and historical Runs.
- Make canonical Project data available to Study identity checks performed
  against a data-less Session worktree.
- Add a transactionally constructed `ohlcv-factor-lab` Project template with a
  deterministic synthetic multi-asset OHLCV fixture.
- Add one fixed vectorized factor Judge with chronological splits,
  cross-sectional factor metrics, and an explicit causality/no-lookahead audit.
- Expose template and dataset-path construction through the Agent CLI,
  capability descriptors, schemas, and docs.
- Prove the bounded Project → Run → Session → Experiment → Campaign → Studio
  path without a long backtest or live trading dependency.

### Out of scope

- Production market-data download, adjustment, exchange-calendar, or symbol
  master contracts.
- Portfolio simulation, Broker integration, Freqtrade migration, live
  execution, or transaction-cost modeling.
- A universal factor DSL, ML training platform, parameter sweep, or large
  checked-in dataset.
- Replacing historical V0/Freqtrade research snapshots.

## Acceptance

- [x] `aq project create ... --template ohlcv-factor-lab` atomically publishes
      a complete Project with editable factor, fixed Judge, fixed Study,
      research program, and deterministic local OHLCV data.
- [x] The starter's baseline Run succeeds quickly and publishes finite
      train/validation/test factor metrics plus a report artifact.
- [x] A known causal factor improvement can receive KEEP, while a future-leaking
      factor is rejected by the Judge's causality audit.
- [x] Changing a declared data file changes `datasetHash` and `inputHash`,
      stales an existing Session, and is visible as a file-hash inventory in new
      Run evidence.
- [x] Existing Studies without dataset paths serialize and hash exactly as
      before; existing RunResult objects without data source hashes still load.
- [x] A bounded fake external Researcher Campaign can edit/evaluate the starter,
      and `aq studio snapshot` observes its verified Run/Experiment/Campaign
      evidence.
- [x] CLI schemas, capabilities, docs, wheel contents, focused tests, full
      tests, and documentation links all pass.

## Work

- [x] Audit Study/Run/Session data-root semantics and transactional Project
      construction.
- [x] Record the content-lock, worktree, template, and Judge authority design.
- [x] Implement optional dataset closures, canonical data-root loading, frozen
      inventories, and backward-compatible Run validation.
- [x] Implement transactional template construction and public CLI discovery.
- [x] Implement the deterministic OHLCV generator, editable baseline factor,
      fixed Judge, and research program.
- [x] Add regression, no-lookahead, known-improvement, Campaign, Studio, build,
      and CLI evidence.
- [x] Complete the acceptance audit, update durable docs, commit, and push.

## Findings and decisions

- 2026-07-24 — Session worktrees intentionally omit `data/`; Study loading must
  accept the owning Project's canonical data root instead of copying potentially
  large data into every Session.
- 2026-07-24 — Dataset `paths` is optional. Absence preserves the V1 declarative
  dataset object and hash byte-for-byte; presence opts the Study into file
  content identity.
- 2026-07-24 — Project templates are construction inputs, not shared runtime
  dependencies. The completed Project owns copied source and generated data.
- 2026-07-24 — The first reference Judge measures factor research rather than
  Broker behavior. It uses only OHLCV, chronological splits, forward returns
  owned by the fixed Judge, and causality checks owned outside the editable
  factor closure.

## Verification

- `uv run python -m unittest discover -s tests -v` — 63 tests passed.
- `uv run python scripts/check_doc_links.py` — 129 links resolved.
- `uv run python -m compileall -q autoquant tests` — passed.
- `git diff --check` — passed.
- `uv build --out-dir <temporary>` — source distribution and wheel built; the
  wheel contains all Factor Lab and Studio package assets.
- Bounded reference evidence: baseline `score` approximately `0.1106`; causal
  relative-volume candidate `score` approximately `0.7990` and KEEP; negative
  shift candidate failed with `factor.lookahead`.
- The Factor Lab Campaign/Studio smoke produced two verified Runs, one KEEP
  Experiment, and one terminal Campaign in the shared snapshot.
- No checked-in historical Run was regenerated; every acceptance Run used a
  temporary generated Project.

## Progress log

- 2026-07-24 — Plan created after auditing Study hashing, Run execution,
  Session worktree materialization, and INM's self-contained starter pattern.
- 2026-07-24 — Added backward-compatible content locks, transactional template
  construction, the fixed causal factor Judge, and full-loop evidence.

## Completion

Shipped the first directly usable V2 quantitative reference Project. Agents can
now start from ordinary pandas factor code, iterate through the same governed
Run/Session/Campaign protocol used by the generic Core, and let humans observe
the verified evidence in Studio. Production data ingestion, Broker simulation,
ML templates, and richer multi-metric gates remain separate future outcomes.
