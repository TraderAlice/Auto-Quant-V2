# Let Session worktrees re-enter read-only CLI orientation

- Status: `proposed`
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

- Define a confined, verifiable backlink from a Session worktree to its owning
  Project and Session.
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

- [ ] `aq orient .` from an active Session worktree returns the same brief,
      reasons, evidence, and next action as orientation from its owning
      Project.
- [ ] Resolution uses the exact owning Project and Session locks; forged,
      stale, moved, escaped, and symlinked paths fail clearly.
- [ ] Dataset bytes remain only in the canonical Project and candidate
      evaluation identity remains unchanged.
- [ ] Human CLI, JSON, Studio, docs, focused/full regression, and a fresh
      external coding-Agent retry all pass.

## Work

- [ ] Audit positional Project resolution and Session worktree
      materialization boundaries.
- [ ] Add the smallest authenticated owner/session marker and confined
      resolver.
- [ ] Route read-only orientation through the resolved canonical context and
      expose both roots without ambiguity.
- [ ] Add adversarial path/identity tests, documentation, and a clean Grok
      retry.

## Findings and decisions

- 2026-07-29 — Preserve the empty Session `data/` directory. Copying bytes
  multiplies storage and symlinks weaken the existing no-symlink confinement
  rule; CLI owner resolution is the intended route.
- 2026-07-29 — Generated lifecycle commands already target the canonical
  Project, so this plan begins with read-only orientation instead of widening
  every command's path semantics.

## Verification

- Pending.

## Progress log

- 2026-07-29 — Proposed from the clean Grok promotion-v6 retry after
  `aq orient <session-worktree> --json` reproduced
  `validation.failed / dataset.directory`.

## Completion

Pending.
