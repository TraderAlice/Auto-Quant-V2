# Request-driven research intake and OHLCV dataset snapshots

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/CLI]], [[docs/PROJECT_FORMAT]],
[[docs/STUDIO]], [[docs/design/workspace-project-boundaries]],
[[docs/design/study-run-evidence]],
[[docs/design/request-bound-portfolio-mandates]],
[[docs/design/portfolio-risk-governor]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the boundary that turns a strict delegated Research Request
and caller-supplied market-data package into one self-contained AutoQuant
Project. It covers package semantics, normalization, provenance, content
identity, transactional construction, CLI discovery, and pre-Session Studio
observation.

It does not fetch market data, authenticate provider claims, compute corporate
actions, create live subscriptions, start an autonomous Campaign, or publish
to OpenAlice.

## Authoritative locations

- Package validation, normalization, snapshot materialization, and intake
  verification: `autoquant/intake.py`
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

V1 deliberately supports only `1d` session data. The current Factor,
Portfolio, and RL reference Judges annualize at 252 and assume one aligned
daily panel. Continuous markets, intraday sessions, exchange holidays, mixed
asset classes, and distinct listing histories require later explicit
contracts.

## Validation and normalization

Before any Project is visible, Core:

1. validates strict manifest and Research Request schemas;
2. confines every asset path beneath the package directory and rejects
   symlinks, duplicates, and unsafe symbols;
3. reads CSV, Parquet, or Feather and accepts `date`, `datetime`, `timestamp`,
   or `time` as the timestamp field;
4. requires finite positive OHLCV, coherent high/low bounds, unique
   timestamps, and no weekend rows for the session clock, then orders the
   canonical daily output;
5. requires every asset to share the exact timestamp panel;
6. enforces template-specific breadth and history floors;
7. requires each requested asset and non-null venue to exist in the package
   and requires the request's single asset class to equal the package class.

Canonical Project data uses:

```text
timestamp,open,high,low,close,volume
```

with one `YYYY-MM-DD` row per session and one `<symbol>.csv` per asset. There is
no implicit forward fill, timestamp intersection, survivorship repair, or
corporate-action transformation.

## Snapshot and identity

The resulting `data/ohlcv/snapshot.json` records:

- package id, version, class, frequency, market, adjustment, and provider;
- request hash and requested assets;
- exact research universe and common time range;
- source path/hash and normalized path/hash for every asset;
- observations and coverage for every asset;
- template and fixed Study id.

The Study declares `ohlcv/**`, so canonical CSV, snapshot, and README bytes all
enter `datasetHash`, Run identity, Session locks, and Reports. Editing any one
creates a different Study/Run identity and stales an existing Session.

Portfolio and governed-RL intake also writes the strict fixed
`strategies/portfolio-mandate.json`. Core derives it from the exact normalized
request and dataset universe: requested assets are tradable, remaining assets
are context-only, and direction determines long/cash, short/cash, or
dollar-neutral construction and benchmark. The same derivation fixes a
trailing-covariance volatility policy: 60-row window, 20-row minimum, 252
annualization periods, 15% annualized ceiling, and no scale-up. Portfolio and
RL Studies bind the same file as a dependency. Intake reconstructs it on every
load, so request or mandate tampering fails rather than changing the position
or risk question silently.

Project-root `request.json` preserves the exact canonical caller request.
Project-root `intake.json` points to and hashes the request, snapshot, and
generated Study. Its `studyInputHash` is the immutable identity at handoff,
not a requirement that editable research source remain unchanged forever.
Core and Studio verify the fixed Study/dataset contract while exposing whether
the current Study input still matches that intake identity. Existing Runs
become stale evidence after an intentional source change; the intake itself
does not become corrupt.
Once a delegated Session starts, the existing Session contract copies and
freezes the request and derived Brief independently.

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
3. start a delegated Session using the preserved request.

For Portfolio or RL work, those commands operate only after the request-derived
Portfolio Mandate has been content-locked into the Study identity.

The three single-lane templates remain available for narrow, explicitly
selected work. `ohlcv-research-desk` is the default delegated-research intake:
one dataset snapshot supports coordinated Factor, Portfolio, and governed RL
Studies without asking the caller to choose an implementation method.

The command does not silently run research.

## Studio

Before a Session exists, Studio shows:

```text
research mandate → locked dataset snapshot → immutable baseline → iterate
```

The view distinguishes requested assets from the wider research universe and
includes coverage, provider/adjustment claims, template, Study, latest verified
baseline selection/audit/stress metrics, and the exact copyable `session.start`
command. After Session start, the existing
request → evidence → report board becomes authoritative.

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

- V1 handles one aligned daily session panel and one declared asset class.
- Symbols are restricted to path-safe identifiers.
- It does not prove point-in-time universe membership, delisting coverage,
  corporate-action correctness, or vendor licensing.
- Provider retrieval and OpenAlice Inbox publication remain external
  authority.
