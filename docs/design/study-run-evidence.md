# Study contracts and immutable Run evidence

Status: V1 Python Judge lane implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/workspace-project-boundaries]], and
[[docs/design/agent-cli-contract]].

## Scope

This document owns fixed quantitative Study contracts, human research
programs, Judge and editable source closures, dataset and objective identity,
bounded Python Judge execution, structured Judge output, immutable RunResult
publication, and Run verification.

It does not own autonomous Researcher invocation, KEEP/REVERT/CRASH
Experiments, source promotion, Freqtrade adaptation, dataset byte manifests,
or Studio presentation.

## Authority model

V1 establishes three authority surfaces:

1. A human-authored Study and `program.md` define the research question,
   subject, dataset identity, primary metric, improvement direction, and
   operating intent.
2. Candidate work may change only the explicit Project-local editable source
   closure beneath `strategies/`, `factors/`, or `models/`.
3. A fixed Python Judge closure executes from frozen bytes and writes one
   strict result. Its files, Study, program, dataset identity, objective, and
   Harness are outside candidate authority.

`aq run execute` does not yet mutate candidate source. A future Research
Session will stage a disposable Project, invoke an external Researcher, prove
that its diff stays inside the same editable closure, run this Judge, and
promote only a reviewed KEEP.

## Source of truth

- Study schema, loading, closures, and identity: `autoquant/studies.py`
- Judge execution, RunResult publication, and immutable verification:
  `autoquant/runs.py`
- Human/Agent operations: `autoquant/cli.py`
- Machine capability descriptors: `autoquant/capabilities.py`
- Canonical formats: [[docs/PROJECT_FORMAT]]
- Canonical commands and envelopes: [[docs/CLI]]
- Focused evidence tests: `tests/test_studies.py`, `tests/test_runs.py`, and
  `tests/test_cli.py`

## Study identity

A Study contains:

- stable id, name, description, and human program;
- subject kind/name/version;
- exact editable files or trailing-`/**` directory closures;
- one Python Judge entrypoint, its complete fixed source closure, arguments,
  and wall-clock timeout;
- primary metric, maximize/minimize direction, and minimum improvement;
- dataset id/version, asset class, universe, and date range.

The Core derives:

- `studyHash` from the strict Study definition;
- `programHash` from program bytes;
- `judgeHash` from every fixed Judge source path and content hash;
- `sourceHash` from every editable source path and content hash;
- `datasetHash` from the declared dataset identity;
- `studyInputHash` from those five identities.

The complete Run `inputHash` additionally binds the installed AutoQuant
Harness id/version/commit, dirty state, source hash, and Python version.
Identical Study/source/Harness inputs preserve the same `inputHash`; repeated
executions still receive unique immutable Run ids.

## Closure and confinement invariants

1. Study ids match their immediate `studies/<id>/` directory.
2. Study manifest objects and all nested objects are strict.
3. Exact source paths are files. Trailing-`/**` closures are real directories.
4. Source traversal never follows symlinks and ignores generated Python cache
   files.
5. Editable paths stay beneath the Project's declared strategy, factor, or
   model directories; Judge paths stay beneath its declared Judge directory.
6. The Study manifest, program, Judge entrypoint, and every Judge source file
   are outside the editable closure.
7. The Judge entrypoint is included in the declared Judge closure.
8. Program, Judge, editable source, and artifact paths are Project- or
   artifact-root-confined POSIX relative paths.

## Execution model

```text
strict Study load
→ hash Study/program/Judge/editable sources/dataset/Harness
→ freeze Run inputs and editable source bytes
→ materialize isolated source workspace
→ execute fixed Python Judge with a bounded timeout
→ validate one Judge output JSON and exact artifact inventory
→ normalize success or failure RunResult
→ hash every Run file
→ write terminal manifest last
→ atomically rename the complete Run into discovery
```

The isolated execution workspace contains only the Project manifest, Study,
program, fixed Judge sources, and editable sources. It does not inherit
undeclared Project code. Dataset access is explicit through
`AUTOQUANT_DATA_ROOT`; the V1 dataset identity is declarative and does not yet
prove byte content.

Judge environment:

- `AUTOQUANT_PROJECT_ROOT`: isolated source workspace;
- `AUTOQUANT_DATA_ROOT`: original Project-local data directory;
- `AUTOQUANT_STUDY_PATH`: frozen Study manifest;
- `AUTOQUANT_RUN_OUTPUT`: required Judge output JSON path;
- `AUTOQUANT_ARTIFACTS_DIR`: confined artifact output directory;
- `AUTOQUANT_INPUT_HASH`: complete Study plus Harness input identity.

The Judge process is not an OS sandbox. It is ordinary Project-authored Python
with a fixed source and evidence contract. Host-level sandboxing is a separate
deployment concern.

## Failure evidence

Process exit, timeout, missing output, malformed JSON, non-finite metrics,
missing primary metric, invalid artifacts, and inconsistent status/errors all
produce a completed immutable RunResult with `status: failed`. Stdout, stderr,
partial raw Judge output, and any written files remain inspectable.

A CLI operation failure is reserved for conditions where trustworthy evidence
cannot be published, such as invalid Study identity or an immutable Run
collision.

## Immutable Run invariants

1. Each visible Run directory has a terminal `manifest.json` with
   `completed: true`.
2. Hidden staging directories and visible incomplete directories are ignored by
   listing.
3. The terminal manifest maps every other file to its SHA-256 hash and pins the
   normalized `result.json` hash.
4. Loading or listing a completed Run rejects changed, deleted, or added files,
   and validates the strict RunResult contract after verifying its bytes.
5. RunResult records status, metrics, subject/version, asset universe,
   dataset/time range, artifacts, errors, Study/Judge/source identity,
   execution timing, and Harness version/source identity.
6. Completed Run directories are read-only protocol artifacts. New analysis
   produces a derived artifact or new Run rather than changing them.

## Non-goals

- Claiming dataset reproducibility from a name and date range alone.
- Letting the Judge train, repair, or promote a candidate.
- Treating a failed Judge process as absent evidence.
- Selecting different framework libraries per asset class.
- Running a long backtest as part of repository validation.

## Change checklist

- Update Study, Judge output, RunResult schemas, parser behavior, CLI
  capability descriptors, and canonical docs together.
- Keep Judge and editable source closures disjoint.
- Add failure evidence for each new execution failure mode.
- Preserve manifest-last atomic publication and full-file tamper verification.
- Add Studio as a projection of verified RunResult rather than a second
  evaluator.
- When dataset byte identity is added, migrate active Study examples explicitly
  and retain historical Runs under their recorded V1 contract.

## Verification

```bash
uv run aq schema study --json
uv run aq schema judge-output --json
uv run aq schema run-result --json
uv run python -m unittest tests.test_studies tests.test_runs tests.test_cli -v
```

## Known gaps

- Dataset content manifests and corporate-action/session metadata are not
  content-hashed.
- There is no Freqtrade Study adapter.
- There is no baseline/candidate comparison or Experiment verdict.
- There is no source promotion transaction.
- There are no streamed progress events.
- Studio does not yet list Studies or Runs.
