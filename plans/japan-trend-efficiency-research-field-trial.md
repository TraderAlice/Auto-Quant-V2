# Japan trend-efficiency research field trial

- Status: `completed`
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

- [x] A fresh installed-wheel worker preserves the exact question and writes
      the English research brief before quantitative work.
- [x] The worker starts with zero OHLCV, discovers the Japanese acquisition
      guidance, attempts two routes, and preserves truthful provider semantics
      and task-complete package evidence.
- [x] Exactly one predeclared Factor family evaluates the fixed formula over
      the exact prediction universe and caller-owned horizons without hidden
      parameter or universe search.
- [x] Portfolio evidence uses the same current Factor, long-only roles, named
      benchmark, cadence, caps, costs, and volatility ceiling.
- [x] The handoff distinguishes predictive qualification from post-cost
      portfolio viability and reports negative or inconclusive evidence
      honestly.
- [x] Context-only `1306.T` never enters Factor ranking or model positions and
      no result grants Order or trading authority.
- [x] Every material retry or failure becomes either deterministic regression
      coverage and a bounded repair or an explicit provider/research limit.
- [x] Final worker replay, complete tests, docs, build/install, Studio, and
      no-hardlink clean-clone smoke pass before `v0.9.12` is tagged and pushed.

## Work

- [x] Define one caller-fixed non-U.S. Factor-to-Portfolio assignment from a
      clean released `v0.9.11` baseline.
- [x] Prepare an isolated installed-wheel desk and immutable host inventory.
- [x] Run the unchanged baseline assignment with a fresh Grok worker.
- [x] Audit the transcript, files, evidence, and scientific answer.
- [x] Implement only reproduced reusable friction with deterministic tests.
- [x] Replay the complete assignment with a fresh worker.
- [x] Complete the `v0.9.12` release audit and publish the tag.

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
- 2026-08-01 — Candidate cohort 26 began with zero OHLCV and the exact updated
  wheel. It first encountered strict invalid-OHLC rejection, explicitly
  authorized the bounded removal, then independently encountered and
  separately authorized the `1306.T` transient-scale removal. The final
  provider audit exposed both OHLC observations (`8306.T`, `8035.T`) and both
  scale-island observations (`1306.T`) while preserving exact raw bytes and
  boundary ratios. The aligned panel contained 1,844 sessions per asset.
- 2026-08-01 — Cohort 26 created exactly one `decision-signal` Project, one
  Factor Run, one Portfolio Run, two Reports, one Factor-led Dossier, and no
  Session. `1306.T` remained context-only throughout. It correctly concluded
  that validation IC `0.087665` was not stable cross-split Factor evidence and
  refused to let Portfolio validation Sharpe `1.675691` rescue negative train
  and test-relative evidence. Host validation and Studio projection passed;
  terminal orientation is `dossier-published`,
  `required-research-complete`, `observe`, with no primary action.
- 2026-08-01 — The final worker also exposed one operational defect outside
  the scientific lifecycle: an Agent shell may keep `aq` on the candidate
  venv while resolving bare `python3` to the system interpreter. The worker
  attempted a user-site pandas install before recovering, which is unacceptable
  Harness ergonomics even though the research evidence remained isolated.
  Bundled Skills now use the `aq-python` bridge, which always executes with the
  interpreter and dependencies that own the current AutoQuant installation;
  guidance explicitly forbids repairing this mismatch with global/user
  installs.

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
- Candidate cohort 26 used wheel SHA-256
  `45add5ab92fd434bc1c88278ff9cd155b979d83a993c21e93a78a147fd6eeb4a`.
  Its exact assignment, 948-line exported transcript, raw stream, provider
  packages, immutable Project evidence, and host audits remain under
  `grok-field-trials/cohort-26-japan-trend-efficiency-v0912-scale-clean`.
  `aq validate` returned no diagnostics; Studio projected one Project; the
  final desk contains one Project, two Runs, two Reports, one Dossier, and zero
  Sessions.
- The Harness-owned Python bridge and regenerated canonical/discovery Skill
  bundle passed 35 focused tests in 2.423 seconds; `aq-python` selected the
  repository venv interpreter and imported its pandas without ambient
  `python3` or user-site repair.
- Complete repository regression passed all 387 tests in 1,107.397 seconds,
  and all 1,328 documentation links resolved. Lock validation, Python
  compileall, and Studio JavaScript syntax checks also passed. The final
  build/install, bounded Agent runtime, and clean-clone receipts are recorded
  below at publication.
- Final source and wheel distributions built successfully. The Python 3.11.14
  wheel environment installed pandas 3.0.5, exposed all 53 public `aq`
  commands, and resolved `aq-python` to its own interpreter. Wheel SHA-256 is
  `0503714efb42ac0593c3e48dd7a9cad54596515edc2df823226a5a427d2e17da`;
  sdist SHA-256 is
  `7a38163d38d14275edbec727cd953c9b9ccf8980dd202ec2083d09106d97a0da`.
- Fresh Grok 4.5 cohort 27 completed the exact installed-runtime smoke in
  three turns. It read only the generated acquisition and Yahoo Skills, chose
  `aq-python` itself, ran provider `--help`, printed the trial venv's exact
  `sys.executable`, installed nothing, acquired nothing, and changed no
  Workspace file. Session `019fbb6a-9e85-7850-9401-3143a3f49b2a` and its
  76-line transcript remain under
  `grok-field-trials/cohort-27-aq-python-runtime-v0912`.

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
- 2026-08-01 — Candidate cohorts 25 and 26 successively reproduced the hidden
  Yahoo benchmark scale defect and proved the bounded repair. Cohort 26 is the
  clean scientific acceptance replay: correct claim before the first Run,
  complete anomaly disclosure, one immutable Run per lane, honest negative
  cross-lane handoff, and terminal Dossier orientation. Its ambient-Python
  friction produced the final `aq-python` runtime bridge; only the complete
  release audit remains.
- 2026-08-01 — Complete regression passed all 387 tests. The release audit
  then rebuilt the distributions and repeated installed-wheel, bounded fresh
  Agent, Studio, and no-hardlink clean-clone verification before publication.

## Completion

AutoQuant `0.9.12` proved that a fresh coworker can start from a fixed Japanese
research question and zero OHLCV, acquire and audit imperfect provider data,
preserve the caller's prediction/context boundary, translate one fixed Factor
into Portfolio evidence, and stop with a truthful negative/inconclusive
Dossier. Reproduced Workbench friction became bounded data-quality gates,
canonical provider identity, pre-Run claim guidance, terminal Dossier
orientation, and a Harness-owned Python runtime bridge. The release adds no
shared data inventory, live execution authority, or OpenAlice migration;
OpenAlice deliberately remains on `0.8.31`.
