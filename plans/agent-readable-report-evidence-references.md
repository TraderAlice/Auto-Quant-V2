# Make Research Report evidence references self-describing

- Status: `completed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0819-multistage-factor-portfolio/desk/workspace/projects/grok-build-multistage-gate-v0819`
- Related design: [[docs/design/quant-research-lifecycle]],
  [[docs/CLI]], and [[docs/PROJECT_FORMAT]].

## Outcome

A Coding Agent can author valid Research Report `evidenceRefs` from public CLI
discovery alone, without trial-and-error guesses about Run-root paths or
artifact eligibility.

## Context

A fresh installed `aq 0.8.19` Grok worker correctly completed one gated
multi-Study investigation: Factor baseline, one checked Experiment, KEEP,
Report-bound promotion, scientific Portfolio early-stop, and Factor-only
Dossier. It did not run Portfolio or RL after the qualification gate blocked
them.

During Report publication, the worker first supplied a Run-root path and then
an artifact on an Experiment reference. Core correctly rejected both, but the
public `report-analysis` JSON Schema described `artifactPath` only as a
free string or null. The worker had to infer the actual contract from error
messages and inspect Run result JSON.

## Scope

- Encode in the public JSON Schema that Experiment and Campaign references
  require `artifactPath: null`.
- Describe Run `artifactPath` as either null or an exact declared
  `result.artifacts[].path`, such as `artifacts/factor-report.json`; explicitly
  reject Project paths, Run-root prefixes, and filesystem paths in guidance.
- Add complete Run and Experiment examples to Schema discovery.
- Put the same concise contract in `aq report publish --help`, capabilities,
  CLI docs, and Project format docs.
- Preserve the strict existing Report validation and immutable evidence model;
  this is an Agent discoverability improvement, not a relaxation.
- Re-run a fresh isolated worker against installed release-candidate CLI and
  require a first-attempt valid Report reference.

## Acceptance

- [x] JSON Schema validation rejects non-null Experiment/Campaign artifact
      paths before Report publication.
- [x] Schema and help expose one exact valid Run and Experiment reference.
- [x] Existing valid Reports and strict semantic validation remain unchanged.
- [x] A fresh worker publishes without `report.artifact-kind` or
      `report.unknown-artifact` recovery.
- [x] Full regression, wheel install, and clean-clone smoke pass.

## Field verification

A second isolated Grok Build worker used only an installed `aq 0.8.20`
release-candidate wheel, the unchanged assignment, and a fresh Project. It
inspected `aq schema report-analysis --json` and
`aq report publish --help` before authoring evidence. The assignment allowed
exactly one Report publication invocation.

The worker used `artifacts/factor-report.json` for Run evidence and JSON null
for Experiment evidence. Its first and only invocation succeeded as Report
`report-20260729T190753748783Z-a915f8c8ce36`. Independent validation and
Studio projection emitted no diagnostics. The worker also correctly treated a
Session-objective KEEP as scientifically blocked, created no Portfolio or RL
Run, and left a Factor-only Dossier.

Repository verification completed with 311/311 tests in 796.165 seconds,
1,089/1,089 documentation links, a fresh Python 3.11 wheel installation, and
an unoverridden candidate-tree Workspace smoke.

## Observed but not adopted

The retry suggested returning allowed evidence triples only after invalid
Report publication. Because public discovery supported a first-attempt
success, this is not a current blocker and would optimize error recovery
rather than the intended pre-action contract.

It also suggested a top-level `portfolioAdmitted` alongside Experiment KEEP.
The existing authority object already states
`scientificQualification: false`, `downstreamAdmission: false`, and
`tradingAuthority: none`; human output repeats that the verdict is
Session-objective-only, and orientation owns the downstream gate. A second
Portfolio-specific boolean would duplicate authority and couple generic
Sessions to one downstream lane, so it was intentionally not added.
