# Request-bound portfolio mandates

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/portfolio-construction-lab]],
  [[docs/design/request-bound-portfolio-mandates]],
  [[docs/design/signal-policy-and-attribution]],
  [[docs/design/rl-factor-policy-lab]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/design/research-program-orchestration]].

## Outcome

Make a request-driven AutoQuant Project answer the caller's actual position
question. Derive one strict, content-locked Portfolio Mandate from the Research
Request and require both Portfolio and governed-RL lanes to use it for
tradable assets, permitted direction, cash, target sizing, constraints, and
benchmark evidence.

## Context

The delegated request already distinguishes `long`, `short`, `long-short`,
`relative-value`, and `research-only`, and requested assets may be a subset of
the supplied peer universe. The current fixed Portfolio and RL Judges ignore
that information: every Run trades the entire universe as a gross-one,
dollar-neutral book.

This is not only a presentation mismatch. A caller asking whether to buy AAPL
can currently receive evidence from an implicit AAPL-plus-peer long/short
portfolio. The factor universe is useful research context, but it must not
silently become the tradable universe or change the requested exposure.

## Scope

### In scope

- A strict versioned `strategies/portfolio-mandate.json` in every new Portfolio and RL
  template Project.
- Deterministic request mapping:
  - `long` → requested-assets-only long/cash mandate;
  - `short` → requested-assets-only short/cash mandate;
  - `long-short` and `relative-value` → requested-assets-only
    dollar-neutral mandate;
  - `research-only` and synthetic templates → explicitly disclosed
    all-universe research-neutral mandate.
- Separate research universe, tradable universe, direction, gross limit, net
  rule, per-asset cap, cash permission, and short permission.
- Direction-aware mechanical entry/hold/exit state transitions and
  risk/conviction sizing. Directional mandates may retain cash rather than
  invent an opposing book or violate the asset cap.
- Mandate-aware constraint audits, benchmarks, Run metrics, artifacts,
  decision ledgers, CLI/Studio projections, Reports, and Dossiers.
- The RL action sleeves use the exact same mandate and cannot learn around its
  position constraints.
- Intake and Study identity detect mandate/request tampering.
- Compatibility with historical Projects whose copied Judges predate this
  template contract.

### Out of scope

- Live orders, UTA mutations, TPSL, L2 fills, or Broker state.
- User-configurable leverage, arbitrary optimizer constraints, or a strategy
  DSL.
- Borrow availability, locate fees, nonlinear impact, futures margin, or
  production covariance optimization.
- Inferring that peer/context assets are valid hedges without an explicit
  caller request.

## Acceptance

- [x] A strict mandate is derived from normalized request bytes and records
  research versus tradable assets without ambiguity.
- [x] The mandate is part of fixed Study/Run/Session identity and a changed
  request or mandate invalidates evidence rather than silently changing it.
- [x] Long and short mandates can hold cash, never take the opposite sign, and
  never trade context-only assets.
- [x] Long-short/relative-value mandates retain fixed gross/net/cap invariants
  and fail visibly when the requested tradable set cannot fund both sides.
- [x] Every decision row explains tradability, permitted direction, signal
  transition, risk strength, target, execution, and contribution.
- [x] Portfolio metrics, constraints, benchmark, artifacts, explorer, Studio,
  Report, and Dossier evidence disclose and reconcile the mandate.
- [x] Every RL action target passes the same mandate audit and reported policy
  evidence names the locked mandate identity.
- [x] Existing synthetic reference behavior remains deterministic and legacy
  Projects remain loadable.
- [x] Focused/full tests, real request smoke, browser QA, docs, isolated wheel,
  commit, and push pass.

## Work

- [x] Audit the request, intake, Study identity, Portfolio Core/Judge, RL
  sleeves, evidence, and Studio boundaries.
- [x] Define and materialize the strict mandate contract.
- [x] Generalize mechanical construction, accounting, evidence, and RL sleeves.
- [x] Project the mandate through Agent/Studio/report surfaces.
- [x] Complete deterministic, real-project, browser, full-suite, and wheel
  verification.

## Findings and decisions

- 2026-07-24 — Requested assets are conservatively the only tradable assets
  for directional and relative-value mandates. Remaining dataset assets are
  factor/benchmark context, not implicit hedge authorization.
- 2026-07-24 — A directional mandate may leave capital in cash when signals or
  caps cannot use the gross limit. It must not manufacture a short/long side
  merely to remain fully invested.
- 2026-07-24 — `research-only` keeps the historical all-universe neutral
  research portfolio, but now records that choice explicitly instead of
  pretending it came from a directional request.
- 2026-07-24 — A directionally authorized all-cash path is valid evidence,
  including when no requested asset crosses its fixed entry threshold.
  Dollar-neutral construction still fails visibly when both sides cannot be
  funded under the cap.
- 2026-07-24 — Researcher timeout recovery must terminate the entire external
  process group before restoring the Session leader; terminating only the
  parent shell permits a child to mutate the restored worktree later.

## Verification

- `git diff --check` passed.
- `uv run python -m compileall -q autoquant tests` passed.
- `node --check autoquant/studio_assets/studio.js` passed.
- `uv run python -m unittest tests.test_documentation -v` passed and resolved
  all 388 repository double-links.
- The focused mandate/intake/Portfolio/RL/CLI/Dossier/Report/program/Studio
  regression ran 60 tests successfully in 217.107 seconds.
- `uv run python -m unittest
  tests.test_mandates
  tests.test_research.ExternalResearchCampaignTests.test_protocol_and_command_failures_restore_the_leader
  -v` ran 6 tests successfully, including directional all-cash and child
  process timeout recovery.
- `uv run python -m unittest discover -s tests -v` ran 132 tests successfully
  in 401.087 seconds.
- A final sdist and wheel were built, the wheel was reinstalled with all 161
  dependencies in an isolated Python 3.11 environment, and the installed
  `aq` entry point successfully emitted the Portfolio Mandate schema, executed
  a Portfolio Run, projected its Explorer, and built a valid Studio snapshot.
  A direct installed-wheel check also accepted a zero-position long/cash book.
- A bounded request-driven equity Project used AAPL and MSFT as the only
  tradable long assets, kept NVDA, QQQ, and SPY as context, completed all three
  lanes and Reports, and published Dossier
  `dossier-20260724T142758627917Z-7cb795881d3c`.
- Browser QA passed at 1440×900, 900×900, and 390×844. Portfolio lane selection
  synchronized the Explorer and Inspector, the mandate/current-book evidence
  remained readable, responsive layout held, and browser diagnostics were
  empty.

## Progress log

- 2026-07-24 — Plan activated after the cross-workbench audit proved the
  request direction and requested asset subset were absent from Portfolio and
  governed-RL position construction.
- 2026-07-24 — Added the versioned request-derived mandate, fixed dependency
  identity, direction-aware construction, mandate-aware benchmarks and
  constraints, governed-RL sleeve binding, and strict tamper detection.
- 2026-07-24 — Projected the mandate through immutable artifacts, Portfolio and
  RL Explorers, CLI schema discovery, Studio, lane Reports, and Project
  Dossiers while retaining legacy-project observation.
- 2026-07-24 — Completed deterministic, real-request, isolated-wheel, browser,
  documentation, and full-suite verification.

## Completion

AutoQuant now distinguishes the research universe from authorized positions
and binds both mechanical Portfolio evidence and governed adaptive evidence to
one immutable request-derived mandate. Directional requests can remain partly
or entirely in cash without inventing an opposing position, context assets
cannot silently become trades, and every downstream human/Agent evidence
surface discloses the same contract. Historical synthetic and legacy evidence
remain observable under explicit compatibility semantics.
