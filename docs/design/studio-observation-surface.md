# Studio observation surface

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/CLI]], [[docs/PROJECT_FORMAT]],
[[docs/design/agent-cli-contract]], [[docs/design/research-session-loop]], and
[[docs/design/external-researcher-driver]],
[[docs/design/research-intake-and-dataset-snapshots]], and
[[docs/design/quant-research-lifecycle]].

## Scope

This document owns the local Studio snapshot, read-only HTTP boundary,
presentation responsibilities, and the distinction between immutable evidence
and mutable execution progress.

It does not own research decisions, evaluation, source mutation, promotion,
remote hosting, authentication, or cloud persistence.

## Ownership

Studio has three layers:

```text
AutoQuant Core loaders
→ versioned Studio snapshot
→ CLI JSON or local read-only HTTP
→ packaged browser presentation
```

Core loaders remain authoritative for Project confinement, Study identity, Run
and Experiment integrity, Session authority, and Campaign hashes. The snapshot
normalizes those verified objects for observation. The HTTP server and browser
must not reimplement validators or inspect arbitrary Project files.

The browser may sort, filter, select, render, and copy an exact Core-generated
CLI command. It cannot create metrics, change verdicts, execute commands,
publish Reports, or write Project state. Clipboard copy grants no new
authority.

## Snapshot contract

One snapshot represents either:

- every immediate Project in a Workspace; or
- one direct Project.

It records its schema version, generation time, source scope, Workspace
identity when present, and ordered Project observations. Each Project contains:

- identity, description, research program, and validation diagnostics;
- verified pre-Session request intake, dataset snapshot, and exact
  Session-start command when present;
- latest verified baseline decision metrics, with selection versus visible
  audit/stress roles preserved rather than collapsed into one score;
- latest verified governed RL baseline, fold/seed, training, action, and
  implementation projection when available;
- verified Study and Run summaries;
- verified Session snapshots and Experiment histories;
- verified delegated requests and derived Research Briefs;
- verified terminal Campaign summaries;
- verified immutable Research Report summaries;
- explicitly mutable active Campaign progress;
- exact CLI commands for copy-only human/Agent handoff;
- counts and a normalized recent-evidence timeline derived from those objects.

Failure to verify one evidence category never turns unverified bytes into
display data. The category returns no claims plus structured diagnostics, while
other independently verified categories remain observable.

## Mutable Researcher progress

Terminal Runs, Experiments, Campaigns, and Research Reports are immutable
evidence. A Report remains valid when its Session later adds evidence because
it freezes a verified chronological prefix. A currently executing external
Researcher needs a different contract.

Before invoking a Researcher turn, Campaign execution writes a strict
`progress.json` inside the hidden Campaign staging directory. It records:

- Campaign and Session identity;
- `running` status and current phase;
- start/update timestamps and current turn;
- declared turn, wall-clock, and per-turn budgets;
- completed Experiment ids and verdict counts;
- only the hash of the external command.

Progress is mutable operational telemetry and is always labelled as such.
Studio reads it through a strict Research module loader. It never uses progress
to infer a verdict or completed Campaign. On terminal publication the final
progress file becomes manifest-pinned Campaign evidence.

A stale hidden staging directory may represent an interrupted process. V1
shows its last update rather than claiming liveness.

## Local HTTP boundary

`aq studio serve` binds to `127.0.0.1` by default. It exposes only:

- the packaged application shell and fixed CSS/JavaScript assets;
- a health response;
- the versioned snapshot response.

There is no arbitrary path, artifact download, mutation, command, or shell
endpoint. Responses set a restrictive Content Security Policy, disable
sniffing and framing, and avoid cross-origin access. Binding to a non-loopback
address is an explicit operator choice and V1 has no authentication.

## Presentation priorities

The first viewport answers:

1. Which research Projects exist?
2. Which Sessions are active, and what is each current leader?
3. Are external Researchers running, stopped, failed, or budget-exhausted?
4. Which hypotheses were kept, reverted, or crashed?
5. What did the caller ask, is its dataset content-locked, and is a verified
   Report ready?
6. What exact headless command advances or inspects the work?
7. What verified evidence changed most recently?

The visual system is a dense research observatory rather than a generic admin
dashboard. It supports keyboard focus, narrow screens, reduced motion, empty
Projects, invalid evidence diagnostics, manual refresh, and bounded automatic
refresh.

Before a delegated Session exists, the first viewport prioritizes mandate,
requested assets versus research universe, dataset authority, immutable
baseline evidence, and the exact next headless action. Generic object counts
must not displace available quantitative evidence. Sign alone is not a
promotion threshold: the browser may mark negative return/risk evidence as
adverse, but it must not colour a positive factor or portfolio value as
successful unless Core exposes an explicit verified pass decision.

## Invariants

1. Studio never bypasses a Core loader for completed evidence.
2. Immutable and mutable states are visually and structurally distinct.
3. Snapshot and HTTP output are versioned and deterministic apart from
   generation time and current progress.
4. One invalid category cannot silently corrupt another category's claims.
5. Browser presentation performs no Project writes or command execution.
6. Server routes are fixed and read-only.
7. The packaged application has no network or CDN dependency.
8. CLI and HTTP expose the same snapshot builder.

## Known gaps

- There is no progress event stream; the browser polls the bounded snapshot.
- Progress does not prove the originating process is still alive.
- Portfolio, Factor, and governed RL Runs have artifact-specific bounded
  explorers.
- Studio operations remain read-only.
- Remote and multi-user serving are not supported.
