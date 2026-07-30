# Manifest-rooted staged dataset intake

- Status: `completed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0825-adopt-existing-event/desk/workspace/projects/grok-build-adopt-existing-event-v0825`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/agent-cli-contract]], and
  [[docs/design/agent-operator-experience]].

## Outcome

A coding Agent with caller-supplied OHLCV already staged in a nested directory
can discover and use the dataset-package manifest as the safe source root,
intaking those exact files without first making an Agent-managed duplicate,
while Core retains portable relative paths and strict confinement.

## Context

The fresh installed `0.8.25` Grok Event Study worker received unchanged Yahoo
CSV files under `workspace/staging/raw-ohlcv/`. It placed its package manifest
inside a new Project-side `intake-materials/` directory, then copied both raw
files beside that manifest because public schema and capability text said only
that asset paths are confined beneath the package directory.

Core already supports the correct no-intermediate-copy layout: put
`dataset-package.json` at `workspace/staging/` and use manifest-relative paths
such as `raw-ohlcv/NVDA.csv`. A direct reproduction preserved the exact source
hashes and produced the required Project-local normalized snapshot. The gap is
therefore Agent discoverability, not path authority.

## Scope

### In scope

- Describe each dataset asset path as a portable POSIX-relative path resolved
  from the directory containing the package manifest.
- Show that placing the manifest at the staged files' common ancestor avoids
  an intermediate raw-data copy.
- Project the rule through public JSON schema, capability discovery, CLI help,
  Agent guidance, and intake documentation.
- Make the adjacent Research Request source artifact/revision pairing explicit
  in the same public discovery surfaces after the verification worker's only
  first-attempt intake retry.
- Add deterministic coverage for nested manifest-relative staged sources and
  retain current path/symlink rejection.
- Prove the route with a fresh installed-wheel Grok field trial.

### Out of scope

- Absolute paths, parent traversal, symlinks, Workspace-relative source roots,
  a second path authority, or a relaxed confinement boundary.
- Eliminating the Project-local normalized content-locked dataset snapshot.
- A data downloader, registry, dataset-package builder, or automatic manifest
  generation.
- Treating post-intake editing of the Agent-owned `research.md` as a defect.

## Acceptance

- [x] Public schema, capability output, and CLI help independently expose the
      manifest-root rule and a concrete nested staging example.
- [x] A package manifest at a staged source common ancestor intakes nested
      assets directly, preserves exact source hashes, and validates normally.
- [x] Parent, absolute, and symlink paths remain rejected; no new path
      authority or fallback is introduced.
- [x] Agent and design documentation distinguish the avoidable intermediate
      copy from the intentional Project-local normalized snapshot.
- [x] Research Request schema rejects a half-present source
      artifactPath/artifactRevision pair and tells Agents to provide both or
      use two explicit nulls.
- [x] A fresh installed-wheel Grok worker naturally constructs the no-copy
      layout, completes one bounded assignment, and records no path workaround.
- [x] Focused/full tests, docs, build/install smoke, clean clone, and release
      verification agree before `0.8.26`.

## Work

- [x] Reproduce and classify the `0.8.25` field-trial friction.
- [x] Implement and test manifest-root discoverability across public surfaces.
- [x] Close the verification worker's source-revision discovery retry without
      weakening provenance.
- [x] Update Agent, CLI, design, status, and originating Project notes.
- [x] Complete installed-state worker retry and release verification.

## Findings and decisions

- 2026-07-30 — Core's current package-root confinement is already the smallest
  safe and portable model. The source files need not be siblings of the
  manifest; they need only be descendants of its directory.
- 2026-07-30 — The Project-local normalized snapshot is intentional durable
  research state. This plan removes only the worker-created staging duplicate.
- 2026-07-30 — `research.md` remains Agent-maintained after intake. The
  originating worker's manual rewrite was expected research clarification, not
  template corruption.
- 2026-07-30 — The fresh `0.8.26` worker discovered the manifest-root layout
  before intake and made no raw-data duplicate. Its only first-attempt retry
  came from a half-present Research Request source artifact/revision pair.
  Runtime semantics are correct, so public schema/help will expose and enforce
  the existing pair rather than accepting unversioned artifact provenance.

## Verification

- Pre-change direct reproduction:
  - package manifest at `/tmp/v0825-no-copy-repro/staging/dataset-package.json`;
  - sources at `staging/raw-ohlcv/NVDA.csv` and `SPY.csv`;
  - asset paths `raw-ohlcv/NVDA.csv` and `raw-ohlcv/SPY.csv`;
  - `aq project intake` and `aq validate` passed;
  - source and normalized SHA-256 values remained respectively
    `57c6c8c...d904` and `7dad9b4e...688e2`;
  - no worker-managed raw-data duplicate was required.
- Fresh installed-wheel `0.8.26` verification worker:
  - naturally placed `dataset-package.json` at `workspace/staging/` with
    `raw-ohlcv/NVDA.csv` and `raw-ohlcv/SPY.csv`;
  - preserved both original hashes, created one intentional normalized
    Project snapshot, and made no intermediate raw-data copy;
  - created one Project, one fixed Event Run, and zero Sessions;
  - left strict Event Explorer, validation, orientation, and Studio valid;
  - recorded one initial `request.source-revision` retry, now included in this
    plan's public-discovery fix.
- Fresh final-wheel `0.8.26` Grok worker:
  - discovered both the manifest-root and paired-source contracts from public
    surfaces and completed intake without any CLI failure;
  - created Project `nvda-gap-event-v0826-final` and exactly one fixed Run
    `run-20260730T001840054647Z-ce288a4c9166`, with zero Sessions;
  - preserved source SHA-256 values
    `57c6c8c...d904` / `7dad9b4e...688e2` and left only the two caller files
    plus the intentional two Project snapshot files;
  - left strict Event Explorer, Project validation, orientation, and one
    Workspace Studio snapshot valid with no diagnostics.
- Focused intake/CLI/version regression passed 56/56 tests in 231.321 seconds.
- Full repository regression passed 322/322 tests in 924.699 seconds.
- Documentation validation resolved 1,117/1,117 double-links.
- Final source distribution and wheel built; a fresh Python 3.11 environment
  installed `aq 0.8.26`, exposed both public contracts, created and validated
  a Factor Project, and contained the Event template plus Studio assets.

## Progress log

- 2026-07-30 — Plan activated from the isolated `0.8.25` Grok Event Study
  field trial after the safe no-intermediate-copy route was reproduced.
- 2026-07-30 — Fresh installed-wheel Grok verification proved the new package
  layout discovery and promoted its only adjacent first-attempt retry into the
  same public intake-contract fix.
- 2026-07-30 — A second fresh final-wheel worker completed without retry; full
  regression, docs, distribution, and installed-state smoke passed.

## Completion

Released as `v0.8.26`. AutoQuant now makes its existing safe package-root
model discoverable to coding Agents and makes the existing paired source
provenance rule executable in the public schema. No alternate path authority
or data-copy semantic was introduced.
