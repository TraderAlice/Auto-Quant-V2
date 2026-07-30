# Preserve caller fixed-weight benchmarks and exact RL preflight state

- Status: `active`
- Updated: `2026-07-30`
- Originating trial:
  `/Users/ame/2607AutoQuant/grok-field-trials/cohort-04-global-etf-governed-rl`
- Related: [[plans/agent-employability-validation]],
  [[docs/design/caller-owned-benchmark-reference]], and
  [[docs/design/agent-operator-experience]].

## Outcome

One research request accepted by the public schema produces the same immutable
fixed-weight benchmark in Portfolio and governed-RL evaluation, while the fast
RL candidate Check exercises the exact raw state contract advertised by the
real Judge.

After the bounded fixes, a different fresh installed-wheel worker must retry
the corrected global-ETF governed-RL assignment without source access or
framework-developer coaching.

## Context

Fresh worker 4 of the employability cohort correctly found negative adaptive
value and retained the mechanical baseline, but the attempt exposed two Core
contract contradictions:

1. the public research-request schema and normalizer accept
   `benchmarkPolicy.kind: fixed-weights`, while Portfolio Mandate construction
   rejects every supplied benchmark except cash or one asset;
2. the governed-RL program advertises fields such as
   `market_volatility_20`, pretrade net/cash/max-weight state, and candidate
   action distances, while the fast Check supplies an older partial state.

The worker also disclosed that the frozen assignment misstated the supplied
dataset start/end dates. That caller-packet error must be corrected before a
retry; it is not a Workbench defect and the retry cannot be labeled
byte-identical.

## Scope

### In scope

- Materialize a validated caller fixed-weight benchmark as complete
  research-universe weights in the shared Portfolio Mandate.
- Preserve strict positive, unit-sum, requested-asset-only intake validation.
- Validate and content-lock the same benchmark during mandate reload.
- Make the RL preflight raw state contain the complete current runtime field
  contract.
- Add focused regressions and publish the next patch release.
- Retry the same decision problem with corrected dataset identity and a new
  isolated worker.

### Out of scope

- New benchmark optimization, rebalancing semantics, data routes, policy
  actions, model families, or trading authority.
- Parsing prose task budgets or repairing worker-owned invalid JSON.
- Weakening Workspace selection, source confinement, Session delegation, or
  Report completion gates.

## Acceptance

- [x] A normalized fixed-weight research request builds and reloads one
      canonical caller-supplied benchmark with complete universe weights.
- [x] Unknown, negative, zero-total, non-unit-sum, or otherwise invalid
      caller benchmark weights remain rejected.
- [x] Portfolio and governed-RL Judges consume the same content-locked
      benchmark without a fallback to direction defaults.
- [x] An RL candidate that directly reads every advertised runtime state field
      passes the fast Check; a missing/invalid field still fails normally.
- [ ] Focused and full regressions, docs, build/install, version/capability,
      clean-clone, and Studio smoke pass for `0.8.30`.
- [x] A different fresh worker receives only the installed release candidate,
      corrected
      caller assignment, and staged data; its evidence and final answer are
      independently reviewed under the employability protocol.

## Work

- [x] Align Portfolio Mandate construction, reload validation, and schema with
      the already-public fixed-weight research-request contract.
- [x] Align the generic governed-RL preflight state with the exact runtime
      policy-state columns.
- [x] Add regression coverage for both contradictions.
- [x] Update version, public milestone docs, and validation records.
- [x] Build and install the exact wheel from a clean fixed commit.
- [x] Freeze and execute a corrected fresh-worker retry packet.
- [x] Record the retry and return to cohort synthesis.

## Findings and decisions

- 2026-07-30 — This is immediate Core work despite being observed by only one
  worker: both issues are direct contradictions between public contracts, not
  preferences or discoverability friction.
- 2026-07-30 — `fixed-weights` remains a caller-owned descriptive reference.
  It does not grant those assets tradability or make the benchmark an
  optimized candidate.
- 2026-07-30 — The initial worker's negative RL conclusion is scientifically
  useful, but the attempt is excluded from the final qualifying cohort because
  Core silently changed the requested reference and the caller packet had
  incorrect date facts.
- 2026-07-30 — Portfolio Mandates now carry `fixed-weights` as a distinct
  caller-supplied benchmark kind with complete research-universe weights.
  Portfolio and governed-RL share the same strict Judge resolver; no fallback
  reference is admitted.
- 2026-07-30 — Generic RL preflight now constructs exactly the current
  `POLICY_STATE_COLUMNS` surface. A regression candidate reads every field by
  its public name before any full Judge evaluation.
- 2026-07-30 — The fresh `0.8.30` candidate-wheel worker passed fixed-weight
  intake and its first state-encoder Check, then returned one evidence-backed
  REVERT and completed the delegated Session. This directly closes both
  originating contradictions.
- 2026-07-30 — One first baseline execution hit the intake template's
  120-second timeout; later locked executions completed in roughly 93–113
  seconds. The worker transparently discarded one temporary 180-second probe
  whose Study hash did not match intake. This is a first-occurrence runtime
  observation, not a reason to change the scientific contract or immediately
  raise every RL timeout.

## Verification

- Mandate, Check, Portfolio, and governed-RL focused regression: 46 tests
  passed in 143.118 seconds.
- One shared three-lane intake Project with a fixed-weight caller benchmark
  completed Factor, Portfolio, and governed-RL Runs successfully in 48.201
  seconds.
- Candidate wheel
  `auto_quant-0.8.30-py3-none-any.whl`
  (`90ea4f4…2cbdbb`) was built from clean commit `2636c5b`, installed in a
  fresh Python 3.11 environment, and exposed public version `0.8.30`.
- Fresh isolated Grok Build completed the corrected task in 939.45 seconds
  without source, docs/tests/plans, web, memory, subagents, or coaching.
  Fixed-weight intake succeeded directly; one Check passed on the first
  attempt; one Experiment returned REVERT; Report, completion, strict
  Explorer, final orientation, validation, and Studio independently
  reconcile. Full release regression remains in progress.

## Progress log

- 2026-07-30 — Activated from independently reproduced mandate construction
  and preflight/runtime contract mismatches in cohort worker 4.
- 2026-07-30 — Core contracts and regressions implemented; patch release and
  fresh-worker retry remain.
- 2026-07-30 — Corrected fresh-worker retry completed and independently
  reconciled. Only full release verification, tag, and push remain.
