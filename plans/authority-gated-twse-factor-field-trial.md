# Authority-gated TWSE Factor field trial

- Status: `completed`
- Updated: `2026-08-01`
- Target release: `0.9.9`
- Related design: [[docs/design/agent-native-market-data-acquisition]],
  [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/factor-diagnostics]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that a fresh quantitative coworker starting with no market data can obey
one caller-fixed data-authority gate for a real TWSE Factor question. The
worker must acquire official TWSE raw daily evidence and one independent
same-semantics raw route before treating the study as answerable. If either
route or their semantic comparison is unavailable, it must stop with an
unsupported research handoff instead of publishing a single-provider result.
If the gate is satisfied, it must complete one bounded causal Factor research
chain and preserve every acquisition, dataset, Run, Report, and authority
identity needed for review.

## Context

The `0.9.0` Taiwan delegation used the same six-stock question. Its worker
attempted official TWSE first, received a CDN security page, then continued on
a FinMind-only panel. The factor evidence was weak and honestly disclosed, but
the result was rejected because the caller explicitly required official-plus-
peer raw evidence. That trial proved useful framework fixes while leaving the
quantitative assignment itself incomplete.

AutoQuant `0.9.8` now has stronger request-first guidance, standardized route
failure evidence, strict Project intake, direct Run Reports, and a complete
materialized market-data Skill bundle. A clean retry can distinguish whether
the remaining problem is provider availability, worker compliance, or a
reusable Workbench contract gap. Existing data inventory is not supplied and
must not narrow the question.

## Field assignment

Use completed daily raw OHLCV from `2025-01-01` through the latest completed
TWSE session for `2330`, `2454`, `2303`, `3711`, `2382`, and `3231`. Test one
causal cross-sectional hypothesis: whether 60-session relative strength
combined with 20-session traded-value expansion predicts higher 10-session
forward cross-sectional returns.

Official TWSE monthly history is mandatory venue evidence. FinMind is the
intended independent raw peer, with Yahoo available only as a differently
adjusted coverage/freshness route. The worker may choose the exact causal
normalization and combination method, but may not change universe, venue,
window, primary horizon, price semantics, source gate, or research-only scope.
A negative factor result is fully acceptable. A single-source result is not.

## Scope

### In scope

- Start a fresh installed-`0.9.8` standalone Workspace with zero staged market
  data and no access to repository source or prior trials.
- Preserve exact provider attempts, failures, raw responses, transformations,
  package audits, same-semantics comparison, and selection reasoning.
- Observe whether the worker establishes the data gate before Project intake,
  Study execution, or interpretation.
- When the gate passes, require one predeclared causal candidate, bounded
  evaluation, immutable evidence, and an honest terminal Report/handoff.
- Promote only independently reproduced Worker/Core/Skill friction required to
  make this assignment truthful and operable.

### Out of scope

- Adding a central market-data inventory, cache, universal downloader, live
  feed, TPEx coverage, corporate-action authority, or redistribution promise.
- Weakening the official-plus-peer condition because an unofficial source is
  structurally valid or convenient.
- Portfolio construction, target weights, Broker, Order, TP/SL, execution, or
  trading authority.
- Generalizing a Taiwan-specific failure into a cross-provider workflow engine
  without another concrete need.

## Acceptance

- [x] A fresh worker starts from the exact `v0.9.8` wheel, no staged OHLCV,
  public CLI/schema/Skills only, and preserves a complete transcript.
- [x] The English research brief fixes the six TWSE listings, raw daily
  semantics, date window, 10-session horizon, official-plus-peer authority
  gate, research-only scope, and truthful stop condition before acquisition.
- [x] Official TWSE and FinMind attempts use the bundled routes and preserve
  exact success or standard bounded failure evidence without hidden fallback.
- [x] No numerical cross-source agreement is claimed unless adjustment,
  sessions, symbols, and price/volume semantics are compatible; Yahoo cannot
  masquerade as a raw peer.
- [x] Project intake and quantitative interpretation occur only if both
  required raw routes and their bounded comparison pass. Otherwise the final
  handoff is explicitly unsupported and contains no authoritative Run/Report.
- [x] If admitted, exactly one bounded Factor investigation answers the fixed
  hypothesis, separates train/validation/test audit, and grants no target-
  weight or trading authority.
- [x] Every material baseline failure is either a reproducible Workbench gap
  repaired with regression coverage or an explicit provider/worker limitation.
- [x] Final wheel replay, complete tests, documentation links, build/install,
  and clean-clone Workspace smoke pass before `v0.9.9` is tagged and pushed.

## Work

- [x] Recover the rejected `0.9.0` Taiwan assignment and isolate its unclosed
  data-authority condition.
- [x] Prepare the exact installed-wheel, zero-data worker boundary and baseline
  evidence inventory.
- [x] Run and independently review the fresh `0.9.8` worker.
- [x] Implement only reproduced reusable friction and rerun the assignment.
- [x] Complete final verification, release documentation, tag, and push.

## Findings and decisions

- 2026-08-01 — Repeating the caller question is intentional: the earlier
  result was never accepted, and the identical authority condition gives a
  direct before/after measure of Agent employability rather than a new toy
  demo.
- 2026-08-01 — The research gate is semantic, not “two HTTP requests.” TWSE
  official raw plus FinMind raw can support numerical overlap comparison;
  Yahoo split-adjusted history may support coverage context but cannot satisfy
  the required raw peer role.
- 2026-08-01 — A truthful blocked result can pass the worker-compliance part of
  the trial while leaving provider availability external. It does not justify
  inventing a `0.9.9` feature or weakening the caller's requirement.
- 2026-08-01 — The fresh `0.9.8` Grok worker passed the authority gate: it
  wrote the English brief first, attempted official TWSE and FinMind, retained
  the 307 route failure and complete six-name FinMind peer package, performed
  no Project intake, Run, or Report, and returned `UNSUPPORTED` rather than a
  single-source Factor answer.
- 2026-08-01 — The TWSE provider script did not itself retain the 307 response
  body or request-level receipt. The worker manually probed the same authorized
  URI to make its handoff auditable. `0.9.9` makes that failure evidence a
  deterministic provider-Skill output and corrects same-raw comparison
  guidance to FinMind; Yahoo remains coverage-only when semantics differ.
- 2026-08-01 — The final installed-`0.9.9` replay reproduced the same local
  TWSE 307 block without a manual probe. The provider Skill automatically
  retained five exact 800-byte security bodies, their hashes and paths, the
  exact official URI, status/reason, and safe response headers, then emitted
  provider- and route-level failure receipts without a success package.
- 2026-08-01 — The final worker created a blank brief-first Project scaffold
  but performed no dataset intake, Study, Session, Run, Report, or quantitative
  interpretation. This respects the acceptance boundary: construction notes
  may exist before the gate, while authoritative Project intake may not. The
  conditional admitted-Factor requirement was not exercised because G1 failed.

## Verification

- `uv run python -m unittest discover` — 378 tests passed in 928.146 seconds.
- `uv run python scripts/check_doc_links.py` — all 1,306 double-links resolve.
- `uv lock --check`, `git diff --check`, complete Python compile, explicit
  Python 3.9 TWSE-script compile, Studio JavaScript syntax, and canonical
  `fetch-twse-ohlcv` Skill validation passed.
- `uv build` rebuilt the source distribution and wheel. A fresh Python 3.11.14
  environment installed the wheel, reported `aq 0.9.9`, exposed all 52 public
  commands, initialized an empty Workspace, created and validated one blank
  smoke Project, and passed orientation.
- Final wheel SHA-256:
  `049369a2178cab7b4efdf92c8d89615912c695cf233ecb38701141e7e6599c6d`.
- A no-hardlink clone without local override passed root `aq orient`,
  `aq validate`, `aq project list`, and `aq studio snapshot` while retaining a
  clean worktree.
- Final Grok 4.5 session `019fba6f-cb96-7a30-8a29-6fcf8cc714d5`
  used 17 turns and candidate wheel SHA-256
  `eaf14173a280ba8d923cbea6e5ac4cbefa140eeed191d0a3210664366b8921d9`.
  The final artifact rebuild changed only packaged release documentation and
  was freshly installed and capability-smoked afterward. Host audit of the
  replay confirmed automatic official failure receipts, a valid FinMind peer
  package, no manual
  probe or private implementation inspection, and no authoritative research
  artifacts after the failed gate.

## Progress log

- 2026-08-01 — Created the `0.9.9` field plan from clean released `v0.9.8`
  after auditing the prior Taiwan trial and current acquisition Skills.
- 2026-08-01 — Prepared `cohort-17-authority-gated-twse-factor-v098` with the
  exact released wheel, Python 3.11.14, all 16 materialized Skills, zero
  Projects, zero staged data, and an explicit no-single-source-completion
  worker contract.
- 2026-08-01 — Grok session `019fba62-c38f-7292-ad58-cf2ad1e6ddb7`
  completed in 12 turns without repository/package source inspection. Host
  review confirmed zero Projects/Runs/Reports, a standard official route
  failure, a valid FinMind V4 peer package, and no unauthorized source.
- 2026-08-01 — A live Python 3.9-compatible source smoke reproduced TWSE's
  HTTP 307 and automatically preserved all five exact security bodies, safe
  response headers, request hashes/paths, provider failure, and standard route
  failure without a second probe or false dataset package.
- 2026-08-01 — Grok session `019fba6f-cb96-7a30-8a29-6fcf8cc714d5`
  replayed the unchanged assignment from an empty installed-`0.9.9` Workspace
  in 17 turns. Host review confirmed automatic provider receipts, a valid
  six-name FinMind raw peer package, no Yahoo fallback or manual TWSE probe,
  no private package/repository source inspection, and an explicit
  `UNSUPPORTED` handoff with no authoritative research artifacts.

## Completion

Completed in `v0.9.9`. AutoQuant now preserves exact bounded TWSE provider
failure evidence at the Skill boundary, guides raw Taiwan peer comparison to
FinMind rather than Yahoo, and has independently proved that a fresh coworker
can stop truthfully when the caller's data authority remains unavailable.
OpenAlice remains unchanged at `0.8.31`.
