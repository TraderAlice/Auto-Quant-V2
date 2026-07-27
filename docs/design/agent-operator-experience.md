# AI-first Agent operator experience

Status: implemented for the V2 Agent Work Brief, evidence-driven research
agenda, and read-only orientation surface.

Related: [[docs/design/agent-cli-contract]],
[[docs/design/agent-native-quant-workbench]],
[[docs/design/research-program-orchestration]],
[[docs/design/research-session-loop]],
[[docs/design/external-researcher-driver]],
[[docs/design/evidence-driven-research-agenda]],
[[docs/design/studio-observation-surface]], and
[[docs/design/study-run-evidence]].

## Purpose

AutoQuant is operated primarily by coding Agents. A human, a local Agent, or a
coworker in a host such as OpenAlice may supply the question. Humans define or
approve intent, review evidence, and accept or reject the result. The default
operating surface must therefore optimize for a new Agent to sit at an existing
Workspace desk and take one correct bounded action, while preserving a concise
truthful review surface for humans.

The interface is not a larger prompt. It is a verified Core work contract:

```text
Workspace / Project path
+ verified request and Project construction
+ current Study / Session / Run / Report state
+ scientific progression and conflicts
+ verified diagnosis and bounded experiment briefs
+ fixed authority and editable closures
→ Agent Work Brief
├── aq orient --json
├── concise human terminal projection
└── Studio decision brief
```

Existing detailed objects remain available for deep inspection. Orientation
answers what the operator should do now and why.

The brief must work without an external orchestrator. Host Session identity,
cross-Workspace communication, and authenticated provenance may add context,
but Project files and Core evidence remain sufficient to orient a replacement
Agent. Standalone and hosted operation use the same brief contract.

## Operator and reviewer roles

The Agent is the principal research operator. It may:

- inspect verified context and evidence;
- record a concrete Project-observed Workbench gap in `framework-needs.md`
  at the canonical Project coordination surface, outside an active candidate
  edit/evaluate operation, without changing fixed research authority;
- start an explicitly offered bounded operation;
- edit only the candidate closure inside an active Session worktree;
- propose a falsifiable hypothesis;
- evaluate through the fixed Judge;
- inspect immutable verdict and diagnostic evidence.

The Agent may not:

- change the request, dataset snapshot, Study, Judge, objective, mandate, gate,
  immutable history, or promotion rules;
- treat visible-test diagnostics as selection evidence;
- copy candidate source into the canonical Project outside the guarded
  promotion operation;
- infer trading authority from research weights, Reports, or Dossiers.

The human is the intent owner and evidence reviewer. Human review does not
create a second evaluator: Studio displays the same Core work brief and
evidence that the Agent receives.

An external coworker may delegate or discuss a task, but does not become the
quantitative evaluator. Its message is caller context until AutoQuant binds it
to a Project request and fixed research authority.

## Assignment clarification before orientation

The verified Agent Work Brief orients work after enough Project authority
exists to derive current state. It does not replace the earlier act of
understanding an assignment.

For a genuinely new question, the Quant Agent uses `aq project create` to
establish a self-contained construction site, then reads and updates the
returned Project-root `research.md` in English. Before downloading data,
editing research source, training, or evaluating, the Agent must make the
decision context, question, scope, horizon, evidence, caller-owned constraints,
evaluation meaning, deliverable, assumptions, unresolved questions, and
proposed route explicit.

The Agent chooses research methods using domain judgment. It asks the
delegating Agent or user whenever missing intent could materially change the
universe, direction, horizon, risk interpretation, benchmark, evaluation, or
usefulness of the answer. Clarification repeats until the question is bounded
and falsifiable. Conversation may use the caller's language; Project working
materials use English, and the user-facing Agent may translate the final
evidence.

Strict requests and manifests are derived after this step. They make understood
authority machine-verifiable but are not an automatic intake parser or a
substitute for the living Markdown brief.

## Agent Work Brief

The V2 brief is compact, strict, and derived entirely from verified current
state. It contains:

- identity: Workspace/Project and optional delegated request;
- objective: current research question and selected Study objective;
- focus: lane, Study, coordination phase, scientific stage, and operating
  mode;
- evidence: current Run/Session/Report/Dossier identities needed to understand
  the focus, without embedding raw histories or complete diagnostics;
- blockers: stable reason codes, explanations, and whether they arise from
  missing coordination evidence, scientific admission, staleness, or source
  conflict;
- authority: selection split, visible-test role, research authority, and
  `tradingAuthority: none`;
- research agenda: zero to three deterministic Factor, Portfolio, or
  governed-RL experiment briefs derived from the current immutable leader
  evidence, each with editable targets, typed evidence references, validation
  checks, and stop conditions;
- filesystem contract: the exact operating root, candidate-editable patterns,
  and protected authority categories;
- primary action: one existing Core-generated command with exact `argv`,
  working directory, operation effect, and expected evidence kind;
- supporting read-only actions only when they materially help the primary
  action.

The brief does not copy the entire program projection. A caller may use the
referenced detailed command when it needs full lane, Run, Session, or report
history.

The research agenda does not replace the primary action. It says which
scientific change is worth testing after the lifecycle permits an edit;
`primaryAction` still says whether the operator must establish a baseline,
start a Session, run preflight, evaluate, publish, complete, or promote. Agenda
moves have no operation effect and cannot execute themselves.

Factor moves can prioritize explicitly declared components, but they never
infer Python provenance or claim that a fixed diagnostic-blend removal is an
arbitrary final-factor ablation. Portfolio moves can change only the factor
closure; fixed Mandate, sizing, risk, execution, and cost rules remain
evaluation pressure. RL moves can change only the causal encoder; fixed
factors, actions, rewards, learning rules, and Portfolio mechanics remain
protected. Positive validation evidence may intentionally produce a
freeze-and-external-holdout move instead of another in-sample edit.
Once such a Dossier is bound into a later Project, the work brief switches to
`external-audit`, exposes no editable paths, routes only to `holdout.run`, and
marks the research agenda unavailable because candidate selection is frozen.
After the terminal result it returns to `observe`.

## Operating modes

Operating modes summarize existing state; they do not replace it.

- `observe`: choose a Project or inspect a terminal/complete result.
- `establish-baseline`: execute missing or stale immutable baseline evidence.
- `edit-and-evaluate`: operate only inside an active Session worktree and
  evaluate one hypothesis.
- `publish-evidence`: freeze the current leader and evidence prefix in a
  Report or Dossier.
- `external-audit`: execute the exact Dossier-bound source once on the
  strictly later Project; no candidate edit or selection is permitted.
- `complete`: retain a reported baseline or finish required cross-lane
  research without changing candidate source.
- `promote`: apply an accepted non-baseline Session leader through the existing
  guarded promotion operation.

One brief has exactly one primary mode and at most one primary action.

## Filesystem authority

The distinction between ownership and current edit authority is explicit.

Before a Session exists, a Study may declare `factors/**`, `strategies/**`, or
`models/**` as its candidate source closure. This describes what a future
Session may stage; it is not an instruction for a governed Agent to edit the
canonical Project directly.

During an active Session:

- `operatingRoot` is the disposable Session Project;
- editable paths are resolved beneath that root;
- the canonical Project, request, data, Study, program, Judge, mandate,
  dependency closures, Runs, Experiments, Reports, and Dossiers are protected;
- the primary candidate action is `experiment evaluate` or a terminal evidence
  operation already authorized by the Session state.

No brief may advertise two writable roots.

## Operator reason taxonomy

Stable Project-level reason categories distinguish:

- `study-selection-required`;
- `baseline-evidence-missing`;
- `current-evidence-stale`;
- `session-required`;
- `session-active`;
- `scientific-gate-blocked`;
- `report-required`;
- `shared-source-conflict`;
- `promotion-ready`;
- `baseline-completion-ready`;
- `required-research-complete`.

Implementation may add more specific codes, but it must not collapse
scientific rejection into missing workflow state or describe an immutable
negative result as an infrastructure failure.

A Workspace with a declared default Project resolves normally. A Workspace
without a default requires `--project ID` through the existing structured
`workspace.selection-required` CLI error. Orientation never guesses which
research question the Agent should operate.

## CLI and Studio parity

`aq orient` is read-only and uses the standard versioned CLI envelope.
`nextActions` repeats the brief's exact primary/supporting actions using the
existing action schema and declared effects.

Studio receives the same brief and a Core hash. JavaScript may format or
progressively disclose its fields. It must not independently choose the focus
lane, derive a scientific stage from metric signs, rank experiment briefs,
invent filesystem authority, or substitute a different next action.

## Feedback tiers

Orientation must truthfully distinguish the feedback operations that already
exist:

- structural inspection and validation;
- fixed seconds-scale candidate preflight;
- bounded baseline Run execution;
- Session Experiment evaluation;
- full repository engineering regression.

It must not advise a Project Researcher to run the AutoQuant repository's full
engineering suite, nor pretend that structural validation or preflight creates
selection evidence. Preflight preserves the fixed Study boundary and formal
Judge authority.

## Invariants

1. Orientation is read-only and cannot start research implicitly.
2. Every claim is reconstructed from verified Core state.
3. There is one operating root, one primary mode, and at most one primary
   action.
4. Existing lifecycle and scientific-gate objects remain authoritative.
5. A work brief never grants broader edit authority than its active Study and
   Session.
6. Validation selects; visible test audits; neither role is rewritten for
   convenience.
7. CLI and Studio share the exact brief and hash.
8. Every brief states that AutoQuant has no trading authority.
9. Agenda ordering uses train context and validation evidence only; visible
   test audit cannot change a move, its order, or its wording.
10. Agenda moves never broaden the declared editable closure or become
    executable lifecycle actions.
11. A standalone Agent and a host-started Agent receive the same quantitative
    orientation for the same Workspace state.
12. Required orientation survives replacement of the native Agent Session;
    private chat history is never the only source of Project truth.

## Known limitations

- V1 orients one selected Project, not a portfolio of simultaneous Projects.
- It does not measure Agent token use, reasoning quality, or provider cost.
- It does not execute commands or guarantee that an external Agent follows
  them.
- Recipes are fixed for the reference Factor, Portfolio, and governed-RL
  objectives; unknown Study objectives are explicitly unsupported.
