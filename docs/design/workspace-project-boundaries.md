# Workspace and Project boundaries

Status: implemented for repository-root/default and initialized Workspaces,
strict local discovery override, blank/template construction, and
request-driven self-contained Projects.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], and
[[docs/design/agent-cli-contract]], and
[[docs/design/agent-native-quant-workbench]].

## Scope

This document owns Workspace discovery, Project identity, root confinement,
self-contained starter creation, and default Project selection. It does not
own Study, Run, evaluation, research-loop, dataset-format, or Studio semantics.

## Core model

- An AutoQuant Workspace is a directory containing
  `autoquant-workspace.json` and one configured immediate Projects directory.
- It is a persistent quantitative desk that can be cloned and operated
  standalone or materialized by a host Workspace Template.
- The AutoQuant source clone is itself the canonical shipped Workspace. Its
  checked-in manifest discovers the checked-in `projects/` and selects one
  ordinary complete sample Project.
- A Project is a directory containing `autoquant.json`, its human research
  program, and every research surface it owns, including fixed Judges and
  immutable Run/Experiment evidence and durable research Sessions.
- The Workspace has no dataset, factor, strategy, model, Study, or Run catalog.
- Reuse is explicit copying or a future content-addressed dependency. Mutable
  inherited research assets are forbidden.
- Every Project command resolves exactly one Project before loading any
  quantitative domain configuration.
- The first created Project becomes the default. Later changes to the default
  are explicit Workspace mutations.
- A new research request normally creates or continues a Project. It does not
  require a fresh Workspace unless environment or ownership isolation is
  intentional.
- Durable Project research state is ordinary Git-managed Workspace state.
  Project-local data and cache policies remain separate.
- A Workbench developer may place one ignored complete
  `autoquant-workspace.local.json` beside the base manifest. Its presence is
  explicit authority to select an external Projects directory for that
  checkout; it does not change the default distributed Workspace.

## Source of truth

- Core schemas, creation, loading, resolution, and inspection:
  `autoquant/workspace.py`
- CLI projection: `autoquant/cli.py`
- Canonical public file format: [[docs/PROJECT_FORMAT]]
- Confinement and isolation tests: `tests/test_workspace.py`
- End-to-end CLI tests: `tests/test_cli.py`

## Invariants

1. Project ids use lowercase kebab-case and equal their immediate directory
   names.
2. Workspace discovery scans exactly one directory level and rejects visible
   files, incomplete entries, and symlink Projects.
3. Workspace and Project roots, the effective Projects directory, the
   research program, and declared Project directories cannot be symlinks.
4. The checked-in manifest uses POSIX relative paths confined beneath its
   Workspace. Only the ignored local override may name a relative escape or
   absolute external Projects path.
5. Manifest objects are strict; unknown keys and unsupported schema versions
   fail validation.
6. A directory cannot be both a Workspace and Project.
7. A direct Project path cannot receive a redundant Workspace `--project`
   selection.
8. Project creation stages a complete blank, explicitly selected reference
   template, or validated request/dataset intake in a hidden temporary
   directory and atomically renames it into discovery.
9. Project data and cache contents are ignored by their own `.gitignore`
   files. Neither location is durable system truth.
10. Changing one Project does not change another Project's files or identity.
11. Host-specific metadata may surround a Workspace but cannot redefine
    Project discovery, quantitative identity, or evaluation semantics.
12. An invalid local override fails explicitly; Core never silently falls back
    to the checked-in Projects.
13. Project creation and default selection write to the effective
    configuration file, so local development cannot accidentally mutate the
    shipped manifest.
14. CLI and Studio disclose the effective Projects path, configuration path,
    and whether discovery comes from the Workspace manifest or local override.

## File-to-operation flow

```text
autoquant-workspace.json
→ optional strict autoquant-workspace.local.json
→ effective Workspace configuration and Projects path
→ confined immediate Project discovery
→ default or explicit Project selection
→ strict autoquant.json load
→ required owned-path validation
→ Project context
→ CLI validate/inspect projection
```

Project creation travels the reverse direction: strict id, Workspace, and
template/intake validation → hidden staged starter → optional self-contained
template population and Study validation → atomic rename → optional
first-default Workspace update.

## Non-goals

- Shared mutable Workspace datasets, strategies, models, or inherited
  templates. Construction templates are copied/generated into Project
  ownership.
- Recursive Project discovery.
- Git repositories as Project identity.
- Owning Study or Run semantics, which are defined in
  [[docs/design/study-run-evidence]].
- Migrating external real research cases into the shipped repository sample.

## Change checklist

- Update schema emitters, parsers, starter creation, and canonical format
  documentation together.
- Add rejection tests for every new path-bearing field.
- Prove a Workspace with at least two Projects resolves and inspects them
  independently.
- Project new operations through both human and JSON CLI paths.
- Update Studio source projection and browser labeling with every Workspace
  configuration change.

## Verification

```bash
uv run python -m unittest tests.test_workspace tests.test_cli -v
uv run python -m unittest tests.test_repository_workspace -v
uv run aq project list . --json
uv run aq validate . --json
uv run aq studio snapshot . --json
```

## Known gaps

- Project manifests expose semantic directory slots, including `sessions`, but
  do not select a default Study, dataset, Session, or execution profile.
- Project identity is strict path identity but not yet a content hash.
- There are factor, portfolio, and governed RL reference templates plus strict
  caller-supplied daily-OHLCV intake. Network/provider adapters and additional
  Broker/backtest adapters remain future work.
