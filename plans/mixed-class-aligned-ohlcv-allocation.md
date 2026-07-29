# Mixed-class aligned OHLCV Allocation

- Status: `completed`
- Updated: `2026-07-30`
- Originating desk:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0822-mixed-class-allocation/desk`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/portfolio-native-allocation-lab]],
  [[docs/design/caller-owned-asset-position-roles]], and
  [[docs/design/caller-owned-benchmark-reference]].

## Outcome

A Coding Agent can truthfully intake one aligned daily or multi-interval OHLCV
panel containing several economic asset classes, and a fixed Allocation Study
can compare its long-only ERC candidate set with a funded reference containing
context-only assets without silently adding those reference assets to the
candidate optimizer.

## Context

A fresh no-memory, no-web, no-subagent Grok worker using only installed
`aq 0.8.22` attempted a fixed monthly ERC question over AAPL/NVDA equities,
GLD/TLT funds, and a fund-class SPY reference. Research Requests already
require per-instrument `assetClass`, but aligned V1 packages allow only one
top-level class and intake requires every requested class to equal it. Package
class values `equity`, `fund`, and a descriptive mixed value all failed with
`request.dataset-asset-class`; no Project was created.

The same fixed question exposed a second contract contradiction. SPY belongs
only to the 60/40 reference, so its correct position role is `context-only`.
Request validation forbids fixed benchmark weight on a context-only asset,
while marking SPY `long-only` would place it in `tradableAssets` and change the
ERC question. Allocation runtime already simulates a separately funded
reference over the complete research universe, so this is an intake/contract
restriction rather than an accounting limitation.

## Scope

### In scope

- Let V1–V4 package asset rows optionally carry one complete per-asset
  `assetClass` vector.
- When that vector exists, require every class to be supported and require the
  top-level class to be its canonical common class or `mixed` summary.
- Keep legacy homogeneous packages without per-asset classes valid and
  unchanged.
- Freeze supplied per-asset classes into Project dataset snapshots and verify
  them against the Research Request and normalized snapshot on every load.
- Let `ohlcv-allocation-lab` fixed-weight reference legs be requested
  `context-only` without adding them to candidate `tradableAssets`, caps,
  targets, or risk contributions.
- Project the truthful dataset/reference partition through CLI, Explorer,
  Studio, docs, schemas, and immutable Run identity.

### Out of scope

- Changing OHLCV alignment, calendars, annualization, pricing, or volume
  semantics.
- Arbitrary optimizer methods, expected returns, custom reference schedules,
  Orders, or live-trading authority.
- Adding a new position role solely for benchmarks; `context-only` already
  expresses zero candidate position authority.
- General fixed-weight benchmark support in Portfolio/RL Mandates outside the
  fixed Allocation route.

## Acceptance

- [x] The unchanged mixed AAPL/NVDA/GLD/TLT/SPY package and request create one
      valid fixed Allocation Project without class flattening.
- [x] Package and snapshot schemas reject partial class vectors, unsupported
      classes, wrong top-level summaries, request/package mismatches, and
      rehashed class tampering.
- [x] Legacy V1–V4 packages and historical snapshots without per-asset classes
      remain valid.
- [x] SPY remains `context-only` in the candidate contract and has zero
      candidate target/executed/risk contribution while carrying 60% of the
      separate fixed reference target.
- [x] One immutable Run, strict Allocation Explorer, orientation, and Studio
      all validate with no Session or trading authority.
- [x] A fresh installed-wheel Grok retry completes the unchanged assignment
      without metadata workaround.
- [x] Full regression, documentation graph, wheel install, and exact-commit
      clone smoke pass before `v0.8.23`.

## Work

- [x] Reproduce the gap with a fresh installed-release worker and preserve its
      exact structured failures.
- [x] Add the complete optional per-asset class vector to package, intake,
      snapshot, and load-time identity contracts.
- [x] Remove the false Allocation restriction on context-only fixed-reference
      legs while retaining the candidate/reference authority partition.
- [x] Add deterministic end-to-end, compatibility, schema, tamper, CLI, and
      Studio tests.
- [x] Update public schemas, capabilities, canonical docs, status, and version.
- [x] Complete installed-wheel Grok retry and release audit.

## Findings and decisions

- 2026-07-30 — A package-level `mixed` string alone is not evidence: the exact
  per-symbol classes must be present, complete, content-locked, and matched to
  the Research Request.
- 2026-07-30 — Per-asset classes are optional only as a complete vector so
  legacy packages remain valid without Core guessing missing members.
- 2026-07-30 — A fixed-reference leg may be context-only because reference
  accounting is evaluation, not candidate position authority. Runtime already
  constructs separate reference roles and weights over the full universe.

## Verification

- Fresh installed-wheel worker 1:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0823-mixed-class-allocation-retry`
- Fresh final-wheel worker 2:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0823-mixed-class-allocation-final`
- Final Run:
  `run-20260729T221653432441Z-dab337ec6897`
- One valid Project, one succeeded fixed Run, zero Sessions, exact input-byte
  hashes, complete per-asset classes, SPY candidate target/executed/risk
  contribution all zero, strict Allocation reconciliation, and valid Studio.
- `uv run python -m unittest discover -s tests -v` — 315 passed in 805.092 s.
- `uv run python scripts/check_doc_links.py` — 1,104 links resolved.

## Progress log

- 2026-07-30 — Plan created from the isolated `0.8.22` mixed-class Allocation
  field trial.
- 2026-07-30 — Implemented complete optional V1–V4 per-asset classes, frozen
  snapshot/load-time verification, and context-only fixed Allocation reference
  legs. Deterministic V1–V4 materialization plus full mixed Allocation
  Run/Explorer/Studio coverage pass.
- 2026-07-30 — A fresh installed-wheel `0.8.23` worker completed the unchanged
  assignment in one Project, one fixed Run, and zero Sessions. Its only
  concrete contract friction was the compact Study/Explorer class summary;
  Study inspection and the Run-bound Allocation read model now project the
  complete verified class map without changing the Study definition.
- 2026-07-30 — A second fresh final-wheel worker repeated the complete
  assignment after the read-model fix. Full regression passed 315 tests in
  805.092 seconds and all 1,104 documentation links resolved.

## Completion

Released as `v0.8.23`.
