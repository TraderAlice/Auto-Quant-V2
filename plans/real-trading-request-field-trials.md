# Real trading request field trials

- Status: `active`
- Updated: `2026-07-28`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/request-bound-portfolio-mandates]], and
  [[docs/design/project-derived-workbench-needs]].
- Field evidence: [[docs/trading-request-field-trials]].

## Outcome

Prove whether an AutoQuant coworker can receive representative questions that
an OpenAlice investment-research desk encounters during real trading work,
clarify each question without distorting caller intent, execute the appropriate
bounded quantitative research, and return useful evidence or an explicit
unsupported boundary. Repair reusable Workbench gaps only when field-trial
evidence demonstrates them.

## Context

AutoQuant has deep executable coverage of Factor, Portfolio, governed RL,
multi-interval OHLCV, request-owned mandates, immutable Runs, and research
handoffs. Most proof so far follows those implementation lanes. A delegating
Agent does not naturally ask for a lane; it asks whether to add to an asset,
which names deserve capital, how large positions should be, whether a
relative-value thesis survives costs, or where an existing book is crowded.

The next product test must therefore begin with ordinary trading questions and
judge the complete Agent experience from clarification through handoff.
Passing requires preserving the caller's decision and uncertainty, not merely
finding a schema-compatible paraphrase.

## Scope

### In scope

- Maintain a compact field-trial matrix of raw caller-language requests,
  material clarifications, chosen research route, supported and unsupported
  semantics, evidence produced, and observed Agent friction.
- Exercise at least three distinct request families:
  cross-sectional selection/target weights, single- or small-asset timing with
  wider context and multiple intervals, and relative-value or portfolio-risk
  diagnosis.
- Use public `aq` operations, Project-root English `research.md`, content-locked
  OHLCV, bounded Runs/Sessions, and immutable Reports or Dossiers.
- Record Project-observed gaps in each Project's `framework-needs.md`; promote
  only reusable, reproduced gaps into Core changes.
- Preserve negative research conclusions and honest unsupported boundaries as
  successful field-trial outcomes when the Workbench remains operable.

### Out of scope

- Live account access, Broker reconciliation, approval, order submission, or
  pretending historical target weights are executable account instructions.
- Automatic natural-language classification or replacing Agent clarification
  with a rigid request form.
- Full fundamental, news, options, L2, borrow, funding, tax, or point-in-time
  constituent data support.
- Reopening Order/TPSL implementation unless a field trial proves historical
  execution semantics are required to answer the research question itself.
- Optimizing a candidate until every request produces a positive strategy.

## Acceptance

- [x] A durable matrix covers representative trading requests and distinguishes
  caller intent, necessary clarification, Workbench route, and known boundary.
- [ ] At least three materially different request families are constructed and
  exercised through public AutoQuant workflows using non-toy market data.
- [ ] Every trial leaves a recoverable English brief, exact request/data
  authority, reproducible evidence, and a useful handoff or explicit refusal.
- [ ] Observed Agent friction is separated into Project-local methodological
  work versus reusable Workbench gaps, with the highest-priority common gap
  implemented and regression-tested when one is demonstrated.
- [ ] CLI, Studio, Reports/Dossiers, documentation, focused tests, full
  regression, package build, and repository cleanliness are audited before
  completion.

## Work

- [x] Inventory existing capabilities against raw trading-request archetypes
  and publish the initial field-trial matrix.
- [x] Construct and complete the cross-sectional selection/target-weight trial.
- [x] Construct and complete the multi-interval timing/context trial.
- [ ] Construct and complete the relative-value or portfolio-risk trial.
- [x] Reproduce and prioritize common Workbench gaps revealed by the trials.
- [x] Implement the highest-priority justified improvement and rerun affected
  trials.
- [ ] Complete regression, documentation, packaging, commit, and push.

## Findings and decisions

- 2026-07-28 — The field trials begin from ordinary delegated language rather
  than Factor/Portfolio/RL lane names. Routing is researcher-owned method;
  changing the supported decision, horizon, universe, risk appetite, or
  deliverable to fit an existing template is not allowed.
- 2026-07-28 — Existing positions and authenticated account state remain
  OpenAlice/UTA authority. AutoQuant may research model target weights and
  historical risk; the delegating Agent can compare those with live holdings.
- 2026-07-28 — The first new Project validates directly, but Workspace-level
  validation retroactively rejects an older Project that predates the fixed
  Factor-claim dependency. Recorded Study hashes distinguish a complete legacy
  closure from partial tampering, so Core should grandfather only the former
  and keep strict validation for every current contract.
- 2026-07-28 — The first request omitted a Factor research claim because the
  caller asked for allocation, not novelty. Intake's `novel-factor` default
  silently strengthens and changes that question. General decision support
  needs a third explicit claim that gates on robust raw predictive evidence
  while retaining style overlap as disclosure.
- 2026-07-28 — The 5/10/20/60-session baseline executed successfully, but
  Explorer and orientation assumed `rankIcH1`. Path sampling must use the
  request's primary horizon, not one hardcoded diagnostic.
- 2026-07-28 — The first field-driven public contract increment is AutoQuant
  `0.2.0`: decision-signal research, complete legacy claim compatibility, and
  primary-horizon Explorer sampling. Existing immutable Runs retain their
  recorded Harness identity.
- 2026-07-28 — The corrected equity-allocation Session retained five-session
  reversal as an improved but unqualified leader: validation IC `0.084686`,
  HAC t `1.715`, uneven validation folds, and family-adjusted p `0.258767`.
  The immutable Report correctly withheld target weights and Portfolio/RL
  progression instead of manufacturing an allocation.
- 2026-07-28 — The authorized-only follow-up produced validation IC `0.061599`
  and `REVERT`, proving that context-only target observations materially change
  a request-specific decision claim. AutoQuant `0.3.0` now gives candidate
  code the complete research panel but evaluates `decision-signal` only on
  Mandate `tradableAssets`; Factor-identity claims retain complete-universe
  evaluation. Factor diagnostics disclose the exact prediction population.
- 2026-07-28 — Source `KEEP`, scientific qualification, and downstream
  progression are distinct authorities. CLI guidance now states that
  promotion preserves the best source and closes the Session without granting
  Factor qualification, Portfolio/RL admission, or trading authority.
- 2026-07-28 — The BTC hourly trial proved a same-Core single-asset temporal
  Factor contract. AutoQuant `0.4.0` evaluates one request-authorized asset
  across time while leaving ETH, SOL, BNB, and XRP available only as feature
  context; two or three prediction assets remain a relative-value boundary.
- 2026-07-28 — Multi-horizon continuation reverted at validation IC
  `-0.178427`; the opposite overextension-reversion hypothesis retained
  `0.178427`, HAC t `2.391`, and two positive validation folds. A clean
  AutoQuant `0.4.1` reproduction had family-adjusted p `0.033568`, while the
  already-visible sample still requires a fresh external holdout.
- 2026-07-28 — Full hourly Portfolio evaluation exposed repeated pandas and
  Mandate work plus an unrealistic 60-second budget. AutoQuant `0.4.1`
  vectorized covariance/accounting storage, reused resolved Mandates, and
  deduplicated equivalent robustness profiles; `0.4.2` fixes the bounded
  Portfolio budget at 180 seconds. The 9,408-hour Run completed in 144,399 ms.
- 2026-07-28 — The completed Portfolio result is negative: validation gross
  Sharpe `1.920` becomes net Sharpe `-1.819` after 15 bps, with annualized
  one-way turnover `82.473`. The same Run exposed an open correctness defect:
  no-trade drift allowed executed BTC weight `0.316860` above its `0.30` cap.

## Verification

- Cross-sectional field trial:
  - baseline Run `run-20260728T081235762766Z-c6e953f8dad6`;
  - retained leader Run `run-20260728T081340625334Z-de1a16dbede3`;
  - authorized-only reverted Run
    `run-20260728T081727225961Z-132c0948dceb`;
  - terminal Report `report-20260728T081902704910Z-bcb2bc282fd6`;
  - promoted terminal Session
    `session-20260728T081255744887Z-4d3d9bd0df53`.
- Crypto timing/context field trial:
  - preserved AutoQuant `0.3.0` unsupported Run
    `run-20260728T085522890105Z-ef731be49a57`;
  - AutoQuant `0.4.0` baseline
    `run-20260728T091727168123Z-92487791e08b`;
  - retained temporal factor Run
    `run-20260728T092002595194Z-eb3f9a63a874`;
  - clean AutoQuant `0.4.1` reproduction
    `run-20260728T095650387668Z-a3bb04252cdc`;
  - complete AutoQuant `0.4.2` Portfolio Run
    `run-20260728T100043368147Z-bf56b58eeef7`.
- Prediction-universe and affected workflow regression: 42 Factor/Intake tests
  and 37 Explorer/Research-program/Session/CLI/orientation tests passed.
- Full-suite, package, and cleanliness audit remain pending until all three
  request families complete.

## Progress log

- 2026-07-28 — Plan created after auditing current templates, completed
  capability plans, and the Agent-native workbench/intake boundaries.
- 2026-07-28 — Published the initial request matrix and constructed
  `us-megacap-one-month-allocation` from a clarified caller-style question and
  an existing twelve-asset Yahoo daily package.
- 2026-07-28 — The first Workspace-wide validation exposed a reproducible
  persistent-desk compatibility defect before any research execution.
- 2026-07-28 — Repaired legacy Factor-claim compatibility and primary-horizon
  Explorer sampling, then recovered a complete Factor tear sheet and Agent
  orientation from the real 20-session baseline.
- 2026-07-28 — Completed the corrected request with two bounded Experiments,
  an evidence-bound negative Report, and a promoted terminal Session. Repaired
  the reusable prediction-population and promotion-authority UX gaps revealed
  by that handoff.
- 2026-07-28 — Completed the BTC multi-interval timing/context request through
  Factor qualification, clean reproduction, and the full costed BTC/cash
  Portfolio route. Preserved the negative implementation conclusion and
  recorded the post-drift asset-cap defect for Core repair.

## Completion

Pending.
