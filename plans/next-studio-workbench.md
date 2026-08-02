# Next Studio workbench

- Status: `completed`
- Updated: `2026-08-02`
- Related design: [[docs/design/studio-observation-surface]] and [[docs/design/next-studio-workbench]].

## Outcome

AutoQuant contains a reviewable Next.js research workbench that internalizes the approved Evidence Console design, consumes the existing verified read-only Studio snapshot, and keeps private host/plugin integrations outside the open-source repository.

## Context

The repository currently ships a Python standard-library server and a large packaged HTML/CSS/JavaScript presentation. A separately approved Next.js prototype now covers the complete factor-research front half, but it still uses deterministic demonstration data and lives outside this repository. The merge must preserve Core authority and standalone operation while establishing a better-maintained frontend path.

No third-party component library exists to upgrade. The prototype already uses the latest stable Next.js and React releases, so this change internalizes its token and component layer instead of adding a UI dependency.

## Scope

### In scope

- Add a repository-owned `studio-web/` Next.js App Router application.
- Reuse the existing `autoquant-studio-snapshot` HTTP contract through one read-only same-origin proxy.
- Internalize the approved three-layer design tokens and shared UI components.
- Preserve all nine factor-research routes and clearly distinguish connected Core evidence from demonstration records.
- Document and test the open-source/private-plugin boundary.
- Preserve the existing Python Studio and package behavior while the new workbench reaches contract parity.

### Out of scope

- Bundling Node.js or compiled Next assets into the Python wheel.
- Replacing `aq studio serve` in this change.
- Mutation endpoints, command execution, remote hosting, authentication, or multi-user support.
- Private plugin implementations, host orchestration protocols, credentials, proprietary payloads, broker access, accounts, orders, or live trading.

## Acceptance

- [x] `studio-web/` uses the latest stable Next.js and React versions available on 2026-08-02 and adds no component-library dependency.
- [x] All nine research routes render through one internal token/component system and preserve the approved non-trading product scope.
- [x] Connected mode consumes only the verified read-only Studio snapshot and exposes explicit source, validity, freshness, and diagnostics state.
- [x] Demo mode remains deterministic and visibly labelled; it cannot be confused with verified Core evidence.
- [x] Public source contains no private plugin invocation, credential, endpoint, proprietary payload, or host-only implementation.
- [x] Targeted Python Studio tests, frontend tests, lint, production build, responsive browser checks, documentation checks, and package build pass.

## Work

- [x] Audit repository Studio ownership, public snapshot contract, current versions, and plugin/host boundaries.
- [x] Establish design-pipeline foundations and an active integration plan.
- [x] Import and normalize the Next workbench under `studio-web/`.
- [x] Add the read-only Core snapshot bridge and honest connected/demo source state.
- [x] Add boundary tests and durable public documentation.
- [x] Run Python, frontend, build, browser, and open-source leakage checks.
- [x] Complete design-pipeline release-readiness checks.
- [x] Complete final review and PR-ready audit.

## Findings and decisions

- 2026-08-02 — Repository `main` is tagged `v0.9.31`; the current Studio is native HTML/CSS/JavaScript over a verified Python snapshot, not a component-library application.
- 2026-08-02 — npm reports Next.js `16.2.12` and React `19.2.8` as the latest stable releases. The new workbench will pin those exact versions for reproducibility.
- 2026-08-02 — The Next workbench is added beside the packaged Studio first. Replacing the wheel-bundled presentation before behavioral parity would couple Python installation to Node and make the change difficult to review or revert.
- 2026-08-02 — The open-source seam is the existing normalized snapshot contract. Private tools may produce Core-owned evidence outside this repository, but Studio receives only verified snapshot data and never contains their invocation logic.
- 2026-08-02 — Next's latest stable release still resolves vulnerable PostCSS and Sharp versions. Repository overrides move only those existing transitive dependencies to patched releases; the official npm audit is clean.

## Verification

- Frontend tests, boundary scan, lint, production build, browser routes, npm
  production audit, documentation checks, Python compilation, and wheel build
  pass locally.
- The complete Python suite ran 455 tests: 436 pass and 19 fail on existing
  Windows-only shell/path/CRLF assumptions. The changed documentation and
  package boundaries pass their targeted checks; details are recorded in the
  change QA artifact.

## Progress log

- 2026-08-02 — Plan created after repository, version, snapshot, and host-boundary inspection.
- 2026-08-02 — Workbench, Core bridge, honest source modes, boundary scanner,
  documentation, and browser evidence completed.

## Completion

Completed with a separate Next.js workbench, a loopback-only read boundary,
an internalized design system, explicit demo evidence, and PR-ready validation.
