# Agent employability validation

Status: active acceptance record.

Related: [[plans/agent-employability-validation]],
[[docs/agent-employability-trial-template]],
[[docs/trading-request-field-trials]],
[[docs/design/agent-native-quant-workbench]],
[[docs/design/agent-operator-experience]], and
[[docs/design/project-derived-workbench-needs]].

## Question

Can a fresh coding coworker who does not know AutoQuant receive a quantitative
assignment and reliably return a scientifically truthful, useful answer using
only the installed Workbench, the assignment, and supplied data?

This is stricter than asking whether AutoQuant contains the required Lab or
whether a framework developer can complete the workflow.

## Evidence grades

| Grade | Meaning |
| --- | --- |
| `A — qualifying` | Fresh worker, installed release, no repository internals or coaching, exact prompt/output preserved, immutable Project evidence independently verified, and final answer audited. |
| `B — worker evidence` | Fresh installed worker evidence exists, but one qualifying condition or the complete answer audit still needs confirmation. |
| `C — capability evidence` | A real-data Project proves the research method and evidence contracts, but execution was led by the framework-development context. |
| `D — fixture evidence` | Deterministic tests or samples prove mechanics only. |
| `unknown` | The record does not establish enough worker conditions; absence is not upgraded by inference. |

Only Grade A trials count toward the final employability cohort. Lower grades
remain useful for choosing the next assignment and avoiding redundant Core
work.

## Qualifying worker protocol

A qualifying trial fixes the following before the worker starts:

1. Install one exact released wheel in a fresh environment.
2. Give a fresh no-memory worker only:
   - the caller-style assignment;
   - the intended Workspace or permission to create one;
   - staged data and truthful provenance;
   - the installed `aq` command and its public help/schema surfaces.
3. Do not provide repository source, tests, plans, other Project answers,
   private implementation instructions, web access, subagents, or corrective
   hints. A task may explicitly permit a provider-retrieval tool in a separate
   trial, but that changes the declared worker packet.
4. Preserve the exact prompt, durable outward handoff, environment and wheel
   identity, staged-input hashes, command transcript or retry summary, created
   Project identities, immutable evidence ids, final answer, and elapsed time.
   Private reasoning or chain-of-thought is neither required nor an acceptable
   substitute for the outward record.
5. Do not coach through a failure. End and classify the attempt, improve Core
   only under the promotion rule, and retry the unchanged assignment with a
   different fresh worker.
6. Have the Workbench Agent independently validate the Project, Runs,
   Reports/Dossiers, Studio projection, raw-input immutability, and every claim
   in the outward answer.

Clarification is correct behavior when caller-owned meaning is materially
missing. A validation REVERT, negative result, unsupported boundary, or
decision not to enter Portfolio/RL is not a retry.

## Observation record

Each trial uses one concise Markdown record. It must answer:

- What exact user decision and raw language did the worker receive?
- What data, release, tools, permissions, and time boundary were supplied?
- Did the worker select the right Project and Study route?
- Did it ask only necessary caller-owned clarifications?
- Did it discover the operating root and editable/fixed boundary?
- How many worker-caused CLI retries, Core failures, and formal research
  Experiments occurred?
- Did it distinguish validation selection, visible test audit, Session verdict,
  scientific qualification, and external-holdout requirements?
- Did it create any unintended Project, Session, Run, holdout, Portfolio, RL,
  Order, or trading claim?
- Did its final answer directly answer the user, cite immutable evidence,
  explain uncertainty and limitations, and stop at the right point?
- What friction belongs to research method, one worker, documentation,
  discoverability, correctness, or missing Core capability?
- Did independent verification agree with every material claim?

Counts and timestamps are recorded, but no weighted score hides a scientific
failure. Each dimension is marked `pass`, `friction`, `fail`, or `unknown`.

## Outcome classes

| Outcome | Meaning |
| --- | --- |
| `independent-pass` | Useful verified terminal answer, no worker-caused CLI retry, no coaching, and no material semantic drift. |
| `recoverable-pass` | Useful verified terminal answer after one worker-caused recoverable CLI retry. |
| `high-friction-pass` | Useful verified terminal answer after two or more worker-caused retries; valuable evidence, but not acceptable in the final cohort. |
| `useful-boundary` | Worker correctly stops for missing caller authority, unsupported semantics, or insufficient evidence and explains what is needed. |
| `operational-block` | The intended supported route cannot complete because of discoverability, runtime, CLI, or evidence-contract friction. |
| `semantic-failure` | The worker changes the question, misuses evidence, overclaims qualification, exceeds authority, or returns an answer unsupported by immutable evidence. |

## Friction promotion

- Any scientific-integrity, data-provenance, authority, or trading overclaim is
  severe and may justify an immediate bounded Core plan after reproduction.
- An operational block that prevents a supported assignment may justify an
  immediate fix when independently reproduced.
- Discoverability or wording friction becomes Core work after the same failure
  appears in two independent workers or two materially different assignments.
- A one-off low-severity observation remains recorded. The Workbench does not
  accumulate features merely to erase every worker preference.
- Every fix is retried on the unchanged assignment by a different fresh worker.
  The failed predecessor remains evidence and is never rewritten.

## Initial coverage audit

This is deliberately conservative. [[docs/trading-request-field-trials]]
remains the detailed research-result ledger.

| Assignment family | Strongest current evidence | Employability state | Next action |
| --- | --- | --- | --- |
| Reported-book crowding/sizing | Real Yahoo fixed Studies plus `0.8.22` installed-worker Book Risk/Event desk | `A — qualifying` for descriptive crowding | Fresh target-sizing remains optional coverage; fixed Book Risk answer and desk behavior now reconcile independently. |
| Price event behavior | Real NVDA/SPY Event Study plus final `0.8.26` zero-retry installed worker | `A — qualifying` | Exact prompt/handoff, staged hashes, Project, Run, Explorer, orientation, validation, and Studio reconcile. |
| Daily editable Factor with a negative conclusion | `0.8.28` nine-asset price/volume worker, one REVERT, zero CLI retry | `A — qualifying` | Seed of the final cohort; retain unchanged. |
| Multi-interval/context Factor | Real BTC and gold/dollar Projects plus installed-worker candidate-contract trials | `B — worker evidence` | Audit isolation and answer quality; run a fresh different task if incomplete. |
| Factor-to-Portfolio target weights | Real global-ETF and Crypto programs; `0.8.19` fresh worker correctly stopped at the Factor gate | `A — useful-boundary`, but no target-weight handoff | Run a fresh caller-style assignment whose valid evidence can exercise downstream Portfolio without forcing a positive result. |
| Portfolio-native fixed Allocation | `0.8.24` final-wheel capped ERC fidelity worker | `A — qualifying` | Exact validation-performance/fidelity split reconciles independently; other Allocation workers remain optional audit evidence. |
| Governed RL incremental value | Clean unchanged nine-asset RL Run under 120 seconds with a negative Report | `C — capability evidence` | Give a fresh worker a bounded RL-relevant question and audit whether it selects, interprets, and stops correctly. |
| Multi-Project desk selection | `0.8.22` installed worker completed independent Book Risk and Event Projects | `A — qualifying` | Treat as operability evidence, not a substitute for research-answer coverage. |
| Honest unsupported boundary | Several Projects refuse contract-chain, labelled-event, Broker, and Order semantics | `B — worker evidence` | Include one fresh ambiguity/boundary case only if the four-task cohort lacks it. |

## Final cohort gate

The final cohort includes the clean `0.8.28` Factor trial and at least four
fresh post-plan workers across materially different assignments.

It passes only when:

- every task produces a useful verified answer or useful boundary;
- no final replay contains a semantic failure, provenance fabrication, hidden
  caller-intent change, or trading-authority overclaim;
- at least 80% are `independent-pass`;
- none requires live coaching, source inspection, or more than one
  worker-caused CLI retry;
- fixed, editable, Portfolio, multi-interval/context, and governed-RL or
  explicit RL-gate behavior are represented;
- every reported number and conclusion reconciles to immutable evidence;
- every remaining friction has an explicit accept/fix/defer disposition.

Only then may a follow-up plan freeze the minimum OpenAlice consumption
contract. Host integration is not part of this validation record.

## Trial ledger

| Trial | Grade | Outcome | Route | Worker retries | Final-answer audit | Notes |
| --- | --- | --- | --- | ---: | --- | --- |
| `v0.8.19-multistage-factor-portfolio` | `A` | `high-friction-pass` | editable Factor → Portfolio gate | 2 | passed | One SPY-required candidate earned KEEP but failed fixed HAC qualification; worker correctly withheld Portfolio/RL, but two Report evidence-reference guesses exposed the gap fixed and freshly retried in `0.8.20`. |
| `v0.8.22-multi-project-fixed-studies` | `A` | `independent-pass` | Book Risk + Event Study in one desk | 0 | passed | Explicit Project selection preserved separate datasets, one fixed Run per Project, truthful descriptive answers, and no Session/trading work. |
| `v0.8.24-capped-erc-fidelity` | `A` | `independent-pass` | fixed Portfolio-native Allocation | 0 | passed | Worker separated positive validation relative performance from 0/6 construction-fidelity decisions and did not collapse them into one strategy claim. |
| `v0.8.26-manifest-root-event` | `A` | `independent-pass` | fixed Event Study | 0 | passed | One adopted Workspace, one Project, one Run; staged bytes stayed unchanged; 22-event descriptive answer retained wide uncertainty and no trading authority. |
| `v0.8.28-price-volume-negative` | `A` | `independent-pass` | daily editable Factor | 0 | passed | Nine Yahoo assets; baseline used only real daily inputs; one checked REVERT; Report/completion retained the baseline; no Portfolio, RL, holdout, Order, or second Experiment. |
| `cohort-01-sector-factor-portfolio` | `A` | `independent-pass` | editable Factor → Portfolio gate | 0 | passed | First fresh post-plan worker. Eleven sector ETFs plus SPY; one failed and one passing bounded Check, one REVERT, and a truthful negative handoff. Fixed Factor qualification withheld Portfolio weights. |

The four pre-plan rows establish strong historical evidence but do not count
toward the required four fresh post-plan workers. Additional historical rows
remain pending conservative audit. Fresh rows are added only after independent
evidence verification.

Fresh post-plan progress: `1/4`. The first worker covers editable Factor and a
truthful Factor-to-Portfolio gate, but does not yet satisfy the target-weight
handoff coverage item because the scientific gate correctly blocked
Portfolio.

Its exact packet and review live outside the product repository at
`/Users/ame/2607AutoQuant/grok-field-trials/cohort-01-sector-factor-portfolio`.
The installed `0.8.28` CLI independently revalidated the Project, both Factor
Runs, Report, Dossier, program gates, orientation, Studio, staged source
hashes, and normalized intake hashes. A natural 252→21 skip-month candidate
failed the bounded 256-timestamp/prefix Check and was changed to 126→21 before
the sole formal Experiment. That scientifically costly first occurrence is
recorded and deferred pending independent recurrence or a separately justified
contract fix. Post-trial agenda ambiguity did recur for the second materially
different assignment, so [[plans/optional-post-trial-research-agenda]] is now
active.
