# Request-driven research intake and OHLCV dataset snapshots

Status: V1 aligned daily, V2 continuous-1h, V3 configurable/session, and V4
observed-only daily Factor intake implemented.

Related: [[docs/ARCHITECTURE]], [[docs/CLI]], [[docs/PROJECT_FORMAT]],
[[docs/STUDIO]], [[docs/design/workspace-project-boundaries]],
[[docs/design/study-run-evidence]],
[[docs/design/request-bound-portfolio-mandates]],
[[docs/design/caller-owned-portfolio-research-policy]],
[[docs/design/request-bound-research-horizon]],
[[docs/design/portfolio-risk-governor]], and
[[docs/design/quant-research-lifecycle]], and
[[docs/design/causal-multi-interval-factor-inputs]].

## Scope

This document owns the boundary that turns a strict delegated Research Request
and caller-supplied market-data package into one self-contained AutoQuant
Project. It covers package semantics, normalization, provenance, content
identity, transactional construction, CLI discovery, and pre-Session Studio
observation.

It does not fetch market data, authenticate provider claims, compute corporate
actions, create live subscriptions, start an autonomous Campaign, or deliver
the result through an optional host.

## Before strict intake

An external assignment may arrive as ordinary conversation in any language.
Before this document's machine intake boundary applies, the Quant Agent creates
or continues a Project and maintains an English Project-root `research.md`.
The Agent clarifies material caller-owned intent until the decision, question,
scope, horizon, constraints, evaluation meaning, and deliverable are bounded
and testable.

The strict Research Request is a later derived execution contract. It freezes
the understood inputs used by Studies, Sessions, Runs, Reports, and Dossiers;
it is not the user-facing submission format and does not replace the Markdown
brief. `aq project intake` is therefore an atomic fast path when the clarified
request and compatible data package already exist, not an automatic
natural-language classifier.

## Authoritative locations

- Package validation, normalization, snapshot materialization, and intake
  verification: `autoquant/intake.py`
- Completed-bar aggregation, reconciliation, and causal alignment:
  `autoquant/intervals.py`
- Transactional Project construction: `autoquant/workspace.py` and
  `autoquant/templates.py`
- Public command/schema/capability projection: `autoquant/cli.py` and
  `autoquant/capabilities.py`
- Read-only observation: `autoquant/studio.py` and
  `autoquant/studio_assets/`
- Deterministic contract tests: `tests/test_intake.py` and
  `tests/test_cli.py`
- Request-derived position authority: `autoquant/mandates.py`

## External package

V1 accepts one JSON package manifest and its relative source files:

```json
{
  "schemaVersion": 1,
  "kind": "autoquant-ohlcv-dataset-package",
  "id": "us-mega-cap-daily",
  "version": "2026-07-22",
  "assetClass": "equity",
  "frequency": "1d",
  "market": {
    "clock": "session",
    "calendar": "XNYS",
    "timezone": "America/New_York"
  },
  "priceAdjustment": "provider-adjusted",
  "provider": {
    "name": "yahoo-finance",
    "retrievedAt": "2026-07-23T00:00:00Z",
    "sourceUri": "https://finance.yahoo.com/",
    "terms": "provider terms apply"
  },
  "assets": [
    {
      "symbol": "AAPL",
      "venue": "XNAS",
      "currency": "USD",
      "path": "AAPL.csv"
    }
  ]
}
```

The manifest is caller-supplied context. Provider, adjustment, venue, calendar,
and terms fields are preserved and hashed but are not authenticated by
AutoQuant.

V1 deliberately supports only `1d` session data. Factor, Portfolio, and RL
annualize that clock at 252 and consume one aligned daily panel.

V2 accepts a strict continuous UTC base instead:

```json
{
  "schemaVersion": 2,
  "kind": "autoquant-ohlcv-dataset-package",
  "id": "crypto-hourly",
  "version": "2026-07-26",
  "assetClass": "crypto",
  "baseInterval": "1h",
  "featureIntervals": ["3h", "4h", "6h", "12h", "1d"],
  "timestampSemantics": "bar-close",
  "aggregation": {
    "method": "complete-utc-midnight-bar-close-v1",
    "anchor": "00:00"
  },
  "market": {
    "clock": "continuous",
    "calendar": "24/7",
    "timezone": "UTC"
  }
}
```

V2 asset/provider/adjustment fields are the same as V1. Each asset path names
the one authoritative 1h file; AutoQuant derives every declared higher
interval from it.

V3 keeps that package shape, adds `terminalBucketPolicy`, permits bounded
configurable base intervals, and supports either continuous UTC or XNYS
regular-session authority. The exact XNYS calendar, DST, early-close, and
terminal partial-bar contract is in
[[docs/design/configurable-session-interval-inputs]].

V4 keeps the V1 daily asset/provider shape but explicitly changes panel
authority:

```json
{
  "schemaVersion": 4,
  "kind": "autoquant-ohlcv-dataset-package",
  "frequency": "1d",
  "panelPolicy": {
    "alignment": "observed-only",
    "missingObservation": "absent-no-fill"
  }
}
```

V4 is accepted only by the Factor template. Each asset keeps its own observed
dates and listing-history start; there is no forward/back fill and no global
timestamp intersection. Portfolio and governed RL fail explicitly because
their accounting/state contracts do not yet define changing-universe
semantics. V1 remains exact and aligned rather than silently acquiring a new
meaning.

## Validation and normalization

Before any Project is visible, Core:

1. validates strict manifest and Research Request schemas;
2. confines every asset path beneath the package directory and rejects
   symlinks, duplicates, and unsafe symbols;
3. reads CSV, Parquet, or Feather;
4. for V1/V4, accepts a conventional timestamp alias, requires finite positive
   daily OHLCV and no weekend session rows, then orders canonical output;
5. for V2/V3, requires explicit timezone-aware base-bar-close timestamps,
   exact UTC-hour boundaries, consecutive rows with no gaps, strict OHLCV
   geometry, and complete UTC-midnight-anchored aggregation groups;
6. requires every asset to share the exact base timestamp panel for V1–V3;
   V4 instead requires at least 120 observations per asset, at least four
   observed assets on enough union timestamps for each requested horizon, and
   records the complete observed-only availability surface;
7. enforces template-specific breadth and history floors;
8. requires each requested asset and non-null venue to exist in the package
   and requires the request's single asset class to equal the package class;
9. derives the request's exact numerical Horizon Mandate and rejects a largest
   diagnostic target that leaves fewer than 20 purged rows in any split.

Canonical Project data uses:

```text
timestamp,open,high,low,close,volume
```

with one `YYYY-MM-DD` row per session and one `<symbol>.csv` per asset. There is
no implicit forward fill, timestamp intersection, survivorship repair, or
corporate-action transformation.

For V4, `snapshot.json` additionally freezes the exact panel policy, union and
complete timestamp counts, observed/possible rows, observation coverage, and
minimum/median/maximum assets per timestamp. Every asset records its own
observed start, end, and row count. Load-time validation recomputes these facts
from normalized bytes.

V2 uses `data/ohlcv/<interval>/<symbol>.csv`. The fixed loader recomputes every
materialized 3h/4h/6h/12h/1d file from 1h bytes and rejects a mismatch even if
the derived file and snapshot hashes were both rewritten. It then exposes the
base columns plus `bar_close__<interval>`, namespaced OHLCV, and
`age_bars__<interval>` through the ordinary complete-universe
`compute_factor(panel)` pandas API. Backward-as-of alignment permits only
source closes at or before the decision close. See
[[docs/design/panel-native-factor-api]].

## Snapshot and identity

The resulting `data/ohlcv/snapshot.json` records:

- package id, version, class, clock/interval surface, market, adjustment, and
  provider;
- request hash and requested assets;
- exact research universe and common time range;
- source path/hash and normalized interval path/hash for every asset;
- observations and coverage for every asset and materialized interval;
- template and fixed Study id.

The Study declares `ohlcv/**`, so canonical CSV, snapshot, and README bytes all
enter `datasetHash`, Run identity, Session locks, and Reports. Editing any one
creates a different Study/Run identity and stales an existing Session.

Portfolio and governed-RL intake also writes the strict fixed
`strategies/portfolio-mandate.json`. Core derives it from the exact normalized
request and dataset universe: direction supplies the default role for
requested assets, or one complete caller role vector marks each requested
asset long-only, short-only, two-sided, or context-only. Remaining dataset
assets are context-only. Core derives the construction family, gross-side
limits, and a role-aware default benchmark. If the canonical request contains
`portfolioPolicy`, the same derivation locks its gross, global fallback and
named requested-asset caps, volatility ceiling, linear cost, no-trade band,
reference NAV, and ordinary Portfolio/RL decision cadence; otherwise it
records documented reference defaults. The
same derivation fixes a
trailing-covariance volatility policy: 60-row window, 20-row minimum, 252
periods for V1 daily data, 8760 for V2 continuous hourly data, or the verified
V3 decision clock, the request/default annualized ceiling, and no scale-up.
Portfolio and RL Studies bind the same file as a
dependency. Intake reconstructs it on every load, so request or mandate
tampering fails rather than changing the position or risk question silently.

If the request contains `benchmarkPolicy`, the same derivation locks cash or
one named dataset-universe asset into a complete benchmark weight vector.
The asset may remain context-only; benchmark membership never expands
position authority. Omission records the direction-derived benchmark rather
than treating it as caller intent. Portfolio and governed RL use the identical
vector for every relative metric. See
[[docs/design/caller-owned-benchmark-reference]].

Every intake also writes
`strategies/research-horizon.json`. Optional strict
`request.horizonPolicy` supplies one primary and one to five diagnostic
forward-bar targets; otherwise the Mandate records reference defaults rather
than caller facts. Factor selection and primary diagnostics use the primary
target. All lanes bind the exact Mandate, and Reports/Dossiers disclose it.
Portfolio and RL still use sequential next-bar accounting and do not relabel
that accounting as a direct multi-bar forecast.

Project-root `request.json` preserves the exact canonical caller request.
For the fixed Book Risk route, optional `positionScenarios` preserves one to
eight caller-authored complete hypothetical books beside the baseline
`positionSnapshot`. Core requires the same timestamp and currency, requested
non-context assets, complete funding, and distinct books; it never interprets
sparse transfers or generates a scenario. The derived
`strategies/position-snapshot.json` freezes baseline and scenarios together so
one Run compares them against one content-locked dataset and method.
Alternatively, optional `positionSizing` freezes one caller-authorized
positive held-asset-to-cash path, a fixed 63/126/252-bar historical covariance
window, and one annualized-volatility ceiling. It is mutually exclusive with
scenarios. The derived dependency authorizes an exact one-dimensional
historical target-position calculation only; it grants no optimization,
account, Order, or trading authority.
Project-root `intake.json` points to and hashes the request, snapshot, and
generated Study. Its `studyInputHash` is the immutable identity at handoff,
not a requirement that editable research source remain unchanged forever.
Core and Studio verify the fixed Study/dataset contract while exposing whether
the current Study input still matches that intake identity. Existing Runs
become stale evidence after an intentional source change; the intake itself
does not become corrupt.
Iterative Factor, Portfolio, RL, and coordinated-desk intake records
`status: ready-for-session`; once a delegated Session starts, the existing
Session contract copies and freezes the request and derived Brief
independently. The fixed descriptive Book Risk route instead records
`status: ready-for-run`. It has no candidate source or selection loop, so
advertising a Session would contradict its authority contract.

## Transactional construction

The public operation is:

```text
aq project intake <workspace> <project-id>
  --request <request.json>
  --dataset <ohlcv-package.json>
  --template ohlcv-research-desk
```

Validation and construction occur inside the existing hidden Project staging
directory. Any failure removes that staging directory and leaves Workspace
discovery/default selection unchanged. A successful operation atomically
publishes the Project and returns exact commands to:

1. inspect the coordinated research program;
2. execute a bounded baseline Run in the recommended lane;
3. for iterative templates only, start a delegated Session using the
   preserved request.

For Portfolio or RL work, those commands operate only after the request-derived
Portfolio Mandate has been content-locked into the Study identity.
Book Risk intake terminates at the fixed Run and its read-only Explorer; it
returns no `session.start` action.

The three single-lane templates remain available for narrow, explicitly
selected work. `ohlcv-research-desk` is the default delegated-research intake:
one dataset snapshot supports coordinated Factor, Portfolio, and governed RL
Studies without asking the caller to choose an implementation method.

The command does not silently run research.

## Studio

Before iterative research starts, Studio shows:

```text
research mandate → locked dataset snapshot → immutable baseline → iterate
```

The view distinguishes requested assets from the wider research universe and
includes coverage, provider/adjustment claims, template, Study, latest verified
baseline selection/audit/stress metrics, and the exact copyable next command.
That command is `session.start` for iterative templates and `run.execute` for
the fixed descriptive Book Risk route. After Session start, the existing
request → evidence → report board becomes authoritative; after a Book Risk
Run, the verified read-only Explorer becomes authoritative.

Studio remains read-only and does not duplicate validation or construction.

## Invariants

1. No invalid intake leaves a visible partial Project.
2. All source paths are confined and all normalized dataset bytes are local to
   the Project.
3. Request assets are a subset of the research universe and share its declared
   asset class.
4. No missing date is silently filled or removed.
5. Provider and adjustment metadata are disclosed claims, not authenticated
   provenance.
6. Dataset bytes, snapshot, Study, Runs, Sessions, and Reports form one
   verifiable identity chain.
7. Core creates the Project but does not autonomously start research.
8. AutoQuant retains no Broker or trading-account authority.
9. Research-universe assets outside the request remain context-only unless the
   request explicitly authorizes them.
10. V2/V3 materialized higher bars must reconcile to locked base bytes, and all
    three research lanes consume the same causally aligned surface.
11. V4 retains absent rows as absence, is Factor-only, and exposes usable
    cross-sectional breadth in immutable evidence.

## Verification and change checklist

Run the bounded intake/CLI/Studio tests plus the repository-required full
regression. A real-data smoke must copy caller-supplied files into an isolated
temporary package, create a Project, remove dependence on that source
directory, and execute the Project-local Study.

When changing this boundary:

- update the JSON Schema, capability descriptor, CLI output, Studio snapshot,
  and canonical docs together;
- prove every newly accepted calendar/frequency/class against Judge timing and
  annualization semantics before advertising it;
- preserve structured failures and all-or-nothing Project publication;
- treat provider fields as disclosed claims unless a separate authenticated
  provenance authority is introduced;
- never mutate a dataset behind an existing Study, Session, Run, or Report
  identity.

## Known limits

- V1 handles one aligned daily session panel; V2 handles one continuous UTC
  1h panel with exact 3h/4h/6h/12h/1d derived bars; V3 handles bounded
  configurable continuous bases and XNYS regular sessions; V4 handles an
  observed-only ragged daily panel for Factor research only.
- V3 XNYS regular-session intraday aggregation is supported; extended hours,
  unscheduled halts, and other exchange calendars are not.
- Symbols are restricted to path-safe identifiers.
- It does not prove point-in-time universe membership, delisting coverage,
  corporate-action correctness, or vendor licensing.
- Provider retrieval and optional host/Inbox delivery remain external
  authority.
