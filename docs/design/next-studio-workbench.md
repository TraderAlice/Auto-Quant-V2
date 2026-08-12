# Next Studio workbench

Status: implemented and verified for pull request.

Related: [[docs/design/studio-observation-surface]], [[docs/ARCHITECTURE]], and
[[plans/next-studio-workbench]].

## Scope

This document owns the maintainable Next.js presentation that sits above the
existing verified Studio snapshot. It does not change Core evidence authority,
the snapshot schema, `aq studio serve`, or the Python package boundary.

The workbench is a factor-research product. It covers factor passports,
point-in-time replay, event cohorts, factor experiments, test evidence,
research jobs, data authority, and reproduction. It has no account, broker,
order, exchange-execution, or live-trading surface.

## Runtime boundary

```text
AutoQuant Core loaders
→ versioned autoquant-studio-snapshot
→ loopback-only aq studio serve
→ server-side same-origin Next proxy
→ repository-owned React views
```

The Next application does not read Project files, run Core commands, recompute
metrics, or infer verdicts. It may select, filter, compare, and render values
already present in the snapshot. The proxy accepts one configured loopback
Core origin and exposes only the fixed snapshot response.

The existing packaged Studio remains the default `aq studio serve`
presentation until the Next surface reaches behavioral parity. This avoids a
Node.js runtime dependency in the Python wheel and keeps the migration
reversible.

## Source modes

The workbench has two honest source states:

- `connected`: a verified `autoquant-studio-snapshot` was loaded from Core;
- `demo`: deterministic repository fixtures are being shown for product
  exploration.

The source state is visible in persistent chrome. A failed, invalid, stale, or
unavailable Core response cannot silently fall back to verified-looking demo
data. The error remains visible and the user may deliberately enter demo mode.

## Internal design system

The workbench adds no third-party component library. Its design system is
repository-owned and follows three token layers:

1. primitives define raw color, spacing, type, radius, and duration values;
2. semantic tokens assign research meaning such as evidence, warning, valid,
   unavailable, canvas, and surface;
3. component tokens define the shared shell, panels, controls, tables, chips,
   inspector, and chart surfaces.

Components consume component or semantic tokens rather than raw colors. This
makes the Evidence Console identity portable without coupling the repository
to a vendor library.

## Open-source and private extension boundary

Open-source code may contain:

- the versioned Core snapshot contract;
- public adapter labels and normalized provenance fields;
- deterministic demo records;
- a loopback Core URL configuration;
- UI state and pure research comparisons.

Open-source code must not contain:

- plugin or MCP invocation implementations;
- private host tool names, schemas, routing tables, or authentication flows;
- tokens, cookies, credentials, authenticated headers, or private endpoints;
- raw proprietary provider payloads or licensed content;
- broker, account, order, or live-execution adapters.

Private hosts integrate outside this repository. They may materialize verified
Core evidence or supply the same normalized snapshot through the public
loopback boundary. The workbench does not need a generic plugin SDK or a
host-specific code path.

## Invariants

1. Core remains the only authority for verified research evidence.
2. Connected and demo evidence are always visibly distinct.
3. The frontend performs no Project write, command execution, verdict, or
   trading action.
4. Private plugin implementations remain outside the repository.
5. The Python package stays operable without Node.js.
6. Next.js and React versions are pinned exactly for reproducible builds.
7. Accessibility and reduced-motion behavior remain part of the component
   contract.
8. Vulnerable transitive build dependencies are overridden only to their
   published patched versions and remain covered by the npm audit gate.

## Migration gate

Replacing the packaged Studio requires a separate plan after route and
behavioral parity, wheel/package strategy, offline asset policy, and the full
Python regression suite are proven. This change intentionally leaves that gate
closed.
