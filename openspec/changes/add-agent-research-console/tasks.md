## 1. Contract and documentation foundation

- [x] 1.1 Resolve and document the Project-format locations, schemas, manifest rules, and loaders for FactorDefinition, ExperimentDefinition, Operator receipts, artifact approvals, and reproduction receipts in `docs/PROJECT_FORMAT.md` and the relevant `docs/design/` contracts.
- [x] 1.2 Add strict schema fixtures for the new objects, including valid, unknown-field, stale-version, path-escape, tampered, and unsupported-version cases.
- [x] 1.3 Extend `autoquant/capabilities.py` and CLI documentation with closed Operator intents and machine-readable request/receipt schemas; do not expose arbitrary commands.
- [x] 1.4 Add compatibility rules that project existing Study/Session/Experiment/Run/Campaign evidence without rewriting or migrating immutable artifacts.

## 2. Unified Operator Port

- [x] 2.1 Implement the Core-owned Operator request validator, closed capability registry, expected-state checks, and idempotency store over existing Core operations.
- [x] 2.2 Implement immutable terminal AgentOperationReceipt publication for completed, stopped, failed, unavailable, stale, and confirmation-required outcomes.
- [x] 2.3 Route an initial read-only set of inspect, explain, compare, and reproduce-readiness operations through the Operator Port and prove CLI/JSON parity.
- [x] 2.4 Add same-origin Next.js transport through one `/api/studio/operator` adapter that delegates validation and mutation authority to Core.
- [x] 2.5 Add regression tests proving identical retries do not repeat work, conflicting retries fail closed, stale state cannot mutate, and every accepted failure receives a receipt.
- [x] 2.6 Add boundary tests proving the port rejects shell commands, raw provider invocations, credential payloads, unknown intents, unconstrained paths, and chat-specific authority.

## 3. Versioned research definitions

- [x] 3.1 Implement strict FactorDefinition version creation/loading with hypothesis, calculation/source identity, parameters, direction/unit, exact data/PIT dependencies, cohort, tests, failure gates, lifecycle, and lineage.
- [x] 3.2 Implement strict ExperimentDefinition draft, confirmation, and freeze flow over exact definition versions, data/subject, outcome/horizon, benchmark, costs, split/purge, robustness, holdout, executor, budgets, and stop conditions.
- [x] 3.3 Preserve StrategyDefinition as a separate object that references exact factor versions and owns composition, Portfolio/ML/RL validation, costs, risk, holdout, and artifact closure.
- [x] 3.4 Implement Core semantic diffs for changed definition fields, affected evidence, invalidated assumptions, and new version identity.
- [x] 3.5 Bind every new ExperimentRun and Operator receipt to the exact FactorDefinition/StrategyDefinition and ExperimentDefinition versions used.
- [x] 3.6 Add tests proving approved versions are immutable, edits fork drafts, historical Runs do not move, tampering fails closed, and unresolved PIT/clock/cost/stop fields block execution readiness.

## 4. Bounded ResearchCampaign

- [x] 4.1 Extend the existing Researcher Campaign charter with approved candidate, wall-time, CPU, GPU, and cost ceilings plus fixed stop conditions while preserving legacy turn/wall compatibility.
- [x] 4.2 Enforce all budgets in Core, preserve unknown provider spend as unknown, and publish used/remaining budget in progress and terminal receipts.
- [x] 4.3 Add CPU-first screening and fixed-gate rejection before optional GPU/MOSS dispatch; require provider availability and an approved resource/cost envelope for private executors.
- [ ] 4.4 Add evidence-ready, budget-exhausted, failed-gate, blocked, stopped-by-user, inconclusive, and failed terminal projections without weakening existing immutable Campaign statuses.
- [ ] 4.5 Enforce frozen holdout isolation during candidate generation and selection and require a separate audited confirmation before opening it.
- [ ] 4.6 Add tests for every budget dimension, immediate stop, malformed Researcher response after valid Experiments, worktree restoration, private-provider absence, negative/inconclusive campaigns, and holdout-access rejection.

## 5. Read-only ResearchLedger shell

- [x] 5.1 Add `/research` and `/research/[sessionId]` routes that assemble existing verified snapshot evidence into Data → Question → Factor → Experiment → Campaign → Evidence → Approval → Reproduction without browser-side verdicts.
- [x] 5.2 Build `ResearchLedger`, structured conversation entries, `OperationReceiptCard`, dominant stage canvas, review inspector, and collapsible task tray using the existing AutoQuant/Mantine adapter.
- [x] 5.3 Reorganize primary navigation into Work, Assets, Evidence, and Operations while preserving all existing route URLs and deep links.
- [x] 5.4 Implement truthful loading, empty, partial, unavailable, invalid, stale, error, and demo-isolated states for each ledger stage.
- [x] 5.5 Add frontend projection tests proving missing ReplayBundle, market clock, definition, approval, or provider evidence affects only its owning widget and never fabricates connected completion.

## 6. Editable console and confirmation flow

- [x] 6.1 Build `FactorDefinitionEditor` and `ExperimentDefinitionEditor` from installed Mantine form primitives with Core validation, draft/version identity, and Technical Details disclosure.
- [x] 6.2 Build `SemanticDiff` and `ConfirmationInspector` with exactly one primary confirmation action plus save-draft, return-for-revision, and stop actions where valid.
- [ ] 6.3 Connect data freeze, new definition version, changed boundary, budget expansion, private provider, holdout opening, artifact decision, and reproduction start to Operator confirmation receipts.
- [ ] 6.4 Prove inspect, explain, compare, draft, and approved-envelope execution do not generate redundant confirmation prompts.
- [ ] 6.5 Add frontend and Core integration tests for stale confirmation, version races, retry idempotency, validation errors, and successful new-version creation.

## 7. Campaign and evidence workspaces

- [x] 7.1 Build `CampaignBudgetBar` for candidate/time/compute/cost usage and `CandidateRunTable` for candidate version, stage, executor, spend, failed gate, best evidence, stop reason, and next valid action.
- [ ] 7.2 Connect bounded start, pause, resume, and immediate stop through the Operator Port while preserving mutable-progress versus terminal-evidence labeling.
- [x] 7.3 Build `EvidenceReview` with Outcome, Replay, Cohorts, Robustness, Costs, and Provenance views over verified Core projections only.
- [ ] 7.4 Keep `lightweight-charts` as the sole K-line runtime and add synchronized semantic tables/inspectors for every meaningful chart mark.
- [ ] 7.5 Add tests proving budget exhaustion does not auto-expand, table focus survives polling, negative/invalid candidates remain visible, and connected evidence never falls through to demo data.

## 8. Artifact approval and reproduction

- [x] 8.1 Implement exact-version artifact review over definition, data, Experiment, Run, assessment, cost, holdout, limitation, and diagnostic closure.
- [x] 8.2 Implement approve, reject/return, and retain-as-draft receipts without changing definition verdicts or deleting reviewed evidence.
- [ ] 8.3 Implement reproduction from an approved manifest with separate exact-match, within-tolerance, drift, unavailable, and failed receipts.
- [ ] 8.4 Project approval and every reproduction attempt into the ResearchLedger, Studio snapshot, Audit, CLI/JSON, and stable deep links.
- [ ] 8.5 Add tests for stale review, incomplete closure, negative evidence retention, private executor absence, CPU equivalence policy, metric/hash drift, and immutable original artifacts.

## 9. Responsive, accessibility, and motion verification

- [x] 9.1 Implement the 1440 px three-region layout and 1024–1439 px Drawer behavior with the central canvas minimum width defined by the Designer Pipeline specification.
- [x] 9.2 Implement review-only behavior below 1024 px without hiding evidence, decisions, stop status, or reproduction receipts.
- [ ] 9.3 Add skip-link, visual-order tabbing, visible focus, focus return, polite live regions, keyboard shortcuts, table alternatives, and no-focus-steal polling behavior.
- [x] 9.4 Apply only CSS focus/press feedback and bounded Drawer/Modal transitions; suppress nonessential motion under `prefers-reduced-motion`.
- [x] 9.5 Run manual browser acceptance at 375×812, 768×1024, 1024×768, 1440×900, and 1920×1080 with zero horizontal overflow at supported layouts.

## 10. Completion evidence

- [x] 10.1 Run `openspec validate add-agent-research-console --strict --json` and resolve every issue before implementation approval and again before archive.
- [x] 10.2 Run targeted Core suites for Operator Port, definitions, Campaigns, approvals, reproduction, Studio snapshot, and CLI capabilities.
- [ ] 10.3 Run `uv run python scripts/check_doc_links.py` and `uv run python -m unittest discover -s tests -v`.
- [x] 10.4 Run frontend tests, ESLint, `npm run check:boundary`, and the Next.js production build.
- [ ] 10.5 Execute browser scenarios for factor discovery, strategy verification, immediate stop, budget exhaustion, missing ReplayBundle, stale confirmation, exact reproduction, and reproduction drift with clean console logs.
- [ ] 10.6 Verify that OpenAlice, Hermes, Codex, the embedded Agent, and Studio projections use the same Operator schema and receipt fixtures.
- [x] 10.7 Record actual verification evidence in this checklist and repository status/design documents; do not mark the OpenSpec change complete from routes, documentation, fixtures, or available Core inventory alone.

## Verification evidence (2026-08-04)

- Core targeted suites: `uv run python -m unittest tests.test_operator_port tests.test_research_definitions tests.test_research_artifacts tests.test_research tests.test_runs tests.test_run_binding_preflight tests.test_run_binding_persistence tests.test_run_binding_drift tests.test_studio tests.test_cli -v` — 157 tests passed. A preceding system-Python invocation was rejected at import time because it lacked the repository dependency `exchange_calendars`; no test body ran in that invocation.
- Frontend: `npm test` — 86 tests passed; `npm run lint`, `npm run check:boundary`, and `npm run build` passed. The production build generated `/research` and `/research/[sessionId]` successfully.
- OpenSpec: `openspec validate add-agent-research-console --strict --json` passed before this checklist update; the final strict validation is rerun after every checklist edit.
- Documentation links: `python scripts/check_doc_links.py` — 1,570 links resolved.
- Browser: verified responsive/review-only behavior and no horizontal overflow at 375×812, 768×1024, the 1024 breakpoint from both adjacent device-pixel sizes, 1440×900, and 1920×1080; Drawer focus return, skip-link focus, polite live region, receipt visibility, and a clean error console were also checked. A real `campaign.stop` request disabled both Stop entries in flight; after Core returned a terminal `stopped` receipt with matching `autoquant-campaign-stop-request` evidence, the Inspector action disappeared, the tray action stayed disabled, and a second DOM click did not issue another request. When the external researcher outlived Core's wait window, Core returned `unavailable` with terminal publication pending; this remains a 7.2 blocker and is not treated as stopped by the frontend.
- Independent review status: **REQUEST CHANGES** overall; 6.2 is accepted. Tasks 4.4–4.6, 6.3–6.5, 7.2, 7.4–7.5, 8.3–8.5, 9.3, and the remaining completion scenarios stay unchecked until their implementation and evidence exist. Structured definition, artifact-review, and reproduction-request editors now exist, but exact reproduction outcomes still require a Core-controlled executor and Campaign/accessibility acceptance remains incomplete.
- No commit, push, PR, CI, deployment, OpenSpec archive, or external account/provider mutation was performed.
