# Establish Study contracts and immutable RunResult evidence

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/ARCHITECTURE]],
  [[docs/design/study-run-evidence]], [[docs/design/agent-cli-contract]], and
  [[docs/design/workspace-project-boundaries]].

## Outcome

An AutoQuant Project can own one or more strict quantitative Studies; a human
or Agent can execute a selected Study through one bounded Python Judge and
receive an immutable, self-describing RunResult that pins the Study, Judge,
editable source closure, dataset/universe/time range, Harness identity,
metrics, artifacts, logs, duration, status, and errors.

## Context

The Workspace/Project foundation creates the construction site but cannot yet
produce research evidence. The old AutoQuant loop prints metrics to stdout and
stores a compact untracked ledger, which is useful Agent memory but
insufficient for cross-Project inspection, reproducibility, Studio, or ML.

Mujica Research Lab V2 establishes the transferable evidence shape:
human-owned program, explicit editable source closure, fixed Judge, bounded
execution, immutable artifacts, and manifest written last. AutoQuant first
needs the Study/Run half of that protocol before it can safely add isolated
Agent mutation, KEEP/REVERT/CRASH Experiments, or promotion.

## Scope

### In scope

- Strict project-local `studies/<id>/study.json` and `program.md`.
- A single standardized `python` Judge lane with a project-confined entrypoint,
  fixed arguments, timeout, and strict result-output protocol.
- Explicit subject kind/name, editable exact files or `/**` directory closures,
  primary metric direction/minimum improvement, and dataset identity including
  asset class, universe, and time range.
- Validation that the Study, program, and Judge are outside the editable source
  closure and that every owned path is real, confined, and non-symlink.
- Deterministic hashes for Study, Judge, program, editable sources, dataset,
  and complete input identity.
- Immutable `runs/<id>/` publication with frozen inputs/sources, logs,
  normalized `result.json`, optional Judge artifacts, and `manifest.json`
  written last.
- `aq study create/list/inspect`, `aq run execute/list/show`, capability
  descriptors, human/JSON parity, artifacts, and next actions.
- Fast synthetic Judge fixtures covering success, failure evidence, timeout,
  source identity, isolation, immutability, and CLI flows.

### Out of scope

- Invoking an external Researcher or modifying candidate source.
- KEEP/REVERT/CRASH comparison Sessions, source promotion, or Git mutation.
- Freqtrade adapter migration, long OHLCV backtests, and dataset downloading.
- Copying large dataset bytes into every Run; this version pins declared
  dataset identity and leaves content manifests for a later data contract.
- ML training-specific sample budgets or model artifacts beyond ordinary Judge
  output artifacts.
- Studio implementation.

## Acceptance

- [x] A Study cannot place its program, Judge, manifest, or any undeclared
  Project path inside the editable source closure.
- [x] `aq study create/list/inspect` exposes a complete fixed evaluation
  contract to humans and Agents.
- [x] A successful synthetic Judge Run publishes immutable frozen inputs,
  editable source bytes/hashes, metrics, dataset identity, subject identity,
  artifacts, logs, execution timing, Harness version/commit, and terminal
  manifest.
- [x] Judge failure, malformed output, and timeout publish inspectable failed
  RunResults without promoting or deleting evidence.
- [x] `aq run list/show` ignores incomplete directories, rejects tampered
  terminal evidence, and returns stable artifacts/next actions.
- [x] Repeating identical source and Study inputs preserves the same input hash
  while creating separate immutable Runs.
- [x] Documentation links, the complete bounded unit suite, package build,
  legacy profile discovery, and real human/JSON Study/Run flows pass without a
  market-data download or backtest.

## Work

- [x] Audit AutoQuant's legacy program/oracle and INM/Mujica's locked
  evaluation, source closure, Session, Experiment, and immutable evidence
  contracts.
- [x] Define the canonical Study, Judge output, RunResult, and Run manifest
  formats.
- [x] Implement strict Study loading, creation, closure validation, and hashes.
- [x] Implement bounded Judge execution and atomic immutable Run publication.
- [x] Add Study/Run CLI operations and capability descriptors.
- [x] Add focused Core and end-to-end CLI tests.
- [x] Update architecture, public formats, CLI, and subsystem design docs.
- [x] Complete acceptance, fix a dedicated commit, and publish it.

## Findings and decisions

- 2026-07-24 — The first V2 execution lane is deliberately one Python Judge,
  not a per-asset engine registry. Freqtrade will later adapt behind the same
  Study/Run evidence contract.
- 2026-07-24 — The Judge is Project-local because research questions differ,
  but it is outside the Agent-editable closure and its bytes participate in
  input identity.
- 2026-07-24 — Runs record a deterministic `inputHash` separately from their
  unique Run id. Identical inputs can be re-executed without pretending
  nondeterministic runtimes must produce one shared artifact.
- 2026-07-24 — A Judge crash is a completed execution artifact with failed
  status, not an excuse to discard logs. CLI operation failure remains reserved
  for cases where the Harness cannot publish trustworthy evidence.
- 2026-07-24 — Dataset bytes are not implicitly copied. The V1 Study contract
  requires explicit dataset id/version, asset class, universe, and time range;
  a later dataset manifest can add content hashes and storage references.
- 2026-07-24 — The Project now has a first-class `judges/` ownership slot.
  Judge paths must stay there while candidate-editable paths stay in
  `strategies/`, `factors/`, or `models/`; authority is visible in the
  filesystem instead of relying on path-disjointness alone.
- 2026-07-24 — Run loading verifies both terminal file hashes and the strict
  RunResult contract. File integrity is necessary but does not replace semantic
  protocol validation.

## Verification

- `uv run python scripts/check_doc_links.py` — 72 links resolved.
- `uv run python -m unittest discover -s tests -v` — 33 bounded tests passed.
- `uv build` — source distribution and wheel built.
- `uv run prepare.py --list-profiles` and
  `uv run run.py --list-profiles` — crypto and US-equities legacy profiles
  remained discoverable.
- `git diff --check` and `uv run python -m compileall -q autoquant` — passed.
- A disposable real Workspace executed human and JSON CLI flows from
  Workspace/Project creation through Study inspection, successful bounded Run,
  Run listing, and Run verification. The fixed Judge returned `score=2.75`
  with one verified immutable artifact.

## Progress log

- 2026-07-24 — Plan created and indexed after the Workspace/Project/CLI
  foundation was fixed in commit `b1105f4`.
- 2026-07-24 — Added strict Study/Judge/editable/dataset identity, the isolated
  Python Judge lane, immutable manifest-last Runs, and public CLI/schema
  operations.
- 2026-07-24 — Exercised process exit, malformed output, timeout, incomplete
  publication, byte tampering, semantically invalid rehashed RunResult,
  repeated identical inputs, and complete CLI flows.

## Completion

Completed on 2026-07-24. The next independent milestone is the governed
Research Session/Experiment loop that may mutate only the declared editable
closure and can promote a reviewed KEEP without weakening this evidence
contract.
