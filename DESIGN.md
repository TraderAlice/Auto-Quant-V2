---
name: AutoQuant Studio Evidence Workbench
schema: design-pipeline.design-foundation.v0.1
sourceMode: requirements-only
activeChange: next-studio-workbench
---

## Product Context

AutoQuant Studio is a dense, repeated-use research environment for factor researchers. Its central promise is point-in-time truth: a researcher can see what information was actually available at a historical moment, form a factor hypothesis from that evidence, and test it without silently changing the evidence underneath.

The product is self-hosted and open source. It supports A-share announcements, crypto events and financial news through adapters. It has no live trading, broker account or order-routing surface.

## Overview

The design posture is an evidence console, not a marketing dashboard and not a retail trading terminal. The primary screen lets a user scan a shared time axis, select evidence, compare cohorts and move into a test without losing context.

Priorities:

1. Make time, provenance and uncertainty legible before visual appeal.
2. Make repeated research work fast: dense, stable, keyboard-friendly and unsurprising.
3. Keep data visualizations inspectable. A chart never hides the source, time boundary or computation behind it.
4. Use visual distinction to identify state and evidence class, not to claim confidence that the data does not have.

## Colors

| Token | Value | Use |
|---|---|---|
| ink-950 | #0B1118 | application canvas |
| ink-900 | #111A24 | persistent navigation and inspector |
| ink-800 | #182434 | raised data surfaces and selected rows |
| line-700 | #2D3A49 | grid lines, separators and chart axes |
| paper-100 | #E7EDF3 | primary text |
| paper-300 | #AFBDCB | secondary text and annotations |
| signal-cyan | #52C7D9 | confirmed factor signal and selected time cursor |
| event-amber | #F1B35C | event marker and pending evidence |
| success-mint | #6BCB9A | completed research job and passing data health |
| danger-coral | #EC7C73 | failed job, invalid input and blocking data issue |
| muted-slate | #728198 | unavailable, restricted or partial state |

Color never carries meaning alone. Every trusted-state color has an icon, visible label and programmatic name.

## Typography

- UI and tabular data use an installed system sans-serif stack with tabular numerals.
- Metric values use tabular figures at 14-18 px; dense tables use 12-13 px with a minimum 1.35 line height.
- Screen titles are functional labels, not editorial hero copy.
- Long evidence text is constrained to a readable measure in the inspector, never compressed into chart tooltips.

## Layout

- Desktop research workbench: 12-column fluid grid with a persistent 240 px navigation rail, a 320-400 px inspector and a flexible central canvas.
- The central canvas owns the shared time axis. K-line, factor signal, market snapshot and event tracks align to it.
- At 1024 px and below, the inspector becomes a focus-managed drawer and event filters become a collapsible panel. Charts retain horizontal pan/zoom rather than shrinking labels below legibility.
- At 768 px and below, research actions use a staged single-column flow: context, chart, selected evidence, action drawer. No critical state is hover-only.
- Dense data uses rows, dividers and hierarchy; avoid nested decorative cards.

## Components

| Component | Contract |
|---|---|
| Trust strip | Fixed, top-of-workspace summary of replay time, bundle coverage, source/permission state and known gaps. |
| Replay transport | Time cursor, step, jump-to-event, pause and optional playback. Always shows timezone and visible-at boundary. |
| Event marker | Encodes adapter, evidence state and group membership; opens a full inspector, never a content-only tooltip. |
| Evidence inspector | Shows source, all relevant timestamps, license state, revision, hash and local/open-source access policy. |
| Cohort tray | Holds one or two explicitly named event groups; comparison cannot start until both have a saved membership rule. |
| Factor passport header | Stable identity, version, latest test status, linked research frame and direct links to data/compute/audit. |
| Test configuration panel | Shows active universe, lag, cost, rebalance, coverage and visibility policy before a run is created. |
| Result provenance card | Always accompanies test metrics with input snapshots, engine version, job ID and output hash. |
| Compute job row | State, resource budget, start/end, retries, logs, outputs and link back to research object. |
| Evidence status chip | Known, partial, delayed, revised, restricted or missing; includes an explanatory detail on focus/click. |

## Do's and Don'ts

Do:

- Put the replay timestamp and data coverage in the primary reading path.
- Preserve a user's research context across every jump between replay, factor, test, task and audit.
- Use calm visual hierarchy and durable table layouts for repeated work.
- Make empty, delayed, restricted and failed states useful: say what is absent, why and what can be done next.
- Offer keyboard navigation for time stepping, opening the inspector and adding evidence to a cohort.

Don't:

- Do not use candlesticks, red/green returns or neon movement to imply a trading product.
- Do not use a generic card grid or dashboard hero as the main research surface.
- Do not hide data versions, timing assumptions or restricted content behind an advanced menu.
- Do not invent confidence scores when coverage or provenance is unknown.
- Do not autoplay a historical narrative or use decorative data animation.

## Source Decisions

| Source | Adopted | Rejected | Reason |
|---|---|---|---|
| Approved replay-first design | Shared time axis, right-side evidence inspector, factor passport entry and ResearchFrame/ReplayBundle concepts | Treating replay as the only required product page | The product requires the full research loop, not a single viewer. |
| Approved AutoQuant scope | Unified research kernel, complete research pages and explicit non-trading boundary | Real trading surfaces | AutoQuant owns factor research from evidence to test result. |
| Requirements-only design synthesis | Quiet, dense evidence-console posture with AutoQuant-owned tokens and domain components | Borrowing another product's visual identity or live-site style | Public Mantine primitives may supply accessible component mechanics, but they must remain themed by AutoQuant and may not define the product identity. |
