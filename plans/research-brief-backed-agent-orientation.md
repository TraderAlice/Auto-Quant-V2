# Make Agent orientation follow the maintained research brief

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/agent-cli-contract]], and
  [[docs/design/workspace-project-boundaries]].

## Outcome

An unfamiliar coding Agent can rewrite a local Project's flexible English
`research.md`, run `aq orient`, and receive the actual maintained research
question plus its source path through the same Core object used by Studio.
Delegated request manifests remain higher authority, and Projects without a
clearly headed question retain the safe Project-description fallback.
The completed change ships as AutoQuant `0.8.9`.

## Context

The first clean Grok Build onboarding field trial successfully discovered the
effective repository-root Workspace, created
`grok-build-onboarding-smoke`, wrote a precise English brief, executed exactly
one bounded Factor Run, and interpreted weak-positive evidence honestly.
It also found that orientation continued to show the short create-time
description instead of the later `### Research question` maintained in
`research.md`.

That behavior contradicts the documented division of authority:
`research.md` is the Project's Agent-maintained narrative authority, while the
Agent Work Brief is supposed to orient a replacement coworker without a
documentation scavenger hunt. The Project observation is preserved in its
canonical `framework-needs.md`.

## Scope

### In scope

- Extract a clearly headed `Research question`, `Research question ...`, or
  `Fixed question` section from the manifest-declared research program.
- Preserve Markdown content through the next same-or-higher-level heading,
  with a bounded size suitable for orientation.
- Make delegated intake request title/question/path take precedence.
- Identify research-brief-derived questions distinctly in the strict Agent
  Work Brief contract and expose the source path to CLI and Studio unchanged.
- Cover extraction, fallback, delegated precedence, CLI JSON, and Studio
  parity with deterministic tests and a second clean external-Agent field
  trial.

### Out of scope

- Replacing flexible Markdown with a rigid research-question manifest.
- Automatically rewriting `research.md`, parsing caller intent, or selecting a
  Study.
- Changing Project default-selection behavior, CLI installation, Run envelope
  shapes, or large Explorer payloads found in the same field trial.
- Changing any dataset, Study, Judge, factor, evaluation semantic, or immutable
  Run.

## Acceptance

- [x] A local Project with a clearly headed maintained question returns that
      exact section as `question.text`, identifies the research brief as its
      origin, and returns its absolute source path.
- [x] A delegated Project continues to return the request manifest's title,
      question, origin, and path even when `research.md` contains different
      text.
- [x] A Project without a recognized question heading safely falls back to its
      manifest name/description and does not guess from arbitrary prose.
- [x] CLI JSON and Studio contain the exact same Core Agent Work Brief and
      hash after the contract change.
- [x] A fresh Grok Build Project independently confirms that its rewritten
      question is visible from orientation before research execution.
- [x] Documentation links, focused tests, complete unit tests, build/package
      smoke, and repository-root CLI smoke pass without regenerating research
      fixtures or immutable Runs.
- [x] Package/README/CLI/Harness version identity agrees on `0.8.9`.

## Work

- [x] Preserve the first Grok field-trial observation in the originating
      Project and activate this repository plan.
- [x] Implement bounded Markdown-section extraction and version the Agent Work
      Brief method.
- [x] Update strict schema tests, CLI/Studio parity tests, and public design
      documentation.
- [x] Run focused and complete verification plus a fresh Grok field trial.
- [x] Build and smoke the `0.8.9` source/wheel distributions.
- [x] Audit every acceptance item, resolve the Project need with retry
      evidence, and complete the plan.

## Findings and decisions

- 2026-07-29 — The mismatch is not an intake-authority problem. Delegated
  `request.json` already gives Core an exact machine-bound question and must
  remain first. The gap affects locally created Projects whose working intent
  evolves in the required Markdown brief.
- 2026-07-29 — Extraction will recognize an explicit question heading rather
  than infer a question from arbitrary prose. This preserves flexible
  Markdown while preventing Core from pretending that instructions or method
  notes are caller intent.
- 2026-07-29 — This plan deliberately leaves the other field-trial friction
  items separate so one retry can attribute any improvement to the changed
  orientation contract.
- 2026-07-29 — `sourcePath` identifies either the delegated request or
  maintained Markdown source. The existing `requestPath` remains populated
  only for delegated intake, so a research brief is not mislabeled as a
  machine-bound request.
- 2026-07-29 — The independent retry passed before creating evidence, then
  completed one bounded baseline only to prove question provenance remains
  stable through the normal lifecycle.

## Verification

- `uv run python -m unittest -v tests.test_orientation tests.test_studio
  tests.test_cli` — 28 focused orientation/CLI/Studio tests passed in 41.035
  seconds.
- `uv run python -m unittest discover -s tests -v` — 289/289 tests passed in
  819.903 seconds.
- `uv run python scripts/check_doc_links.py` — 1,033/1,033 documentation
  double-links resolve.
- `node --check autoquant/studio_assets/studio.js`, `git diff --check`, and
  the repository-root `aq orient`/Studio equality audit passed.
- First Grok field trial (`grok-build-onboarding-smoke`) reproduced the stale
  create-time question. Fresh retry
  `grok-build-orientation-v4-retry` saw exact
  `project-research-brief` text and source before any Run, then produced
  `run-20260729T102102694588Z-bb36fea1de60`; independent audit found one Run,
  zero Sessions, unchanged template candidate hash, valid Project state, and
  identical CLI/Studio work briefs.
- `uv build --out-dir /tmp/autoquant-0.8.9-dist-2` produced the `0.8.9` sdist
  and wheel. A fresh Python 3.11 environment installed that wheel, discovered
  capabilities, initialized an empty Workspace, created a Factor Project,
  projected its maintained question identically through CLI/Studio, and
  completed installed-wheel Run
  `run-20260729T104008027209Z-cb009f62930a` with
  `autoquant.python-judge` `0.8.9`, `dirty: false`.
- No checked-in or external historical Run was regenerated; the retry and
  installed-wheel smoke created new evidence only in their own new Projects.

## Progress log

- 2026-07-29 — Plan activated from the clean
  `grok-build-onboarding-smoke` field trial under AutoQuant `0.8.8`.
- 2026-07-29 — Implemented the v4 question projection, provenance, bounded
  Markdown extraction, human compaction, and Studio origin label.
- 2026-07-29 — Fresh Grok retry and independent audit passed, then full
  regression and installed-wheel verification closed `0.8.9`.

## Completion

AutoQuant `0.8.9` now makes its first verified orientation command agree with
the flexible English brief that Agents are required to maintain. Structured
delegated authority remains first, arbitrary prose is never promoted into
intent, and CLI/Studio share the same source-aware object. The original
Project need preserves the failure and links the successful independent retry.
Other onboarding friction from the first Grok trial remains deliberately
separate for later evidence-led iterations.
