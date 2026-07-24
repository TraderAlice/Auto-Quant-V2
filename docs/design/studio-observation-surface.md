# Studio observation surface

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/CLI]], [[docs/PROJECT_FORMAT]],
[[docs/design/agent-cli-contract]], [[docs/design/research-session-loop]],
[[docs/design/external-researcher-driver]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/request-bound-portfolio-mandates]], and
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
- verified Portfolio Mandate direction, construction, authorized/context-only
  assets, cash/cap, benchmark, and fixed identity when available;
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
5. What did the caller ask, is its dataset content-locked, and are the lane
   Reports and Project Dossier ready?
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

For a multi-Study Quant Research Program, the Project viewport is a research
cockpit rather than the report page of whichever Run happens to be selected.
It presents the current evidence chain in causal order:

1. validation rank IC asks whether the candidate factor predicts;
2. costed validation net Sharpe asks whether the mechanical portfolio preserves
   useful evidence after implementation; and
3. validation advantage versus the Judge-selected baseline asks whether the RL
   policy adds value beyond simpler fixed or contextual policies.

Those values remain descriptive projections of verified Run evidence. Browser
code may state exact relationships such as negative IC or trailing a baseline
and may visually mark them adverse. It cannot infer that a positive sign
passes uncertainty, robustness, minimum-improvement, or promotion gates. The
recommended lane and CLI action come from the verified Research Program status,
not from a browser-side workflow decision.

The cockpit shows all program lanes together, then exposes one complete bounded
Factor, Portfolio, or RL explorer at a time. Lane selection changes only
presentation and the accessibility tree; it does not select a model, Run,
baseline, validation split, or Judge outcome. An unbound collaboration handoff
is compact, while a caller-bound intake or delegated Session retains the full
request → evidence → report surface.

Selecting an evidence lane also selects that lane's latest Session in the
Inspector so the visible Run, Report, and Session remain semantically aligned.
The Portfolio and RL explorers disclose the same fixed mandate. Context-only
assets are visibly distinct and may never appear as current positions.

For a request-driven canonical Program, the collaboration surface composes no
evidence in the browser. Core supplies Dossier readiness, lane Report
currentness, explicit optional omissions, blockers, latest immutable summary,
and exact next command. The visible flow is
`request → lane Reports → Project Dossier → OpenAlice`. A selected Session may
change the evidence Inspector, but it does not demote the overall handoff back
to a single-lane Report.

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
9. Cross-lane cockpit labels describe verified relationships and never create
   a pass, rejection, KEEP, or promotion verdict.
10. Evidence-lane selection hides presentation detail only; every claim still
    comes from the same Core-projected snapshot.
11. Evidence lane and Inspector Session stay aligned; browser selection cannot
    combine one lane's explorer with another lane's Report.

## Known gaps

- There is no progress event stream; the browser polls the bounded snapshot.
- Progress does not prove the originating process is still alive.
- Portfolio, Factor, and governed RL Runs have artifact-specific bounded
  explorers.
- Studio operations remain read-only.
- Remote and multi-user serving are not supported.
