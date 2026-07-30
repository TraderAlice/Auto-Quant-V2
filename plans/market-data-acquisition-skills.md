# Agent-native market-data acquisition skills

- Status: `active`
- Updated: `2026-07-30`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Give a fresh coding Agent a versioned, progressively disclosed Skill bundle
that can select a suitable source, acquire and audit real closed-bar OHLCV,
package it for AutoQuant, and preserve the resulting evidence without adding a
universal downloader to Core.

The first accepted coverage set is daily listed-equity research for the United
States, mainland China A shares, Japan, South Korea, Taiwan, Vietnam, and
explicitly named European Union venues. Every claimed route must be proved by
a real acquisition and a clean AutoQuant intake; unsupported or degraded
provider behavior must remain visible rather than being hidden behind a
nominal market-support label.

## Context

AutoQuant already has a strict provider-neutral boundary after bytes arrive:
it validates conventional OHLCV, market-clock and interval semantics,
materializes a normalized Project-local snapshot, and binds its exact identity
to Studies and Runs. It deliberately does not fetch market data or authenticate
provider claims.

Real field trials currently obtain Yahoo and Binance data through useful but
task-local scripts under external input/trial directories. This works, but a
new Agent must rediscover provider endpoints, symbol conventions, adjustment
semantics, timestamp handling, raw-response preservation, and the
`autoquant-ohlcv-dataset-package` contract. Encoding every provider and market
combination in `aq` would make Core own unstable network behavior and a large
cross-market semantic surface.

Acquisition is therefore treated as Agent procedure:

```text
ordinary research assignment
→ market/provider routing Skill
→ provider-specific acquisition Skill
→ raw bytes + exact retrieval audit
→ common AutoQuant packaging Skill
→ strict project intake
→ Project-local content-locked snapshot
```

Skills are improved from real use. They do not become authority merely because
their prose or scripts claim that a provider supports a market.

## Scope

### In scope

- Define one discoverable Skill bundle and its standalone/OpenAlice
  materialization path.
- Keep the top-level routing surface small through progressive disclosure.
- Separate market semantics from provider mechanics and AutoQuant packaging.
- Extract reusable, tested procedures from existing Yahoo and Binance
  acquisition work.
- Establish and field-test an Eastmoney route for mainland China A shares.
- Research and prove at least one daily adjusted or explicitly unadjusted
  route for every first-batch market.
- Preserve the acquisition script, provider response or closest available raw
  evidence, retrieval time when known, source URI, terms claim, hashes,
  transformation audit, and final package.
- Make every real acquisition update a durable field-trial ledger and feed
  only demonstrated reusable friction back into the Skills.
- Verify a fresh coding Agent can discover the right references, fetch,
  inspect, package, intake, validate, and explain the dataset without private
  repository knowledge or live coaching.

### Out of scope

- A universal `aq data fetch` provider API or Core-owned downloader.
- A hosted data service, credentials vault, subscription manager, or
  authenticated provider-quality guarantee.
- Automatic corporate-action truth, survivorship-free universes, delisted
  security history, futures chains, roll construction, or live feeds.
- Full intraday support for every first-batch market. Initial coverage means
  completed daily bars; intraday routes are added only through bounded real
  needs.
- Treating “Europe” or “EU” as one synthetic exchange calendar. Coverage is
  venue-specific even when one routing reference groups the venues.
- A mutable global market-data cache. Workspace-level content-addressed
  dataset reuse remains a separate future design if Project-local duplication
  becomes material.
- Broker, account, Order, TP/SL, or trading authority.

## Skill topology

### Always-discoverable router

`acquire-market-ohlcv`

- Trigger on requests to obtain, refresh, prepare, or troubleshoot historical
  OHLCV for AutoQuant research.
- Ask for or infer only researcher-owned implementation choices; surface
  missing caller-owned market, instrument, interval, date range, adjustment,
  and research-clock intent.
- Route by market/venue, interval/history, adjustment need, credentials,
  network availability, and provider limitations.
- Read only the relevant market references and invoke exact provider/package
  Skill ids.
- Never claim that a symbol lookup proves listing, adjustment, or calendar
  semantics.

Its first-batch references are kept one level below `SKILL.md`:

```text
references/
├── common-acquisition-checklist.md
├── us-equities.md
├── cn-a-shares.md
├── japan-equities.md
├── south-korea-equities.md
├── taiwan-equities.md
├── vietnam-equities.md
└── eu-equity-venues.md
```

Each market reference owns symbol/venue conventions, timezone and completed
daily-bar meaning, calendar/session caveats, adjustment choices, suspension
and missing-observation treatment, volume units, currency, known provider
routes, and required post-fetch checks. Detailed provider API mechanics do not
belong in these references.

### Provider execution Skills

Initial planned provider Skills:

- `fetch-yahoo-ohlcv` — extract the already-proven Chart API workflow,
  adjustment audit, raw JSON preservation, retries, and provider metadata;
- `fetch-eastmoney-ohlcv` — establish and prove the A-share route rather than
  copying an unverified endpoint recipe;
- `fetch-binance-ohlcv` — preserve the already-proven paginated closed-hour
  public-kline procedure as a non-stock continuous-market reference.

Additional provider Skills are admitted only when a first-batch market lacks a
reliable route or a real request demonstrates a useful fallback. Provider
names are not frozen in advance merely to complete a matrix.

Each provider Skill may contain:

```text
SKILL.md
agents/openai.yaml
scripts/
references/
```

Scripts are narrow, parameterized starting points rather than an SDK. They
write into an explicit Workspace staging package and never mutate a Project
directly. Credentials come from the host environment and are never persisted
in Skill files, generated manifests, logs, or Projects.

### AutoQuant packaging Skill

`package-autoquant-ohlcv`

- Inspect raw/provider-normalized observations before intake.
- Check OHLC relationships, positivity rules, duplicates, ordering, coverage,
  missing timestamps, timezone and bar-close semantics, volume meaning,
  adjustment consistency, and market-specific calendar expectations.
- Choose the narrowest truthful V1–V5 dataset-package contract.
- Generate or complete `dataset-package.json` without inventing provider
  retrieval time, venue, adjustment, calendar, continuous-series, or terms
  claims.
- Keep manifest asset paths confined beneath their manifest directory.
- Run strict `aq project intake`, `aq validate`, and read-only inspection.
- Explain what AutoQuant verified and which provider claims remain external
  input authority.

## First-batch coverage definition

A market is not “covered” until its ledger row contains:

1. an explicit market and venue scope;
2. one real, non-toy completed-daily-bar acquisition;
3. exact provider route and Skill revision;
4. symbol-mapping evidence;
5. price-adjustment and volume semantics;
6. timezone, session-date, suspension, and missing-observation treatment;
7. retained raw/audit evidence and hashes;
8. a valid AutoQuant dataset package and content-locked Project snapshot;
9. a fresh-worker handoff that states unresolved limitations honestly.

The initial market matrix is:

| Route | Initial coverage unit |
| --- | --- |
| United States | named XNYS/XNAS/ARCX-listed equities or funds |
| Mainland China | named XSHG/XSHE/XBSE A shares, with venue differences disclosed |
| Japan | named Tokyo-listed equities |
| South Korea | named KRX-listed equities |
| Taiwan | named TWSE/TPEx-listed equities with venue disclosed |
| Vietnam | named HOSE/HNX/UPCoM-listed equities with venue disclosed |
| European Union | separately named venues; first proof must not imply one EU calendar |

This plan intentionally does not predeclare one provider as reliable across
all rows. Current provider documentation, terms, endpoints, history limits,
and returned bytes must be researched when each route is built.

## Workspace and data lifecycle

Phase one keeps the existing ownership model:

```text
workspace/
├── staging/market-data/<package-id>/
│   ├── acquisition script
│   ├── raw provider evidence
│   ├── normalized source CSVs
│   ├── provider-audit.json
│   └── dataset-package.json
└── projects/<project-id>/
    └── data/ohlcv/
        ├── normalized content-locked CSVs
        └── snapshot.json
```

Staging is caller/host-owned acquisition material. A Project snapshot becomes
quantitative input authority only after strict intake. Separate research
questions normally create separate Projects on the same persistent Workspace;
changing from A-share research to U.S.-equity research does not require a new
Workspace.

Two Projects may currently materialize duplicate normalized bytes. Real usage
must measure that cost before proposing a Workspace dataset store. If promoted,
that follow-up must use immutable content identity and preserve exact
Project/Run dataset binding; it must not introduce a mutable “latest data”
dependency.

## Learning loop

Every acquisition follows the same improvement loop:

1. Preserve the ordinary assignment and clarify its data meaning.
2. Give a fresh worker the current Skill bundle and permitted network/access
   context.
3. Record the chosen market reference, provider Skill, fallback reasoning,
   commands, retries, raw hashes, elapsed time, and final package identity.
4. Independently verify provider bytes, transformations, package semantics,
   Project snapshot, and Agent handoff.
5. Classify friction as task-specific, market-reference, provider-Skill,
   packaging-Skill, AutoQuant Core, host/network, or unsupported.
6. Improve only the owning layer.
7. Re-run a fresh worker when the change affects discovery, execution, or
   scientific meaning.

The field-trial ledger must distinguish:

- acquisition success from scientifically suitable data;
- provider absence from Agent misuse;
- nominal symbol coverage from correct venue/asset identity;
- adjusted-close availability from correctly adjusted OHLC;
- retrieval/package timestamps from the provider retrieval time;
- a valid package from authenticated provider truth.

## Acceptance

- [ ] The Skill source and standalone/OpenAlice discovery/materialization
  model has one canonical, tested implementation without manually maintained
  divergent copies.
- [ ] `acquire-market-ohlcv` routes a fresh Agent to one relevant market
  reference and exact provider/package Skills without loading the full
  regional catalogue.
- [ ] `fetch-yahoo-ohlcv`, `fetch-eastmoney-ohlcv`, and
  `fetch-binance-ohlcv` pass Skill validation and their bundled scripts pass
  representative executable tests.
- [ ] `package-autoquant-ohlcv` produces a strict, confined, provenance-honest
  package and verifies the resulting Project through public `aq` surfaces.
- [ ] Every first-batch market satisfies the coverage definition with real
  retained evidence; European coverage names exact venues and never claims a
  synthetic EU calendar.
- [ ] At least one route exercises provider fallback or ends with a truthful
  unsupported/degraded conclusion instead of silently changing semantics.
- [ ] Fresh-worker field trials cover at least one XNYS-style session market,
  mainland China A shares, one non-U.S. Asian market, and one named EU venue
  before the remaining matrix is accepted.
- [ ] Existing Yahoo/Binance task-local scripts are either incorporated as
  traceable Skill resources or retained as historical inputs with the new
  canonical replacement identified.
- [ ] No Skill downloads directly into `projects/`, mutates an immutable Run,
  stores credentials, grants trading authority, or bypasses strict intake.
- [ ] Documentation links, Skill validators, deterministic tests, build,
  installed/discovered Skill smoke, full repository tests, and clean
  standalone Workspace intake pass.

## Work

- [ ] Audit existing Yahoo/Binance acquisition scripts and field-trial
  artifacts into a reusable-procedure inventory.
- [ ] Decide and prove the canonical Skill source plus `.agents`/Claude/OpenAlice
  materialization model.
- [ ] Scaffold the router, Yahoo, Eastmoney, Binance, and packaging Skills
  using the maintained Skill initializer and generated agent metadata.
- [ ] Write the common checklist and seven first-batch market references,
  keeping provider mechanics in provider Skills.
- [ ] Extract and parameterize the Yahoo and Binance scripts; add deterministic
  fixture tests plus opt-in bounded live smokes.
- [ ] Research Eastmoney from current primary/observable behavior, implement
  the narrow A-share procedure, and run the first complete acquisition.
- [ ] Establish the market/provider coverage matrix from real tasks, adding a
  provider Skill only where evidence requires it.
- [ ] Create the acquisition field-trial ledger and execute isolated
  fresh-worker trials across the acceptance matrix.
- [ ] Promote repeated packaging or Core friction only after its owning layer
  is identified; keep speculative provider convenience out of `aq`.
- [ ] Update Agent guidance, README, current status, architecture references,
  and release notes after the Skill bundle is proven.
- [ ] Complete Skill validation, regression, install/discovery, network-bound
  smoke, documentation, and clean-Workspace verification.
- [ ] Audit acceptance and split any content-addressed dataset-store or
  additional-market work into separately indexed plans.

## Findings and decisions

- 2026-07-30 — Acquisition remains outside AutoQuant Core. Skills own unstable
  provider procedure; strict intake owns quantitative data admission.
- 2026-07-30 — Use one router plus provider/package Skills and one-level market
  references. Seven market × multiple provider top-level Skills would duplicate
  semantics and overload Agent discovery.
- 2026-07-30 — Initial coverage means completed daily bars. Intraday support is
  admitted from real research needs rather than promised uniformly.
- 2026-07-30 — The current Project-local snapshot remains authoritative.
  Workspace-level dataset deduplication is deferred until real storage evidence
  justifies changing the self-contained Project boundary.
- 2026-07-30 — Existing OpenAlice materializes shared Agent Skills under
  `.agents/skills/` and Claude-specific copies under `.claude/skills/`; the
  AutoQuant bundle still needs one canonical source and a no-drift
  materialization path before implementation.

## Verification

Pending. Each real acquisition will record exact provider window, retrieval
time claim, raw and normalized hashes, Skill revision, package identity,
Project/Run identifiers when applicable, fresh-worker transcript, and
independent verification.

## Progress log

- 2026-07-30 — Plan created from the existing provider-neutral intake boundary,
  task-local Yahoo/Binance acquisition evidence, OpenAlice Skill discovery
  paths, and the first-batch market request.

## Completion

Pending.
