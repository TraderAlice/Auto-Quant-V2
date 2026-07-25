# Gate downstream research with verified upstream evidence

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/evidence-gated-research-progression]],
  [[docs/design/research-program-orchestration]],
  [[docs/design/factor-qualification-funnel]],
  [[docs/design/portfolio-decision-explorer]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

One multi-Study Project advances because verified scientific evidence supports
the next question, not merely because the previous lane produced a Run or
Report. Weak Factor evidence keeps research in Factor; failed mechanical
monetization keeps it in Portfolio; governed RL becomes optional only after a
reported, qualified factor and a reported positive post-cost mechanical
baseline.

## Scope

### In scope

- Strict reconstruction of current Factor qualification and Portfolio
  viability before program progression.
- Report-bound Factor→Portfolio and Portfolio→RL admission states.
- One Core-owned progression diagnosis and recommended lane/action.
- Repeat Session entry after a prior terminal Session.
- CLI, Studio, schema, canonical documentation, and deterministic tests.
- Legacy evidence fails closed without becoming invalid or fabricated.

### Out of scope

- Changing Factor or Portfolio Judge metrics, KEEP/REVERT, promotion, or
  selection-adjustment rules.
- Automatically executing a Run, starting a Session, or requiring optional RL.
- Dossier authorship, Broker/UTA/account state, orders, or trading.

## Acceptance

- [x] A current Factor Run must have reconstructable positive qualification
      and a current frozen Report before Portfolio is admitted.
- [x] A current Portfolio Run must have positive post-cost viability and a
      current frozen Report before optional RL is admitted.
- [x] Failed or legacy upstream evidence routes research back to the first
      unsupported lane with a precise evidence stage and focus.
- [x] Terminal lane history exposes a fresh governed Session command instead
      of trapping the Project behind its latest completed Session.
- [x] CLI and Studio render the exact Core progression and distinguish blocked,
      active, admitted, and optional lanes without browser-derived inference.
- [x] Deterministic tests, bounded real evidence, browser QA, documentation,
      package checks, full regression, commit, and push pass.

## Work

- [x] Audit current scientific evidence and phase-only lane routing.
- [x] Specify evidence/report gates and authority boundaries.
- [x] Implement Core progression and repeat-Session command generation.
- [x] Integrate CLI/schema and Studio cockpit presentation.
- [x] Verify weak-factor, failed-portfolio, positive synthetic, legacy, and
      terminal-Session paths.
- [x] Complete real-data/browser QA, full regression, docs, commit, and push.

## Findings and decisions

- 2026-07-25 — `reported` is a coordination phase, not scientific readiness.
  Existing orchestration can recommend a downstream lane after any upstream
  Report even when the frozen diagnosis explicitly says not to add complexity.
- 2026-07-25 — A reported weak result is still useful OpenAlice evidence. The
  gate routes the next research question; it never invalidates or hides the
  Report.
- 2026-07-25 — Optional RL should be admitted by positive simple evidence but
  not automatically recommended merely because its Study exists.
- 2026-07-25 — A failed upstream gate is a publishable answer. Dossier
  requirements are therefore derived from frozen upstream Report evidence:
  Factor is always required, Portfolio is required only after positive Factor
  qualification, and governed RL remains optional.
- 2026-07-25 — Existing downstream Reports remain eligible as optional context
  so historical snapshots stay usable, but they cannot override a failed gate
  or force new downstream execution.
- 2026-07-25 — The deterministic candidate `relative_volume_20 + intraday`
  produced positive Factor qualification and validation post-cost Portfolio
  Sharpe `11.3951`, proving the progression can admit both gates as well as
  reject weak evidence.

## Verification

- `node --check autoquant/studio_assets/studio.js`
- `uv run python -m compileall -q autoquant tests`
- Focused research-program, Dossier, CLI, and Studio tests: passed.
- `uv run python scripts/check_doc_links.py`: 609 links resolved.
- `uv build`: source distribution and wheel built successfully.
- `uv run python -m unittest discover -s tests`: 171 tests passed in
  1127.799 seconds.
- Real provider-adjusted Yahoo evidence: AAPL, MSFT, NVDA, QQQ, and SPY;
  1,254 sessions from 2021-07-23 through 2026-07-22.
- Real weak-Factor Run:
  `run-20260725T062643410335Z-489a9c80da49`; validation rank IC `+0.0028`,
  HAC t `+0.0782`, diagnosis `raw-statistical-evidence-weak`.
- Real immutable early-stop chain:
  Session `session-20260725T062654925538Z-dae6060e594c`,
  Report `report-20260725T062654977421Z-3759e6e80a7f`, and
  Factor-only Dossier `dossier-20260725T062655695713Z-a72bb8f83827`.
- Browser QA at 1280×720 verified Factor focus, Portfolio/RL locks, published
  one-lane Dossier, `1/1 required ready · 1 included`, and no horizontal
  overflow.

## Progress log

- 2026-07-25 — Plan activated after browser and Core audit of the current
  Factor, Portfolio, RL, and OpenAlice handoff surfaces.
- 2026-07-25 — Added Core-owned report-bound scientific progression, terminal
  Session restart commands, dynamic Dossier requirements, CLI/schema
  projection, and Studio admission states.
- 2026-07-25 — Verified deterministic positive and negative paths, materialized
  a real Yahoo early-stop handoff, completed browser QA, documentation,
  packaging, and full regression.

## Completion

Completed 2026-07-25. Downstream research is now admitted by verified
scientific evidence rather than coordination phase, and negative upstream
results can return as immutable OpenAlice-ready early-stop Dossiers.
