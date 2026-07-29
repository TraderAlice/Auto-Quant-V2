# Repository-root AutoQuant Workspace

- Status: `active`
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

- [ ] A clean clone resolves `sample-research-desk` through `aq orient .`,
  `aq validate .`, Project listing, and Studio snapshot.
- [ ] The sample owns Factor, Portfolio, and governed-RL Studies plus one
  verified immutable historical Factor Run and no Session.
- [ ] Repository Projects remain ordinary Git-managed research state, with
  only Project-local data/cache policies unchanged.
- [ ] A valid ignored local override selects relative or absolute external
  Projects, and every invalid or unsafe override fails explicitly.
- [ ] Project creation and default selection write through the active local
  configuration without mutating the checked-in manifest.
- [ ] CLI and Studio expose effective Projects path and configuration source.
- [ ] Documentation, full tests, source/wheel smoke, clean-clone smoke,
  version `0.8.8`, tag, and canonical push reconcile.

## Work

- [ ] Generate and verify the sample and historical `0.8.7` baseline before
  changing Harness source or release metadata.
- [ ] Implement strict base/local Workspace configuration resolution and
  active-configuration writes.
- [ ] Add focused repository-root, override, CLI, and Studio tests.
- [ ] Update README, canonical references, architecture, and status.
- [ ] Complete release verification, plan audit, commit, tag, push, and local
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

## Verification

Pending.

## Progress log

- 2026-07-29 — Plan created and indexed.

## Completion

Pending.
