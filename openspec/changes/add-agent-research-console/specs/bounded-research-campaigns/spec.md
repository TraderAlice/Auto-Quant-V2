## ADDED Requirements

### Requirement: Approved Campaign charter
Every autonomous ResearchCampaign SHALL bind one active Session and one approved ExperimentDefinition and SHALL freeze the research question, subject, data, outcome, horizon, benchmark, holdout policy, candidate policy, executor policy, budgets, and stop conditions.

#### Scenario: Start a valid Campaign
- **GIVEN** an active Session and approved ExperimentDefinition with complete budgets and stop rules
- **WHEN** the user approves Campaign start
- **THEN** Core publishes the charter identity before the first candidate begins and every turn references that charter

#### Scenario: Research boundary changes mid-Campaign
- **GIVEN** a Campaign is running
- **WHEN** an Agent proposes a different outcome, horizon, benchmark, data version, or holdout policy
- **THEN** the Campaign pauses and requires a new semantic confirmation rather than silently changing selection authority

### Requirement: Enforced multi-dimensional budgets
Core SHALL enforce positive candidate/turn and wall-time ceilings plus declared CPU, GPU, and cost ceilings when those resources are measurable. Unknown provider spend SHALL remain unknown and SHALL NOT be interpreted as zero.

#### Scenario: Candidate budget exhausted
- **GIVEN** the Campaign has completed its maximum permitted candidates
- **WHEN** no prior stop condition ended the Campaign
- **THEN** the Campaign terminates as budget-exhausted and no new candidate is generated

#### Scenario: Cost telemetry unavailable
- **GIVEN** a provider cannot report authoritative cost
- **WHEN** the Agent requests use under a monetary ceiling
- **THEN** the provider is unavailable for that authorized path unless a separately approved non-monetary resource envelope exists

### Requirement: CPU-first executor routing
The public workflow SHALL use CPU for cheap validation and rejection before optional private GPU/MOSS work unless the approved ExperimentDefinition records why CPU screening is inapplicable. GPU/MOSS execution SHALL require an installed provider declaration and an approved resource/cost envelope.

#### Scenario: Private provider absent
- **GIVEN** no GPU/MOSS provider is installed
- **WHEN** a Campaign reaches a candidate that requests that executor
- **THEN** the candidate reports provider-unavailable and the public CPU workflow remains usable

#### Scenario: CPU screen rejects candidate
- **GIVEN** a candidate fails a fixed cheap leakage, coverage, or validity gate
- **WHEN** executor routing is evaluated
- **THEN** no private compute starts and the candidate row records the exact failed gate

### Requirement: Truthful terminal outcomes
Campaigns SHALL terminate with evidence-ready, budget-exhausted, failed-gate, blocked, stopped-by-user, inconclusive, or failed semantics. They SHALL preserve negative and invalid Experiments and SHALL NOT continue searching until a favorable result appears.

#### Scenario: Valid but inconclusive Campaign
- **GIVEN** all planned candidates complete without adequate support or contradiction
- **WHEN** the declared stop condition is reached
- **THEN** the Campaign terminates as inconclusive with completed receipts and does not request automatic budget expansion

#### Scenario: Protocol failure after valid Experiments
- **GIVEN** earlier Experiments completed and a later external Researcher response is malformed
- **WHEN** Core restores the leader worktree and terminates the Campaign
- **THEN** the Campaign is failed, earlier Experiments remain valid, and the failure is not rewritten as missing evidence

### Requirement: Holdout protection
The Campaign SHALL NOT expose or use frozen holdout outcomes for candidate generation, selection, budget extension, or definition editing. Opening a holdout SHALL be a separately confirmed, auditable, terminal validation action.

#### Scenario: Agent requests holdout during selection
- **GIVEN** candidate selection is still active
- **WHEN** the Agent requests frozen holdout evidence
- **THEN** the Operator Port rejects the request and preserves the holdout seal
