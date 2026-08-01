# Multi-source observed Factor packaging

- Status: `complete`
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

- [x] V6 strictly represents at least two providers and binds every asset to
  exactly one content-addressed source package.
- [x] The public compositor preserves every V5 asset byte and observation,
  performs no alignment/fill/transformation, and publishes an exact audit.
- [x] Invalid, incompatible, ambiguous, unsafe, overlapping, or tampered
  inputs fail without a partial output package.
- [x] V6 passes strict Factor intake, snapshot reload/tamper checks, one Run,
  Explorer, Report, CLI, and Studio while showing source-level provenance.
- [x] Generated Agent Skill bundles explain and expose the single-source V5 →
  multi-source V6 route without implementation inspection.
- [x] A fresh installed-wheel Grok coworker uses two distinct source packages
  for one bounded cross-market Factor question and stops truthfully on the
  evidence.
- [x] Focused tests, full regression, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.26`.

## Work

- [x] Define V6 manifest, snapshot, JSON Schema, and composition authority.
- [x] Implement Core validation/materialization and the bundled compositor.
- [x] Add deterministic positive, negative, integration, CLI, and Studio
  coverage plus public documentation.
- [x] Advance version/sample evidence and run a fresh installed-wheel field
  assignment.
- [x] Complete the release audit, commit, tag, push, and verify `v0.9.26`.

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

- Focused V6 composition, close-time causality, public Candidate Contract, and
  CLI capability tests pass.
- `uv lock --check`, complete module compilation, and all 1,459 documentation
  double-links pass.
- `uv run python -m unittest discover -s tests` passes all 439 tests in
  1,063.457 seconds. The first release-audit run exposed two stale V5-only CLI
  assertions; the public capability was already correct, the assertions were
  advanced to V6, and the entire suite was rerun from the beginning.
- The final clean wheel has SHA-256
  `901c9ed1fdc83bdb9484e85dec3b4a578d6668a400480102cc8a1f022ddaefe0`
  and records candidate commit `01404f725571130fd84a5b74f2e9e4e31384c7e1`.
- Fresh Grok (`grok-4.5-build`, 25 turns, session
  `019fbf4c-d98a-7db2-aba4-dd07f54ded68`) used only that installed wheel. It
  confirmed the corrected V6 Candidate Contract, preserved both provider
  identities and all four source files byte-for-byte, created exactly one
  succeeded Run, one completed Session, and one Report, then stopped on a weak
  negative result without opening Portfolio or RL. Transcript SHA-256 is
  `0ca5ab8dc682814567d8134b60f7867c8976e7846c30fb0c602d6ef86d38233c`.
- An independent field verifier reconciled 1,606 Toyota observations against a
  separately computed backward as-of QQQ return. Values matched exactly and
  every selected QQQ close was strictly earlier than the Toyota close. Its
  receipt is `grok-field-trials/cohort-39-multi-source-observed-v0926-final/
  evidence/field-audit.json` outside the release repository.
- Final source/wheel build, isolated installed-version/capability smoke,
  repository-root Workspace validation, no-local-override clean-clone replay,
  package-content audit, and remote branch/tag identity passed before
  publication.

## Progress log

- 2026-08-02 — Plan created from the explicit multi-provider provenance gap
  retained by the completed `0.9.25` calendar-materialization release.
- 2026-08-02 — Implemented strict V6 package/snapshot authority, public
  transactional V5 compositor, independent V6 package audit, source-aware
  CLI/Studio disclosure, and deterministic end-to-end plus fail-closed tests.
- 2026-08-02 — The focused Workspace Skill suite passed 40 tests; the V6
  integration separately proved JSON Schema, exact byte preservation, strict
  intake, CLI projection, Run, Factor Explorer, immutable Report, Studio, and
  rejection of a rehashed unknown-source snapshot.
- 2026-08-02 — Advanced the candidate to `0.9.26` and regenerated both Agent
  discovery roots plus `autoquant-skills.json` from the canonical Skill; Skill
  validation and all 1,459 documentation links pass.
- 2026-08-02 — Added sample Run
  `run-20260801T212920787441Z-4fafdd0a9412` from clean candidate commit
  `3cd8cd99de9602b1903dc6bbd8ec8714c64026cc`; the immutable result reports
  Harness `0.9.26`, `dirty=false`, and preserves all fourteen earlier Runs.
- 2026-08-02 — The first installed-wheel Grok trial completed the full route
  and independently produced a truthful negative Factor Report, while also
  detecting that the public Candidate Contract still advertised a V5-only
  schema pattern and legacy rectangular labels for a correctly running V6
  surface. The trial was retained as defect-discovery evidence rather than
  accepted as the release proof.
- 2026-08-02 — Corrected the V6 public schema and observation labels, added an
  exact contract regression, rebuilt from a clean commit, and reran the whole
  assignment with a fresh Grok coworker. The final trial confirmed the public
  surface before writing research code and passed independent byte,
  provenance, lifecycle, Studio, and causal as-of verification.
- 2026-08-02 — The complete 439-test regression, documentation, build,
  installed-wheel, package-content, root Workspace, clean-clone, tag, and
  remote identity gates passed. OpenAlice remained unchanged at `v0.8.31`.

## Completion

`v0.9.26` is published as the narrow multi-source observed Factor packaging
release. It adds no downloader, provider authentication, alignment engine,
universal provenance graph, Portfolio/RL V6 intake, or host migration policy.
