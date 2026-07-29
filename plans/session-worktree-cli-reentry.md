# Let Session worktrees re-enter read-only CLI orientation

- Status: `completed`
- Updated: `2026-07-29`
- Related design: [[docs/design/agent-operator-experience]],
  [[docs/design/research-session-loop]], and
  [[docs/design/study-run-evidence]].

## Outcome

An Agent can run `aq orient .` from the exact Session worktree advertised as
its `operatingRoot`. Core resolves that worktree back to its owning canonical
Project and active Session, reads the locked canonical dataset closure, and
returns the same verified Agent Work Brief as orientation from the Project
root.

## Context

The clean AutoQuant `0.8.11` Grok retry followed
`filesystem.operatingRoot` literally and invoked orientation from the Session
worktree. The command failed `dataset.directory` because Session worktrees
intentionally contain an empty `data/` directory: evaluation receives the
owning Project's content-locked data root without duplicating potentially
large dataset bytes.

Generated Session check, evaluate, and promotion commands already use the
canonical Project path and remain correct. The friction is CLI re-entry:
`operatingRoot` truthfully names the only writable candidate surface, but that
surface cannot currently be used as the positional Project argument for
read-only orientation.

## Scope

### In scope

- Define a confined, fixed-inventory-locked Session marker and verify it
  against the worktree's exact owning Project and Session topology.
- Resolve `aq orient <worktree>` and equivalent read-only inspection through
  the owning Project's locked dataset and Session authority.
- Keep JSON, human CLI, and Studio projection equal to canonical-Project
  orientation.
- Reject copied, moved, stale, symlinked, or forged worktrees rather than
  guessing an owner.
- Make the distinction between writable `operatingRoot` and canonical
  evidence root explicit to Agents.

### Out of scope

- Copying large dataset closures into every Session.
- Symlinking dataset directories into disposable worktrees.
- Treating a detached worktree as an independent Project.
- Allowing mutation commands to bypass their existing explicit canonical
  Project and Session arguments.

## Acceptance

- [x] `aq orient .` from an active Session worktree returns the same brief,
      reasons, evidence, and next action as orientation from its owning
      Project.
- [x] Resolution uses the exact owning Project and Session locks; forged,
      stale, moved, escaped, and symlinked paths fail clearly.
- [x] Dataset bytes remain only in the canonical Project and candidate
      evaluation identity remains unchanged.
- [x] Human CLI, JSON, Studio, docs, focused/full regression, and a fresh
      external coding-Agent retry all pass.

## Work

- [x] Audit positional Project resolution and Session worktree
      materialization boundaries.
- [x] Add the smallest authenticated owner/session marker and confined
      resolver.
- [x] Route read-only orientation through the resolved canonical context and
      expose both roots without ambiguity.
- [x] Add adversarial path/identity tests, documentation, and a clean Grok
      retry.

## Findings and decisions

- 2026-07-29 — Preserve the empty Session `data/` directory. Copying bytes
  multiplies storage and symlinks weaken the existing no-symlink confinement
  rule; CLI owner resolution is the intended route.
- 2026-07-29 — Generated lifecycle commands already target the canonical
  Project, so this plan begins with read-only orientation instead of widening
  every command's path semantics.
- 2026-07-29 — A fresh `0.8.11` Grok coworker independently reproduced the
  exact `dataset.directory` failure from the advertised `operatingRoot`, then
  safely completed one Check and one REVERT Experiment through canonical
  Project commands. This confirms a general Agent-operability defect rather
  than a one-off promotion-trial artifact.
- 2026-07-29 — Topology inference alone cannot distinguish an ordinary
  standalone Project from a copied Session worktree. New worktrees will carry
  one strict marker inside their fixed inventory; read-only orientation will
  resolve only when that marker, Session manifest, canonical Project, exact
  worktree path, and locked marker hash agree.
- 2026-07-29 — A repeated request for an executable first-edit action remains
  deliberately declined. Candidate editing is Agent-owned preparation; the
  brief already exposes root, closure, reason, and review instruction, while
  CLI actions retain executable-command semantics.
- 2026-07-29 — The installed-wheel retry exposed one adjacent real defect:
  promotion returned a redundant `run.execute` while post-promotion
  orientation selected `session.start`. Promotion now projects actions from
  the same reconstructed Work Brief as orientation and Studio.

## Verification

- `uv run python -m unittest discover -s tests -q` passed all 299 tests.
- `uv run python scripts/check_doc_links.py` resolved all 1,048 links.
- Focused Session/CLI tests prove exact worktree/canonical human and JSON
  parity, Studio parity, absent copied data, direct mutation non-redirection,
  marker locking even against a matching editable pattern, and rejection of
  detached, forged, missing, changed, and symlinked markers.
- The first clean `0.8.11` Grok coworker Project
  `grok-build-worktree-reentry-v0111` reproduced the exact worktree
  `dataset.directory` failure, then completed one passing Check and one REVERT
  Experiment without touching framework source.
- A fresh Grok coworker using only a new installed `0.8.12` wheel created
  `grok-build-worktree-reentry-v0812-retry`; worktree orientation succeeded
  before source inspection, retained canonical/worktree parity with no copied
  data, and completed Check
  `check-20260729T121515296398Z-990bdd36a4e6`, KEEP Experiment
  `exp-0001-c97180509d5a`, guarded promotion
  `promotion-20260729T121546426161Z-8d7264014275`, validation, and Studio.
- A final fresh Python 3.11 wheel install repeated worktree/canonical
  orientation, Check `check-20260729T122121184924Z-f559e827c355`, KEEP
  Experiment `exp-0001-b34ea230528c`, guarded promotion
  `promotion-20260729T122126905978Z-804005a9aeb8`, post-promotion action
  equality, validation, and Studio with Harness `0.8.12`,
  `commit: unavailable`, and `dirty: false`.

## Progress log

- 2026-07-29 — Proposed from the clean Grok promotion-v6 retry after
  `aq orient <session-worktree> --json` reproduced
  `validation.failed / dataset.directory`.
- 2026-07-29 — Activated after independent Project
  `grok-build-worktree-reentry-v0111` naturally reproduced the same failure
  and preserved a full baseline → Check → REVERT report.
- 2026-07-29 — Implemented a strict root marker forced into fixed inventory,
  exact owner/session/topology/hash resolution for `orient` only, canonical
  JSON context, dual-root human output, and no-data-copy CLI/Studio parity
  coverage. Mutation commands retain direct Project semantics.
- 2026-07-29 — Fresh installed-wheel Grok retry and final wheel lifecycle
  passed. The retry's post-promotion action drift was fixed and independently
  rechecked before completion.

## Completion

AutoQuant `0.8.12` makes the advertised Session worktree an honest read-only
orientation entry point. Core verifies one fixed-inventory-locked marker
against the exact canonical Project, Session, topology, and hash; it keeps
dataset bytes canonical and every mutation command explicit. Human CLI, JSON,
Studio, a failing predecessor trial, a successful installed-wheel Grok retry,
and a final clean wheel lifecycle now agree. Promotion responses also reuse
the post-mutation Work Brief instead of suggesting redundant evidence.
