# Establish the Agent-native workbench product model

- Status: `completed`
- Updated: `2026-07-27`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/ARCHITECTURE]], [[docs/design/agent-operator-experience]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Give humans and coding Agents one coherent description of AutoQuant V2 as an
independent Agent-native quantitative workbench that can run by itself or
materialize unchanged as an OpenAlice Workspace desk.

## Context

The current implementation already has a long-lived Workspace, multiple
self-contained Projects, bounded Sessions, immutable Runs, a CLI, and Studio.
Its top-level documentation still over-centers the OpenAlice request/Inbox
handoff and can make AutoQuant look like a quantitative backend rather than a
complete desk where a coding Agent performs quantitative work.

OpenAlice and AutoQuant are related by a shared operating model, not a private
service API. OpenAlice may create an AutoQuant Workspace from a template and
send a coworker a request; the same AutoQuant repository must remain complete
and useful when cloned and operated independently.

## Scope

### In scope

- Define the product identity, standalone/OpenAlice parity, desk metaphor, and
  formal Workspace/Project/Study/Session/Run/Report mapping.
- Make Agent operability, filesystem state, Git, bounded commands, evidence,
  and resumability explicit product requirements.
- Reframe reports and Dossiers as durable deliverables rather than the core
  cross-system API.
- Clarify AutoQuant, optional host, Project, Agent, human, and live-trading
  authority boundaries.
- Align the repository entry points and active design documents with this
  model.

### Out of scope

- Implementing OpenAlice Workspace creation or cross-Workspace messaging.
- Changing current schemas, CLI behavior, Studio behavior, or research
  evaluation semantics.
- Implementing the pending Order/TPSL execution kernel.
- Rewriting completed plans, which remain historical execution records.

## Acceptance

- [x] README, package description, contributor routing, and architecture share
  one product definition.
- [x] A new Agent can distinguish the persistent workbench from a Project,
  Study, Session, Run, and deliverable.
- [x] Standalone and OpenAlice-hosted use are described as the same AutoQuant
  artifact and workflow, not separate editions.
- [x] OpenAlice remains an important first-party host without becoming
  AutoQuant's internal lifecycle or mandatory dependency.
- [x] Active lifecycle, Dossier, Studio, and order-native designs use generic
  caller/delivery language and identify OpenAlice as one collaboration path.
- [x] Documentation links and the bounded repository test suite pass.

## Work

- [x] Audit current entry documents and active designs for product-positioning
  conflicts.
- [x] Add the canonical Agent-native workbench product design.
- [x] Align README, AGENTS, architecture, package metadata, and operator docs.
- [x] Reframe active research/delivery/order documents without changing
  executable contracts.
- [x] Run link, terminology, and bounded regression checks.
- [x] Complete, commit, and push the documentation milestone.

## Findings and decisions

- 2026-07-27 — The useful abstraction is a desk, not a backend: OpenAlice is a
  larger Trading Harness, a Workspace Template is the desk blueprint, a
  Workspace is the persistent desk, and an Agent Session is a coworker using
  its files and tools.
- 2026-07-27 — AutoQuant's core value is converting quantitative research into
  a file-backed, versioned, testable workflow that coding Agents can operate.
- 2026-07-27 — Reports are important durable Project artifacts but are not the
  product's defining integration protocol; collaborating Agents can deliver
  and interpret them directly.

## Verification

- `uv run python scripts/check_doc_links.py` — 890 repository double-links
  resolve.
- `uv run python -m unittest tests.test_documentation tests.test_workspace
  tests.test_cli -v` — 21 tests passed in 40.201 seconds.
- `uv run aq capabilities --json` — public discovery envelope emitted.
- `uv build` — source distribution and wheel built successfully.
- `git diff --check` — clean.

## Progress log

- 2026-07-27 — Plan activated; Order/TPSL implementation paused until the
  workbench product model is canonical.
- 2026-07-27 — Added the canonical product model and aligned the public,
  contributor, architecture, lifecycle, Studio, deliverable, and active
  order-native descriptions.

## Completion

Completed on 2026-07-27. AutoQuant now has one documented identity as an
independent Agent-native quantitative workbench that can materialize unchanged
as an OpenAlice Workspace desk. Reports remain durable Project deliverables,
OpenAlice remains an optional first-party host, and historical order/TPSL
research is separated from external live-trading authority. No executable
schema or evaluation behavior changed.
