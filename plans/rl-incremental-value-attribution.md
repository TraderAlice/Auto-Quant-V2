# RL incremental value attribution

- Status: `completed`
- Updated: `2026-07-25`
- Related design:
  [[docs/design/rl-incremental-value-attribution]],
  [[docs/design/causal-rl-policy-state-and-baseline]], and
  [[docs/design/rl-factor-opportunity-audit]].

## Outcome

A quant researcher can explain whether an adaptive policy adds value over the
validation-selected mechanical policy, and locate that value or loss in gross
selection, implementation cost, market regime, action switching, and asset
contribution.

## Scope

- Compare each RL fold/seed path with the exact mechanical baseline selected by
  that fold's validation evidence.
- Preserve independent full-path portfolio accounting for both policies.
- Reconcile gross-return difference minus incremental cost to net active
  return at every timestamp.
- Reconcile per-asset active gross contribution to the portfolio gross-return
  difference.
- Report active return, tracking error, information ratio, relative drawdown,
  hit rate, tail days, regime buckets, action-pair buckets, and asset
  contributions.
- Publish one immutable artifact, strict CLI projection, report summary, and
  Studio view.
- Keep validation as the only selection evidence and test as visible audit.

## Acceptance

- [x] Every attribution row matches one immutable policy action row.
- [x] Each row uses the fold's validation-selected baseline on both validation
      and test.
- [x] Gross minus incremental cost equals net active return.
- [x] Asset active contributions sum to gross active return.
- [x] Aggregate, regime, action-pair, and asset totals reconcile.
- [x] Legacy Runs remain readable without fabricated attribution.
- [x] A bounded real Run, strict tamper test, Studio browser QA, full tests, and
      wheel smoke pass before completion.

## Findings

- The controlled causal encoder reached `32.082895` validation mean net Sharpe
  but remained `-6.032028` behind the selected mechanical baseline.
- Mean-trial-path gross edge / incremental cost / net active return were
  `-0.062631` / `0.001730` / `-0.064362`. Selection, not cost, dominates.
- The paths were materially active on `30.56%` of days and won `37.27%` of
  those active days.
- Below-trend volume and `policy-switch / baseline-hold` rows contain nearly
  the entire loss. The largest action-pair failures replace `intraday` with
  `activity` or `balanced`.
- Losses are concentrated in fold 1 seeds 11 and 29. Fold 1 seed 47 and every
  fold 2 seed are slightly positive, identifying seed stability as the next
  bounded learning target.

## Verification

- Controlled real Run `run-20260725T001214654906Z-8ef7a7479506` succeeded in
  `30.732s`; strict CLI reconstruction passed.
- Full suite — 157 tests in `851.030s`.
- Studio / Reports / CLI subset — 29 tests in `44.051s`.
- Strict RL projection and rehashed-tamper subset — 2 tests in `63.697s`.
- Deterministic duplicate-Run test — passed in `62.338s`.
- Compile, JavaScript syntax, and diff checks — passed.
- Documentation audit — 543 double-links resolved.
- Wheel smoke — all seven required RL template and Studio assets present.
- Browser QA — validation/test attribution switch, mean-trial-path headline,
  updated decision brief, zero horizontal overflow, and zero console errors.
