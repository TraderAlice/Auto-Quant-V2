## ADDED Requirements

### Requirement: Evidence closure before approval
The system SHALL present the exact factor or strategy version, data, ExperimentDefinition, Runs, deterministic assessment, costs, holdout state, limitations, and unresolved diagnostics before artifact approval.

#### Scenario: Incomplete evidence closure
- **GIVEN** a StrategyDefinition references a required holdout that has not been assessed
- **WHEN** the user opens artifact review
- **THEN** the review identifies the missing holdout assessment and disables approval without hiding other valid evidence

#### Scenario: Negative evidence remains visible
- **GIVEN** a Campaign contains contradicted, invalid, or inconclusive candidates
- **WHEN** an artifact review is opened for the selected version
- **THEN** those terminal outcomes remain in the evidence closure and are not removed by selecting a preferred candidate

### Requirement: Exact-version artifact decision
Approval or rejection SHALL bind one exact FactorDefinition or StrategyDefinition version and its evidence manifest. Approval SHALL freeze a new immutable research artifact and SHALL NOT mutate the definition verdict or any Run.

#### Scenario: Approve an exact factor version
- **GIVEN** FactorDefinition version 4 has a complete evidence closure
- **WHEN** the user approves version 4
- **THEN** the system publishes an immutable artifact referencing version 4 and its exact evidence while leaving other drafts unchanged

#### Scenario: Definition changes during review
- **GIVEN** an approval review was prepared for StrategyDefinition version 2
- **WHEN** version 3 is created before confirmation
- **THEN** the stale review cannot approve version 3 or silently transfer its decision; the user must review the new semantic diff

### Requirement: Approval choices preserve research state
The review SHALL support approve, reject/return for revision, and retain as research draft. Rejection or revision SHALL preserve all completed evidence and SHALL NOT delete the reviewed version.

#### Scenario: Return artifact for revision
- **GIVEN** evidence is valid but the user rejects the proposed artifact
- **WHEN** the user selects return for revision
- **THEN** the reviewed version and evidence remain immutable and a new draft may be created with the rejection receipt linked

### Requirement: Independent reproduction receipt
Reproduction SHALL run from an approved artifact manifest and exact available environment, create a new immutable receipt, preserve the original artifact, and classify the result as exact match, within declared tolerance, drift, unavailable dependency, or failure.

#### Scenario: Exact reproduction
- **GIVEN** all referenced inputs and the approved CPU environment are available
- **WHEN** reproduction completes with matching artifacts and metrics
- **THEN** the receipt records exact match and links both original and reproduced evidence

#### Scenario: Reproduction drift
- **GIVEN** reproduction completes but one metric or artifact hash differs beyond declared tolerance
- **WHEN** the comparison is published
- **THEN** the receipt records drift, names the differing evidence, and leaves the original approval unchanged

#### Scenario: Private executor unavailable
- **GIVEN** the approved artifact references a private executor that is not installed
- **WHEN** reproduction is requested
- **THEN** the system publishes an unavailable receipt and does not substitute CPU unless the artifact explicitly permits an equivalent CPU environment

### Requirement: Audit continuity
Every approval, rejection, reproduction, stop, failure, and unavailable outcome SHALL be reachable from the ResearchLedger and Audit through stable object and receipt references.

#### Scenario: Audit a reproduced artifact
- **GIVEN** an approved artifact has multiple reproduction attempts
- **WHEN** the user opens Audit
- **THEN** each attempt appears as a separate immutable receipt with its environment, inputs, result, drift, and lineage
