## ADDED Requirements

### Requirement: One shared Operator Port
The system SHALL expose one closed, provider-neutral Operator Port for the Studio UI, embedded Agent, OpenAlice, Hermes, and Codex. No client SHALL receive a chat-specific mutation path, UI-scraping authority, or arbitrary shell capability.

#### Scenario: Equivalent clients invoke the same operation
- **GIVEN** two clients submit the same authorized research request with distinct actor identities
- **WHEN** Core accepts each request
- **THEN** both requests use the same schema, capability adapter, validation, receipt format, and evidence authority

### Requirement: Strict request envelope
Every Operator request SHALL include a schema version, idempotent request identity, actor, Workspace/Project/session references, closed research intent, exact object/version references, requested authority, budget, confirmation reference when required, and expected prior state.

#### Scenario: Unknown intent is rejected
- **GIVEN** a request names an intent outside the closed Operator capability registry
- **WHEN** the port validates the request
- **THEN** the request fails before any Project mutation and returns a sanitized terminal receipt

#### Scenario: Stale prior state is rejected
- **GIVEN** the referenced definition or session state changed after the client prepared its request
- **WHEN** the client submits the stale expected state
- **THEN** the operation fails closed with current object references and no partial mutation

### Requirement: Idempotent operation receipts
An accepted Operator operation SHALL produce an immutable terminal receipt describing the accepted request hash, actual operations, final status, artifacts, evidence, budget spent, warnings, gates, sanitized errors, next valid actions, and reproduction lineage.

#### Scenario: Identical retry
- **GIVEN** a terminal receipt exists for a request identity and request hash
- **WHEN** the identical request is retried
- **THEN** the prior receipt is returned without repeating the operation or consuming additional budget

#### Scenario: Conflicting retry
- **GIVEN** a terminal receipt exists for a request identity
- **WHEN** different request bytes reuse that identity
- **THEN** the port rejects the conflict and does not mutate research state

#### Scenario: Failure still produces a receipt
- **GIVEN** an accepted operation fails because an input, provider, or execution condition is unavailable
- **WHEN** the operation reaches a terminal state
- **THEN** the port publishes a failed or unavailable receipt with preserved completed evidence and a named recovery action

### Requirement: Confirmation-bound authority
The Operator Port SHALL allow inspection, explanation, comparison, drafting, and execution within an already approved Experiment/Campaign envelope without repeated confirmation. It SHALL require semantic confirmation for new/frozen data or definition versions, changed research boundaries, budget expansion, frozen holdout opening, private paid provider use outside standing authority, artifact decisions, and reproduction start.

#### Scenario: Work continues inside approved budget
- **GIVEN** an ExperimentDefinition and Campaign charter are approved
- **WHEN** the Agent screens another permitted candidate without changing inputs or ceilings
- **THEN** the operation proceeds and publishes a receipt without a new confirmation prompt

#### Scenario: Budget expansion pauses
- **GIVEN** a Campaign has reached its approved candidate ceiling
- **WHEN** the Agent requests additional candidates
- **THEN** the port pauses the operation and returns an awaiting-confirmation receipt containing only the proposed budget diff

### Requirement: Immediate stop
An authorized user stop SHALL take precedence over new automated research, require no additional confirmation, preserve completed evidence, and publish a terminal stopped receipt.

#### Scenario: Stop a running Campaign
- **GIVEN** a Campaign is running and has completed one or more Experiments
- **WHEN** the user issues stop
- **THEN** no new candidate begins, completed Experiments remain valid, mutable progress closes, and the stopped receipt identifies the last completed state
