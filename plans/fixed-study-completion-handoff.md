# Make fixed-Study completion an explicit answer handoff

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]],
  [[docs/design/evidence-driven-research-agenda]],
  [[docs/design/reported-position-book-risk]],
  [[docs/design/ohlcv-price-event-study]], and
  [[docs/design/portfolio-native-allocation-lab]].

## Outcome

After a current successful fixed Book Risk, Price Event, or Allocation Run, a
Coding Agent sees that no further CLI work is required, receives an explicit
instruction to write and return the decision-support answer, and can still use
the exact verified Explorer as an optional read-only supporting action.

## Context

A fresh external Grok Build coworker used only the installed AutoQuant
`0.8.13` CLI to classify a non-predictive ERC request, independently choose
`ohlcv-allocation-lab`, create a Project, execute the fixed Study exactly once,
reconcile the Allocation Explorer, and write the correct answer without
starting a Session, Factor lane, RL lane, or Order.

Post-Run orientation contained the right facts—`review.status: complete`,
`descriptive-audit-complete`, no agenda moves, and a read-only Explorer—but
still placed `run.allocation` in `primaryAction`. The worker therefore had to
infer that inspection was optional and the actual next step was an Agent-owned
written answer.

The same field trial also found that `researchAgenda.run.inputHash` contained
the Study input hash while every other exact Run identity surface labels the
Run's Harness-bound hash `inputHash`. The two valid hashes were semantically
mislabelled.

## Scope

### In scope

- Give completed fixed Book Risk, Price Event, and Allocation Studies no
  primary CLI action.
- Keep their exact Explorer as a supporting read-only evidence path.
- Put the Agent-owned write/return handoff in `review.next` without fabricating
  an unexecutable CLI action or new operation effect.
- Make `researchAgenda.run.inputHash` equal the immutable Run's own
  `inputHash`.
- Preserve CLI, Studio, human review, tests, and documentation parity.

### Out of scope

- Adding a structured universal outward-report object.
- Making Markdown authoring a Core mutation command.
- Automatically sending a response to OpenAlice or a user.
- Changing fixed Study, Judge, dataset, metric, or selection semantics.
- Changing the distinct `studyInputHash` field on immutable Runs.

## Acceptance

- [x] A complete fixed Study has `primaryAction: null`, `operatingMode:
      observe`, `review.status: complete`, and an explicit write/return
      instruction.
- [x] Its exact `run.book-risk`, `run.event-study`, or `run.allocation`
      Explorer remains one supporting read-only action and remains projected
      through ordinary envelope `nextActions` and Studio commands.
- [x] No fake `review.write-*` command or `agent-local` operation effect is
      introduced.
- [x] Every descriptive agenda's `run.inputHash` equals the same immutable
      Run `inputHash` returned by `run show` and its Explorer.
- [x] Focused/full regression, docs, build/install smoke, and one fresh
      installed-wheel Grok retry pass.

## Work

- [x] Reproduce both Project-observed completion-handoff defects.
- [x] Implement terminal fixed-Study action ordering and exact Run identity.
- [x] Update fixed Book Risk, Event, Allocation, CLI, Studio, and schema
      regression coverage.
- [x] Update public design/docs and the originating Project need disposition.
- [x] Complete clean installed-wheel retry.
- [x] Complete final regression and release audit.

## Findings and decisions

- 2026-07-29 — A complete Work Brief should have no mandatory executable
  action. The Explorer remains valuable evidence access, so it becomes
  supporting rather than disappearing.
- 2026-07-29 — Writing or returning an answer is Agent-owned work, not a Core
  command. Use `review.next`; do not invent a non-executable action merely to
  fill `primaryAction`.
- 2026-07-29 — The research agenda already has one field named `inputHash`.
  Correct it to the Run's actual Harness-bound `inputHash` rather than widening
  the compact agenda with a second Study hash.

## Verification

- Focused Allocation, Book Risk, Event Study, orientation, and CLI regression
  passed all 56 tests.
- `uv run python scripts/check_doc_links.py` resolved all 1,059 documentation
  links; `git diff --check` passed.
- Source distribution and wheel build passed; a fresh environment installed
  `auto-quant==0.8.14`.
- Fresh installed-wheel Grok Project
  `grok-build-fixed-completion-v0814` independently selected
  `ohlcv-book-risk-lab` and completed exactly one fixed Run
  `run-20260729T135618598499Z-a37e9d56fb52` without a Session, Factor,
  Portfolio, RL, or Order.
- The coworker and an independent installed-CLI audit both verified null
  primary action, explicit answer handoff, supporting `run.book-risk`,
  human/JSON/Studio parity, Project validity, one Run and zero Sessions.
- Agenda and immutable Run input hashes both equal
  `d3b3032338d7673aae5f604e421000bc426966b81c02388a2de0d9d81f0d1685`;
  the separate Study input hash remains
  `a9b960c09c1b3be34597a547ef6ecceb5acf9f123bf3329dfef62cfac1ebeaaf`.
- `uv run python -m unittest discover -s tests -v` passed all 302 tests in
  874.499 seconds.
- Final source distribution, fresh-install, capability, version, validation,
  orientation, Run inspection, and Studio smoke passed before release.

## Progress log

- 2026-07-29 — Activated from installed-wheel Project
  `grok-build-allocation-handoff-v0813` after the worker completed the
  assignment correctly but had to infer both terminal answer handoff and exact
  hash meaning.
- 2026-07-29 — Fresh installed-wheel Project
  `grok-build-fixed-completion-v0814` used the public CLI only, selected the
  correct fixed Book Risk route, executed exactly one Run, and passed both
  completion-handoff and Run-hash assertions with no new open Workbench need.

## Completion

AutoQuant `0.8.14` gives every completed fixed Book Risk, Price Event, and
Allocation Study an honest terminal handoff: no mandatory Core action, one
explicit Agent-owned write/return instruction, and the exact strict Explorer
available as optional evidence. Its descriptive agenda now names the immutable
Run's actual input identity. A fresh external installed-wheel coworker used
these surfaces to complete a real Book Risk audit in one Run, return the
correct evidence-backed answer, and report no new Workbench need.
