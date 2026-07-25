# Freeze mechanical decisions into the OpenAlice handoff

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/quant-research-lifecycle]],
  [[docs/design/program-research-dossiers]],
  [[docs/design/portfolio-decision-explorer]], and
  [[docs/design/studio-observation-surface]].

## Outcome

A Portfolio lane Research Report freezes the verified mechanical decision of
its exact leader Run, and a Project Research Dossier carries that same Report
snapshot into the OpenAlice handoff. A later Run, Session change, or Studio
refresh cannot silently replace the decision that the published document
describes.

## Context

The Portfolio diagnostics and Studio now expose a reconciled current mechanical
decision, but immutable Reports freeze only raw Run metrics/artifact identities.
Their Markdown explains mandate, capacity, risk, lifecycle, and parameter
stability without the leader Run's actual per-asset trigger/target/execution
state. OpenAlice therefore receives a rigorous conclusion but not the compact
conditional position evidence visible inside AutoQuant.

## Scope

### In scope

- A small report-level `leaderDecisionSupport` snapshot bound to the exact
  leader Run id and result hash.
- The complete verified Portfolio mechanical decision and explicit `null` for
  non-Portfolio leaders.
- Deterministic Portfolio Report and Dossier Markdown sections with per-asset
  trigger, target, pretrade, executed, and reason evidence.
- Exact reconstruction on load, legacy Report/Dossier compatibility,
  rehashed-tamper rejection, CLI/Studio visibility, and bounded real-project
  verification.

### Out of scope

- Replacing Report analysis, adding live prices, price targets, Broker orders,
  TPSL, account state, or OpenAlice Inbox mutation.
- Recomputing a Dossier from the latest Run instead of its included Reports.
- Freezing the complete Portfolio diagnostics/path or adding forward
  recommendations without Agent-authored evidence references.

## Acceptance

- [x] Every new Report binds decision support to its frozen leader Run id and
      result hash.
- [x] Portfolio Reports contain the exact Core-verified mechanical decision;
      Factor/RL Reports explicitly contain no Portfolio decision.
- [x] Report and Dossier Markdown identify the evidence timestamp, every
      authorized asset's next state conditions, target/pretrade/executed
      weights, execution gate, and `tradingAuthority: none`.
- [x] Existing Reports and Dossiers load without fabricated decision support.
- [x] Fully rehashed decision-support tampering is rejected by reconstruction.
- [x] CLI, Studio, package, and real request-driven publication evidence pass.

## Work

- [x] Audit Report/Dossier evidence composition and immutable leader identity.
- [x] Implement report decision-support derivation and legacy-safe verification.
- [x] Carry the snapshot through Dossier projection and canonical Markdown.
- [x] Expose concise publication state through CLI/Studio summaries.
- [x] Complete controlled publication, tamper, regression, package, and browser
      audits.

## Findings and decisions

- 2026-07-25 — Dossier composition must inherit the Report snapshot; deriving
  from a Dossier-time latest Run would break the existing point-in-time
  evidence hierarchy.
- 2026-07-25 — The full diagnostics object contains path, attribution, and
  parameter surfaces already represented elsewhere. Only the reconciled
  `mechanicalDecision` belongs in this handoff increment.
- 2026-07-25 — “Current” means current at the leader Run's final historical
  decision timestamp, never current market/account state.
- 2026-07-25 — A development-time Session completion was correctly rejected
  after Harness source changed. The published Report remains valid; the
  content lock must not be bypassed to make the mutable Session appear done.

## Verification

- `uv run python -m unittest tests.test_reports tests.test_dossiers
  tests.test_studio tests.test_cli -v`: 31 affected tests exercised Report,
  Dossier, CLI, and Studio; the two newly exposed legacy/tamper failures were
  fixed and rerun successfully.
- `uv run python -m unittest
  tests.test_reports.ResearchHandoffTests.test_legacy_report_without_selection_v2_fields_remains_loadable
  tests.test_dossiers.ProgramResearchDossierTests.test_required_lane_reports_publish_immutable_dossier
  -v`: both focused compatibility and rehashed-tamper tests pass.
- `uv run python scripts/check_doc_links.py`: 557 documentation double-links
  resolve.
- `uv build --out-dir /tmp/autoquant-build-check-20260725`: source and wheel
  packages build successfully.
- Real Yahoo OHLCV request: Session
  `session-20260725T020637294176Z-e4100e98610b` published immutable Report
  `report-20260725T020659012295Z-76d579a94586` over Run
  `run-20260725T020625799701Z-d94f17d5238d`. CLI reload and canonical Markdown
  preserve decision hash `8de6653f28a440f52efde1ac4e56e63dfa224cc05aeca6972f184bce21150d96`,
  timestamp `2026-07-21`, two state changes, 20.672043% proposed turnover,
  the 5% band, and no trading authority.
- Browser audit at `http://127.0.0.1:8784/#yahoo-leadership`: the handoff card
  and Session Inspector show the same frozen timestamp/gate; desktop layout has
  no horizontal overflow and the full Portfolio explorer remains read-only.

## Progress log

- 2026-07-25 — Plan activated after comparing the Portfolio Studio read model
  with Report and Dossier frozen evidence.
- 2026-07-25 — Added the exact leader decision-support snapshot, legacy-safe
  reconstruction, Report/Dossier Markdown, CLI/Studio projections, controlled
  Dossier tamper coverage, and real Yahoo Report publication.

## Completion

Completed with a real request-driven Yahoo Portfolio Report plus the canonical
deterministic multi-lane Dossier fixture preserving the same Report snapshot
through CLI, Markdown, Studio, exact reload, legacy, and tamper checks.
