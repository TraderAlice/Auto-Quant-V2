# Independent research review handoff field trial

- Status: `completed`
- Updated: `2026-08-01`
- Target release: `0.9.16`
- Related design: [[docs/design/agent-native-quant-workbench]],
  [[docs/design/run-bound-research-reports]],
  [[docs/design/research-intake-and-dataset-snapshots]], and
  [[docs/design/agent-operator-experience]].

## Outcome

Prove whether a fresh quantitative coworker with no original conversation can
independently review one completed AutoQuant Project, distinguish immutable
calculation evidence from provider/package declarations and unbound supporting
files, detect overclaim or missing provenance, and leave a durable review
without mutating the research it audits.

The exact released `0.9.15` wheel is the baseline. `0.9.16` will contain only
the smallest coherent reusable repair justified by the untouched review
assignment. Breaking replacement is allowed when current semantics are wrong;
no compatibility layer or OpenAlice migration is required.

## Review assignment

Give a fresh reviewer a byte-for-byte copy of the completed `v0.9.15` field
Project `reported-book-path-stress` and its Workspace-owned staging evidence,
but no original prompt, transcript, implementation checkout, or private notes.
The reviewer must answer:

> Independently review the completed reported-book historical path-stress
> research. Do not trust the final prose merely because it is published. Use
> only public installed AutoQuant surfaces and the inherited Workspace to
> determine which central quantitative claims are independently reconstructed
> from immutable Run evidence, which data/provenance statements are only
> declared by a package or provider, which supporting claims depend on mutable
> Workspace files outside the Run/Report contract, and which claims cannot be
> verified. Check the five selected episodes, fixed-unit arithmetic, exact
> holding attribution, non-overlap selection, requested data endpoint,
> split-adjustment authority, independent Nasdaq coverage statement, and all
> evidence references. Return a durable English review with explicit verdicts,
> limitations, and remediation priorities. Do not edit the Project, acquire
> data, rerun research, create a Session, optimize the book, or grant trading
> authority.

The reviewer classification is frozen before it starts:

- `verified`: reconstructed or hash-verified by a strict public AutoQuant
  reader from Project-owned immutable evidence;
- `declared`: present in a verified manifest or snapshot but not independently
  authenticated by AutoQuant;
- `observed-unbound`: visible to the reviewer in Workspace files that are not
  bound into the reviewed Run/Report identity;
- `unverified`: absent, contradictory, stale, or not reproducibly connected to
  the reviewed evidence.

The review must distinguish scientific review from research execution. It may
inspect and interpret; it may not change inputs, create replacement results,
or silently promote mutable staging into immutable authority.

## Scope

### In scope

- One isolated fresh Grok 4.5 reviewer using the exact installed `0.9.15`
  release wheel and a copied completed Workspace.
- Read-only orientation, strict Project/Run/Report/Explorer validation,
  evidence-reference resolution, provider-package provenance classification,
  and durable review handoff.
- Exact transcript, filesystem mutation, command, evidence, and claim-class
  inventory.
- The smallest reusable Core, CLI, Studio, schema, template, Skill, or
  documentation repair for each reproduced review defect.
- A fresh candidate-wheel review replay and complete release audit before
  tagging `v0.9.16` when a product change is justified.

### Out of scope

- Recomputing the research through ad hoc pandas, acquiring replacement data,
  changing the reported book, rerunning the Judge, forecasting, optimization,
  causal episode labels, account authentication, Orders, or trading advice.
- Treating review prose as a new quantitative Run or allowing a reviewer to
  mutate the object it reviews.
- A universal trust/certification framework, reviewer reputation system,
  cryptographic provider attestation, central data catalog, or OpenAlice
  version change. OpenAlice remains on `0.8.31`.

## Acceptance

- [x] A fresh reviewer begins with no source checkout or original conversation,
      identifies the completed Project from public Workspace surfaces, and
      performs no Project or research mutation.
- [x] The reviewer uses strict readers rather than trusting Report prose or
      manually recomputing quantitative authority.
- [x] Every material claim is classified as verified, declared,
      observed-unbound, or unverified with an executable evidence reason.
- [x] The five episodes, fixed-unit path, greedy non-overlap, contributions,
      dominance conclusion, and formal dataset endpoint are independently
      verified from immutable Project evidence.
- [x] Split-adjustment semantics remain a package/provider declaration unless
      independently bound evidence proves more; Nasdaq overlap and route
      failure are not promoted beyond their actual binding.
- [x] The reviewer leaves one durable immutable or explicitly non-authoritative
      review artifact and does not create a Session, Run, candidate, or
      replacement primary Report.
- [x] Every material baseline failure is retained and classified; only a
      reproduced reusable Workbench defect enters the candidate release.
- [x] A fresh candidate reviewer completes the unchanged assignment using only
      installed public surfaces and produces a strict, portable, tamper-evident
      review when the admitted repair requires one.
- [x] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and no-local-override clean-clone smokes pass
      before publication.

## Work

- [x] Define and index the independent review assignment.
- [x] Build an isolated installed-`0.9.15` review desk from completed evidence.
- [x] Run and audit one fresh reviewer without coaching.
- [x] Admit and implement only reproduced reusable product friction.
- [x] Replay the unchanged task with a fresh candidate-wheel reviewer.
- [x] Complete the release audit and publish `v0.9.16` if warranted.

## Findings and decisions

- 2026-08-01 — Review is not another backtest lane. Its object is a frozen
  Project evidence graph; its output must never alter the truth it assesses.
- 2026-08-01 — A verified manifest field is not the same as authenticated
  provider truth. The reviewer must preserve this distinction explicitly.
- 2026-08-01 — Workspace staging may be useful acquisition history, but its
  presence alone cannot grant Run or Report authority. Portability and binding
  must be tested rather than inferred from filesystem proximity.
- 2026-08-01 — Existing Holdout Assessment is intentionally not generalized
  before the baseline. It interprets one frozen source-versus-later result and
  does not yet prove a general completed-Project review contract.
- 2026-08-01 — The untouched `0.9.15` reviewer completed the assignment in
  four minutes using installed public readers, independently hash-verified the
  Run and Report, reconstructed the fixed path-stress identities from strict
  Explorer output and bound artifacts, and left the inherited Workspace
  byte-for-byte unchanged (233/233 file hashes and the full path inventory).
- 2026-08-01 — Baseline review correctly separated the reported position and
  split-adjustment semantics as declarations, and classified the Nasdaq route
  failure and overlap comparison as `observed-unbound`. It found that Report
  finding `coverage-window` cited a bound artifact containing no Nasdaq
  evidence, so that clause is unverified as published.
- 2026-08-01 — The reusable defect is not missing quantitative readers. It is
  the absence of a Project-owned immutable Review identity: the reviewer could
  only leave loose Markdown that explicitly has no Workbench authority.
  `0.9.16` will add one narrow completed-Report Review contract with exact
  Report/Run identity, Core-resolved evidence classifications, canonical
  Markdown, and CLI/Studio discovery. It will not import staging into evidence,
  mutate the target, replace the primary Report, or generalize Holdout
  Assessment.
- 2026-08-01 — The fresh installed-`0.9.16` candidate reviewer independently
  discovered `review.publish`, selected detached publication, and produced one
  strict package in four minutes and 23 seconds. Its 8 `verified`, 4
  `declared`, 1 `observed-unbound`, and 1 `unverified` classifications retained
  the baseline result and the exact `coverage-window` reference-integrity
  defect. Public `review.show` passed and the inherited Workspace remained
  byte-for-byte unchanged (233/233 files and 396/396 paths).
- 2026-08-01 — Candidate publication exposed one low-severity entry-boundary
  discoverability issue: `staging/...` observed-file ids correctly require a
  Workspace entry path plus explicit `--project`, but the reviewer first tried
  a Project entry and then probed absolute and parent-relative ids. The
  security boundary remains unchanged; CLI help, machine capabilities, the
  validation diagnostic, and CLI documentation now state the exact route.

## Verification

Baseline trial:

- Released wheel: exact `auto_quant-0.9.15-py3-none-any.whl`.
- Fresh reviewer session: `019fbc45-acf9-71d1-ba76-dd7011ebff5f`.
- Durable loose review:
  `/Users/ame/autoquant-v0916-review-baseline/independent-review.md` with SHA-256
  `f19b3d98871b86e10b497700744afc7271ea6e49e3f71dcc3b4a17792a7d3de5`.
- Transcript:
  `/Users/ame/autoquant-v0916-review-baseline/baseline-transcript.md`.
- The worker used Python only to parse/hash strict reader output and immutable
  Run metrics; it did not re-price OHLCV or substitute ad hoc quantitative
  authority.
- Independent post-run `diff` confirmed identical pre/post Workspace hashes
  and paths.

Candidate trial:

- Candidate wheel:
  `/Users/ame/2607AutoQuant/Auto-Quant/dist/candidate-0.9.16-review/auto_quant-0.9.16-py3-none-any.whl`,
  SHA-256 `84629d5b045352dead4dd4d8487192c42a6ddb1b8d213b59e1d40d0fb9501587`.
- Fresh reviewer session: `019fbc63-e49c-7510-be74-a69c6ba18b5c`.
- Detached Review:
  `/Users/ame/autoquant-v0916-review-candidate/output/review-20260801T081829692481Z-e779b0ca5dba`.
- Package file SHA-256 values: `analysis.json`
  `b3f3e2d7687a27375bfe4ebebc0471022e278a80fe4394b1edf5a40a0f644a69`,
  `evidence.json`
  `431fc4f98ab2bf31fe999f77a457d50b5fa916add394402d111f3d01582e4597`,
  `manifest.json`
  `a651214a38964a970149386b7d34f3ccdc5e2be0aa94ae853b1cfc1998a3e66f`,
  `review.json`
  `3987c4eedac28ff41b62901c34602c28683408baa8e66614f9896caf6ff08a1d`,
  and `review.md`
  `cf5e1584a0a97a15f917e850fac58f8b468c59015a4337ef727fc4a79b09b093`.
- Transcript:
  `/Users/ame/autoquant-v0916-review-candidate/candidate-transcript.md`,
  SHA-256 `05915ce8678cc2324fe46dc20a76e7cee5bad3df7110928c9ee392137ac131d2`.
- The reviewer used public installed readers and Python only for structural
  parsing, hash checks, contribution reconciliation, and greedy-selection
  consistency over immutable reader/artifact output. It did not inspect the
  source checkout, acquire or re-price market data, rerun research, or mutate
  Project state.
- Independent post-run `diff` confirmed 233 identical file hashes and 396
  identical paths; output contained exactly one detached `review-*` package.

Release audit:

- Focused Review, Studio, repository Workspace, and CLI regression passed all
  37 tests in 103.131 seconds.
- Complete regression passed all 400 tests in 1,090.736 seconds.
- Documentation validation resolved all 1,374 double-links; `uv lock --check`,
  Python compile, Studio JavaScript syntax, and diff hygiene passed.
- Release artifacts built from clean implementation/field-trial commit
  `611f067e2bf65a4837b369679ea783141a8c965c`:
  - wheel `dist/release-0.9.16/auto_quant-0.9.16-py3-none-any.whl`,
    SHA-256
    `116f6bb2c3054713538c26d9b9a3a4114a0ac89d58c7ff3375c47ac4a359dad5`;
  - source distribution `dist/release-0.9.16/auto_quant-0.9.16.tar.gz`,
    SHA-256
    `cc42939e2facf7976c5b02d645fee524c33a65225155b080aa9bdb7106df35d5`.
- A fresh Python 3.11.14 environment installed the exact wheel with pandas
  3.0.5, reported `aq 0.9.16`, discovered all 57 public commands, loaded the
  Review schema, and exposed the observed-file Workspace-entry guidance in
  both capabilities and CLI help.
- A `git clone --no-local` checkout at
  `611f067e2bf65a4837b369679ea783141a8c965c` contained no local override,
  selected only `sample-research-desk`, and passed installed-wheel `validate`,
  `orient`, `project list`, and valid Studio snapshot.

## Progress log

- 2026-08-01 — Plan activated from clean released `v0.9.15`; OpenAlice remains
  independently pinned to `v0.8.31`.
- 2026-08-01 — Baseline field review passed the scientific task and exposed one
  product gap: no immutable general Review handoff and no machine-enforced
  distinction between Report-bound and merely visible Workspace evidence.
- 2026-08-01 — Candidate replay passed the unchanged scientific and
  no-mutation contract. One observed-file entry-root retry was retained and
  repaired as public discoverability wording without widening filesystem
  authority.
- 2026-08-01 — The clean full suite passed all 400 tests. Documentation,
  lock/syntax, source/wheel build, isolated install, 57-command
  capability/schema/help, and no-local-override clone smokes passed; release
  artifacts and hashes are frozen above.

## Completion

`v0.9.16` closes the reproduced independent-review handoff gap. A fresh
reviewer can now classify one frozen completed Report against its exact Run,
preserve provider declarations and unbound Workspace observations at their
real authority, publish one portable tamper-evident no-target-mutation Review,
and expose attached history to Studio. Baseline and candidate workers found
the same Nasdaq evidence-reference defect; all acceptance, regression,
documentation, build, install, and clean-clone checks pass. OpenAlice remains
independently pinned to `v0.8.31`.
