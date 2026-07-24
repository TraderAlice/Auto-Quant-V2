# Research program orchestration

Status: implemented.

Related: [[docs/design/quant-research-lifecycle]],
[[docs/design/research-intake-and-dataset-snapshots]],
[[docs/design/ohlcv-factor-lab]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/studio-observation-surface]].

## Purpose

One investment question may require several fixed evaluation questions. The
Project owns the evolving question and source; Studies own distinct immutable
evaluation authority.

The first canonical research program is:

```text
caller request + one content-locked OHLCV snapshot
        │
        ├─ factor-quality
        │    causal predictive evidence
        │
        ├─ portfolio-quality
        │    same factor → mechanical state → target weights → costs/risk
        │
        └─ governed-rl-policy
             fixed reference sleeves → adaptive-policy value-add challenge
```

The lanes are coordinated but do not collapse into one score.

## Project construction

`ohlcv-research-desk` creates:

- one Project-level request and dataset snapshot;
- one `factors/candidate.py` shared by Factor and Portfolio Studies;
- one `models/candidate.py` for the governed RL Study;
- precise fixed Judge closures for all three Studies;
- one program manifest declaring lane order, dependencies, roles, editable
  surfaces, and the RL integration boundary.

All Studies bind the exact same dataset id, version, universe, time range, and
file hashes. Canonical source and Judge files are written before any Study
identity is created so later construction cannot silently mutate an earlier
Study's fixed closure.

The Project intake manifest continues to bind the Factor Study as its primary
construction proof for V1 compatibility. The research-program loader verifies
all additional Study identities against the same dataset rather than treating
the single primary pointer as the whole Project.

## Lane semantics

### Factor quality

Owns causal factor discovery and professional IC/decay/quantile/stability
evidence. It edits `factors/**`.

### Portfolio quality

Owns whether the same current factor survives mechanical signal state,
position sizing, constraints, drift, turnover, cost, and risk. It also edits
`factors/**`.

Factor and Portfolio Sessions therefore share an editable surface. The
research-program projection marks simultaneous active Sessions as a conflict;
it never attempts an automatic merge.

### Governed RL policy

Owns whether a bounded adaptive state representation adds value beyond fixed
and contextual baselines. It edits `models/**`.

V1's actions are still fixed reference factor-mixture sleeves. The lane does
not yet consume arbitrary promoted `factors/candidate.py` as an action or state
input. The program must disclose this explicitly so proximity in one Project
is not mistaken for a causal artifact dependency.

## Verified status projection

`aq project program` loads the strict manifest and verifies:

- exact canonical lanes and dependency order;
- every referenced Study;
- shared dataset identity and hash;
- declared editable paths;
- latest immutable Run and whether its `studyInputHash` still matches current
  Project source;
- latest Session, experiment count, leader, and active state;
- immutable Reports for that Session;
- shared-surface concurrency conflicts.

Each lane is projected as:

- `not-started`: no Run or Session evidence;
- `baseline-ready`: current immutable Run exists, no Session;
- `researching`: an active Session exists;
- `reported`: the latest Session has an immutable Report;
- `stale`: the latest Project Run no longer matches current Study input.

These are coordination states, not scientific verdicts.

## Next actions

Core generates exact copy-only commands. It may recommend:

- inspect or execute a missing/stale Study baseline;
- start a delegated Session using the preserved request;
- inspect an active Session;
- inspect an immutable Report;
- advance to the next lane after upstream evidence is reported.

The browser renders these commands but cannot execute them. AI callers receive
the identical object through CLI JSON.

## Authority and invariants

1. A research program coordinates Studies; it cannot alter their Judges or
   promotion rules.
2. One dataset snapshot is materialized once and hashed by every Study.
3. Factor and Portfolio share source intentionally and cannot be researched
   concurrently without an explicit conflict.
4. Currentness is an exact hash comparison, never a timestamp guess.
5. Downstream evidence never retroactively changes an upstream Run.
6. Report readiness is not trading approval.
7. The RL integration boundary is explicit until a governed cross-Study
   artifact dependency exists.
8. AutoQuant has no OpenAlice provenance or live-trading authority.
