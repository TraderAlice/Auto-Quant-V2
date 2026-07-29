# AutoQuant Studio

AutoQuant Studio is the local, read-only human observation surface for the
same verified research state exposed by Core and `aq`. It helps a human review
the desk where coding Agents work; it is neither the primary Agent control
surface nor an OpenAlice-specific report viewer. Standalone and hosted
Workspaces render the same Core snapshot.

## Open a Workspace

```bash
aq studio serve .
```

The server binds to `127.0.0.1:8765`, opens the default browser, and runs until
interrupted. Use a different local port or suppress browser opening with:

```bash
aq studio serve . --port 8877 --no-open
```

A direct Project path is also valid. A Workspace can be restricted to one
Project with `--project ID`.

The repository clone is already a Workspace and opens with the checked-in
`sample-research-desk`. The Workspace rail shows the effective Projects path
and labels an active `autoquant-workspace.local.json` as `LOCAL OVERRIDE`;
the top source label makes the same distinction from the checked-in Workspace
manifest. This is observation only—Studio never selects or rewrites the
configuration.

The default bind is intentionally loopback-only. V1 has no authentication.
Binding `--host` to a non-loopback address is an explicit operator decision.

## What the page shows

The first viewport prioritizes:

- every discovered Project and its verification state;
- pre-research request intake, locked dataset/provider/adjustment claims,
  requested assets versus research universe, baseline selection/audit/stress
  metrics, and the exact lifecycle command—Session start for iterative
  templates or fixed Run execution for Book Risk and Price Event Studies;
- active Sessions and current leader values;
- delegated caller questions, assets, direction, horizon, and Brief identity;
- running external Researcher phase and turn budget;
- KEEP, REVERT, and CRASH optimization trajectories;
- recent immutable Runs, Experiments, Campaigns, Research Reports, and Project
  Research Dossiers;
- factor Run summaries for validation one/five-bar IC, HAC strength, tertile
  spread, weakest chronological fold, maximum fixed-style overlap, test audit
  IC, and rank turnover;
- the latest successful Factor Run's verified IC path, fixed-horizon decay,
  quantile path, fold/regime/asset stability, style overlap, coverage, and
  turnover tear sheet;
- portfolio Run summaries for held-out IC, net Sharpe, signal-state change,
  hysteresis transition reduction, maximum asset return/risk contribution,
  attribution reconciliation, turnover, cost stress, and contextual liquidity
  capacity;
- the latest successful Portfolio Run's verified full-history growth,
  drawdown, exposure, turnover/cost path, current historical target/executed
  book, pre/post risk-governor targets and covariance forecast, recent
  mechanical transitions, final-book compliance and risk-only overrides,
  validation/test attribution, causal 1%/5%
  participation-capacity distributions, latest binding asset, and exact
  request-derived position/risk mandate;
- the latest successful Book Risk Run's reported-position volatility,
  effective risk bets, first-PC crowding, component-risk concentration,
  lookback stability, standardized reduction ranking, pair correlations, and
  unauthenticated-position authority warning;
- the latest successful Price Event Run's fixed event/timing policy, raw,
  complete, overlap-excluded, right-censored, and primary populations,
  conditional/reference distributions, uncertainty, event ledger, and
  no-trading authority warning;
- RL Run summaries for validation/test audit Sharpe, seed/fold dispersion,
  simple-baseline advantage, failure rate, and fold × seed coverage;
- a bounded Session decision matrix comparing baseline, recent candidates, and
  current leader across fixed validation, robustness, implementation, and
  test-audit metrics;
- Session selection split, Project-family unique strategy trials, duplicate
  executions, reproducibility, visible-test role, external-holdout
  requirement, and Core-authored selection adjustment;
- request → lane Reports → Project Dossier readiness and exact copyable
  headless commands;
- a three-lane Research Cockpit showing Factor validation IC, costed Portfolio
  validation Sharpe, RL validation advantage versus the best selected
  baseline, lane phase, evidence-gated admission, Session progress,
  shared-source conflicts, stale evidence, and the exact recommended next
  command;
- a first-position decision brief rendered from the exact Core
  `AgentWorkBrief` and hash also returned by `aq orient`; JavaScript formats
  its review copy but does not choose the focus, edit root, reason, or next
  action; its origin label distinguishes delegated request, verified fixed
  Project request, maintained research brief, and local manifest fallback
  without rereading or trusting files in JavaScript; when fixed candidate
  preflight is available, this same object routes
  edit → bounded Check → formal Experiment and exposes the exact current Check
  id/status without granting selection or trading authority; after KEEP it
  distinguishes a settled leader from a newer worktree edit, makes executable
  guarded promotion primary only for the settled leader, and preserves the
  delegated Report gate;
- a Research Agenda directly beneath the decision surface, rendering the exact
  Core-ordered Factor, Portfolio, or governed-RL experiment briefs from that
  same hashed work brief, including hypothesis, editable target, optional
  declared components, typed validation evidence, required checks, and stop
  conditions; a completed Book Risk or Price Event audit instead shows a
  closed descriptive agenda with no candidate moves; JavaScript never creates
  or reorders moves;
- a frozen external-holdout panel when present, showing the exact source
  Dossier, source-end/strictly-later-start boundary, imported lane set, and
  source-versus-later objective/delta cells from Core; it never colors a lane
  as a production pass or converts the audit into trading authority;
- one selectable Book Risk, Price Event, Factor, Portfolio, or RL evidence
  workbench at a time, keeping the complete bounded explorer available without
  rendering all long reports into one page;
- fixed Study catalog and Project research program;
- category-level diagnostics when evidence cannot be verified.

The browser polls a bounded snapshot every four seconds while visible. Manual
refresh remains available. Running Campaign progress is visibly labelled
mutable; completed evidence is loaded and hash-verified by Core.

Every valid Project snapshot includes `agentWorkBrief` and
`agentWorkBriefHash`. The brief is the shared AI-operator/human-reviewer
contract: Studio's Current Research Decision card and the CLI cannot disagree
about the active question, reason, next lifecycle action, or bounded experiment
order. Agenda moves remain diagnostic-only and cannot execute themselves.
Detailed Cockpit and evidence panels remain richer read models and do not
broaden its filesystem or trading authority. See
[[docs/design/evidence-driven-research-agenda]].

Run cards are diagnostic projections, not replacements for full evidence.
Factor cards show strength, decay, monotonic spread, stability, style overlap,
and test audit evidence beside the headline score. Portfolio cards show signal
churn, hysteresis effect, contribution concentration, risk-governor
activation, and reconciliation.
RL cards show implementation, dispersion, failure, and baseline comparison.
Exact nested metrics, decision ledgers, daily slices, models, training
histories, actions, and artifacts remain in the verified Run.

The Reported Book Risk Explorer is the dedicated existing-holdings view. Core
first verifies the frozen external-reported baseline, any caller-specified
hypothetical books, and every cross-artifact relationship. Studio then shows
the primary-window summary, 63/126/252-bar stability, per-asset signed and
absolute component risk, one-percentage-point reductions toward cash, pairwise
correlations, rolling crowding context, and a same-window scenario table.
For every supplied book the scenario panel exposes volatility rank and delta,
HHI/effective-bet deltas, largest contributor, and primary-window per-asset
weight/risk-share changes. The rank orders only the supplied books; it does not
search or select weights. Studio never substitutes Portfolio model targets,
authenticates a supplied book, optimizes a replacement portfolio, or creates
an order. Its Handoff card terminates at an Agent-owned written answer,
reports the supplied scenario count, and offers the read-only Explorer only as
supporting evidence access; it must not
reuse an iterative template's Session affordance. Use
`aq run book-risk <path> --run ID --points N --json` for the exact read model.

The Price Event Explorer is the dedicated fixed conditional-history view.
Core verifies the immutable Run, derived event authority, exact timing and
return ledger, overlap treatment, reference population, statistics,
uncertainty, and conclusion before the browser receives data. Studio shows the
frozen event clock, sample populations, primary versus unconditional and
matched-reference comparisons, and every event row including exclusions and
right censoring. Its Handoff card terminates at read-only Run review and never
offers a Session, threshold search, event-label inference, Order, or trading
action. The Handoff has no primary CLI task and keeps the Explorer supporting.
Use `aq run event-study <path> --run ID --json` for the exact read model.

The Portfolio Decision Explorer is a bounded projection, not a browser-side
CSV reader. Core first verifies the immutable Portfolio artifacts,
reconciles the complete chronology, and then deterministically samples 180
display points. Performance and exposure are alternate views of the same
verified path. Validation is the selection split; Test audit is visibly
diagnostic and does not enter selection. The latest book is historical
research state, not account holdings or an instruction to trade. Use
`aq run portfolio <path> --run ID --points N --json` for a specific historical
Run or a different bounded point count.

The Portfolio Allocation Explorer is the dedicated fixed construction view.
Core first verifies and rederives the immutable ERC candidate and complete
fixed-weight reference paths. Studio shows validation-only comparison, solver
tolerance and cap-gap counts, latest target/executed/reference weights,
forecast volatility, and a sampled return path. Its Handoff has no primary CLI
task, explicitly asks the Agent to write and return the answer, keeps the
Explorer supporting, and never offers Factor, RL, Session, Order, or trading
actions. Use `aq run allocation <path> --run ID --points N --json` for the
exact read model.

The Strategy Viability panel leads the Portfolio detail with the ordinary
quant-research question: where did the edge stop? Its validation-only chain
shows factor rank IC, gross portfolio Sharpe, annual turnover/base and
break-even cost, and post-cost Sharpe. The supporting strip shows the
0/base/25 bps curve, positive-month breadth, maximum underwater bars,
performance without the best five days, and extra-delay Sharpe delta. Test is
shown separately as visible audit and never changes the stage or research
focus. JavaScript receives the diagnosis from Core and does not infer or tune
it.

The Current Mechanical Decision panel precedes the path/book detail. Its four
stages show current signal-state changes, raw-to-risk-governed gross target,
proposed one-way turnover versus the fixed no-trade band, and whether the
historical book changed. Each asset row shows current percentile/event, every
next transition permitted by its state and Mandate, the percentile-point
buffer to those boundaries, raw/governed target, drifted/executed weight, and
the actual execution reason. The buffer holds peer ranks fixed only to explain
current state; it is not a price target, trigger probability, order, or account
position.

The Position Sizing Anatomy panel then explains the unequal historical
weights. Side cards show configured and funded budget, active breadth,
strength, cap capacity, capped names, and unfunded gross. The asset table
follows score → conviction → trailing volatility → inverse-volatility
strength → uncapped proportional weight → cap/water-fill raw weight →
governed/executed weight. It keeps the simple diagonal risk-budget heuristic
separate from covariance-aware component risk and identifies concentration in
the executed book. Every value comes from the Core projection; JavaScript does
not allocate, optimize, or recommend a position.

The Diversification & Correlation Breakdown panel asks whether those names are
independent risk bets or one crowded trade. Core supplies current effective
risk bets, observed covariance volatility, and a fixed 25% / 50% / 100% ladder
toward perfect position-aligned correlation. Validation and visible test cards
show the ceiling-breach rate at each rung; the asset table separates signed
component contribution, absolute concentration share, and terminal stress-risk
share. JavaScript formats this verified object and never estimates covariance,
assigns scenario probability, selects a Run, or resizes a position.

For request-driven Portfolio evidence, the mandate strip distinguishes the
research universe from assets authorized as positions. It shows direction,
long/cash, short/cash, dollar-neutral, or explicit asset-role family, each
asset's position role, long/short side limits, gross/cap, benchmark, and locked
identity. It also shows the fixed annualized volatility ceiling. The
current book discloses raw target → governed target, forecast volatility →
governed volatility, scale, and status; the validation summary shows how often
the ceiling bound. It separately shows whether the final executed path breached
and how often risk overrode no-trade. The same summary shows the 1% capacity p10 and trade-date
coverage; the book cites the latest rebalance capacity and binding asset.
Those values are an OHLCV dollar-volume envelope, not impact, fill, or live
capital evidence. Context-only assets remain in factor/risk evidence but are
dimmed in the book and always have zero target. These values are verified by
Core; Studio does not estimate covariance or choose risk. The reported cash
field is unused research gross budget, not Broker account balance.

The Mechanical Position Lifecycle panel switches between validation selection
and visible test audit. It shows complete-episode count, win rate, median
holding bars, payoff, intent mismatch, cumulative-contribution MFE/MAE,
per-asset episode contribution/cost, and recent episode rows. Left/right
censored split segments remain visible but never enter complete-episode
win/payoff statistics. Core reconstructs and verifies the rows from the exact
decision ledger before Studio receives them; the browser never invents trades
or compounds an episode as an isolated account return.

The Mechanical Parameter Neighborhood panel switches between validation
context and visible test audit. It shows the fixed five signal profiles across
`0%`, `5%`, and `10%` one-way no-trade bands, outlines the ordinary base cell,
and reports positive-Sharpe/sign-agreement rates, worst local degradation,
turnover, cost, and signal-transition ranges. Color encodes the sign and
magnitude of each cell's net Sharpe; it does not crown a winner. All 15 cells
are predeclared, context-only evidence and cannot change KEEP/REVERT. Core
reconstructs every value from the immutable daily neighborhood artifact before
the browser receives it.

The Session Decision Matrix is also a Core projection. It verifies the
immutable Session/Experiment/Run chain, then compares a bounded set of
baseline, candidate, and leader trials using a fixed family-specific metric
dictionary. Preference arrows make lower-is-better risk and cost fields
explicit. The Selection view excludes test rows from the comparison; the Test
audit view reveals them without changing verdicts, leader choice, or the
validation-only non-dominated set. Context such as hysteresis policy state,
position lifecycle, liquidity capacity, and executed-risk intervention is
display-only, and
failed trials remain visible as
unavailable evidence.

The Session rail, handoff board, trajectory disclosure, and Inspector share
one Project-wide research-family projection. Starting another Session cannot
reset the unique-source count. The browser formats Factor family-wise p-values
or Portfolio PSR/DSR evidence supplied by Core; it does not derive trial
families, calculate corrections, or turn a diagnostic pass into a trading
verdict. Governed RL explains why its dependent fold/seed aggregate has no
valid single-path DSR.

The Factor Evidence Explorer verifies and reconciles the fixed immutable
Factor artifacts before sampling a bounded timeline. Humans may switch between
rank/Pearson IC and fixed-tertile paths, request-bound diagnostic forward
horizons, validation and test audit, and fold/regime/asset/style stability.
The primary horizon is marked explicitly. Those controls format the Core
object; JavaScript never parses CSV, re-bins assets, selects a horizon, or
turns diagnostic evidence into an acceptance gate. The exact headless
`aq run factor` command is copyable from the disclosure footer.

Declaring Runs also show a component panel sourced from the verified Core
projection: validation raw IC, closest train peer and residual IC, fixed-blend
removal delta, test audit, and strongest/redundant summaries. The panel labels
metadata as candidate-declared and says that leave-one-out applies only to the
fixed equal-rank diagnostic blend. It cannot infer pandas column use, alter the
final-factor score, create RL actions, or authorize a position.

The RL Policy Evidence Explorer verifies and reconciles the governed RL
artifacts before showing a claim. It leads with validation value-add versus the
fixed Judge's selected baseline rather than raw Sharpe. Humans may switch among
fold/seed performance, complete training histories, and fixed-sleeve action
allocation, and may reveal test as visibly audit-only evidence. All declared
seeds and their executed-book compliance remain present. New Runs also expose
that the Harness learner was frozen by a train-only blocked stability audit
before validation; legacy Runs label the learner without inventing this
provenance. The headline seed statistic is the maximum within-fold seed
standard deviation; exact-consensus fold count is reconstructed from complete
validation action paths, not score equality. It does not confuse cross-fold
regime differences with seed instability. JavaScript never
selects a seed, substitutes a baseline,
trains a model, or interprets absent state. The exact headless `aq run rl`
command is copyable from the disclosure footer.

New rationale evidence adds a Policy Behavior & Decision Rationale panel. It
shows split-bounded action-run persistence, transitions/retention, one-bar
churn, uncalibrated Q-margin/tie evidence, action-conditioned outcomes,
dominant linear margin drivers, and representative low/high-margin choices.
Every chosen-versus-runner-up contribution is rechecked against frozen model
weights and the immutable action ledger. It is not probability, confidence,
causal importance, or promotion/trading authority; legacy Runs state that the
evidence is unavailable.

The delivery cards and Inspector distinguish optional caller-supplied host
context from authenticated provenance. The current schema can preserve
OpenAlice origin fields, but Studio does not require them for local work. Copy
buttons only write an exact Core-generated CLI string to the local clipboard.
They do not invoke the command or mutate the Project.

When a delegated lane has a current Report and retains its baseline, Studio
shows Core's exact `session complete --report ...` command. The browser only
copies it. After CLI completion, the Session is terminal, active-writer counts
and Program conflicts fall away, and its Report/Dossier evidence remains
immutable and visible. A KEEP lane exposes promotion instead; Studio never
chooses between source adoption and baseline retention.

For a canonical request-driven Research Program, the delivery board is
Project-level even when a Session is selected. It shows current lane Report
coverage, dynamically required blockers, gated/optional omission, and whether
the immutable Dossier is blocked, ready for Agent synthesis, or already
current. Studio loads this state through the same Core Dossier functions used
by CLI. It never composes Reports or authors the synthesis in JavaScript.

The Research Cockpit consumes Core's `progression` projection. It labels the
current Factor focus, Portfolio locked by Factor evidence, and RL locked by the
simple Portfolio baseline without deriving pass/fail from metric signs. A weak
Factor can therefore produce a published one-lane early-stop Dossier while the
downstream workbenches remain read-only. Once both required gates pass, the
deliverable is complete and governed RL is presented as an optional complexity
challenge rather than mandatory program completion.

When the latest Portfolio Report contains frozen leader-decision support,
Studio shows a compact proof strip with the historical decision timestamp,
state-change count, proposed turnover versus the no-trade band, final gate,
cap count, component-risk HHI and largest contributor, and `authority none`.
When present, the next line freezes the validation viability stage, research
focus, and gross/net Sharpe.
This is the Report summary projection, not a browser calculation or a live
market/account state. Full per-asset conditions and weights stay in the
canonical Report/Dossier Markdown and Portfolio explorer. Reports predating
newer snapshots show only the proof they actually froze; legacy Reports show
no invented strip.

For a multi-Study Project, the hero and Inspector use comparable cross-lane
validation readouts instead of promoting the latest Run's absolute headline.
In particular, RL is summarized by value-add versus the Judge-selected
baseline, not raw RL Sharpe. Negative values can be labelled adverse; positive
signs remain descriptive and are never treated as browser-authored acceptance
or promotion decisions. The recommended next lane and command are projected by
Core.

Selecting Factor, Portfolio, or Adaptive Policy evidence also aligns the
Inspector to that lane's latest Session and Report. This prevents a Portfolio
chart from appearing beside RL Session authority while preserving the
Project-level Dossier delivery above it.

For a request-driven Project with no Session, the delivery board shows
`research mandate → dataset → immutable baseline → iterate`. The hero promotes
the latest verified Run's decision metrics over generic object counts, and the
Inspector presents request scope, dataset authority, baseline evidence, and a
copy-only start command before the long research program. Positive values are
not coloured as success without a fixed pass threshold; negative return/risk
evidence is visibly adverse. Once the delegated Session exists, the established
`request → governed evidence → decision-support report` projection replaces
that pre-Session state.

## Machine-readable snapshot

Agents and scripts can inspect the same normalized observation without
starting a server:

```bash
aq studio snapshot . --json
aq schema studio-snapshot --json
aq schema campaign-progress --json
aq schema factor-diagnostics --json
aq schema portfolio-diagnostics --json
aq schema portfolio-mandate --json
aq schema rl-policy-diagnostics --json
aq schema research-program-status --json
aq schema dossier-status --json
aq schema session-completion --json
aq schema session-decision-matrix --json
```

The HTTP projection exposes only:

- `GET /`
- `GET /assets/studio.css`
- `GET /assets/studio.js`
- `GET /api/v1/health`
- `GET /api/v1/snapshot`

There is no arbitrary file, shell, command, mutation, Experiment, or promotion
endpoint. Browser responses use a restrictive Content Security Policy and do
not enable cross-origin access.

## Authority

Studio is not an evaluator. It calls the same Core loaders used by CLI:

- invalid completed evidence is omitted and diagnosed rather than displayed as
  fact;
- Session authority issues remain visible;
- mutable progress cannot create a metric or verdict;
- the browser cannot author analysis or publish a Research Report or Dossier;
- the browser cannot bind, execute, or reinterpret a frozen holdout; it only
  renders Core status and copyable CLI authority;
- no browser interaction changes a Project.

The durable boundary and known gaps are in
[[docs/design/studio-observation-surface]].
