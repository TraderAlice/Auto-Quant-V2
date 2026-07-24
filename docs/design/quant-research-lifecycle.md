# Quantitative research lifecycle and OpenAlice handoff

Status: request-driven Project intake, delegation/report, portfolio, and
governed RL lanes implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/study-run-evidence]], [[docs/design/research-session-loop]],
[[docs/design/external-researcher-driver]],
[[docs/design/studio-observation-surface]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/portfolio-construction-lab]], and
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/research-selection-integrity]], and
[[docs/design/session-decision-matrix]].

## Scope

This document owns the end-to-end product direction for AutoQuant as
OpenAlice's quantitative research workbench:

- external request and final report boundaries;
- the evidence a working quantitative researcher needs;
- the causal translation from factor signals to a portfolio;
- the first governed role for reinforcement learning;
- the division of responsibility between Core, Agent CLI, and Studio.

Detailed executable contracts remain in the subsystem documents linked above.
AutoQuant is a decision-support laboratory. It does not own broker state,
orders, or an OpenAlice Unified Trading Account.

## Workbench collaboration

The durable lifecycle is:

```text
OpenAlice or local caller
→ strict Research Request
→ self-contained Project and fixed Study
→ governed Session with derived Research Brief
→ bounded Runs, Experiments, and Campaigns
→ immutable lane Research Reports
→ immutable Project Research Dossier
→ OpenAlice Inbox publication with authoritative provenance
→ human/Agent decision and separately authorized forward execution
```

A Project is the construction site for one evolving research problem. A Study
is one fixed evaluation question inside it. A Session is one active line of
candidate research against that fixed authority and ends by either promoting
an improved KEEP or completing against an exact baseline-retaining Report. A Run is one immutable
execution. A Report is one lane's content-hashed decision-support handoff over
an exact evidence snapshot. A Dossier composes verified current lane Reports
into the Project-level answer without re-evaluating raw Runs.

The request can now create that construction site through strict external
daily-OHLCV intake. The caller supplies a package; AutoQuant validates and
normalizes it into Project-local content, records provider/calendar/adjustment
claims, binds request/dataset/Study hashes, and exposes exact baseline and
Session-start actions. Retrieval remains external authority. See
[[docs/design/research-intake-and-dataset-snapshots]].

OpenAlice's Workspace and Session ids in a request are caller-supplied context.
AutoQuant preserves and hashes them but cannot authenticate them. OpenAlice
stamps its own authoritative Session origin and exact document revision when
the report is delivered to Inbox. This prevents an AutoQuant process from
forging collaboration provenance while still preserving the request/report
chain.

## Request and brief authority

A Research Request carries:

- the question and decision context;
- requested assets and directional hypothesis;
- intended decision horizon;
- hypotheses, constraints, and requested deliverables;
- optional caller-supplied OpenAlice Workspace, Session, document path, and
  document revision.

Starting a delegated Session validates and normalizes the request, then derives
a Brief from the exact request plus the selected Project, Study, baseline, and
fixed program/Judge/dataset/Harness locks. The request and brief are copied
into the Session and validated on every load.

The Brief has `research-prioritization` authority. It can tell a Researcher
which hypotheses and deliverables matter. It cannot change the Study, Judge,
dataset, promotion rule, or trading account. Human intent is therefore an
input to research, not a hidden override of quantitative evidence.

## Quantitative evidence stack

No single Sharpe ratio is a sufficient research verdict. AutoQuant should
present evidence in layers so a human or Agent can see where a candidate gains
and where it fails.

### Factor quality

- coverage and missingness;
- Pearson IC and rank IC;
- IC mean, dispersion, and IC information ratio;
- forward-horizon decay;
- quantile monotonicity and top-minus-bottom spread;
- stability by asset, chronological fold, and declared market regime.

The implemented reference Factor Lab now fixes dataset-derived purged 1/5/10
bar horizons, Newey-West mean-IC inference, tertile returns/monotonicity,
causal market regimes, two folds per split, per-asset time-series rank
correlation, and overlap with four fixed OHLCV styles. It publishes daily IC
and quantile artifacts while retaining validation one-bar mean IC as the sole
promotion objective. See [[docs/design/factor-diagnostics]].

### Portfolio implementation

- gross and net return, CAGR, volatility, Sharpe, and Sortino;
- maximum drawdown, Calmar, tail loss, and expected shortfall;
- benchmark beta, active return, tracking error, and information ratio;
- turnover, estimated cost, cost drag, and rebalance frequency;
- gross exposure, net exposure, leverage, maximum weight, concentration, and
  participation/capacity evidence when volume assumptions exist.

### Robustness and research integrity

- chronological out-of-sample and walk-forward results;
- per-asset, per-regime, and per-fold dispersion rather than only an aggregate;
- delayed-execution, higher-cost, and parameter-neighborhood stress;
- trial count and selection-adjusted evidence when many variants were tried;
- explicit failure, missing-data, and non-finite metric evidence.

The Deflated Sharpe Ratio literature explains why selection bias, multiple
testing, and non-normal returns must temper the best observed backtest:
<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551>. Transaction-cost
research shows that turnover and expected return are inseparable portfolio
trade-offs:
<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=972184>. These sources
motivate evidence fields; they do not grant a candidate permission to compute
its own acceptance rule.

Core must keep alpha, sizing, portfolio construction, and execution assumptions
separate. A candidate can have predictive factor quality and still be
uninvestable after constraints and costs. Conversely, a stable low-turnover
portfolio may be useful without an impressive raw IC.

Reference candidate promotion uses validation only. Test metrics are visible
diagnostic evidence, so Core conservatively marks a Session as requiring a new
external holdout after candidate iteration. Trial/verdict counts and this
warning are derived from immutable history and frozen into Reports; statistical
selection adjustment remains separate until its assumptions are fixed. See
[[docs/design/research-selection-integrity]].

## Mechanical signal-to-portfolio contract

The implemented `ohlcv-portfolio-lab` uses OHLCV bars and target weights, not
a broker order book:

```text
causal factor values at bar t
→ cross-sectional percentile and explicit entry/hold/exit/reversal intent
→ causal conviction and inverse-volatility sizing
→ long-only or long/short budget
→ per-asset, gross, net, leverage, and concentration constraints
→ target weights
→ optional tolerance/no-trade bands
→ rebalance after a declared lag
→ turnover and fixed cost model
→ portfolio return over the next bar
```

Every transform is fixed Judge authority for a comparison. Positions use only
information available at the decision timestamp, and returns are credited only
after the declared execution lag. OHLCV cannot prove queue position, spread
dynamics, or L2 fills, so results must say `bar-target-weight simulation`
rather than imply exchange-level precision.

Target weights are the correct handoff for AutoQuant because OpenAlice may use
the findings as one input to a later decision. Live order types, TPSL,
available balance, venue rules, and account mutations remain forward-looking
OpenAlice/UTA concerns.

The first reference contract is deliberately narrower than the general sketch:
it uses fixed `0.75/0.25` entry and `0.55/0.45` exit percentiles, is gross-one
dollar-neutral, allocates `+0.5/-0.5`, caps absolute target weight at `0.30`,
retains the drifted book below `0.05` one-way turnover, and charges every
bought or sold dollar at the declared basis-point cost. Its exact ledger
connects signal intent, proposed target, pre-trade drift, executed weight,
trade, return, cost, regime, and component variance contribution. The
executable details are [[docs/design/portfolio-construction-lab]] and
[[docs/design/signal-policy-and-attribution]].

Tolerance bands are a first-class implementation choice: research on
rebalancing frames the problem as tracking-error versus transaction-cost
control rather than blindly trading every calendar interval:
<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3858951>.

## Governed reinforcement learning

The implemented `ohlcv-rl-factor-lab` is a meta-policy over causal factors,
not an opaque trading bot:

- state: current causal factor vector, volatility/regime features, and previous
  target or position;
- action: one governed stateful factor-mixture sleeve and its constrained
  portfolio target weights;
- transition: the next chronological bar or rebalance interval;
- reward: next-period net portfolio return minus fixed cost, risk, turnover,
  and constraint penalties;
- artifact: exact policy configuration, dependency identity, seed, learned
  parameters, and training history.

The Judge owns state timing, action bounds, reward, costs, constraints,
splits, seeds, budgets, and baselines. Candidate code implements only a pure
row-level causal feature transform inside the declared editable closure. The
current Factor Study candidate is a separate content-locked dependency: RL can
select its governed sleeve but cannot edit it.

Required evidence includes:

- chronologically isolated test folds or walk-forward windows;
- every declared random seed, not only the best seed;
- mean, dispersion, and failure rate across seeds and folds;
- equal-weight, fixed-factor, and simple linear baselines;
- net turnover/cost/risk metrics from the same portfolio accounting;
- no test-fold training or reward changes during candidate search, plus
  disclosure when visible test evidence has informed later candidates.

Financial RL evidence is fragile. A recent multi-method benchmark reports weak
robustness and rapid degradation for many deep portfolio methods:
<https://arxiv.org/abs/2306.10950>. More generally, reproducibility work on
deep RL emphasizes intrinsic variance and standardized statistical reporting:
<https://ojs.aaai.org/index.php/AAAI/article/view/11694>. AutoQuant therefore
treats RL as a higher-burden candidate lane rather than a privileged source of
truth.

V1 makes the candidate surface smaller than a general training adapter: the
Agent edits a pure deterministic row-level state encoder. The Judge fixes five
factor-mixture actions (candidate, three references, and equal blend), linear
Q-learning, next-bar costed reward, two
expanding folds, three seeds, portfolio accounting, and fixed/simple-linear
baselines. The promotion objective aggregates validation evidence only. Test
metrics remain visible audit evidence and carry an explicit warning that
repeated inspection consumes holdout value. Exact models, training histories,
and timestamped actions are immutable artifacts. Executable details are in
[[docs/design/rl-factor-policy-lab]].

## Research report

An Agent supplies a strict report-analysis object containing:

- title and executive summary;
- findings with confidence and exact evidence references;
- recommendations with conditions, not broker orders;
- limitations and unresolved questions.

Core resolves every reference against the verified Session and freezes an
evidence snapshot: request/brief, Study locks, baseline and current leader,
Runs, Experiments, Campaigns, artifacts, Harness, and dataset. It then
deterministically renders `report.json` and `report.md`, hashes every file, and
writes the manifest last.

Report authority is `quantitative-decision-support`. A report may recommend
further research, monitoring, avoidance, or a conditional portfolio posture.
It may not claim an order was placed, that OpenAlice approved a trade, or that
caller-supplied origin fields were authenticated.

## Project research dossier

The canonical Research Program returns one Project-level answer by composing
lane Reports:

```text
Run / Experiment / Campaign
→ delegated Session Report
→ Project Research Dossier
→ OpenAlice Inbox
```

Factor and Portfolio Reports are required. Governed RL is optional and is
included only when its current Report pins the selected Factor source;
otherwise the Dossier records the omission and reason. Agent-authored
cross-lane findings cite exact included Report and finding ids. Core verifies
coverage, freezes request/dataset/program/Study/Report/leader identities, and
renders immutable JSON and Markdown. Later research does not reinterpret an
older Dossier. The complete contract is
[[docs/design/program-research-dossiers]].

## Human-computer interaction

The CLI and JSON schemas are the primary control surface because Agents must be
able to discover, execute, and verify the complete lifecycle without a
browser. Every mutation provides:

- one stable capability id and exact command;
- strict machine input and a versioned JSON envelope;
- affected artifacts and their mutability;
- next actions and failure diagnostics.

Studio is the shared situation room for humans and Agents. It should answer:

- What did the caller ask?
- Which Project, Study, and Session own the work?
- What is mutable now, and what evidence is immutable?
- Which metric layer improved or regressed?
- Which constraints, costs, folds, or seeds failed?
- Are lane Reports ready, is the Project Dossier blocked/current, and what
  exact CLI command advances the work?

The browser may copy exact headless commands, filter, compare, and inspect. It
must never invent a metric, approve a candidate, publish a report, or become a
second evaluator. Human guidance enters through explicit request/analysis
artifacts so AI work remains attributable and reproducible.

The implemented Session Decision Matrix is the first multi-candidate HCI
surface under this rule. Core verifies and normalizes a bounded immutable trial
chain; CLI and Studio present the same metric descriptors, preference
directions, validation-only non-dominance, leader trade-offs, and explicitly
separate test-audit evidence. The browser neither chooses metrics nor changes
the fixed primary-objective verdict.

The implemented Factor Evidence Explorer applies the same rule inside one
Run. Core reconciles full daily IC and quantile artifacts before sampling;
Agents receive the normalized object through `aq run factor`, while humans
switch path, horizon, split, and stability views without browser-side
statistics or selection authority.

## Phased delivery

1. Request-driven Project and market-data intake:
   [[plans/request-driven-market-data-intake]].
2. Delegation and report handoff:
   [[plans/openalice-research-handoff]].
3. Causal signal-to-portfolio accounting and professional evidence:
   [[plans/portfolio-construction-lab]].
4. Governed RL factor/target policy lane:
   [[plans/rl-factor-policy-lab]].
5. One-request multi-Study research desk:
   [[plans/multi-study-quant-research-desk]].
6. Governed Factor-to-RL content dependency:
   [[plans/governed-factor-to-rl-fusion]].

Each phase must produce bounded deterministic evidence and a commit before the
next phase changes its assumptions.

## Invariants

1. Caller intent never overrides fixed evaluation authority.
2. Every published claim points to verified immutable evidence.
3. AutoQuant has no live-trading or OpenAlice provenance authority.
4. Signal timing, portfolio accounting, costs, and RL rewards are causal and
   fixed by the Judge.
5. Aggregate metrics never hide required per-asset, fold, regime, or seed
   evidence.
6. CLI and Studio project the same Core objects; Studio remains read-only.
7. Heavy frameworks are optional adapters. The research contract is owned by
   AutoQuant and testable on small deterministic fixtures.

## Change checklist

- Update the request/report schemas, Session locks, CLI capabilities, Studio
  snapshot, canonical docs, and tests together.
- When adding a portfolio metric, state its timing, benchmark, cost, and
  aggregation semantics in the fixed Judge.
- When adding an RL adapter, freeze seeds, budgets, dependency identity,
  baselines, model artifacts, and failure reporting.
- Never expose a field that could be mistaken for broker confirmation or
  authenticated OpenAlice origin.
- Keep routine validation bounded; large datasets or training require an
  explicit plan budget.

## Known gaps

- Mixed-asset/multi-calendar Studies, intraday intake, corporate-action
  verification, and point-in-time universe evidence remain future data work.
- Candidate-factor dependencies are Project-local source closures; immutable
  promoted Report artifacts are not yet a general cross-Project model input.
- Cross-Project report aggregation and OpenAlice-side invocation/Inbox
  publication remain future collaboration work; AutoQuant now owns the exact
  request-driven Project command and report artifacts at its boundary.
