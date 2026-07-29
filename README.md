---
version: 0.8.23
---

# AutoQuant V2

AutoQuant turns quantitative research into a versioned, testable,
Agent-operable engineering workflow.

It is a usable pre-alpha AI-native quantitative workbench, not only a backtest
library, strategy generator, or integration backend. A coding Agent can enter
the filesystem, understand the current question and evidence, take one bounded
action, edit only an authorized research surface, evaluate through fixed
contracts, resume after interruption, and leave durable work for the next
Agent or human reviewer.

The working model is:

```text
long-lived Workspace
└── Project
    ├── question or delegated request
    ├── content-locked data and fixed Studies
    ├── bounded Agent Research Sessions
    ├── factors, portfolios, ML/RL policies, and simulations
    ├── immutable Runs and evidence
    └── Reports, Dossiers, and read-only Studio projections
```

One Workspace may hold multiple self-contained Projects. A Project is one
evolving body of research; a Study locks one evaluation question; a Research
Session is a bounded editable investigation; a Run is an immutable
measurement.

## Current milestone: `0.8.23`

AutoQuant V2 has crossed from an architectural prototype into a usable
research workbench.

Today it can:

- create persistent multi-Project quantitative desks from conversational or
  strict request-driven assignments;
- keep Workspace defaults convenient for disclosed read-only navigation while
  requiring explicit Project identity before state changes in a
  multi-Project desk;
- lock Project-local OHLCV data, market clocks, assumptions, Studies, Judges,
  and Harness identity;
- run cross-sectional or temporal Factor research, mechanical Portfolio
  construction, governed RL, reported-book risk, caller-bounded sizing,
  fixed price-event studies, and Portfolio-native risk-parity allocation;
- use aligned, ragged, continuous, XNYS-session, daily, intraday, and causal
  multi-interval OHLCV surfaces;
- give a coding Agent a recoverable research brief, exact edit boundary,
  bounded next action, deterministic feedback, immutable evidence, and guarded
  promotion;
- expose the same verified state through human CLI, JSON CLI, strict
  Explorers, orientation, Reports/Dossiers, and read-only Studio;
- preserve a rejected hypothesis as useful evidence without manufacturing an
  Order or trading conclusion.

The repository clone is now the Workspace: its checked-in `projects/` is
immediately visible to ordinary filesystem tools, Git preserves durable
research state, and `sample-research-desk` demonstrates the complete
Factor → Portfolio → governed-RL construction with one historical verified
Factor Run. Workbench developers can explicitly redirect effective Project
discovery through an ignored local Workspace configuration without changing
the shipped default. See [current status](docs/STATUS.md) for supported
research routes, verification, maturity, and honest boundaries.

`0.8.9` closes one gap found by an independent Grok Build onboarding trial:
for local Projects, `aq orient` and Studio now surface the explicitly headed
question maintained in `research.md`, its source path, and its provenance
instead of continuing to show a stale create-time description. Delegated
request manifests remain higher authority, and Projects without an explicit
question heading retain the safe manifest-description fallback.

`0.8.10` follows the next independent Grok trial into fixed descriptive
Projects. Orientation now surfaces a locally constructed strict request only
when a current fixed Study dependency binds its exact canonical hash, labels
that authority `project-request`, and still rejects tampered, invalid,
symlinked, or unbound files. The flexible Markdown fallback also accepts the
natural explicit heading `Question`.

`0.8.11` follows the first independent Grok trial through a complete editable
Session. A settled KEEP now routes directly to executable guarded promotion
instead of contradictorily requesting another edit. Newer worktree changes
retain check/evaluation priority, and delegated promotion remains unavailable
until an exact current Report supplies its required `--report` binding. The
accepted candidate's exact passed Check remains visible through that handoff.

`0.8.12` follows another fresh Grok coworker into the exact writable
`operatingRoot`. A Session worktree is now a verified read-only orientation
entry point: its locked marker resolves the owning canonical Project and
Session, while dataset bytes remain canonical and mutation commands keep their
explicit Project paths. Detached, forged, changed, or symlinked worktrees are
rejected.

`0.8.13` follows a fresh Grok coworker through a complete three-lane gating
assignment. Explicit qualified `Question (...)` headings now reach
orientation, Experiment responses state that verdicts are
Session-objective-only, and promotion returns the exact post-mutation Work
Brief. When terminal evidence blocks downstream science, another Session
remains available as optional supporting work instead of an unfinished
primary action.

`0.8.14` follows a fresh Grok coworker through a non-predictive fixed
Allocation assignment. Completed fixed Book Risk, Price Event, and Allocation
Studies now have no false mandatory CLI action: orientation explicitly hands
off to an Agent-owned written answer and keeps the strict Explorer as
supporting read-only evidence. Descriptive agendas also carry the immutable
Run's actual Harness-bound input hash.

`0.8.15` follows a fresh Grok coworker into an editable multi-horizon Factor
assignment. Factor handoffs now disclose the Project's actual base clock,
available completed feature intervals, panel columns, component metadata
fields, and legal roles before source is edited. Bounded preflight validates
static component metadata before running the final factor, and a
baseline-restored Session now follows a verified freeze/external-holdout
agenda instead of simultaneously demanding another in-sample edit.

The installed-wheel retry saw the teaching Project's exact daily base-only
surface before editing, explicitly downgraded the unavailable multi-hour
hypothesis, used one legal `cross-sectional-score` component, passed one
preflight, and spent exactly one Experiment. The three-bar pullback REVERTed
from validation net Sharpe `1.7614` to `-2.0367`; no promotion occurred and
the final Work Brief cleanly froze the restored baseline for external
evidence.

The `0.8.15` repository regression passed all 304 tests, its documentation
graph resolved all 1,064 checked links, and the final source/wheel installation
reproduced the same candidate contract across CLI and Studio.

`0.8.16` follows the next fresh Grok coworker through a real OpenAlice-style
multi-interval intake and one complete delegated REVERT handoff. A restored
leader with trial history now enters explicit review instead of demanding
another edit; delegated Report publication and Session inspection remain
optional supporting actions, then an exact baseline-retaining Report makes
completion primary. The Work Brief separately preserves the latest immutable
Experiment, candidate Run, verdict, and preceding Check after restore and
Session completion.

Repository regression passes all 306 tests, the documentation graph resolves
all 1,069 checked links, and a fresh installed-wheel replay reproduces the
trial-review, Report, completion, and immutable evidence handoff across CLI
and Studio.

`0.8.17` follows a fresh Grok coworker from nine raw Yahoo OHLCV files into
one delegated SPY-relative Factor investigation. Factor preflight now
exercises up to two position-capable assets together with every fixed context
and benchmark asset, so a reference-dependent candidate follows the same
input contract during quick Check and formal evaluation without inventing a
fallback market. KEEP promotion is also explicit across help, JSON,
orientation, and human output as one terminal Session close;
baseline-retaining completion is the mutually exclusive alternative.

The installed retry used a strictly SPY-required implementation with no proxy
fallback, passed its first Check over the disclosed bounded sample plus SPY,
spent one Experiment, published one Report, promoted once, and stopped at the
terminal `promoted` state. Repository regression passes all 307 tests and the
documentation graph resolves all 1,074 checked links.

`0.8.18` follows that same worker's remaining intake friction. A required
`provider.retrievedAt` may now be a known timezone-aware ISO-8601 timestamp or
explicit JSON `null` when caller-supplied bytes do not preserve the original
retrieval time. The public schema tells Agents not to invent Project,
packaging, file, or current-clock precision, and the exact claim remains
content-locked through the Project snapshot and Studio.

A fresh installed Grok worker then used that contract on nine unchanged raw
Yahoo CSVs, created a fixed eight-holding Book Risk Project, preserved
`retrievedAt: null`, executed exactly one Run, started no Session, and returned
strict descriptive evidence. Its retry also hardened manifest-file and
V1/V4/V5 routing guidance. The worker correctly refused to fabricate the
requested maximum drawdown when current Book Risk evidence lacked it; that
method gap is preserved in
[`plans/book-risk-drawdown-evidence.md`](plans/book-risk-drawdown-evidence.md).
Repository regression passes all 309 tests and the documentation graph
resolves all 1,085 checked links.

`0.8.19` closes that preserved method gap without turning Book Risk into a
portfolio backtester. Every new fixed Book Risk Run now applies the supplied
weights to the same immutable close-to-close return panel, publishes a full
primary-window NAV/drawdown path, and reports signed maximum drawdown plus
observed peak, trough, and recovery timestamps. The strict Explorer
independently rebuilds every row and all 63/126/252-window drawdowns; Run
metrics, CLI, Studio, and artifacts reconcile. Older Book Risk Runs remain
readable and explicitly mark this newer evidence unavailable.

A fresh installed Grok worker repeated the unchanged eight-holding assignment,
preserved `retrievedAt: null`, used one fixed Run and no Session, and answered
the formerly unsupported drawdown directly from immutable evidence:
`-0.183079`, from `2025-10-29` to `2026-03-30`, recovered `2026-04-27`. It used
no replacement pandas calculation and recorded no remaining Workbench blocker.
Final repository regression passes all 311 tests in 794.604 seconds, and the
documentation graph resolves all 1,085 checked links.

`0.8.20` follows a fresh Grok coworker through a gated Factor → Portfolio
assignment. The worker improved the Session objective, correctly distinguished
KEEP from scientific qualification, and stopped before Portfolio and RL when
the fixed gate remained blocked. Its only concrete framework failure was
Report evidence-reference discovery: the public schema did not explain the
exact Run-relative artifact path or the required null artifact for Experiment
and Campaign evidence.

The executable `report-analysis` schema now encodes those kind-specific rules
and supplies complete examples; CLI help, capabilities, orientation, and
documentation repeat the same contract. A second isolated installed-wheel
worker inspected only public discovery, published its Report exactly once,
succeeded on that first attempt, and again stopped at the scientific gate
without manufacturing downstream evidence. Final repository regression passes
all 311 tests in 796.165 seconds, and the documentation graph resolves all
1,089 checked links.

`0.8.21` follows a fresh Grok coworker through a source Dossier and caller-fixed
141-session external period. The worker completed the source Factor lifecycle
correctly, then discovered that a frozen Factor-only target inherited the
ordinary three-lane research desk's 240-row and all-diagnostic-horizon gates.
It stopped without padding history or inventing holdout evidence.

AutoQuant now has an atomic, lane-aware `holdout create-target` path. It reuses
the current Dossier's canonical request, creates and freezes the later Project
as one transaction, preserves the ordinary research intake gates, and applies
120/180/240-row Factor/Portfolio/RL target floors. A holdout-authorized Run
records `external-temporal-audit` in its execution identity; a sparse secondary
diagnostic remains visible as insufficient while the primary objective must
retain at least 20 fixed validation observations.

A second fresh installed-wheel Grok worker then rebuilt the unchanged source
research from scratch, discovered the new public path, and completed the
141-session target in one holdout invocation. The exact frozen Factor weakened
from source validation mean IC `+0.101253` to later-period `-0.284679`
(`-0.385932` delta). Both Projects validated, Studio reported no diagnostics,
and no Portfolio, RL, Session, Order, or trading authority was manufactured.
Final repository regression passes all 312 tests in 799.389 seconds, and the
documentation graph resolves all 1,094 checked links.

`0.8.22` follows a fresh Grok coworker through two unrelated fixed Studies in
one persistent Workspace. Both immutable evidence chains remained valid and
Studio kept them separate, but Workspace-level orientation silently treated
the first Project as the current default even after conversational focus moved
to the second. That was adequate for inspection and unsafe as state-change
authority.

Read-only orientation now discloses the effective Workspace, default and
selected Project, selection method, Project count, and every available id.
Once a Workspace contains multiple Projects, Project-local commands advertised
as `creates-artifact` or `mutates-project` fail before mutation unless their
Project is explicit. Direct Project paths, single-Project Workspaces, and
Workspace-wide Studio remain unchanged.

The isolated installed-wheel retry discovered this contract from public
orientation, left the first Project as default, explicitly selected both
fixed Runs, and completed the unchanged book-risk plus price-event assignment.
Independent checks found one valid Run and zero Sessions per Project,
byte-identical isolated data snapshots, and a valid two-Project Studio with no
diagnostics. A deliberate omitted-Project Run was rejected before either Run
count changed.

Repository regression passes all 312 tests in 803.410 seconds, the
documentation graph resolves all 1,099 checked links, and a fresh Python 3.11
environment installs the built `0.8.22` wheel for version, capability,
Workspace, Project, orientation, and validation smoke.

`0.8.23` follows a fresh Grok coworker into a mixed equity/fund Allocation
assignment. V1–V4 OHLCV packages may now preserve an optional complete
per-asset class vector; Core rejects partial vectors and wrong summaries,
freezes the exact classes into the Project snapshot, and verifies them against
the Research Request on every load. Legacy homogeneous packages remain valid.

A fixed Allocation reference may also contain requested `context-only` legs.
Those assets participate in the separately funded, drifted, costed reference
portfolio without entering ERC candidate targets, caps, executed weights, or
risk contributions. This keeps economic metadata and candidate authority
truthful without adding another role or special Project type.

The installed-wheel retry completed the unchanged AAPL/NVDA/GLD/TLT ERC
assignment against a 60/40 SPY/TLT reference in one Project, one fixed Run,
and zero Sessions. It preserved all five classes, kept SPY out of candidate
weights and risk contributions, and surfaced one final read-model friction:
the compact Study summary `mixed` hid the complete class map. Study inspection,
Allocation Explorer, and Studio now project the verified Run-bound per-symbol
classes directly.

A second fresh worker installed the final wheel and repeated the complete
assignment after that read-model fix. Study inspection and Explorer agreed on
the exact five-symbol map, the Run succeeded in about 0.8 seconds, strict
verification reconciled every path, and Studio reported no diagnostics.
Repository regression passes all 315 tests in 805.092 seconds and the
documentation graph resolves all 1,104 checked links.

## Standalone or an OpenAlice desk

AutoQuant has one product shape in both environments:

```text
standalone clone                    OpenAlice Trading Harness
└── AutoQuant Workspace             └── AutoQuant Workspace desk
    └── Quant Agent                     └── Quant coworker
        └── Projects                        └── Projects
```

Standalone, a human or Agent clones AutoQuant and operates it directly.
Inside OpenAlice, the same workbench can be materialized as a specialized
Workspace desk. An Agent at another desk can delegate a quantitative task to a
coworker at the AutoQuant desk and receive a report when the work is useful.
There is no separate OpenAlice edition and no private service API defining the
research lifecycle.

AutoQuant owns quantitative research and historical simulation. An optional
host owns cross-Workspace communication and authenticated provenance. Brokers,
live accounts, approvals, and real order submission remain outside AutoQuant;
in OpenAlice that authority belongs to UTA. AutoQuant may model target
portfolios, orders, and TPSL when required for valid research without claiming
live-trading authority.

Existing-book questions use the separate `ohlcv-book-risk-lab`. It preserves
one caller-supplied baseline weight snapshot and may compare up to eight
caller-specified complete hypothetical books under the same historical
covariance windows. It returns component-risk, common-movement, standardized
reduction-sensitivity, fixed static-weight drawdown, and explicit
scenario-delta evidence without pretending that any snapshot is authenticated
account truth, reconstructed broker equity, or an optimized target.
See [reported-position Book Risk](docs/design/reported-position-book-risk.md).

Price-defined conditional-history questions use
`ohlcv-event-study-lab`. Its first fixed contract preserves a downside opening
gap, exact delayed close entry and holding clock, every qualifying or censored
event, overlap treatment, unconditional same-asset history, and matched
reference-asset outcomes. It has no candidate Session, does not pretend an
OHLCV gap proves an earnings/news event, and returns no Order or live-trading
authority. See [OHLCV Price Event Study](docs/design/ohlcv-price-event-study.md).

Non-predictive strategic-allocation questions use
`ohlcv-allocation-lab`. Its narrow V1 contract constructs a long-only
equal-risk-contribution book from trailing completed returns, enforces
caller-owned caps and a scale-down-only volatility ceiling, and compares it
with a separately drifted and costed fixed-weight reference on the same
decision schedule. It has no Factor, RL, editable candidate, Session, Order, or
trading authority. See
[Portfolio-native Allocation Lab](docs/design/portfolio-native-allocation-lab.md).

See the canonical
[Agent-native workbench model](docs/design/agent-native-quant-workbench.md)
and [architecture](docs/ARCHITECTURE.md).

## Quick start

AutoQuant requires Python 3.11 and
[uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:TraderAlice/Auto-Quant-V2.git
cd Auto-Quant-V2
uv sync
uv run aq --version
uv run aq capabilities --json
uv run aq project list .
uv run aq validate .
uv run aq orient . --json
uv run aq studio serve .

# Start a genuinely new assignment as a sibling Project.
uv run aq project create . research-desk \
  --name "Research Desk" \
  --description "Coordinate factor, portfolio, and RL evidence" \
  --template ohlcv-research-desk \
  --json
# A Quant Agent now completes researchBriefPath and records any real
# framework gap at frameworkNeedsPath.
uv run aq project program . --project research-desk
uv run aq orient . --project research-desk --json
```

The checked-in `autoquant-workspace.json` selects the repository's internal
`projects/` and `sample-research-desk`. The sample is an ordinary Project, not
special runtime state. Its first Factor Run truthfully records the clean
`0.8.7` Harness that created it; it is retained so Studio has inspectable
evidence on first launch.

Framework contributors with a separate real-research collection may add the
Git-ignored `autoquant-workspace.local.json`. It is a complete strict Workspace
manifest and may point `projects_directory` outside the repository:

```json
{
  "default_project": "my-current-research",
  "name": "AutoQuant Development Desk",
  "projects_directory": "../quant-workspace/projects",
  "schema_version": 1
}
```

CLI and Studio disclose the effective Projects directory and whether this
local override is active. Invalid overrides fail explicitly. A normal clone
has no override and remains self-contained.

The `0.8.8` release was closed with 286 passing tests, 1,029 checked
documentation links, source/wheel and installed-wheel smoke, and a second
no-hardlink clean-clone replay of the complete root Workspace.

The `0.8.9` release was closed with 289 passing tests, 1,033 checked
documentation links, an independent pre-Run Grok Build retry, and a fresh
installed-wheel Workspace/Project/orientation/Factor-Run smoke.

The `0.8.10` release was closed with 293 passing tests, 1,038 checked
documentation links, an independent zero-file-inspection Grok Build Event
Study retry, and a fresh installed-wheel Workspace/Project/orientation/Event
Run smoke whose Harness recorded `0.8.10` and `dirty: false`.

The `0.8.11` release was closed with 296 passing tests, 1,048 checked
documentation links, two independent editable-Session Grok Build trials, and
a fresh installed-wheel Python 3.11 baseline → Check → KEEP → guarded
promotion → Studio smoke whose Harness recorded `0.8.11`,
`commit: unavailable`, and `dirty: false`.

The `0.8.12` release was closed with 299 passing tests, 1,048 checked
documentation links, one fresh Grok reproduction under `0.8.11`, one fresh
installed-wheel Grok retry under `0.8.12`, adversarial owner-marker coverage,
and a final Python 3.11 wheel baseline → worktree re-entry → Check → KEEP →
promotion → post-orient/Studio smoke whose Harness recorded `0.8.12`,
`commit: unavailable`, and `dirty: false`.

The `0.8.13` release was closed with 301 passing tests, 1,052 checked
documentation links, one fresh installed-wheel Grok three-lane gating task,
and a final Python 3.11 wheel inspection smoke. The coworker recovered its
qualified research question, re-entered its Session worktree, completed one
Check and one KEEP, promoted through the guarded path, then correctly stopped
at `scientific-gate-blocked` with no Portfolio/RL Run or second Factor Session.
The final wheel also repeated Session-only verdict authority on immutable
Experiment inspection.

`project create` is the normal construction entry point. It creates
`research.md`, `framework-needs.md`, the Project manifest, and the Project-local
strategy, factor, model, Judge, Study, Session, data, Run, and cache surfaces.
Before quantitative work, the Agent rewrites `research.md` in English, asks the
delegating Agent or user about every material ambiguity, and continues only
when the question is bounded and testable. Real reusable Workbench gaps go in
`framework-needs.md`, not the research brief. The caller may converse in any
language.

Factor candidates receive the complete Study universe as one ordinary
long-form pandas DataFrame:

```python
def compute_factor(panel: pd.DataFrame) -> pd.Series:
    within_asset = panel.groupby("asset")["close"].pct_change(20)
    return within_asset.groupby(panel["timestamp"]).rank(pct=True)
```

This supports causal rolling features and same-timestamp cross-asset context
without a factor DSL. Factor, Portfolio, governed RL, and preflight use the
same panel runtime and whole-panel timestamp-prefix causality audit.

`aq` emits compact human output by default and a versioned machine envelope
under `--json`. See [CLI.md](docs/CLI.md) and
[PROJECT_FORMAT.md](docs/PROJECT_FORMAT.md).

CSV intake works in the base environment. Parquet and Feather are optional:

```bash
uv sync --extra columnar
```

## Start from a real research request

A caller may begin with an ordinary conversational assignment. The Quant Agent
first turns it into the Project's English Markdown research brief; strict JSON
does not replace that clarification step.

Once intent is understood and a matching OHLCV package is available, the Agent
can derive the strict request and use the atomic intake fast path below. Intake
validates and normalizes the complete panel, checks its market-clock and
interval contract, confines all paths, copies the data into the Project, and
locks every source byte before creating Studies.

```bash
uv run aq schema research-request --json
uv run aq schema ohlcv-dataset-package --json
uv run aq project intake . us-leadership \
  --request research-request.json \
  --dataset /path/to/dataset.json \
  --json
```

The request may lock:

- long-only, short-only, two-sided, or context-only duties per asset;
- gross, per-asset, volatility, cost, no-trade, and reference-NAV assumptions;
- cash or one named dataset asset as the evaluation benchmark;
- primary and diagnostic forward horizons;
- Portfolio/RL decision cadence and dataset/session clock anchor;
- one reported or hypothetical funded baseline plus optional caller-authored
  complete hypothetical books for a fixed, non-authenticated Book Risk audit.
- one fixed adjusted-OHLCV opening-gap event, delayed return clock, matched
  reference asset, overlap policy, and minimum useful sample count.
- one fixed equal-risk-contribution construction and complete funded
  fixed-weight reference portfolio.

These are immutable research assumptions. They never grant live position or
execution authority.

## Research loop

A Session creates a disposable worktree with an exact editable closure. A fast
candidate Check can catch structural errors without creating evidence.
The fixed Judge alone publishes metrics and a KEEP, REVERT, or CRASH verdict.
Promotion remains a separate guarded operation.

```bash
uv run aq session start . \
  --study factor-quality \
  --request research-request.json \
  --json

uv run aq session check . \
  --session session-... \
  --json

uv run aq experiment evaluate . \
  --session session-... \
  --hypothesis "Add volatility normalization" \
  --json

uv run aq session promote . \
  --session session-... \
  --json
```

Any explicit external coding-Agent command can drive the same bounded loop.
AutoQuant supplies the verified brief, protects fixed source, and retains every
turn and evaluation as evidence:

```bash
uv run aq research run . \
  --session session-... \
  --agent-command 'my-coding-agent --autoquant-research' \
  --max-turns 5 \
  --max-wall-seconds 900 \
  --turn-timeout-seconds 300 \
  --json
```

## Evidence and deliverables

Factor Runs publish purge-aware IC, decay, quantile, style, regime, and
component evidence. Portfolio Runs apply one fixed causal signal-to-position
policy with caps, side limits, covariance risk scaling, drift/no-trade
execution, costs, capacity, lifecycle, and robustness diagnostics. Governed RL
may select only among fixed factor sleeves built through that same Portfolio
Mandate; it cannot rewrite the action, reward, risk, or execution contracts.
Fixed Price Event Runs instead publish a complete conditional-event ledger,
reference distributions, descriptive uncertainty, and an evidence-status
conclusion without entering the candidate-selection lifecycle.

Agents may publish lane Reports, and the canonical Factor → Portfolio →
optional RL program can compose them into one immutable Project Dossier:

```bash
uv run aq report publish . \
  --session session-... \
  --analysis report-analysis.json \
  --json

uv run aq dossier status . --json
uv run aq dossier publish . \
  --analysis dossier-analysis.json \
  --json
```

A Report or Dossier is a durable evidence-bound Project artifact, not a
mandatory RPC response. It may be reviewed locally, handed to another Agent,
or delivered through a host. When OpenAlice is the host, it may publish the
exact Markdown through Inbox and attach authenticated collaboration
provenance; AutoQuant deliberately does not impersonate that authority.

## Studio

Studio is a lightweight read-only view over the same verified Core loaders
used by the CLI:

```bash
uv run aq studio snapshot . --json
uv run aq studio serve .
```

It shows current Projects, requests, Agent work briefs, Sessions, experiments,
lane progression, Portfolio Mandates, mechanical position evidence, governed
RL evidence, Reports, Dossiers, and exact copyable next commands.

## Repository structure

```text
Auto-Quant/
├── autoquant/                 # V2 Core, CLI, templates, and Studio
├── docs/                      # canonical contracts and design invariants
├── plans/                     # bounded engineering execution records
├── scripts/                   # repository checks
├── tests/                     # deterministic bounded verification
├── AGENTS.md                  # contributor and Agent routing guide
├── PLANS.md                   # active/completed plan index
└── pyproject.toml             # package and runtime dependencies
```

The repository-root Auto-Quant Classic/Freqtrade arena is retired. Research
data belongs inside caller-created Projects; Git history is the archive for
the removed Classic strategies, notebooks, and experiment snapshots. See
[retired-flat-freqtrade-harness.md](docs/design/retired-flat-freqtrade-harness.md).

## Development

Read [AGENTS.md](AGENTS.md) and [PLANS.md](PLANS.md) before non-trivial
changes. Do not launch an unbounded autonomous loop or a long multi-year
backtest as routine validation.

The current release proof and tested capability boundary are recorded in
[docs/STATUS.md](docs/STATUS.md); detailed real-request outcomes live in
[docs/trading-request-field-trials.md](docs/trading-request-field-trials.md).

```bash
uv run python scripts/check_doc_links.py
uv run python -m unittest discover -s tests -v
uv build
```

## License

MIT.
