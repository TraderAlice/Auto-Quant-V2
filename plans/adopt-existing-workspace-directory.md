# Adopt an existing Workspace directory safely

- Status: `completed`
- Updated: `2026-07-30`
- Originating desk:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0824-cap-fidelity-retry/desk`
- Related design: [[docs/design/workspace-project-boundaries]],
  [[docs/design/agent-cli-contract]], and
  [[docs/design/agent-operator-experience]].

## Outcome

A Coding Agent that has already staged caller-owned input files inside its
intended desk directory can explicitly adopt that directory as an AutoQuant
Workspace without moving or rewriting those inputs, while ordinary
`workspace init` remains an empty-directory constructor and refuses ambiguous
ownership.

## Context

A fresh no-memory, no-web, no-subagent Grok worker using installed `aq 0.8.24`
prepared request and dataset packaging below `./workspace` before running
`aq workspace init ./workspace`. Core returned `path.not-empty`; the worker
recovered by moving packaging outside the Workspace and completed the
Allocation task correctly.

The failure was safe but operationally unnatural. A Workspace may legitimately
contain host or caller material outside its configured `projects/`, and the
repository root already demonstrates that surrounding files do not redefine
Project discovery. Silently accepting every non-empty directory would be too
broad, however: initialization creates a new ownership boundary and must not
overwrite manifests or adopt a pre-existing Projects tree by accident.

## Scope

### In scope

- Add an explicit `workspace init --adopt-existing` mode.
- Preserve every pre-existing entry byte-for-byte.
- Require the target to be a real directory or an absent path, with no
  Workspace manifest, local override, or pre-existing `projects/` entry.
- Keep default initialization's current empty-target requirement.
- Make human help, capability discovery, structured failure text, docs, and
  tests explain both safe routes: external staging or explicit adoption.
- Prove the flow with a fresh installed-wheel Grok fixed-Study assignment
  whose caller inputs are already staged under the intended Workspace.
- Release the bounded change as `0.8.25`.

### Out of scope

- Importing or interpreting arbitrary existing Project trees.
- Recursively discovering Projects or treating staging as Workspace-owned
  quantitative state.
- Deleting, moving, rewriting, or Git-ignoring caller files.
- Making adoption implicit, interactive, or host-specific.
- Changing Project intake, dataset semantics, Study evaluation, or trading
  authority.

## Acceptance

- [x] Default init still rejects a non-empty target with an exact recovery
      message that names external staging and `--adopt-existing`.
- [x] Explicit adoption preserves nested caller files and creates only the
      manifest plus a new empty `projects/`.
- [x] Adoption rejects target/root symlinks, files, existing base/local
      manifests, any existing `projects` file/directory/symlink, and leaves
      all pre-existing bytes unchanged on every failure.
- [x] Capability JSON and `--help` fully describe the option, ownership
      boundary, and effect.
- [x] A fresh installed-wheel Grok worker discovers adoption, creates one
      requested Project and one fixed Run from inputs already under the target,
      with zero Sessions and no staging relocation.
- [x] Full regression, documentation graph, final wheel install, exact-commit
      clone smoke, commit, tag, and canonical push pass for `v0.8.25`.

## Work

- [x] Reproduce and preserve the installed-release worker friction.
- [x] Implement safe opt-in adoption and deterministic failure contracts.
- [x] Add Core/CLI/capability/compatibility/symlink/preservation tests.
- [x] Update canonical Workspace, CLI, Agent-experience, status, and release
      documentation.
- [x] Complete fresh packaged retry and release audit.

## Findings and decisions

- 2026-07-30 — Non-empty initialization must remain opt-in because creating a
  Workspace is an ownership decision, not ordinary directory inspection.
- 2026-07-30 — Existing `projects/` is never adopted. Its meaning cannot be
  established without validating every entry and deciding whether the caller
  intended those directories to become Workspace-owned Projects.
- 2026-07-30 — Staging remains surrounding caller/host material. Adoption
  preserves it but does not add it to Workspace manifests, Project identity,
  or Git policy.

## Verification

- Fresh installed-wheel worker:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0825-adopt-existing-event`
- Fixed Event Run:
  `run-20260729T233228959130Z-27b7bbb73ced`
- One valid Project, one succeeded fixed Run, zero Sessions, unchanged hashes
  for assignment/NVDA/SPY staging files, strict Event Explorer, and valid
  Studio without diagnostics.
- `uv run python -m unittest discover -s tests -v` — 321 passed in 826.969 s.
- `uv run python scripts/check_doc_links.py` — 1,113 links resolved.
- Final `0.8.25` source/wheel build and fresh Python 3.11 install passed;
  installed CLI capability/help plus a byte-preserving adopted-Workspace smoke
  reconciled.

## Progress log

- 2026-07-30 — Plan created from the only concrete operational friction in the
  successful `0.8.24` capped-Allocation Grok retry.
- 2026-07-30 — Implemented explicit safe adoption, default recovery guidance,
  parser/capability discovery, collision preservation tests, and canonical
  ownership documentation.
- 2026-07-30 — A fresh installed-wheel `0.8.25` worker adopted co-located
  staging without relocation, completed one bounded fixed Event Study, and
  independently reported no scientific or evidence cost.
- 2026-07-30 — Full regression and documentation verification passed; final
  source/wheel install and exact-commit clone audits closed the release.

## Completion

Released as `v0.8.25`.
