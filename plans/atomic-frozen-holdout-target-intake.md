# Atomic lane-aware frozen-holdout target intake

- Status: `completed`
- Updated: `2026-07-30`
- Originating Project:
  `/Users/ame/2607AutoQuant/grok-field-trials/v0820-frozen-holdout/desk/workspace/projects/grok-build-megacap-source-v0820`
- Related design: [[docs/design/frozen-external-holdout-challenge]],
  [[docs/design/research-intake-and-dataset-snapshots]], [[docs/CLI]], and
  [[docs/PROJECT_FORMAT]].

## Outcome

A Coding Agent can take one current source Dossier plus a caller-supplied
strictly later OHLCV package and atomically create a frozen target Project
whose intake requirements match the Dossier's included lanes. The operation
uses the source Project's canonical request, never leaves a weaker unbound
Project behind, and advertises the exact one-shot holdout Run as its next
action.

## Context

A fresh installed-`aq 0.8.20` Grok worker completed a valid 2024–2025 Factor
Session, Report, promotion, and Factor-only Dossier. It then truthfully stopped
because the caller-fixed 2026-01-02 through 2026-07-27 package contains 141
XNYS sessions while ordinary `ohlcv-research-desk` intake requires 240 rows
and every diagnostic horizon to retain 20 eligible observations in all three
research splits.

That 240-row rule is appropriate for a fresh coordinated Factor → Portfolio →
RL mining desk. It is unnecessarily broad for a Factor-only Dossier's frozen
external audit: the candidate is already selected, Portfolio/RL are absent,
and the primary 5-session validation objective still has 23 eligible later
observations. Requiring an Agent to create the target through ordinary
research intake also forces it to rediscover and reproduce the source
Project's canonicalized request before binding.

## Scope

- Add one public atomic `holdout create-target` command.
- Take the source Project/Dossier as request and lane authority; accept only a
  target Workspace, target Project id, and later dataset package from the
  caller.
- Use lane-aware minimum history:
  - Factor-only: at least 120 rows plus primary-horizon validation capacity;
  - included Portfolio: at least 180 rows;
  - included governed RL: at least 240 rows.
- For the target intake gate, require 20 eligible observations for the exact
  primary objective in the fixed validation slice. Keep all diagnostic
  horizons visible in the immutable Run; do not use them for target
  selection.
- Create the ordinary research-desk Project and frozen binding atomically.
  On any compatibility, non-overlap, source, or binding failure, remove the
  staged target and restore Workspace configuration exactly.
- Materialize the sparse-secondary-diagnostic behavior in the bound target's
  fixed Factor Judge closure. Do not change the ordinary template Judge or
  stale the repository sample's historical `0.8.7` Run.
- Keep ordinary `project intake` and existing two-Project `holdout bind`
  behavior unchanged.
- Explain that Project intake stores canonical request JSON and that holdout
  equality is canonical-content equality, not caller key-order preservation.

## Acceptance

- [x] A 141-session Factor-only target that preserves at least 20 primary
      validation observations can be created, bound, run once, and verified.
- [x] The same bytes remain rejected by ordinary research-desk intake.
- [x] Portfolio/RL Dossiers retain their 180/240-row target floors.
- [x] The atomic operation copies source canonical request authority and
      rejects overlap, incompatible data, stale Dossiers, and existing target
      ids without leaving Project or Workspace mutations.
- [x] CLI help, capabilities, orientation, Studio, and durable docs agree on
      the new operation and its no-selection/no-trading authority.
- [x] A fresh installed-wheel Grok retry completes the unchanged caller-fixed
      141-session external audit without source/docs/error-driven workaround.
- [x] Full regression, documentation graph, wheel install, and exact-commit
      clone smoke pass.

## Field verification

A second fresh Grok Build worker used only an isolated installed
`auto-quant-0.8.21` wheel and public CLI/schema discovery under:

`/Users/ame/2607AutoQuant/grok-field-trials/v0821-frozen-holdout-retry`

It rebuilt the source Project from the unchanged caller bytes, spent one
Factor Experiment, published a Factor-only Dossier, discovered
`holdout create-target`, and completed the 141-session later audit with one
holdout invocation. Source validation objective mean IC was
`0.10125313283208022`; the exact frozen 2026 objective was
`-0.28467908902691513`. The later object therefore weakened by
`-0.38593222185899534`; Core did not convert that result into selection or
trading authority.

Independent verification found:

- both Projects valid and present in Studio with no diagnostics;
- source and target canonical request bytes equal;
- one target Run, no target Session, and one terminal holdout result;
- `execution.evaluationRole=external-temporal-audit`;
- 23 usable primary 5-session validation observations;
- the secondary 10-session validation diagnostic retained with 18
  observations and `sufficient=false`.

The worker's remaining observations do not broaden this plan. CLI envelope
`ok` continues to mean command/protocol success while Check verdict remains
domain data; more localized causality diffs are a separate diagnostic
enhancement; and the holdout result deliberately preserves the source
objective metric id for exact comparison while its evaluation role prevents
re-selection semantics.

## Verification

- `uv run python -m unittest discover -v`:
  312 tests passed in 799.389 seconds.
- `uv run python scripts/check_doc_links.py`:
  1,094 documentation links resolved.
- Built `auto_quant-0.8.21-py3-none-any.whl`, installed it into a fresh Python
  3.11 environment, and passed version, capability, Workspace, Project,
  orientation, and validation smoke.
- The release commit is re-cloned without local override before the tag is
  pushed; this final publication check does not mutate repository content.
