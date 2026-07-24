# Quantitative research lifecycle and OpenAlice handoff

Status: delegation/report lane implemented; portfolio and RL lanes targeted.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/study-run-evidence]], [[docs/design/research-session-loop]],
[[docs/design/external-researcher-driver]], and
[[docs/design/studio-observation-surface]].

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
→ immutable Research Report
→ OpenAlice Inbox publication with authoritative provenance
→ human/Agent decision and separately authorized forward execution
```

A Project is the construction site for one evolving research problem. A Study
is one fixed evaluation question inside it. A Session is one active line of
candidate research against that fixed authority. A Run is one immutable
execution. A Report is a content-hashed decision-support handoff over an exact
evidence snapshot.

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

## Mechanical signal-to-portfolio contract

The initial portfolio lane uses OHLCV bars and target weights, not a broker
order book:

```text
causal factor values at bar t
→ cross-sectional normalization or rank
→ optional causal volatility scaling
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

Tolerance bands are a first-class implementation choice: research on
rebalancing frames the problem as tracking-error versus transaction-cost
control rather than blindly trading every calendar interval:
<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3858951>.

## Governed reinforcement learning

The first RL use case is a meta-policy over causal factors or portfolio target
weights, not an opaque trading bot:

- state: current causal factor vector, volatility/regime features, and previous
  target or position;
- action: factor blend weights or constrained portfolio target weights;
- transition: the next chronological bar or rebalance interval;
- reward: next-period net portfolio return minus fixed cost, risk, turnover,
  and constraint penalties;
- artifact: exact policy configuration, dependency identity, seed, learned
  parameters, and training history.

The Judge owns state timing, action bounds, reward, costs, constraints,
splits, seeds, budgets, and baselines. Candidate code may implement a feature
transform, policy, or training method only within the declared editable
closure.

Required evidence includes:

- untouched chronological test folds or walk-forward windows;
- every declared random seed, not only the best seed;
- mean, dispersion, and failure rate across seeds and folds;
- equal-weight, fixed-factor, and simple linear baselines;
- net turnover/cost/risk metrics from the same portfolio accounting;
- no test-set tuning or reward changes during candidate search.

Financial RL evidence is fragile. A recent multi-method benchmark reports weak
robustness and rapid degradation for many deep portfolio methods:
<https://arxiv.org/abs/2306.10950>. More generally, reproducibility work on
deep RL emphasizes intrinsic variance and standardized statistical reporting:
<https://ojs.aaai.org/index.php/AAAI/article/view/11694>. AutoQuant therefore
treats RL as a higher-burden candidate lane rather than a privileged source of
truth.

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
- Is a verified report ready, and what exact CLI command advances the work?

The browser may copy exact headless commands, filter, compare, and inspect. It
must never invent a metric, approve a candidate, publish a report, or become a
second evaluator. Human guidance enters through explicit request/analysis
artifacts so AI work remains attributable and reproducible.

## Phased delivery

1. Delegation and report handoff:
   [[plans/openalice-research-handoff]].
2. Causal signal-to-portfolio accounting and professional evidence:
   [[plans/portfolio-construction-lab]].
3. Governed RL factor/target policy lane:
   [[plans/rl-factor-policy-lab]].

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

- Portfolio construction/accounting is designed but not implemented.
- RL execution is designed but not implemented and depends on the portfolio
  lane.
- Cross-Project report aggregation and OpenAlice-side automatic Project
  creation remain future collaboration work.
