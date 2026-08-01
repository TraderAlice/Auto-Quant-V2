# Frozen-holdout research handoff

- Status: `completed`
- Updated: `2026-08-01`
- Target release: `0.9.11`
- Related design: [[docs/design/frozen-external-holdout-challenge]],
  [[docs/design/program-research-dossiers]],
  [[docs/design/run-bound-research-reports]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove that a fresh quantitative coworker can take one completed Factor and
Portfolio research conclusion plus a caller-supplied strictly later dataset,
freeze the exact selected research objects, run the existing external-period
challenge, and leave a durable evidence-backed answer to the caller's actual
question: does the original conclusion still hold in the new period?

## Context

AutoQuant already has a scientifically conservative frozen-holdout protocol.
It imports the exact leader source closure from a current Dossier, requires a
separate later non-overlapping Project, prohibits new selection, and publishes
one immutable external-temporal-audit result per included lane. Earlier field
use proved the atomic flow for a Factor-only Dossier.

The next real maintenance question is broader than whether the command runs.
A completed coordinated Project may have concluded both that a Factor is
predictive and that its mechanical target translation is viable after costs.
When a later period arrives, a coworker must discover the frozen path, preserve
the original evidence, execute every included lane, interpret heterogeneous
Factor and Portfolio diagnostics without inventing one universal pass rule,
and produce a handoff that another Agent or human can recover from files.

The field trial comes before any new abstraction. Existing direct Reports,
Dossiers, holdout result state, ordinary Markdown, and Studio may already be
sufficient. Only independently reproduced operator friction may become a
Workbench change.

## Field assignment

Start from the completed `0.9.4` NVDA/QQQ relative-value Project and its current
Factor-plus-Portfolio Dossier. The selected frozen candidate asks whether
ten-session relative momentum supports a bounded dollar-neutral NVDA versus
QQQ model target, with AAPL, MSFT, and SPY restricted to context.

Supply a deterministic, task-complete, strictly later panel with the exact
same market clock, interval, adjustment meaning, asset universe, and request
authority. Ask a fresh worker whether the original Factor qualification and
Portfolio viability conclusions survive the later period. The worker may not
retune sources, start a Session, reinterpret context assets as tradable, or
convert historical evidence into an Order or live-trading approval.

## Scope

### In scope

- Reuse the current Dossier as the only candidate and lane authority.
- Exercise atomic lane-aware target creation and one-shot Factor/Portfolio
  holdout execution from an installed release wheel.
- Preserve source Project evidence byte-for-byte and keep the target frozen.
- Require a durable caller-facing interpretation that identifies both source
  and holdout evidence and separates Factor persistence from Portfolio
  post-cost viability.
- Audit CLI orientation, next-action routing, Report/Dossier compatibility,
  Studio projection, and filesystem discoverability after terminal execution.
- Promote only reproducible field friction into the smallest coherent public
  contract change.

### Out of scope

- Re-estimating, retuning, promoting, or automatically replacing the frozen
  candidate after later-period inspection.
- A universal pass/fail threshold across Factor IC, Portfolio Sharpe, or RL
  objectives.
- Shared mutable latest-data caches, automatic downloads, background refresh,
  or a general model registry.
- Cross-universe transfer, universe drift, overlapping windows, or non-temporal
  stress datasets.
- Broker, Order, TP/SL, account, execution, suitability, or trading authority.

## Acceptance

- [x] One released-wheel baseline starts from a current verified
      Factor/Portfolio Dossier and one complete strictly later compatible
      dataset package.
- [x] A fresh worker discovers and completes the frozen path without private
      source inspection, candidate edits, Session creation, or target
      selection.
- [x] Both lanes execute exactly once and expose source/later objective values,
      deltas, complete diagnostics, immutable identities, and external-audit
      authority.
- [x] The final handoff answers whether each original conclusion weakened,
      persisted, or remains inconclusive without manufacturing a universal
      threshold or trading recommendation.
- [x] Source Project evidence remains byte-identical; the target remains
      content-verifiable, non-iterative, and recoverable through CLI and
      Studio.
- [x] Every material operator failure is either repaired with deterministic
      regression coverage or retained as an explicit research/provider limit.
- [x] Final wheel replay, complete tests, documentation links, build/install,
      and clean-clone Workspace smoke pass before `v0.9.11` is tagged and
      pushed.

## Work

- [x] Audit the existing frozen-holdout, Report, Dossier, orientation, and
      target-freeze contracts before proposing a new surface.
- [x] Prepare the exact source baseline, strictly later package, isolation
      rules, and immutable source inventory.
- [x] Run and review a fresh installed-`0.9.10` worker against the unchanged
      caller-style assignment.
- [x] Implement only reproduced reusable friction and replay the same task.
- [x] Complete release documentation and final verification, tag, and push.

## Findings and decisions

- 2026-08-01 — The correct scientific operation for “does the old conclusion
  still hold?” is the existing frozen external temporal audit, not a refreshed
  Study that may reopen selection. Same-Project data vintages answer repeated
  fixed descriptive questions; a selected Factor/Portfolio claim instead
  needs candidate freeze plus strictly unseen later evidence.
- 2026-08-01 — Separate source and target Projects are intentional here. The
  target is disposable execution state for a one-shot audit, while the source
  Project remains the long-lived research lineage and selection record.
- 2026-08-01 — The current Holdout Core already governs exact sources,
  non-overlap, per-lane execution, and authority. The unknown is the research
  handoff after execution, so no Report/Dossier schema change is authorized
  until a fresh worker demonstrates the need.
- 2026-08-01 — A fresh isolated Grok 4.5 worker using only the installed
  `0.9.10` wheel created the target and executed both lanes exactly once. The
  source Project's 93-file SHA-256 inventory remained byte-identical and the
  target validated, oriented, and projected into Studio without error.
- 2026-08-01 — The worker answered the mixed result correctly, but needed
  seven ad hoc Python inspections of raw Run artifacts after `holdout show`
  exposed only objective scalars. Its final `holdout-assessment.md` was a
  loose Project-root file invisible to Core. This reproduces one reusable
  handoff defect: verified result interpretation needs a bounded evidence
  read model plus an immutable result-bound Assessment, not another selection
  operation or a universal pass rule.
- 2026-08-01 — A second fresh Grok 4.5 worker used the installed candidate
  wheel and public CLI only. It did not inspect private package source or raw
  Run artifacts, did not rerun either lane, and published Assessment
  `holdout-assessment-cb7783b524a1aaf5` with overall `mixed`, Factor
  `weakened`, and Portfolio `strengthened`. The source Project remained
  byte-identical and the target retained exactly two Runs.
- 2026-08-01 — The candidate worker's only retry came from copying a relative
  `holdout-analysis.json` path from Workspace-root orientation. The executable
  `nextAction` now emits the absolute target-Project path, covered by a
  deterministic regression and a final installed-wheel smoke.

## Verification

- `uv run python -m unittest discover -s tests -v` passed all 381 tests in
  945.087 seconds.
- `uv run python scripts/check_doc_links.py` resolved all 1,321 documentation
  links; `uv lock --check`, Python compilation, JavaScript syntax, and
  `git diff --check` passed.
- The final source distribution and wheel built successfully. A fresh Python
  3.11.14 environment installed the wheel with pandas 3.0.5, reported
  `aq 0.9.11`, and exposed all 53 public commands. Wheel SHA-256:
  `b7247bc475d1fe601641b826268399a523fe8c74c2500d636cb4711d82525994`.
- A final installed-wheel copy of the completed unassessed target validated
  and emitted an absolute `holdout.assess --analysis` path.
- Browser QA loaded the assessed Project through the live read-only Studio,
  showed the lane-specific Assessment, and verified refresh after fixing the
  latent Factor qualification-card JavaScript error.
- A no-hardlink clone of the committed repository loaded the root Workspace,
  selected and validated `sample-research-desk`, listed Projects, oriented,
  and produced a Studio snapshot with the final installed wheel.

## Progress log

- 2026-08-01 — Plan created from the clean released `v0.9.10` state after the
  existing Holdout contract was audited. The completed `0.9.10` data-vintage
  plan was also moved from the active index to completed.
- 2026-08-01 — Completed cohort 20 against an exact installed `0.9.10` wheel.
  The result deliberately diverged across lanes (Factor primary IC
  `0.562 → 0.028`; Portfolio validation net Sharpe `12.90 → 15.35`), proving
  the handoff must preserve lane-specific interpretation. Transcript and
  fixtures remain outside the repository under
  `grok-field-trials/cohort-20-frozen-holdout-handoff-v0910`.
- 2026-08-01 — Completed cohort 21 against the installed `0.9.11` candidate.
  The worker used verified CLI projections rather than raw artifact
  reverse-engineering, published the immutable mixed Assessment, and left the
  source untouched. Transcript and fixtures remain outside the repository
  under `grok-field-trials/cohort-21-frozen-holdout-assessment-v0911`.

## Completion

`v0.9.11` closes the frozen-holdout lifecycle as `bound` → `completed` →
`assessed`. Core owns exact evidence identity and verification; the Agent owns
the lane-specific interpretation. The release adds no universal threshold,
new selection path, data inventory, execution authority, or OpenAlice change.
