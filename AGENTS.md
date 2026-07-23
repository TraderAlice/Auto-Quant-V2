# AutoQuant V2 contributor guide

AutoQuant V2 is a pre-alpha, AI-native quantitative research workbench. Domain
correctness, reproducible evidence, and a coherent project model take priority
over backward compatibility while V2 is taking shape. Preserve the archived
V0 experiments as historical evidence; do not silently reinterpret them under
new Harness semantics.

Use Python 3.11 and `uv` for repository code and scripts. Keep projects
self-contained: a Workspace owns project discovery and a standardized Harness,
while each Project owns its research question, source inputs, strategies or
models, Runs, and durable artifacts.

## Plan workflow

Read [[PLANS]] before starting non-trivial work. A plan is required when work
crosses packages or public surfaces, changes a domain model, contains meaningful
unknowns, or needs multiple implementation steps. Small, local fixes can
proceed without one.

For planned work:

1. Copy [[plans/_template]] to a stable kebab-case filename and register it in
   the matching status section of [[PLANS]] before implementation.
2. Treat the plan as the live coordination record. Update its checklist,
   findings, decisions, verification evidence, and date as work evolves; do not
   reconstruct them only at the end.
3. Keep durable system truth in the relevant `docs/design/` document. A plan
   may link to design intent but must not become a second source of current
   invariants.
4. Before marking a plan `completed`, audit every acceptance item against
   executable or manual evidence. Move the index entry to the completed section
   and preserve the plan as a concise record.
5. If a plan is replaced, mark it `superseded` and link its replacement. If
   follow-up work remains after completion, create and index a separate plan
   rather than leaving unchecked work in a completed plan.

Plan structure, lifecycle, and its boundary with design documentation are
defined in [[docs/design/documentation-system]].

## Design map

Read the relevant linked document before changing a subsystem:

- Documentation ownership and update protocol:
  [[docs/design/documentation-system]]
- System direction, Workspace/Project ownership, and runtime boundaries:
  [[docs/ARCHITECTURE]]
- Workspace discovery, Project identity, self-contained construction, and path
  confinement: [[docs/design/workspace-project-boundaries]]
- Versioned CLI envelopes, capability discovery, operation effects, artifacts,
  and next actions: [[docs/design/agent-cli-contract]]
- Fixed Study authority, editable/Judge source closures, bounded execution, and
  immutable RunResult evidence: [[docs/design/study-run-evidence]]
- Resumable Agent worktrees, KEEP/REVERT/CRASH Experiments, and guarded source
  promotion: [[docs/design/research-session-loop]]
- Provider-neutral external Researcher turns, budgets, restoration, and
  immutable Campaign evidence: [[docs/design/external-researcher-driver]]
- Canonical Workspace and Project file schemas: [[docs/PROJECT_FORMAT]]
- Human and machine-readable command behavior: [[docs/CLI]]
- Current Freqtrade/OHLCV Harness manifest and profile contract:
  [[docs/harness]]
- Historical research snapshots: [[versions/README]]

Add new active design documents to this map when a subsystem gains its own
invariants. Keep this list as a routing surface, not a historical catalog.

## Required change loop

1. Read [[PLANS]], the active plan when one exists, and the relevant design
   document(s); identify the current invariant being changed.
2. Make the smallest coherent source, schema, fixture, and project changes.
3. Update every affected design document in the same change. If the concept has
   no document, create one under `docs/design/` and add it to the design map.
4. Exercise the affected public CLI or Python boundary with bounded inputs.
5. Run:

   ```bash
   uv run python scripts/check_doc_links.py
   uv run python -m unittest discover -s tests -v
   ```

6. If evaluation semantics, dataset identity, or result hashes changed,
   explicitly record which checked-in fixtures or immutable Runs were
   regenerated and why.
7. If a locked benchmark or Judge contract changed, relock it deliberately and
   prove both an unchanged candidate and a known-improvement path.

Do not launch the autonomous NEVER STOP loop, download large datasets, or run a
long multi-year backtest as routine validation. Use fast deterministic tests
and bounded smoke fixtures unless the active plan explicitly requires a larger
run and records its budget.

Tests prove executable behavior; design documents explain why the behavior
exists and which invariants future changes must preserve. Neither substitutes
for the other.
