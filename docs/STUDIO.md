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
- running external Researcher phase and turn budget;
- KEEP, REVERT, and CRASH optimization trajectories;
- recent immutable Runs, Experiments, and Campaigns;
- fixed Study catalog and Project research program;
- category-level diagnostics when evidence cannot be verified.

The browser polls a bounded snapshot every four seconds while visible. Manual
refresh remains available. Running Campaign progress is visibly labelled
mutable; completed evidence is loaded and hash-verified by Core.

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
- no browser interaction changes a Project.

The durable boundary and known gaps are in
[[docs/design/studio-observation-surface]].
