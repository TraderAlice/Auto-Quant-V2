# Run-bound Research Reports

Status: implemented in `0.9.5`; Study-owned follow-up request binding added in
`0.9.8`.

Related: [[docs/design/quant-research-lifecycle]],
[[docs/design/research-session-loop]],
[[docs/design/research-program-orchestration]],
[[docs/design/study-run-evidence]], [[docs/design/independent-research-reviews]],
and [[docs/design/agent-operator-experience]].

## Purpose

A Research Report is immutable Agent-authored interpretation over verified
AutoQuant evidence. Its evidence anchor must reflect how that evidence was
produced:

- a **Run anchor** reports one already immutable current Study execution;
- a **Session anchor** reports a bounded editable investigation and its exact
  Experiment/Campaign prefix.

Creating a Session merely to obtain a report directory is invalid modeling.
A Session grants candidate edit/evaluate authority and records search history;
a frozen baseline reproduction needs neither.

## Ownership and layout

Run-bound Reports are Project-owned:

```text
reports/
└── report-<UTC timestamp>-<identity>/
    ├── analysis.json
    ├── report.json
    ├── report.md
    └── manifest.json
```

Session-bound Reports remain beneath the Session because their evidence prefix
belongs to that investigation. Discovery is explicit across both locations;
identifiers remain globally unique within a Project.

## Run anchor authority

`aq report publish <path> --study ID --run ID --analysis FILE` requires:

1. verified request-driven Project intake;
2. one successful immutable Run owned by the selected Study;
3. the Run is current for the Study's fixed and editable content identity;
4. the Run request, dataset, source/dependency, Harness, and Study identities
   remain exactly verifiable;
5. every analysis evidence reference resolves within the one frozen Run;
6. no active or historical Session exists for the Study, because omitting a
   real candidate-search prefix would understate selection history.

The frozen evidence contains the exact Run projection, selection-integrity
snapshot at publication time, and derived leader decision support. It contains
no Experiment or Campaign catalog and cannot cite those evidence kinds.

The Report request follows immutable Run authority, not merely Project-root
intake. A primary Study freezes the Project request. A same-Project fixed
follow-up may instead freeze a Study-owned request and its corresponding
position snapshot beneath the Run dependency sources. Publication and loading
verify that the snapshot request hash matches that frozen request, then use it
in both `report.json` and Report identity. Older and newer Studies can therefore
answer different questions over one retained dataset without relabeling either
Report.

## Shared Report anchor

Every current Report exposes one strict anchor:

```json
{
  "kind": "run | session",
  "studyId": "ohlcv-factor-quality",
  "runId": "run-...",
  "sessionId": null
}
```

For a Session Report, `runId` is the frozen leader and `sessionId` is the
owning Session. For a Run Report, `sessionId` is null. CLI, Studio, Dossier, and
Markdown use this anchor instead of guessing semantics from a path or treating
all Reports as evidence of candidate search.

## Coordinated program semantics

A required Research Desk lane is report-ready when its current successful Run
has either:

- a Run-bound Report for the exact Project request and current Run; or
- a Session-bound Report for the exact Project request and current Session
  leader.

The first route is preferred when the caller supplied or accepted a frozen
baseline and no candidate iteration occurred. The second is required when the
claim depends on a governed Experiment history. Both routes preserve the same
Factor-to-Portfolio and Portfolio-to-RL content checks.

When the verified evidence-driven agenda says
`no-further-in-sample-tuning` and every proposed move has an empty editable
target, Agent Orientation promotes the current Run-bound `report.publish`
command over `session.start`. A weak or unresolved baseline with a real
candidate-edit target retains the governed Session route; Run Reports are not
a shortcut around needed investigation.

## Non-goals

- Reports do not turn Runs into selection or trading authority.
- A later Independent Review classifies a Report; it does not rewrite or
  replace the primary researcher's Report.
- A Report does not make a scientifically blocked lane admissible.
- Fixed single-lane Studies remain free to return Run/Explorer evidence without
  manufacturing a Report.
- This contract does not infer research intent, choose a template from prose,
  or publish into OpenAlice.
