# Expose portfolio diversification and correlation-breakdown stress

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/portfolio-diversification-stress]],
  [[docs/design/portfolio-risk-governor]],
  [[docs/design/portfolio-decision-explorer]],
  [[plans/report-bound-mechanical-decision-handoff]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

One verified Portfolio Run explains whether apparently different positions are
independent risk bets or one crowded trade. For every validation/test decision
date and the current historical book, Core reconstructs covariance component
concentration, effective risk bets, and a perfect position-aligned correlation
upper bound. The evidence reaches CLI, Studio, immutable Report, Project
Dossier, and the OpenAlice handoff without becoming an optimizer or trading
instruction.

## Scope

### In scope

- Strict reconstruction from the immutable Portfolio decision ledger.
- Current-book and validation/test diversification summaries.
- Absolute component-risk HHI and effective risk bets.
- A fixed 25% / 50% / 100% covariance-blend ladder from the observed causal
  covariance toward the perfect position-aligned correlation upper bound.
- Fixed-ceiling breach, stress multiplier, weakest historical date, and
  per-asset stress-risk share.
- Frozen Report/Dossier evidence, Studio presentation, schema, tests, real-data
  QA, and canonical documentation.
- Flat and insufficient-risk-history states remain explicit.

### Out of scope

- A covariance optimizer, cluster-aware resizing, risk-parity solving, or
  changing the fixed Judge objective.
- Estimating a probability for the perfect-correlation scenario.
- Selecting candidates from validation/test stress, changing KEEP/REVERT, or
  gating Portfolio/RL progression.
- Live positions, account capital, Broker/UTA state, or trading authority.

## Acceptance

- [x] Every available active-book row reconciles sample covariance variance,
      causal own volatility, component-risk concentration, and the fixed
      perfect position-aligned correlation upper bound.
- [x] Current evidence shows sample forecast, stress forecast, multiplier,
      ceiling breach, effective risk bets, largest risk contributor, and
      per-asset stress-risk shares.
- [x] Validation and visible test separately expose coverage, breach rate,
      median/p95/maximum stress multiplier, median/minimum effective risk bets,
      and the weakest dated book.
- [x] Flat, unavailable, negative component contribution, and single-position
      books have explicit finite semantics.
- [x] CLI, Studio, Report, and Dossier consume the same Core object and retain
      context-only, no-trading authority.
- [x] Tamper, schema, deterministic, real-data, browser, package, documentation,
      and full regression checks pass before commit and push.

## Work

- [x] Audit current sizing, covariance governor, component-risk, and handoff
      surfaces.
- [x] Specify fixed stress semantics and authority boundaries.
- [x] Implement and schema the strict Portfolio diversification projection.
- [x] Freeze and verify it through Report/Dossier decision support.
- [x] Add Studio summary/detail and canonical documentation.
- [x] Complete deterministic/real/browser/package/full-regression evidence.

## Findings and decisions

- 2026-07-25 — Current sizing anatomy shows only the latest component-risk HHI.
  It does not expose effective risk bets, historical concentration, or what
  happens if correlations align with the position signs.
- 2026-07-25 — The existing ledger already contains executed weights, exact
  next-bar asset returns, portfolio variance, and component variance for every
  asset/date. Core can reconstruct the same causal covariance window and its
  own-volatility diagonal without a new mutable artifact.
- 2026-07-25 — The terminal stress covariance is the deterministic
  positive-semidefinite upper bound in which every active pair is perfectly
  correlated in the direction that makes their PnL risks reinforce. Its daily
  volatility is `sum(abs(weight_i) * own_vol_i)`.
- 2026-07-25 — A terminal upper bound alone alarmed almost every real Yahoo
  date and was too blunt for a trader. The fixed ladder therefore blends the
  observed covariance 25%, 50%, and 100% toward that upper bound, preserving
  positive semidefiniteness while showing when diversification first fails.
- 2026-07-25 — The scenario is intentionally an upper bound, not a forecast,
  likelihood, pass/fail gate, or reason to optimize against visible test data.
- 2026-07-25 — Real provider-adjusted Yahoo evidence for AAPL/MSFT/NVDA/QQQ/SPY
  (`run-20260725T073205741490Z-4ab22ffdf47c`) had 4 current active positions,
  2.4705 effective risk bets, 10.1423% observed covariance volatility, and a
  15% fixed ceiling. The 25% / 50% / 100% scenarios reached 15.7118% /
  19.7701% / 26.0547%, so the current book first breached at the shallowest
  rung.
- 2026-07-25 — On the same real evidence, validation 25% / 50% / 100% breach
  rates were 77.6% / 97.6% / 100%; visible-test rates were 39.6% / 74.4% /
  98.8%. This confirms that the ladder distinguishes moderate breakdown from
  the almost-always-alarming terminal endpoint.
- 2026-07-25 — Studio browser QA at 1280×900 showed the complete ladder,
  split rates, and asset-risk table without document-width overflow. The
  responsive 641-pixel layout collapsed the summary, ladder, and split cards
  into one column as specified.

## Verification

- `uv run python -m unittest tests.test_portfolio_explorer
  tests.test_reports tests.test_dossiers tests.test_cli tests.test_studio` —
  59 affected tests passed in 484.969 seconds.
- `uv run python -m unittest discover -s tests` — all 174 repository tests
  passed in 1196.325 seconds.
- `uv run python scripts/check_doc_links.py` — 626 documentation double-links
  resolved.
- `uv run python -m compileall -q autoquant tests`,
  `node --check autoquant/studio_assets/studio.js`, and `git diff --check`
  passed.
- `uv build` produced the source distribution and wheel; direct wheel
  inspection confirmed all three packaged Studio assets.
- Real Yahoo Run
  `run-20260725T073205741490Z-4ab22ffdf47c` reconstructed all 250 validation
  and 250 visible-test scenario dates and produced the current/split numbers
  recorded above.
- Browser QA used the live packaged Studio contract at 1280×900 and its
  responsive 641-pixel layout. The complete ladder and per-asset table rendered
  without document-width overflow.

## Progress log

- 2026-07-25 — Plan activated after a professional portfolio-workflow audit
  identified correlation concentration as the largest remaining mechanical
  construction and OpenAlice handoff gap.
- 2026-07-25 — Core/schema, CLI, Studio, Report/Dossier freezing, deterministic
  edge-state tests, real Yahoo reconstruction, and browser presentation are
  implemented.
- 2026-07-25 — Affected and full regression, documentation links, package
  contents, JavaScript/Python syntax, diff hygiene, real-data, and browser
  evidence passed. Plan completed.

## Completion

AutoQuant now distinguishes nominal asset count from effective risk bets and
shows when diversification begins to fail under a fixed causal covariance
stress ladder. The exact verified object is available through CLI and Studio,
frozen through Report/Dossier/OpenAlice handoff, backward-compatible with
legacy reports, and explicitly unable to select, resize, or trade.
