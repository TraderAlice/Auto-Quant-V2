# Retire the flat Freqtrade Harness

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/retired-flat-freqtrade-harness]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/research-intake-and-dataset-snapshots]].

## Outcome

Make AutoQuant V2 the only executable repository architecture by removing the
repository-root Freqtrade arena, its archived research data, its runtime
dependency, and its public compatibility claims.

## Context

The flat `prepare.py` / `run.py` arena helped bridge Auto-Quant Classic into
the first V2 commits. It now duplicates Project intake, execution, evidence,
and Agent ownership with a weaker contract and keeps a large Freqtrade runtime
installed even though no V2 Project imports it.

V2 is pre-alpha and the owner has explicitly released the repository from
backward-compatibility requirements. Historical Git commits remain the archive.

## Scope

### In scope

- Remove the flat Harness executables, manifest, Freqtrade config, strategies,
  notebooks, chart, and version-snapshot data.
- Remove Freqtrade-only Python modules, exports, tests, and dependencies.
- Retain only the generic OHLCV normalization required by V2 intake under a
  V2-owned module.
- Remove current documentation and contributor rules that advertise the flat
  compatibility surface.
- Leave a small tombstone at historical documentation link targets so old plan
  records remain navigable without presenting an executable interface.

### Out of scope

- Rewriting immutable V2 RunResult, Report, or Dossier schemas.
- Renaming algorithm/protocol identifiers that legitimately end in `-v1`.
- Removing bounded “evidence unavailable” states from V2 artifacts; those are
  separate schema-tightening work.
- Purging the removed files from Git history.

## Acceptance

- [x] No root flat-Harness command or Classic research data remains.
- [x] AutoQuant imports and installs without Freqtrade, TA-Lib, Jupyter, or
  Matplotlib.
- [x] V2 request intake still normalizes conventional OHLCV safely.
- [x] Current docs describe only Workspace → Project → Study → Run execution.
- [x] Bounded and complete deterministic regression, package build, and
  documentation validation pass.

## Work

- [x] Audit the flat-Harness dependency and documentation closure.
- [x] Remove files, modules, tests, exports, and dependencies.
- [x] Move generic OHLCV normalization into the V2 intake boundary.
- [x] Rewrite current architecture, quick-start, and contributor guidance.
- [x] Verify, commit, and push the retirement.

## Findings and decisions

- 2026-07-27 — `autoquant.intake` is the only V2 consumer of the old
  `autoquant.data` module, and it needs only conventional OHLCV normalization.
- 2026-07-27 — `autoquant.profiles`, `autoquant.metrics`, and
  `autoquant.freqtrade_adapter` form an isolated Classic/Freqtrade closure.
- 2026-07-27 — Git history, rather than a live `versions/` data tree, is the
  durable archive for removed pre-V2 experiments.
- 2026-07-27 — CSV remains in the base runtime. Parquet/Feather support is one
  explicit `columnar` extra so the default environment does not carry PyArrow.
- 2026-07-27 — `jsonschema` is a development dependency used by contract tests,
  not a transitive runtime accident inherited from the old stack.

## Verification

- `uv sync` removed 153 installed packages from the old dependency closure;
  the resulting development environment is 86 MB.
- `uv run python -c ...` confirmed both `freqtrade` and optional `pyarrow` are
  absent from the base environment while `aq capabilities --json` succeeds.
- `uv run python -m unittest tests.test_ohlcv
  tests.test_intake.RequestDrivenIntakeTests.test_v2_research_desk_runs_one_shared_surface_across_all_lanes
  -v` — four focused normalization and complete three-lane intake tests passed.
- `uv run python -m unittest discover -s tests -v` — all 215 tests passed in
  1766.559 seconds.
- `uv build` — source distribution and wheel built successfully.
- `uv run python scripts/check_doc_links.py` — all 845 documentation
  double-links resolved.
- `uv run python -m compileall -q autoquant tests` and `git diff --check`
  passed.

## Progress log

- 2026-07-27 — Plan activated after caller authorization to remove old
  interfaces and data instead of carrying compatibility into V2.
- 2026-07-27 — Removed the root commands, manifest, config, strategies,
  notebook, chart, five archived experiment trees, and exposed ignored candle
  data/result journal.
- 2026-07-27 — Removed the isolated Freqtrade modules and runtime closure,
  relocated generic OHLCV normalization, and rewrote current repository docs.
- 2026-07-27 — Focused, complete, packaging, documentation, and environment
  verification passed.

## Completion

Completed on 2026-07-27. AutoQuant V2 Projects and the `aq` CLI are now the
only executable architecture in the current tree. Classic source and evidence
remain reachable from Git history but impose no dependency or compatibility
contract on V2.
