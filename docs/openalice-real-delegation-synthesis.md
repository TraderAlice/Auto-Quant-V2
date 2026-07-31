# AutoQuant 0.9 real-delegation synthesis

Status: field cohort and release-readiness audit accepted.

Related: [[plans/openalice-real-delegation-field-trials]],
[[docs/agent-employability-synthesis]],
[[docs/agent-employability-validation]],
[[docs/design/agent-native-quant-workbench]],
[[docs/design/agent-native-market-data-acquisition]], and
[[docs/design/quant-research-lifecycle]].

## Decision

AutoQuant is ready to act as a persistent quantitative coworker desk for
controlled OpenAlice use.

This does not mean every worker or provider route succeeds. It means a fresh
coding Agent can enter the same standalone Workbench, recover a delegated
question, acquire or bind auditable OHLCV, choose a supported research route,
produce immutable quantitative evidence, preserve negative or blocked
results, and return a useful answer without receiving trading authority.

The `0.9.0` field cohort deliberately tested whether the desk is good to work
at, not whether one more model could be added.

## Cohort

| Assignment | Useful outcome | Disposition |
| --- | --- | --- |
| Mainland-China Factor → possible weights | weak Factor evidence correctly blocked weights; exposed Git/session identity and intake lifecycle defects | exploratory pilot |
| Taiwan official-first Factor | official route remained unavailable; worker disclosed degradation and withheld the requested authority claim | framework retry only |
| Korean opening-gap event | Naver/Daum plus separate adjusted Yahoo evidence found no observed post-gap advantage | accepted |
| Reported semiconductor book | complete current-book crowding and reduction rankings answered the caller without optimizer or order claims | accepted |
| Crypto causal multi-interval Factor | exact 1h clock with completed 4h/1d context found no stable short-horizon reversion signal | accepted after integrity retries |
| US sector governed RL | richer state improved the learner but still failed the fixed KEEP and mechanical-baseline tests | accepted |

Negative evidence dominates this cohort by design. None of the accepted tasks
needed a positive backtest to be useful.

## Demonstrated strengths

### A new Agent can orient itself

Fresh Grok 4.5 workers discovered the Workspace, Project templates, Skills,
strict intake, editable closure, fixed Studies, Explorers, Reports, and Studio
without private source coaching. They maintained English internal briefs and
returned Chinese caller-facing handoffs when requested.

### One desk supports materially different research

The same Workbench handled:

- fixed price-event evidence;
- reported current-book risk;
- single-target temporal and causal multi-interval Factor research;
- cross-sectional Factor gates;
- caller-bound target-weight and risk assumptions;
- bounded governed RL versus mechanical baselines.

The Harness did not fragment into asset-specific engines or require a strategy
DSL. Ordinary pandas candidate code and Study-specific fixed Judges were
enough.

### Scientific refusal is a normal result

Workers correctly stopped when:

- official source authority was unavailable;
- validation evidence was weak or unstable;
- downstream Portfolio admission failed;
- a richer RL encoder improved absolute metrics but not enough to beat its
  predeclared threshold or mechanical alternatives.

No accepted task manufactured weights, Orders, TPSL, Broker activity, or a
trading instruction.

### Data acquisition works as Agent knowledge

Workers used the versioned Skill router and market-specific procedures rather
than a universal downloader. They preserved provider and adjustment semantics,
kept raw/normalized market bytes out of ordinary Git state, and used peer
sources only when their contracts could be compared honestly.

### Evidence is recoverable without the chat

Every accepted result is reconstructible from Project files, immutable Runs,
strict Explorer output, Session/Report state when applicable, Harness
identity, and Git. Studio and JSON CLI load the same verified evidence.

## Repaired weaknesses

Real workers found the following general defects. Each was repaired on the
`0.9.0` line, regression-tested, and independently retried:

| Observed failure | Repair |
| --- | --- |
| a Project-only Git commit falsely staled an unchanged Harness | executable Harness equality now uses id, version, source hash, and Python identity while retaining commit provenance |
| brief-first Project creation conflicted with atomic intake | intake may hydrate only the exact pristine selected scaffold and preserves Agent notes |
| workers mislabeled OpenAlice provenance or force-added ordinary data after seeing the tracked sample fixture | guidance defines source semantics, null unknown host ids, ignores root staging, and names the sample fixture exception |
| reported-book Runs omitted complete shorter-lookback rankings | every declared lookback now carries one verified complete ranking |
| generic Factor scaffolds invited evaluation before the caller candidate | the source is explicitly an API demonstrator and first commands require the real predeclared candidate before Session start |
| single-target temporal Factor intake demanded irrelevant context padding | request-bound temporal/relative-value decision populations use one/two-asset floors while cross-sectional breadth remains strict |
| Agent prose overclaimed that visible test evidence was unused | Core's `not-observable` and external-holdout wording is now explicit in operator guidance |
| single-lane templates opened request-free Sessions that could not publish terminal Reports | strict intake's verified Project request is the safe CLI default and templates show `--request request.json` explicitly |

The repair rule was deliberately conservative: fix only severe or independently
recurring friction, then give the changed path to a fresh worker. One-off
preferences remained observations rather than framework features.

## Honest remaining limits

- Provider access can fail or degrade. AutoQuant can preserve that boundary;
  it cannot make an exchange CDN available.
- A prose preregistration is not an immutable batch of multiple candidate
  source files. Current editable Sessions expose baseline test before later
  Experiments. A production-grade post-iteration claim still needs a fresh
  external holdout.
- Temporal Factor evidence does not yet publish the same component attribution
  surface as cross-sectional mode.
- Complete governed-RL evidence is heavy. The five-ETF two-Run case occupied
  about 79 MiB, principally for rationale, opportunity, and attribution
  artifacts.
- Coding Agents remain fallible. The Workbench makes mistakes visible and
  recoverable; it does not pretend they cannot happen.
- Method coverage is intentionally finite. Unsupported contract chains,
  microstructure, alternative data, or execution semantics must be declined or
  introduced through a justified new Lab.

## OpenAlice consumption boundary

OpenAlice should keep the integration thin:

```text
OpenAlice coworker request
  → persistent AutoQuant Workspace desk
  → coding Agent creates or continues one Project
  → AutoQuant research + immutable evidence
  → plain-language coworker handoff with applicable ids
  → requesting OpenAlice conversation
```

OpenAlice owns conversation, clarification, authenticated Workspace
provenance, live account state, execution planning, UTA, approvals, and order
submission. AutoQuant owns historical quantitative research.

No universal task DSL, metric transport schema, Broker adapter, or hidden
host-specific orchestration API is required. The universal outward object is
the coworker's answer; Run, Report, and Dossier ids remain applicable
supporting evidence rather than one mandatory artifact type.

## Checkout and version boundary

The Workbench keeps its ordinary Git checkout. A coding Agent may pull a newer
commit and resolve ordinary conflicts. If that is not worthwhile, the old desk
may be retired and a fresh one created.

AutoQuant does not add `aq upgrade`, automatic Workspace migration, or a
compatibility matrix while its research model is still evolving. Immutable
Runs retain the exact Harness identity under which they were produced; that is
evidence provenance, not a promise to migrate every old mutable desk.

## Release-readiness result

The `0.9.0` audit passed:

1. all 354 unit tests passed;
2. all 1,209 documentation double-links resolved;
3. lock validation and source/wheel builds passed;
4. a fresh Python 3.11 wheel install exposed version `0.9.0`, all 50 public
   commands, all 16 Skills, and completed Workspace/Project/Studio smoke;
5. a remote clean clone oriented to the checked-in sample, validated, listed
   Projects, projected its current Factor Explorer, and created a sibling
   Project through the installed wheel.

The line is release-ready. It is still described as the `0.9.0` development
line rather than “released `v0.9.0`” until a maintainer deliberately creates
that release.
