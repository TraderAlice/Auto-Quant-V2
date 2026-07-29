# AutoQuant V2 current status

Status: usable pre-alpha at `0.8.15`.

Updated: 2026-07-29.

Related: [[README]], [[docs/ARCHITECTURE]],
[[docs/design/agent-native-quant-workbench]],
[[docs/trading-request-field-trials]], and [[PLANS]].

## Milestone

AutoQuant V2 has crossed the line from an architectural prototype into a
usable Agent-native quantitative research workbench.

At `0.8.15`, a human, local coding Agent, or coworker delegated from OpenAlice
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
Studies plus one explicitly historical clean `0.8.7` Factor Run for immediate
Studio inspection. An ignored strict local Workspace configuration lets
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

The latest annotated release tag is `v0.8.15`; `v0.8.14` remains the
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

## What works today

| Research need | Current route | Lifecycle |
| --- | --- | --- |
| cross-sectional or temporal factor research | `ohlcv-factor-lab` | editable candidate, bounded Session, validation-only selection |
| factor-to-target portfolio research | `ohlcv-portfolio-lab` | editable factor source, fixed Portfolio construction and accounting |
| adaptive policy value beyond fixed factor sleeves | `ohlcv-rl-factor-lab` | editable causal encoder, fixed actions/reward/risk, bounded seeds and folds |
| coordinated Factor → Portfolio → optional RL investigation | `ohlcv-research-desk` | multiple Studies in one persistent Project |
| historical risk of one reported or hypothetical funded book | `ohlcv-book-risk-lab` | fixed Study, no candidate Session |
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

`0.8.15` is suitable for controlled standalone use and initial OpenAlice desk
integration. It is still pre-`1.0`: public contracts are versioned and strict,
but the project continues to prefer domain correctness and Agent operability
over backward compatibility while the product shape settles.

The next useful work should come from new real assignments and their
Project-local `framework-needs.md`, not from adding speculative framework
surface merely to resemble older quantitative platforms.
