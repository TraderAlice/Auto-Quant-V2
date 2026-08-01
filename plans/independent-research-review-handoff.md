# Independent research review handoff field trial

- Status: `active`
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

- [ ] A fresh reviewer begins with no source checkout or original conversation,
      identifies the completed Project from public Workspace surfaces, and
      performs no Project or research mutation.
- [ ] The reviewer uses strict readers rather than trusting Report prose or
      manually recomputing quantitative authority.
- [ ] Every material claim is classified as verified, declared,
      observed-unbound, or unverified with an executable evidence reason.
- [ ] The five episodes, fixed-unit path, greedy non-overlap, contributions,
      dominance conclusion, and formal dataset endpoint are independently
      verified from immutable Project evidence.
- [ ] Split-adjustment semantics remain a package/provider declaration unless
      independently bound evidence proves more; Nasdaq overlap and route
      failure are not promoted beyond their actual binding.
- [ ] The reviewer leaves one durable immutable or explicitly non-authoritative
      review artifact and does not create a Session, Run, candidate, or
      replacement primary Report.
- [ ] Every material baseline failure is retained and classified; only a
      reproduced reusable Workbench defect enters the candidate release.
- [ ] A fresh candidate reviewer completes the unchanged assignment using only
      installed public surfaces and produces a strict, portable, tamper-evident
      review when the admitted repair requires one.
- [ ] Focused/full tests, documentation links, lock/syntax, build/install,
      Studio, root Workspace, and no-local-override clean-clone smokes pass
      before publication.

## Work

- [x] Define and index the independent review assignment.
- [x] Build an isolated installed-`0.9.15` review desk from completed evidence.
- [x] Run and audit one fresh reviewer without coaching.
- [ ] Admit and implement only reproduced reusable product friction.
- [ ] Replay the unchanged task with a fresh candidate-wheel reviewer.
- [ ] Complete the release audit and publish `v0.9.16` if warranted.

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

## Progress log

- 2026-08-01 — Plan activated from clean released `v0.9.15`; OpenAlice remains
  independently pinned to `v0.8.31`.
- 2026-08-01 — Baseline field review passed the scientific task and exposed one
  product gap: no immutable general Review handoff and no machine-enforced
  distinction between Report-bound and merely visible Workspace evidence.

## Completion

Complete this section only after every acceptance item is independently
verified and the release, if any, is published.
