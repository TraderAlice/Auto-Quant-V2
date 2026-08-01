# Atomic Study-owned dataset intake

- Status: `active`
- Updated: `2026-08-01`
- Target release: `0.9.19`
- Related design: [[docs/design/research-intake-and-dataset-snapshots]],
  [[docs/design/study-run-evidence]], [[docs/design/agent-native-market-data-acquisition]],
  and [[docs/design/agent-native-quant-workbench]].

## Outcome

Let a fresh quantitative coworker add one scientifically distinct fixed Study
to an existing Project directly from one external Research Request and one
complete task-local OHLCV package. One public command must validate, normalize,
bind, and create the Study without making the coworker impersonate an unrelated
Project template, inspect installed implementation modules, or leave partial
source/data state after an ordinary failure.

The exact released `0.9.18` wheel is the untouched baseline. `0.9.19` admits
only the smallest reusable repair reproduced by that field evidence. It does
not introduce shared data inventory, automatic reuse, a universal Study DSL,
or a second execution engine.

## Baseline evidence

The final `0.9.18` continuation worker correctly completed one recovery Study,
Run, and Report, but public surfaces did not expose generic same-Project data
intake. To finish, the worker had to:

- read installed `autoquant.intake`, `autoquant.runs`, `autoquant.studies`, and
  `autoquant.cli` implementation modules;
- try unrelated `ohlcv-book-risk-lab`, `blank`, and
  `ohlcv-book-path-stress-lab` profiles to discover which policy checks would
  admit the request;
- write `workspace/staging/materialize_recovery_dataset.py` and call private
  composition of `prepare_project_intake` plus `materialize_intake_dataset`;
- materialize request and data before `aq study create`, so a later Study
  validation failure was not one atomic user action.

The worker ultimately produced the requested shape at
`/Users/ame/autoquant-v0918-recovery-final-candidate`, but success depended on
private source knowledge. That is useful baseline evidence, not acceptable
Agent ergonomics.

## Public contract

Extend `aq study create` with an external-package form:

```bash
aq study create <path> <study-id> \
  --request <research-request.json> \
  --dataset <dataset-package.json> \
  <ordinary fixed Study contract>
```

This form must:

- strictly validate the external request and package before Project mutation;
- use a generic `study-owned-ohlcv` admission profile whose job is structural
  data authority, not the scientific policy semantics owned by the custom
  Judge;
- materialize the canonical request at
  `strategies/<study-id>/request.json` and normalized data beneath
  `data/studies/<study-id>/ohlcv/`;
- generate and bind a matching position snapshot when the request contains a
  reported `positionSnapshot`;
- infer dataset id, version, class, universe, time range, and content closure;
- merge generated exact request dependencies with any additional caller-fixed
  dependencies and preserve optional upstream immutable Run evidence;
- reject occupied owned paths before mutation and remove newly created
  source/data/Study paths after any ordinary command failure.

The existing manual form remains available for custom or already materialized
data. External `--request`/`--dataset` and manual dataset identity options are
two explicit, mutually exclusive forms. The external form initially accepts
aligned V1-V3 packages; V4 ragged daily and V5 observed intraday remain tied to
their proven Factor semantics instead of being silently generalized.

“Atomic” means the CLI leaves no partial owned paths after validation or Study
creation errors. It does not promise a crash-consistent filesystem transaction
across arbitrary power loss.

## Scope

### In scope

- Generic V1-V3 request/package preparation for a custom fixed Study.
- One integrated CLI/Core path for Study-owned request, optional reported-book
  snapshot, normalized data, exact dependencies, and Study creation.
- Strict no-overwrite and ordinary-failure rollback behavior.
- Capability, help, Skill, CLI, Project-format, design, and Agent guidance.
- Focused deterministic tests, installed-wheel smoke, and one fresh Grok replay.

### Out of scope

- Automatic data reuse or a Workspace-wide dataset inventory.
- Inferring the Judge, objective, scientific method, or executable strategy
  from the Research Request.
- Generalizing V4/V5 policy, changing specialized Book Risk `study intake`, or
  deleting manual Study construction.
- Orders, TPSL, execution authority, account access, or OpenAlice pin changes.
- A universal transaction log or Workspace migration framework.

## Acceptance

- [ ] `aq study create --request FILE --dataset PACKAGE` creates one valid
      Study-owned request/data closure and infers the exact dataset contract.
- [ ] A request containing `positionSnapshot` creates and explicitly binds the
      matching normalized position snapshot without a manual hash pairing.
- [ ] Additional fixed dependencies and one prior Run artifact binding compose
      with the generated request/data closure.
- [ ] The resulting Study executes through its public Judge, freezes exact
      request/data/upstream identity in one immutable Run, and projects through
      inspect, Orientation, Report, and Studio surfaces.
- [ ] External and manual construction forms cannot be mixed, and request plus
      package are required together.
- [ ] Existing source, data, or Study ownership paths are never overwritten.
- [ ] An induced post-materialization Study failure removes every newly owned
      source/data/Study path while preserving all pre-existing Project bytes.
- [ ] V4/V5 packages fail with an explicit honest boundary; V1-V3 retain their
      strict clock, alignment, provenance, request matching, and horizon checks.
- [ ] Capability discovery, `--help`, installed Skills, and public docs expose
      the external form without requiring implementation-source inspection.
- [ ] A fresh installed-candidate Grok completes an unchanged same-Project
      follow-up with exactly one new fixed Study, one Run, one Report, no
      Session, and no ad hoc materialization script.
- [ ] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and clean-clone smokes pass before publication.

## Work

- [x] Audit the final `0.9.18` worker and retain its workaround as baseline
      product evidence.
- [ ] Implement generic Study-owned V1-V3 preparation and atomic creation.
- [ ] Update machine discovery, Agent Skills, public docs, and deterministic
      tests.
- [ ] Build an isolated candidate wheel and replay a distinct continuation task
      with a fresh Grok worker forbidden from inspecting installed source.
- [ ] Admit only newly reproduced defects, complete the release audit, and
      publish `v0.9.19` if acceptance is satisfied.

## Findings and decisions

- 2026-08-01 — Data duplication remains intentional. Each Study may own the
  complete package selected by its question; ambient Project data is visible
  context, not automatic quantitative authority.
- 2026-08-01 — Project template selection and Study dataset admission are
  different decisions. A custom Judge should not claim to be Book Risk or Path
  Stress merely to obtain strict OHLCV normalization.
- 2026-08-01 — The new route belongs on `study create`, because request/data
  materialization and Study validation form one user intention. A separate
  `study dataset materialize` command would preserve the exact two-phase
  failure exposed by the baseline.

## Verification

Record focused tests, candidate wheel identity, fresh-worker transcript and
artifact identities, full release gates, final commit, and final tag here as
they become authoritative.
