# Project one Factor Run into a professional evidence explorer

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/factor-evidence-explorer]],
  [[docs/design/factor-diagnostics]],
  [[docs/design/research-selection-integrity]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

An Agent or human can inspect one verified Factor Run as a bounded professional
tear sheet: predictive path, horizon decay, quantile behavior, stability by
fold/regime/asset, fixed-style overlap, coverage, and turnover. CLI and Studio
consume the same Core object, and visible test evidence remains audit-only.

## Context

The fixed Factor Judge already publishes strong evidence, but most of it is
buried in nested Run metrics and three immutable artifacts. Studio exposes only
headline values, while Agents must know internal artifact layouts to recover
daily evidence. That makes it too easy to optimize one aggregate IC without
seeing temporal instability, horizon collapse, non-monotonic quantiles, style
repackaging, or single-asset dependence.

Portfolio Runs already have a bounded artifact-specific explorer. Factor
research needs the equivalent read model before adding more model families or
parameter search.

## Scope

### In scope

- A bounded Core projection over the fixed `factor-report`, `factor-daily`, and
  `factor-quantiles` artifact set.
- Full-file verification and reconciliation against immutable Run metrics
  before deterministic sampling.
- IC path, horizon profile, quantile summary/path, fold/regime/asset stability,
  style overlap, coverage, and rank-turnover evidence.
- Explicit training, validation-selection, and test-audit roles.
- `aq run factor`, a versioned schema/capability, Studio projection, and exact
  copyable command.
- Responsive charts and tables that format—but never derive—the Core object.

### Out of scope

- Candidate-selected horizons, quantiles, regimes, styles, or acceptance gates.
- Portfolio construction, execution/capacity claims, parameter sweeps,
  selection-adjusted statistics, or live trading.
- Browser artifact downloads or browser-side CSV parsing.

## Acceptance

- [x] Core verifies a successful fixed Factor Run and all three declared
      artifacts before returning evidence.
- [x] Daily and quantile artifacts reconcile to the immutable aggregate metrics
      across every split and horizon.
- [x] Output is bounded, deterministic, preserves split/regime anchors, and
      discloses total/sampled rows.
- [x] Factor summary, horizon decay, quantiles, folds, regimes, assets, styles,
      coverage, and turnover are machine-readable with explicit split roles.
- [x] Test rows are labelled audit-only and never become a selection claim.
- [x] `aq run factor --json`, schema discovery, capabilities, Studio snapshot,
      and copyable next actions share the same Core read model.
- [x] Studio renders the latest verified Factor Run without reading artifacts
      or recomputing statistics in JavaScript.
- [x] Tamper, malformed CSV, row/byte limits, non-Factor Runs, full regression,
      browser interaction, and wheel packaging are verified.

## Work

- [x] Audit current Factor artifacts, Portfolio explorer pattern, CLI, and
      Studio gaps.
- [x] Implement the verified bounded Core projection and schema.
- [x] Add CLI/capability and Studio snapshot contracts.
- [x] Build the responsive Factor Explorer and browser interactions.
- [x] Complete deterministic, regression, documentation, and wheel evidence.

## Findings and decisions

- 2026-07-24 — The Judge already owns the correct professional evidence. The
  missing layer is a safe read model, not new candidate authority.
- 2026-07-24 — V1 projects the fixed 1/5/10-bar, tertile, causal-regime, and
  OHLCV-style protocol. It is intentionally not a generic chart DSL.
- 2026-07-24 — Core reconciles full artifacts before sampling so the browser
  cannot mistake a convenient subset for authoritative evidence.

## Verification

- `node --check autoquant/studio_assets/studio.js`
- `uv run python -m unittest discover -s tests -q`
  — 113 tests passed on final bytes in 194.061 seconds.
- Deterministic tests verify 320 complete daily rows before 40–400 point
  sampling, all split/horizon means and observation counts, every quantile
  group/spread/monotonicity, split/regime/extreme anchors, schema, and Studio
  projection.
- Adversarial tests reject a non-Factor Run, out-of-range points, oversized
  artifacts, and a truncated daily artifact even after its Run manifest is
  deliberately rehashed. Studio retains the immutable Run while dropping only
  the invalid explorer claim.
- A fresh Python 3.11 environment installed the built wheel with all 161
  resolved dependencies, then successfully ran `aq schema factor-diagnostics`,
  `aq run factor`, `aq studio snapshot`, and packaged-asset checks.
- Browser QA verified IC/quantile, 1/5/10-bar, validation/test-audit, and
  regime/fold/asset/style controls, responsive layout, copy-only CLI, semantic
  labels, and the disclosure footer.
- A bounded real Yahoo Finance intake used 752 aligned daily observations for
  SPY, QQQ, IWM, TLT, GLD, and EFA from 2023-01-03 through 2025-12-31. The
  fixed baseline honestly displayed validation Rank IC `-0.063087`, HAC t
  `-1.766613`, weakest fold `-0.115830`, and maximum momentum overlap
  `0.648322` rather than styling adverse evidence as success.

## Progress log

- 2026-07-24 — Activated after Session-level comparison exposed candidate
  trade-offs but left the factor evidence beneath each candidate opaque.
- 2026-07-24 — Implemented full artifact reconciliation, bounded shared path
  anchors, normalized horizon/quantile/stability/style evidence, CLI/schema,
  and the responsive Studio explorer.
- 2026-07-24 — Real ETF evidence exposed negative one-bar validation behavior,
  positive longer-horizon behavior, and material momentum overlap, proving the
  multi-layer view catches conclusions a headline metric would hide.

## Completion

Delivered one verified Core/CLI/Studio Factor tear sheet that serves AI
iteration and human review without granting the browser statistical or
selection authority.
