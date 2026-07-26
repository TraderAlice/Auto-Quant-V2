# Give research Agents a fast governed candidate preflight

- Status: `completed`
- Updated: `2026-07-26`
- Related design: [[docs/design/candidate-preflight-feedback]],
  [[docs/design/agent-operator-experience]],
  [[docs/design/study-run-evidence]],
  [[docs/design/research-session-loop]], and
  [[docs/design/agent-cli-contract]].

## Outcome

An Agent working inside an active AutoQuant Session can validate one edited
candidate through a fixed, Study-local, seconds-scale preflight before paying
for the complete Judge. The result is structured, hash-bound to the exact
candidate and fixed preflight contract, visible through `aq orient` and Studio,
and explicitly has no metric, KEEP/REVERT verdict, selection role, trial-count
effect, promotion role, or trading authority.

## Context

The AI-first orientation milestone removed entry ambiguity, but the next
offered action for an active Session is still the full immutable Experiment.
Measured on the bounded reference fixtures:

- Factor formal Run: `3.55s`;
- Portfolio formal Run: `11.44s`;
- governed RL formal Run: `47.13s`;
- repository regression: `178` tests in `1061.725s`.

A syntax error, wrong candidate API, mutation, non-finite output, or obvious
lookahead therefore consumes the same formal Run/Experiment path as a
scientifically plausible candidate. This is poor feedback for the primary AI
operator and pollutes immutable research history with failures that carry no
useful quantitative comparison.

The fast path cannot be a smaller backtest whose score quietly enters
selection. A fixed preflight may reject structurally invalid candidates, but
only the complete Judge may publish metrics and decide KEEP/REVERT/CRASH.

## Scope

### In scope

- Add an optional fixed `preflight.json` beside one Study without changing the
  scientific Study or historical Run identity.
- Define a strict Python preflight runner contract, source closure, timeout,
  output protocol, and immutable CandidateCheck result.
- Add `aq session check <path> --session ID [--json]`.
- Validate active Session authority and require an exact changed candidate.
- Execute from an isolated source workspace against the owning Project's
  content-locked data root.
- Preserve passed/failed Check results under the Session, bound to candidate
  source, Study input, preflight source, Harness, and fixed authority.
- Keep failures editable in place: a failed Check never restores the leader,
  advances the Experiment sequence, creates a Run, or changes trial counts.
- Route `aq orient` and therefore Studio through:
  `candidate edit required → candidate check required/failed → formal evaluate`.
- Add bounded Factor/Portfolio checks for pandas factor API, determinism,
  input immutability, numeric alignment, finite values, and prefix causality.
- Add a bounded RL check for feature-name/vector alignment, determinism,
  input immutability, numeric finiteness, and fixed bounds.
- Preserve legacy Studies without a preflight; they continue directly to the
  complete Judge.

### Out of scope

- Producing a fast alpha score, approximate Sharpe/IC, or any selection metric.
- Replacing, sampling, weakening, or changing the complete Judge.
- Making preflight success mandatory for direct formal evaluation.
- Treating a Check as an Experiment, Run, Report, Dossier, admission gate, or
  promotion prerequisite.
- Generic linting of the AutoQuant repository or autonomous candidate repair.
- Streaming formal Judge progress or parallel search.

## Acceptance

- [x] A changed candidate with a fixed preflight can be checked through one
      versioned CLI command without creating a Run or Experiment.
- [x] Check identity binds the exact candidate, Study, preflight sources,
      fixed Session authority, data identity, Harness, and execution contract.
- [x] Passed and failed results are strict, immutable, tamper-verified, and
      contain no quantitative selection metric or verdict.
- [x] Failed checks preserve candidate edits for repair and do not change the
      leader, Experiment sequence, trial family, Reports, or Project source.
- [x] A later edit makes the prior Check stale; a matching passed Check makes
      formal `experiment evaluate` the Agent Work Brief's primary action.
- [x] Fresh/failed/stale/passed states produce truthful stable reason codes,
      exact operating roots, and no broader authority.
- [x] Factor, Portfolio, and RL reference Projects reject representative
      contract/causality failures and pass their baseline candidates in a
      materially cheaper bounded path.
- [x] Legacy Study/Run/Session identities and behavior remain compatible when
      `preflight.json` is absent.
- [x] Capability, schemas, CLI, Core, Studio projection, docs, package assets,
      focused tests, timing smoke, and full regression pass before push.

## Work

- [x] Measure current reference Run and repository-regression latency.
- [x] Define the no-selection preflight authority boundary.
- [x] Implement fixed preflight loading, execution, Check publication, and
      tamper verification.
- [x] Add Session CLI and Agent Work Brief state routing.
- [x] Add reference Factor/Portfolio/RL preflights and deterministic tests.
- [x] Complete timing, legacy, Studio, package, documentation, and full
      regression evidence; commit and push.

## Findings and decisions

- 2026-07-26 — Preflight is a separate optional `preflight.json`, not a field
  in `study.json`. Changing operational feedback must not retroactively change
  the scientific identity of an otherwise identical formal Study or Run.
- 2026-07-26 — Check results are immutable diagnostics so orientation can
  distinguish passed, failed, and stale candidates. They are excluded from
  Experiment history and research-family trial counts.
- 2026-07-26 — Formal evaluation remains callable without a Check. Orientation
  makes preflight the default Agent route when supported, while the complete
  Judge remains the only selection authority.
- 2026-07-26 — A freshly started Session has no changed candidate and should
  ask for an edit instead of offering an evaluate command that would fail with
  `experiment.unchanged`.
- 2026-07-26 — Preflight sources must be disjoint from both editable source
  and the formal Judge closure. Reference templates therefore use exact Judge
  inventories; a legacy broad `judges/**` Study must narrow deliberately
  before opting in.

## Verification

- `uv run python -m unittest tests.test_checks -v` — 3 tests passed, including
  exact passed/failed/stale routing, tamper rejection, non-selection state
  invariants, and reference Factor/Portfolio/RL pass/failure cases.
- Live Factor CLI smoke — Check execution `306ms`; full `aq session check`
  round trip `0.74s`; formal Factor Run baseline measured `3.55s`.
- `uv run python -m unittest tests.test_orientation tests.test_cli
  tests.test_sessions tests.test_studio tests.test_research_program -v` —
  37 tests exercised; one expected capability-list fixture was updated for
  the new public command, with no runtime regression.
- `uv build --wheel` — built `auto_quant-0.1.0-py3-none-any.whl`; inspection
  confirmed both fixed preflight scripts and `autoquant/checks.py`.
- `uv run python scripts/check_doc_links.py` — 652 links resolved.
- `uv run python -m unittest discover -s tests -v` — 181 tests passed in
  `1126.812s`, including complete Factor, Portfolio, governed RL, Session,
  Report/Dossier, Studio, and compatibility coverage.

## Progress log

- 2026-07-26 — Plan activated after measuring Factor, Portfolio, RL, and full
  repository feedback latency and auditing Study/Run/Session authority.
- 2026-07-26 — Implemented immutable CandidateCheck publication, Session/CLI
  integration, shared Core orientation state, reference checks, schemas,
  package assets, and bounded fail/pass/stale tests.

## Completion

Completed on 2026-07-26. Active research Agents now receive an exact
edit/check/evaluate feedback route when a Study opts into fixed preflight,
while legacy Studies and all formal Judge selection semantics remain
unchanged. The next independent milestone may improve formal Judge progress
or expand causal multi-interval research inputs without reopening this
non-selection evidence contract.
