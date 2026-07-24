# Research selection and visible-test integrity

Status: V1 implemented.

Related: [[docs/ARCHITECTURE]], [[docs/PROJECT_FORMAT]],
[[docs/design/research-session-loop]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/quant-research-lifecycle]], and
[[docs/design/session-decision-matrix]].

## Scope

This document owns candidate-selection versus test-evidence semantics across
reference Runs, Sessions, Studio, and Research Reports. It defines what Core
can prove from immutable history and what must remain an explicit warning.

It does not make visible data secret, infer whether a human actually looked at
a metric, or manufacture a selection-adjusted statistic without sufficient
inputs.

## Run contract

Every successful reference Judge publishes:

```json
{
  "research_integrity": {
    "selection_split": "validation",
    "test_role": "visible-diagnostic",
    "test_enters_selection": false,
    "external_holdout_rule": "required-after-test-guided-iteration"
  }
}
```

The objective metric name is validation-specific:

- factor: `validation_mean_ic`;
- portfolio: `validation_net_sharpe`;
- RL: `validation_mean_net_sharpe`.

Test metrics remain in Run evidence. They are useful for audit and debugging,
but cannot affect KEEP/REVERT. A reference Judge may not describe them as
permanently untouched once exposed through normal Run output.

Generic user-authored Studies that do not publish this contract project
`selection_split=unspecified`, `test_role=unspecified`, and do not receive
invented claims about their evaluator.

## Session projection

Core derives selection integrity only from verified state:

- selection metric and declared split from the current leader Run;
- candidate trials from immutable Experiment count;
- KEEP, REVERT, and CRASH counts from immutable verdicts;
- evaluated Runs as baseline plus candidate trials;
- test visibility and objective use from the Run contract;
- `externalHoldoutRequired=true` when at least one candidate trial exists and
  test evidence is visible.

Core cannot know whether a person or Agent read a particular field. It uses a
conservative rule: after visible test evidence and candidate iteration, the
same test range no longer supports a fresh holdout claim.

## Report evidence

Research Reports freeze the exact Session selection-integrity projection beside
Runs, Experiments, and Campaigns. Report loading recomputes it from the frozen
Experiment prefix and leader Run, then rejects any mismatch even if all report
files were rehashed.

Core renders a Markdown section containing:

- selection metric and split;
- candidate/evaluated Run count and verdict counts;
- test role and whether it enters selection;
- whether a new external holdout is required;
- the fixed warning.

Agent analysis may add interpretation but cannot omit or overwrite this
Core-authored disclosure.

## Studio projection

Studio receives the same Session projection. It shows trial count and holdout
status beside the leader, and labels test values on Run cards as audit evidence.
It does not estimate a corrected Sharpe, decide that a holdout is fresh, or
reset history.

The Session Decision Matrix follows the same boundary. Only declared
validation metrics can enter baseline comparison and non-dominance. Test rows
use a distinct audit relation, full-scope diagnostics remain display-only, and
context values have no preference direction. Showing those rows cannot change
the immutable KEEP/REVERT/CRASH chain.

## Invariants

1. Reference KEEP/REVERT objectives use validation only.
2. Visible test metrics never enter a reference objective.
3. Trial and verdict counts come from verified immutable Experiments.
4. A candidate trial after visible test evidence triggers the conservative
   external-holdout requirement.
5. Report and Studio projections share Core-derived values.
6. Generic Studies receive explicit unknowns, not inferred evaluator claims.
7. Historical test visibility cannot be undone by deleting or reverting a
   candidate.

## Change checklist

- Name the selection split in every new reference objective.
- Keep diagnostic test fields separate from objective fields.
- Update Session, Report, Studio, template docs, and tests together.
- Never describe exposed test evidence as untouched.
- Add a statistical adjustment only with a dedicated design that fixes inputs,
  assumptions, and interpretation.

## Known gaps

- There is no blind/encrypted test execution or one-time reveal operation.
- Trial count is disclosed but not yet transformed into Deflated Sharpe or
  family-wise error control.
- External data governance remains an OpenAlice/organization responsibility.
