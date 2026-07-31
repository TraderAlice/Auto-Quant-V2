# Authority-gated TWSE Factor field trial

- Status: `active`
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

- [ ] A fresh worker starts from the exact `v0.9.8` wheel, no staged OHLCV,
  public CLI/schema/Skills only, and preserves a complete transcript.
- [ ] The English research brief fixes the six TWSE listings, raw daily
  semantics, date window, 10-session horizon, official-plus-peer authority
  gate, research-only scope, and truthful stop condition before acquisition.
- [ ] Official TWSE and FinMind attempts use the bundled routes and preserve
  exact success or standard bounded failure evidence without hidden fallback.
- [ ] No numerical cross-source agreement is claimed unless adjustment,
  sessions, symbols, and price/volume semantics are compatible; Yahoo cannot
  masquerade as a raw peer.
- [ ] Project intake and quantitative interpretation occur only if both
  required raw routes and their bounded comparison pass. Otherwise the final
  handoff is explicitly unsupported and contains no authoritative Run/Report.
- [ ] If admitted, exactly one bounded Factor investigation answers the fixed
  hypothesis, separates train/validation/test audit, and grants no target-
  weight or trading authority.
- [ ] Every material baseline failure is either a reproducible Workbench gap
  repaired with regression coverage or an explicit provider/worker limitation.
- [ ] Final wheel replay, complete tests, documentation links, build/install,
  and clean-clone Workspace smoke pass before `v0.9.9` is tagged and pushed.

## Work

- [x] Recover the rejected `0.9.0` Taiwan assignment and isolate its unclosed
  data-authority condition.
- [ ] Prepare the exact installed-wheel, zero-data worker boundary and baseline
  evidence inventory.
- [ ] Run and independently review the fresh `0.9.8` worker.
- [ ] Implement only reproduced reusable friction and rerun the assignment.
- [ ] Complete final verification, release documentation, tag, and push.

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

## Verification

Pending.

## Progress log

- 2026-08-01 — Created the `0.9.9` field plan from clean released `v0.9.8`
  after auditing the prior Taiwan trial and current acquisition Skills.

## Completion

Pending.
