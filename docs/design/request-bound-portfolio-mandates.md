# Request-bound Portfolio Mandates

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/signal-policy-and-attribution]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/program-research-dossiers]].

## Scope

This document owns the fixed position contract that connects a delegated
Research Request to Portfolio and governed-RL evidence. It separates the
assets a caller authorized AutoQuant to model as positions from the wider
research universe used for cross-sectional context.

It does not grant live-trading authority, infer hedges, choose leverage,
optimize arbitrary constraints, place orders, or mutate OpenAlice UTA state.

## Project contract

Every newly constructed Portfolio or governed-RL Project contains:

```text
strategies/
└── portfolio-mandate.json
```

The strict `autoquant-portfolio-mandate` records:

- a content-derived mandate id;
- whether it came from a normalized Research Request or a synthetic template;
- the exact request hash and requested direction;
- research, tradable, and context-only asset sets;
- construction family, gross limit, net rule, per-asset cap, cash permission,
  short permission, and benchmark;
- `quantitative-decision-support` authority and `tradingAuthority: none`.

The file is a fixed Study dependency, not candidate-editable source and not
Judge source. Its bytes enter Study, Run, and Session identity. Portfolio and
RL Studies in one canonical Research Desk depend on the same exact file.

Historical Projects whose copied Studies predate this dependency remain
loadable. Their verified evidence is explicitly projected as legacy implicit
research-neutral behavior; it is never reinterpreted as request-bound.

## Request mapping

Core derives one deterministic contract from the normalized request:

| Request direction | Tradable assets | Family | Net rule | Benchmark |
| --- | --- | --- | --- | --- |
| `long` | requested assets only | `long-cash` | long-only | equal-weight long requested assets |
| `short` | requested assets only | `short-cash` | short-only | equal-weight short requested assets |
| `long-short` | requested assets only | dollar-neutral | zero | cash |
| `relative-value` | requested assets only | dollar-neutral | zero | cash |
| `research-only` | complete research universe | dollar-neutral | zero | equal-weight long research universe |

Synthetic templates have no caller request. They declare a
`template-default` `research-only` mandate over the complete fixture universe
so the historical reference benchmark remains explicit.

Requested assets are intentionally conservative authorization. Other dataset
assets may improve ranking, regime, style, or benchmark context, but they
cannot become positions or implicit hedges without caller intent.

## Mechanical construction

All families share the same causal percentile, hysteresis, conviction,
inverse-volatility strength, per-asset cap, drift, no-trade band, and
next-bar accounting.

Directional families modify only permitted position state and budget:

- `long-cash` can enter, hold, and exit long intent; it never enters short;
- `short-cash` can enter, hold, and exit short intent; it never enters long;
- unused gross budget remains cash when signals or the per-asset cap cannot
  use it;
- context-only assets always have flat intent, zero target, and
  `allocation_status=context_only`.

Dollar-neutral families require exact funded long and short sides under the
fixed gross/net/cap rules. Insufficient requested breadth remains flat and
fails the active-target audit visibly rather than changing exposure.

The daily accounting path records `cash_weight = 1 - gross_exposure`. This is
the unused research gross budget, not a Broker cash-balance claim.

## Governed RL

Every fixed factor action and factor mixture is first converted into a
complete stateful sleeve under the same Portfolio Mandate. RL selects among
those sleeves; it cannot:

- trade a context-only asset;
- take a sign forbidden by the request;
- change cash, gross, net, or cap semantics;
- substitute a different benchmark;
- learn around a failed mandate constraint.

The RL Study separately depends on both `factors/**` and the mandate. Program
and Dossier compatibility compare the Factor subset of the dependency closure
to the Factor lane source, while separately requiring Portfolio and RL
mandate ids to match.

## Evidence projection

Successful Portfolio and RL Runs freeze the complete normalized mandate under
`metrics.portfolio_mandate`. Portfolio reports and decision ledgers also
record its identity and per-asset tradability.

Core projections expose:

- direction and construction family;
- authorized and context-only assets;
- gross limit, per-asset cap, cash, short, and benchmark semantics;
- constraint errors for gross, net rule, opposite-sign exposure,
  context-only exposure, and maximum weight;
- current gross, net, and unused cash budget;
- the exact fixed dependency hash.

CLI, Studio, lane Reports, and Project Dossiers consume those verified
objects. Studio may format the mandate and dim context-only rows, but it
cannot infer or alter a position permission.

## Identity and tamper behavior

For a request-driven Project, intake reconstructs the expected mandate from
the canonical request plus dataset universe on every load. A changed request,
asset partition, construction field, or derived id is invalid evidence.

The mandate's content-derived id is a readable join key, not a substitute for
the Study dependency file hash. Runs and Sessions retain the complete hash
inventory.

## Invariants

1. Research-universe membership does not imply position authorization.
2. Directional mandates never take the opposite sign and may retain cash.
3. Context-only assets always have zero target and executed exposure.
4. Relative-value and long-short evidence cannot silently relax zero net.
5. Portfolio and governed RL use the same exact mandate in one Project.
6. Candidate factor/model code cannot edit or choose the mandate.
7. Benchmarks follow the declared position question.
8. Every surface discloses that weights are historical research evidence with
   no trading authority.
9. Historical implicit-neutral evidence remains loadable and labelled legacy.

## Known limits

- V1 fixes gross limit `1.0`, per-asset cap `0.30`, and cash permission.
- The request does not yet express named hedge assets, sector bounds,
  covariance budgets, borrow availability, futures margin, or leverage.
- Cash is an unused-gross-budget field, not financing or collateral
  accounting.
- Position permissions are Project-local and do not represent OpenAlice
  account authorization.
