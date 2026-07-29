# Make terminal research handoffs qualification-aware

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]], and
  [[docs/design/evidence-gated-research-progression]].

## Outcome

A Coding Agent completing one bounded Factor trial can distinguish a local
Session verdict from scientific qualification, immediately see the
post-promotion gate state, and stop cleanly when terminal evidence blocks
downstream research while retaining another Session as an explicit optional
follow-up.

## Context

A fresh external Grok Build coworker used clean AutoQuant `0.8.12` surfaces to
complete a three-lane Factor → Portfolio → governed-RL assignment. Its
relative-volume candidate earned a `KEEP` inside the fixed Session objective,
but strict qualification correctly found complete known-style overlap and no
style-neutral edge, blocked Portfolio admission, and therefore blocked RL.

The scientific result was correct, but the Agent surface exposed three
avoidable frictions:

- the maintained heading `Question (bounded, falsifiable)` was not recognized
  as an explicit research-question section;
- `KEEP` and guarded promotion did not themselves state their narrower
  objective-relative authority strongly enough;
- after terminal blocked evidence, a fresh Factor Session was still presented
  as the primary action, making an already-complete one-shot assignment look
  unfinished.

## Scope

### In scope

- Recognize explicit qualified `Question (...)` research-brief headings
  without accepting arbitrary prose.
- Add non-mutating CLI-envelope authority disclosures to Experiment evaluation
  and return the exact post-promotion Agent Work Brief from promotion.
- Make another Session optional supporting work, rather than primary work,
  after terminal Session evidence and a blocked scientific gate.
- Preserve JSON, human CLI, Studio, and documentation agreement.

### Out of scope

- Changing immutable Experiment, Run, promotion, or scientific-evidence
  schemas.
- Encoding assignment-specific trial budgets in Core.
- Preventing an Agent or human from explicitly starting another Session.
- Removing the Workspace default Project; explicit default selection remains
  intentional, while `aq project list` and explicit Project paths provide
  neutral discovery.

## Acceptance

- [x] `Question (bounded, falsifiable)` is recovered as maintained English
      research authority and remains bounded to that Markdown section.
- [x] Experiment evaluation states that `KEEP` is Session-objective-only and
      grants neither scientific qualification, downstream admission, nor
      trading authority.
- [x] Promotion returns the same post-mutation Work Brief visible from
      subsequent orientation and prints its leading disposition.
- [x] A terminal scientifically blocked lane has no primary action, exposes an
      optional supporting `session.start`, and remains operable when explicitly
      continued; an initial weak baseline still requires its first Session.
- [x] Focused/full regression, docs, build/install smoke, and one fresh
      installed-wheel Grok retry pass.

## Work

- [x] Reproduce and classify the external coworker's reported friction.
- [x] Implement explicit question-heading and qualification-authority
      projections.
- [x] Implement terminal-blocked optional continuation semantics.
- [x] Update tests, public docs, and the worker-needs disposition.
- [x] Complete installed-wheel retry and release audit.

## Findings and decisions

- 2026-07-29 — Session `KEEP` remains valid: it means the candidate improved
  the Session's locked objective. Scientific qualification remains a separate
  verified gate and must be disclosed instead of conflated with that verdict.
- 2026-07-29 — Core will not infer that a delegated assignment allows exactly
  one trial. It can truthfully demote further research to optional after
  terminal blocked evidence without removing the explicit continuation route.
- 2026-07-29 — Workspace-root orientation continues to honor the committed or
  local default Project. This is an intentional reusable-workbench contract,
  not an implicit neutral scope.
- 2026-07-29 — The clean installed-wheel retry found one small continuity
  asymmetry: evaluation disclosed verdict authority but later
  `experiment.show` did not. The same envelope-level authority is now
  projected on both paths without changing immutable Experiment evidence.

## Verification

- Focused question, program-orientation, human CLI, and JSON CLI regression
  passed.
- `uv run python scripts/check_doc_links.py` resolved all 1,052 documentation
  links.
- Source distribution and wheel build passed; a fresh Python 3.11 environment
  installed `auto-quant==0.8.13`.
- Fresh installed-wheel Grok Project
  `grok-build-qualification-handoff-v0813` completed baseline Run
  `run-20260729T125656798915Z-fc7f7c9f6868`, Check
  `check-20260729T125742361195Z-4ec0282e97e9`, KEEP Experiment
  `exp-0001-6764ee589031`, candidate Run
  `run-20260729T125746371213Z-6afe7c0aa2fe`, and guarded promotion
  `promotion-20260729T125800913504Z-db44512b4d52`.
- The coworker recovered its exact question, verified worktree re-entry and
  promotion/orientation parity, reported Session-only verdict authority, and
  stopped at `style-neutral-edge-absent` without Portfolio/RL or a second
  Factor Session.
- A final wheel read the coworker's immutable Experiment with the new
  `verdictAuthority`, validated the Project, and proved orientation/Studio
  Work Brief parity.
- `uv run python -m unittest discover -s tests -v` passed all 301 tests in
  887.073 seconds.

## Progress log

- 2026-07-29 — Activated from the clean `0.8.12` Grok Project
  `grok-build-research-desk-gating-v0812` after its correct negative scientific
  result exposed three reproducible Agent-handoff defects.
- 2026-07-29 — A fresh installed-wheel `0.8.13` Grok coworker completed the
  exact one-Session gating assignment, used every new disclosure correctly,
  stopped before blocked Portfolio/RL work, and reported no blocking open
  needs. Its minor history-inspection asymmetry was added to the final wheel.

## Completion

AutoQuant `0.8.13` makes a bounded research handoff qualification-aware
without changing scientific evidence or removing explicit continuation.
Qualified question headings remain recoverable, Experiment evaluation and
history disclose Session-only verdict authority, promotion returns the exact
subsequent Work Brief, and terminal blocked evidence leaves no false unfinished
primary action. A fresh installed-wheel Grok coworker used these surfaces to
complete one real Factor trial, reject downstream admission, and stop cleanly.
