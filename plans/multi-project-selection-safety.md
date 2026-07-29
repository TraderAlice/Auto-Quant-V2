# Multi-Project selection safety

- Status: `completed`
- Updated: `2026-07-30`
- Originating desk:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0821-multi-project-batch/desk/workspace`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/CLI]], [[docs/design/workspace-project-boundaries]], and
  [[docs/PROJECT_FORMAT]].

## Outcome

A Coding Agent can use one persistent Workspace containing several unrelated
Projects without silently publishing immutable evidence to whichever Project
happened to become the Workspace default first.

Read-only commands may continue to use the default Project, but their human
and JSON output names the Workspace, selection method, default, selected
Project, Project count, and available Project ids. Commands that create
Project-local artifacts or mutate a Project require an explicit `--project ID`
whenever their input path is a Workspace containing more than one Project.

## Context

A fresh installed-`aq 0.8.21` Grok worker completed two independent fixed
questions in one Workspace:

- `reported-book-risk-v0821` /
  `run-20260729T205409066255Z-d8a569e7290c`;
- `nvda-gap-event-v0821` /
  `run-20260729T205414156428Z-2f23c410cb04`.

Both Projects validated and Studio kept their evidence separate. The worker
also observed that the Workspace default remained the first-intaken reported
book after the event Project was created. `orient`, `inspect`, and `validate`
without `--project` therefore selected the reported book even when the
operator's conversational focus had moved to the event study.

The default is useful for a one-Project clone and read-only re-entry. It is
not sufficient authority for an artifact-producing command in a desk with
multiple Projects, because an immutable Run, Check, Experiment, Report, or
Dossier cannot be safely “moved” after a mistaken selection.

## Scope

- Detect whether a Project command entered through a direct Project path or a
  Workspace path.
- Preserve current default behavior for direct Project paths, single-Project
  Workspaces, and read-only commands.
- In a Workspace with two or more Projects, reject a Project-local
  state-changing command without `--project ID` before it creates any state.
- Surface structured selection provenance for read-only `orient`, `inspect`,
  and `validate` responses; add a compact human selection line.
- Let `orient` advertise `project list` when it selected a default from a
  multi-Project Workspace.
- Make public capabilities and durable docs state the rule.
- Do not change Workspace Studio's intentional all-Project observation or the
  explicit `project default` operation.

## Acceptance

- [x] Multi-Project Workspace state-changing commands fail before mutation with a
      structured issue that names the default and every available Project.
- [x] The same command proceeds when `--project` is explicit.
- [x] Direct Project and single-Project Workspace artifact commands retain
      existing behavior.
- [x] Read-only default and explicit selection both expose machine-readable
      Workspace/selection provenance.
- [x] Human `orient`, `inspect`, and `validate` output discloses the selected
      Project and selection method for Workspace entry.
- [x] `aq capabilities`, CLI help, architecture/boundary docs, and tests agree.
- [x] A fresh installed-wheel Grok retry completes the unchanged two-Project
      assignment with separated Runs and no default-directed artifact.
- [x] Full regression, documentation graph, wheel install, and exact-commit
      clone smoke pass before `v0.8.22`.

## Installed-wheel retry

A new no-memory, no-web, no-subagent Grok worker used only the built `0.8.22`
wheel under:

`/Users/ame/2607AutoQuant/grok-field-trials/v0822-multi-project-retry`.

After both Projects existed, the worker inspected Workspace orientation,
observed `stateChangeRequiresExplicitProject: true`, left the Workspace default
unchanged, and explicitly selected each Project for its fixed Run. It produced:

- `reported-book-risk-v0822` /
  `run-20260729T211540220465Z-5ba86b710638`;
- `nvda-gap-event-v0822` /
  `run-20260729T211544248069Z-445c4e607725`.

Independent verification found both Projects valid, one Run and zero Sessions
each, byte-identical Project-local dataset snapshots, and one valid
two-Project Studio snapshot with no diagnostics. A deliberate installed-wheel
`run execute` without `--project` returned
`workspace.explicit-project-required`; both Run counts remained unchanged.

## Verification

- `uv run python -m unittest`:
  312 tests passed in 803.410 seconds.
- `uv run python scripts/check_doc_links.py`:
  1,099 documentation double-links resolved.
- A fresh Python 3.11 environment installed the built `0.8.22` wheel and
  passed version, capability, Workspace, Project, orientation, and validation
  smoke.
- A clean clone of the release commit, without local Workspace override,
  rebuilt and installed the same wheel and passed root orientation, validation,
  Project discovery, Studio snapshot, version, and capability smoke before the
  tag was created.
