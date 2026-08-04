# Agent Research Console

- Status: `active`
- Updated: `2026-08-03`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/agent-operator-experience]],
  [[docs/design/external-researcher-driver]],
  [[docs/design/research-session-loop]],
  [[docs/design/studio-observation-surface]], and
  [[docs/design/quant-research-lifecycle]].
- OpenSpec change: `add-agent-research-console`.

## Outcome

The approved Agent Research Console is executable through one Core-owned,
closed Operator Port from exact research inputs through bounded Campaign
evidence, exact-version artifact decisions, and independent reproduction, with
the Studio projecting the same receipts in a truthful eight-stage
ResearchLedger.

## Context

Core already owns strict Studies, Sessions, Experiments, immutable Runs,
Campaign history, Reports, Reviews, Dossiers, ComputeJobs, and the versioned
Studio snapshot. The approved OpenSpec change adds the missing shared operator
boundary, versioned FactorDefinition and ExperimentDefinition inputs, enforced
multi-dimensional Campaign budgets, artifact decisions, reproduction receipts,
and the session-first Studio projection. Designer Pipeline change
`autoquant-replay-research-workbench` remains the visual and interaction fact
source; this plan is only the repository execution record.

## Scope

### In scope

- Implement `openspec/changes/add-agent-research-console` in its declared order.
- Keep FactorDefinition, Factor Passport, ExperimentDefinition, and
  StrategyDefinition/Portfolio/ML/RL as separate version-linked objects.
- Add one structured request/receipt path with idempotency, confirmation,
  optimistic state checks, path confinement, budget enforcement, and audit.
- Add `/research` and `/research/[sessionId]` over verified Core projections,
  including truthful partial/unavailable/invalid/demo-isolated states.
- Preserve CPU-first public execution and provider-neutral unavailable receipts
  for optional private GPU/MOSS executors.

### Out of scope

- Live accounts, Orders, broker/exchange credentials, or trading execution.
- Private GPU/MOSS implementations, credentials, or vendor-specific code.
- Arbitrary shell, chat-specific authority, browser-side verdicts, or fake
  ReplayBundle/market-clock/entity evidence.
- New UI, docking, chart, animation, or runtime dependencies.
- Commit, push, PR, CI, deployment, archive, or provider-account mutation.

## Acceptance

- [ ] Core and Studio consume one closed Operator request/receipt schema, with
  CLI/JSON and same-origin transport parity.
- [ ] Versioned FactorDefinition and ExperimentDefinition retain immutable
  approved history and bind every new Run/receipt to exact versions.
- [ ] Campaign candidate/time/CPU/GPU/cost ceilings and fixed stop conditions
  are Core-enforced, including unknown-spend, stop, negative, inconclusive,
  provider-unavailable, and holdout-isolation paths.
- [ ] `/research` and `/research/[sessionId]` render the eight-stage ledger and
  editable/approval/reproduction surfaces without inventing connected evidence.
- [ ] Targeted Core/frontend suites, full repository checks, strict OpenSpec
  validation, production build, browser scenarios, and accessibility checks
  provide fresh evidence.

## Work

- [ ] Freeze repository locations, schemas, loaders, capabilities, and
  compatibility projection.
- [ ] Implement and verify the Core Operator Port plus read-only receipt/ledger
  projection.
- [ ] Implement and verify versioned definitions and bounded Campaign authority.
- [ ] Implement and verify the read-only ResearchLedger Studio shell.
- [ ] Enable structured mutations, evidence review, artifact decisions, and
  reproduction only after the Core projection is approved.
- [ ] Complete responsive/accessibility/browser verification and record exact
  evidence in the OpenSpec checklist without archiving the change.

## Findings and decisions

- 2026-08-03 — DESIGN SHA-256 remains
  `a16ac2cd0e06fa0e06ecda6f3a368c61ab05bbecca487b209bd44f5d63cdeec2`;
  MOTION SHA-256 remains
  `3e061d31c8c29b1e09d8e715c2d96ddca4ef741e661bcaea41195ca32e5a38a0`.
- 2026-08-03 — CC Switch real route probes passed for MiniMax
  (`MiniMax-M2.7-highspeed`, HTTP 200) and DeepSeek (`deepseek-v4-pro`, HTTP
  200). MiniMax owns Core-only files; DeepSeek owns `studio-web` only.
- 2026-08-03 — Existing dirty worktree changes are preserved as user-owned
  context. The two provider routes run sequentially and may not edit the same
  file.

## Verification

- Pending implementation evidence.

## Progress log

- 2026-08-03 — Plan created and registered after the approved OpenSpec and
  Designer Pipeline facts were read and foundation hashes were reverified.

## Completion

Complete only after the OpenSpec completion evidence is fresh. Do not archive
the change in this task.
