# Align daily Factor baselines with the actual panel surface

- Status: `proposed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0827-final-price-volume/desk/workspace/projects/grok-price-volume-factor-v0827-final`
- Related design: [[docs/design/panel-native-factor-api]] and
  [[docs/design/ohlcv-factor-lab]].

## Outcome

A pure daily Factor intake starts from a daily-only baseline candidate whose
declared components and source match the panel it can actually receive, while
multi-interval packages retain their current causal feature-aware baseline.

## Context

The final `0.8.27` Grok worker correctly saw `featureIntervals: []`, but the
V1 daily template baseline still declared `momentum_3h_4`,
`momentum_12h_2`, and `momentum_1d_3`. Missing feature branches no-op safely,
yet the baseline is a mismatched comparison and overstates multi-interval
intent on a daily-only desk.

## Scope

### In scope

- Select or derive baseline candidate source from the verified interval
  surface during intake.
- Keep Factor components, candidate contract, Run artifacts, and template
  consistency checks aligned.

### Out of scope

- Choosing a request-specific null, changing the fixed Judge, or weakening
  multi-interval causality.

## Acceptance

- [ ] Daily V1/V4/V5 Factor intake declares only available base-clock inputs.
- [ ] Multi-interval intake retains its complete feature-aware baseline.
- [ ] Baseline Runs, Sessions, sample Projects, tests, and documentation agree.

## Work

- [ ] Reproduce the mismatch independently and choose the smallest template
      selection boundary.
- [ ] Implement and verify surface-aligned baseline source.

## Findings and decisions

- 2026-07-30 — Proposal recorded from a final installed-wheel worker; no
  implementation route has been selected yet.

## Verification

- Pending.

## Progress log

- 2026-07-30 — Proposed from the `0.8.27` final Factor field trial.

## Completion

Pending.
