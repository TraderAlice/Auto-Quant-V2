---
name: package-autoquant-ohlcv
description: Audit provider-acquired OHLCV, choose the narrowest truthful AutoQuant V1-V5 package contract, create a confined provenance-honest dataset manifest, and complete strict Project intake and validation. Use after any market-data provider acquisition or when repairing an external dataset package before AutoQuant research.
---

# Package AutoQuant OHLCV

Convert acquired evidence into a strict AutoQuant input without promoting
provider claims into authenticated facts.

## Inspect before packaging

1. Read [package-contracts.md](references/package-contracts.md).
2. Keep the manifest at the common ancestor of its relative asset files.
3. Run:

```bash
aq-python scripts/audit_ohlcv_package.py \
  --package /absolute/path/dataset-package.json \
  --write-audit /absolute/path/package-audit.json
```

4. Resolve every error. Do not forward-fill, change adjustment, align away
   observations, or rename venues merely to satisfy intake.
5. Inspect the exact public schema when creating or repairing a manifest:

```bash
aq schema ohlcv-dataset-package --json
```

When two independent routes cover the same assets, compare them before
selection:

```bash
aq-python scripts/compare_ohlcv_packages.py \
  --left /absolute/path/source-a/dataset-package.json \
  --right /absolute/path/source-b/dataset-package.json \
  --write-audit /absolute/path/source-comparison.json
```

Require the same price-adjustment claim for a numerical comparison. Inspect
date coverage, latest common observation, price differences, volume ratios,
and each provider's raw audit before choosing a route. Agreement does not turn
two unofficial sources into venue authority.

When adjustment claims differ, compare coverage only and preserve the
incompatibility explicitly:

```bash
aq-python scripts/compare_ohlcv_packages.py \
  --left /absolute/path/raw/dataset-package.json \
  --right /absolute/path/adjusted/dataset-package.json \
  --mode coverage-only \
  --write-audit /absolute/path/coverage-comparison.json
```

Coverage-only reports dates, row counts, overlap, freshness, and zero-volume
counts. It deliberately emits no price or volume comparison.

## Choose the contract

- V1: aligned completed daily session panel.
- V2: continuous UTC 1h base with deterministic completed higher intervals.
- V3: configurable continuous or XNYS regular-session base interval.
- V4: observed-only ragged daily Factor input.
- V5: observed-only intraday mixed-class Factor input.

Choose the narrowest contract that describes the acquired bytes. A provider
claiming an interval or calendar does not prove the corresponding AutoQuant
contract.

## Preserve provenance

- Use the original known provider retrieval timestamp or JSON `null`.
- Keep provider, source URI, terms claim, market, venue, currency, adjustment,
  volume, and timestamp semantics explicit.
- Use per-asset classes on every asset or omit them from every asset.
- Keep paths POSIX-relative descendants; reject absolute paths, `..`, and
  symlinks.
- Preserve acquisition and package audits beside staging bytes.

## Intake

Only after the English research brief and strict Research Request agree:

For a new research body, create its Project-root authority:

```bash
aq project intake <workspace> <project-id> \
  --request /absolute/path/research-request.json \
  --dataset /absolute/path/dataset-package.json \
  --json
aq validate <workspace> --project <project-id> --json
aq orient <workspace> --project <project-id> --json
```

For a distinct fixed question that belongs inside an existing Project, keep a
complete task-local package and create one Study-owned authority in the same
operation:

```bash
aq study create <workspace> <study-id> \
  --project <project-id> \
  --subject-kind research \
  --judge <project-relative-judge.py> \
  --judge-path '<project-relative-judge-closure>' \
  --no-editable \
  --metric <primary-metric> \
  --request /absolute/path/research-request.json \
  --dataset /absolute/path/dataset-package.json \
  --json
aq validate <workspace> --project <project-id> --json
```

Add fixed method files with repeatable `--dependency`. Add prior immutable
evidence only with an exact `--upstream-run` plus repeatable
`--upstream-artifact`. Do not pass manual dataset identity flags with external
`--request/--dataset`, impersonate a specialized template, inspect installed
AutoQuant source, or write a private materialization script. This generic route
accepts aligned V1-V3 packages; V4/V5 remain Factor-only.

Return the Project id, content-locked snapshot identity, source hashes,
coverage, unresolved provider limitations, and no trading authority. A valid
package proves structural admission, not provider correctness.
