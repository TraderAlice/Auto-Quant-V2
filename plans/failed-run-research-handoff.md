# Failed Run research handoff

- Status: `completed`
- Updated: `2026-08-02`
- Related design: [[docs/design/study-run-evidence]],
  [[docs/design/agent-operator-experience]],
  [[docs/design/research-program-orchestration]], and
  [[docs/design/quant-research-lifecycle]].

## Outcome

Make one immutable failed Run an honest re-entry point instead of making a new
Agent believe the Study has never run. An unchanged failed attempt must be
inspected before any repair, while a Judge-declared scientific limit can be
reported and handed off as the terminal result of the exact fixed question.

## Context

The `0.9.21` field worker correctly produced one structured failed Run after a
fixed sparse temporal Factor had no validation-period variation. The Run kept
the exact population counts and error, but the next `aq orient` discarded that
identity, reported `baseline-evidence-missing`, and recommended the identical
`run.execute` command. The durable evidence contract and the Agent work brief
therefore disagree.

`status: failed` includes both fixed scientific limits and defects requiring
repair. AutoQuant must not infer that every failure is a publishable research
conclusion, but neither class should be hidden or blindly repeated.

## Scope

### In scope

- Give every newly published failed Run an explicit, verified failure
  disposition: `scientific-limit` or `repair-required`.
- Let a Judge declare a scientific limit; classify process, timeout, malformed
  output, exception, and otherwise unclassified failures as repair-required.
- Project the latest current failed attempt, exact disposition, errors, and
  inspection action through Run CLI, orientation, research programs, and
  Studio.
- Permit an immutable Run-bound Report only for a current
  `scientific-limit` Run and make that Report the terminal handoff.
- Keep downstream Factor/Portfolio/RL admission closed because a reported
  scientific limit is not successful qualifying evidence.

### Out of scope

- Automatically choosing a replacement hypothesis, Study type, dataset, or
  provider.
- Starting a governed optimization Session without a successful baseline.
- Treating ordinary candidate, Judge, runtime, or infrastructure defects as
  scientific conclusions.
- Retrofitting a new disposition into immutable Runs created by older Harness
  versions.

## Acceptance

- [x] A current failed attempt is present in `aq orient` evidence and never
  appears as `baseline-evidence-missing` or an unchanged `run.execute` action.
- [x] A repair-required failure routes first to exact Run inspection and cannot
  be published as a Run-bound Research Report.
- [x] A scientific-limit failure routes to one immutable Run-bound Report;
  after publication orientation is terminal and offers no repeated execution.
- [x] CLI JSON, ordinary terminal output, research-program status, Studio
  snapshot, Report evidence, and canonical schemas agree on the disposition.
- [x] A fresh installed-wheel Grok worker can receive the sparse Factor task,
  create exactly one failed Run, publish or explain the exact bounded outcome,
  and stop without retrying or manufacturing a usable Factor.
- [x] Focused tests, complete unit tests, docs links, build, installed smoke,
  clean-clone smoke, and remote branch/tag identity pass for `v0.9.22`.

## Work

- [x] Extend Judge output and RunResult normalization with verified failure
  disposition while preserving older immutable Run readability.
- [x] Correct single-Study and research-program current-attempt selection,
  actions, agendas, Reports, and Studio projections.
- [x] Add deterministic scientific-limit, repair-required, stale-attempt,
  downstream-gate, and terminal-report tests.
- [x] Update Agent, CLI, Studio, Run evidence, orchestration, lifecycle, status,
  and release documentation.
- [x] Build the candidate wheel and run the fresh-worker field assignment.
- [x] Complete the release audit, commit, push, tag, and verify `v0.9.22`.

## Findings and decisions

- 2026-08-02 — An immutable failed Run proves an attempt occurred even when it
  cannot satisfy a Study objective. Re-entry must distinguish “no attempt”
  from “current attempt failed.”
- 2026-08-02 — Failure disposition is Judge/Core evidence, not an Agent guess.
  Missing or infrastructure-generated disposition is conservatively
  `repair-required`; only an explicit `scientific-limit` may be reported as the
  bounded conclusion.
- 2026-08-02 — Reporting a scientific limit closes only the exact fixed Study.
  It never opens downstream Portfolio/RL gates or grants trading authority.
- 2026-08-02 — Fresh Grok 4.5 used the installed candidate wheel, executed the
  fixed sparse temporal candidate exactly once, followed post-Run orientation
  to `report.publish`, authored the schema-valid Report, and stopped at
  `scientific-limit-reported` with no Session, Dossier, retry, or source edit.
- 2026-08-02 — The field worker found one public wording defect: Report CLI
  help still said “successful Run.” Help and capability discovery now disclose
  the exact scientific-limit exception. Its other observations were accurate
  boundaries rather than blockers.

## Verification

- Focused Run/Report/Orientation/Program/intake regression: 90 tests passed in
  308.306 seconds.
- Complete unit suite: 427 tests passed in 1,052.884 seconds.
- `uv lock --check`, Python byte compilation, Studio JavaScript syntax,
  `git diff --check`, and all 1,408 documentation links passed.
- Source distribution and wheel built successfully. A fresh Python 3.11.14
  environment installed the wheel as `aq 0.9.22` from `site-packages`, exposed
  57 public commands and all 16 packaged Skills, and disclosed the exact
  scientific-limit Report exception through both CLI help and capability
  discovery.
- The final installed wheel revalidated the isolated field Workspace with zero
  diagnostics and projected its terminal one-Run/one-Report result through
  orientation and Studio without mutation.
- A no-local-override clone independently passed root `validate`, `orient`,
  `project list`, and `studio snapshot` with zero diagnostics and a clean Git
  worktree.
- The published `origin/main` and annotated `v0.9.22` tag were verified to
  resolve to the same release commit.

## Progress log

- 2026-08-02 — Plan created from the `0.9.21` sparse temporal Factor field
  re-entry defect.
- 2026-08-02 — Focused Run/Report/Orientation/Program/intake regression passed
  90 tests in 308.306 seconds. Candidate wheel field session
  `3cfcd912-3b36-48ef-ab36-3a13c1a7ab73` created Run
  `run-20260801T165753420107Z-72ebe1da8796` and Report
  `report-20260801T165826235891Z-8a6f53803c20`; independent validate,
  orientation, and Studio audit returned zero diagnostics and exactly one Run,
  one Report, zero Sessions, and zero Dossiers.
- 2026-08-02 — Complete regression passed all 427 tests in 1,052.884 seconds;
  the release audit resolved 1,408 documentation links and passed lock, source,
  installed-wheel, package-content, field-replay, and clean-clone checks.

## Completion

Completed on 2026-08-02. AutoQuant now preserves an unchanged failed attempt as
first-class re-entry evidence, distinguishes reportable scientific limits from
repair-required defects, and makes only the exact reported scientific limit a
terminal no-retry handoff. The release was published as `v0.9.22`; OpenAlice's
independent `v0.8.31` Harness selection was not changed.
