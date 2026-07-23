# Establish the live research Studio foundation

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/studio-observation-surface]].

## Outcome

Humans can open one lightweight local AutoQuant Studio and understand a
Workspace's Projects, fixed Studies, immutable Runs, active Sessions,
Experiment verdict trajectories, terminal Campaigns, and bounded in-progress
Researcher state without trusting a second evaluator or reading raw
directories.

## Context

Core and the Agent CLI now support the complete manual and externally driven
edit/evaluate loop, but their evidence remains optimized for machine
inspection. The north star also requires a concise human observation surface.

Mujica separates verified Studio snapshots from presentation. INM serves
Workspace/Project snapshots through a local server and makes the browser a
projection of Core. AutoQuant should preserve those boundaries without adding
a large web framework or a remotely hosted service that cannot access
Project-local research evidence.

## Scope

### In scope

- One versioned, serializable Studio snapshot built only through Core loaders.
- Workspace and direct-Project discovery with per-Project diagnostics.
- Read-only summaries for Studies, Runs, Sessions, Experiments, Campaigns, and
  current Researcher progress.
- A lightweight local HTTP server and static responsive browser application.
- `aq studio snapshot` and `aq studio serve`.
- Auto-refresh, Project selection, research pulse, verdict trajectory,
  evidence timeline, and detail inspection.
- Strict local binding defaults, security headers, and no arbitrary file API.
- Fast snapshot, HTTP, CLI, static-asset, syntax, and packaging tests.

### Out of scope

- UI-owned evaluation, editing, Experiment execution, promotion, or command
  execution.
- Remote hosting, authentication, multi-user access, or cloud persistence.
- Streaming subprocess logs or resumable Campaign recovery.
- Full quantitative charting over large artifact datasets.

## Acceptance

- [x] One Workspace page shows every Project and the latest verified research
  state without interpreting unverified evidence as fact.
- [x] Active Researcher work is visible as explicitly mutable progress while
  terminal Campaign evidence remains hash-verified and immutable.
- [x] Direct Project and multi-Project Workspace snapshots share one versioned
  contract used by both CLI and HTTP.
- [x] The first viewport prioritizes research state, leader values, verdict
  movement, and recent evidence rather than generic administration chrome.
- [x] The server binds to loopback by default, exposes only fixed read-only
  routes, and emits defensive browser headers.
- [x] Empty, populated, invalid-evidence, mobile, keyboard, and refresh states
  have deliberate behavior.
- [x] Full bounded tests, documentation links, build/package contents, legacy
  discovery, and local HTTP smoke pass.

## Work

- [x] Audit Mujica and INM Studio ownership, snapshot, and server patterns.
- [x] Define the Studio snapshot and mutable-progress boundary.
- [x] Implement snapshot construction and Campaign progress.
- [x] Implement CLI, local server, and static browser application.
- [x] Add focused and end-to-end tests.
- [x] Update durable design and public documentation.
- [x] Complete acceptance, commit, and publish.

## Findings and decisions

- 2026-07-24 — AutoQuant Studio is local application infrastructure, not a
  hosted marketing site: its authority comes from reading local Project
  evidence through Core, so remote deployment would be misleading.
- 2026-07-24 — Mujica's verified snapshot separation and INM's
  Workspace-aware local server are the relevant sister-project patterns.
- 2026-07-24 — The first Studio is read-only. UI mutations would require
  operation effects, confirmation, progress, and receipts and belong in a
  separate plan.
- 2026-07-24 — No frontend framework is required for the first observation
  surface. Standard-library HTTP plus packaged HTML/CSS/JavaScript keeps the
  Harness installation small and offline-capable.

## Verification

- `git diff --check`
- `uv run python -m compileall -q autoquant tests`
- `node --check autoquant/studio_assets/studio.js`
- `uv run python scripts/check_doc_links.py` — 115 links resolved.
- `uv run python -m unittest discover -s tests -v` — 54 tests passed,
  including real concurrent Researcher progress and a live CLI HTTP process.
- `uv build` — source distribution and wheel built.
- Wheel inspection confirmed `studio.py` and all three packaged browser assets.
- `uv run prepare.py --list-profiles` and
  `uv run run.py --list-profiles` — legacy crypto/equity profiles discovered
  without executing a backtest.

## Progress log

- 2026-07-24 — Plan created after bounded external Campaigns were published in
  commit `d8bf0f7`.
- 2026-07-24 — Implemented the shared snapshot, category diagnostics, mutable
  Campaign progress, CLI/HTTP projections, packaged responsive UI, and local
  server security boundary.
- 2026-07-24 — All acceptance checks passed; the Studio foundation is ready to
  publish.

## Completion

AutoQuant now ships one local research observatory over the same verified Core
state consumed by Agents. It distinguishes live mutable progress from
immutable evidence, remains read-only, and adds no frontend runtime dependency.
Confirmed Studio operations and richer artifact charts remain separate future
work.
