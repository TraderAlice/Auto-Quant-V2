# Atomic Study-owned dataset intake

- Status: `completed`
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

- [x] `aq study create --request FILE --dataset PACKAGE` creates one valid
      Study-owned request/data closure and infers the exact dataset contract.
- [x] A request containing `positionSnapshot` creates and explicitly binds the
      matching normalized position snapshot without a manual hash pairing.
- [x] Additional fixed dependencies and one prior Run artifact binding compose
      with the generated request/data closure.
- [x] The resulting Study executes through its public Judge, freezes exact
      request/data/upstream identity in one immutable Run, and projects through
      inspect, Orientation, Report, and Studio surfaces.
- [x] External and manual construction forms cannot be mixed, and request plus
      package are required together.
- [x] Existing source, data, or Study ownership paths are never overwritten.
- [x] An induced post-materialization Study failure removes every newly owned
      source/data/Study path while preserving all pre-existing Project bytes.
- [x] V4/V5 packages fail with an explicit honest boundary; V1-V3 retain their
      strict clock, alignment, provenance, request matching, and horizon checks.
- [x] Capability discovery, `--help`, installed Skills, and public docs expose
      the external form without requiring implementation-source inspection.
- [x] A fresh installed-candidate Grok completes an unchanged same-Project
      follow-up with exactly one new fixed Study, one Run, one Report, no
      Session, and no ad hoc materialization script.
- [x] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and clean-clone smokes pass before publication.

## Work

- [x] Audit the final `0.9.18` worker and retain its workaround as baseline
      product evidence.
- [x] Implement generic Study-owned V1-V3 preparation and atomic creation.
- [x] Update machine discovery, Agent Skills, public docs, and deterministic
      tests.
- [x] Build an isolated candidate wheel and replay a distinct continuation task
      with a fresh Grok worker forbidden from inspecting installed source.
- [x] Admit only newly reproduced defects, complete the release audit, and
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
- 2026-08-01 — The final candidate worker discovered the integrated route from
  public capability, help, schema, and installed Skill surfaces. It did not
  read installed implementation modules, prior transcripts, or write an ad hoc
  materializer. The generic custom-Judge surface was sufficient; a dedicated
  recovery-durability Lab or Explorer is not justified by one descriptive
  follow-up.
- 2026-08-01 — Worker-reported friction around an absent coordinated
  `research-program.json`, unsupported evidence-driven agenda for a custom
  metric, terminal Orientation, and a truncated Nasdaq history is honest task
  or provider scope, not a defect in atomic intake. Re-acquiring a complete
  task-local package also preserves the existing demand-led data invariant.
- 2026-08-01 — The release gate caught stale checked-in Workspace Skill copies
  after the canonical packaging Skill changed. Re-materializing both discovery
  roots and keeping the repository bundle verification versioned closes that
  packaging defect without changing the public intake contract.

## Verification

Two discarded launches are not counted as product evidence. The Codex-app
Grok thread failed with a scheduler `systemError` before taking any action. A
first CLI launch then omitted the candidate virtual environment from `PATH`;
that worker inspected ambient source and a prior transcript before it reached
Study construction, so it was stopped and its Workspace was rejected. The
authoritative replay began again in a fresh directory with the installed
candidate CLI explicitly first on `PATH`.

The isolated installed-wheel replay used Grok session
`019fbd45-86de-7010-8302-b5d6a0cc8670` at
`/Users/ame/autoquant-v0919-durability-final-candidate`. It added exactly Study
`ohlcv-book-path-recovery-durability`, succeeded Run
`run-20260801T122535519420Z-84653e611761`, and published Report
`report-20260801T122614364560Z-0f9aa1ab8b38`, with zero Sessions. The Study
bound recovery Run `run-20260801T113412099979Z-5b156acfd245`, its exact episode
and contribution artifacts, the generated request and position snapshot, one
additional fixed Project snapshot, and the complete Study-owned Yahoo package.
The immutable result identifies Harness `0.9.19`, result hash
`980974a6c714ce4287f44e1f793f4c7922b97d2b84949aeb53581cceac2da57b`,
and Study input hash
`a1fbe1b6d8e545b17b9510cebde2d422896dabe764695ce718de1d367893b2f7`.

Public validation, inspect, Orientation, Report, and Studio surfaces all
accepted the terminal evidence. All 77 inherited Project files outside the
authorized `research.md` update remained byte-identical. An independent
stdlib replay reconstructed all 260 reported book-path points directly from
the frozen opening units and Study-owned closes with zero absolute residual.
Transcript audit found no private implementation read or ad hoc materializer.

Focused intake and CLI regressions plus repository Skill-bundle verification
passed. The first complete suite was deliberately invalidated: the checked-in
Skill copies were stale, and updating them while that suite was still running
changed Harness source identity between two RL reproducibility executions.
After the canonical bundle was re-materialized and the repository was held
still, the clean rerun passed all 415 tests in 1,259.120 seconds, including the
same RL reproducibility case.

Lock validation, Python and Studio JavaScript syntax, diff checks, and all
1,387 documentation links passed. Source and wheel builds succeeded. A fresh
Python 3.11.14 environment outside the source checkout installed the exact
wheel, reported `aq 0.9.19`, loaded AutoQuant from `site-packages`, disclosed
all 57 public commands and all four external/upstream `study.create`
arguments, and loaded the changed Study and RunResult schemas. Final wheel
SHA-256 is
`6a083f6600750b6c4fdd0b7eccd2f6634606d81901418db6176c92317d3f7876`;
source-distribution SHA-256 is
`d72903c55c4bdcf02bd47fb895780efd6045195f1e0937f09f819afff8a51de0`.

## Completion

Completed on 2026-08-01 as `v0.9.19`. A fresh installed-wheel coworker used
the public atomic Study-owned intake rather than private implementation
knowledge, preserved the long-lived Project, and returned one exact
evidence-bound descriptive continuation. OpenAlice remains independently
pinned to `v0.8.31`.
