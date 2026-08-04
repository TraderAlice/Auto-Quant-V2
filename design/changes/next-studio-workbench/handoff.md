# Next Studio workbench handoff

## State

- Status: complete
- Phase: archive
- Change: `next-studio-workbench`
- Branch: `feat/next-studio-workbench`

## Goal

Internalize the approved Next.js Evidence Console in Auto-Quant-V2, consume
the verified read-only Studio snapshot, and keep private plugin integrations
outside the open-source repository.

## Foundations

- [DESIGN.md](../../../DESIGN.md) — ready,
  `966e41398c9b6e0736d2b0318adad0bdb0efcb9a5c3893b47cc9385e7c61d71a`.
- [MOTION.md](../../../MOTION.md) — ready,
  `aa65393e00df714613a2e9d39db47dbf990f299bc7b4cefae47ba2b8f5b443db`.

## Artifacts

- [brief.md](brief.md)
- [directions.md](directions.md)
- [design.md](design.md)
- [motion.md](motion.md)
- [tasks.md](tasks.md)
- [qa.md](qa.md)
- [Repository plan](../../../plans/next-studio-workbench.md)
- [Durable design](../../../docs/design/next-studio-workbench.md)

## Decisions

- Use exact latest stable Next `16.2.12` and React `19.2.8`.
- Add no third-party component library; internalize tokens and components.
- Reuse the existing snapshot and keep the Python package Node-free.
- Add the Next workbench beside the packaged Studio until parity is proven.
- Keep private plugin clients and host protocols outside public source.

## Blockers

None.

## Verification

- Frontend tests, lint, boundary scan, production build, and npm audit pass.
- Connected, unavailable, and explicit demo states pass desktop, tablet, and
  mobile browser checks.
- Documentation links, targeted Python tests, compilation, and package build
  pass.
- The complete Windows Python suite exposes 19 existing Unix-path/CRLF
  assumptions; none reads or imports `studio-web/`.

## Next actions

None for this change.
