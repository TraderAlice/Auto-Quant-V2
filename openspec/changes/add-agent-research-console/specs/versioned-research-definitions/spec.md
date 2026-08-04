## ADDED Requirements

### Requirement: Separate research definition objects
The system SHALL model FactorDefinition, ExperimentDefinition, and StrategyDefinition as separate versioned objects. FactorDefinition SHALL own factor hypothesis/calculation/dependencies/cohort/tests; ExperimentDefinition SHALL own a frozen validation plan; StrategyDefinition SHALL own approved factor composition, rules, Portfolio/ML/RL validation, holdout, costs, risk assumptions, and artifact closure.

#### Scenario: Strategy references a factor
- **GIVEN** an approved FactorDefinition version exists
- **WHEN** a StrategyDefinition uses that factor
- **THEN** it references the exact factor version and does not copy or assume ownership of the factor definition lifecycle

#### Scenario: Factor edit does not edit a strategy
- **GIVEN** a StrategyDefinition references FactorDefinition version 3
- **WHEN** a researcher creates FactorDefinition version 4
- **THEN** the strategy remains bound to version 3 until a separately reviewed StrategyDefinition version changes the reference

### Requirement: Immutable version lineage
Saving changes to an approved definition SHALL create a new draft version. Published versions, semantic diffs, approvals, and evidence references SHALL be immutable and strictly loadable.

#### Scenario: Edit an approved FactorDefinition
- **GIVEN** FactorDefinition version 2 is approved and has immutable Runs
- **WHEN** the user saves a changed calculation
- **THEN** the system creates a new draft version, preserves version 2 unchanged, and leaves all existing Runs bound to version 2

#### Scenario: Tampered definition version
- **GIVEN** published definition bytes no longer match their manifest
- **WHEN** Core loads the version
- **THEN** the version is invalid evidence, dependent run/approval actions are disabled, and no browser fallback reconstructs the missing content

### Requirement: Complete FactorDefinition semantics
A validation-ready FactorDefinition SHALL declare hypothesis, executable calculation or source identity, parameters, output direction/unit, exact data versions and fields, availability/PIT semantics, missing-data policy, universe/cohort, expected horizon, required tests, and failure conditions.

#### Scenario: Missing market clock blocks validation readiness
- **GIVEN** a factor depends on time-sensitive inputs with no verified availability or market-clock semantics
- **WHEN** the user requests validation readiness
- **THEN** the definition remains draft with named unresolved dependencies and cannot produce a credibility-bearing ExperimentDefinition

### Requirement: Frozen ExperimentDefinition
An executable ExperimentDefinition SHALL freeze exact FactorDefinition or StrategyDefinition versions, DataPackage and ResearchSubject identity, outcome/horizon, benchmark, costs, split/purge, robustness, selection adjustment, holdout policy, executor policy, budgets, and stop conditions.

#### Scenario: Run uses exact plan version
- **GIVEN** ExperimentDefinition version 5 is frozen
- **WHEN** an ExperimentRun starts
- **THEN** the Run receipt records version 5 and all frozen input identities, and later plan edits cannot change that Run

#### Scenario: Invalid plan cannot run
- **GIVEN** an ExperimentDefinition lacks a cost policy or required stop condition
- **WHEN** execution is requested
- **THEN** Core rejects the request before compute begins and returns the exact missing plan fields

### Requirement: Semantic diff and confirmation
Definition confirmation SHALL present semantic field changes, affected evidence, newly invalid assumptions, and the new version identity instead of a raw JSON diff alone.

#### Scenario: Data dependency changes
- **GIVEN** a draft changes the input DataPackage version
- **WHEN** confirmation is requested
- **THEN** the review identifies the old/new data identities, evidence that cannot transfer, and the Experiments that require a new Run
