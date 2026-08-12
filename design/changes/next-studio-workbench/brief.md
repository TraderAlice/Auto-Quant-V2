# Brief: Next Studio workbench integration

## Goal

Merge the approved Next.js factor-research frontend into Auto-Quant-V2 as a
repository-owned, PR-ready workbench that consumes verified Core snapshots and
contains no private plugin implementation.

## Audience

Factor researchers reviewing point-in-time evidence, forming event cohorts,
testing candidate factors, and reproducing research results.

## Existing facts

- Auto-Quant-V2 `main` is tagged `v0.9.31`.
- The current Studio is packaged native HTML/CSS/JavaScript over
  `autoquant-studio-snapshot`.
- No frontend component-library dependency exists.
- Next `16.2.12` and React `19.2.8` are the latest stable npm releases on
  2026-08-02.
- The approved prototype already contains nine research routes and no trading
  surface.

## Constraints

- Preserve Core as the only evidence authority.
- Preserve standalone Python installation and the current packaged Studio.
- Add no component library and no speculative plugin SDK.
- Keep all private plugin calls, credentials, host protocols, and proprietary
  payloads outside the open-source repository.
- Keep demo evidence explicit and impossible to confuse with connected Core
  evidence.
- Preserve the approved DESIGN.md and MOTION.md foundations.

## Acceptance checks

- The Next app builds and all nine routes render.
- The app consumes the existing snapshot only through a read-only server-side
  proxy and validates its identity before presenting it as connected evidence.
- Source mode, validity, freshness, and diagnostics are visible.
- Public-source leakage checks reject private plugin, secret, and live-trading
  integration markers.
- Existing Python Studio behavior and tests remain unchanged.
