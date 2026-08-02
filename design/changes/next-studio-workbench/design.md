# Change design: Next Studio workbench

## Foundations

- Project design foundation: ../../../DESIGN.md
- Design foundation SHA-256: `966e41398c9b6e0736d2b0318adad0bdb0efcb9a5c3893b47cc9385e7c61d71a`
- Project motion foundation: ../../../MOTION.md
- Motion foundation SHA-256: `aa65393e00df714613a2e9d39db47dbf990f299bc7b4cefae47ba2b8f5b443db`
- Runtime: Next.js App Router `16.2.12`, React `19.2.8`, semantic DOM, CSS, and SVG

## Architecture

```text
aq studio serve (read-only, loopback)
    │
    └── GET /api/v1/snapshot
            │
            ▼
studio-web/app/api/studio/snapshot/route.js
    │ fixed path, loopback URL, timeout, identity validation
    ▼
Studio source context
    │ connected | unavailable | demo
    ▼
nine research routes + shared shell
```

The proxy is the only new integration seam. It does not accept arbitrary URLs,
forward headers, execute commands, or expose a plugin registry. The existing
snapshot is reused unchanged.

## Route map

| Route | Surface |
|---|---|
| `/` | Research home and Core connection state |
| `/factors/aq-event-drift` | Factor passport |
| `/replay` | Point-in-time replay |
| `/events` | Cohort comparison |
| `/lab` | Factor laboratory |
| `/results` | Test results |
| `/jobs` | GPU/MOSS research tasks |
| `/data` | Data catalog |
| `/audit` | Audit and reproduction |

## Data contract

- Connected data must have `kind === "autoquant-studio-snapshot"`, a supported
  `schemaVersion`, a generation time, a harness identity, and a projects array.
- Invalid or unreachable Core data produces an explicit unavailable state.
- Demo records remain local and deterministic. Entering demo mode is an
  explicit user action and the shell keeps the `DEMO DATA` label visible.
- Browser code performs presentation-only transformations. It never reads
  Project files or derives research verdicts.

## Component and token contract

- One CSS token file contains primitive, semantic, and component layers.
- Shared React components own panels, metrics, chips, provenance fields,
  controls, empty states, and tables.
- Components reference semantic/component variables; raw palette values remain
  in the primitive layer.
- Status color always has text and accessible state.

## Open-source cut

Public source includes only the snapshot client, public adapter labels,
deterministic demo fixtures, and view logic. Private plugin/MCP clients,
credentials, host schemas, proprietary payloads, and live execution remain
outside the repository. No placeholder plugin framework is added.

## Responsive and accessibility behavior

- Desktop keeps navigation, evidence canvas, and inspector visible.
- Tablet collapses the inspector below the main canvas.
- Mobile uses a staged review flow without horizontal page overflow.
- The app preserves skip navigation, semantic landmarks, visible focus,
  real table headers, textual chart summaries, and reduced-motion behavior.

## Reconciliation

No external visual reference is used. This change directly inherits the
requirements-only DESIGN.md and MOTION.md foundations, so there is no reference
fidelity conflict to reconcile.
