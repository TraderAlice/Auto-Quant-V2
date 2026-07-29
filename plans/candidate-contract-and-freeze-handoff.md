# Expose the candidate contract and honor freeze handoffs

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]],
  [[docs/design/causal-multi-interval-factor-inputs]], and
  [[docs/design/evidence-driven-research-agenda]].

## Outcome

Before editing a factor candidate, a Coding Agent can read one verified public
contract that states the actual Project panel clock, available completed
feature intervals, panel columns, component metadata fields, and legal
component roles. After an unsuccessful trial restores a strong baseline, the
Agent Work Brief follows a verified freeze/external-holdout agenda instead of
simultaneously demanding another in-sample edit.

## Context

A fresh external Grok Build coworker used only the installed AutoQuant
`0.8.14` CLI for a one-trial multi-horizon pullback-to-target-weight
assignment. It independently chose `ohlcv-portfolio-lab`, established a
successful baseline, started one Session, and kept all edits in the declared
worktree.

The default teaching Project is a legacy daily base-only fixture. Its shipped
candidate contains conditional 3h/12h/1d branches for compatibility with
request-intake Projects, but neither Study inspection nor orientation stated
that this particular Project had no completed feature intervals. The worker
therefore wrote an unavailable multi-hour hypothesis. Its one preflight first
failed on an empty final factor; after a local correction, the one Experiment
CRASHed because the natural-looking role `context-state` is outside the legal
`cross-sectional-score` / `timestamp-context` enum.

After CRASH restored the baseline, orientation reported `CANDIDATE EDIT
REQUIRED` while its verified research agenda reported
`no-further-in-sample-tuning` and recommended freezing for external evidence.
The worker stopped only because the delegated one-trial rule overrode the
generic edit label.

## Scope

### In scope

- Project the exact factor panel/component candidate contract through
  `study inspect`, Agent Work Brief, human CLI, JSON, and Studio.
- Distinguish legacy base-only data from a content-locked V2/V3/V5 interval
  surface without inventing unavailable higher intervals.
- State the legal component roles and metadata fields at the edit handoff.
- Let bounded preflight reject illegal static component metadata before
  executing the final factor.
- When current verified leader evidence yields
  `no-further-in-sample-tuning`, make an unchanged active Session an
  observe/freeze handoff rather than a generic candidate-edit requirement.
- Preserve an explicit optional read-only Session inspection path and explicit
  user-owned continuation; do not silently close or mutate the Session.

### Out of scope

- Pretending the legacy teaching fixture contains multi-hour data.
- Changing its historical prices, baseline metrics, or selection evidence.
- Claiming the preflight panel differs from the formal Judge: independent
  inspection shows both use the same base-only dataset contract.
- Automatically retrying a candidate, granting extra experiment budget, or
  weakening immutable CRASH evidence.
- Adding a universal factor DSL or changing component diagnostic authority.

## Acceptance

- [x] Base-only teaching Projects disclose `featureIntervals: []`, while
      request-intake Projects disclose their exact canonical interval surface.
- [x] Factor edit handoffs disclose the panel API, actual available columns,
      required component metadata fields, and exactly
      `cross-sectional-score` / `timestamp-context` roles.
- [x] The same candidate contract is available from Study inspection,
      orientation, schema validation, human CLI, and Studio projection.
- [x] Illegal component roles fail bounded preflight before final-factor
      execution or formal Experiment evaluation.
- [x] A baseline-restored active Session plus verified
      `no-further-in-sample-tuning` agenda has no primary edit action, uses
      observe mode, explains freeze/external-holdout, and retains only
      supporting read-only Session inspection.
- [x] Ordinary initial, changed, failed-check, passing-check, KEEP, and
      promotion Session routes remain unchanged.
- [x] Focused/full regression, docs, build/install smoke, and one fresh
      installed-wheel Grok retry pass.

## Work

- [x] Reproduce the worker's Run, Check, CRASH, orientation, and agenda
      evidence from installed `0.8.14` public surfaces.
- [x] Correctly classify the reported panel mismatch as missing Project
      contract discovery rather than divergent preflight/Judge data.
- [x] Implement and validate the public candidate contract.
- [x] Implement static preflight metadata validation and freeze-aware
      orientation.
- [x] Update public docs and originating Project need disposition.
- [x] Complete clean installed-wheel retry and release audit.

## Findings and decisions

- 2026-07-29 — Conditional higher-interval code in a reusable template is not
  evidence that a particular Project supplies those columns. The verified
  Project must project its actual data surface before an Agent chooses a
  hypothesis.
- 2026-07-29 — `factor-diagnostics` contains the component-role enum deep in a
  post-Run schema, but that is not an adequate edit-time contract. Put legal
  roles next to the candidate API and actual panel surface.
- 2026-07-29 — The worker's preflight/Study mismatch diagnosis is declined:
  both preflight and Judge call the same loader and fall back to the same
  legacy OHLCV files. Missing contract discovery caused the false assumption.
- 2026-07-29 — A research agenda that explicitly freezes the current source
  must outrank generic “leader restored, edit again” coordination language.
  Core will not infer a trial budget or close the Session automatically.

## Verification

- Fresh installed-wheel Grok retry: one baseline, one Session, one passing
  preflight, one REVERT Experiment, no promotion, and final freeze handoff.
- High-risk regression slice: 79/79 tests in 250.231 seconds.
- Full repository regression: 304/304 tests in 907.116 seconds.
- Documentation graph: 1,064/1,064 checked links.
- Source distribution and wheel built; fresh Python 3.11 install reported
  `aq 0.8.15`.
- Installed CLI verified capability/schema discovery, clean-root sample
  validation/default orientation, candidate-contract parity across
  orientation and Study inspection, local-override discovery, and exact
  CLI/Studio Work Brief parity.

## Progress log

- 2026-07-29 — Activated from installed-wheel Project
  `grok-build-multihorizon-pullback-v0814`. Baseline Run
  `run-20260729T142247215245Z-a3b6d26f4dd8` succeeded at validation net Sharpe
  `1.761404`; Check
  `check-20260729T142415996935Z-4c958a413a7a` failed `factor.empty`; Experiment
  `exp-0001-84b7bd3a56e6` CRASHed `factor.component-role`; baseline remained
  leader and no promotion occurred.
- 2026-07-29 — A fresh `0.8.15` release-candidate wheel retry independently
  read the exact daily base-only contract, used legal component metadata,
  passed Check `check-20260729T150219634466Z-de18f4e1a36f`, and spent exactly
  one Experiment `exp-0001-abbd17eaf907`. The pullback REVERTed and final
  orientation froze the restored baseline with no primary action.
- 2026-07-29 — Retry feedback added one explicit interval-availability rule
  and distinguished predeclared bounded Session authority from a diagnostic
  freeze recommendation before the first Experiment.

## Completion

Completed on 2026-07-29. Release `v0.8.15` preserves the independent Project
evidence and closes its promoted Workbench needs without changing immutable
research outcomes.
