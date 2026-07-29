# Add fixed-book drawdown evidence to Book Risk

- Status: `proposed`
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

## Acceptance sketch

- [ ] Hand-calculated deterministic fixtures prove return, NAV, and
      peak-to-trough conventions including no-loss and unrecovered cases.
- [ ] Current/lookback drawdown values reconcile across Run metrics, report,
      Explorer, and Studio.
- [ ] Peak/trough/recovery timestamps are observed-row timestamps and remain
      content-locked.
- [ ] Rehashed drawdown or path tampering is rejected.
- [ ] A fresh worker answers the caller's exact drawdown request without
      ad-hoc pandas calculations or widening into Portfolio/Order work.

## Notes

This plan should start from the fixed Judge's existing book-return convention,
not from a generic portfolio backtester. Whether rolling sampled risk rows
also need rolling drawdown should be decided from the first implementation
fixture rather than assumed.
