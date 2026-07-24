# Separate candidate selection from exposed test evidence

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/research-selection-integrity]] and
  [[docs/design/quant-research-lifecycle]].

## Outcome

AutoQuant reference Studies promote candidates using validation evidence only,
while Sessions, Studio, and Research Reports disclose trial counts, visible
test evidence, and the need for a new external holdout after test-guided
iteration.

## Context

The factor and portfolio reference Judges originally used the minimum of
validation and test metrics as their primary score. That makes test evidence a
selection input on every Experiment, contradicting the claimed holdout role
and understating multiple-testing risk. RL already uses validation-only
promotion and explicitly labels test visibility; the earlier templates and
collaboration surfaces must adopt the same discipline.

## Scope

### In scope

- Validation-only objective metrics for factor and portfolio templates.
- One standardized Run-level research-integrity contract across all three
  reference Judges.
- Verified Session-derived selection-integrity evidence: candidate trial
  counts, verdict counts, selection split, test visibility, and external
  holdout warning.
- Frozen Research Report evidence and Studio presentation of the same values.
- Known-improvement, Report tamper, snapshot, UI, CLI/template, and packaging
  regression coverage.

### Out of scope

- Pretending visible test data can be cryptographically un-seen.
- A universal Deflated Sharpe implementation without the required return and
  trial-distribution assumptions.
- Organizational access control for external datasets.

## Acceptance

- [x] Factor and portfolio KEEP/REVERT decisions use validation metrics only;
      test metrics remain visible diagnostic evidence and never enter the
      objective.
- [x] Every reference Run declares selection split, test role/visibility,
      whether test enters selection, and the external-holdout rule.
- [x] Session snapshots derive immutable-history trial/verdict counts and mark
      exposed test evidence as selection-contaminated after candidate research.
- [x] Research Reports freeze and verify the exact selection-integrity
      snapshot; Markdown discloses it without relying on Agent-authored prose.
- [x] Studio presents selection metric/split, candidate trials, test visibility,
      and external-holdout status from verified Core data.
- [x] Existing generic Studies remain valid with an explicit `unspecified`
      integrity fallback rather than guessed semantics.
- [x] Bounded tests prove objective isolation, trial counting, report tamper
      rejection, Studio parity, and known improvements.
- [x] Canonical docs, capabilities, wheel contents, full tests, and links agree.

## Work

- [x] Define the standardized Run and Session integrity projections.
- [x] Correct factor and portfolio selection metrics.
- [x] Freeze integrity into Reports and project it through Studio.
- [x] Complete regression, package, documentation, and completion audits.

## Findings and decisions

- 2026-07-24 — A test metric can be reported or used for selection, but not
  both while still being called an untouched holdout.
- 2026-07-24 — V1 does not claim blindness: test metrics are visible. Once a
  Session evaluates candidates, a new external period/dataset is required for
  a fresh production-grade audit.
- 2026-07-24 — Trial count is exact immutable Experiment history. A
  selection-adjusted ratio remains future work until its statistical inputs
  and interpretation are fixed rather than guessed.

## Verification

- `uv run python -m unittest discover -s tests` — 84 tests passed.
- `uv run python scripts/check_doc_links.py` — 193 links resolved.
- `uv run python -m compileall -q autoquant tests` — passed.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `git diff --check` — passed.
- `uv build` — source distribution and wheel built.
- Wheel audit confirmed Core, all three reference Judges/programs, and Studio
  JavaScript are packaged.

## Progress log

- 2026-07-24 — Activated after the post-RL completion audit found test metrics
  directly embedded in both earlier reference objectives.
- 2026-07-24 — Added test-tail mutation regressions proving factor and
  portfolio validation objectives are invariant while test diagnostics change.
- 2026-07-24 — Completed after full Core/CLI/Report/Studio/package validation.

## Completion

Reference KEEP/REVERT is now validation-only. Test evidence remains visible and
is labeled as diagnostic, immutable Experiment history supplies exact trial and
verdict counts, and Core carries the same external-holdout warning through
Sessions, Reports, and Studio. Generic Studies retain explicit unknown
semantics rather than receiving invented research-integrity claims.
