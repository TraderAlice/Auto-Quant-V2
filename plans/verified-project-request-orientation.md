# Surface verified Project requests in Agent orientation

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/study-run-evidence]].

## Outcome

A fresh coding Agent entering a fixed template Project receives its real
machine-bound question from `aq orient` even when the Project was constructed
locally rather than through external intake. Core distinguishes verified
Project request authority from delegated intake and flexible Markdown, refuses
unbound or tampered request files, and continues to give CLI and Studio the
same source-aware work brief.
The completed change ships as AutoQuant `0.8.10`.

## Context

The third independent Grok Build trial exercised a different route:
`ohlcv-allocation-lab`, one fixed non-predictive ERC baseline, no editable
candidate, and no Session. The research and all evidence surfaces worked, but
orientation returned an empty local question despite a valid Project-root
`request.json` whose canonical hash is frozen into the Allocation Study
dependency.

The cause is structural. `build_agent_work_brief` reads a request only through
the external intake loader. Shipped fixed Allocation, Event Study, and Book
Risk template constructors also create strict requests and request-bound
dependencies, but intentionally do not create external intake manifests.
The same trial naturally used `## Question`, demonstrating that the new
Markdown fallback remains unnecessarily coupled to a narrow heading phrase.
The originating observation is preserved in the Project's
`framework-needs.md`.

## Scope

### In scope

- Load a Project-root `request.json` only when it strictly validates and its
  canonical request hash is present in a fixed Study dependency.
- Preserve external delegated intake as first authority.
- Add distinct `project-request` question provenance with exact source and
  request path.
- Recognize the exact Markdown heading `Question` as a flexible local fallback
  while retaining explicit-heading, fence, and bounded-content safety.
- Version the Agent Work Brief method and keep CLI/Studio parity.
- Cover valid, tampered, unbound, delegated-precedence, Markdown-fallback, CLI,
  fixed-template, and Studio behavior.
- Prove the change with a fresh external-Agent retry and package smoke.

### Out of scope

- Treating any arbitrary `request.json` as authority.
- Parsing caller intent from free prose or making Markdown a rigid schema.
- Changing the fixed Allocation result, Study/Judge semantics, or Session
  lifecycle.
- Solving the separate coarse top-level Study authority labels, Explorer
  payload size, CLI installation, or Run command envelope-shape friction.

## Acceptance

- [x] A shipped fixed Allocation Project exposes its validated request title
      and question with `origin: project-request` before any Run.
- [x] The request source is accepted only when at least one fixed Study
      dependency binds the same canonical request hash.
- [x] Tampered, invalid, symlinked, or unbound request files never become
      orientation claims.
- [x] Delegated intake remains first authority; an exact `Question` Markdown
      heading works only as the flexible local fallback.
- [x] CLI JSON, human CLI, and Studio share the same strict v5 work brief and
      provenance without mutating Project state.
- [x] A new Grok Build retry recovers the fixed request from orientation
      without separately opening request/policy files to discover the question.
- [x] Focused tests, complete regression, documentation links, build/install
      smoke, and version identity pass without regenerating historical evidence.
- [x] README/package/CLI/Harness identity agrees on `0.8.10`.

## Work

- [x] Preserve and independently reproduce the third Grok field-trial need.
- [x] Implement verified fixed-dependency request binding and v5 provenance.
- [x] Extend Markdown fallback, strict schema, CLI/Studio tests, and docs.
- [x] Run a new Grok retry plus focused/full/package verification.
- [x] Resolve the Project need, complete the acceptance audit, and publish the
      next patch release.

## Findings and decisions

- 2026-07-29 — The request file alone is insufficient authority. Core will
  require strict request validation plus an exact `source.requestHash` match
  inside a declared fixed Study dependency.
- 2026-07-29 — Locally constructed template requests are not delegated
  requests. `project-request` keeps provenance truthful instead of overloading
  `delegated-request`.
- 2026-07-29 — Exact `Question` is a natural explicit heading, not arbitrary
  prose inference, so accepting it preserves the flexible-Markdown product
  decision.
- 2026-07-29 — The same generic binding rule is now covered across all three
  locally request-bearing fixed templates: Allocation, Book Risk, and Event
  Study.

## Verification

- Focused version, orientation, Allocation, and CLI suite: 32/32 passed.
- Complete deterministic repository regression: 293/293 passed in 810.455
  seconds.
- Documentation graph: 1,038/1,038 double-links resolved.
- Python compilation, Studio JavaScript syntax, and `git diff --check` passed.
- Fresh Grok Event retry:
  `grok-build-event-request-v5-retry`, pre-inspection orientation 7/7 passed,
  Run `run-20260729T105636893079Z-37f55cae4e05` succeeded, one Run, zero
  Sessions, and no remaining Project Workbench need.
- Fresh Python 3.11 wheel smoke:
  source distribution and wheel built; empty Workspace and fixed Event Project
  created; v5 `project-request` orientation passed; installed Run
  `run-20260729T111506668195Z-c0a6c31e4b8e` succeeded; strict Explorer and
  Studio agreed; Harness recorded version `0.8.10`, commit `unavailable`, and
  `dirty: false`.

## Progress log

- 2026-07-29 — Plan activated from
  `grok-build-allocation-smoke-v089` under clean AutoQuant `0.8.9`.
- 2026-07-29 — A fresh Grok Build coworker created
  `grok-build-event-request-v5-retry` and, before opening any request, policy,
  Study, Judge, or research file, recovered the exact Event Study question
  from `aq orient`: `origin: project-request`, both paths at `request.json`,
  empty editable closure, no trading authority, and the correct fixed baseline
  action. It then produced exactly one successful Run and zero Sessions.
- 2026-07-29 — Independent CLI validation, strict Event Explorer,
  post-Run orientation, and Studio snapshot reproduced the same request,
  Run, four-event primary population, descriptive `observed-advantage`
  conclusion, and no-trading boundary.
- 2026-07-29 — Complete regression, documentation, build, fresh-install, and
  installed-wheel Event Run verification passed; the originating Allocation
  Project need was marked resolved.

## Completion

AutoQuant `0.8.10` surfaces only validated, fixed-dependency-bound local
Project requests as first-class orientation authority, preserves delegated and
flexible-Markdown provenance, and has been independently exercised by a fresh
coding coworker before file inspection.
