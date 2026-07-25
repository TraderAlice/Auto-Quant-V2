# Qualify candidate factors before portfolio and RL research

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/factor-qualification-funnel]],
  [[docs/design/factor-evidence-explorer]],
  [[docs/design/cross-study-factor-dependencies]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

One immutable Factor Run proves whether a candidate retains validation
predictive information after neutralizing its train-selected dominant OHLCV
style, whether it improves a simple style blend, and whether that residual edge
is chronologically stable before Portfolio or governed-RL research interprets
the source.

## Scope

### In scope

- Train-only dominant-style selection from the fixed Factor style dictionary.
- Same-timestamp cross-sectional rank neutralization.
- Candidate/style/residual/blend IC paths and fixed-horizon summaries.
- Validation-only failure diagnosis, visible-test audit, legacy compatibility,
  CLI, Studio, immutable Report, and Project Dossier evidence.

### Out of scope

- Mining an unbounded factor library, optimizing neutralization, fitting target
  returns, changing the Factor promotion metric, or automatically admitting a
  source into RL.
- Portfolio performance claims, Broker/UTA/account state, orders, or trading.

## Acceptance

- [x] Style selection uses train only and remains fixed on validation/test.
- [x] Daily candidate, style, residual, and blend evidence reconstructs every
      declared mean and observation count.
- [x] Diagnosis distinguishes absent raw edge, statistically weak raw or
      neutral evidence, absent neutral edge, absent
      blend uplift, residual temporal instability, and positive qualification.
- [x] CLI, Studio, Report, and Dossier expose identical frozen evidence without
      changing Factor KEEP/REVERT or RL authority.
- [x] Historical Factor Runs remain readable without invented qualification.
- [x] Deterministic tests, bounded real OHLCV evidence, browser QA, package
      checks, documentation checks, full regression, commit, and push pass.

## Work

- [x] Audit current Factor, Portfolio, and RL evidence boundaries.
- [x] Specify the fixed qualification and authority contract.
- [x] Implement Judge evidence and immutable artifact.
- [x] Implement Core reconstruction, diagnosis, and schema.
- [x] Freeze and render CLI, Studio, Report, and Dossier projections.
- [x] Verify bounded real evidence and legacy behavior.
- [x] Complete regression, documentation, commit, and push.

## Findings and decisions

- 2026-07-25 — Existing style correlation reports redundancy but cannot prove
  whether the candidate retains predictive information after removing that
  exposure.
- 2026-07-25 — The comparison style must be chosen on train overlap, not
  validation alpha, so qualification cannot become a hidden model-selection
  loop.
- 2026-07-25 — One-style contemporaneous rank neutralization remains meaningful
  for small request-driven universes where a four-style multivariate regression
  would saturate the cross-section.
- 2026-07-25 — A positive validation IC is not enough to advance research. The
  bounded Yahoo candidate had positive raw IC but a `0.0782` HAC t-statistic;
  the diagnosis now stops at independent-sample/effect-size evidence instead
  of treating the IC sign as success.
- 2026-07-25 — A deterministic relative-volume candidate can improve the
  locked Factor objective while being a direct `relative_volume_20` style
  clone. Its residual IC becomes zero, proving qualification must remain
  separate from KEEP/REVERT.

## Verification

- `node --check autoquant/studio_assets/studio.js`
- `uv run python -m compileall -q autoquant`
- Six focused Factor Lab, Explorer, CLI, compatibility, and Studio tests passed
  in `18.718s`.
- The immutable required-lane Dossier test passed in `62.785s`.
- `uv run python scripts/check_doc_links.py` resolved 593 documentation
  double-links.
- `uv build` produced the source distribution and wheel.
- `git diff --check`
- `uv run python -m unittest discover -s tests` passed 167 tests in
  `1048.358s`.
- Bounded real Yahoo OHLCV evidence used AAPL, MSFT, NVDA, QQQ, and SPY over
  1,254 sessions from 2021-07-23 through 2026-07-22. The frozen handoff is
  Session `session-20260725T052334536569Z-64fc40a2c320`, Run
  `run-20260725T052323098689Z-6f33d25dc7d0`, and Report
  `report-20260725T052334587594Z-163633399b10`.
- Browser QA at 1,280 px confirmed the five-stage qualification chain, the
  frozen Report proof, correct weak-statistical-evidence routing, and no
  horizontal overflow (`documentWidth == viewportWidth == 1280`).

## Progress log

- 2026-07-25 — Plan activated after RL fusion diagnosis correctly routed the
  reference failure back to factor-sleeve research.
- 2026-07-25 — Added train-only style selection, style-neutral and blend paths,
  exact reconstruction, validation diagnosis, legacy compatibility, and frozen
  CLI/Studio/Report/Dossier projections.
- 2026-07-25 — Real Yahoo evidence exposed the sign-only decision bug; the
  Studio decision brief and qualification cards now require the fixed positive
  HAC threshold and route the next work to factor evidence rather than RL.

## Completion

Completed on 2026-07-25. Candidate factors now have one immutable,
reconstructable qualification funnel before Portfolio or governed-RL
complexity, without changing existing promotion or trading authority.
