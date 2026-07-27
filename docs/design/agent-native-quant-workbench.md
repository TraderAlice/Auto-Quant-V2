# Agent-native quantitative workbench

Status: active, pre-alpha product model.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/agent-operator-experience]],
[[docs/design/workspace-project-boundaries]],
[[docs/design/quant-research-lifecycle]], and
[[docs/design/documentation-system]].

## Product definition

AutoQuant V2 turns quantitative research into a versioned, testable,
Agent-operable engineering workflow.

It is not merely a backtest library, an autonomous strategy generator, an
OpenAlice backend, or a report converter. It is the complete working
environment in which a coding Agent can receive a quantitative question,
inspect local evidence, modify an authorized research surface, run bounded
experiments, preserve immutable results, resume after interruption, and
deliver a reviewable conclusion.

The workbench is useful in two composition modes:

```text
standalone
human or Agent
→ AutoQuant Workspace
→ Projects, research, evidence, and deliverables

hosted
OpenAlice or another Agent harness
→ materialize the same AutoQuant Workspace
→ assign a coworker and a request
→ Projects, research, evidence, and deliverables
→ return the result through the host's collaboration surface
```

These are not separate editions. The repository, CLI, Project formats,
evaluation semantics, Studio, and evidence remain the same. A host may add
identity, scheduling, communication, credentials, and shared tools around the
Workspace, but AutoQuant Core does not branch on an OpenAlice mode.

## Why AutoQuant and OpenAlice fit without a private integration

OpenAlice is a larger Agent-native Trading Harness. Chat is one Workspace
desk; AutoQuant is another specialized Workspace desk. Both are built around
the same substrate: a persistent directory, Git history, files as context,
native coding-Agent Sessions, explicit tasks, CLI tools, and durable
artifacts.

The desk metaphor maps to the formal model:

| Office concept | AutoQuant/OpenAlice concept | Ownership |
| --- | --- | --- |
| office floor | OpenAlice or another host Harness | discovers desks and coordinates coworkers |
| desk blueprint | Workspace Template | materializes an initial file state |
| desk | AutoQuant Workspace | persistent quantitative workbench and Project discovery |
| coworker at the desk | Agent Session | operates through files and `aq` |
| assignment on the desk | Project | owns one evolving body of research |
| fixed evaluation question | Study | locks candidate and Judge authority |
| bounded line of investigation | Research Session | owns editable worktree and Experiments |
| laboratory measurement | Run | immutable execution under pinned inputs |
| memorandum or case file | Report or Dossier | durable deliverable over verified evidence |

A Chat Agent may ask an AutoQuant coworker to investigate a question. That is
Agent-to-Agent collaboration, not a requirement for Chat to call a private
quant service API. The Quant Agent works inside AutoQuant and can return a
Markdown report, a Dossier, selected artifacts, or an ordinary explanation.
The transport does not define the workbench.

## Workspace lifetime

An AutoQuant Workspace is a long-lived desk, not one disposable request.

- It can contain multiple independent Projects.
- A new request normally creates or continues a Project on an existing desk.
- A new Workspace is appropriate when the operator needs a separate
  environment, ownership boundary, dependency line, or intentionally isolated
  body of work.
- Disposable state belongs below a Project Session, candidate worktree, cache,
  or Run staging directory.
- Copying a Workspace Template creates the initial desk state. It does not make
  the resulting Workspace temporary or subordinate to the template source.

The current one-level Project discovery and self-contained Project rule are
defined in [[docs/design/workspace-project-boundaries]].

## The Agent-operable research loop

The normal loop begins with either a local question or a delegated request:

```text
question or request
→ choose an existing Project or create a Project scaffold
→ write the English Markdown research brief
→ clarify material caller-owned ambiguity
→ inspect verified orientation
→ lock dataset and Study authority
→ establish baseline evidence
→ start bounded Research Session
→ edit only the candidate closure
→ check, evaluate, KEEP/REVERT/CRASH
→ compare and promote or retain baseline
→ publish Report/Dossier when useful
→ continue, hand off, or stop
```

When real research exposes a missing reusable capability, the Quant Agent
records it separately in Project-root `framework-needs.md`. Workbench
development may then reproduce and promote that evidence into a repository
design and plan without turning the investment assignment into a framework
backlog. See [[docs/design/project-derived-workbench-needs]].

The loop does not require a browser or an external orchestrator. `aq` and
Project files are sufficient. Studio observes the same Core state for humans
and Agents; it does not own a parallel lifecycle.

Reports and Dossiers are first-class because research needs durable,
evidence-bound conclusions. They are not mandatory RPC responses. A Project
may remain valuable as an unfinished investigation, a negative result, a
reusable dataset and Judge, or a source of evidence for another Project.

## AI-first product requirements

AutoQuant is designed for a coding Agent as the primary operator and a human
as intent owner, reviewer, and collaborator.

### Clarify before quantifying

`aq project create` gives a new assignment a durable construction site and
returns its Project-root `research.md`. Before data acquisition, candidate
edits, training, or evaluation, the Quant Agent rewrites the assignment there
as a bounded English research brief.

The brief records the decision to support, research question, motivation,
scope, horizon or cadence, known evidence, material constraints, evaluation
meaning, deliverable, assumptions, open questions, and proposed route. This is
guidance for an intelligent operator, not a rigid form. The Agent owns
methodological judgment but may not invent caller-owned intent. Material
ambiguity is returned to the delegating Agent or user as many times as needed
before fixed research authority is created.

English is the internal workbench language so replacement Agents share one
stable working surface. Host or user-facing Agents retain the caller's natural
conversation locale and may translate evidence. A strict request or manifest
is created only after clarification and locks execution semantics; it does not
replace the Markdown narrative.

### Immediate orientation

A newly seated Agent must be able to discover, without reconstructing chat
history:

- which Workspace and Project it is in;
- the research question and current evidence;
- which files are authoritative, editable, generated, or immutable;
- the current blocker or scientific failure layer;
- one safe bounded next action;
- the exact command, working directory, expected effect, and artifact.

`AGENTS.md`, `aq capabilities`, `aq orient`, manifests, and Project-local
plans provide this orientation.

### File-backed authority

Important state must be inspectable in ordinary files with explicit schemas
and content identities. Hidden process memory cannot be the only source of
research truth. Git records meaningful source and documentation changes;
immutable Run/Report manifests record quantitative evidence.

### Bounded feedback

The default loop must offer fast deterministic validation, candidate checks,
small fixtures, and explicit execution budgets. An Agent should not need a
five-year backtest to learn that a column is missing, a path escaped, a factor
looks ahead, or a candidate violated its editable closure.

### Project-derived evolution

The Workbench improves from observed research friction rather than speculative
feature accumulation. Every new Project exposes `framework-needs.md` for
English Agent-maintained evidence about missing expression, evaluation,
inspection, or handoff capabilities. The note is not machine authority;
accepted reusable changes still require repository design, planning, tests,
and release evidence.

### Resumability and handoff

Another Agent must be able to continue from the Workspace files, current
Project state, plans, Git history, and immutable evidence. Native conversation
history is helpful context but not required to reconstruct system truth.

### Clear failure and next action

Errors and read models must distinguish malformed input, unavailable data,
stale evidence, fixed-authority violations, scientific rejection, and
infrastructure failure. A negative experiment is evidence, not a crashed
workbench.

### One Core, multiple projections

Human CLI, JSON CLI, Studio, Reports, and Dossiers project the same verified
Core objects. Presentation code must not invent metrics, selection rules,
portfolio decisions, or filesystem authority.

## Ownership boundaries

### AutoQuant Workbench owns

- quantitative Project and Study structure;
- dataset snapshots and research identities;
- factor, strategy, portfolio, ML, and governed-RL research surfaces;
- bounded evaluation, simulation, comparison, and immutable evidence;
- research-oriented order and protection semantics when needed for valid
  historical experiments;
- Agent orientation, quantitative CLI operations, and Studio observation;
- Reports, Dossiers, and reproducibility artifacts.

### Project owns

- its question, assumptions, universe, data, source, Judges, Sessions, Runs,
  analysis, and deliverables;
- every mutable research choice that must not silently affect another
  Project.

### Optional host Harness owns

- creating or discovering Workspace desks;
- starting and resuming native Agent Sessions;
- cross-Workspace task assignment and communication;
- host-authenticated provenance, scheduling, Inbox, and shared tool injection.

OpenAlice is the first-party example. AutoQuant does not require those services
to operate and does not forge their identity.

### Live trading authority owns

Broker credentials, authenticated accounts, current positions, venue
capabilities, approvals, order submission, and live reconciliation remain
outside AutoQuant. In OpenAlice that authority belongs to UTA.

AutoQuant may research target portfolios, orders, limit/stop behavior, and
TPSL because execution assumptions affect quantitative validity. Such evidence
remains simulation under declared inputs. It never becomes a claim that a live
order was staged, approved, submitted, or filled.

## Template and upgrade boundary

An OpenAlice AutoQuant Template should eventually be a thin materializer of a
pinned AutoQuant release or commit plus host-owned context injection. It should
not maintain a second fork of quantitative code, schemas, prompts, or Project
logic.

The Workspace records the AutoQuant version from which it was created. Later
upgrade design must distinguish:

- workbench-managed assets that may be reconciled deliberately;
- Project-owned research state that must be preserved;
- immutable evidence that remains interpreted under its recorded Harness
  version;
- local Agent or human customization that cannot be overwritten silently.

Copying a newer template over a worked-in desk is not an upgrade strategy.

## Invariants

1. AutoQuant remains fully operable when cloned without OpenAlice.
2. Hosted operation uses the same Core, CLI, schemas, Project model, and
   evidence as standalone operation.
3. A Workspace is persistent and may own multiple Projects.
4. A Project owns its quantitative state; mutable research assets are not
   inherited silently across Projects.
5. A coding Agent can discover one safe next action from files and bounded
   commands.
6. Project truth survives Agent Session interruption or replacement.
7. Reports and Dossiers are durable deliverables, not mandatory integration
   RPCs.
8. Browser presentation and external hosts do not become quantitative
   evaluators.
9. Simulated orders or target weights never grant live-trading authority.
10. OpenAlice-specific provenance and communication remain optional host
    context, not AutoQuant Core identity.

## Non-goals

- Embedding a proprietary model loop or requiring one Agent provider.
- Making every quantitative request create a new Workspace.
- Treating AutoQuant as a Broker adapter or UTA replacement.
- Requiring a structured cross-system response when a human-readable report is
  sufficient.
- Building a generic organization scheduler, chat system, or Inbox inside the
  quantitative Core.
- Allowing standalone and OpenAlice-hosted modes to drift into separate
  products.

## Documentation consequences

- `README.md` owns the concise public promise and first successful workflow.
- `AGENTS.md` routes a coding Agent from product identity to current plans and
  subsystem designs.
- [[docs/ARCHITECTURE]] owns runtime and domain boundaries.
- [[docs/PROJECT_FORMAT]] and [[docs/CLI]] own executable contracts.
- [[docs/design/agent-operator-experience]] owns verified orientation and edit
  authority.
- [[docs/design/quant-research-lifecycle]] owns the detailed research and
  evidence lifecycle.
- Integration-specific documents may explain OpenAlice delivery, but they must
  not redefine AutoQuant as an OpenAlice-only backend.

## Change checklist

- Can the change run identically in standalone and hosted Workspaces?
- Does a new Agent know how to discover and operate it?
- Is durable truth file-backed and attributable?
- Are mutation, immutability, and edit authority explicit?
- Is there a fast bounded failure path before expensive evaluation?
- Can another Agent resume without private chat context?
- Does any host-specific feature remain optional and outside quantitative
  evaluation truth?
- Does simulated decision evidence remain separate from live-trading
  authority?
