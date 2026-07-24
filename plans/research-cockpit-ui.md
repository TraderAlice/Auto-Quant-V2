# Research cockpit UI

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/studio-observation-surface]] and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Make the first AutoQuant Studio viewport operate as a multi-Study research
cockpit: humans and Agents can see the current Factor, Portfolio, and adaptive
policy evidence chain, identify adverse evidence without inventing a browser
verdict, choose one detailed evidence lane, and copy the exact Core-projected
next CLI action.

## Context

The governed research desk already projects professional evidence for all three
lanes, but Studio initially selected one Run and promoted that Run's metrics
into the Project hero. The resulting long page looked like a Factor report with
Portfolio and RL appended below it. It also made a high absolute RL Sharpe easy
to misread even when RL trailed the Judge-selected baseline.

Studio remains a read-only projection. Negative headline relationships may be
marked adverse, but sign alone is not an acceptance gate and JavaScript must
not manufacture KEEP, rejection, or promotion decisions.

## Scope

### In scope

- Put the three-lane research program before report and artifact detail.
- Use comparable lane-specific validation readouts in the Project hero.
- Show one bounded evidence explorer at a time through accessible lane tabs.
- Compact an unbound OpenAlice handoff while preserving the collaboration
  boundary.
- Replace the default Inspector's raw program dump with evidence, scope, and
  next-action context.

### Out of scope

- New Core metrics, Judge thresholds, RunResult fields, or mutation endpoints.
- Authoring or publishing a cross-Study report.
- Executing CLI commands from Studio.
- Changing the Factor, Portfolio, or RL evaluation contracts.

## Acceptance

- [x] The first viewport names all three research lanes and leads with the
  correct relative metric: validation IC, costed validation Sharpe, and RL
  advantage versus the best selected baseline.
- [x] Studio marks negative observations adverse but never interprets a
  positive sign as a Core acceptance decision.
- [x] Factor, Portfolio, and RL evidence can be selected independently while
  the other long explorers remain hidden.
- [x] The Project Inspector exposes the same evidence chain, shared research
  scope, and exact copy-only recommended CLI action.
- [x] Empty handoff state is compact and still explains how an OpenAlice
  request binds to evidence and a return report.
- [x] Static asset, HTTP, browser interaction, responsive, and regression
  checks pass without changing immutable research evidence.

## Work

- [x] Inspect the current Studio projection, program status, explorer
  read-models, and first-viewport layout.
- [x] Implement the Project cockpit, evidence lane selector, compact handoff,
  and evidence-oriented Inspector.
- [x] Update Studio design/operator documentation and deterministic tests.
- [x] Run the bounded verification loop, inspect the rendered browser, and
  audit every acceptance item.

## Findings and decisions

- 2026-07-24 — Absolute RL performance is not the relevant cockpit headline;
  validation advantage versus the fixed selected baseline is.
- 2026-07-24 — Studio may style a negative value as adverse, but only Core and
  its fixed Judge own acceptance. The browser therefore uses descriptive
  relationship labels rather than pass/fail or promotion verdicts.
- 2026-07-24 — Detailed explorers remain complete, but only one is rendered
  into the active accessibility tree at a time to keep the page usable as a
  workbench.

## Verification

- `node --check autoquant/studio_assets/studio.js` — passed.
- `uv run python scripts/check_doc_links.py` — 339 double-links resolved.
- `uv run python -m unittest discover -s tests` — 122 tests passed on the final
  source state in 225.707 seconds.
- Focused Studio and Research Program regression — 8 tests passed in 25.520
  seconds after the final semantics were applied, then again in 24.950 seconds
  after adding single-Study fallback projection.
- `uv build` produced the source archive and wheel; direct wheel inspection
  confirmed the cockpit HTML, comparative RL JavaScript, and evidence-tab CSS.
- Browser smoke against the three-Run Factor Fusion Desk:
  Project cockpit rendered, Factor → Portfolio and Inspector → RL switching
  worked, inactive explorers left the accessibility tree, and browser logs
  were empty.
- Browser device emulation at 640 × 900 activated the narrow-screen rules,
  showed a one-column evidence selector, and proved body and shell
  `scrollWidth === clientWidth` with no horizontal overflow.

## Progress log

- 2026-07-24 — Plan recorded after the first visual prototype exposed the
  difference between a useful cockpit readout and a browser-authored verdict.
- 2026-07-24 — Completed the evidence hierarchy, one-lane workbench,
  collaboration compaction, Inspector coordination surface, package checks,
  responsive QA, and full regression audit.

## Completion

Studio now opens multi-Study Projects as a truthful research cockpit. It leads
with comparable validation relationships, preserves Core/Judge authority,
keeps detailed verified explorers one click away, and exposes the exact
copy-only command for the next governed research action.
