# AutoQuant V2 work plans

This file is the repository-level index of planned and completed engineering
work. Detailed plans live in `plans/`; long-lived system intent and current
invariants live in `docs/design/`.

## Status model

- `proposed`: the outcome is understood, but work has not started.
- `active`: implementation is in progress and this plan is the current
  coordination record.
- `paused`: work is intentionally stopped and the reason is recorded in the
  plan.
- `completed`: every acceptance item is satisfied and verification evidence is
  recorded.
- `superseded`: the plan will not be completed because another linked plan
  replaced it.

## Active plans

There are no active plans.

## Proposed plans

| Plan | Outcome | Updated |
| --- | --- | --- |
| [[plans/rl-factor-policy-lab]] | Add a bounded RL factor-allocation lane with fixed rewards, walk-forward evidence, multiple seeds, and simple baselines. | 2026-07-24 |

## Paused plans

There are no paused plans.

## Completed plans

| Plan | Outcome | Updated |
| --- | --- | --- |
| [[plans/portfolio-construction-lab]] | Added a fixed causal factor-to-target-weight Judge with drift, costs, professional evidence layers, stresses, artifacts, and a complete reference Project. | 2026-07-24 |
| [[plans/openalice-research-handoff]] | Turned an external research request into one Study-bound Session brief and a verified decision-support report that OpenAlice can publish. | 2026-07-24 |
| [[plans/content-locked-ohlcv-factor-lab]] | Gave Agents a self-contained, content-locked OHLCV reference Project for bounded factor research through the complete V2 evidence loop. | 2026-07-24 |
| [[plans/live-research-studio-foundation]] | Give humans one local read-only Workspace observatory for verified research evidence and explicitly mutable in-progress Campaign state. | 2026-07-24 |
| [[plans/bounded-external-researcher-driver]] | Let a replaceable external coding Agent autonomously drive a bounded Session while preserving strict proposal, evidence, verdict, and stopping authority. | 2026-07-24 |
| [[plans/governed-research-session-loop]] | Gave Agents a resumable edit/evaluate loop with locked Study authority, immutable KEEP/REVERT/CRASH evidence, and guarded promotion. | 2026-07-24 |
| [[plans/study-run-evidence-foundation]] | Made one locked quantitative Study executable through a bounded Python Judge that publishes complete immutable RunResult evidence for later Agent experiments and Studio inspection. | 2026-07-24 |
| [[plans/workspace-project-cli-foundation]] | Gave humans and Agents one strict multi-project Workspace boundary and a versioned machine-discoverable CLI before research execution moves into Projects. | 2026-07-24 |
| [[plans/planning-and-documentation-foundation]] | Established the live planning, durable design-documentation, and executable link-validation rules needed for long-running Agent development. | 2026-07-24 |

## Superseded plans

There are no superseded plans.

## Working rules

1. Create a plan for work that crosses packages or public surfaces, changes a
   domain model, contains meaningful unknowns, or needs more than one
   implementation step. Small, local fixes do not need ceremonial plans.
2. Copy [[plans/_template]], give the file a stable kebab-case name, and add it
   to the matching status section here before implementation begins.
3. Keep the plan current while working. Record newly discovered constraints and
   decisions when they affect the route, and update checkboxes as evidence is
   produced rather than reconstructing progress at the end.
4. A plan coordinates a change; it does not own lasting system truth. When work
   changes an invariant or public contract, update the relevant `docs/design/`
   document in the same change.
5. Mark a plan `completed` only after every acceptance item is satisfied and
   its verification section contains the commands, tests, or manual checks that
   prove it. Move its index entry here but keep the plan file as a concise
   execution record.
6. Mark a plan `superseded` only when it links to the replacement plan and
   explains why the original outcome is no longer being pursued.
7. Use ISO dates (`YYYY-MM-DD`) and repository-root-relative double-links so
   `uv run python scripts/check_doc_links.py` can verify every reference.

The planning workflow itself is part of
[[docs/design/documentation-system]].
