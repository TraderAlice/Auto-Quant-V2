## Why

The connected Studio can display real Studies, Runs, Campaign progress, diagnostics, Factor Research, and Strategy Research, but it does not yet provide one operable Agent research session. Conversation, editable definitions, execution, evidence review, approval, and reproduction are fragmented, while the current browser boundary remains mostly read-only.

This change turns the approved Designer Pipeline direction into an executable product contract without replacing existing Core evidence models or adding a privileged chat path.

## What Changes

- Add a session-first ResearchLedger console covering Data → Question → Factor → Experiment → Campaign → Evidence → Approval → Reproduction.
- Add one structured Operator Port used by the embedded Agent, OpenAlice, Hermes, Codex, and the Studio UI, with idempotent requests, bounded authority, confirmation gates, and immutable operation receipts.
- Add versioned editable FactorDefinition and ExperimentDefinition workflows while preserving immutable ExperimentRun evidence and existing Study/Session semantics.
- Extend the existing linear Research Campaign into a product-visible bounded campaign with candidate, time, compute, and cost budgets, explicit stop conditions, truthful negative/inconclusive outcomes, and CPU-first routing.
- Add evidence review, exact-version artifact approval, and independent reproduction with explicit match, drift, unavailable, and failure outcomes.
- Reorganize the Studio entry around research sessions, data, factor assets, strategy assets, evidence, tasks, and audit while preserving existing deep links and connected evidence projections.
- Keep Mantine 9.5.1 as the generic component substrate and `lightweight-charts` 5.2.0 as the sole K-line runtime. No docking system, second UI library, second financial chart runtime, or chat-specific executor is added.

Non-goals:

- Replacing immutable Core evidence, Session/Experiment authority, fixed Judges, or existing provenance checks with browser logic.
- Making demo Replay data appear connected when ReplayBundle, market-clock, or entity mapping contracts are unavailable.
- Requiring GPU/MOSS or a private provider for the public workflow to function.
- Rebuilding the existing Factor, Portfolio, ML, governed-RL, Report, Review, or Dossier evaluators in the frontend.

## Capabilities

### New Capabilities

- `research-session-console`: One resumable ResearchLedger workbench with synchronized conversation, stage canvas, review inspector, task tray, responsive review, keyboard access, and truthful product states.
- `operator-port`: One provider-neutral research request/receipt boundary shared by every Agent client and the Studio UI, including authority, confirmation, idempotency, budget, artifact, evidence, and recovery semantics.
- `versioned-research-definitions`: Editable FactorDefinition and ExperimentDefinition versions with semantic diffs, confirmation, frozen inputs, immutable Run linkage, and separate definition/evidence lifecycles.
- `bounded-research-campaigns`: Autonomous but bounded candidate research with declared candidate/time/compute/cost ceilings, fixed stop conditions, CPU-first screening, optional private executors, and terminal negative/inconclusive states.
- `research-artifact-approval`: Evidence closure, exact-version approval/rejection, immutable factor/strategy research artifacts, and independent reproduction receipts with drift comparison.

### Modified Capabilities

None. This repository has no existing OpenSpec main specs; the change formalizes behavior currently distributed across repository design documents and the upstream Designer Pipeline change.

## Impact

- Core/API: new Operator Port envelope/receipt projection over existing loaders and future versioned definition contracts; extension of Campaign budgets without weakening existing Session, Experiment, Run, Judge, restoration, or manifest authority.
- Studio: new `/research` session surfaces, navigation reorganization, editable research forms, campaign/evidence/approval components, and localized human-language projections.
- Data and evidence: existing DataPackage, ResearchSubject, Study, Run, ReplayBundle, Report, Review, Dossier, and diagnostic identities remain authoritative.
- Providers: CPU remains the public default. GPU/MOSS remain optional provider adapters with explicit availability, resource, cost, and receipt states.
- Dependencies: no new runtime dependency is proposed.
- Upstream design authority: the canonical Designer Pipeline change remains `autoquant-replay-research-workbench`, with DESIGN hash `a16ac2cd0e06fa0e06ecda6f3a368c61ab05bbecca487b209bd44f5d63cdeec2` and MOTION hash `3e061d31c8c29b1e09d8e715c2d96ddca4ef741e661bcaea41195ca32e5a38a0`.
