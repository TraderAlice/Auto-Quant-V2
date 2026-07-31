# Agent-native market-data acquisition

Status: accepted at `0.8.31`.

Related: [[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/workspace-project-boundaries]],
[[docs/market-data-acquisition-field-trials]], and
[[plans/market-data-acquisition-skills]].

## Purpose

AutoQuant turns market-data acquisition into a discoverable coding-Agent
procedure while keeping provider networking outside Core. The same installed
Harness supplies a small market router, narrow provider Skills, and a common
packaging Skill to every initialized Workspace.

```text
research question
→ acquire-market-ohlcv
→ one market reference
→ two suitable provider Skills
→ retained raw bytes and provider audits
→ same-semantics comparison when allowed
→ package-autoquant-ohlcv
→ strict Project intake
→ content-locked Project snapshot
```

Core starts at the dataset-package boundary. It validates paths, schemas,
OHLCV invariants, market clocks, interval semantics, and content identity. It
does not authenticate a provider's venue, adjustment, volume, calendar,
terms, or redistribution claim.

## Canonical Skill bundle

Canonical Skill bytes live under `autoquant/workspace_skills/` and ship in the
wheel. Workspace creation transactionally materializes the same bytes under
`.agents/skills/` and `.claude/skills/`, then records every file hash in
`autoquant-skills.json`. Generated discovery copies are not edited by hand.

`acquire-market-ohlcv` is the only regional catalogue an Agent needs to read
first. It loads one relevant market reference, then invokes exact provider and
packaging Skills. Provider scripts are bounded, parameterized procedures, not
a stable downloader SDK or a Core compatibility promise.

## Source-diversity rule

Every accepted market or explicitly named venue has at least two
independently executable sources. The routes are peers selected by the
research need, not a hard-coded primary/fallback chain. Selection considers:

- venue authority and symbol identity;
- completed-session freshness and history;
- raw, split-adjusted, or split-and-dividend-adjusted price meaning;
- volume unit and trade-scope evidence;
- missing and suspended observations;
- credentials, rate limits, access behavior, and terms;
- retained response and transformation audit quality.

An official route is listed first when it is practically accessible. Taiwan,
for example, begins with official TWSE; FinMind is an independently executable
aggregator route, and Yahoo is a broad split-adjusted route.

Source plurality is not semantic equivalence. Raw and adjusted packages are
never relabelled to permit comparison. When contracts match, the common
comparison tool records date overlap, OHLC tolerances, volume ratios, missing
rows, and exact package hashes. When contracts differ, a numerical comparison
must fail and the ledger records only route plurality.

## Evidence and lifecycle

Acquisition writes to explicit Workspace staging, never directly into a
Project:

```text
workspace/
├── staging/market-data/<dataset-id>/
│   ├── raw/
│   ├── normalized CSVs
│   ├── provider-audit.json
│   └── dataset-package.json
└── projects/<project-id>/data/ohlcv/
    ├── normalized content-locked inputs
    └── snapshot.json
```

The provider audit retains request URIs, observed retrieval time, raw hashes,
response metadata, conversions, dropped placeholders, anomalies, and
limitations. Staging remains caller/host-owned working evidence. A package
becomes quantitative input authority only after strict `aq project intake`
creates the Project-local normalized snapshot and `aq validate` passes.

In the repository-root desk, `staging/` and each Project's `data/` and cache
are Git-ignored persistent local evidence. Agents do not force-add ordinary
provider bytes or normalized market data. The checked-in sample's small
deterministic fixture is a teaching/distribution exception, not a precedent
for real Projects. Briefs, contracts, source, Runs, Reports, and Dossiers
remain ordinary Git-managed research state; provider redistribution terms and
an explicit caller request govern any deliberately distributable data fixture.

Changing markets does not require a new Workspace. Separate research
questions normally become sibling Projects; their immutable snapshots may
currently duplicate bytes. A shared mutable “latest data” cache is not part of
this contract.

## Failure behavior

Provider access is expected to degrade. A route stops truthfully on blocking,
shape changes, ambiguous symbols, stale or truncated output, or contradictory
semantics. It records the failure and may try another named peer route, but it
never silently changes adjustment, venue, interval, or authority claims.

The first field-trial matrix proves named U.S., XSHG/XSHE/XBSE, Tokyo, KRX,
TWSE, HOSE, and XPAR routes. It does not imply all securities, TPEx, all
Vietnamese boards, one synthetic European calendar, survivorship-free
universes, delisted history, futures rolls, live feeds, or redistribution
rights.

## Trading boundary

Acquisition and research intake grant no account, Broker, Order, TP/SL, or
trading authority. AutoQuant may later produce factor or target-weight
evidence from the locked dataset. OpenAlice or another execution-facing
system remains responsible for live state, suitability, execution planning,
and user authorization.
