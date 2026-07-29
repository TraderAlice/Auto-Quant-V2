# Make Factor preflight reference-aware and promotion closure explicit

- Status: `completed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0816-raw-intake/desk/workspace/projects/grok-build-raw-intake-v0816`
- Related design: [[docs/design/candidate-preflight-feedback]],
  [[docs/design/panel-native-factor-api]],
  [[docs/design/research-session-loop]], and
  [[docs/design/agent-operator-experience]].

## Outcome

An unfamiliar Factor worker can use a caller-declared context or benchmark
asset in its candidate without adding a fake fallback solely for preflight,
and can recognize KEEP promotion as the terminal Session close without trying
an inapplicable completion command afterward.

## Context

A fresh Grok Build worker received only installed `aq 0.8.16`, one English
Factor-only assignment, and nine raw adjusted-OHLCV CSVs. It independently
authored the strict request/package, created a Project, established a
baseline, and implemented a causal downside-resilience factor against
caller-declared context/benchmark asset SPY.

The first CandidateCheck failed with `factor.empty` because the fixed Factor
preflight used `study.dataset.universe[:2]` (AAPL/MSFT), while the full Judge
panel correctly included SPY. The worker added an equal-weight market fallback
only to make preflight exercise a different path. Its next Check passed and
the single authorized Experiment KEEP improved validation mean IC from
`-0.115138` to `0.125601`.

After publishing the exact Report, guarded promotion correctly copied the KEEP
leader and terminally marked the Session `promoted`. The worker nevertheless
attempted `session.complete` before and after promotion because public command
language did not state the mutually exclusive close paths compactly enough.

## Scope

### In scope

- Build the bounded Factor preflight panel from up to two position-capable
  assets plus every fixed mandate context asset and named benchmark asset that
  belongs to the Study universe.
- Keep the 256-timestamp bound and full Judge authority unchanged.
- Disclose the exact bounded asset surface in the passing Check message.
- Preserve two-asset behavior for template/custom Studies with no usable fixed
  mandate reference metadata.
- Make CLI capability/help, next-action descriptions, promotion response, and
  post-promotion completion diagnostics state that KEEP promotion is one
  terminal close path and baseline completion is the alternative.
- Keep `promoted` and `completed` as distinct mutually exclusive states; do
  not fabricate an idempotent completion receipt after promotion.

### Out of scope

- Turning preflight into a smaller backtest or selection gate.
- Changing formal Factor metrics, KEEP/REVERT rules, Report authority, or
  Project source-promotion semantics.
- Inferring arbitrary symbol references from candidate source.
- Adding automatic data acquisition or a generic feature/reference DSL.
- Rewriting the originating `0.8.16` Check, Experiment, Report, promotion, or
  research result.
- Redesigning caller-supplied provider acquisition provenance. The installed
  retry exposed that `retrievedAt` cannot honestly represent unknown legacy
  acquisition time; that separate intake-contract question remains recorded
  in the retry Project rather than being folded into this Session fix.

## Acceptance

- [x] A SPY-dependent candidate without an alternate-market fallback passes
      preflight when SPY is a fixed context/benchmark asset.
- [x] The same bounded Check includes two decision assets, all declared
      references, at most 256 timestamps, and reports that surface exactly.
- [x] No-request/no-reference template behavior remains deterministic and
      bounded to the first two Study assets.
- [x] Promotion is machine- and human-readable as terminal closure, and
      `session.complete` after promotion returns a specific already-promoted
      explanation rather than generic `session.closed`.
- [x] Existing Check identity/authority, Experiment selection, promotion
      atomicity, historical artifacts, CLI/Studio parity, and templates remain
      valid.
- [x] Focused/full tests, docs, build/install smoke, and a fresh installed-CLI
      worker retry agree before release.

## Work

- [x] Reproduce and test the preflight reference omission and promotion
      terminality ambiguity.
- [x] Implement fixed-mandate reference selection and terminal-close
      disclosures.
- [x] Update Agent, CLI, design, status, and field-trial documentation.
- [x] Complete installed-state worker retry and release verification.

## Findings and decisions

- 2026-07-30 — Preflight must use Study-fixed dependency metadata, not the
  mutable request or candidate-source symbol inference. The fixed Portfolio
  mandate already owns context assets and benchmark identity and participates
  in Study/Check input identity.
- 2026-07-30 — `promoted` and `completed` are intentionally alternative
  terminal states. Improving explanation is safer than accepting a no-op
  command that appears to create a second close event.
- 2026-07-30 — Grok's positive validation KEEP is research evidence, while
  negative test IC, fold instability, and style overlap remain scientific
  limitations rather than framework defects.
- 2026-07-30 — The installed `0.8.17` retry passed a strictly SPY-required
  candidate on the first Check, spent one Experiment, published one Report,
  promoted once, recognized `promoted` as terminal, and issued no second close.
- 2026-07-30 — Retry feedback showed that the technically exact decision
  sample could be mistaken for the full universe. The release message now says
  `bounded decision sample` and includes sampled/full position-capable counts.

## Verification

- Fresh installed `aq 0.8.17` Grok retry:
  - Check `check-20260729T170808260744Z-58d2f7e549e6` passed first try with a
    candidate that raises when SPY is absent and has no proxy fallback;
  - Experiment `exp-0001-efdb39a4eeb5` KEEP improved validation mean IC from
    `-0.115138` to `0.158148`;
  - Report `report-20260729T170935463829Z-b39635bfac1a` was published,
    promotion terminally closed the Session, and the worker issued no second
    close command.
- 73 related CLI/Check/Session/Report/orientation/repository tests passed in
  77.644 seconds before full regression.
- Full repository regression passed 307/307 tests in 816.360 seconds.
- Documentation validation resolved 1,074/1,074 double-links.
- Final source distribution and wheel built; a fresh Python 3.11 environment
  reported `aq 0.8.17`, exposed terminal promotion/completion capability
  descriptions, validated the checked-in sample Project, and produced equal
  CLI/Studio Agent Work Briefs.

## Progress log

- 2026-07-30 — Plan activated from the isolated raw-input Grok field trial.
- 2026-07-30 — Core fix, installed-worker retry, full regression, docs, and
  final package smoke completed.

## Completion

Completed for `0.8.17`. The retry also exposed an independent
unknown-provider-retrieval-time intake question; it remains explicitly
recorded and does not weaken this plan's terminal or preflight outcome.
