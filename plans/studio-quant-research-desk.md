# Studio quant research desk

- Status: `completed`
- Updated: `2026-07-25`
- Related design: [[docs/design/studio-observation-surface]].

## Outcome

AutoQuant Studio reads as a persistent quant research workbench rather than a
static result page. A researcher can see the exact
Workspace → Project → Study → Run context and move through a long evidence
surface without losing that context.

## Scope

- Preserve Studio's read-only, Core-verified evidence boundary.
- Put the current Workspace, Project, focused Study, and immutable Run in the
  persistent project rail.
- Add section navigation derived only from currently visible Studio surfaces.
- Keep the navigation aligned with scroll position and handle the document-end
  case where the final section cannot reach the sticky header.
- Compress the first viewport so the current decision, headline metrics, lane
  selector, and beginning of detailed evidence can coexist.
- Keep the rail out of the compact mobile layout instead of duplicating the
  horizontal Project selector.

## Acceptance

- [x] Workspace, Project, Study, and Run context appear in the desktop rail.
- [x] The research desk lists only visible sections for the selected Project.
- [x] Section buttons use semantic navigation controls and retain keyboard
      focus behavior.
- [x] Smooth navigation lands on the requested surface and the final catalog
      entry remains active at document end.
- [x] The 1280 px viewport has no horizontal overflow or browser errors.
- [x] Studio and CLI tests, JavaScript syntax, diff checks, and documentation
      links pass.

## Verification

- Studio and CLI subset — 20 tests in `37.146s`.
- Studio-only regression — 7 tests in `3.810s`.
- JavaScript syntax and diff whitespace checks — passed.
- Documentation audit — 544 double-links resolved.
- Browser QA — real RL Run context rendered in the rail; five visible section
  controls; document-end navigation selected `Studies & Runs`; zero horizontal
  overflow and zero console warnings/errors.
