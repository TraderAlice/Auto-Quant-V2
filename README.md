---
version: 0.9.6
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

## Current release: `v0.9.6`

AutoQuant V2 has crossed from an architectural prototype into a usable
research workbench.

`v0.9.6` is the current AutoQuant release. `v0.8.31` remains the Harness
currently consumed by OpenAlice until the host deliberately selects the newer
tag; this is version provenance, not an automatic Workspace-migration promise.
The minor-version boundary marks the next phase: improve the real delegated-
research loop from OpenAlice request through AutoQuant evidence handoff without
weakening standalone Workspace operation or prematurely freezing a
host-specific API. Bounded follow-up work defaults to patch releases such as
`v0.9.1`, `v0.9.2`, `v0.9.3`, and onward.

`v0.9.6` makes market-data work demand-led instead of inventory-led. A fresh
installed `0.9.5` coworker began with a fixed CATL/CSI 300 ETF Event question
and zero staged OHLCV, independently attempted Yahoo, Eastmoney, and Tencent,
selected truthful split-adjusted data, and completed one negative fixed Run.
The field trial then promoted only observed friction: price-only Event Studies
retain valid zero-volume sessions and may keep every asset `context-only`;
mainland raw routes preserve listed-fund classes; cross-adjustment comparison
has an explicit coverage-only mode; and failed provider commands leave a
standard local route audit. Existing data still never narrows a caller's
question, and duplicate task-coherent Project snapshots remain acceptable.
OpenAlice is intentionally unchanged at `0.8.31`. See
[[plans/demand-led-market-data-field-trial]] and
[[docs/design/agent-native-market-data-acquisition]].

The pre-final source audit passed all 371 tests in 923.813 seconds and all
1,276 documentation links. The installed-wheel coworker replay and clean-clone
release checks are recorded in the completed plan.

### `v0.9.5`

`v0.9.5` removes two forms of avoidable work observed in a clean delegated
trial. `aq project templates` now publishes the fit, anti-fit, lane set, and
composition rule for every construction, so coordinated Factor-to-Portfolio
or Factor-to-RL work selects `ohlcv-research-desk` before intake rather than
discovering that requirement after a standalone baseline. A verified current
Run can now receive a Project-owned immutable Research Report directly through
`aq report publish --study ... --run ...`; no empty Session, Check, Experiment,
completion, or promotion history is manufactured. Real editable Sessions keep
their own Reports and take precedence once started. Research Program, Dossier,
orientation, CLI, and Studio consume the same explicit `run | session` anchor.
See [[docs/design/run-bound-research-reports]] and
[[plans/agent-route-and-run-bound-reports]].

A fresh installed-wheel Grok 4.5 worker compared public routes, selected the
Research Desk on its first attempt, executed one Factor and one Portfolio Run,
published two direct Run Reports and one Dossier, and finished with zero
Sessions, Checks, or Experiments. The `v0.9.5` release audit passed all 368
tests in 929.173 seconds and all 1,271 documentation links, plus JavaScript
syntax, build, fresh Python 3.11 installation, capability/template discovery,
and clean-clone checks.

### `v0.9.4`

`v0.9.4` makes normalized signal-intent attribution obey the same fixed
prediction-mode contract as actual Portfolio construction. An explicit
two-asset relative-value signal now becomes one capped complementary pair:
each side is bounded by the lesser side budget and both per-leg caps, and
unused gross capacity remains Cash. Ordinary cross-sectional dollar-neutral
research keeps its full-side breadth rule. The strict Explorer discloses both
evaluation mode and intent construction and proves exact relative-pair parity
with the pre-governor target; historical Run bytes and Portfolio performance
remain unchanged. See [[docs/design/signal-policy-and-attribution]] and
[[plans/relative-value-monetization-intent-parity]].

Two isolated Grok 4.5 trials exercised opposite scientific outcomes using
only the installed `0.9.4` wheel. A deliberately rank-invariant score-rescale
candidate passed Check but correctly received `REVERT`; its additional trial
caused the adjusted Factor gate to block Portfolio, and the worker returned no
weights. A second frozen-factor reproduction passed Factor-to-Portfolio and
reported NVDA `-0.30`, QQQ `+0.30`, and zero context weights. Its normalized
intent was active on all 75 raw-target validation dates, used
`capped-complementary-relative-value-pair`, reconciled to the pre-governor pair
with maximum error `0.0`, and correctly identified trading cost rather than
signal intent as the largest adverse stage.

The `v0.9.4` release audit passed all 361 unit tests in 1066.637 seconds and
all 1,253 documentation links. Studio JavaScript syntax and the locked package
environment also passed; source/wheel, fresh installed-wheel capability, and
clean-clone smoke are recorded in the completed release plan.

### `v0.9.3`

`v0.9.3` makes temporal Factor-to-target translation locally auditable without
turning robustness analysis into a parameter search. Single-asset timing and
two-asset relative-value Portfolio Runs retain the fixed 60-observation causal
percentile with a 20-observation minimum, then publish predeclared 40/60/120
paths for validation-only state and target agreement. Visible test remains
audit-only; no alternate window enters selection or becomes a recommendation.
The strict Portfolio Explorer reconstructs every path from the immutable
Factor decision ledger and joins the diagnosis to the existing
factor-intent, sizing/caps, risk-governor, execution/no-trade, and cost chain.
Cross-sectional Runs explicitly report the temporal-window stress as not
applicable. See [[docs/design/target-translation-robustness]].

A fresh isolated Grok 4.5 worker used only the installed `0.9.3` wheel to
complete a fixed NVDA/QQQ relative-value assignment with AAPL/MSFT/SPY as
context-only assets. It independently reached the Portfolio gate, kept all
context targets at zero, treated 60 as the immutable base rather than choosing
the best profile, and reported validation-only `stable-target-path` from a
minimum active-state agreement of `0.8214` and maximum mean absolute target
delta of `0.04369`. All three current profiles agreed on NVDA `-0.30` and QQQ
`+0.30`. The worker also preserved the separate monetization-loss diagnosis
and no-trading authority.

The `v0.9.3` release audit passed all 361 unit tests in 1009.615 seconds and
all 1,246 documentation links. It also passed Studio JavaScript syntax, source
and wheel builds, fresh Python 3.11 installed-wheel version and all-50-
capability smoke, and a no-hardlink clean clone that selected and validated
the repository sample through CLI and Studio.

`v0.9.2` makes the Factor-to-target-weight boundary prediction-mode aware.
Cross-sectional research ranks only its true prediction population;
single-asset timing uses a causal 60-observation own-history percentile with
20 observations required; and two-asset relative value uses the caller-ordered
factor spread with exact complementary leg scores. Context-only assets remain
available to editable factor construction but receive no fixed decision score
or target weight. Portfolio and governed RL now bind the same Factor claim,
prediction population, and immutable translation contract, while strict
Explorers recompute and reject rehashed score or role tampering. This remains
target-weight research with no Order, Broker, TPSL, account, or trading
authority. See
[[docs/design/prediction-mode-target-weight-translation]].

A fresh isolated Grok 4.5 worker then replayed a supplied BTC timing factor
over 47,040 fixed hourly rows using only the installed `0.9.2` wheel. With zero
retries or Core failures it completed Factor qualification, Report/promotion,
one fixed Portfolio Run, strict Explorers, final orientation, and Studio. The
corrected Explorer showed BTC-only causal-history scoring and unavailable
context scores; validation net Sharpe was `-3.2244` versus about `-0.9312`
under the obsolete context-ranked path, while the latest historical model
target remained BTC `0` / Cash `1`. The negative monetization result is
preserved rather than hidden behind the positive predictive Factor gate.

The `v0.9.2` release audit passed all 360 unit tests in 995.694 seconds and all
1,227 documentation links. The release also passed Studio syntax, source and
wheel builds, fresh Python 3.11 installed-wheel version/capability smoke, and a
no-hardlink clean-clone repository-root validation and Studio snapshot.

`v0.9.1` makes explicit Factor-component evidence useful in every supported
prediction mode. Cross-sectional Runs retain per-date rank IC, while
single-asset and two-asset relative-value Runs now expose within-split temporal
rank-correlation contribution, train-selected nearest-peer residual evidence,
fixed diagnostic-blend leave-one-out, pairwise redundancy, and conditional
context states through the same immutable RunResult, artifact, Explorer,
agenda, CLI, Studio, Report, and Dossier contract. The diagnostics remain
research-prioritization evidence and never enter Factor promotion or grant
Portfolio/RL/trading authority.

A fresh Grok 4.5 worker used the installed candidate to acquire 13,800 Binance
Spot 1h bars per asset, author a five-component LINK-versus-ETH multi-interval
Factor, publish one truthful negative-evidence Report, and stop without an
unnecessary Experiment. Its one reusable friction was repaired: an explicit
two-sided relative-value pair now remains dollar-neutral and zero-net even
when the caller also names context-only assets. A second fresh worker verified
that exact three-role intake without omitting context or editing the mandate.

Six isolated Grok 4.5 assignment families now cover mainland-China and Taiwan
source boundaries, a Korean price event, a reported semiconductor book,
causal Crypto multi-interval Factor research, and US-sector governed RL.
Accepted workers returned useful negative or bounded evidence without
manufacturing trading authority. Repeated Agent friction produced narrowly
tested `0.9.0` repairs; the synthesis and remaining honest limits are recorded
in [[docs/openalice-real-delegation-synthesis]].

The `v0.9.1` release audit passed all 356 unit tests and all 1,214
documentation links. Lock validation, sdist/wheel builds, a fresh Python 3.11
wheel install, all 50 public CLI capabilities, all 16 Skills in both Agent
discovery roots, and the complete no-hardlink clean-clone repository-root
workflow also passed. The clone selected `sample-research-desk` from the
committed Workspace manifest and strictly projected its current
`candidate-declared-components-v3` Run through CLI and Studio.

`0.8.31` made historical market-data
acquisition an Agent-native, versioned Skill bundle rather than a universal
Core downloader. A small router now sends a coding Agent to market-specific
semantics, narrow provider procedures, exact raw-response audits, truthful
V1–V5 packaging, and strict Project intake. The first field-trial matrix
covers named U.S., mainland-China, Japanese, South Korean, Taiwanese,
Vietnamese, and Euronext Paris equities with at least two independently
executable routes per market; unlike raw and adjusted contracts remain
distinct.

Two isolated installed-wheel coworkers exercised the complete first-batch
matrix and created valid U.S. and Korean handoff Projects. The final Python
3.11 wheel smoke materialized all 16 Skills into both discovery roots and
passed orientation, validation, Project listing, and Studio projection. Full
regression passes 346 tests in 1124.263 seconds and all 1,193 documentation
links resolve.

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
- materialize 16 canonical acquisition/package Skills into both Agent
  discovery roots, route by venue and data semantics, retain provider bytes
  and hashes, compare same-semantics sources, and bind accepted OHLCV through
  the existing content-locked intake contract.

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

`0.8.25` follows the next concrete Agent-operability friction. A fresh Grok
coworker naturally staged caller inputs below its intended `./workspace`
before initialization, then had to move them after the empty-target guard
failed. `aq workspace init --adopt-existing` now makes that ownership choice
explicit: it preserves surrounding caller/host files, creates only the
Workspace manifest and a new empty `projects/`, and refuses any existing
configuration or Projects entry. Default initialization remains strict and
its failure names both safe recovery routes.

The isolated installed-wheel Grok retry discovered adoption through public
help/capabilities, preserved all three pre-staged input hashes, and completed a
fixed NVDA downside-gap Event Study in one Project, one Run, and zero Sessions.
Strict Event Explorer and Studio remained valid; no staging relocation or
rewrite occurred. Repository regression passes all 321 tests in 826.969
seconds and the documentation graph resolves all 1,113 checked links.

`0.8.26` follows that same worker into dataset packaging. Dataset asset paths
remain strictly confined, portable, and relative to the package manifest
directory, but public schema, capability JSON, CLI help, and Agent guidance
now say explicitly that the manifest may sit at staged files' common ancestor.
An Agent can therefore intake `staging/raw-ohlcv/AAPL.csv` through
`staging/dataset-package.json` without creating a second raw staging copy.
The Project-local normalized content-locked snapshot remains intentional.

The first isolated `0.8.26` worker naturally discovered that layout and exposed
one adjacent first-attempt retry: Research Request `source.artifactPath` and
`artifactRevision` were not visibly paired. The final schema describes and
enforces the existing both-values-or-both-null contract, while CLI and
capabilities repeat it. A second fresh final-wheel Grok completed the unchanged
NVDA/SPY Event assignment on its first intake with one Project, one Run, zero
Sessions, exact source hashes, no intermediate raw copy, and no CLI failure.
Strict Explorer, validation, orientation, and Studio all reconciled.
Repository regression passes all 322 tests in 924.699 seconds and the
documentation graph resolves all 1,117 checked links.

`0.8.27` follows a fresh editable Factor coworker through primary-20
price-trend plus dollar-volume research. Callers may now list only additional
diagnostic horizons: Core canonically adds the separately declared primary,
retains the five-horizon limit, and exposes that rule in public schema and
Agent guidance. A validated current baseline-retaining completion now has no
false `SESSION REQUIRED` action, projects its exact immutable Report, and
keeps another Session only as an optional explicit follow-up. Report-bound
promotion now has the same terminal navigation without being mislabeled as
scientific qualification. Public Report schema also carries one complete
copyable analysis example. Core still does not infer a trial budget from prose.
Repository regression passes all 325 tests in 959.906 seconds and the
documentation graph resolves all 1,129 checked links.

`0.8.28` makes the first editable Factor Session describe its scientific
surface truthfully. Intake now seeds the baseline from the verified interval
surface: daily and observed-only inputs declare only base-clock momentum,
while actual 3h/12h/1d inputs enable only their available components. Selection
integrity separately reports first candidate-audit visibility and later
post-audit source iteration. The external-holdout boundary remains
conservative, but Core no longer claims that visible test evidence actually
guided an edit because that human/Agent behavior is not observable. Historical
Runs and Reports retain their original bytes and remain readable.

A fresh isolated installed-wheel Grok replay completed the unchanged daily
price-trend plus dollar-volume assignment with no CLI retry. Its baseline
declared only base-clock momentum, its two-component candidate passed Check
but worsened validation IC and REVERTed, and its immutable Report/completion
closed a useful negative result. Selection integrity reported one first
candidate audit, zero post-audit iterations, unobservable actual guidance, and
the unchanged external-holdout requirement. One adjacent optional-agenda
presentation issue is indexed separately rather than folded into this release.
Repository regression passes all 326 tests in 868.625 seconds and the
documentation graph resolves all 1,143 checked links.

`0.8.29` resolves that presentation issue after a second materially different
fresh worker reproduced it. An evidence-derived agenda now carries one strict
`moveRole`: `current-research-guidance`, `optional-follow-up`, or
`unavailable`. After an immutable trial is awaiting review or a completed
research lane has no required primary action, CLI JSON, human orientation, and
Studio retain useful hypotheses but label them as optional follow-up. Core
still does not parse experiment budgets from Markdown, suppress evidence, or
authorize automatic execution, promotion, or trading.

A different fresh installed-wheel Grok replay then repeated the originating
price/volume assignment. Its one candidate improved validation mean IC from
`-0.119921` to `-0.097214` and therefore earned Session KEEP, while fixed
diagnosis remained `raw-predictive-edge-absent`. It correctly published,
promoted the relatively better source, returned a negative scientific answer,
and stopped at `required-research-complete` with
`moveRole: optional-follow-up`; no second Session, Portfolio, RL, Order, or
trading claim followed. Full regression passes 326 tests in 851.125 seconds
and all 1,162 documentation links resolve.

`0.8.30` closes two public-contract contradictions exposed by the fresh
governed-RL worker. Caller-supplied `fixed-weights` now remain one distinct,
complete, content-locked benchmark through the Portfolio Mandate and both
Portfolio and RL Judges. Fast RL preflight now supplies every raw state field
advertised by the full Judge, including candidate action, pretrade, distance,
and previous-action fields.

A different fresh Grok Build used only the exact installed `0.8.30` wheel,
corrected caller assignment, and nine immutable global-ETF CSVs. Fixed-weight
intake succeeded directly, the first candidate Check passed, one richer state
encoder REVERTed (`0.568435` versus leader `0.613754`), and the delegated
Session published and completed one negative-evidence Report. Strict evidence
showed validation advantage `-0.096473` versus the best mechanical baseline,
so the worker correctly retained the mechanical sleeves and made no trading
claim. This gives the final employability cohort four independent passes and
one recoverable pass across five materially different assignments.
Full repository regression passes 327 tests in 1034.965 seconds.

`0.8.24` followed another isolated Grok coworker into a capped ERC assignment
with two independent caller questions. The installed `0.8.23` worker could
answer validation relative performance, but correctly refused to claim that
90% of validation decisions met risk-contribution tolerance: Core exposed only
all-period solver counts and one test-dated latest decision.

Allocation Runs now publish immutable train/validation/test
`constructionFidelity`. Strict Explorer independently rederives every
scheduled, eligible, within-tolerance, cap-gap, maximum-error, and latest-
eligible field from the decision ledger. Orientation, CLI, and Studio expose
validation fidelity directly. The existing performance conclusion is
explicitly `relative-performance-only`; valid older Runs gain the derived read
projection without artifact migration.

The fresh final-wheel retry answered both fidelity clauses on its first fixed
Run from public Core evidence only: validation had 6 eligible decisions, 0
within tolerance, and a latest validation decision with a 0.2011 maximum
contribution error. It created one Project, one Run, zero Sessions, and left
Studio valid without diagnostics. Repository regression passes all 317 tests
in 808.042 seconds and the documentation graph resolves all 1,109 checked
links.

`0.8.23` followed a fresh Grok coworker into a mixed equity/fund Allocation
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

OpenAlice keeps the desk's original Git checkout. AutoQuant V2 does not add an
`aq upgrade` workflow or promise automatic Workspace migration: a coding Agent
may pull and reconcile ordinary Git changes, or retire an old desk and create a
fresh one. Immutable Runs keep the Harness identity under which they were
produced even when the mutable checkout later moves.

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

If the package does not exist yet, start from the Workspace's
`$acquire-market-ohlcv` Skill. It routes one market at a time to exact
provider procedures, requires two independently executable sources for
accepted coverage, preserves raw responses and transformation audits under
Workspace staging, and compares only matching price contracts. Official
routes come first when practical; Yahoo is broad but not an automatic primary.
`$package-autoquant-ohlcv` then bridges the selected staging package into the
same strict intake below. See
[Agent-native market-data acquisition](docs/design/agent-native-market-data-acquisition.md)
and the [field-trial ledger](docs/market-data-acquisition-field-trials.md).

Package asset paths resolve from the directory containing the dataset manifest.
If raw files already exist under `staging/raw-ohlcv/`, place
`dataset-package.json` at `staging/` and use paths such as
`raw-ohlcv/AAPL.csv`. This avoids a temporary second raw-data copy; the
Project-local normalized content-locked snapshot created by intake remains
intentional. Parent paths, absolute paths, and symlinks are rejected.

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
- cash, one named dataset asset, or one funded non-negative fixed-weight
  basket as the evaluation benchmark;
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
