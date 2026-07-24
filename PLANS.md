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

There are no proposed plans.

## Paused plans

There are no paused plans.

## Completed plans

| Plan | Outcome | Updated |
| --- | --- | --- |
| [[plans/mechanical-position-lifecycle-evidence]] | Reconstructed every split-bounded executed position episode with holding, contribution, cost, excursion, and signal/execution mismatch evidence. | 2026-07-25 |
| [[plans/executed-book-risk-compliance]] | Made the final post-drift, post-no-trade Portfolio and governed-RL book obey the causal request-bound volatility ceiling. | 2026-07-25 |
| [[plans/ohlcv-liquidity-capacity-envelope]] | Turned exact mechanical trade paths and causal trailing OHLCV dollar volume into a reconciled capital-capacity envelope. | 2026-07-25 |
| [[plans/portfolio-risk-governor]] | Made every request-bound Portfolio and governed-RL sleeve obey one causal covariance-based volatility ceiling with auditable sizing evidence. | 2026-07-25 |
| [[plans/selection-adjusted-research-evidence]] | Quantified Project-wide strategy-search selection risk instead of treating a chosen backtest as one isolated trial. | 2026-07-24 |
| [[plans/request-bound-portfolio-mandates]] | Bound Portfolio and governed-RL positions to one request-derived, content-locked direction and tradable-asset mandate. | 2026-07-24 |
| [[plans/reported-session-completion]] | Let a delegated baseline-retaining lane finish without promotion and leave no false active conflict. | 2026-07-24 |
| [[plans/program-research-dossier]] | Published one immutable Project-level OpenAlice handoff over verified Factor, Portfolio, and optional RL Reports. | 2026-07-24 |
| [[plans/research-cockpit-ui]] | Turned the three-lane Studio first viewport into a truthful Project cockpit with selectable evidence detail. | 2026-07-24 |
| [[plans/governed-factor-to-rl-fusion]] | Bound the current candidate factor into governed RL as a content-locked Study dependency and measured adaptive value beyond the factor itself. | 2026-07-24 |
| [[plans/multi-study-quant-research-desk]] | Created one request-driven Project with coordinated Factor, Portfolio, and governed-RL Studies plus shared CLI/Studio program status. | 2026-07-24 |
| [[plans/rl-policy-evidence-explorer]] | Projected one governed RL Run into verified baseline, fold/seed, training, action, and implementation evidence for Agents and Studio. | 2026-07-24 |
| [[plans/factor-evidence-explorer]] | Projected one verified Factor Run into a bounded professional tear sheet for Agents and Studio. | 2026-07-24 |
| [[plans/session-decision-matrix]] | Compared one verified Session across professional factor, portfolio, implementation, robustness, mechanical-policy, and RL evidence. | 2026-07-24 |
| [[plans/portfolio-decision-explorer]] | Projected verified portfolio accounting, positions, mechanical signal state, and attribution into a bounded human/Agent decision surface. | 2026-07-24 |
| [[plans/request-driven-market-data-intake]] | Turned a real request and caller-supplied OHLCV snapshot into a content-locked research Project. | 2026-07-24 |
| [[plans/mechanical-signal-policy-and-attribution]] | Made signal-state triggers, target sizing, and portfolio contribution attribution explicit. | 2026-07-24 |
| [[plans/professional-factor-diagnostics]] | Added purge-aware rank/Pearson IC, decay, significance, quantiles, style overlap, stability, and exact daily evidence. | 2026-07-24 |
| [[plans/research-selection-integrity]] | Made reference promotion validation-only and disclosed trial/test reuse across Session, Report, and Studio. | 2026-07-24 |
| [[plans/rl-factor-policy-lab]] | Added a governed causal state encoder and fixed factor-mixture Q-policy with folds, seeds, portfolio rewards, simple baselines, and exact model evidence. | 2026-07-24 |
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
