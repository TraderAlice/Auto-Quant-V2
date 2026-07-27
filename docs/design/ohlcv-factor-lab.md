# OHLCV Factor Lab reference Project

Status: V1 reference Project implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/workspace-project-boundaries]],
[[docs/design/study-run-evidence]],
[[docs/design/factor-diagnostics]], and
[[docs/design/research-session-loop]].

## Scope

This document owns the first executable quantitative reference Project:
transactional template construction, its deterministic OHLCV fixture, the
editable factor API, fixed factor-quality Judge, research objective, and
bounded validation semantics.

It does not define a universal market-data format, Broker simulator, portfolio
optimizer, live-trading interface, production alpha claim, or framework-wide
factor DSL.

## Construction boundary

`ohlcv-factor-lab` is a Project creation template, not a runtime parent.
Construction stages the ordinary Project plus every template-owned file in the
Workspace's hidden creation directory, validates the completed Project and
Study, then atomically renames it into discovery.

The resulting Project owns:

```text
research.md
factors/candidate.py
judges/ohlcv_factor.py
studies/ohlcv-factor-quality/
data/ohlcv/<asset>.csv
```

No created Project imports template resources from the installed AutoQuant
package. The small synthetic dataset is generated deterministically during
construction rather than bundled as a large static asset.

`blank` remains the default Project construction mode. Selecting a template is
explicit and machine-discoverable through the CLI capability contract.

## Dataset contract

The reference Study opts into the content-locked dataset contract from
[[docs/design/study-run-evidence]] with a Project-data-relative trailing
closure:

```json
{
  "paths": ["ohlcv/**"]
}
```

Every matched regular file participates in `datasetHash`. Symlinks, traversal,
missing exact files, empty closures, and matches outside the canonical Project
data root are rejected.

The Session candidate worktree remains data-less. Canonical and worktree Study
identity both hash the owning Project's data root, and the Judge reads that
same root through `AUTOQUANT_DATA_ROOT`. A data change therefore stales the
Session rather than silently changing its evaluation population.

## Editable factor API

The Agent may edit only `factors/candidate.py`. It exports:

```python
def compute_factor(frame: pandas.DataFrame) -> pandas.Series:
    ...
```

`frame` contains one asset's chronological `timestamp`, `open`, `high`, `low`,
`close`, and `volume` observations. The returned Series must:

- have the same index and length as the input;
- contain numeric values or missing warm-up values;
- derive each value only from that row and prior rows;
- avoid mutating the input;
- avoid reading Project data, Judge output, or environment-owned evaluation
  state directly.

The API deliberately uses ordinary pandas and NumPy expressions. AutoQuant
does not wrap them in a legacy event/line abstraction.

## Fixed Judge semantics

The Judge owns target construction and evaluation:

1. Load and strictly validate each declared OHLCV CSV.
2. Compute the candidate factor independently per asset.
3. Audit causality by recomputing selected historical prefixes and comparing
   values already emitted by the full-history computation.
4. Fix 60/20/20 boundaries from the dataset timeline, independently of
   candidate warm-up and coverage.
5. Load the immutable Horizon Mandate, compute its primary and diagnostic
   close-to-close forward returns, and purge signal rows whose target would
   cross a split boundary.
6. Measure per-timestamp cross-sectional Spearman information coefficient.
7. Aggregate chronological train, validation, test, HAC, decay, fixed-tertile,
   fixed-style, per-asset, fold, and causal-regime diagnostics.
8. Publish finite primary `validation_mean_ic`, diagnostic test metrics, a
   research-integrity declaration, a JSON tear sheet, and exact daily CSV
   evidence.

The primary score is validation mean IC at
`primaryForwardBars` only. Test IC and every non-primary horizon are visible
diagnostic evidence and never enter candidate selection. Exact aggregation,
minimum population, and integrity rules live in the fixed Judge source and are
content-hashed with every Run. See
[[docs/design/research-selection-integrity]]. Diagnostic definitions and
artifact reconciliation are fixed by [[docs/design/factor-diagnostics]].

The causality audit is a misuse detector, not a proof against arbitrary hostile
Python. It reliably rejects common future leaks such as negative shifts,
centered windows, or full-sample normalizers whose past outputs change when
future rows are withheld.

## Synthetic fixture

The generated fixture is small, deterministic, and clearly labeled synthetic.
It contains multiple assets and a causal, discoverable relationship between a
current volume surprise and a later return, plus noise. This provides:

- a fast baseline suitable for routine tests;
- a known improvement path for KEEP verification;
- a stable no-lookahead regression target;
- no implication that the factor works on real markets.

Replacing it with real data is a Project-local action. Once files covered by
the Study dataset closure change, existing Sessions become stale and new Runs
receive a new dataset identity.

## Invariants

1. Template construction is atomic with ordinary Project discovery.
2. Created Projects are self-contained and never depend on mutable template
   files.
3. Candidate authority excludes Judge, Study, program, and data bytes.
4. Forward returns and split boundaries are computed only by the fixed Judge.
5. Validation and test periods are chronological and purge-aware, never random
   row splits or candidate-dependent dates.
6. Candidate selection uses validation only; visible test evidence requires a
   new external holdout after test-guided iteration.
7. Data file hashes are preserved in new immutable Run evidence.
8. Routine validation remains bounded and does not invoke a multi-year
   backtest.

## Known limits

- The CSV format is a reference fixture contract, not a production ingestion
  standard.
- Cross-sectional factor quality is not a tradable portfolio return.
- HAC, quantile, style, asset, fold, and regime slices are diagnostics; they do
  not remove multiple-testing risk or become extra promotion objectives.
- The Judge does not model fees, fills, position limits, corporate actions, or
  exchange calendars.
- One factor function is evaluated at a time; ensembles and model fitting are
  future Project templates, not implicit complexity in this one.
