# Factor-component attribution

Status: Implemented.

Related: [[docs/design/causal-multi-interval-factor-inputs]],
[[docs/design/factor-diagnostics]],
[[docs/design/factor-evidence-explorer]],
[[docs/design/research-selection-integrity]],
[[docs/design/portfolio-construction-lab]],
[[docs/design/rl-factor-policy-lab]], and
[[docs/design/program-research-dossiers]].

## Purpose

A final factor Series is necessary for ranking assets, but it is not enough for
research iteration. When an Agent combines 1h momentum, completed 4h reversal,
12h activity, and daily trend, the next useful questions are:

1. Which declared component has validation predictive evidence?
2. Which component mostly repeats another declared component?
3. Does a component retain information after its closest declared peer is
   removed?
4. Does removing it help or hurt one fixed, target-independent diagnostic
   blend?

AutoQuant answers those questions only when the candidate explicitly declares
components. Core never parses Python source or guesses column provenance.

## Candidate contract

The only required API remains:

```python
def compute_factor(frame: pandas.DataFrame) -> pandas.Series:
    ...
```

A candidate may additionally export:

```python
FACTOR_COMPONENTS = {
    "momentum_1h_10": {
        "label": "10-hour momentum",
        "intervals": ["base"],
        "hypothesis": "Recent relative strength persists over the next bar.",
    },
}

def compute_factor_components(frame: pandas.DataFrame) -> pandas.DataFrame:
    ...
```

The DataFrame contains one to twelve candidate-declared numeric Series on the
same index as `frame`. Its ordered columns must be unique safe identifiers and
must be entries in `FACTOR_COMPONENTS`. Metadata may describe more components
than one dataset materializes so one source file can remain compatible with a
daily V1 Project and a multi-interval V2 Project. Evidence records only the
columns actually returned for the Run.

Each materialized component declares:

- a concise human label;
- the supplied intervals it claims to use (`base` resolves to the current
  decision interval);
- one falsifiable hypothesis sentence.

The declaration is research metadata, not proof of runtime column access.
Candidate source and metadata are already content-locked in the Run subject.

If the function and metadata are both absent, the Run is a valid legacy
candidate and component evidence is unavailable. Supplying only one of them is
an API error.

## Fixed validation

Preflight uses at most two assets and 256 base rows. The complete Judge uses
the locked Study population. Both require:

- no input mutation;
- an exactly aligned DataFrame;
- numeric values, with warm-up `NaN` allowed and infinity forbidden;
- at least one finite observation per materialized component;
- identical columns and values for repeated fixed input;
- prefix stability when future rows are withheld;
- safe, bounded names and metadata;
- declared intervals drawn from the Run's supplied interval surface.

The complete Judge repeats prefix causality for every component. Component
failure is candidate failure because downstream evidence would otherwise
misdescribe the code.

## Fixed evidence

All predictive targets and split masks are the same purged 1/5/10-base-bar
contract used by the final factor.

For every materialized component, the Judge records:

- coverage;
- train, validation, and test-audit rank IC summaries at 1/5/10 bars;
- same-date cross-sectional rank association with the final factor;
- the closest other component selected only by maximum absolute train rank
  association;
- rank-residual IC after that fixed nearest peer is removed;
- validation and test-audit effect of removing the component from a fixed
  equal-weight cross-sectional percentile-rank blend.

Every component pair also records mean and mean-absolute same-date rank
association by split. Ties are deterministic by component name. Sparse cells
retain observations and null statistics.

The fixed blend is a diagnostic reference:

```text
each component
→ same-date cross-sectional percentile rank
→ equal mean across available components
```

Leave-one-out compares this all-component reference with the same reference
excluding one component. It is never labeled as an ablation of
`compute_factor`, because arbitrary candidate composition is not known.

## Diagnosis and selection integrity

Validation may determine a bounded research-prioritization diagnosis such as:

- preserve a component with positive raw, residual, and blend evidence;
- diversify a component that predicts but is highly redundant;
- simplify a component whose removal improves the fixed blend;
- gather more evidence for sparse or unstable components.

This diagnosis has no acceptance or trading authority. The only Factor
promotion objective remains final-factor validation one-bar mean rank IC.
Test evidence is visible audit only. The number of materialized components and
pairwise comparisons is disclosed because a larger declared surface increases
researcher degrees of freedom; Project-family candidate trial adjustment
remains separately authoritative.

## Evidence flow

```text
candidate.py declaration + component DataFrame
→ fixed preflight contract
→ fixed Factor Judge
→ RunResult metrics + factor-components.json
→ hash verification and semantic reconciliation
→ Factor Explorer / Studio
→ frozen Factor Report
→ frozen Project Dossier for OpenAlice
```

The artifact is bounded structured evidence, not executable source. Historical
Runs without it project `available: false`; no evidence is invented.

## Downstream boundary

Portfolio and governed RL continue to consume only the final factor Series from
the content-locked dependency. Component evidence can guide the next Factor
experiment or a human handoff, but it cannot:

- create positions;
- alter the request-bound mandate;
- bypass covariance, execution, cost, or capacity rules;
- create dynamic RL experts or actions;
- promote a candidate;
- publish to OpenAlice Inbox.

If a future design wants components to become governed RL sleeves, it must
predeclare that action authority independently and compare against the same
fixed baselines. This contract does not grant it implicitly.

## Bounds

- materialized components: 1–12;
- metadata entries: 1–24;
- interval claims per component: 1–6;
- component artifact: 8 MiB;
- universe: inherited Factor bound of 256 assets;
- horizons: fixed 1, 5, and 10 base bars.

## Invariants

1. Component disclosure is explicit and optional; source inference is absent.
2. Every materialized component is deterministic, aligned, immutable, numeric,
   and prefix causal.
3. Component targets, purges, splits, and final-factor population are fixed by
   the Judge.
4. Nearest-peer selection is train-only and target-free.
5. Fixed-blend ablation is not candidate-factor attribution.
6. Validation diagnoses; test only audits.
7. Final-factor `validation_mean_ic` remains the sole promotion objective.
8. CLI, Studio, Report, and Dossier consume one verified bounded Core object.
9. Portfolio, RL, OpenAlice, Broker, order, and account authority remain
   unchanged.

## Known limits

- Metadata is a candidate claim, not instrumented proof of column access.
- Pairwise residualization does not solve multivariate collinearity.
- A component can be economically meaningful even when standalone
  cross-sectional IC is weak.
- Equal-rank leave-one-out describes one fixed reference blend, not every
  nonlinear or regime-dependent composition.
- Small universes can make daily cross-sectional correlations coarse.
