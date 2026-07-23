# Governed Research Sessions and Experiments

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]], [[docs/CLI]],
[[docs/design/study-run-evidence]], and
[[docs/design/agent-cli-contract]].

## Scope

This document owns the resumable Agent edit/evaluate loop above a fixed Study:
Session identity, disposable working construction, Experiment evidence,
KEEP/REVERT/CRASH comparison, leader restoration, and guarded promotion.

It does not own the Researcher's model/provider, proposal quality, parallel
search, portfolio guardrails, or Studio presentation.

## Authority model

The human-owned Study remains the authority. A Researcher receives:

- the Study program and objective;
- the exact editable strategy/factor/model closure;
- a disposable Session worktree path;
- the current leader Run, metric, source hash, and prior Experiment history;
- one bounded evaluate command.

The Researcher may edit candidate source in the worktree and describe one
hypothesis. It cannot decide the verdict, rewrite history, change fixed inputs,
or publish source to the owning Project. The fixed Judge and Core comparison
decide KEEP, REVERT, or CRASH. Promotion is a separate explicit operation.

This separates the replaceable intelligence that proposes code from the stable
Harness that controls authority and evidence.

## Project layout

The Project gains one durable `sessions/` ownership slot:

```text
sessions/
└── session-<UTC timestamp>-<identity>/
    ├── session.json
    ├── worktree/
    │   └── <project-id>/
    │       ├── autoquant.json
    │       ├── research.md
    │       ├── <fixed selected Study and Judge files>
    │       ├── <editable candidate files>
    │       └── <empty required Project directories>
    ├── experiments/
    │   └── exp-0001-<candidate identity>/
    │       ├── result.json
    │       ├── changes.json
    │       ├── diff.patch
    │       └── manifest.json
    ├── campaigns/
    │   └── campaign-<UTC timestamp>-<identity>/
    │       ├── turns/
    │       ├── result.json
    │       └── manifest.json
    └── promotion.json
```

`session.json` is a mutable, strict coordination pointer. Immutable Runs and
Experiment directories are the evidence. `promotion.json` is written once when
the accepted leader is copied back to the Project.

## Session identity and locks

A Session pins:

- owning Project and selected Study;
- Study, program, Judge, dataset, and Harness identities;
- successful baseline Run id, metric, and source hash;
- current leader Run id, metric, and source hash;
- Project source hash at Session start;
- worktree path, status, timestamps, and next Experiment sequence.

Session start executes a fresh successful baseline through the ordinary
Study/Run contract. It then constructs the worktree from exact fixed and
editable bytes. Canonical Project candidate source is not changed.

Evaluation rejects stale or modified authority before running:

1. the owning Project and worktree Project manifests still agree;
2. canonical and worktree Study/program/Judge/dataset hashes equal Session
   locks;
3. the installed Harness identity equals the baseline lock;
4. every worktree file outside the editable closure equals the fixed inventory;
5. the mutable leader and sequence reconstruct exactly from immutable
   Experiment history;
6. the candidate source differs from the current leader.

For a content-locked Study, canonical and worktree identity checks hash the
same owning Project data root. Dataset bytes are not copied into the worktree;
changing them stales the Session before another candidate can run.

## Experiment execution

```text
Agent edits Session worktree
→ validate fixed inventory and candidate closure
→ publish candidate Run in owning Project
→ compare primary metric with current leader
→ publish immutable Experiment evidence
→ KEEP: retain candidate worktree and advance leader
→ REVERT/CRASH: restore exact leader source bytes
→ atomically update mutable Session pointer
```

The candidate Judge executes from the Session worktree but reads the owning
Project's declared data directory. Its Run is published in the owning
Project's canonical `runs/`, so Studio and CLI need no second Run catalog.

The V1 verdict rule is deliberately small:

- `CRASH`: candidate Run status is failed;
- `KEEP`: candidate Run succeeded and its direction-normalized improvement is
  strictly positive and at least `minimum_improvement`;
- `REVERT`: candidate Run succeeded but did not clear that threshold.

An Experiment records the hypothesis, before/candidate source hashes, leader
and candidate Runs, primary values, signed direction-normalized improvement,
threshold, verdict, structured source changes, unified text diff, errors, and
timestamps. Its terminal manifest pins every other Experiment file.

## Restoration and promotion

REVERT and CRASH never copy candidate bytes into the owning Project. After
their evidence is published, the worktree editable closure is restored from
the verified immutable leader Run.

Promotion is allowed only when:

- the Session is active and has at least one KEEP beyond baseline;
- the current leader Run is successful and matches the Session leader hashes;
- fixed Study/Judge/Harness locks remain current;
- the owning Project editable source still equals its Session-start hash;
- no promotion receipt already exists.

Promotion backs up the confined Project editable closure, applies exact leader
files including deletions, reloads the Study to verify the accepted source
hash, and restores the backup on any failure. Only then does it write the
promotion receipt and mark the Session promoted. A stale promotion changes
nothing.

V1 promotion is process-atomic with verified rollback, not a cross-filesystem
transaction. Concurrent writers outside AutoQuant remain prohibited during
the short promotion critical section.

## Agent loop

The CLI is the shared protocol:

```text
aq session start <path> --study <id> --json
→ edit data.worktree under data.editablePaths
→ aq experiment evaluate <path> --session <id> --hypothesis "..." --json
→ inspect verdict/history/nextActions
→ repeat or aq session promote <path> --session <id> --json
```

An external Codex, another coding Agent, or a human can drive these same
operations. The implemented provider-neutral bounded layer is
[[docs/design/external-researcher-driver]]; it composes this contract rather
than entering the Judge or promotion authority.

## Invariants

1. Sessions and Experiments are Project-local and path-confined.
2. Candidate execution never imports undeclared Project source.
3. Fixed authority is checked before every Experiment and promotion.
4. Candidate Runs use the canonical Run evidence protocol.
5. Experiment manifests are written last and verified on load.
6. Every Experiment verdict is recomputed from its immutable candidate Run when
   Session history is validated.
7. KEEP alone advances the Session leader.
8. REVERT and CRASH restore the exact prior leader.
9. Promotion is explicit, stale-base guarded, hash-verified, and rollback-safe.
10. Session pointers may be rebuilt from immutable Runs and Experiments; they
   are not research evidence by themselves.

## Known gaps

- One Session has one linear leader; there are no branches or Pareto fronts.
- Comparison uses one primary metric without per-asset guardrails.
- Session recovery after process termination between Experiment publication
  and pointer update is not yet automated.
- Studio observation is read-only; Session operations remain CLI/Core-owned.
