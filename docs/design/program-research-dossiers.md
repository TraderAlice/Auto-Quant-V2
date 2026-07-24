# Program research dossiers

Status: implemented.

Related: [[docs/design/quant-research-lifecycle]],
[[docs/design/research-program-orchestration]],
[[docs/design/request-bound-portfolio-mandates]],
[[docs/design/research-selection-integrity]],
[[docs/design/studio-observation-surface]], [[docs/PROJECT_FORMAT]], and
[[docs/CLI]].

## Scope

This document owns the immutable Project-level answer produced by a canonical
multi-Study Research Program. A Research Dossier synthesizes lane Reports for
one content-locked Research Request and dataset.

It does not own lane evaluation, candidate selection, Agent research,
OpenAlice Inbox publication, authenticated origin, account state, orders, or
trading authority.

## Composition boundary

The evidence hierarchy is:

```text
Run / Experiment / Campaign
→ delegated Session Report
→ Project Research Dossier
→ OpenAlice Inbox publication
```

A lane Report already freezes and verifies the request, Brief, Session leader,
Study/Harness/dataset locks, Run metrics and artifacts, Experiment/Campaign
prefix, selection integrity, findings, and limitations. The Dossier cites
these Reports and their finding ids. It never re-evaluates raw Runs or invents
a cross-lane score.

Factor and Portfolio are required lanes. Governed RL is optional because the
research question may not justify adaptive complexity. When RL lacks a current
Report, the Dossier freezes it under `omittedOptionalLanes` with a reason. An
optional lane with current evidence is included and must be covered by the
cross-lane analysis.

## Readiness

`aq dossier status` is the Agent discovery surface. Readiness requires:

1. verified request-driven Project intake;
2. the canonical Factor → Portfolio → RL Research Program;
3. no Program identity or shared-source violation;
4. a delegated Session for every required lane;
5. a verified Report whose frozen leader equals that Session's current leader;
6. a leader Run whose Study input, dataset, source, and fixed dependency
   identities equal the current lane Study;
7. the same content-locked Project request in every included Report.
8. Portfolio and included governed-RL leader Runs use the same fixed Portfolio
   Mandate; RL factor-dependency comparison uses only the `factors/**` subset
   of its multi-input dependency closure.

Readiness is a publication-time condition. A published Dossier is a valid
point-in-time snapshot when later research adds evidence or changes the current
leader, just as an older lane Report remains valid.

The status object exposes every lane, blockers, omission reasons, the current
Report/finding catalog, latest Dossier, and exact next headless action. It is
read-only and does not author analysis.

## Analysis contract

The Agent supplies `autoquant-research-dossier-analysis`:

- title and executive summary;
- findings with confidence and non-empty Dossier evidence references;
- conditional recommendations;
- limitations and unresolved questions.

Each evidence reference contains:

- canonical `laneId`;
- exact `reportId`;
- optional `findingId`.

The Report id must be the included current Report for that lane. A non-null
finding id must exist in its verified analysis. At least one finding reference
must cover every included lane. Recommendations cannot introduce evidence that
is not part of the frozen lane catalog.

## Immutable artifact

Publication creates:

```text
dossiers/
└── dossier-<timestamp>-<hash>/
    ├── analysis.json
    ├── dossier.json
    ├── dossier.md
    └── manifest.json
```

The Project manifest remains V1-compatible; `dossiers/` is a reserved,
optional, confined Project root created on first publication. Symlinks and
non-file entries are rejected.

`dossier.json` freezes:

- Project identity and publication time;
- authority `quantitative-decision-support` and `tradingAuthority: none`;
- exact request plus request hash;
- dataset snapshot plus manifest/content hashes;
- canonical Research Program manifest plus hash;
- every included lane's Study identity;
- Report id/hash, analysis/evidence hashes, Session id, title, summary,
  findings, selection integrity, and Harness;
- leader Run id/hash, subject/source/dependency identity, objective, metrics,
  artifacts, and dataset;
- request-derived Portfolio Mandate identity and complete frozen metrics for
  every applicable lane;
- omitted optional lanes;
- normalized cross-lane analysis and its hash;
- OpenAlice handoff boundary.

The manifest is written last after hashing the other three files. Loading
verifies file hashes, canonical Markdown, normalized analysis, derived id,
intake/program identity, every referenced immutable Report and leader Run,
and exact frozen projections.

## Markdown and OpenAlice

`dossier.md` is the human handoff document. It includes:

- caller question, decision context, assets, direction, and horizon;
- authorized positions, context-only research assets, construction family,
  cash/cap, and benchmark from the frozen Portfolio Mandate;
- executive synthesis;
- a lane evidence table;
- lane Report summaries and selection-integrity warnings;
- cross-lane findings and conditional recommendations;
- limitations, unresolved questions, and omitted optional lanes;
- reproducibility hashes and publication instructions.

AutoQuant preserves caller-supplied OpenAlice Workspace/Session/document
context but cannot authenticate it. The Dossier states that OpenAlice must
publish the exact Markdown through Inbox and stamp its own authoritative
Workspace, Session, and document revision.

## CLI and Studio

The headless lifecycle is:

```bash
aq dossier status <project> --json
aq schema dossier-analysis --json
aq dossier publish <project> --analysis dossier-analysis.json --json
aq dossier list <project> --json
aq dossier show <project> --dossier ID --json
```

Studio observes the same Core status. It may display blockers, included and
omitted lanes, latest Dossier summary, and copy exact commands. It cannot
author analysis, publish, select evidence, or send an Inbox document.

## Invariants

1. A Dossier cites verified lane Reports, not ungoverned raw claims.
2. Required-lane coverage is complete; optional-lane omission is explicit.
3. Publication uses current evidence; later research does not invalidate the
   immutable point-in-time artifact.
4. Every cross-lane reference resolves to one frozen Report or finding.
5. Browser and CLI consume the same Core readiness/list/load functions.
6. Dossier authority is decision support only; trading authority is always
   none.
7. OpenAlice provenance becomes authoritative only when OpenAlice publishes
   the exact handoff artifact.

## Known gaps

- Dossiers are Project-local; cross-Project aggregation is not implemented.
- Core does not generate qualitative synthesis.
- OpenAlice Inbox publication remains outside AutoQuant.
