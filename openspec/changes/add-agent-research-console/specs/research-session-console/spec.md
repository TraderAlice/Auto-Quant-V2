## ADDED Requirements

### Requirement: Resumable ResearchLedger
The system SHALL provide one resumable research session ledger with the ordered stages Data, Question, Factor, Experiment, Campaign, Evidence, Approval, and Reproduction. Each stage SHALL expose its state, exact object/version references, receipts, blockers, and next valid actions without calculating research conclusions in the browser.

#### Scenario: Resume an existing research session
- **GIVEN** a session has a frozen data version, approved ExperimentDefinition, terminal Campaign, and pending artifact review
- **WHEN** the user or an Agent client reopens the session
- **THEN** the ledger restores the same stage states and object references and opens the pending review without replaying prior operations

#### Scenario: Partial session remains navigable
- **GIVEN** a session has valid Runs but no connected ReplayBundle
- **WHEN** the Evidence stage is opened
- **THEN** the route, ledger, valid Run evidence, and diagnostics remain visible while Replay shows a named unavailable state

### Requirement: Research-first workbench layout
The Studio SHALL present research sessions through a conversation region, a dominant authoring/evidence canvas, a review/confirmation inspector, and a collapsible research-task tray. The interface SHALL preserve existing deep links to Factor, Strategy, Replay, Results, Jobs, and Audit evidence.

#### Scenario: Desktop research layout
- **GIVEN** a viewport of at least 1440 CSS pixels
- **WHEN** a research session is opened
- **THEN** conversation, central canvas, and review inspector are simultaneously available and the central canvas retains at least 560 CSS pixels

#### Scenario: Medium-width confirmation
- **GIVEN** a viewport between 1024 and 1439 CSS pixels
- **WHEN** a confirmation is required
- **THEN** the inspector opens in a focus-managed Drawer and focus returns to its initiating control on close

#### Scenario: Small-screen review
- **GIVEN** a viewport below 1024 CSS pixels
- **WHEN** the session is opened
- **THEN** the user can read the question, evidence, conclusion, approval history, stop status, and reproduction receipt while complex authoring is explicitly deferred to desktop

### Requirement: Structured research conversation
The conversation surface SHALL distinguish user questions, Agent proposals, user decisions, operation receipts, and evidence conclusions. Every Agent proposal SHALL identify affected objects/versions, evidence inputs, budget impact, semantic changes, and required confirmation.

#### Scenario: Agent proposes a definition change
- **GIVEN** an approved FactorDefinition exists
- **WHEN** the Agent proposes a changed calculation or dependency
- **THEN** the conversation links to a semantic diff for a new draft version and does not imply that the approved version or its Runs changed

### Requirement: Accessible and stable interaction
The console SHALL provide visual-order keyboard navigation, a skip link to the active canvas, visible focus, text alternatives for charts, focus return for overlays, polite status announcements, and reduced-motion behavior. Polling or task updates SHALL NOT steal focus or reorder a focused row.

#### Scenario: Campaign update during keyboard review
- **GIVEN** a keyboard user is inspecting an earlier candidate row
- **WHEN** Campaign progress updates
- **THEN** the row remains focused, status is announced politely, and the table does not automatically reorder

### Requirement: Human-language primary states
Primary UI copy SHALL describe the research meaning of a state. Study, Run, ComputeJob, ReplayBundle, schema, and hash identities SHALL remain available in Technical Details and Audit.

#### Scenario: Missing contract copy
- **GIVEN** a required ReplayBundle contract is unavailable
- **WHEN** the user opens evidence review
- **THEN** primary copy names the missing research evidence and consequence while Technical Details exposes the exact internal contract state
