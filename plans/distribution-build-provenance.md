# Distribution build provenance

- Status: `active`
- Updated: `2026-08-02`
- Related design: [[docs/design/distribution-build-identity]],
  [[docs/design/study-run-evidence]],
  [[docs/design/agent-cli-contract]], [[docs/STUDIO]], and
  [[docs/design/versioning-and-release]].

## Outcome

Make an installed AutoQuant distribution identify the exact Git source commit
that built it, instead of losing commit provenance when a Run executes outside
a source checkout. The same current Harness identity must be discoverable
before work and then appear unchanged in immutable Run evidence.

## Context

The isolated `0.9.22` worker installed a candidate wheel and correctly recorded
the package version plus a content-derived Harness source hash, but its Run
reported `harness.commit: unavailable`. Runtime Git probing cannot recover the
build source after installation and can accidentally discover an unrelated
parent repository when a virtual environment lives inside another checkout.

The current Harness source hash also covers Python files and repository build
metadata but omits packaged templates, Studio assets, and Workspace Skills.
Those files materially change what an Agent can do and observe. Exact release
identity therefore needs both immutable build provenance and one complete
runtime-package closure.

## Scope

### In scope

- Generate immutable build identity inside wheel and source distributions from
  the source checkout's exact Git commit and relevant dirty state.
- Preserve that identity when a wheel is built from the generated source
  distribution, without requiring `.git` inside the archive.
- Prefer embedded distribution identity over any unrelated runtime parent Git
  repository; keep direct source-checkout operation honest.
- Hash the complete packaged AutoQuant runtime closure, including Python,
  templates, Studio assets, and Skills, while excluding caches and generated
  build identity metadata from the content digest.
- Add a machine-readable and human-readable CLI identity command; expose the
  same identity through capability discovery and Studio snapshots/UI.
- Keep historical immutable Runs readable and make all new Run, Check, and
  Session evidence consume the same identity function.

### Out of scope

- Signing wheels, supply-chain attestations, PyPI publication, or remote tag
  verification inside the running package.
- Claiming that a dirty candidate wheel is the clean release represented by a
  later tag.
- Adding a Workspace migration or OpenAlice auto-upgrade mechanism.
- Rewriting historical Runs whose original distribution could not name a
  commit.

## Acceptance

- [x] A clean Git build produces a wheel whose `aq version --json`, capability
  discovery, Studio snapshot, and new Run all report the exact build commit and
  `dirty: false` as one identical seven-field Harness object.
- [x] A dirty build reports the current base commit and `dirty: true`; a build
  without Git or embedded identity reports `unavailable` rather than borrowing
  a surrounding repository's identity.
- [x] Building a wheel from the generated sdist preserves the original build
  commit and dirty flag.
- [x] Runtime `sourceHash` changes when any packaged Python, template, Studio,
  or Skill byte changes, and ignores caches or generated identity metadata.
- [x] Existing immutable Run/Session/Check evidence remains readable.
- [x] A fresh installed-wheel Grok worker discovers the identity without
  implementation access, completes one bounded quantitative assignment, and
  hands off a Run whose Harness identity matches its pre-work discovery.
- [ ] Focused tests, complete unit tests, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.23`.

## Work

- [x] Add the build hook and runtime build-identity reader.
- [x] Complete runtime-closure hashing and share one Harness identity contract.
- [x] Add CLI, capability, Studio JSON, and Studio UI projection.
- [x] Add deterministic source, dirty, sdist, wheel, parent-repository, closure,
  and historical-evidence regressions.
- [x] Update Agent, architecture, CLI, Studio, evidence, versioning, status, and
  release documentation.
- [x] Build the candidate wheel and run a fresh Grok field assignment.
- [ ] Complete the release audit, commit, push, tag, and verify `v0.9.23`.

## Findings and decisions

- 2026-08-02 — Package version identifies the declared release line; commit
  identifies the build source; runtime source hash identifies the executable
  package closure. None substitutes for the other two.
- 2026-08-02 — Installed distributions must prefer embedded provenance. Running
  Git discovery upward from `site-packages` can attribute AutoQuant to the
  repository that merely contains the virtual environment.
- 2026-08-02 — `buildProvenance` belongs inside the shared Harness object, not
  beside it. New Run, Check, and Session evidence freezes the seven-field
  identity; historical six-field evidence remains valid.

## Verification

- Focused Harness identity, Run, Check, Session, CLI, Studio, and Report
  regression: 75 tests in 142.681 seconds, all passing.
- Full regression: 430 tests in 1,054.040 seconds, all passing.
- Documentation graph: 1,430 links resolved.
- Clean candidate wheel from commit `f4843fa42b38f33cc05d81a0b401d4395409cc22`:
  SHA-256 `85ea9af755890f63b9e995db1f66f1dba8039628e11e17739aa4192e879c7ab1`.
  The wheel rebuilt through its sdist preserved that commit, `dirty: false`,
  and runtime closure hash
  `afa1b49e7a83465e81db696ac5aea2f5bb6504784bb4ca0d21016a3653fc4e36`.
- Final isolated field Workspace:
  `/Users/ame/autoquant-v0923-build-provenance-field-retry`.
  Grok session `019fbe75-3878-7a10-8de1-78e81b1ffc9c` created Run
  `run-20260801T175455537825Z-60ef712dc897` and Report
  `report-20260801T175531501814Z-f47425637678`; independent public-surface
  replay found one exact seven-field Harness object in version, capabilities,
  Studio, and Run evidence, a valid terminal Project, one Run, one Report,
  zero Sessions, and zero Dossiers.
- Repository sample Run
  `run-20260801T175812734661Z-2105d3af241b` records the same runtime closure
  from the exact clean source checkout and preserves all older sample evidence.

## Progress log

- 2026-08-02 — Plan created from the `0.9.22` field worker's installed-wheel
  `harness.commit: unavailable` observation.
- 2026-08-02 — Build hook, exact-root runtime resolution, complete package
  closure hashing, `aq version`, capabilities, and Studio projection landed.
  Focused version/Run/CLI/Studio regression passed 45 tests in 77.990 seconds,
  including sdist-to-wheel preservation and installation beneath an unrelated
  parent Git repository.
- 2026-08-02 — The first installed-wheel Event Study field pass completed one
  valid NVDA downside-gap Run and Report and preserved the exact source commit.
  It also found two acceptance-test defects: the supplied request used Factor
  fields instead of the Event Study schema, and `buildProvenance` was not yet
  nested in immutable Run evidence. The worker repaired the request correctly;
  the Harness identity contract is being repaired before a fresh final pass.

## Completion

Pending final installed smoke, clean-clone smoke, and remote branch/tag audit.
