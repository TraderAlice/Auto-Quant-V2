# Route a settled KEEP to guarded promotion

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]], and
  [[docs/design/research-session-loop]].

## Outcome

After a governed Session produces a KEEP and its worktree still matches the
accepted leader, a replacement coding Agent receives guarded promotion as the
single primary action instead of a contradictory instruction to edit another
candidate. Delegated Sessions expose promotion only when an exact current
Report makes the generated command executable.

## Context

The first editable Grok Build field trial under clean AutoQuant `0.8.10`
completed one Factor baseline, one Session, one passing candidate check, one
KEEP Experiment, and guarded promotion. Immediately after KEEP, however,
`aq orient` returned:

- `candidate-edit-required` before `promotion-ready`;
- `primaryAction: null`;
- `session.promote` only in `supportingActions`; and
- review text instructing another edit even though the worktree already
  matched the KEEP leader.

An independent disposable-Workspace replay reproduced the exact state. The
cause is ordering inside `_session_actions`: unchanged-candidate routing is
computed before non-baseline-leader promotion routing.

The same audit found that the CLI next-action builder already withholds
delegated promotion until an exact current Report exists and includes
`--report` when it does. Agent orientation must preserve that gate instead of
emitting a command that would fail.

## Scope

### In scope

- Make guarded promotion the primary action when an active non-delegated
  Session has a non-baseline KEEP leader and no newer candidate edit.
- For delegated Sessions, expose the same primary promotion only when an exact
  current Report binds the leader, including its `--report` argument.
- Keep check/evaluate routing primary when the worktree contains a newer
  candidate than the current leader; promotion may remain supporting there
  only when it is currently executable.
- Keep the first-edit state explicit and writable without inventing a fake CLI
  command for an Agent-owned code edit.
- Retain the exact passed candidate Check id/status through a settled KEEP
  handoff when its verified source, Study, preflight, and Harness identities
  remain current.
- Preserve CLI, JSON, Studio, and human orientation parity and cover both
  single-Study and research-program routes.
- Prove the change with a fresh external coding-Agent retry.

### Out of scope

- Automatically editing candidate source or executing promotion.
- Adding a structured Project trial budget; one-shot limits remain ordinary
  assignment intent in `research.md`.
- Changing KEEP, Report, promotion, downstream qualification, external
  holdout, or trading authority.
- Adding a new generic action type for free-form Agent code edits.

## Acceptance

- [x] A settled non-delegated KEEP returns `session.promote` as
      `primaryAction`, with `promotion-ready` as the leading reason and no
      `candidate-edit-required` contradiction.
- [x] A newer unmeasured worktree edit continues to route to candidate check
      or evaluation while any executable promotion remains secondary.
- [x] A delegated KEEP without a current Report never advertises an
      unexecutable promotion; an exact Report enables primary promotion with
      the required `--report` argument.
- [x] A fresh Session whose candidate still equals baseline retains the clear
      Agent-owned edit instruction, exact worktree, and editable closure with
      no fabricated command.
- [x] CLI JSON, human CLI, and Studio share the same updated work brief and
      next action.
- [x] Promotion-ready orientation retains the exact accepted candidate's
      passed Check pointer rather than dropping it after leader advancement.
- [x] Focused/full regression, documentation, build/install smoke, and a fresh
      Grok retry pass before the next patch release.

## Work

- [x] Preserve and independently reproduce the Project-derived routing defect.
- [x] Implement one executable-promotion projection shared across Session
      states.
- [x] Add single-Study, delegated-program, CLI, Studio, and regression tests.
- [x] Update durable Agent-operability and CLI contracts.
- [x] Retry with a fresh coding coworker and complete release verification.

## Findings and decisions

- 2026-07-29 — A null primary action is truthful while the next operation is
  an Agent-owned source edit. Pointing to `session.show` would be executable but
  would not advance the lifecycle, so the fresh-Session behavior remains.
- 2026-07-29 — The one-Experiment limit came from flexible assignment intent.
  Adding a machine trial-budget field would contradict the Workbench's
  Markdown-first task model and is declined.
- 2026-07-29 — Promotion is primary only when the worktree still matches the
  KEEP leader. Any newer edit must be checked/evaluated or intentionally
  discarded before promotion.
- 2026-07-29 — Delegated promotion is not executable without an exact current
  Report. Orientation will match the existing CLI next-action gate and include
  `--report` when eligible.
- 2026-07-29 — The fresh v6 retry passed every promotion-routing gate and
  exposed one adjacent audit gap: the accepted candidate's verified Check
  becomes non-current only because the Session leader advances to that same
  candidate. Orientation will retain an exact-identity Check pointer through
  promotion-ready/report-required handoff without weakening pre-evaluation
  freshness rules.

## Verification

- `uv run python -m unittest discover -s tests -q` passed all 296 tests.
- `uv run python scripts/check_doc_links.py` resolved all 1,048 links.
- `uv build` produced both the `0.8.11` source distribution and wheel.
- A fresh Python 3.11 wheel install created an empty Workspace and Factor
  Project, then completed baseline, Session, passing candidate Check
  `check-20260729T115350749976Z-2e8e29cbaf87`, KEEP Experiment
  `exp-0001-b576ca64fab8`, promotion-first human/JSON orientation, guarded
  promotion `promotion-20260729T115419616068Z-eb8e998b8f93`, validation, and
  Studio projection with Harness `0.8.11`, `commit: unavailable`, and
  `dirty: false`.
- The independent Grok v6 retry completed baseline
  `run-20260729T114022711352Z-fd48d6b1f7e9`, Check
  `check-20260729T114140454677Z-0aa3ee81da1a`, KEEP Experiment
  `exp-0001-d6a21935a2e3`, and guarded promotion
  `promotion-20260729T114209738602Z-8c863950d949` without a second
  Experiment.

## Progress log

- 2026-07-29 — Plan activated from
  `grok-build-session-loop-v010/framework-needs.md` under clean AutoQuant
  `0.8.10`; an independent temporary Session reproduced the contradictory
  post-KEEP work brief.
- 2026-07-29 — A fresh Grok v6 retry passed promotion routing and found the
  adjacent exact-Check pointer and worktree CLI re-entry gaps. The Check
  pointer was fixed in this release; worktree re-entry is preserved in
  [[plans/session-worktree-cli-reentry]].
- 2026-07-29 — Full regression, documentation, build, fresh-wheel lifecycle,
  guarded promotion, and Studio verification passed.

## Completion

AutoQuant `0.8.11` ships Agent Work Brief v6: a settled KEEP becomes one
executable guarded-promotion primary action, delegated Report gates and newer
candidate priority remain intact, and the accepted candidate's exact passed
Check remains visible through handoff. The separately indexed Session
worktree CLI re-entry plan preserves the only material operational friction
found by the successful retry.
