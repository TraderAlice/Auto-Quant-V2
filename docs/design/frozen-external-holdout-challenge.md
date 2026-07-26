# Frozen external holdout challenge

Status: V1 implemented.

Related: [[docs/design/research-selection-integrity]],
[[docs/design/evidence-driven-research-agenda]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/program-research-dossiers]],
[[docs/design/study-run-evidence]], and
[[docs/design/quant-research-lifecycle]].

## Purpose

A positive validation result is not the end of research. After an Agent has
iterated against validation and repeatedly seen the Project's visible test
audit, the next credible question is whether the exact frozen research object
survives a later period that did not participate in those choices.

AutoQuant V1 already states that requirement but has no governed operation for
it. The external holdout challenge makes it a real Core object. It is not a
new strategy-search Project and not a live-trading approval.

## Lifecycle

```text
Source Project
  current immutable Dossier
  exact leader Run source closures
             │
             │ aq holdout bind
             ▼
Target Project
  new compatible intake
  strictly later dataset
  no Runs / Sessions / Reports
  imported frozen candidate sources
  immutable holdout binding
             │
             │ aq holdout run
             ▼
  existing fixed Judges execute once
  immutable per-lane Runs
  immutable holdout result
```

The target is created through ordinary `aq project intake`; binding never
downloads data or creates a Project implicitly.

## Source authority

Binding accepts one source Project and one current completed Dossier. Core
loads and verifies the Dossier against its Reports and leader Runs. Included
lanes determine the challenge:

- Factor imports the exact frozen `factors/**` bytes from the Factor leader
  Run.
- Portfolio must name the same factor source identity as Factor. It receives
  no independent mutable copy.
- Governed RL, when included, imports exact frozen `models/**` bytes from the
  RL leader Run and requires the same frozen factor dependency.

The target binding stores a portable projection of source Dossier identity,
source dataset identity, per-lane Run/result/source/dependency hashes, and the
exact imported bytes with hashes. Later verification does not depend on the
source Project remaining mounted.

## Target compatibility

V1 fails closed unless:

- target template is the coordinated `ohlcv-research-desk`;
- target request is byte-equivalent to the source request;
- target asset class, universe, base interval, feature intervals, timestamp
  semantics, market clock, calendar, timezone, and aggregation contract match;
- target dataset starts strictly after the source dataset ends;
- dataset id/version/hash differ;
- the target has no Runs, Sessions, Reports, Dossiers, or prior binding;
- expected Factor/Portfolio and optional RL Study/Judge authority is current.

The exact-universe rule makes V1 a temporal stability challenge. Cross-universe
transfer, universe drift, and mixed-calendar research need different
interpretation and remain separate work.

## Frozen behavior

After binding:

- editable source files are operationally frozen even though existing Study
  identity still calls them the subject source closure;
- `session start`, external Campaign creation, promotion, and candidate
  preflight/evaluation are unavailable;
- ordinary Project validation and read-only exploration remain available;
- any source, request, dataset, Study, Judge, dependency, or binding mutation
  invalidates the challenge before a Run starts.

The generic Run primitive remains the underlying evidence publisher, but the
public holdout operation owns the permitted lane set and one-shot result.
Repeated invocation returns the verified terminal result; it never creates a
new trial.

## Result

The immutable result records:

- source Dossier and request identity;
- source and target dataset identity and non-overlap proof;
- binding hash and per-lane source/holdout Harness identity;
- for each lane, source Run/result/source identity, holdout Run/result/input
  identity, objective value and delta;
- terminal lane status and errors;
- authority:
  `evaluationRole=external-temporal-audit`,
  `candidateFrozen=true`,
  `selectionAllowed=false`,
  `automaticPromotion=false`,
  `tradingAuthority=none`.

Core does not manufacture a universal pass threshold. Factor IC, Portfolio
Sharpe, and RL aggregate objectives have different uncertainty and baseline
semantics. Existing lane diagnostics remain the evidence; the holdout result
compares the predeclared objective and labels the outcome, but final
interpretation belongs in a later report/Dossier or the requesting OpenAlice
workbench.

## OpenAlice boundary

OpenAlice supplies the later dataset and target Project identity, then receives
the immutable challenge result as quantitative decision support. AutoQuant
does not authenticate the caller, place an order, choose position size in a
live account, or treat external-period survival as permission to trade.

## Compatibility

Existing Projects, Runs, Reports, and Dossiers without holdout state remain
unchanged. A target becomes governed only when the binding file exists.
Malformed or partially written bindings/results are structured validation
failures, never silently ignored.

## Known limits

- V1 is a same-request, same-universe, strictly later-period challenge.
- There is no hidden test server, encryption, or one-time secret reveal.
- Provider/corporate-action/point-in-time-universe truth remains caller
  authority.
- Cross-Project Report and model registries beyond this narrow Dossier import
  remain future work.
