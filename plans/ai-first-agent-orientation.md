# Make AutoQuant immediately operable by a new research Agent

- Status: `active`
- Updated: `2026-07-25`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]],
  [[docs/design/research-program-orchestration]],
  [[docs/design/research-session-loop]], and
  [[docs/design/study-run-evidence]].

## Outcome

A new coding Agent can enter any AutoQuant Workspace or Project, run one
read-only command, and receive a compact verified work brief that identifies
the current research question, scientific stage, evidence blocker, exact
editable worktree boundary, protected authority, and one executable next
action with its effect. The same Core-authored brief drives Studio's human
decision card, so the AI operator and human reviewer cannot be shown different
instructions.

## Context

AutoQuant already exposes truthful state through `aq project program`,
`aq study inspect`, `aq session show`, immutable Runs, and structured
`nextActions`. The information is nevertheless spread across several deep
objects and assumes that a caller already understands Workspace, Project,
Study, Session, Run, Report, Dossier, lane phase, and scientific progression.

On the current real five-asset Project, `aq project program --json` emits about
13.8 KB. It correctly identifies Factor as the focus and provides an exact
baseline command, but a fresh Agent must still infer:

- whether it should edit canonical Project source or a disposable Session
  worktree;
- which paths are candidate-editable and which belong to fixed authority;
- whether the absence of downstream work is a scientific gate or missing
  coordination evidence;
- which one of several inspect, execute, start, evaluate, report, complete, or
  promote operations is the immediate job;
- which evidence may guide selection and which visible-test evidence is audit
  only.

The primary AutoQuant operator is an AI Researcher. Humans supply intent,
authority, review, and acceptance. The default interface must therefore be a
machine-stable work contract with a concise human projection, not a
documentation scavenger hunt.

## Scope

### In scope

- Add a read-only `aq orient <workspace-or-project> [--project ID] [--json]`
  operation.
- Build one strict Core `AgentWorkBrief` from already verified Project, Study,
  research-program, Session, Run, Report, Dossier, and progression state.
- Cover blank, single-Study, canonical three-lane research-desk, active
  Session, terminal Session, stale evidence, blocked gate, conflict, and
  completed-required-research states.
- Expose the research question, current focus, evidence state, blocker,
  selection/test authority, exact operating root, editable closures, protected
  categories, and one primary next action.
- Distinguish `observe`, `establish-baseline`, `edit-and-evaluate`,
  `publish-evidence`, `complete`, and `promote` operating modes without adding
  another lifecycle state machine.
- Make canonical Project source versus disposable Session-worktree authority
  explicit. A governed research Agent must never be told to edit the canonical
  Project while an active Session worktree owns candidate changes.
- Include exact `argv`, working directory, operation effect, and expected
  evidence kind for the primary action.
- Let Studio render the exact Core work brief and hash as the first human
  decision surface.
- Add capability discovery, strict schema, deterministic fixtures, legacy
  behavior, canonical docs, package checks, and bounded browser QA.

### Out of scope

- Automatically executing the recommended command.
- Choosing a model/provider, writing prompts for one vendor, or adding a
  generic autonomous Agent.
- Changing Factor/Portfolio/RL admission, Judge objectives, KEEP/REVERT,
  promotion, Report, or Dossier authority.
- A generic shell planner, OS sandbox, Broker/UTA access, or trading action.
- Adding more quantitative models or improving factor quality.
- Shortening Judge/backtest runtime or adding a new fast-check operation.
  Research-feedback latency will be a separate plan after orientation exposes
  the existing tiers truthfully.

## Acceptance

- [ ] From a Workspace or selected Project path, `aq orient --json` returns one
      strict versioned envelope and never mutates Project or research state.
- [ ] A fresh Agent can identify the question, current lane/Study/Session/Run,
      scientific blocker, exact operating root, editable closures, protected
      authority, and primary executable action without reading another CLI
      response.
- [ ] When no Session exists, the brief does not advertise direct canonical
      edits as the governed next step; when a Session is active, it points only
      to its disposable worktree and declared editable closure.
- [ ] Blocked progression, stale evidence, shared-source conflicts, reported
      baseline retention, promotion readiness, and completed required research
      each produce distinct stable reason codes and truthful actions.
- [ ] Selection authority remains validation-only, visible test remains audit
      only, and every brief states `tradingAuthority: none`.
- [ ] Studio and CLI consume the same Core object and hash; JavaScript does not
      independently infer the current research decision or next action.
- [ ] Human output fits one terminal viewport for the reference Projects while
      JSON omits raw histories and heavyweight diagnostic artifacts.
- [ ] Capability, schema, deterministic, legacy, browser, documentation,
      package, and full regression checks pass before commit and push.

## Work

- [x] Audit current Project/program/Study/Session status and next-action
      surfaces.
- [x] Define the AI-operator/human-reviewer authority model and bounded first
      milestone.
- [ ] Implement and schema one Core Agent Work Brief projection.
- [ ] Add `aq orient`, capability discovery, human output, and JSON contract.
- [ ] Replace Studio's browser-authored decision inference with the frozen Core
      work brief.
- [ ] Exercise every coordination/scientific state with deterministic tests
      and one real Project.
- [ ] Complete browser, package, documentation-link, and full-regression
      evidence; commit and push the fixed milestone.

## Findings and decisions

- 2026-07-25 — `aq project program --json` is already the correct verified
  status substrate. The new work brief will project it rather than introduce a
  parallel Project or research lifecycle.
- 2026-07-25 — The current real Yahoo research-desk status is roughly 13.8 KB
  and correctly recommends a Factor baseline, but it does not directly state
  the safe edit root or protected authority expected by a fresh Agent.
- 2026-07-25 — The external Researcher turn brief already proves the value of
  supplying fresh objective, editable paths, leader, history, budget, and
  response contract without terminal scraping. Orientation generalizes that
  principle to the pre-Session and cross-lane entry point.
- 2026-07-25 — `aq orient` is a projection and routing command, not a new state
  machine. Every phase, blocker, and action must be derived from existing
  verified Core objects.
- 2026-07-25 — Canonical Project paths may describe source ownership, but the
  governed Agent edit surface is a Session worktree. The brief must not make a
  direct canonical edit look equivalent to a Session Experiment.
- 2026-07-25 — Fast factor feedback is important but has different correctness
  and budget questions. It will follow as a separately indexed plan rather
  than weakening the orientation milestone.

## Verification

Pending.

## Progress log

- 2026-07-25 — Plan activated after auditing the existing CLI/program/session
  surfaces and confirming that trustworthy state exists but is not yet
  compressed into an AI-first work contract.

## Completion

Pending.
