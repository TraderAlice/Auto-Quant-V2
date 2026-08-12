# Next Studio workbench QA

## Control plane

- Design foundation: ready, SHA-256
  `966e41398c9b6e0736d2b0318adad0bdb0efcb9a5c3893b47cc9385e7c61d71a`.
- Motion foundation: ready, static posture, SHA-256
  `aa65393e00df714613a2e9d39db47dbf990f299bc7b4cefae47ba2b8f5b443db`.
- Pipeline schema: `design-pipeline.state.v2`.
- Registry: `design-pipeline.phases.v2`.
- Dependency self-check: ready; no required capability missing.
- `next-dev-loop`: not applicable because its hard floor is Next `16.3+`
  while npm latest stable is `16.2.12`; no canary dependency will be introduced.

## Verification

### Frontend

- `npm test`: 4/4 tests pass, including point-in-time visibility, cohort
  comparison, loopback-only Core access, and snapshot identity.
- `npm run check:boundary`: passes; public application code contains no
  authenticated header, API key, private MCP tool name, or unapproved
  environment variable.
- `npm run lint`: passes with ESLint `9.39.5`, the latest release compatible
  with all `eslint-config-next@16.2.12` plugins.
- `npm run build`: passes with Next.js `16.2.12` and React `19.2.8`; all nine
  research routes and the read-only snapshot proxy are emitted.
- `npm audit --omit=dev --registry=https://registry.npmjs.org`: zero known
  vulnerabilities after overriding Next's existing transitive PostCSS and
  Sharp dependencies to patched releases `8.5.18` and `0.35.0`.

### Browser

- Connected desktop home: Core `0.9.31`, real Project/Study/counts and four
  Core diagnostics render with no console error or horizontal overflow.
- Every desktop route renders its expected research heading with no horizontal
  overflow.
- Every non-home route renders at `375x812` with no horizontal overflow.
- Connected home and gated-to-demo replay render at `768x1024` with no
  horizontal overflow.
- Core-only routes gate demo records until the explicit demo action is used.
- Replay keyboard stepping changes the observed time; first Tab focuses the
  skip link with a visible outline.
- Evidence: `qa-connected-desktop.png`, `qa-demo-replay-desktop.png`, and
  `qa-demo-replay-mobile.png`, and `qa-demo-replay-tablet.png`.

### Repository

- `uv run python -m compileall -q autoquant tests`: passes.
- `uv run python scripts/check_doc_links.py`: 1,558 links resolve.
- `uv run python -m unittest tests.test_documentation -v`: 3/3 pass.
- `uv build`: succeeds; the Python wheel contains Core only and no Next,
  generated, credential, or private-plugin files.
- Full local suite: 455 tests executed; 436 pass. The 19 Windows failures are
  pre-existing platform assumptions: external Researcher tests execute the
  absolute Unix path `/bin/sh`, one build test expects `.venv/bin/python`, and
  CRLF checkout changes immutable sample bytes and their derived manifests.
  No failure reads or imports `studio-web/`; targeted checks cover every
  changed Python and packaging boundary in this change.

### Security boundary

- Only `AUTOQUANT_STUDIO_CORE_URL` is accepted, and only as an unauthenticated
  loopback HTTP origin.
- The same-origin proxy exposes one fixed GET to `/api/v1/snapshot`, forwards
  no caller URL or credential, uses `no-store`, and fails closed.
- Private plugin clients, host schemas, provider payloads, broker/account/order
  adapters, and live-trading code are absent.
