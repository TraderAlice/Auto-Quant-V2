# AutoQuant Studio

AutoQuant Studio is the local, read-only human observation surface for the
same verified research state exposed by Core and `aq`.

## Open a Workspace

```bash
aq studio serve ./quant-workspace
```

The server binds to `127.0.0.1:8765`, opens the default browser, and runs until
interrupted. Use a different local port or suppress browser opening with:

```bash
aq studio serve ./quant-workspace --port 8877 --no-open
```

A direct Project path is also valid. A Workspace can be restricted to one
Project with `--project ID`.

The default bind is intentionally loopback-only. V1 has no authentication.
Binding `--host` to a non-loopback address is an explicit operator decision.

## What the page shows

The first viewport prioritizes:

- every discovered Project and its verification state;
- active Sessions and current leader values;
- delegated caller questions, assets, direction, horizon, and Brief identity;
- running external Researcher phase and turn budget;
- KEEP, REVERT, and CRASH optimization trajectories;
- recent immutable Runs, Experiments, Campaigns, and Research Reports;
- factor Run summaries for validation one/five-bar IC, HAC strength, tertile
  spread, weakest chronological fold, maximum fixed-style overlap, test audit
  IC, and rank turnover;
- portfolio Run summaries for held-out IC, net Sharpe, signal-state change,
  hysteresis transition reduction, maximum asset return/risk contribution,
  attribution reconciliation, turnover, and cost stress;
- RL Run summaries for validation/test audit Sharpe, seed/fold dispersion,
  simple-baseline advantage, failure rate, and fold × seed coverage;
- Session selection split, candidate trial count, visible-test role, and
  external-holdout requirement;
- request → evidence → report readiness and exact copyable headless commands;
- fixed Study catalog and Project research program;
- category-level diagnostics when evidence cannot be verified.

The browser polls a bounded snapshot every four seconds while visible. Manual
refresh remains available. Running Campaign progress is visibly labelled
mutable; completed evidence is loaded and hash-verified by Core.

Run cards are diagnostic projections, not replacements for full evidence.
Factor cards show strength, decay, monotonic spread, stability, style overlap,
and test audit evidence beside the headline score. Portfolio cards show signal
churn, hysteresis effect, contribution concentration, and reconciliation.
RL cards show implementation, dispersion, failure, and baseline comparison.
Exact nested metrics, decision ledgers, daily slices, models, training
histories, actions, and artifacts remain in the verified Run.

The handoff cards and Inspector distinguish caller-supplied OpenAlice context
from authenticated provenance. Copy buttons only write an exact Core-generated
CLI string to the local clipboard. They do not invoke the command or mutate the
Project.

## Machine-readable snapshot

Agents and scripts can inspect the same normalized observation without
starting a server:

```bash
aq studio snapshot ./quant-workspace --json
aq schema studio-snapshot --json
aq schema campaign-progress --json
```

The HTTP projection exposes only:

- `GET /`
- `GET /assets/studio.css`
- `GET /assets/studio.js`
- `GET /api/v1/health`
- `GET /api/v1/snapshot`

There is no arbitrary file, shell, command, mutation, Experiment, or promotion
endpoint. Browser responses use a restrictive Content Security Policy and do
not enable cross-origin access.

## Authority

Studio is not an evaluator. It calls the same Core loaders used by CLI:

- invalid completed evidence is omitted and diagnosed rather than displayed as
  fact;
- Session authority issues remain visible;
- mutable progress cannot create a metric or verdict;
- the browser cannot author analysis or publish a Research Report;
- no browser interaction changes a Project.

The durable boundary and known gaps are in
[[docs/design/studio-observation-surface]].
