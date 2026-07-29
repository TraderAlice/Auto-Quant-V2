# Add fixed-book drawdown evidence to Book Risk

- Status: `completed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0818-unknown-retrieval-book-risk/desk/workspace/projects/grok-build-unknown-retrieval-book-risk-v0818`
- Related design: [[docs/design/reported-position-book-risk]],
  [[docs/PROJECT_FORMAT]], and [[docs/CLI]].

## Outcome

A fixed descriptive Book Risk Run can answer the common caller question
“what was this book's historical maximum drawdown?” from the same immutable
OHLCV panel and static-weight return convention as its volatility evidence,
without turning the result into an optimizer, scenario, or trading action.

## Context

A fresh installed `aq 0.8.18` Grok worker received one exact hypothetical
eight-name funded book and was explicitly asked for realized volatility,
drawdown, covariance concentration, and component-risk concentration. It
correctly used one fixed Book Risk Run and refused to calculate drawdown
outside strict evidence when neither Run metrics, Book Risk diagnostics,
`book-risk-report.json`, nor `book-risk-path.csv` contained it.

The result answered every requested risk-shape question except drawdown. That
is a real method gap, not an Agent reporting problem.

## Proposed scope

- Define the path as the cumulative return of the same static target weights
  applied to each observed asset-return row used by the fixed covariance
  audit; disclose that this is a daily constant-weight research convention,
  not reconstructed broker holdings.
- Emit primary-window maximum drawdown, peak timestamp, trough timestamp, and
  recovery timestamp/null in the immutable Book Risk report and strict
  Explorer.
- Add the same maximum-drawdown scalar to fixed lookback rows where sample
  capacity permits.
- Reconcile metrics, JSON schema, CSV/report artifacts, Explorer, Studio,
  tamper checks, docs, and one fresh installed-worker retry.
- Preserve reported/hypothetical book identity, no optimizer, no Order, no
  scenario invention, and no live-account authority.

## Implementation decisions

- The fixed path begins at NAV `1.0` on the observed close immediately before
  the first return in the selected window. Each later row applies the static
  supplied asset weights to same-clock close-to-close simple returns; cash has
  zero return. This is a daily constant-weight research path, not reconstructed
  broker holdings.
- Maximum drawdown is signed (`NAV / running peak - 1`) and therefore lies at
  or below zero. Peak, trough, and any recovery are actual timestamps from the
  content-locked close panel.
- A no-loss path uses the initial observed timestamp for peak, trough, and
  recovery. An unrecovered loss has `recoveryTimestamp: null`.
- The full primary-window equity path becomes an immutable CSV artifact.
  Fixed lookback rows carry the scalar maximum drawdown; the primary report
  carries the complete interval identity.
- Compatibility follows immutable Run identity: pre-`0.8.19` Book Risk Runs
  keep their historical artifact contract and expose drawdown as unavailable.
  They are not rejected and are never retrofitted with newly calculated
  evidence.

## Acceptance sketch

- [x] Hand-calculated deterministic fixtures prove return, NAV, and
      peak-to-trough conventions including no-loss and unrecovered cases.
- [x] Current/lookback drawdown values reconcile across Run metrics, report,
      Explorer, and Studio.
- [x] Peak/trough/recovery timestamps are observed-row timestamps and remain
      content-locked.
- [x] Rehashed drawdown or path tampering is rejected.
- [x] A fresh worker answers the caller's exact drawdown request without
      ad-hoc pandas calculations or widening into Portfolio/Order work.

## Notes

This plan should start from the fixed Judge's existing book-return convention,
not from a generic portfolio backtester. Whether rolling sampled risk rows
also need rolling drawdown should be decided from the first implementation
fixture rather than assumed.

The implementation keeps rolling covariance/crowding rows unchanged. The
primary equity artifact already contains the complete largest fixed lookback,
so the strict Explorer derives and reconciles 63/126/252-window maximum
drawdowns from that one path without adding a second sampled path contract.

## Fresh worker evidence

A fresh isolated Grok Build worker received only installed `aq 0.8.19`, the
unchanged prior assignment, and nine raw caller-supplied CSVs. It created
Project `grok-build-book-risk-drawdown-v0819`, executed fixed Study
`ohlcv-book-risk` exactly once as Run
`run-20260729T182310268777Z-51c5e979a05c`, started no Session, edited no
candidate, and used no web or replacement pandas calculation.

Strict evidence reported maximum drawdown `-0.18307858163213264`, peak
`2025-10-29`, trough `2026-03-30`, and recovery `2026-04-27`, while preserving
`provider.retrievedAt: null`. The worker's `framework-needs.md` recorded no
remaining blocker. Independent validation and Studio projection reconciled
the same values and 253-row primary equity path.

## Verification

- `uv run python -m unittest tests.test_book_risk_lab -v`: 16/16 passed.
- `uv run python -m unittest discover -s tests -v`: 311/311 passed in
  794.604 seconds.
- `uv run python scripts/check_doc_links.py`: 1,085/1,085 links resolved.
- The real `0.8.18` field-trial Run
  `run-20260729T174536010358Z-c388e3a0c03f` remains readable in the
  `0.8.19` CLI and Studio with drawdown explicitly unavailable and no
  diagnostic.
- The fresh `0.8.19` worker Run and Studio both reconcile maximum drawdown
  `-0.18307858163213264`, its exact interval, all three lookbacks, and the
  253-row equity path.
- A freshly built wheel installed into an empty Python 3.11 environment
  reports `aq 0.8.19`, publishes the new diagnostics schema, validates the
  worker Project, reads its new evidence, and reads the real `0.8.18` Run
  through the explicit compatibility projection.
