# Evidence-driven research agenda

- Status: `completed`
- Updated: `2026-07-26`
- Related design: [[docs/design/evidence-driven-research-agenda]],
  [[docs/design/agent-operator-experience]],
  [[docs/design/factor-component-attribution]],
  [[docs/design/portfolio-construction-lab]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Give an AI researcher up to three bounded experiment briefs derived from the
current verified Factor, Portfolio, or governed-RL evidence, so the Agent knows
which falsifiable change to try, why it is prioritized, what editable surface
it may touch, which validation checks decide it, and when to stop without
using visible test evidence as a selection input.

## Context

AutoQuant already verifies deep professional evidence and reduces it to a
scientific failure stage such as style-neutral edge absent, cost fragility, or
seed/fold instability. The AI-first `AgentWorkBrief` still turns that evidence
into only a generic instruction to edit one candidate hypothesis. An incoming
Agent must rediscover how the diagnosis maps to the actual editable factor or
state-encoder closure, which is avoidable work and invites inconsistent
research choices.

The previous component-evidence milestone now supplies explicit multi-interval
component hypotheses, validation raw/residual evidence, fixed-blend removal
diagnostics, and target-free redundancy. Those facts can safely prioritize a
next Factor experiment when their authority and limitations stay explicit.
Portfolio and RL already expose equivalent fixed diagnosis stages that can
produce bounded mechanical-signal and state-representation experiments.

## Scope

### In scope

- Define one strict, bounded research-agenda read model over a verified
  immutable Run.
- Produce deterministic Factor experiment briefs from qualification and
  optional declared-component evidence.
- Produce deterministic Portfolio experiment briefs that change only the
  editable factor, never fixed sizing, Mandate, risk, execution, or cost rules.
- Produce deterministic RL experiment briefs that change only the causal
  state encoder, never fixed actions, rewards, portfolio mechanics, or learning
  rules.
- Add the agenda to the hashed `AgentWorkBrief`, concise `aq orient` output,
  and a matching first-class Studio panel.
- Keep no-evidence, legacy, unsupported, and completed/external-holdout states
  explicit instead of inventing an experiment.

### Out of scope

- Automatically editing candidate code, running an experiment, choosing a
  winner, promoting a leader, or creating a live order.
- Generating unconstrained market stories or inferring undeclared component
  semantics from Python source.
- Using test-audit values, ex-post RL oracle actions, or Dossier prose to rank
  candidate experiments.
- Opening fixed Judge parameters, Portfolio mechanics, RL action sleeves,
  learning hyperparameters, request authority, or trading access to the Agent.
- A general LLM planner or unbounded hyperparameter search.

## Acceptance

- [x] Every `AgentWorkBrief` includes one schema-valid agenda with explicit
  status, verified Run identity when available, diagnosis, authority, and zero
  to three ordered experiment briefs.
- [x] Factor agendas use validation-only qualification/component facts and
  preserve the distinction between fixed diagnostic-blend removal and an
  arbitrary final-factor ablation.
- [x] Portfolio agendas translate the first failed mechanical layer into a
  factor-representation hypothesis without advertising fixed sizing, risk,
  execution, cost, or Mandate edits.
- [x] RL agendas translate factor-capture, switching-cost, active-risk, or
  seed/fold evidence into state-encoder hypotheses without changing fixed
  actions, rewards, learning rules, or portfolio mechanics.
- [x] Each experiment brief identifies editable paths, optional component
  targets, auditable evidence references, validation success checks, and stop
  conditions; test remains visible audit only.
- [x] `aq orient --json`, concise human output, and Studio render the same Core
  agenda covered by the existing work-brief hash.
- [x] Deterministic unit, legacy/waiting, schema, CLI, Studio, and end-to-end
  tests pass without a long backtest.

## Work

- [x] Audit verified diagnostics and current AI orientation across Factor,
  Portfolio, RL, and OpenAlice handoff.
- [x] Define the bounded agenda authority, schema, and lane-specific research
  recipes.
- [x] Implement the pure agenda builder and verified Run dispatch.
- [x] Bind the agenda into `AgentWorkBrief`, CLI, Studio, schemas, and docs.
- [x] Exercise all lane recipes and negative/compatibility states.
- [x] Run browser acceptance, complete regression, documentation links, and
  package builds.
- [x] Audit acceptance, complete the plan, commit, and push.

## Findings and decisions

- 2026-07-26 — Existing diagnostics already own the scientific stage; the
  agenda must consume those verified read models rather than create a second
  browser- or prompt-side diagnosis.
- 2026-07-26 — An experiment brief is a research-priority suggestion, not an
  execution command. The existing `primaryAction` remains the sole lifecycle
  operation advertised by `AgentWorkBrief`.
- 2026-07-26 — Portfolio Agents edit only the factor surface. Mechanical
  sizing, signal state, risk, execution, and costs remain fixed evaluation
  pressure, so Portfolio agendas must propose signals that survive them rather
  than suggest changing them.
- 2026-07-26 — RL Agents edit only the causal encoder. Action sleeves,
  learning configuration, rewards, and portfolio mechanics remain fixed.
- 2026-07-26 — Positive validation evidence should sometimes produce a
  freeze-and-external-holdout brief instead of inviting more in-sample tuning.
- 2026-07-26 — Session candidate source lives in its disposable worktree, but
  every formal candidate Run is published under the owning Project. Agenda
  evidence therefore resolves the immutable leader from the canonical Project
  while retaining the worktree as the separate edit target.

## Verification

- `uv run python -m unittest discover -s tests -v` — 199 tests passed in
  1210.995 seconds, including real bounded Factor, Portfolio, and governed-RL
  research flows.
- `uv run python -m unittest tests.test_research_agenda
  tests.test_orientation tests.test_studio -v` — 16 focused contract and
  presentation tests passed after the final Run-ownership correction.
- `uv run python scripts/check_doc_links.py` — all 702 documentation
  double-links resolve.
- `uv build --out-dir /tmp/autoquant-agenda-build.zMIBii` — source and wheel
  packages built successfully.
- `node --check autoquant/studio_assets/studio.js`,
  `python -m py_compile`, and `git diff --check` passed.
- Browser acceptance exercised the exact Core agenda at 1280 px and 390 px:
  the desktop three-card and mobile single-column layouts had no horizontal
  overflow, console errors, or page errors.

## Progress log

- 2026-07-26 — Plan created from the post-component-evidence AI workflow audit.
- 2026-07-26 — Added the strict research-agenda schema, deterministic
  lane-specific recipes, work-brief/CLI/Studio integration, and bounded tests.
- 2026-07-26 — Corrected Session leader evidence resolution to the canonical
  Project Run store, completed full regression and browser acceptance, and
  closed the plan.

## Completion

Completed on 2026-07-26. AutoQuant now converts verified lane diagnosis into
zero to three bounded, auditable experiment briefs while leaving execution,
selection, promotion, and trading authority unchanged.
