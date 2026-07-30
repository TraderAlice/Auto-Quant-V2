# AutoQuant employability synthesis and OpenAlice gate

Status: accepted cohort under `v0.8.30`.

Related: [[plans/agent-employability-validation]],
[[docs/agent-employability-validation]],
[[docs/design/agent-native-quant-workbench]],
[[docs/design/quant-research-lifecycle]], and
[[docs/design/agent-cli-contract]].

## Decision

AutoQuant is employable as an independent quantitative-research coworker.

This claim is deliberately narrower and more useful than “AutoQuant supports
quant research.” A fresh coding Agent that does not know the repository can
receive an ordinary caller assignment, discover the installed Workbench,
preserve the question and data, choose a supported route, operate the fixed
and editable boundaries, interpret validation and visible-test evidence, stop
without trading authority, and return a useful identifier-bound answer.

The final cohort contains five materially useful workers:

| Worker | Research decision | Outcome |
| --- | --- | --- |
| clean `0.8.28` seed | Daily price/volume Factor; no stable edge | `independent-pass` |
| post-plan 1 | Sector Factor → Portfolio gate | `independent-pass` |
| post-plan 2 | Reported retail-book crowding/risk | `independent-pass` |
| post-plan 3 | BTC multi-interval Factor → target weights | `recoverable-pass` |
| post-plan 4 | Global-ETF governed RL vs mechanical sleeves | `independent-pass` |

Every worker returned a useful verified answer or supported boundary. Four of
five completed without a worker-caused CLI retry, exactly meeting the 80%
gate. No final worker received live coaching, inspected repository internals,
changed caller intent, used test evidence for selection, fabricated
provenance, claimed trading authority, or required more than one recoverable
worker retry.

Negative evidence is part of the result. The cohort includes a rejected
Factor, a scientifically blocked Portfolio transition, a valid all-cash
target book, and a REVERTed RL encoder. Employability means reaching the right
bounded answer, not manufacturing a positive backtest.

## What is now stable

### Desk model

- AutoQuant is a persistent Workspace containing ordinary Projects.
- A Project is one evolving research body; it keeps its English brief, source,
  fixed Studies, immutable Runs, Sessions when applicable, Reports, and
  artifacts.
- A request usually creates a new Project, but completed coworker work remains
  on the desk and is normal reusable context.
- The installed AutoQuant version is part of evidence identity. Historical
  Projects and Runs retain their original Harness identity.

### Coworker operating contract

- `aq capabilities --json`, public schemas, `aq orient`, validation errors,
  and the filesystem provide enough information for a fresh Agent.
- The Agent writes or completes English `research.md` before quantitative
  execution and asks the caller when material intent remains ambiguous.
- Fixed Studies produce immutable descriptive evidence without inventing a
  Session. Editable Studies use exactly the advertised closure, fast Check,
  bounded Experiment, formal KEEP/REVERT, Report, and terminal completion or
  promotion.
- Validation governs selection. Visible test remains audit-only; external
  holdout is a separate explicit contract.
- Portfolio and governed RL preserve caller-owned asset roles, mandate,
  benchmark, costs, cadence, risk ceiling, and no-trading authority.

### Outward answer contract

The universal outward object is a coworker handoff, not one mandatory Core
artifact kind.

A useful handoff:

1. directly answers the caller in plain language;
2. names exact immutable Run/Experiment/Report/Dossier identifiers that
   actually apply;
3. distinguishes validation, visible test, scientific qualification, and
   external-holdout limits;
4. explains assumptions, uncertainty, and unsupported claims;
5. states `tradingAuthority: none` in substance and stops.

A fixed single-lane Study may cite its Run and Explorer without manufacturing
a Session Report. A standalone editable lane may have a Report but no
multi-Study Dossier. A multi-lane program may publish both. OpenAlice must not
require an inapplicable artifact merely to obtain a uniform transport shape.

## Minimum OpenAlice consumption boundary

OpenAlice may now consume AutoQuant as another original Workspace desk without
embedding AutoQuant's research internals.

The minimum stable boundary is:

```text
OpenAlice coworker request
  ├── English Markdown assignment
  ├── caller-owned data files and provenance
  └── pinned AutoQuant version
            ↓
persistent AutoQuant Workspace / Project
            ↓
fresh coding Agent uses public aq + filesystem
            ↓
plain-language handoff + applicable immutable evidence ids
            ↓
OpenAlice research conversation decides what to do next
```

OpenAlice needs only to:

1. select/install one pinned AutoQuant release;
2. create or reuse a persistent Workspace desk;
3. stage the Markdown assignment and caller-owned files inside that desk's
   authorized intake area;
4. launch a coding coworker with the installed `aq` command and desk-local
   filesystem;
5. preserve the resulting Project and return the coworker's handoff to the
   requesting conversation;
6. optionally use `aq orient --json`, `aq validate --json`, and
   `aq studio snapshot --json` for read-only observability.

OpenAlice does **not** need to:

- translate every request into a universal strategy or task DSL;
- select the Study route on the Agent's behalf;
- parse every quantitative metric into Launcher state;
- require Report or Dossier existence for every route;
- copy Project state out of the Workspace;
- expose Broker, Order, TP/SL, account, or live-trading authority to
  AutoQuant.

OpenAlice still owns conversation, user clarification, live account state,
execution planning, Orders, Broker adapters, and final trading decisions.
AutoQuant owns the independent research desk and returns decision support.

## Remaining boundaries

- Data remains caller- or provider-supplied OHLCV with explicit provenance;
  provider claims are not automatically authenticated.
- The Workbench is broad, not universal. Unsupported event labels, contract
  chains, microstructure, Broker semantics, or account authority require an
  explicit boundary or later Lab rather than improvisation.
- Repeated visible-test inspection consumes research value; external holdout
  remains deliberate and separate.
- Fixed and single-lane routes do not share one universal immutable outward
  artifact type. This is accepted because the Agent handoff is universal.
- One long nine-asset RL execution hit the current 120-second template timeout
  before later locked executions completed in roughly 93–113 seconds. This is
  recorded as a first occurrence and is not yet a general timeout change.
- Agent performance is good enough to employ, not infallible. Raw CLI errors,
  Project evidence, and independent validation remain part of the operating
  model.

## Friction dispositions

| Observation | Disposition |
| --- | --- |
| First daily Factor surface exposed misleading multi-interval/test context | fixed in `0.8.28` |
| Completed research agenda looked mandatory | fixed in `0.8.29` |
| Root-staged symlink rejected | accepted confinement boundary; physical copy works |
| Fixed/single-lane route lacks Report or Dossier | accepted applicability boundary |
| Public fixed-weight benchmark rejected by Mandate builder | fixed in `0.8.30` |
| RL fast Check omitted advertised runtime fields | fixed in `0.8.30` |
| One 120-second long-panel RL timeout | defer pending recurrence or a bounded runtime plan |

## Gate

The employability gate is passed. OpenAlice consumption work may begin only
as a thin desk lifecycle and coworker-handoff integration around the minimum
boundary above. It should not freeze AutoQuant's current internal CLI command
sequence or turn quantitative research into a trading-execution subsystem.
