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
| [[plans/retire-flat-freqtrade-harness]] | Remove the executable Auto-Quant Classic/Freqtrade compatibility arena and make V2 Projects the only current architecture. | 2026-07-27 |
| [[plans/caller-owned-asset-position-roles]] | Let callers assign long-only, short-only, two-sided, or context-only research duties to individual assets and make Portfolio/RL share them. | 2026-07-27 |
| [[plans/market-clock-decision-anchors]] | Bound caller-owned Portfolio/RL cadence to either the complete dataset or each verified XNYS market session. | 2026-07-27 |
| [[plans/caller-owned-decision-cadence]] | Separated caller-owned Portfolio/RL decision cadence from the locked base K-line cadence while preserving continuous risk compliance. | 2026-07-27 |
| [[plans/caller-owned-benchmark-reference]] | Let delegated research questions choose cash or one named opportunity-cost asset and make Portfolio/RL share and explain that exact benchmark. | 2026-07-27 |
| [[plans/caller-owned-asset-position-caps]] | Let callers assign different maximum research weights to requested assets and make Portfolio/RL share, audit, and explain those exact limits. | 2026-07-27 |
| [[plans/request-bound-research-horizon]] | Made the caller's numerical forward horizon govern Factor selection and remain explicit across Portfolio, RL, Studio, and handoff evidence. | 2026-07-27 |
| [[plans/caller-owned-portfolio-research-policy]] | Let each OpenAlice/local request lock the risk, cost, rebalance, and reference-capital assumptions shared by Portfolio and governed RL. | 2026-07-27 |
| [[plans/configurable-session-interval-inputs]] | Made the base K-line interval explicit and added calendar-verified XNYS intraday/session aggregation shared by Factor, Portfolio, and RL. | 2026-07-27 |
| [[plans/frozen-external-holdout-challenge]] | Bound a completed research Dossier's exact leaders to a strictly later compatible Project and published one frozen external-period challenge. | 2026-07-26 |
| [[plans/evidence-driven-research-agenda]] | Turned verified Factor, Portfolio, and governed-RL diagnoses into bounded validation-only experiment briefs for AI researchers. | 2026-07-26 |
| [[plans/governed-factor-component-evidence]] | Made candidate-declared multi-horizon factor components individually auditable without inferring source semantics or changing Portfolio/RL authority. | 2026-07-26 |
| [[plans/causal-multi-interval-factor-inputs]] | Let one 1h decision clock consume completed 3h/4h/6h/12h/1d factor context through a content-locked causal pandas surface shared by Factor, Portfolio, and RL. | 2026-07-26 |
| [[plans/fast-candidate-preflight]] | Gave research Agents a fixed seconds-scale candidate check before complete Judge evaluation without creating selection evidence. | 2026-07-26 |
| [[plans/ai-first-agent-orientation]] | Gave a new research Agent one verified work brief with the current question, blocker, edit boundary, and exact next action, shared with human Studio review. | 2026-07-25 |
| [[plans/portfolio-diversification-stress]] | Explained whether different positions are independent risk bets or one correlation-crowded trade, and froze that stress through OpenAlice handoff. | 2026-07-25 |
| [[plans/evidence-gated-research-progression]] | Made verified Factor and Portfolio evidence—not mere lane completion—govern downstream Portfolio/RL research admission and early-stop handoff. | 2026-07-25 |
| [[plans/factor-qualification-funnel]] | Proved distinct incremental candidate-factor information before Portfolio and governed-RL research. | 2026-07-25 |
| [[plans/rl-factor-fusion-diagnosis]] | Diagnosed whether candidate-factor opportunity becomes stable post-cost adaptive value versus a mechanical baseline. | 2026-07-25 |
| [[plans/signal-to-portfolio-monetization]] | Explained how normalized signal intent becomes sized, governed, executed, and post-cost portfolio return. | 2026-07-25 |
| [[plans/portfolio-strategy-viability]] | Diagnosed whether a mechanical strategy loses its edge at factor prediction, gross monetization, trading friction, or post-cost robustness. | 2026-07-25 |
| [[plans/portfolio-sizing-anatomy]] | Explained how signal conviction, inverse volatility, caps, water-filling, covariance risk, and execution produce each asset weight. | 2026-07-25 |
| [[plans/report-bound-mechanical-decision-handoff]] | Froze one Portfolio leader Run's verified mechanical decision through lane Report, Project Dossier, and OpenAlice handoff. | 2026-07-25 |
| [[plans/mechanical-decision-ticket]] | Made the current signal threshold, target sizing, risk adjustment, and execution gate inspectable from one verified Portfolio Run. | 2026-07-25 |
| [[plans/governed-rl-factor-opportunity-audit]] | Exposed every governed RL decision's same-pretrade one-step factor opportunities without granting hindsight selection authority. | 2026-07-25 |
| [[plans/portfolio-parameter-neighborhood]] | Made every mechanical Portfolio result disclose its local entry/exit and no-trade parameter stability without opening a hidden optimization channel. | 2026-07-25 |
| [[plans/rl-policy-behavior-rationale]] | Explained governed-RL action persistence and every frozen linear chosen-versus-runner-up Q decision with exact reconciled evidence. | 2026-07-25 |
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
