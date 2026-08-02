# AutoQuant Studio Web

This is the repository-owned Next.js Evidence Console for factor research. It
uses the existing read-only Core snapshot and contains no plugin, broker,
account, order, or live-trading integration.

## Run locally

In the repository root:

```powershell
uv run aq studio serve . --no-open
```

In `studio-web/`:

```powershell
npm install
npm run dev
```

The web app reads `http://127.0.0.1:8765/api/v1/snapshot` by default. To use a
different loopback port, set `AUTOQUANT_STUDIO_CORE_URL` to an unauthenticated
loopback HTTP origin such as `http://127.0.0.1:8877`.

When Core is unavailable, the app does not silently present fixtures as
verified evidence. Use the visible “使用演示数据” action to enter deterministic
demo mode.

## Boundary

Private hosts and plugins live outside this repository. Public frontend code
accepts only the normalized Studio snapshot and does not forward credentials,
authenticated headers, proprietary payloads, or tool invocations.
