# Repository-root AutoQuant Workspace

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/workspace-project-boundaries]],
  [[docs/design/agent-native-quant-workbench]], and
  [[docs/design/agent-operator-experience]].

## Outcome

A clean AutoQuant repository clone is itself an immediately operable,
Git-backed Workspace with one complete multi-Study sample Project, while a
Workbench developer can explicitly redirect effective Project discovery to an
ignored external local configuration without changing the checked-in default.

## Context

The implemented Workspace/Project model is correct, but the repository still
requires operators to initialize a second `quant-workspace` directory. That
distribution shape makes a new coding Agent jump between Harness source and a
separate desk, weakens ordinary filesystem discovery, and contradicts the
product model that a cloned AutoQuant desk should already be ready for work.

Real Workbench development also owns many large research cases that should not
be shipped to every user. The checked-in Workspace must therefore keep
internal, Git-managed Projects as its default while supporting one explicit,
ignored local override for the development checkout.

## Scope

### In scope

- Make the repository root a canonical Workspace with one complete
  `sample-research-desk` Project.
- Preserve one immutable Factor baseline produced by the clean `0.8.7`
  Harness and disclose that historical runtime identity.
- Add a strict ignored local Workspace override that may select an external
  Projects directory.
- Project effective configuration through CLI JSON, human output, and Studio.
- Update the product documentation and publish `0.8.8`.

### Out of scope

- Migrating the existing external real research Projects into the repository.
- Changing `aq workspace init` from an empty-Workspace constructor.
- Adding special runtime semantics for the sample Project.
- Changing Study currentness or immutable Run identity rules.

## Acceptance

- [x] A clean clone resolves `sample-research-desk` through `aq orient .`,
  `aq validate .`, Project listing, and Studio snapshot.
- [x] The sample owns Factor, Portfolio, and governed-RL Studies plus one
  verified immutable historical Factor Run and no Session.
- [x] Repository Projects remain ordinary Git-managed research state, with
  only Project-local data/cache policies unchanged.
- [x] A valid ignored local override selects relative or absolute external
  Projects, and every invalid or unsafe override fails explicitly.
- [x] Project creation and default selection write through the active local
  configuration without mutating the checked-in manifest.
- [x] CLI and Studio expose effective Projects path and configuration source.
- [x] Documentation, full tests, source/wheel smoke, clean-clone smoke,
  version `0.8.8`, tag, and canonical push reconcile.

## Work

- [x] Generate and verify the sample and historical `0.8.7` baseline before
  changing Harness source or release metadata.
- [x] Implement strict base/local Workspace configuration resolution and
  active-configuration writes.
- [x] Add focused repository-root, override, CLI, and Studio tests.
- [x] Update README, canonical references, architecture, and status.
- [x] Complete release verification, plan audit, commit, tag, push, and local
  development override setup.

## Findings and decisions

- 2026-07-29 — The sample uses the complete `ohlcv-research-desk` template,
  but seeds only one Factor Run so the first Studio view has real evidence
  without pre-running Portfolio or RL.
- 2026-07-29 — The local override is a complete strict
  `autoquant-workspace.local.json`; its presence is the explicit authority to
  resolve Projects outside the repository. The checked-in manifest remains
  confined.
- 2026-07-29 — `aq workspace init` remains an empty constructor. The sample is
  repository-template state, not mandatory state for every independently
  initialized Workspace.
- 2026-07-29 — The external collection's previous default
  `us-large-cap-cross-section` predates the current canonical research-program
  contract and fails honest orientation. The ignored development override
  therefore selects the verified compatible
  `global-etf-risk-parity-allocation-v087-clean` while preserving all 41
  external Projects.

## Verification

- `uv run python scripts/check_doc_links.py` — 1,029/1,029 links.
- `uv run python -m unittest discover -s tests -v` — 286/286 tests in
  866.145 seconds.
- `uv build` — `0.8.8` source and wheel distributions succeeded; required
  templates and Studio assets were present and repository Projects remained
  outside the wheel.
- Installed-wheel smoke — version/capabilities, empty Workspace init,
  `ohlcv-factor-lab` creation, and validation passed under Python 3.11.
- Clean-clone smoke — internal default discovery, tracked OHLCV fixture,
  Project validation, Agent orientation, Studio snapshot/Factor Explorer, and
  repository sample tests passed without a local override.

## Progress log

- 2026-07-29 — Plan created and indexed.
- 2026-07-29 — Implemented the root Workspace, complete sample, external local
  override, CLI/Studio disclosure, and `0.8.8` documentation.
- 2026-07-29 — Full regression, distributions, installed wheel, and corrected
  clean-clone smoke passed. The first clone replay exposed and fixed the empty
  Session-directory packaging gap.
- 2026-07-29 — Canonical `main` and annotated tag `v0.8.8` were pushed; the
  ignored local configuration discovered 41 external Projects and oriented
  successfully to the compatible 0.8.7 allocation Project.

## Completion

AutoQuant `0.8.8` shipped the repository-root Workspace at release commit
`d2e56f0`. The root default remains the complete internal sample for every
clean clone. The current Workbench checkout separately uses its ignored local
override for the existing external Project collection, leaving Git clean.
