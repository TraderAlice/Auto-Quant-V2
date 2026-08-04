## Context

AutoQuant already has strong research evidence primitives: fixed Studies, versioned Sessions, immutable Experiments and Runs, bounded external Researcher Campaigns, ComputeJob receipts, Reports, Reviews, Dossiers, frozen holdouts, and a versioned Studio snapshot. The connected Next.js Studio projects much of this evidence and now has distinct Factor Research and Strategy Research management surfaces.

The missing product layer is an operable research session. The current UI is organized around modules and read models; it lacks a unified request/receipt boundary, editable definition contracts, Campaign cost/compute authority, a persistent conversation-to-evidence ledger, and direct artifact approval/reproduction.

The visual and interaction source of truth remains the existing Designer Pipeline change:

- Change: `autoquant-replay-research-workbench`
- Console refinement: `agent-research-console.md`
- DESIGN SHA-256: `a16ac2cd0e06fa0e06ecda6f3a368c61ab05bbecca487b209bd44f5d63cdeec2`
- MOTION SHA-256: `3e061d31c8c29b1e09d8e715c2d96ddca4ef741e661bcaea41195ca32e5a38a0`

This OpenSpec change owns implementation requirements and acceptance. It does not fork the visual foundation.

## Goals / Non-Goals

**Goals:**

- Provide one resumable ResearchLedger from data and question through definition, experiment, bounded Campaign, evidence, approval, and reproduction.
- Give the Studio UI and every Agent client one Operator Port with the same authority, request, terminal receipt, and recovery semantics.
- Add editable FactorDefinition and ExperimentDefinition versions without mutating existing Run evidence.
- Extend Campaign authority to candidate, wall-time, compute, and cost budgets with explicit stop conditions and truthful terminal outcomes.
- Keep Factor and Strategy management distinct while preserving navigation and evidence links between them.
- Reuse existing Core loaders, Session/Experiment/Run authority, snapshot projection, Mantine 9.5.1, and lightweight-charts 5.2.0.

**Non-Goals:**

- Replacing Core validation, Judges, selection integrity, holdout authority, or immutable evidence with browser logic.
- Making the embedded chat a privileged executor.
- Adding a second component system, docking framework, financial chart runtime, or animation runtime.
- Requiring private GPU/MOSS providers in the public repository.
- Filling connected Replay gaps with demo evidence.
- Reimplementing Portfolio, supervised-ML, governed-RL, Report, Review, or Dossier evaluation semantics.

## Decisions

### 1. ResearchSession is a ledger projection, not a new evaluator

The session console SHALL assemble references to existing and new Core-owned objects in causal order:

`DataPackage → ResearchQuestion → FactorDefinition/StrategyDefinition → ExperimentDefinition → Campaign/ExperimentRun → EvidenceAssessment → ArtifactApproval → ReproductionReceipt`.

The ledger records stage state, object version, author, timestamp, operation receipt, blockers, and next valid actions. It never calculates a research verdict. Existing Core loaders remain authoritative for evidence integrity.

Alternative rejected: a chat transcript as the session record. Conversation prose is not sufficient authority, cannot guarantee idempotency, and cannot reconstruct exact evidence.

### 2. One Operator Port wraps existing capabilities

Add a Core-owned operator service used by CLI/JSON and the local Studio mutation route. The Next.js route is a same-origin transport adapter, not the authority owner.

The request envelope contains:

- schema version and `requestId`;
- Workspace, Project, session, and actor references;
- research intent;
- exact object/version references;
- requested authority and confirmation reference;
- candidate, time, compute, and cost budget;
- expected prior state for optimistic concurrency.

The terminal receipt contains:

- accepted request hash and idempotency result;
- actual operations and final status;
- created/read artifact and evidence references;
- budget spent;
- warnings, failed gates, and sanitized errors;
- next valid actions and reproduction lineage.

Duplicate `requestId` plus identical request bytes returns the prior receipt. Duplicate identity with different bytes fails closed. Every accepted mutation produces a terminal receipt, including stop, failure, and unavailable outcomes.

Alternative rejected: separate chat, UI, and OpenAlice adapters. Multiple authority paths would drift and would make receipts incomparable.

### 3. Definition plans are mutable only through new versions

FactorDefinition is a program-level research object containing hypothesis, calculation/source identity, parameters, direction/unit, exact data dependencies, availability/PIT semantics, universe/cohort, tests, failure gates, and version lineage.

ExperimentDefinition freezes one executable test plan: definition versions, data snapshot, ResearchSubject, outcome/horizon, benchmark, costs, split/purge, robustness, selection adjustment, holdout policy, executor policy, budget, and stop conditions.

StrategyDefinition remains separate and references exact approved factor versions while owning composition, rules, Portfolio/ML/RL validation, holdout, cost/risk assumptions, and artifact closure.

Saving an approved definition creates a new draft version. ExperimentRuns retain the exact definition and plan version they evaluated. The implementation may place these records inside the existing Project artifact topology, but it must follow the repository's manifest-last, strict-loader, path-confinement, and immutable-publication conventions.

Alternative rejected: editing Study JSON or reassigning historical Runs. That would invalidate existing evidence identity.

### 4. Campaign extends existing Session/Experiment authority

The existing external Researcher driver remains the candidate-edit and evaluation engine. This change adds an approved Campaign charter and product projection rather than replacing it.

The charter freezes:

- question, subject, outcome, horizon, benchmark, data, and holdout policy;
- candidate count/turn ceiling;
- aggregate wall time;
- CPU/GPU resource ceilings;
- monetary/token cost ceiling when measurable;
- fixed stop conditions and permitted candidate-generation families.

Existing `max_turns`, `max_wall_seconds`, per-turn timeout, worktree restoration, immutable Experiment history, and fixed Judge rules remain valid. CPU is the default screening path. GPU/MOSS is selected only when an installed provider declaration and an approved resource/cost envelope exist.

Campaign progress is mutable telemetry and never evidence. Terminal Campaign artifacts are manifest-pinned and preserve completed Experiments even when the Campaign later fails.

Alternative rejected: frontend-only budgets. A visual progress bar without Core enforcement is not an authority boundary.

### 5. Confirmation is semantic and narrow

The Agent may inspect, explain, compare, draft, and execute within an already approved Experiment/Campaign envelope. The Operator Port pauses and requires a semantic confirmation receipt for:

- importing or freezing a new data version;
- saving/finalizing a new definition version;
- changing subject, outcome, horizon, benchmark, costs, holdout, executor scope, or any budget ceiling;
- opening a frozen holdout;
- using a paid/private provider outside a standing approval;
- approving/rejecting an artifact or starting reproduction.

Stop is immediate and does not require confirmation. It preserves completed evidence and publishes a terminal receipt.

### 6. Evidence, approval, and reproduction remain separate states

EvidenceAssessment uses the existing deterministic vocabulary: `supported`, `contradicted`, `inconclusive`, or `invalid-test`. Approval does not change that verdict; it records a human decision over one exact version and evidence closure.

Reproduction always creates a new receipt and compares the reproduced evidence with the approved manifest. Outcomes are exact match, within declared tolerance, drift, unavailable dependency, or failure. Reproduction never overwrites the original artifact or Run.

### 7. Studio uses a ResearchLedger workbench

At 1440 px and above:

- keep the existing 178 px navigation rail;
- use a 340–380 px conversation column;
- keep a flexible central authoring/evidence canvas with 560 px minimum;
- use a 320–380 px review/confirmation inspector;
- add a collapsible research-task tray.

At 1024–1439 px, the inspector becomes a Mantine Drawer. Below 1024 px, the product supports reading evidence, approval history, stop, and reproduction status; complex definition editing and multi-cohort comparison remain desktop-first.

Generic components use installed Mantine primitives through the AutoQuant adapter. New domain components are `ResearchLedger`, `AgentProposal`, `OperationReceiptCard`, `SemanticDiff`, `FactorDefinitionEditor`, `ExperimentDefinitionEditor`, `CampaignBudgetBar`, `CandidateRunTable`, `EvidenceReview`, `ConfirmationInspector`, and `ReproductionReceipt`.

### 8. Connected and demo evidence remain explicit

The console reads existing verified Studio snapshot categories and future Operator receipts. Missing ReplayBundle, market clock, entity mapping, definition, or provider contracts affect only the owning stage/widget. The route and ledger remain visible with a named unavailable state.

Demo evidence remains isolated behind explicit demo entry and is never used to satisfy connected acceptance.

## Risks / Trade-offs

- **Operator Port becomes an overly broad command bus** → Use a closed intent registry, strict schemas, exact object references, path confinement, and Core capability adapters; no arbitrary shell or provider command.
- **New definition objects duplicate Study authority** → Treat definitions as versioned inputs and ExperimentDefinition as the frozen plan; Study/Judge and immutable Run evidence remain the evaluation authority.
- **Campaign budgets drift from existing Researcher limits** → Extend the existing Campaign contract and map legacy turn/wall budgets into the new charter rather than running two schedulers.
- **Conversation becomes the visual center** → Lock the central canvas minimum width and keep receipts/objects addressable independently of chat.
- **Dense UI harms accessibility** → Preserve visual-order tabbing, skip links, focus return, text state, table alternatives, and reduced-motion behavior; never move focus on polling updates.
- **Private GPU/MOSS paths contaminate the public build** → Expose provider-neutral availability and receipts only; keep credentials and invocation packages outside the public repository.
- **Documentation is mistaken for completion** → OpenSpec tasks remain unchecked until executable tests and browser scenarios pass; route compilation and fixture/demo output do not satisfy workflow acceptance.

## Migration Plan

1. Introduce strict Operator request/receipt schemas and a read-only receipt projection over existing Core capabilities.
2. Add the `/research` shell and ResearchLedger using existing snapshot evidence before enabling mutations.
3. Add FactorDefinition and ExperimentDefinition version storage/loaders plus semantic diff and confirmation.
4. Extend existing Campaign authority with compute/cost budgets and product-visible stop reasons.
5. Add evidence review, exact-version approval, and reproduction receipts.
6. Move existing Factor/Strategy/Results/Jobs surfaces into session-aware navigation while preserving their routes and deep links.
7. Add optional GPU/MOSS providers only after public CPU completion and provider-boundary tests pass.

Rollback is additive: disable the new Operator mutation route and `/research` navigation entry while retaining existing connected evidence routes and immutable artifacts. Published receipts and versions are never deleted during rollback.

## Open Questions

- Which existing Project subdirectory is the best durable home for definition versions and Operator receipts while preserving current Project-format conventions? Resolve before implementation and update `docs/PROJECT_FORMAT.md` in the same source change.
- Should the first Operator Port transport be CLI-only plus the local Next.js bridge, or should `aq studio serve` gain a narrowly authenticated mutation endpoint? The first slice SHOULD keep the current same-origin local bridge and Core-owned validation unless a separate security design is approved.
- Which cost unit is authoritative for providers that cannot report currency or token spend? Unknown spend MUST remain unknown and MUST NOT be interpreted as zero.
