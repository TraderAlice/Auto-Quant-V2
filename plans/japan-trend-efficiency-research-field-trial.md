# Japan trend-efficiency research field trial

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.12`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/panel-native-factor-api]],
  [[docs/design/prediction-mode-target-weight-translation]],
  [[docs/design/program-research-dossiers]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that a fresh quantitative coworker can begin with one caller-fixed
Japanese-equity question and no staged data, acquire a complete task-local
panel, test one predeclared price-efficiency factor, carry the same signal into
a bounded long-only Portfolio study, and return an evidence-backed answer
without private Workbench knowledge or trading claims.

The field trial comes before framework design. `0.9.12` will contain only
reusable friction reproduced by the worker or a truthful record that the
current Workbench already handles the assignment. No compatibility layer is
required when a cleaner current contract needs a breaking change.

## Field assignment

Ask whether persistent, low-churn trends contain useful medium-horizon
cross-sectional information among a fixed Japanese large-cap research
universe and whether the same signal survives mechanical portfolio
translation after costs.

- Prediction assets: Toyota (`7203.T`), Sony Group (`6758.T`), Hitachi
  (`6501.T`), Mitsubishi UFJ (`8306.T`), Keyence (`6861.T`), Recruit
  (`6098.T`), Tokyo Electron (`8035.T`), and Fast Retailing (`9983.T`).
- Context and named opportunity-cost benchmark: TOPIX ETF (`1306.T`), never a
  prediction or position asset.
- Completed daily observations: `2019-01-01` through `2026-07-31`, with the
  actual final completed provider session disclosed.
- Candidate score: trailing 60-session close return divided by the sum of
  absolute daily close returns over the same window. Higher positive values
  mean a more directionally efficient uptrend. The formula is fixed before
  evaluation; no parameter search is authorized.
- Primary forward horizon: 20 completed bars; diagnostic horizons: 5 and 60.
- Portfolio policy: long-only, gross limit `1.0`, per-asset cap `0.20`, named
  benchmark `1306.T`, 20-bar decision cadence, `15` basis points proportional
  cost, and a `15%` annualized research volatility ceiling.
- Use at least two suitable Japanese provider routes. Distinct raw and
  split-adjusted contracts may be compared for coverage only, never relabelled
  as numerically equivalent.
- Quantitative decision support only. Do not create Orders, TP/SL, live
  positions, or a trading recommendation.

## Scope

### In scope

- One isolated fresh Grok 4.5 worker using an exact installed `0.9.11` wheel,
  a newly initialized Workspace, generated Skills, public CLI/schema surfaces,
  and provider networking.
- Research-brief quality, Project/template choice, demand-led data acquisition,
  semantic audit, strict intake, Factor authorship, preflight, governed
  evaluation, Portfolio translation, Report/Dossier handoff, and stopping.
- Exact retry, failure, raw-access, mutation, Run, and evidence inventories.
- The smallest coherent Core, Skill, template, CLI, Studio, or documentation
  repair for every reproducible material Workbench defect.
- A second fresh installed-wheel replay and complete release audit before
  tagging `v0.9.12`.

### Out of scope

- Broad TOPIX constituent discovery, historical membership, survivorship-free
  universe construction, or changing the caller-fixed asset list.
- Factor-window, horizon, cost, cap, volatility-target, or universe search.
- Treating Nikkei as JPX authority or Yahoo as official venue truth.
- A shared data inventory, automatic background refresh, broker integration,
  Order simulation, TP/SL, suitability, or live execution.
- OpenAlice version changes; it remains pinned to `0.8.31`.

## Acceptance

- [ ] A fresh installed-wheel worker preserves the exact question and writes
      the English research brief before quantitative work.
- [ ] The worker starts with zero OHLCV, discovers the Japanese acquisition
      guidance, attempts two routes, and preserves truthful provider semantics
      and task-complete package evidence.
- [ ] Exactly one predeclared Factor family evaluates the fixed formula over
      the exact prediction universe and caller-owned horizons without hidden
      parameter or universe search.
- [ ] Portfolio evidence uses the same current Factor, long-only roles, named
      benchmark, cadence, caps, costs, and volatility ceiling.
- [ ] The handoff distinguishes predictive qualification from post-cost
      portfolio viability and reports negative or inconclusive evidence
      honestly.
- [ ] Context-only `1306.T` never enters Factor ranking or model positions and
      no result grants Order or trading authority.
- [ ] Every material retry or failure becomes either deterministic regression
      coverage and a bounded repair or an explicit provider/research limit.
- [ ] Final worker replay, complete tests, docs, build/install, Studio, and
      no-hardlink clean-clone smoke pass before `v0.9.12` is tagged and pushed.

## Work

- [x] Define one caller-fixed non-U.S. Factor-to-Portfolio assignment from a
      clean released `v0.9.11` baseline.
- [x] Prepare an isolated installed-wheel desk and immutable host inventory.
- [x] Run the unchanged baseline assignment with a fresh Grok worker.
- [x] Audit the transcript, files, evidence, and scientific answer.
- [ ] Implement only reproduced reusable friction with deterministic tests.
- [ ] Replay with a second fresh worker and complete the `v0.9.12` release.

## Findings and decisions

- 2026-08-01 — Japan was chosen because the current Skill bundle claims a
  broad delayed adjusted route plus one narrow recent raw route, while Core's
  daily research contract is intentionally provider-observed rather than
  XNYS-specific. This tests whether that separation works in an actual
  Factor-to-Portfolio task rather than another acquisition-only smoke.
- 2026-08-01 — The universe and formula are caller-fixed. A current large-cap
  list is not historical membership evidence, so the resulting claim is only
  about the named fixed research universe and must disclose survivorship and
  selection scope.
- 2026-08-01 — A favorable Factor scalar is not enough. The assignment must
  carry the exact signal through position roles, benchmark-relative evidence,
  costs, caps, cadence, and risk governance before describing portfolio
  viability.
- 2026-08-01 — The fresh `0.9.11` worker completed the assignment and returned
  a truthful negative/inconclusive Factor conclusion plus a mechanically
  feasible but benchmark-inferior Portfolio diagnosis. It kept `1306.T` out
  of rankings and positions, published a Factor-only early-stop Dossier, and
  made no trading claim.
- 2026-08-01 — Yahoo returned one impossible split-adjusted OHLC row for each
  of `8306.T` and `8035.T`. The strict Skill correctly stopped, but the worker
  needed two ad hoc wrappers to retain raw evidence and drop those isolated
  observations. The reusable repair is an explicit, tightly bounded, audited
  `drop-observation` policy; strict rejection remains the default and price
  repair remains forbidden.
- 2026-08-01 — Nikkei's asset example used provider code `7203` as the dataset
  symbol, so exact peer-package coverage comparison rejected it against Yahoo
  `7203.T`. Canonical research identity must stay stable across routes while
  the shorter numeric lookup remains provider metadata.
- 2026-08-01 — After the current early-stop Dossier was published, orientation
  still projected the blocked Factor lane and a new Session as current work.
  A matching immutable Dossier is already the caller handoff; further research
  must be explicitly optional until newer evidence makes it stale.
- 2026-08-01 — Candidate cohort 23 was stopped before research because the
  host launch packet inherited a PATH that did not select the candidate wheel.
  The worker then discovered the development checkout outside its desk. This
  is invalid host preparation, not product evidence, and does not count as a
  replay.
- 2026-08-01 — Candidate cohort 24 used only the installed `0.9.12` wheel and
  completed the research, two provider routes, Factor and Portfolio Runs,
  Reports, Factor-only Dossier, validation, orientation, and Studio. Final
  evidence again found weak/inconclusive Factor qualification and no robust
  benchmark-relative Portfolio advantage; it correctly withheld trading
  authority and stopped at `required-research-complete`.
- 2026-08-01 — Cohort 24 first selected the default `novel-factor` claim,
  noticed after a visible Run that this identity claim evaluates the complete
  research universe, then deleted the Project and recreated it with the
  caller-correct `decision-signal` claim. The final scientific contract is
  correct, but deleting immutable evidence is unacceptable and the replay is
  not first-attempt clean. The prediction-population semantics remain correct:
  factor identity uses the complete universe while request-bound decision
  support excludes Mandate context assets. Agent guidance now requires claim
  choice and resolved-population inspection before evaluation, plus preserved
  evidence and disclosure for any later request-binding correction.
- 2026-08-01 — The explicit Yahoo drop policy preserved two invalid
  observations on the same session (`8035.T` and `8306.T`, 2022-05-17). The
  aligned panel lost one date, and the worker disclosed only the first asset
  it had inspected. A successful acquisition now projects one top-level
  `invalidOhlc` summary in both command output and provider audit so Agents see
  every affected asset and observation without manually traversing per-asset
  records.
- 2026-08-01 — Candidate cohort 25 selected `decision-signal` before its first
  Run, kept `1306.T` outside the prediction population, and disclosed both
  invalid-OHLC assets from the new command summary. It then independently
  found a second, more serious provider defect: Yahoo emitted `1306.T` near
  one-tenth scale on 2026-03-30/31 before returning near its prior scale on
  2026-04-01, without a matching split event. Factor evidence remained valid,
  but benchmark-relative Portfolio metrics became nonsensical. The worker
  correctly disclosed the defect, withheld those active metrics, and published
  only the Factor lane in the Dossier.
- 2026-08-01 — A temporary scale island is not ordinary OHLC geometry and must
  not be conflated with a persistent corporate action. Yahoo acquisition now
  rejects by default a one-to-three-row island with a fivefold boundary jump,
  inverse exit, and near-origin recovery. A separate explicit bounded policy
  may remove the exact observations while preserving raw bytes and boundary
  ratios; it never rescales a price. Persistent regime changes remain outside
  this repair and require provider/corporate-action evidence.

## Verification

- Candidate implementation: 51 focused tests passed in 108.874 seconds;
  documentation link audit passed for 1,327 links; lock check and compileall
  passed.
- Live provider reproduction retained raw payloads and exactly one bounded
  invalid observation each for `8035.T` and `8306.T` on 2022-05-17; no price
  was repaired or clamped.
- Candidate cohort 24 host validation, orientation, program, Dossier, Studio,
  installed-wheel identity, and filesystem audits passed. Its remaining
  claim-selection/deletion and incomplete anomaly-disclosure behavior requires
  one final clean replay after the guidance and summary repair.
- Yahoo summary and repository Skill materialization focused regression: 31
  tests passed in 1.439 seconds.
- The transient-scale detector reproduced the exact two-row `1306.T` island
  from retained Yahoo raw JSON, rejected it by default, and under explicit
  policy removed only 2026-03-30/31 with entry ratio `0.098354`, exit ratio
  `10.479268`, recovery ratio `1.016985`, and per-asset drop bound `2`.

## Progress log

- 2026-08-01 — Plan created and indexed from clean released `v0.9.11`. No
  implementation change is authorized until the fresh baseline worker exposes
  concrete friction.
- 2026-08-01 — Baseline cohort 22 completed from the exact `v0.9.11` wheel in
  an empty desk. Host validation, orientation, program, Dossier, Studio, and
  pre-existing-file mutation audits passed; three reproducible Agent-facing
  frictions above were admitted for the candidate release.
- 2026-08-01 — Candidate commit `45e8ef6` implemented bounded Yahoo anomaly
  removal, canonical Nikkei symbol mapping, terminal Dossier orientation, and
  version `0.9.12`. Cohort 24 validated those repairs and exposed two final
  Agent-operability gaps: pre-Run Factor-claim selection and top-level anomaly
  enumeration. Both now have bounded guidance/code regressions; a clean replay
  remains required before release.

## Completion

Complete this section only when status becomes `completed`.
