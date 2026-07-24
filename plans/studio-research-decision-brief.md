# Studio research decision brief

## Goal

Make the first AutoQuant Studio viewport answer the questions a quant lead or a
delegating OpenAlice workbench needs before inspecting detailed evidence:

1. What research question is this Project answering?
2. What is the current evidence verdict?
3. Which comparison or acceptance boundary produced that verdict?
4. What should the quant team investigate next?
5. Is this local research or a delegated request with a return contract?

The immutable evidence explorers remain authoritative. The browser only derives
a concise readout from already verified snapshot fields.

## Scope

- Add a project-level decision brief to the existing hero.
- Prefer the focused Study description when a Project has no description.
- For RL Runs, lead with validation value-add versus the best declared simpler
  baseline, not standalone Sharpe.
- Surface opportunity capture and implementation drag in the first metric row.
- Remove the large handoff empty state for local, unbound Projects.
- Compact a one-lane evidence selector instead of reserving a three-lane grid.
- Preserve delegated intake, dossier, Session, and detailed explorer behavior.

## Verification

- Static HTML/CSS/JavaScript contract tests.
- JavaScript syntax check.
- Existing Studio and full Python regression suites.
- Browser verification at desktop and narrow viewports against a real immutable
  RL Run snapshot.

