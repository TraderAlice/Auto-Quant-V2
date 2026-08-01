# AutoQuant V2 current status

Status: `v0.9.26` is the current AutoQuant release and `v0.8.31` remains the
Harness currently consumed by OpenAlice until the host deliberately selects a
newer tag.

Updated: 2026-08-02.

Related: [[README]], [[docs/CHANGELOG]], [[docs/ARCHITECTURE]],
[[docs/design/agent-native-quant-workbench]],
[[docs/trading-request-field-trials]],
[[docs/agent-employability-validation]], and [[PLANS]].

This document describes only the current checkout's tested capability and
honest boundary. Concise release history lives in [[docs/CHANGELOG]]; exact
historical proof remains in completed plans and immutable Git tags.

## Current milestone

The `0.9.26` candidate closes the provenance gap that appears when one
cross-market Factor question needs assets from distinct providers. V6 retains
V5's exact completed-close, observed-only, absent-no-fill, one-target semantics
while replacing one synthetic top-level provider with an ordered vector of
content-addressed source packages. Every asset freezes its exact source id;
every source retains its own provider claim.

The public packaging Skill now composes at least two complete, compatible,
disjoint strict V5 packages transactionally. It copies every CSV, Parquet, or
Feather byte unchanged and emits a composition audit binding source manifests,
providers, assets, hashes, rows, timestamps, and preservation claims. It never
subsets, aligns, fills, transforms, converts adjustment, or resolves duplicate
symbols. Drift, unsafe paths, symlinks, conflicting authority, duplicate
identity, provider ambiguity, or an occupied output fail without partial V6
state.

Deterministic evidence passes V5 → V6 → JSON Schema and independent
package audit → strict Factor intake → CLI → Run → Factor Explorer → immutable
Report → Studio, plus rehashed snapshot-tamper rejection. Generated Workspace
Skills disclose the same route without requiring Core inspection. A fresh
installed-wheel Grok coworker independently materialized Nasdaq V4 to V5,
composed distinct Yahoo and Nasdaq V5 sources into V6, confirmed the public
ragged observed-only Candidate Contract, produced exactly one causal Factor
Run and one evidence-bound Report, and stopped on an unsupported result. The
full 439-test regression and final packaging audit pass; exact proof is retained
in [[plans/multi-source-observed-factor-packaging]].

The published `v0.9.25` baseline already materializes exact scheduled daily
closes from strict date-only V4 plus explicit exchange-calendar authority. V5
accepts observed bars through `1d`, retains timezone-aware UTC close claims,
ragged absent-no-fill rows, per-asset class and volume semantics, one explicit
temporal target, and a horizon advancing only on that target's observed bars.

Candidate code must express asynchronous context through an explicit causal
backward as-of operation. Core never manufactures a common calendar or implicit
fill. Factor availability distinguishes the complete source panel from the
target evaluation timeline, and deterministic Toyota/SPY evidence proves that
a Tokyo decision cannot see the later same-date New York close.

The root sample preserves fifteen historical Runs without rewriting old
results and now projects a clean `0.9.26` Factor Run bound to candidate commit
`3cd8cd9`. OpenAlice remains independently pinned to `v0.8.31`.

## What works today

| Research need | Current route | Lifecycle |
| --- | --- | --- |
| cross-sectional or temporal factor research | `ohlcv-factor-lab` | editable candidate, bounded Session, validation-only selection |
| factor-to-target portfolio research | `ohlcv-portfolio-lab` | editable factor source, fixed construction and accounting |
| adaptive policy value beyond fixed factor sleeves | `ohlcv-rl-factor-lab` | editable causal encoder, fixed actions/reward/risk, bounded seeds and folds |
| coordinated Factor → Portfolio → optional RL investigation | `ohlcv-research-desk` | multiple Studies in one persistent Project |
| historical volatility, drawdown, and covariance risk of one reported or hypothetical funded book | `ohlcv-book-risk-lab` | fixed Study, no candidate Session |
| caller-authored complete book scenarios or one-leg cash sizing | `ohlcv-book-risk-lab` | fixed bounded authority, no optimizer or Order |
| OHLCV-observable conditional price event | `ohlcv-event-study-lab` | fixed event ledger and references, no candidate Session |
| non-predictive strategic risk-parity allocation | `ohlcv-allocation-lab` | fixed ERC Study and fixed-weight reference, no Factor/RL Session |
| strictly later external-period challenge | frozen holdout flow | one-shot immutable audit, no new selection |

The common Portfolio Core covers caller-owned asset roles, gross and per-asset
caps, cash, benchmarks, decision cadence, market-clock anchors,
scale-down-only covariance volatility control, drift, no-trade handling,
linear traded-notional cost, capacity diagnostics, contribution accounting,
position lifecycles, and validation/test authority.

## Data and market surfaces proven

The current OHLCV contracts have been exercised with:

- aligned adjusted XNYS daily panels;
- calendar-verified XNYS intraday sessions and early closes;
- continuous UTC Crypto bars;
- configurable base intervals and causally completed higher intervals;
- observed-only ragged daily and mixed-class intraday panels;
- exact close-time asynchronous cross-market daily panels;
- exact per-asset provider provenance across compatible V5 source packages;
- long-only, short-only, two-sided, and context-only asset roles.

CSV works in the base environment. Parquet and Feather are optional. Provider,
adjustment, observed-calendar, close-time, continuous-series, and event-label
claims remain explicit input authority rather than facts silently invented by
AutoQuant.

## AI operator experience

The primary operator is a coding Agent; the human owns intent, review, and
collaboration. The workbench supplies:

- recoverable English `research.md` problem definition and clarification;
- Project-local `framework-needs.md` for reusable Workbench gaps;
- machine-readable capability, schema, orientation, and exact-next-action
  discovery;
- ordinary pandas factor code rather than a proprietary factor DSL;
- deterministic preflight before complete evaluation;
- disposable Session worktrees with a declared editable closure;
- bounded Judge, Campaign, fold, seed, turn, and wall-clock execution;
- immutable KEEP/REVERT/CRASH evidence and guarded promotion;
- strict Explorers that independently reconcile artifacts;
- one read-only Studio projection over the same verified Core loaders;
- durable files, manifests, Git, Runs, Reports, Reviews, and Dossiers that let
  another Agent resume without private chat history.

Fixed research routes expose no fictional editable Session. A negative result
is evidence; invalid input, authority violation, timeout, or corrupt artifact
remains a structured failure.

## Real-request proof

Field trials cover materially different delegated questions: U.S. selection,
global allocation, hourly crypto timing, relative value, reported-book risk,
hypothetical funding alternatives, fixed price events, mixed-class Factors,
cross-market acquisition, persistent-Project follow-ups, independent Review,
frozen holdout, and clarification-first delegation.

The canonical results, Run identifiers, versions, and limitations are preserved
in [[docs/trading-request-field-trials]]. The methodology for judging whether a
fresh coworker was actually employable is in
[[docs/agent-employability-validation]].

## Honest boundary

AutoQuant is not a broker, live account, OMS, universal backtesting SDK, hosted
data service, or catalogue of every quantitative method. It does not own:

- broker credentials, authenticated positions, approvals, tax lots, margin,
  borrow, venue capability, live reconciliation, or order submission;
- silent data acquisition or authentication of provider adjustment, roll,
  survivorship, corporate-action, calendar, or labelled-event semantics;
- arbitrary optimizers, every ML model, high-frequency order-book simulation,
  or a universal asset DSL;
- the final execution conversation between current account state, user intent,
  and live venue constraints.

In OpenAlice, UTA and the investment-research conversation can consume
AutoQuant evidence without moving live-trading authority into the quant desk.

## Known product gaps

- The first-class method catalogue remains intentionally narrow; general
  supervised ML, richer portfolio constructors, clustering/HRP, probabilistic
  models, and other methods should follow demonstrated research demand.
- External OHLCV acquisition and package preparation still require Agent
  judgment. The public Skill now covers one observed daily close-time
  materialization route without turning Core into a downloader.
- Studio is a verified observation surface, not a full interactive research
  authoring or orchestration UI.
- OpenAlice remains deliberately pinned to `0.8.31`; host-side adoption of a
  later release is independent of package publication.
- Fixed Studies, Session Reports, and multi-lane Dossiers do not collapse into
  one universal outward-deliverable type.

## Next use

Continue driving `0.9.x` from bounded real assignments and Project-local
`framework-needs.md`. Prefer correctness and Agent operability over speculative
surface or pre-1.0 compatibility; [[PLANS]] owns the next active item when one
is selected.
