# Allocation construction fidelity by split

- Status: `completed`
- Updated: `2026-07-30`
- Originating desk:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0823-cap-fidelity-allocation/desk`
- Related design: [[docs/design/portfolio-native-allocation-lab]],
  [[docs/design/study-run-evidence]],
  [[docs/design/agent-operator-experience]], and
  [[docs/design/studio-observation-surface]].

## Outcome

A Coding Agent can answer a caller's validation-scoped ERC construction
question from immutable Core evidence: exact scheduled/eligible/within-
tolerance/cap-gap populations, tolerance rate, maximum error, and the latest
eligible validation decision. Relative-performance selection remains a
separate claim and cannot masquerade as construction fidelity.

## Context

A fresh no-memory, no-web, no-subagent Grok worker used only installed
`aq 0.8.23` to evaluate a monthly four-asset ERC candidate with a 0.30
single-name cap and 0.01 contribution tolerance. The fixed Run succeeded and
validation net Sharpe advantage was positive, so the existing performance
conclusion was `supported`.

The worker correctly refused to answer the caller's independent requirement
that at least 90% of validation decisions meet parity tolerance. Run and
Explorer exposed only an all-period solver population and one overall latest
decision, dated in test. The immutable decision ledger contains enough
evidence, but Core did not publish or verify its split-scoped construction
meaning. Private pandas/CSV recomputation would contradict the Workbench's
evidence contract.

## Scope

### In scope

- Add one immutable `constructionFidelity` block with train, validation, and
  test solver populations.
- For each split, expose scheduled and eligible decisions, within-tolerance
  and cap-induced-gap counts, within-tolerance rate, maximum error, and the
  latest eligible decision's status/error/cap-binding evidence.
- Define split membership from the fixed chronological daily-path interval;
  insufficient-history scheduled decisions remain visible but not eligible.
- Keep the existing all-period `solver` and `latestDecision` fields for
  compatibility.
- Have strict Allocation Explorer independently rederive the complete block
  from `allocation-decisions.csv`, reconcile it when a new immutable report
  contains it, and derive it for older valid Runs that predate the block.
- Mark the existing `conclusion` explicitly as
  `relative-performance-only`.
- Project concise validation construction fidelity through Run metrics,
  orientation, Studio, CLI, schemas, and canonical docs.

### Out of scope

- Adding the caller's 90% threshold to the machine Research Request or making
  it a selection rule.
- Changing ERC targets, solver tolerance, caps, return accounting,
  validation/test selection authority, or historical artifacts.
- Treating cap-induced parity gaps as Run failure.
- Orders, live optimization, or trading authority.

## Acceptance

- [x] The unchanged capped field-trial Run exposes validation 6 scheduled,
      6 eligible, 0 within tolerance, 6 cap gaps, rate 0, maximum error
      `0.2010967711126228`, and latest eligible decision 2025-12-31 as a gap.
- [x] Relative-performance conclusion remains supported at validation net
      Sharpe advantage `1.3258834975013458` but is explicitly scoped away from
      construction fidelity.
- [x] New reports and Run metrics carry the exact block; strict Explorer
      independently reconciles every field and rejects rehashed tampering.
- [x] A valid pre-`0.8.24` Allocation Run remains readable and receives a
      derived Explorer block without rewriting its immutable report.
- [x] Orientation and Studio make validation fidelity visible without asking
      the Agent to inspect CSV.
- [x] A fresh installed-wheel Grok retry answers both caller verdicts from
      Core evidence, with one Project, one Run, zero Sessions, and no private
      recomputation.
- [x] Focused/full tests, documentation graph, wheel install, exact-commit
      clone smoke, version `0.8.24`, commit, tag, and canonical push pass.

## Work

- [x] Reproduce the missing evidence with an isolated installed-release worker
      and preserve its exact honest handoff.
- [x] Implement the immutable and independently verified split-fidelity model.
- [x] Add Run/Explorer/orientation/Studio compatibility and tamper tests.
- [x] Update public schemas, capabilities, canonical docs, status, and version.
- [x] Complete fresh packaged retry and release audit.

## Findings and decisions

- 2026-07-30 — An all-period zero-within-tolerance count is not a valid
  substitute for a validation-only population, even when it strongly suggests
  the same answer.
- 2026-07-30 — `supported` remains a legitimate validation relative-
  performance statement; the defect is its missing scope and the absence of a
  separately named construction-fidelity contract.
- 2026-07-30 — The immutable decision ledger already owns the necessary facts,
  so Explorer should rederive them rather than trust a duplicated scalar.

## Verification

- Original valid `0.8.23` Run
  `run-20260729T224011293104Z-998af3ec7483` remains readable and derives
  validation 6 scheduled, 6 eligible, 0 within tolerance, 6 cap gaps, maximum
  error `0.2010967711126228`, and latest validation gap `2025-12-31`.
- Fresh installed-wheel retry:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0824-cap-fidelity-retry`
- Final retry Run:
  `run-20260729T230006982582Z-070757f284b9`
- Independent validation found one valid Project, one succeeded fixed Run,
  zero Sessions, strict construction-fidelity reconciliation, and a valid
  Studio snapshot without diagnostics.
- `uv run python -m unittest discover -s tests -v` — 317 passed in 808.042 s.
- `uv run python scripts/check_doc_links.py` — 1,109 links resolved.
- Node Studio syntax check and source/wheel build passed.

## Progress log

- 2026-07-30 — Plan created from fresh `0.8.23` capped-ERC field trial.
- 2026-07-30 — Implemented immutable split construction fidelity, strict old-
  Run derivation/new-report reconciliation, explicit relative-performance
  scope, and shared CLI/orientation/Studio projection.
- 2026-07-30 — Fresh installed-wheel `0.8.24` worker answered both caller
  fidelity clauses from public Core evidence without private recomputation.
  Full regression and documentation verification passed.

## Completion

Released as `v0.8.24`.
