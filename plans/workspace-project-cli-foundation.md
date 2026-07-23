# Establish Workspace, Project, and Agent CLI foundations

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/ARCHITECTURE]],
  [[docs/design/workspace-project-boundaries]], and
  [[docs/design/agent-cli-contract]].

## Outcome

A human or Agent can initialize one long-lived AutoQuant Workspace, create
multiple self-contained research Projects, select and validate exactly one
Project through either its direct path or Workspace identity, and discover the
same operations through a versioned machine-readable CLI contract.

## Context

AutoQuant V0.5 still treats the framework repository as one mutable research
arena. The V2 north star instead needs a standardized Harness workbench whose
Projects are the concrete construction sites for strategy, factor, and later
ML research.

Integrated Industry Maker and Mujica Robot already prove the useful boundary:
the Workspace contains only discovery and a default Project; immediate Project
directories are real, non-symlink directories; Project ids match their
directory ids; and commands resolve one Project before domain loading.
INM's richer CLI contract also proves that Agents benefit from versioned
success/error envelopes, capability discovery, artifact references, operation
effects, and executable next actions.

## Scope

### In scope

- Strict `autoquant-workspace.json` and `autoquant.json` V1 manifests.
- Workspace initialization, Project creation/list/default, direct or Workspace
  Project resolution, validation, inspection, and schema/capability discovery.
- Self-contained Project starter directories for research instructions,
  strategies, factors, models, studies, project-local data, and Runs.
- Path confinement, id/directory equality, immediate-directory discovery, and
  symlink rejection.
- A lightweight `aq` entry point with human output and versioned JSON
  success/error envelopes containing contexts, artifacts, and next actions.
- Canonical Project-format, CLI, and design documentation plus fast tests.

### Out of scope

- Moving the current V0.5 strategy arena into a generated Project.
- Study, Session, RunResult, Candidate, locked Judge, or promotion semantics.
- Executing Freqtrade, factor research, ML training, or an autonomous loop.
- Studio implementation.
- Shared mutable datasets, strategies, models, or other Workspace catalogs.

## Acceptance

- [x] `aq workspace init`, `aq project create/list/default`, `aq validate`, and
  `aq inspect` work through both human and JSON surfaces.
- [x] A Workspace with two Projects resolves its default or an explicit
  `--project` without loading another Project.
- [x] Escaping `projects_directory`, symlink Project entries, unknown manifest
  keys, invalid ids, mismatched directory ids, and missing starter paths fail
  with structured issues.
- [x] `aq capabilities --json` describes every public command, argument,
  operation effect, output contract, and exit behavior.
- [x] Created Projects are self-contained construction sites for strategies,
  factors, models, studies, project-local data, Runs, and research guidance.
- [x] Documentation links, the complete bounded unit suite, and a real
  temporary-Workspace CLI flow pass without downloading data or backtesting.

## Work

- [x] Audit the current AutoQuant repository and the corresponding INM/Mujica
  Workspace and CLI contracts.
- [x] Define canonical Workspace/Project formats and CLI envelopes.
- [x] Implement strict Core loading, creation, resolution, and inspection.
- [x] Implement the `aq` human and JSON CLI surfaces.
- [x] Add confinement, isolation, envelope, and end-to-end CLI tests.
- [x] Update architecture and public documentation.
- [x] Run final acceptance, complete the plan, and publish a fixed commit.

## Findings and decisions

- 2026-07-24 — The V2 foundation will use `autoquant-workspace.json` and
  `autoquant.json`, mirroring the successful sister-project convention while
  keeping AutoQuant terminology explicit.
- 2026-07-24 — Workspace state owns only `name`, `projects_directory`, and
  `default_project`. Project content is never inherited from a mutable
  Workspace catalog.
- 2026-07-24 — The first Project schema declares its owned directory surfaces
  but does not invent Study or Run schemas before their evaluation and
  immutability contracts are planned.
- 2026-07-24 — JSON CLI envelopes follow INM's mature contract shape. Human
  text remains concise, while Agents can discover exact arguments and effects.
- 2026-07-24 — The existing V0.5 flat Harness remains a compatibility surface
  during this plan; migrating it is a separate bounded outcome.
- 2026-07-24 — Making `aq` a real installed entry point required converting the
  uv project from virtual to editable packaging and explicitly binding Hatch's
  wheel target to `autoquant/`; both wheel and sdist now build.
- 2026-07-24 — Confinement rejects symlinks in every component of an owned
  nested path, not only the final leaf.

## Verification

- `uv run python scripts/check_doc_links.py`: 54 repository double-links
  resolve.
- `uv run python -m unittest discover -s tests -v`: 22 bounded tests pass,
  including two-Project resolution, independent files, strict schemas,
  traversal and symlink rejection, complete starter creation, capability
  discovery, JSON envelopes, structured validation errors, and a subprocess
  CLI flow.
- `uv build`: produced `auto_quant-0.1.0.tar.gz` and
  `auto_quant-0.1.0-py3-none-any.whl`.
- `uv run python -m compileall -q autoquant tests`: all source and tests
  compile.
- Human CLI flow: initialized one temporary Workspace, created `alpha-lab` and
  `model-lab`, listed both, changed the default, validated that default, and
  inspected the explicit non-default Project.
- JSON CLI flow: initialized a separate temporary Workspace, created
  `factor-lab` and `ml-lab`, listed contexts/artifacts/next actions, changed the
  default, validated it, and inspected the explicit other Project.
- `uv run aq capabilities --json`: all eight public command descriptors emit
  under CLI schema V1.
- `uv run prepare.py --list-profiles` and `uv run run.py --list-profiles`:
  legacy crypto and US-equity profile discovery remains intact.
- `git diff --check`: no whitespace errors.

## Progress log

- 2026-07-24 — Plan created and indexed after auditing current AutoQuant,
  INM Workspace/Project boundaries, Mujica resolution rules, and INM's CLI
  envelope/capability system.
- 2026-07-24 — Implemented strict Core manifests, atomic Project starter
  creation, one-Project resolution, packaged `aq`, schemas, human/JSON
  projections, artifacts, next actions, and structured failures.
- 2026-07-24 — Added canonical format/CLI references, boundary design
  documents, 10 new focused tests, package-build verification, and real human
  and JSON two-Project acceptance flows.
- 2026-07-24 — Completed acceptance and moved the plan to completed.

## Completion

Shipped the first executable AutoQuant V2 boundary: one installed `aq` CLI can
create a long-lived Workspace, construct multiple isolated Project roots,
select exactly one default or explicit Project, validate strict path and
identity invariants, and expose the same operations to Agents through a
versioned capability and envelope contract.

The repository-root V0.5 Freqtrade arena remains functional and explicitly
separate. Study/Run evidence, the governed code-optimization loop, and Studio
remain future bounded outcomes rather than hidden partial contracts in this
foundation.
