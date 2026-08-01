# Multi-source observed Factor packaging

- Status: `active`
- Updated: `2026-08-02`
- Target release: `0.9.26`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/design/versioning-and-release]].

## Outcome

Let an installed AutoQuant coworker combine multiple independently acquired,
audited, close-time-aware V5 packages into one strict observed Factor dataset
without erasing which provider supplied each asset, inventing a synthetic
provider claim, aligning calendars, filling missing observations, or rewriting
market bytes.

## Context

`0.9.25` can deterministically turn one date-only V4 package and explicit
exchange-calendar authority into a truthful V5 package. V5 still owns exactly
one top-level provider and adjustment claim. Real cross-market research may
need each venue's appropriate source—for example a Japanese asset from one
provider and U.S. context from another. Concatenating those assets into V5
would falsely attribute every row to one provider or hide a private merge
behind a synthetic provider name.

The `0.9.25` plan deliberately left multi-provider provenance to a separate
contract. The next narrow step is composition, not a data lake or universal
provenance graph.

## Scope

### In scope

- Add a V6 observed base-bar Factor package with the same completed-close,
  observed-only, absent-no-fill, target-owned horizon semantics as V5.
- Replace V5's single provider in V6 with a complete ordered `sources` vector.
  Each source freezes its own id, exact source-package id/version/hash, and
  provider claim; every asset names exactly one source id.
- Keep one uniform top-level `priceAdjustment` and base interval across the
  composition. Refuse heterogeneous adjustments rather than pretending raw,
  split-adjusted, dividend-adjusted, and provider-adjusted returns are
  interchangeable.
- Add a bundled `compose_observed_packages.py` procedure to
  `$package-autoquant-ohlcv`. It consumes at least two strict V5 manifests,
  includes their complete disjoint asset inventories, copies exact asset bytes
  into a transactional V6 output, and emits a content-bound audit.
- Fail closed on source-package drift, duplicate source ids/symbols, unsafe or
  symlink paths, incompatible interval/market/panel/adjustment authority,
  duplicate or malformed timestamps, invalid V5 inputs, occupied output, or
  any byte/value/row-count change.
- Freeze V6 sources and per-asset source ids into Project snapshots, Run
  identity, CLI/Studio discovery, README handoff, and load-time tamper checks.
- Keep V5 readable as a single-source contract; V6 is the only honest
  multi-source route.
- Prove V5 → V6 → strict intake → Factor Run → Explorer → immutable Report
  with deterministic fixtures and a fresh installed-wheel Grok assignment
  using two genuinely distinct provider claims.

### Out of scope

- Fetching data, authenticating provider claims, choosing providers, or
  deciding that two providers are economically comparable.
- Selecting a subset from a source package, deduplicating overlapping symbols,
  resolving conflicting observations, vendor consensus, stitching history,
  resampling, currency conversion, calendar alignment, missing-row fill, or
  corporate-action reconciliation.
- Mixing price-adjustment claims, accepting V1–V4 inputs directly, composing
  multi-interval derived bars, or extending V6 to Portfolio/RL/fixed Studies.
- Treating source-package hashes as authenticated exchange truth; they prove
  only exact caller-supplied evidence identity.

## Acceptance

- [ ] V6 strictly represents at least two providers and binds every asset to
  exactly one content-addressed source package.
- [ ] The public compositor preserves every V5 asset byte and observation,
  performs no alignment/fill/transformation, and publishes an exact audit.
- [ ] Invalid, incompatible, ambiguous, unsafe, overlapping, or tampered
  inputs fail without a partial output package.
- [ ] V6 passes strict Factor intake, snapshot reload/tamper checks, one Run,
  Explorer, Report, CLI, and Studio while showing source-level provenance.
- [ ] Generated Agent Skill bundles explain and expose the single-source V5 →
  multi-source V6 route without implementation inspection.
- [ ] A fresh installed-wheel Grok coworker uses two distinct source packages
  for one bounded cross-market Factor question and stops truthfully on the
  evidence.
- [ ] Focused tests, full regression, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.26`.

## Work

- [ ] Define V6 manifest, snapshot, JSON Schema, and composition authority.
- [ ] Implement Core validation/materialization and the bundled compositor.
- [ ] Add deterministic positive, negative, integration, CLI, and Studio
  coverage plus public documentation.
- [ ] Advance version/sample evidence and run a fresh installed-wheel field
  assignment.
- [ ] Complete the release audit, commit, tag, push, and verify `v0.9.26`.

## Findings and decisions

- 2026-08-02 — V6 composes already close-time-aware V5 packages. Calendar
  derivation remains a separate auditable step per source, so composition does
  not become a second timestamp oracle.
- 2026-08-02 — The first contract includes each input's complete inventory.
  Subsetting would introduce another selection manifest and risk silently
  changing the meaning of the audited source package.
- 2026-08-02 — Adjustment must be uniform, but provider metadata must not be.
  This solves the observed provenance problem without claiming that arbitrary
  heterogeneous price histories are comparable.

## Verification

Pending.

## Progress log

- 2026-08-02 — Plan created from the explicit multi-provider provenance gap
  retained by the completed `0.9.25` calendar-materialization release.

## Completion

Pending.
