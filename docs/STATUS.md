# AutoQuant V2 current status

Status: usable pre-alpha released as `v0.9.15`; `v0.8.31` remains the Harness
currently consumed by OpenAlice until the host deliberately selects a newer
tag.

Updated: 2026-08-01.

Related: [[README]], [[docs/ARCHITECTURE]],
[[docs/design/agent-native-quant-workbench]],
[[docs/trading-request-field-trials]],
[[docs/agent-employability-validation]],
[[docs/agent-employability-synthesis]],
[[docs/openalice-real-delegation-synthesis]], and [[PLANS]].

## Milestone

AutoQuant V2 has crossed the line from an architectural prototype into a
usable Agent-native quantitative research workbench.

The `0.9.15` patch adds a fixed historical Path Stress lane for an externally
reported book. The caller freezes weights, horizon, episode count, overlap
policy, history, calendar, and split-adjusted price meaning before execution.
Core then enumerates every complete window with fixed opening units and no
within-window rebalance, ranks terminal book loss, selects inclusive
non-overlapping episodes greedily, and reconciles each holding contribution as
opening weight times asset cumulative return. Cash remains explicit and flat.

The strict `aq run book-path-stress` Explorer independently reconstructs
window eligibility, path arithmetic, selection, attribution, dominance,
report fields, and metrics. It rejects semantic tampering even when ordinary
artifact hashes are recomputed. The fixed Study has no editable surface or
Session, and Orientation plus Studio keep it in a descriptive historical lane
with no forecast, account, optimization, Order, or trading authority.

The final isolated candidate-wheel Grok session
`019fbc15-55e6-7740-966e-9ee1f1b7d007` began with zero staged data and wrote
its English brief before retrieval. It acquired a complete Yahoo
split-adjusted panel plus independent Nasdaq evidence, then created exactly
one Project, one fixed Study, one successful Run, one Report, and no Session.
The full-history Nasdaq attempt was preserved as truncated-route failure
evidence; a separate 2020–2026 overlap package did not narrow the formal
2010–2026 task.

The immutable Run enumerated 4,149 complete 20-session windows. Its worst
selected episode was 2020-02-19 through 2020-03-18 at `-19.2416%`, dominated
by QQQ. NVDA dominated the other four selected episodes, so the same holding
did not dominate all five. Exact evidence is in
[[plans/reported-book-path-stress-field-trial]].

The demand-led data invariant is permanent: every question owns a complete
task-local package; available inventory never narrows or silently satisfies
the question. Duplicate bytes are acceptable evidence isolation, and any
deduplication remains a transparent storage optimization only. OpenAlice
remains pinned to `0.8.31`.

Final repository verification passed all 395 tests in 1,103.490 seconds and
resolved all 1,359 documentation links. Lock and Python/Studio syntax checks
also passed; installed-wheel and clean-clone evidence is recorded in the
field-trial plan.

### `v0.9.14`

The `0.9.14` patch proves the two halves of ordinary delegation. Under the
released `0.9.13` baseline, a fresh coworker received a materially incomplete
portfolio question, wrote a durable English brief, asked bounded caller-owned
questions, and stopped with no data, Project, Study, Session, Run, Report, or
quantitative authority. After clarification, the same conversation resumed
from the revised brief rather than inventing holdings, constraints, clock, or
data terms.

That clarification exposed fixed Book Risk defects rather than a need for a
generic intake form. A one-held-asset-plus-cash baseline is now valid when the
candidate is honestly absent. Direction-specific target bounds are mandatory
for sizing; the immutable result distinguishes caller-weight, cash,
volatility, unchanged-book, and infeasible boundaries. The target book also
contains its governing pairwise correlations and constant-weight drawdown,
and the rolling observation floor can match the largest declared lookback
without weakening complete-window evaluation.

The final isolated `0.9.14` wheel replay used no source checkout, prior trial,
or staged data. Grok session
`019fbbd5-ca4a-7b01-ac69-7ac0a3419bf6` acquired Yahoo and Nasdaq packages and
created Project `nvda-cash-size-vol-ceiling`, Study `ohlcv-book-risk`, Run
`run-20260801T054228037779Z-c9f31536b860`, and Report
`report-20260801T054310758003Z-cc8455716151`, with no Session. The fixed Run
kept baseline weights exactly `{QQQ: 0.70}` and returned a 20% NVDA target,
10% cash, 19.29% governing volatility, 0.692 pairwise correlation, and -12.49%
target-book maximum drawdown. The caller's 20% cap binds.

The demand-led data invariant is permanent: each question owns one complete
task-local package; available inventory does not narrow the question, choose
the dataset, or supply missing requirements. Duplicate bytes are acceptable
evidence isolation, while transparent deduplication may optimize storage only.
OpenAlice remains pinned to `0.8.31`.

Exact baseline, candidate, rejected-contamination, and final installed-wheel
evidence is recorded in
[[plans/clarification-first-delegation-field-trial]].

Final repository verification passed 391 tests in 965.751 seconds and all
1,342 documentation links. Lock validation, Python and Studio JavaScript
syntax, source/wheel builds, installed-version and capability smoke, and a
no-local-override clean-clone root Workspace validation/Studio smoke also
passed.

### `v0.9.13`

The `0.9.13` patch comes from a fixed Samsung delayed-gap Event Study run by
fresh installed-wheel coworkers beginning with zero OHLCV. The final replay
used Yahoo split-adjusted history as quantitative authority, Naver provider-
adjusted history as independent coverage evidence, and Daum raw history as a
second independent route. It created exactly one Project, one successful Run,
one direct Report, and no Session, optimization loop, or trading authority.

Provider Skills now retain rather than hide real Korean route behavior. Naver
omits only exact no-trade placeholders from normalized observed history and
audits every raw row; it expands only one-KRW rounded OHLC bounds and rejects
larger inconsistencies. Daum records every out-of-range
`accTradePrice / accTradeVolume` ratio as a diagnostic because the provider
does not establish identical aggregate and daily-OHLC session scope. Valid
prices and share volume are neither repaired nor rejected by that ratio.

The field evidence also corrected Naver from `raw` to `provider-adjusted`.
Samsung history is visibly back-adjusted across its 2018 50:1 split, but the
full provider methodology remains undisclosed, so it cannot be relabelled as
split-only or compared numerically with Yahoo or Daum. The final coworker
correctly preserved all three adjustment contracts and used them only within
their declared authority.

The fixed Run found 29 qualifying events, 28 complete outcomes, 20 primary
non-overlapping events, eight overlap exclusions, and one right-censored
event. Samsung's primary mean was `+2.83%`, versus `+0.41%` unconditional and
`+1.15%` for matched SK hynix; matched excess was `+1.68%`. Both primary and
matched-excess 95% normal intervals included zero, so the verified Report
keeps `observed-advantage` descriptive and grants no causal or trading claim.
Exact field evidence is in [[plans/korea-delayed-gap-event-field-trial]].

The demand-led data invariant is permanent: the current question fixes a
task-complete package, available inventory never narrows it, and intentional
duplication is acceptable evidence isolation. Storage deduplication may be an
invisible optimization only. OpenAlice remains pinned to `0.8.31`.

Final repository verification passed 390 tests in 1,102.837 seconds and all
1,335 documentation links. Lock, Python, and Studio JavaScript syntax checks,
source/wheel builds, a fresh Python 3.11.14 installation with pandas 3.0.5 and
53 public commands, and a no-hardlink clean-clone root Workspace validation
and Studio snapshot all passed. Verified wheel SHA-256:
`8657e6a0b6d3a232a19cb861ca6eb053060ef7827ca427f5624a546faddcd0e4`.

### `v0.9.12`

The `0.9.12` patch comes from a zero-data Japanese Factor-to-Portfolio field
trial and two progressively cleaner installed-wheel replays. The final
coworker wrote the English research brief first, selected `decision-signal`
before its first Run, acquired Yahoo plus Nikkei evidence, kept `1306.T`
strictly context-only, and produced exactly one Project, one Factor Run, one
Portfolio Run, two Reports, one Factor-led Dossier, and no Session.

Yahoo acquisition now rejects both impossible OHLC geometry and short-lived
fivefold scale islands by default. Separate explicit bounded policies may drop
only the audited observations while retaining raw bytes, exact OHLCV, and
boundary ratios; no price repair or rescaling is permitted. The final package
disclosed one impossible observation each for `8306.T` and `8035.T`, a
two-session `1306.T` scale island, and 1,844 aligned sessions for every asset.
Nikkei examples keep canonical research symbols separate from provider lookup
codes.

The scientific handoff stayed honest: positive Factor validation IC was weak
under HAC and cross-split evidence, and Portfolio validation Sharpe did not
erase negative training active return or test benchmark-relative
underperformance. Portfolio evidence remained gated context rather than a
reason to promote the Factor. A current immutable Dossier now projects
terminal `required-research-complete` state with `dossier.show` as read-only
support and later hypotheses optional.

The field trial also exposed ambient-Python drift: `aq` could resolve to the
installed Harness while bare `python3` resolved elsewhere. Every bundled Skill
now uses `aq-python`, an entry point bound to the Harness interpreter, and
guidance forbids global or user-site dependency repair. Final repository
verification passed 387 tests in 1,107.397 seconds, 1,328 documentation links,
lock and Python/JavaScript syntax checks, build/install, installed-wheel Agent
runtime, Studio, and no-hardlink clean-clone smokes. OpenAlice remains pinned
to `0.8.31`. Exact evidence is in
[[plans/japan-trend-efficiency-research-field-trial]].

The final Python 3.11.14 wheel install exposed all 53 public `aq` commands and
pandas 3.0.5. A fresh three-turn Grok 4.5 runtime smoke read only the generated
Skills, selected `aq-python` without prompting, printed the trial venv's exact
interpreter, and ran Yahoo provider help with no network request, package
installation, ambient-Python repair, or Workspace mutation. Final wheel
SHA-256: `0503714efb42ac0593c3e48dd7a9cad54596515edc2df823226a5a427d2e17da`.

The `0.9.11` patch makes the end of a frozen external-period audit a durable
research handoff. A fresh installed-`0.9.10` coworker correctly froze and ran
one Factor-plus-Portfolio Dossier against a strictly later dataset and reached
the right mixed conclusion, but it needed seven ad hoc raw-artifact
inspections and wrote an unverified Project-root Markdown note.

`aq holdout show` now returns bounded source-versus-later decision support and
lane diagnostics. `aq holdout assess --analysis` binds one strict
Agent-authored interpretation to the exact result, evidence, and binding and
publishes verified JSON plus deterministic Markdown. The lifecycle is
`bound` → `completed` → `assessed`; completed Runs alone no longer masquerade
as a completed caller handoff. Core computes no universal pass threshold and
grants no selection, promotion, Order, or trading authority. CLI orientation
and Studio expose the same state. Browser verification also caught and fixed
a latent Factor qualification-card refresh failure. Exact evidence is in
[[plans/frozen-holdout-research-handoff]].

The repaired installed-wheel Grok replay used only public CLI projections,
published verified Assessment `holdout-assessment-cb7783b524a1aaf5` as
`mixed` with Factor `weakened` and Portfolio `strengthened`, left the source
Project byte-identical, and retained exactly two target Runs. Final release
verification passed 381 tests in 945.087 seconds, 1,321 documentation links,
lock and Python/JavaScript syntax checks, source/wheel builds, a fresh Python
3.11.14 installation with pandas 3.0.5 and 53 public commands, installed-wheel
absolute-next-action smoke, browser Studio QA, and no-hardlink clean-clone root
Workspace smoke. Wheel SHA-256:
`b7247bc475d1fe601641b826268399a523fe8c74c2500d636cb4711d82525994`.

The request-led data invariant remains explicit: the question determines its
complete venue/assets/interval/clock/adjustment/date package, existing data is
only a possible source, and intentional duplication is preferable to silently
changing the question. OpenAlice remains pinned to `0.8.31`.

The `0.9.10` patch addresses ordinary longitudinal maintenance inside one
Project. A fresh installed `0.9.9` coworker correctly preserved an existing
U.S. mega-cap Book Risk request, dataset, Study, Run, and Report, reacquired a
complete newer Yahoo panel plus an independent Nasdaq audit, and refused to
overwrite the singleton Project intake. It exposed that public `study intake`
could bind a second request only to the original dataset.

The bounded repair adds an optional complete dataset package to `aq study
intake`. A strictly newer comparable vintage receives a Study-owned namespace,
snapshot, content identity, fixed Judge binding, Run, and direct Report while
the original construction evidence remains byte-identical. AutoQuant does not
add a shared cache or inventory gate: each request still owns a task-complete
package, and data reuse never constrains what may be researched. OpenAlice
stays pinned to `0.8.31`. Exact baseline and candidate evidence is recorded in
[[plans/same-project-data-vintage-refresh-field-trial]].

Fresh Grok candidate replay created Study `ohlcv-book-risk-20260731`, Run
`run-20260801T000250149387Z-b0b74ab40a37`, and Report
`report-20260801T000324664906Z-8a7ed7e6119c`. It preserved every prior fixed
or immutable file and changed only longitudinal `research.md`. Yahoo covered
the requested final session; Nasdaq.com's peer display remained one session
late and was disclosed rather than filled or relabelled. Repository regression
passes 380 tests in 933.218 seconds, 1,314 documentation links, lock and syntax
checks, source/wheel builds, and fresh Python 3.11.14 installation exposing 52
public commands.

The `0.9.9` patch revisits the unaccepted `0.9.0` Taiwan Factor assignment
without changing its caller-owned data authority. A fresh installed `0.9.8`
worker started with zero market data, declared official TWSE plus independent
FinMind raw evidence as a gate, obtained the full FinMind peer panel, and hit
TWSE's documented HTTP 307 security block. Unlike the earlier worker, it
stopped at `UNSUPPORTED` before Project intake and produced no Run, Report, or
single-provider factor interpretation.

The provider route itself now preserves evidence that the worker previously
had to reconstruct manually: `provider-failure.json`, a per-request attempt
ledger, safe response headers, and exact error bodies are written before the
process returns nonzero, beside the standard bounded route receipt. Cookies
and other unapproved response headers are excluded; failure creates no dataset
package or quantitative authority. TWSE raw comparison guidance names FinMind
as the peer and keeps Yahoo split-adjusted history coverage-only. Acquisition
remains demand-led, provider networking remains outside Core, and OpenAlice
stays pinned to `0.8.31`. Exact trial evidence is recorded in
[[plans/authority-gated-twse-factor-field-trial]].

The final installed `0.9.9` Grok replay used the unchanged assignment and
public Workbench surfaces, preserved the five official 307 response bodies
without a second probe, and again stopped at `UNSUPPORTED` with no dataset
intake, Study, Session, Run, Report, or factor interpretation. The release
audit passed 378 tests in 928.146 seconds, 1,306 documentation links, lock and
Python/JavaScript syntax checks, source/wheel build, fresh Python 3.11.14
installation with 52 public commands, and a no-hardlink clean-clone root-
Workspace smoke. The final wheel SHA-256 is
`049369a2178cab7b4efdf92c8d89615912c695cf233ecb38701141e7e6599c6d`.

The `0.9.8` patch proves one completed Project can accept a related second
fixed Book Risk question without overwriting its original intake or creating a
duplicate Project. The installed `0.9.7` baseline worker chose the correct
Project and exposed one concrete defect: it could declare and freeze an
alternate position snapshot, but the Book Risk Judge and Explorer still read
the Project-singleton path.

`aq study intake` now validates a new strict request against the retained
asset descriptions and dataset range, then writes Study-owned request,
position-snapshot, covariance-method, and current-Judge paths. The fixed Judge
receives those paths explicitly; Explorer resolves the same snapshot from the
Run's frozen Study arguments. Direct Report publication resolves the request
from immutable Run inputs and verifies it against the frozen position snapshot,
so the follow-up Report cannot be mislabeled with the Project-root question.
Multiple independent fixed Studies remain explicit-selection territory;
orientation preserves that boundary while acknowledging their existing
evidence.

The final installed-wheel Grok 4.5 replay used public CLI, schemas, and
materialized Skills without reading package implementation. It produced the
second successful Study, Run, Explorer answer, and direct Report inside the
existing Project, kept both old and new Reports independently readable, and
changed none of the original 47 files except the explicitly longitudinal
`research.md`. Evolving `research.md` and `framework-needs.md` remain notes;
preservation applies to fixed authority and immutable evidence. Data
acquisition remains demand-led rather than inventory-led, and OpenAlice stays
pinned to `0.8.31`. Exact field and final release evidence is recorded in
[[plans/same-project-book-risk-follow-up-field-trial]].

The release audit passed 376 tests in 925.726 seconds, 1,298 documentation
links, lock and Python/JavaScript syntax checks, source/wheel build, fresh
Python 3.11.14 wheel installation with 52 public commands, the final isolated
Grok replay, and a no-hardlink clean-clone root-Workspace smoke.

The `0.9.7` patch proves a long-lived Workspace can preserve completed A-share
Event research byte-for-byte while accepting a separate U.S. Book Risk task
with newly acquired task-local data. The installed `0.9.6` baseline worker
kept all 30 old Project files, its sole Run, the Workspace default, and one
Workspace manifest unchanged; it created one sibling Project, one fixed Run,
one direct Run Report, and no Session or search loop.

Observed friction became two bounded repairs. For caller-bounded one-leg Book
Risk sizing, the authorized covariance lookback is now the primary/current
window across metrics, contribution and reduction ledgers, drawdown, equity
path, rolling evidence, CLI, and Studio. The immutable equity artifact retains
the longest fixed path so every diagnostic lookback remains independently
reconstructable. U.S. provider guidance now directs fixed Labs to aligned V1
packages and reserves observed-only V4 for intentionally ragged Factor work.
Existing explicit Project identity prevented cross-Project writes, so no new
process-local “active Project” state was added. OpenAlice stays pinned to
`0.8.31`. Exact trial and release evidence is recorded in
[[plans/long-lived-cross-market-workspace-field-trial]].

The release audit passed 374 tests in 923.926 seconds, 1,288 documentation
links, lock and syntax checks, source/wheel builds, fresh Python 3.11.14 wheel
installation with 51 public commands, a fresh installed-wheel Grok 4.5 replay,
and a no-hardlink clean-clone root-Workspace smoke. The final worker completed
with no Core or provider failure and one disclosed accidental probe-Project
create/remove retry; final research state still contains exactly two Projects,
one new Run, one direct Report, zero Sessions, and one Workspace manifest.

The `0.9.6` patch proves the market-data path begins with research demand, not
available inventory. A fresh installed `0.9.5` worker received a fixed CATL
opening-gap question and no OHLCV, attempted three named mainland routes,
preserved raw/adjusted incompatibility, selected one adjusted package, and
completed exactly one negative Event Run. Its reusable friction became narrow
Core and Skill repairs: descriptive Event intake retains finite zero-volume
sessions, accepts all-context-only roles, mainland raw routes preserve caller-
verified fund classes, cross-adjustment comparison supports coverage-only
evidence, and failed provider processes leave a standard bounded record.
Yahoo's one-session adjusted freshness lag and the absence of a second
adjusted mainland route remain explicit external limitations. OpenAlice stays
pinned to `0.8.31`.

The release audit passed 371 tests, 1,279 documentation links, the complete
old-Run compatibility suite, Studio JavaScript syntax, source/wheel builds,
fresh Python 3.11 installation, a zero-retry installed-wheel Grok 4.5 replay,
and a no-hardlink clean-clone Workspace smoke. Exact evidence is recorded in
[[plans/demand-led-market-data-field-trial]].

The `0.9.5` patch makes Agent route choice and evidence publication more
truthful. A public Project-template catalog now states each construction's
lanes, purpose, positive fit, and anti-fit and explicitly routes coordinated
Factor-to-Portfolio or Factor-to-RL assignments to the Research Desk. A
successful current request-bound Run can be reported directly without
inventing an editable Session. These Project-owned Reports carry an explicit
Run anchor, exact request/Study/Run/Harness/dataset/selection-integrity and
decision-support evidence, and zero Check/Experiment authority. Session-owned
Reports remain the path for actual candidate investigation and take precedence
after a Session exists. Program, Dossier, orientation, CLI, and Studio verify
and disclose the same distinction.

One fresh installed-wheel Grok 4.5 worker selected the coordinated Research
Desk on its first attempt, executed exactly one Factor and one Portfolio Run,
published two Run-bound Reports and one Dossier, and finished with zero
Sessions, Checks, or Experiments. The final release audit passed 368 tests,
1,271 documentation links, Studio syntax, source/wheel build, fresh Python
3.11 installation, capability/template discovery, and clean-clone operation.

The `0.9.4` patch aligns normalized signal-intent attribution with actual
prediction-mode-aware Portfolio construction. Explicit two-asset relative
value now uses the same capped complementary pair at intent and pre-governor
target stages, including intentional Cash when per-leg caps are below the
available gross budget. Ordinary cross-sectional dollar-neutral research
retains its full-side breadth rule. Explorer schema, CLI, Studio, Reports,
Dossiers, agenda, docs, and sample evidence disclose the mode and construction
and strictly reconcile pair parity without rewriting immutable Run bytes.

Two fresh installed-wheel Grok 4.5 workers exercised both sides of the
scientific gate. A non-baseline rank-invariant rescaling passed Check, received
`REVERT`, consumed selection budget, and correctly stopped without weights
when adjusted evidence blocked Portfolio. A frozen-factor reproduction reached
Portfolio and reported NVDA/QQQ `-0.30/+0.30`, zero context exposure, 75/75
normalized-intent/raw-target active dates, exact pair-target error `0.0`, and
`monetized-positive` with trading cost as the largest adverse stage. This
separates honest negative selection evidence from the corrected downstream
attribution rather than forcing one trial to demonstrate both.

The `0.9.3` patch adds predeclared target-translation robustness for the two
temporal prediction modes without changing the fixed 60-observation / 20-
minimum construction contract. Single-asset timing and two-asset
relative-value Portfolio Runs now retain exact 40/60/120 state, target,
performance, turnover, cost, and current-book evidence. Validation alone
diagnoses stable versus translation-sensitive target paths; visible test is
audit-only, and alternate windows have no selection or recommendation
authority. Cross-sectional Runs explicitly disclose that the diagnostic does
not apply.

The strict Explorer reconstructs every alternate path from immutable Factor
decision evidence and rejects rehashed score tampering. CLI, Studio, Reports,
research agenda, and sample evidence share the same result. A translation-
sensitive result routes back to factor representation rather than window
tuning, while the existing monetization evidence continues to isolate
factor-intent, sizing/caps, covariance governance, execution/no-trade, and
cost.

One fresh installed-wheel Grok 4.5 worker completed a bounded NVDA/QQQ
relative-value assignment with three context-only assets. It preserved the
pair-only target population, independently found the new 40/60/120 evidence,
kept 60 as the fixed base despite different descriptive Sharpes, and returned
`stable-target-path` with current NVDA/QQQ targets of `-0.30` / `+0.30` under
all profiles. The full release audit passed 361 tests in 1009.615 seconds,
1,246 documentation links, Studio syntax, source/wheel builds, fresh Python
3.11 installation with all 50 public capabilities, and the no-hardlink clean-
clone repository-root workflow.

The `0.9.2` patch gives every supported Factor prediction mode one causal,
request-bound path into mechanical target-weight research. Cross-sectional
signals exclude context-only assets, single-asset timing ranks only its own
causal history, and two-asset relative value ranks the caller-ordered spread
into exact complementary leg scores. Factor, Portfolio, and governed RL bind
the same Factor claim and prediction population; decision artifacts,
Explorers, and Studio disclose and strictly reconcile that contract. The
boundary remains historical target weights with no Order or trading authority.

One fresh installed-wheel Grok 4.5 worker independently replayed a supplied
single-asset BTC timing assignment with four context-only assets. It completed
the bounded Factor-to-Portfolio handoff with zero retries and verified
`single-asset-temporal`, BTC-only causal-history scoring, unavailable context
scores, and a flat BTC/Cash latest model target. Corrected validation net
Sharpe was `-3.2244`, materially worse than the old context-ranked path, so the
trial directly demonstrates why prediction qualification and portfolio
monetization must remain separate gates.

The `0.9.1` patch generalizes candidate-declared Factor component evidence to
single-asset temporal and two-asset relative-value evaluation. Temporal Runs
now disclose raw and nearest-peer-residual rank-correlation contributions,
pairwise redundancy, fixed diagnostic-blend removal evidence, and train-fixed
conditional context states without mislabeling them as cross-sectional IC or
changing the immutable Factor objective. Strict Explorer, research agenda,
CLI, Studio, Reports, Dossiers, templates, and the repository sample consume
the same component-v3 contract.

One fresh Grok 4.5 worker completed a real LINK-versus-ETH multi-interval
relative-value assignment over 13,800 Binance Spot 1h bars per asset and used
the new evidence to return a truthful negative result without spending an
unnecessary Experiment. A second fresh worker verified the resulting mandate
repair: exactly two explicit `two-sided` relative-value assets plus named
`context-only` assets retain the dollar-neutral zero-net pair construction,
caller role provenance, and no-trading authority.

The `0.9.0` real-delegation cohort adds six materially different Grok 4.5
assignment families over source-authority boundaries, fixed Event and Book
Risk evidence, causal multi-interval Factor research, and governed RL. The
accepted workers preserved useful negative evidence and no-trading authority;
every severe or recurring Workbench defect received a regression and a fresh
worker retry. The complete 354-test, documentation, build, installed-wheel,
Skill-discovery, and remote clean-clone audit also passed for the `v0.9.0`
release. See
[[docs/openalice-real-delegation-synthesis]].

With `v0.9.0`, a human, local coding Agent, or coworker delegated from
OpenAlice
can:

1. clone the repository and immediately discover the Harness plus its
   Git-backed `projects/`, complete sample, exact next action, and Studio;
2. preserve an ordinary-language assignment as an English Project research
   brief;
3. clarify caller-owned intent before binding machine authority;
4. atomically create a self-contained Project from a strict request and
   content-locked OHLCV package;
5. choose a fixed Study or enter a bounded editable Research Session;
6. run deterministic factor, portfolio, governed-RL, event, reported-book, or
   Portfolio-native allocation research;
7. retain every measurement as an immutable, versioned Run with exact Harness,
   data, Judge, dependency, and artifact identity;
8. inspect the same verified result through human CLI, JSON CLI, orientation,
   Studio, Reports, or Dossiers;
9. return useful negative evidence without turning rejection into a system
   failure or a fabricated trading instruction.

`0.8.8` made the repository clone the canonical default Workspace. Its
ordinary `sample-research-desk` contains Factor, Portfolio, and governed-RL
Studies, retains explicitly historical clean `0.8.7` and `0.8.28` Factor
Runs, preserves its `0.9.0` development Run, and adds one clean current
`0.9.1` candidate Run with component-v3 evidence, plus a clean current `0.9.2`
Run that binds the shared prediction population for immediate Studio
inspection, a clean `0.9.3` Portfolio Run that explicitly marks temporal
translation robustness not applicable for its cross-sectional mode, and a
clean `0.9.4` Portfolio Run that preserves the cross-sectional normalized-
intent construction after the relative-value repair. An
ignored strict local Workspace configuration lets
Workbench development reuse an external real-Project collection without
shipping those cases or changing the user's internal default.

`0.8.9` makes the Agent Work Brief follow the maintained local research
question. A clearly headed question in `research.md` now reaches CLI and
Studio with explicit provenance and source path; a validated delegated request
still takes precedence, and arbitrary Markdown prose is never guessed into
caller intent. Two clean Grok Build field trials supplied the original failure
and independent pre-Run retry evidence.

`0.8.10` extends the same truthful orientation contract to locally constructed
fixed requests. A Project request is visible only when it strictly validates
and a fixed Study dependency binds its exact canonical hash. This lets
Allocation, Event Study, and Book Risk templates self-describe without
granting authority to an arbitrary file.

`0.8.11` makes the editable Session handoff equally unambiguous. Once a KEEP
leader and worktree are identical, orientation makes guarded promotion the
primary action. A newer candidate remains check/evaluate work, while delegated
promotion remains Report-bound and is never advertised without an executable
`--report` command. The exact passed candidate Check remains attached while
its source, Study, preflight, and Harness identities are still current.

`0.8.12` makes the advertised Session operating root re-enterable. Read-only
orientation verifies a fixed-inventory-locked worktree marker and its exact
owning Project/Session topology, then returns the canonical brief without
copying dataset bytes or redirecting mutation commands.

`0.8.13` makes bounded research completion qualification-aware. Qualified
question headings remain explicit authority, Experiment verdicts disclose
their Session-only scope, promotion returns the exact subsequent Work Brief,
and a scientifically blocked terminal lane treats further research as an
optional continuation.

`0.8.14` makes fixed-Study completion an explicit answer handoff. Current
successful Book Risk, Price Event, and Allocation evidence leaves no primary
CLI action; the Agent is told to write and return the answer while the strict
Explorer remains optional supporting evidence. Descriptive agenda Run identity
now uses the exact immutable Run input hash.

`0.8.15` makes the editable Factor contract visible before source changes.
Study inspection, orientation, JSON, human CLI, and Studio agree on the
Project's actual base interval, available completed feature intervals, panel
columns, component metadata fields, and legal component roles. Preflight
rejects illegal static component metadata before final-factor execution, and
a baseline-restored Session obeys a verified freeze/external-holdout agenda
instead of advertising another in-sample edit.

`0.8.16` makes completed trial evidence a first-class Session handoff.
Restored leaders enter explicit review rather than mandatory-edit language;
delegated evidence can be reported and completed without hiding the option for
another explicitly bounded hypothesis. Current-candidate Check state stays
separate from a durable latest-Experiment/Run/verdict/preceding-Check pointer.

`0.8.17` makes fixed-reference candidates truthful in the fast feedback loop.
Factor preflight uses two bounded decision assets plus all fixed mandate
context and benchmark assets, discloses that exact surface, and leaves the
complete Judge unchanged. KEEP promotion and baseline-retaining completion
are now explicitly projected as mutually exclusive terminal Session paths.

`0.8.18` makes unknown provider retrieval time an honest first-class claim.
Dataset packages keep the required field but may use explicit JSON `null`
instead of forcing a coding Agent to invent a later packaging timestamp.
Known timestamps remain strict and timezone-aware, while both forms stay
content-locked through snapshot validation and Studio.

`0.8.19` makes historical drawdown first-class fixed Book Risk evidence.
New Runs publish the full daily constant-weight close-to-close equity path,
signed maximum drawdown, and observed peak/trough/recovery interval; the
Explorer re-derives every row and each fixed lookback scalar before CLI or
Studio can display it. Pre-`0.8.19` immutable Runs remain readable and mark
drawdown unavailable instead of being invalidated or silently retrofitted.

`0.8.20` makes strict Research Report evidence references self-describing.
The public executable schema, capabilities, CLI help, and durable docs agree
that a Run artifact path is null or copied exactly from
`result.artifacts[].path`, while Experiment and Campaign paths are null. The
existing semantic evidence validation remains strict and unchanged.

`0.8.21` makes frozen external target intake atomic and lane-aware. Core
reuses the current source Dossier's canonical request, applies Factor,
Portfolio, and governed-RL target history floors of 120, 180, and 240 rows,
and rolls back the target plus Workspace configuration on any failure.
Holdout Runs carry explicit external-audit execution identity, keep sparse
secondary diagnostics visible, and still require 20 usable observations for
the exact primary objective.

The isolated installed-wheel retry completed the unchanged 141-session
Factor-only audit through the public atomic path. Its frozen source objective
was `+0.101253` mean IC and the strictly later objective was `-0.284679`;
both Projects remained valid, Studio had no diagnostics, and the negative
external result granted no selection or trading authority.

`0.8.22` makes Project selection safe in a persistent multi-Project desk.
Read-only orientation entered through a Workspace names the effective
Workspace, selection method, default, selected Project, Project count, and
available ids. A Workspace default remains a navigation convenience; any
Project-local `creates-artifact` or `mutates-project` operation requires
explicit Project identity once the Workspace contains multiple Projects and
fails before state changes otherwise.

The isolated installed-wheel retry discovered the selection contract through
public orientation, kept the default unchanged, and completed one fixed Book
Risk Run plus one fixed Price Event Run using explicit Project identity.
Independent verification found both Projects valid, both data snapshots
byte-identical to their separate caller inputs, no Sessions, and a valid
two-Project Studio snapshot without diagnostics. An omitted-Project Run was
then rejected before either immutable Run inventory changed.

`0.8.23` makes aligned mixed-class research truthful without changing its
market clock. V1–V4 OHLCV packages accept either the historical homogeneous
top-level class or one complete per-asset class vector summarized by the
common class or `mixed`. Classified snapshots preserve every instrument class
and match it to the canonical request on every load; partial vectors and
rehashed class tampering fail explicitly.

The fixed Allocation reference may now include requested context-only assets.
Reference membership remains evaluation authority only: those legs stay out
of ERC candidate construction, caps, positions, and component-risk shares
while the independent funded reference still applies its own schedule, drift,
no-trade band, turnover, and cost.

The isolated installed-wheel retry completed the unchanged mixed
AAPL/NVDA/GLD/TLT allocation against a 60/40 SPY/TLT reference with one fixed
Run and no Session. Its remaining concrete friction was information
compression rather than correctness: Study inspection showed only the
top-level `mixed` summary. Study JSON inspection, strict Allocation Explorer,
and Studio now expose the complete verified symbol-to-class map and whether it
came from explicit per-asset declarations or a legacy homogeneous summary.

A second fresh final-wheel worker repeated the complete task after that
read-model change. Study and Explorer class maps matched, SPY candidate target,
executed weight, and risk contribution remained zero while its reference
weight was funded, strict verification reconciled, and Studio had no
diagnostics.

Final verification passes all 315 tests in 805.092 seconds, resolves all 1,104
documentation links, and installs the final `0.8.23` wheel in a fresh Python
3.11 environment for the complete mixed-class Allocation field trial.

`0.8.24` separates a fixed Allocation Run's validation relative-performance
verdict from its ERC construction fidelity. Every split now publishes exact
scheduled, eligible, within-tolerance, cap-gap, maximum-error, and latest-
eligible evidence. Strict Explorer rederives it from immutable decisions,
rejects mismatched new reports, and gives valid older Runs the same read model
without rewriting history. Orientation, CLI, Studio, and public schemas carry
the validation view directly.

The isolated final-wheel Grok retry completed the unchanged capped
AAPL/NVDA/GLD/TLT assignment against the fixed SPY/TLT reference in one
Project, one Run, and zero Sessions. From public Core evidence only, it kept
the positive validation net-Sharpe conclusion scoped to relative performance,
then separately rejected both construction-fidelity clauses: 0 of 6 eligible
validation decisions were within tolerance and the latest validation decision
had a 0.2011 maximum contribution error. Strict verification reconciled the
new block and Studio remained valid without diagnostics. Full regression
passes 317 tests in 808.042 seconds and all 1,109 documentation links resolve.

`0.8.25` lets an Agent explicitly adopt a pre-staged desk as a Workspace
without moving caller files. Default initialization still owns only absent or
empty targets. Adoption preserves every surrounding entry, refuses existing
base/local configuration or any `projects` entry, and does not import staging
into quantitative identity. Parser help, capability JSON, structured failure
text, and the Agent guide expose both safe routes.

The isolated installed-wheel Grok retry began with its assignment plus
NVDA/SPY bytes already below the intended non-empty Workspace. It discovered
`--adopt-existing`, preserved all three staging hashes, created one fixed Event
Study Project and one Run with zero Sessions, and left strict Explorer and
Studio valid. The Run found 22 primary complete events after four overlap
exclusions; its `observed-advantage` conclusion remained explicitly
descriptive with no trading authority. Full regression passes 321 tests in
826.969 seconds and all 1,113 documentation links resolve.

`0.8.26` makes the dataset-package manifest directory an explicit Agent-facing
source root without adding another path authority. Asset paths remain confined
POSIX-relative descendants and symlinks remain invalid. Putting the manifest
at staged files' common ancestor lets intake consume the original caller bytes
directly; only the intentional Project-local normalized content-locked
snapshot is materialized.

The first isolated installed-wheel worker discovered that route from public
schema/help, made no raw-data duplicate, and completed the fixed Event Study.
It also exposed a half-present Research Request source artifact/revision retry.
The final schema now describes and rejects that state before intake, and CLI
help plus capabilities name the both-values-or-both-null rule. A second fresh
final-wheel worker completed the same assignment on its first intake with one
Project, one Run, zero Sessions, unchanged staging hashes, no CLI failure, and
valid strict Explorer, orientation, Project, and Studio evidence.
Full regression passes 322 tests in 924.699 seconds and all 1,117
documentation links resolve.

`0.8.27` makes the separately declared primary forward horizon implicit in the
complete evaluated set, so callers may provide only additional sorted
diagnostics while Core preserves a five-horizon maximum. It also recognizes a
current validated baseline-retaining Session completion as terminal evidence:
the exact Report remains visible, no further Session is required, and an
explicit new Session remains optional without inferred prose budgets. A
Report-bound promotion has the same terminal navigation while continuing to
withhold scientific qualification. Report schema now includes one complete
copyable analysis example after the first verification worker exposed a nested
recommendation-field retry.
Full repository regression passes 325 tests in 959.906 seconds and all 1,129
documentation links resolve.

`0.8.28` aligns every newly seeded Factor baseline with its verified interval
surface. Daily V1/V4 and observed-only V5 inputs expose no fictional feature
components; configurable/multi-interval inputs declare only components whose
bars are actually present. Session, Report, Dossier, CLI, and Studio now
distinguish the first candidate test audit from later post-audit candidate
iterations. Core keeps requiring fresh external evidence after visible test
and candidate iteration, while explicitly marking actual test guidance as
unobservable rather than asserting it occurred. The checked-in sample retains
its immutable `0.8.7` Run and adds current evidence only through an ordinary
versioned Run.

The final installed-wheel worker used the same nine caller-staged Yahoo daily
files and one predeclared price-trend plus dollar-volume hypothesis. It
completed strict intake, baseline, Session, Check, one REVERT Experiment,
Report, baseline-retaining completion, strict Explorer, final orientation, and
Studio with no CLI retry. The first-audit/post-audit distinction projected
exactly, raw staged hashes remained unchanged, and no Portfolio, RL, holdout,
Order, or second Experiment was created.
Full repository regression passes 326 tests in 868.625 seconds and all 1,143
documentation links resolve.

`0.8.29` adds a lifecycle-aware presentation role to the verified research
agenda. A move remains `current-research-guidance` while a bounded
investigation is active. Once an immutable trial is waiting for review or a
reported lane has no required primary action, the same evidence-derived move
becomes `optional-follow-up` in shared JSON, terminal output, and Studio.
Agendas with no move are `unavailable`. This is presentation authority only:
Core neither infers a prose experiment budget nor executes, promotes, or
trades from an agenda.

The `v0.8.31` release remains the selected OpenAlice consumption baseline
until the host deliberately changes its pin. That older release adds a
canonical 16-Skill
market-data acquisition bundle, two-source field evidence for every
first-batch market, strict provider-neutral intake, and truthful route,
adjustment, volume, authority, and degraded-access boundaries. `v0.8.30`
remains the fixed-reference and final employability-cohort milestone.
`v0.8.28` remains the truthful
first-Factor-surface milestone, while `v0.8.27` remains the primary-horizon and
terminal Session-handoff milestone, while `v0.8.26` remains the manifest-rooted
staging and paired request-source milestone, while `v0.8.25` remains the explicit Workspace
adoption milestone, while `v0.8.24` remains the split Allocation
construction-fidelity milestone, `v0.8.23` remains the mixed-class
Allocation milestone, `v0.8.22` remains the multi-Project
selection-safety milestone, `v0.8.21` remains the atomic lane-aware
holdout-target milestone, `v0.8.20` remains the self-describing Report
evidence milestone, `v0.8.19` remains the fixed Book Risk
drawdown milestone, `v0.8.18` the honest unknown-provider provenance
milestone, while `v0.8.17` remains the
reference-aware preflight and terminal-handoff milestone, while `v0.8.16`
remains the completed
trial-handoff milestone, while `v0.8.15` remains the candidate-contract
and freeze-handoff milestone, while `v0.8.14` remains the
fixed-Study answer-handoff milestone, and `v0.8.13` remains the
qualification-aware handoff milestone, and `v0.8.12` remains the
worktree re-entry milestone, and `v0.8.11` remains the
promotion-first orientation milestone, and `v0.8.10` the fixed
Project-request orientation milestone, `v0.8.9` the
research-brief orientation milestone at commit `2157d99`, and `v0.8.8` the
repository-root Workspace milestone at commit `d2e56f0`.

The canonical repository is
[TraderAlice/Auto-Quant-V2](https://github.com/TraderAlice/Auto-Quant-V2).
The earlier personal repository remains a historical backup remote; the
original `TraderAlice/Auto-Quant` repository remains the separate Classic
line.

## `0.9.4` verification snapshot

- the repository sample contains a clean `0.9.4` cross-sectional Portfolio
  Run bound to commit `f17d261` and projected through strict CLI and Studio;
- a fresh non-baseline-factor Grok trial proved honest REVERT and adjusted-
  evidence blocking without manufacturing targets;
- a second fresh Grok trial proved exact relative-value normalized-intent /
  pre-governor target parity through the installed wheel;
- all 361 unit tests passed in 1066.637 seconds and all 1,253 documentation
  double-links resolve;
- build/install/capability and clean-clone evidence are recorded in the
  completed release plan.

## `0.9.2` verification snapshot

- all 360 unit tests pass in 995.694 seconds;
- all 1,227 documentation double-links resolve;
- Studio JavaScript syntax, source and wheel builds, fresh Python 3.11
  installed-wheel version/capability smoke, and a no-hardlink clean-clone
  repository-root workflow pass;
- the repository sample contains a clean `0.9.2` Factor Run bound to commit
  `1166a78` and projects through strict CLI and Studio evidence;
- fresh Grok 4.5 independently completed the exact supplied BTC Factor-to-
  Portfolio handoff with zero retries or Core failures and exposed the fixed
  temporal translation in its outward report.

## `0.9.1` verification snapshot

- Full repository regression passed 356 tests in 960.878 seconds and all
  1,214 documentation links resolve.
- Lock validation and clean sdist/wheel builds passed. The wheel installed in
  a fresh Python 3.11 environment, reported `aq 0.9.1`, and exposed all 50
  public commands through the machine-readable capability manifest.
- A fresh empty Workspace initialized successfully and materialized all 16
  market-data Skills into both `.agents/skills/` and `.claude/skills/`; its
  missing default Project failed with the expected structured selection error.
- A no-hardlink clone with no local override selected the committed
  `sample-research-desk` from `autoquant-workspace.json`. Orientation,
  validation, Project listing, Studio snapshot, and strict Factor Explorer all
  passed; the current sample Run reports
  `candidate-declared-components-v3`.
- One full Grok 4.5 relative-value trial and one focused explicit-role retry
  proved that temporal component evidence is sufficient for a useful negative
  handoff and that a named context asset no longer destroys the caller's
  dollar-neutral pair mandate.
- No long backtest, account access, Order, TP/SL, or trading action ran.

## `0.8.31` verification snapshot

- Clean implementation commit `1e00c92` built sdist
  `auto_quant-0.8.31.tar.gz`
  (`2cb5f816…22f7203`) and wheel
  `auto_quant-0.8.31-py3-none-any.whl`
  (`c365da95…daa2f0`).
- The wheel installed in a fresh Python 3.11 environment, reported
  `aq 0.8.31`, exposed the public capability manifest, initialized a clean
  Workspace, materialized all 16 Skills into both discovery roots, created
  and selected a Project, and passed orientation, validation, Project list,
  and Studio snapshot.
- The canonical and both materialized Skill roots share bundle SHA-256
  `ad18cef0…361b3`; all 16 Skills pass the maintained validator and
  deterministic fixture tests.
- Real bounded two-source field trials cover named U.S.,
  XSHG/XSHE/XBSE, Tokyo, KRX-listed, TWSE, HOSE, and XPAR equities. Matching
  raw or adjusted contracts are compared explicitly; unlike contracts prove
  route plurality only. Official TWSE is authority-first, while Eastmoney's
  repeated connection closure remains visible degraded evidence.
- Two isolated Grok Build coworkers received only an installed wheel, a new
  Workspace, ordinary assignments, materialized Skills, and provider access.
  Together they exercised every first-batch row, created valid U.S. and Korean
  Projects, refused an invalid raw-versus-adjusted comparison, and disclosed
  remaining venue-authority limits. The first found a V4 daily orientation
  defect; the second proved the repaired `1d` candidate surface.
- Full repository regression passed 346 tests in 1124.263 seconds. All 1,193
  documentation links resolve, the build and diff checks pass, and no long
  backtest, account access, Order, TP/SL, or trading action ran.

## `0.8.30` verification snapshot

- Candidate wheel
  `auto_quant-0.8.30-py3-none-any.whl`
  (`90ea4f4…2cbdbb`) was built from clean commit `2636c5b` and installed in a
  fresh Python 3.11 environment.
- A fresh isolated Grok Build received only that installed CLI, the corrected
  caller assignment, and nine staged Yahoo CSVs. No repository source,
  docs/tests/plans, prior trials, web, memory, subagents, or coaching were
  available.
- Caller fixed-weight intake succeeded directly and materialized nine complete
  `1/9` weights in Portfolio Mandate `mandate-91200d039b7e0a29`.
  The first RL candidate Check passed on the complete advertised state.
- Accepted leader Run `run-20260730T100311246926Z-22d3892442e1` returned
  validation mean net Sharpe `0.613754` but validation advantage
  `-0.096473` versus the best fixed mechanical baseline. One Experiment
  scored `0.568435` and REVERTed. The worker published
  `report-20260730T100838822783Z-3dd7edc89b7b`, completed the delegated
  Session as `baseline-reported`, and made no trading claim.
- Independent installed-wheel replay reconciled packet hashes, intake,
  caller benchmark, all Run records, strict RL Explorer, Check, Experiment,
  Report, completion, final orientation, Project validation, and Studio.
- The final employability cohort contains four independent passes and one
  recoverable pass. The minimum OpenAlice desk-consumption gate is recorded in
  [[docs/agent-employability-synthesis]]; no OpenAlice code changed.
- Full repository regression passed 327 tests in 1034.965 seconds. Python and
  Studio JavaScript syntax, lock/diff checks, and the repository sample/fresh-
  template parity test pass.
- Final clean commit `d1f8863` built sdist
  `c6aaad2…5b98e` and wheel `7ea801a…b1531`. A fresh Python 3.11 install
  passed public version/schema/capability and package-content smoke. A
  no-local-override clone loaded and validated the checked-in sample, produced
  a valid zero-diagnostic Studio snapshot, created a fresh research-desk
  Project, and validated it. All 1,177 documentation links resolve.

## `0.8.29` verification snapshot

- Fresh isolated Grok Build used only an installed `0.8.29` wheel from clean
  commit `d45b100`, the unchanged caller assignment, and nine staged Yahoo
  CSVs; no source, repository docs/tests/plans, web, memory, subagents, or
  coaching were available.
- It created one Project, wrote `research.md` before Runs, established one
  baseline, passed one Check, and spent one Experiment. Candidate validation
  mean IC improved from `-0.119921` to `-0.097214`, earning KEEP while fixed
  scientific diagnosis remained `raw-predictive-edge-absent`.
- Report and guarded promotion preserved the relatively better source without
  granting scientific qualification. Terminal orientation returned
  `required-research-complete`, `primaryAction: null`, and
  `researchAgenda.moveRole: optional-follow-up`; the worker stopped with no
  second Session, Portfolio, RL, holdout, Order, or trading claim.
- Independent installed-wheel replay reconciled Project validity, both strict
  Factor Explorers, Report, promotion, final orientation, and Studio
  (`valid: true`, zero diagnostics). Every staged input hash remained
  unchanged.
- Full repository regression passed 326 tests in 851.125 seconds; all 1,162
  documentation links resolve. Python/JavaScript syntax, lock/diff checks,
  source and wheel build, fresh Python 3.11 install, and public version/schema
  smoke passed.

## What works today

| Research need | Current route | Lifecycle |
| --- | --- | --- |
| cross-sectional or temporal factor research | `ohlcv-factor-lab` | editable candidate, bounded Session, validation-only selection |
| factor-to-target portfolio research | `ohlcv-portfolio-lab` | editable factor source, fixed Portfolio construction and accounting |
| adaptive policy value beyond fixed factor sleeves | `ohlcv-rl-factor-lab` | editable causal encoder, fixed actions/reward/risk, bounded seeds and folds |
| coordinated Factor → Portfolio → optional RL investigation | `ohlcv-research-desk` | multiple Studies in one persistent Project |
| historical volatility, drawdown, and covariance risk of one reported or hypothetical funded book | `ohlcv-book-risk-lab` | fixed Study, no candidate Session |
| caller-authored complete book scenarios or one-leg cash sizing | `ohlcv-book-risk-lab` | fixed bounded authority, no optimizer or Order |
| OHLCV-observable conditional price event | `ohlcv-event-study-lab` | fixed event ledger and references, no candidate Session |
| non-predictive strategic risk-parity allocation | `ohlcv-allocation-lab` | fixed ERC Study and fixed-weight reference, no Factor/RL Session |
| strictly later external-period challenge | frozen holdout flow | one-shot immutable audit, no new selection |

The common Portfolio Core already covers caller-owned asset roles, gross and
per-asset caps, cash, benchmarks, decision cadence, market-clock anchors,
scale-down-only covariance volatility control, drift, no-trade handling,
linear traded-notional cost, capacity diagnostics, contribution accounting,
position lifecycles, and validation/test authority.

## Data and market surfaces proven

The current OHLCV contract has been exercised with:

- aligned adjusted XNYS daily panels;
- calendar-verified XNYS intraday sessions and early closes;
- continuous UTC Crypto bars;
- configurable base intervals;
- causally completed higher intervals such as 3h, 4h, 6h, 12h, and 1d;
- observed-only ragged daily panels;
- observed-only mixed-class intraday panels;
- long-only, short-only, two-sided, and context-only asset roles.

CSV works in the base environment. Parquet and Feather are optional. Provider,
adjustment, observed-calendar, and continuous-series claims remain explicit
input authority rather than facts silently invented by AutoQuant.

## AI operator experience

The primary operator is a coding Agent; the human owns intent, review, and
collaboration.

The current workbench gives that Agent:

- `research.md` for recoverable problem definition and clarification;
- `framework-needs.md` for Project-observed Workbench gaps;
- `aq capabilities` for machine discovery;
- `aq orient` for one verified question with delegated/request-brief/local
  provenance, evidence state, filesystem boundary, and exact next action;
- ordinary pandas factor code instead of a proprietary factor DSL;
- fast deterministic candidate checks before complete evaluation;
- disposable Session worktrees with a declared editable closure;
- bounded Judge, Campaign, fold, seed, turn, and wall-clock execution;
- immutable KEEP/REVERT/CRASH evidence and guarded promotion;
- strict Explorers that independently reconcile artifacts rather than trusting
  presentation JSON;
- a read-only Studio built from the same verified Core loaders;
- files, manifests, Git, Runs, Reports, and Dossiers sufficient for another
  Agent to resume without private chat history.

Fixed research routes correctly expose no editable Session. A negative
experiment is evidence; an invalid input, authority violation, timeout, or
corrupt artifact remains a structured failure.

## Real-request proof

The field-trial program has exercised materially different delegated questions,
not only synthetic fixtures:

| Question family | Durable result |
| --- | --- |
| US mega-cap one-month selection | weak factor evidence was rejected and downstream portfolio work was withheld |
| diversified global ETF allocation | Factor and Portfolio completed; governed RL added no stable incremental value and was rejected |
| hourly BTC timing with multi-interval context | factor evidence survived, but post-cost Portfolio evidence rejected adding BTC and exposed a hard-cap correctness gap that was fixed |
| NVDA/SOXX relative value | exact temporal spread semantics worked; evidence was too weak to proceed |
| reported mega-cap book crowding | component-risk concentration and standardized reduction sensitivity were reproduced cleanly |
| caller-authored TSLA funding alternatives | complete hypothetical books were compared without inventing an optimizer |
| NVDA-to-cash risk reduction and cash-funded entry | exact one-dimensional historical-risk boundaries were solved while preserving every unchanged holding |
| delayed downside-gap reaction | fixed event evidence was produced with explicit overlap, censoring, reference, and uncertainty limits |
| hourly gold with dollar context | mixed-class observed-bar research completed and rejected weak candidate signals |
| global ETF risk parity versus 60/40 | clean fixed ERC Run rejected promotion on validation Sharpe despite materially lower volatility and drawdown |

The canonical results, Run identifiers, versions, and limitations are preserved
in [[docs/trading-request-field-trials]].

## `0.8.20` verification snapshot

- a fresh isolated installed-`aq 0.8.19` Grok Build coworker received a fixed
  eight-stock, SPY-context, one-Experiment Factor → conditional Portfolio
  assignment and no repository source, docs, earlier Project, web, memory, or
  subagent access;
- its checked candidate received Session-objective KEEP, improving validation
  mean rank IC from `-0.119921` to `0.027741`, but validation HAC evidence
  remained weak and the worker correctly started no Portfolio or RL Run;
- strict Report validation rejected its guessed Run-root path and an artifact
  attached to Experiment evidence. This preserved the evidence boundary while
  exposing that the public schema had not described the valid representation;
- `0.8.20` now embeds exact Run and Experiment examples plus kind-specific
  artifact-path constraints in `aq schema report-analysis --json`, and repeats
  the same rule in help, capabilities, orientation, and durable documentation;
- a second clean installed-`aq 0.8.20` worker was limited to exactly one
  `aq report publish` invocation. It discovered the public contract, used
  `artifacts/factor-report.json` for Runs and JSON null for Experiments, and
  published Report
  `report-20260729T190753748783Z-a915f8c8ce36` successfully on its first and
  only attempt;
- that retry improved validation mean rank IC from `-0.119921` to `0.039974`
  but retained validation HAC t-statistic `0.542`, test audit mean rank IC
  `-0.171`, and explicit false scientific/downstream authority. It again
  created two Factor Runs, one Session, one Report, one Factor-only Dossier,
  and no Portfolio or RL evidence;
- independent validation and Studio projection emitted no diagnostics;
- final repository regression: 311/311 tests in 796.165 seconds;
- documentation graph: 1,089/1,089 checked links;
- a fresh Python 3.11 wheel installation reported `aq 0.8.20` and reproduced
  the same capability and executable Schema contract.

## `0.8.19` verification snapshot

- a fresh isolated Grok Build coworker used only installed `aq 0.8.19`, the
  unchanged prior hypothetical-book assignment, and nine raw caller-supplied
  Yahoo CSVs; it did not inspect source, repository docs/tests/plans, prior
  reports, another Project, the web, or memory;
- it preserved `provider.retrievedAt: null`, created Project
  `grok-build-book-risk-drawdown-v0819`, executed fixed Study
  `ohlcv-book-risk` exactly once as Run
  `run-20260729T182310268777Z-51c5e979a05c`, and started no Session;
- without an ad-hoc pandas replacement, strict installed evidence reported
  maximum drawdown `-0.18307858163213264`, peak `2025-10-29`, trough
  `2026-03-30`, and recovery `2026-04-27` from a 253-row primary path;
- the same Run retained annualized volatility `0.207404`, HHI `0.138695`,
  `7.210055` effective risk bets, and NVDA as largest contributor at
  `0.227376`; no optimization, Order, or trading authority appeared;
- independent Project validation, strict Explorer, and Studio projection
  reconciled the same drawdown interval and emitted no diagnostics;
- hand-calculated no-loss, unrecovered, and recovered fixtures plus rehashed
  path tampering and pre-`0.8.19` compatibility tests protect the contract.
- final repository regression: 311/311 tests in 794.604 seconds;
- documentation graph: 1,085/1,085 checked links.

## `0.8.18` verification snapshot

- a fresh Grok Build coworker used only installed `aq 0.8.18`, one unchanged
  English hypothetical-book assignment, and nine caller-supplied raw Yahoo
  OHLCV CSVs; it did not inspect framework source, docs, tests, plans, another
  Project, or the web;
- public schema discovery led it to preserve the unknown original provider
  retrieval time as JSON `null`; no filesystem, coverage, Project, package, or
  current-clock timestamp was substituted;
- the coworker selected fixed `ohlcv-book-risk-lab`, wrote `research.md`
  before quantitative work, started no Session, edited no candidate, and
  executed exactly one successful Run
  `run-20260729T174536010358Z-c388e3a0c03f` in 243 ms;
- the immutable Run reported annualized volatility `0.207404`, component-risk
  HHI `0.138695`, `7.210055` effective risk bets, first-PC share `0.388666`,
  and NVDA as the largest risk contributor at `0.227376`; it granted no
  trading authority;
- Project validation and Studio preserved `provider.retrievedAt: null`
  exactly, and source/package/snapshot/Study/Run hashes remained coherent;
- the worker first passed a package directory and then selected Factor-only
  V4 before recovering to its aligned daily V1 manifest. Final release source
  turns the directory mistake into `dataset.manifest-path-required` and makes
  V1 versus Factor-only V4/V5 compatibility visible in capability/schema/help;
- the worker refused to estimate requested maximum drawdown outside immutable
  evidence. That genuine Book Risk method gap is promoted to
  [[plans/book-risk-drawdown-evidence]] rather than reported as if answered;
- final repository regression: 309/309 tests in 792.276 seconds;
- documentation graph: 1,085/1,085 checked links.

## `0.8.17` verification snapshot

- a fresh Grok Build coworker used only installed `aq 0.8.16`, one unchanged
  English assignment, and nine caller-supplied raw Yahoo OHLCV CSVs; it did not
  inspect framework source, docs, tests, plans, another Project, or the web;
- the coworker independently authored strict intake, selected the Factor-only
  route, established baseline Run
  `run-20260729T164405479135Z-01a9a24550be`, and implemented a
  SPY-relative downside-resilience candidate;
- Check `check-20260729T164527945467Z-fed9c7bfdbb5` exposed that the bounded
  preflight omitted the fixed SPY context/benchmark, forcing a scientifically
  different equal-weight fallback; the later formal Experiment still KEEP
  improved validation mean IC from `-0.115138` to `0.125601`;
- after exact Report publication and promotion, the worker also exposed that
  public language did not make `promoted` versus baseline-retaining
  `completed` sufficiently explicit as mutually exclusive terminal paths;
- a fresh installed `aq 0.8.17` retry reimplemented the relative factor with
  an explicit no-SPY failure and no proxy, then passed first Check
  `check-20260729T170808260744Z-58d2f7e549e6`; its message named bounded
  decision sample AAPL/MSFT, fixed reference SPY, and the 256-timestamp cap;
- the retry spent exactly one Experiment
  `exp-0001-efdb39a4eeb5`, KEEP improved validation mean IC from
  `-0.115138` to `0.158148`, published Report
  `report-20260729T170935463829Z-b39635bfac1a`, promoted once, recognized the
  Session as terminal, and issued no completion command afterward;
- the retry's negative/weak test evidence remained visible audit only and did
  not select the candidate; no Portfolio, RL, Order, or trading authority was
  inferred;
- one further wording observation was folded into the release by labeling the
  names as a bounded decision sample with sampled/full counts; the separate
  unknown-provider-retrieval-time issue remains an explicit intake-contract
  limit;
- final repository regression: 307/307 tests in 816.360 seconds;
- documentation graph: 1,074/1,074 checked links.

## `0.8.16` verification snapshot

- a fresh Grok Build coworker used only installed `aq 0.8.15`, one unchanged
  OpenAlice-style request, and one content-locked V2 hourly package; it did not
  inspect framework source, docs, tests, plans, another Project, or the web;
- public intake independently selected `ohlcv-research-desk` and exposed the
  exact `1h + 3h/4h/6h/12h/1d` panel contract before edit;
- the coworker correctly declared a three-base-bar pullback as
  `cross-sectional-score` and causal completed-12h breadth as
  `timestamp-context`; Check
  `check-20260729T153814029674Z-b87f8d42b5aa` passed;
- Experiment `exp-0001-096c849038b4` REVERTed candidate Run
  `run-20260729T153819638110Z-500559f45737` from baseline validation mean IC
  `0.231579` to `-0.935088`; it did not promote or force Portfolio/RL work;
- the coworker published Report
  `report-20260729T153933853847Z-e334ccf7fb50`, completed the
  baseline-retaining delegated Session, and returned an evidence-backed
  negative conclusion;
- its two low-severity Workbench observations originated
  [[plans/post-trial-session-handoff]];
- a fresh installed `0.8.16` public replay returned
  `trial-review-required` after REVERT with only `session.show` and
  `report.publish` supporting choices, made exact completion primary after
  Report publication, and retained the immutable Experiment/Run/passed-Check
  link after Session completion;
- installed CLI and Studio projected the exact same Work Brief throughout the
  replay.
- final repository regression: 306/306 tests in 886.197 seconds;
- documentation graph: 1,069/1,069 checked links;
- source distribution, wheel build, fresh Python 3.11 install, version and
  capability/schema discovery, clean public-CLI Project replay, Project
  validation, and exact CLI/Studio Work Brief parity passed with `aq 0.8.16`.

## `0.8.15` verification snapshot

- a fresh Grok Build coworker used only an installed `0.8.15` release-candidate
  wheel and a new Project, without inspecting framework source, plans, tests,
  docs, another Project, or the web;
- public discovery led it independently to `ohlcv-portfolio-lab` and exposed
  `baseInterval=1d`, `featureIntervals=[]`, exact OHLCV columns, metadata
  fields, legal roles, and the rule that reusable source declarations do not
  grant absent inputs before any edit;
- the coworker explicitly downgraded its unavailable multi-hour design to the
  caller-authorized daily three-bar pullback rather than inventing data;
- baseline Run `run-20260729T150143539661Z-849d291b9edc` established
  validation net Sharpe `1.761404`; Session
  `session-20260729T150158046040Z-5691848ea6e8` produced one passing Check
  `check-20260729T150219634466Z-de18f4e1a36f` and exactly one Experiment
  `exp-0001-abbd17eaf907`;
- candidate Run `run-20260729T150224250038Z-fbdb39515750` REVERTed at
  validation net Sharpe `-2.0367`; the baseline remained leader and no
  promotion occurred;
- final orientation returned `IN SAMPLE FREEZE READY`, observe mode, null
  primary action, explicit external-evidence guidance, and only read-only
  Session inspection;
- two final low-severity observations tightened interval-authority and
  pre-trial agenda/Session wording without changing immutable research
  evidence;
- final repository regression: 304/304 tests in 907.116 seconds;
- documentation graph: 1,064/1,064 checked links;
- source distribution, wheel build, fresh Python 3.11 install, version,
  capability/schema discovery, clean-root Project validation, default
  orientation, Study inspection, local-override discovery, and exact
  CLI/Studio Work Brief parity passed with `aq 0.8.15`.

## `0.8.14` verification snapshot

- a fresh Grok Build coworker used only an installed `0.8.14` wheel and a new
  Project, without inspecting framework source, plans, tests, docs, or another
  research Project;
- public CLI discovery led it independently to `ohlcv-book-risk-lab` for a
  non-predictive equal-weight four-asset risk audit;
- the coworker executed fixed Study `ohlcv-book-risk` exactly once as Run
  `run-20260729T135618598499Z-a37e9d56fb52`, created no Session, and did not
  enter Factor, Portfolio, RL, or Order lifecycles;
- the verified evidence found component-risk HHI `0.2518`, approximately
  `3.971` effective risk bets, BRAVO as the `27.54%` largest absolute risk
  contributor, and BRAVO as the best standardized one-percentage-point
  cash-funded reduction;
- post-completion orientation had null primary action, explicit Agent-owned
  write/return guidance, and `run.book-risk` as optional supporting read-only
  evidence in JSON, human CLI, ordinary `nextActions`, and Studio;
- agenda and immutable Run input hashes both equal
  `d3b3032338d7673aae5f604e421000bc426966b81c02388a2de0d9d81f0d1685`,
  while the distinct Study input hash remains explicit;
- an independent installed-CLI audit reproduced every handoff/hash assertion,
  counted one Run and zero Sessions, validated the Project, and proved exact
  CLI/Studio Work Brief parity;
- final repository regression: 302/302 tests in 874.499 seconds;
- documentation graph: 1,059/1,059 checked links;
- source distribution, wheel build, fresh Python 3.11 install, version,
  capability discovery, Project validation, orientation, Run inspection, and
  Studio parity passed with `aq 0.8.14`.

## `0.8.13` verification snapshot

- a fresh Grok Build coworker used only an installed `0.8.13` wheel and a new
  `ohlcv-research-desk` Project, without opening framework source or reusing
  another Project;
- orientation recovered its exact `Question (bounded, falsifiable)` section
  with Markdown provenance, and worktree re-entry retained exact canonical
  authority;
- the coworker completed one Factor baseline, one Session, one passing Check,
  one KEEP Experiment, and one guarded promotion;
- Experiment authority explicitly remained `session-objective-only`, with
  false scientific qualification/downstream admission and no trading
  authority;
- the candidate improved validation mean IC from `-0.031325` to `0.471945`,
  but strict evidence found perfect `relative_volume_20` style identity and
  zero style-neutral validation IC;
- post-promotion orientation therefore returned
  `scientific-gate-blocked`, null primary action, and one explicitly optional
  Factor Session; the coworker correctly ran neither Portfolio nor RL and did
  not start a second Factor Session;
- promotion Work Brief, subsequent orientation, and Studio were equal, and
  Project validation passed;
- final repository regression: 301/301 tests;
- documentation graph: 1,052/1,052 checked links;
- source distribution, wheel build, fresh Python 3.11 install, capability
  discovery, immutable Experiment inspection, Project validation, orientation,
  and Studio parity passed with `aq 0.8.13`; `experiment show` repeated the
  same verdict-authority disclosure for replacement Agents.

## `0.8.12` verification snapshot

- a fresh `0.8.11` Grok coworker followed the advertised Session
  `operatingRoot`, reproduced `validation.failed / dataset.directory`, safely
  fell back to canonical commands, and completed one Check plus one REVERT;
- a second fresh Grok coworker used only an installed `0.8.12` wheel, entered
  the exact worktree before opening candidate source, and received the same
  canonical Agent Work Brief as Project-root orientation while `data/ohlcv`
  remained absent;
- that retry completed one passing Check, one KEEP Experiment, one guarded
  promotion, Project validation, and Studio projection with no second
  Experiment or framework-source access;
- marker tests reject detached copies, forged identities, removed markers,
  changed locks, and symlinks; the marker remains fixed even if an editable
  pattern would otherwise match it;
- successful promotion now returns the same post-mutation actions as
  orientation and Studio instead of requesting a redundant baseline Run;
- final repository regression: 299/299 tests;
- documentation graph: 1,048/1,048 checked links;
- source distribution, wheel build, fresh Python 3.11 install, empty
  Workspace, Factor Project, baseline, worktree/canonical orientation parity,
  absent copied data, passing Check, KEEP, guarded promotion,
  post-promotion action equality, validation, and Studio passed with Harness
  `0.8.12`, `commit: unavailable`, and `dirty: false`.

## `0.8.11` verification snapshot

- the first fresh Grok Build coworker completed one Factor baseline, one
  passing Check, one KEEP Experiment, and one guarded promotion, and exposed
  the contradictory post-KEEP edit-versus-promote orientation;
- an independent replay reproduced the defect, then a second fresh Grok retry
  under Agent Work Brief v6 received `session.promote` as its sole primary
  action with only `promotion-ready`, no supporting action, and no second
  Experiment;
- focused tests preserve newer-candidate check/evaluate priority and require
  an exact current Report plus `--report` before delegated promotion;
- the same retry exposed a dropped candidate-Check pointer; exact-identity
  handoff now retains that passing Check through promotion-ready and
  report-required states;
- final repository regression: 296/296 tests;
- documentation graph: 1,048/1,048 checked links;
- source distribution, wheel build, fresh Python 3.11 install, empty
  Workspace, Factor Project, baseline, Session edit, passing Check, KEEP,
  promotion-first human/JSON orientation, guarded promotion, Project
  validation, and Studio projection passed with Harness `0.8.11`,
  `commit: unavailable`, and `dirty: false`;
- Session worktree CLI re-entry was deliberately split into
  [[plans/session-worktree-cli-reentry]] rather than copying or symlinking
  content-locked datasets into disposable worktrees.

## `0.8.10` verification snapshot

- an independent fresh Grok Build coworker created a fixed Event Study Project
  and, before opening any request, policy, Study, Judge, or research file,
  recovered the exact question from `aq orient` with
  `origin: project-request`, both source paths, an empty editable closure, no
  trading authority, and the correct baseline action;
- that retry completed exactly one successful Event Study Run and zero
  Sessions; independent validation, strict Explorer, post-Run orientation, and
  Studio reproduced the same request, Run, four-event primary population, and
  descriptive no-trading conclusion;
- strict request binding is deterministically covered for Allocation, Book
  Risk, and Event Study templates, plus delegated precedence, exact `Question`
  fallback, invalid, tampered, symlinked, and unbound refusal;
- final repository regression: 293/293 tests;
- documentation graph: 1,038/1,038 checked links;
- source distribution, wheel build, fresh Python 3.11 install, empty Workspace,
  fixed Event Project construction, pre-Run request orientation, one installed
  Run, strict Explorer, and Studio projection passed with Harness `0.8.10`,
  `commit: unavailable`, and `dirty: false`;
- no Study, Judge, dataset, evaluation semantic, or historical immutable Run
  changed.

## `0.8.9` verification snapshot

- independent Grok Build retry created a fresh Project, wrote its English
  brief, and verified exact `project-research-brief` question provenance before
  any Run existed;
- the same retry completed exactly one bounded synthetic Factor baseline, with
  one Run, zero Sessions, unchanged candidate bytes, and matching CLI/Studio
  orientation;
- delegated-request precedence, explicit-heading extraction, fenced-heading
  exclusion, bounded content, safe fallback, human CLI compaction, and Studio
  parity have deterministic regression coverage;
- final repository regression: 289/289 tests;
- documentation graph: 1,033/1,033 checked links;
- source distribution, wheel build, fresh Python 3.11 install, empty Workspace,
  Project construction, orientation/Studio parity, and one installed-wheel
  Factor Run passed with Harness `0.8.9` and `dirty: false`;
- no Study, Judge, dataset, evaluation semantic, or historical immutable Run
  changed.

## `0.8.8` verification snapshot

- final repository regression: 286/286 tests;
- documentation graph: 1,029/1,029 checked links;
- source distribution and wheel build succeeded;
- installed-wheel smoke verified version/capabilities, empty Workspace
  initialization, packaged Project templates, and validation;
- committed sample evidence verified three Studies, zero Sessions, one
  immutable historical `0.8.7` Run, and strict Factor Explorer projection;
- a no-hardlink clean clone contained the fixed OHLCV bytes and empty Session
  directory, resolved the internal default Project, validated and oriented
  from `.`, and produced a valid Studio snapshot;
- local-override tests covered relative and absolute external Projects,
  strict/invalid configuration, missing paths, symlinks, wrong defaults, and
  write-through without base-manifest mutation.

## `0.8.7` verification snapshot

- final repository regression: 277/277 tests;
- documentation graph: 1,014/1,014 checked links;
- source distribution and wheel build succeeded;
- wheel contents included templates, fixed Judges, strict Explorers, and Studio
  assets;
- clean real-data allocation replay: 4,922 sessions, nine ETFs, 16,458 ms,
  `dirty: false`;
- CLI validation, strict allocation Explorer, Agent orientation, and Studio
  snapshot reconciled the same Run;
- repository `main` and tag `v0.8.7` were pushed cleanly.

These numbers are an archival release proof, not a promise that future releases
will retain the same test count or implementation shape.

## Honest boundary

AutoQuant is not a broker, live account, OMS, universal backtesting SDK, hosted
data service, or catalogue of every quantitative method.

It does not own:

- broker credentials, authenticated positions, approvals, tax lots, margin,
  borrow, venue capability, live reconciliation, or order submission;
- silent data acquisition or authentication of provider adjustment, roll,
  survivorship, corporate-action, or labelled-event semantics;
- arbitrary optimizers, every ML model, high-frequency order-book simulation,
  or a universal asset DSL;
- the final execution conversation between current account state, user intent,
  and live venue constraints.

Those boundaries are deliberate. In OpenAlice, UTA and the investment-research
conversation can consume AutoQuant evidence without moving live-trading
authority into the quant desk.

## Known product gaps

The workbench is usable, but several product layers remain intentionally
unfinished:

- the first-class method catalogue is still narrow; general supervised ML,
  richer portfolio constructors, clustering/HRP, probabilistic models, and
  other methods should be added only when real Projects justify them;
- external OHLCV acquisition and dataset-package preparation still require
  engineering judgment outside the atomic intake command;
- Studio is a verified observation surface, not a full interactive research
  authoring or orchestration UI;
- OpenAlice still needs the host-side path that selects an AutoQuant version,
  materializes or discovers the desk, delegates work, waits for completion,
  and returns selected evidence;
- fixed Studies, Session Reports, and multi-lane Dossiers do not yet collapse
  into one universal outward-deliverable type.

None of these gaps prevents standalone research or an Agent from returning an
ordinary evidence-backed report. They define the next integration and
field-trial surface.

## Maturity and next use

`0.8.18` is suitable for controlled standalone use and initial OpenAlice desk
integration. It is still pre-`1.0`: public contracts are versioned and strict,
but the project continues to prefer domain correctness and Agent operability
over backward compatibility while the product shape settles.

The next useful work should come from new real assignments and their
Project-local `framework-needs.md`, not from adding speculative framework
surface merely to resemble older quantitative platforms.
