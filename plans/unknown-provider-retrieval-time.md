# Preserve unknown provider retrieval time without invented provenance

- Status: `completed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0817-reference-retry/desk/workspace/projects/grok-build-reference-retry-v0817`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/agent-operator-experience]], and [[docs/CLI]].

## Outcome

A coding Agent packaging caller-supplied OHLCV bytes can state that the
original provider retrieval time is unknown without inventing a later
packaging timestamp, while known retrieval times remain strict,
timezone-aware, content-locked claims.

## Context

The fresh installed `0.8.17` Grok retry received historical raw Yahoo CSVs
whose original acquisition time was not preserved. Public schema required a
non-empty `retrievedAt`, so the worker first tried an honest descriptive
string, received `dataset.retrieved-at`, then inserted
`2026-07-30T00:00:00Z` as a packaging clock and relied on free-form terms to
explain that it was not an authenticated retrieval time.

That workaround weakens rather than strengthens provenance. Unknown source
time and known source time are different claims; neither should be silently
converted into the other.

## Scope

### In scope

- Keep `provider.retrievedAt` required as a field.
- Accept either a timezone-aware ISO-8601 string when the original provider
  retrieval time is known, or JSON `null` when it is unknown.
- Preserve the exact string/null through normalized package, Project dataset
  snapshot, hashing, validation, CLI schema discovery, and later intake load.
- Tell Agents in the public schema and operating docs never to substitute a
  later packaging time for an unknown provider retrieval time.
- Cover all current V1–V5 dataset package/snapshot routes through the shared
  provider contract.
- Make the public retry path name the dataset manifest file (not directory)
  and state V1 versus Factor-only V4/V5 template compatibility, after the
  verification worker exposed those adjacent discovery retries.

### Out of scope

- Authenticating provider identity, data acquisition, source URI, corporate
  actions, continuous futures construction, or provider terms.
- Adding a downloader, registry, signed provenance attestation, or generic
  lineage graph.
- Guessing retrieval time from file metadata, market coverage end, Project
  creation time, or the current clock.
- Rewriting existing immutable snapshots or historical Runs.

## Acceptance

- [x] Public dataset-package schema accepts explicit `retrievedAt: null` and
      explains exactly when to use it.
- [x] Empty, naïve, malformed, and non-string/non-null values remain rejected
      with a structured `dataset.retrieved-at` issue.
- [x] Null survives intake normalization, content locking, snapshot
      validation, Project reload, and Studio projection.
- [x] Existing known timestamps and all V1–V5 routes remain valid.
- [x] Passing a package directory produces
      `dataset.manifest-path-required`, and public capability/schema text
      exposes V1 versus V4/V5 template compatibility.
- [x] A fresh installed-CLI Grok worker naturally uses null for unchanged raw
      caller bytes, completes a bounded real assignment, and records no
      retrieval-time workaround.
- [x] Focused/full tests, docs, build/install smoke, clean clone, and release
      verification agree before `0.8.18`.

## Work

- [x] Reproduce and classify the `0.8.17` field-trial friction.
- [x] Implement and test the shared nullable retrieval-time claim.
- [x] Update Agent, CLI, design, status, and originating Project notes.
- [x] Complete installed-state worker retry and release verification.

## Findings and decisions

- 2026-07-30 — JSON `null` is the smallest truthful representation. The field
  remains required, so absence is explicit rather than accidental.
- 2026-07-30 — Package creation time is not provider retrieval time. AutoQuant
  will not infer or substitute one for the other.
- 2026-07-30 — The installed worker used null without prompting beyond the
  caller fact, completed one fixed Book Risk Run, and preserved the claim
  through validation. Its directory-path and V4-template retries were
  accepted as small public discovery improvements.
- 2026-07-30 — Missing Book Risk maximum drawdown is a separate scientific
  evidence gap, promoted to [[plans/book-risk-drawdown-evidence]] rather than
  hidden inside this provenance contract.

## Verification

- Fresh installed `aq 0.8.18` Grok worker:
  - preserved `provider.retrievedAt: null` from public schema discovery
    without substituting another clock;
  - created Project
    `grok-build-unknown-retrieval-book-risk-v0818`;
  - executed exactly one fixed Book Risk Run
    `run-20260729T174536010358Z-c388e3a0c03f`;
  - started no Session, edited no candidate, downloaded no data, and produced
    no invented portfolio, scenario, or Order;
  - left a valid Project whose snapshot and Studio projection still contain
    exact JSON null.
- Shared route test prepared real V1, V2, V3, V4, and V5 fixtures with null;
  known timestamps and invalid empty/naïve/non-string values retain strict
  behavior.
- Related intake/CLI regression passed 50/50 tests in 200.819 seconds.
- Full repository regression passed 309/309 tests in 792.276 seconds.
- Documentation validation resolved 1,085/1,085 double-links.
- Final source distribution and wheel built; fresh Python 3.11 reported
  `aq 0.8.18`, exposed nullable provenance and V1/V4/V5 routing in public
  schema/capabilities, returned `dataset.manifest-path-required` for a
  directory, validated the worker Project, and projected null through Studio.

## Progress log

- 2026-07-30 — Plan activated from the isolated `0.8.17` raw-input Grok
  retry.
- 2026-07-30 — Fresh installed `0.8.18` Book Risk worker completed with
  explicit null provenance and surfaced the next bounded method gap.
- 2026-07-30 — Full regression and final installed-state contract smoke
  completed.

## Completion

Completed for `0.8.18`. The originating workaround is resolved. Missing
fixed-book maximum drawdown remains separately and explicitly owned by
[[plans/book-risk-drawdown-evidence]].
