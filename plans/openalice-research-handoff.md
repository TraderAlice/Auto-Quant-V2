# Establish OpenAlice research delegation and report handoff

- Status: `completed`
- Updated: `2026-07-24`
- Related design: [[docs/design/quant-research-lifecycle]],
  [[docs/design/research-session-loop]], and
  [[docs/design/studio-observation-surface]].

## Outcome

An OpenAlice or local caller can give AutoQuant a strict research request,
start a Study-bound Session whose immutable derived brief pins that request and
the fixed evaluation authority, let an Agent perform bounded research, and
publish a machine-readable plus human-readable report whose claims point to
verified Session evidence. Studio exposes the same handoff state without
becoming a writer or evaluator.

## Context

AutoQuant can already create Projects, execute fixed Studies, iterate through
Sessions and Campaigns, and observe evidence in Studio. It cannot yet preserve
why another workbench asked for the research or return a stable report. The
missing boundary encourages request context to live in chat and conclusions to
be copied without exact evidence identity.

OpenAlice remains the authority for its own Workspace, Session, signature, and
Inbox delivery provenance. AutoQuant may content-bind caller-supplied origin
context but must not claim that environment variables or request JSON
authenticate an OpenAlice identity.

## Scope

### In scope

- Strict V1 research-request and report-analysis schemas.
- An optional research request at Session start and an exact derived brief that
  binds the request, Project, Study, and authority locks.
- Researcher Campaign input that includes the verified request and brief.
- Immutable Session-local report publication, verification, listing, and
  inspection.
- Evidence references that resolve only to verified Runs, Experiments,
  Campaigns, and their declared artifacts.
- CLI capabilities, schemas, JSON envelopes, artifacts, next actions, docs,
  tests, and Studio read-model/UI parity.
- An explicit OpenAlice handoff recipe for publishing the generated Markdown
  report through OpenAlice's authoritative Inbox boundary.

### Out of scope

- Calling OpenAlice tools or mutating its Inbox from AutoQuant.
- Trusting caller-supplied OpenAlice Workspace or Session identifiers.
- Live orders, broker accounts, or trading authorization.
- The portfolio and RL Judges, which have separately indexed plans.
- Free-form report generation inside Core; the Agent supplies strict analysis
  while Core binds evidence and renders deterministic Markdown.

## Acceptance

- [x] A valid request can start a Session and produces deterministic
      `request.json` and `brief.json` content whose hashes are validated on
      every Session load.
- [x] Existing Sessions without a delegated request remain readable and
      executable.
- [x] External Researcher turns receive the verified request/brief, and a
      changed request, brief, Study lock, or Session pointer is rejected.
- [x] `aq report publish/list/show` accepts strict Agent-authored analysis,
      resolves every evidence reference, atomically publishes a fully hashed
      immutable report, and rejects tampering or fabricated evidence ids.
- [x] Report JSON and generated Markdown identify the request, Study, leader,
      metrics, limitations, authority boundary, Harness, dataset, and exact
      evidence snapshot without claiming live-trading authority.
- [x] Studio snapshot and browser presentation show delegated intent and report
      readiness from the verified Core read model, while mutation remains an
      exact CLI command.
- [x] CLI capabilities, schemas, canonical docs, focused tests, full bounded
      tests, and link checks all agree.

## Work

- [x] Establish the lasting OpenAlice delegation, quantitative evidence,
      portfolio, RL, and HCI direction in one indexed design document.
- [x] Implement request/brief parsing, derivation, Session binding, validation,
      and Researcher projection.
- [x] Implement report draft parsing, evidence resolution, immutable
      publication, verification, CLI surfaces, and schemas.
- [x] Extend Studio snapshot and browser UI with request/report state and exact
      copyable headless commands.
- [x] Update canonical formats, CLI, architecture, tests, and examples.
- [x] Run the complete acceptance audit, bounded validation, commit, and push.

## Findings and decisions

- 2026-07-24 — A research Brief belongs to a governed Session rather than
  becoming a free-floating mutable Project document. It binds one external
  question to one fixed Study and its baseline authority.
- 2026-07-24 — Report analysis is Agent-authored structured input. Core verifies
  its evidence references and deterministically publishes JSON plus Markdown;
  it does not invent conclusions.
- 2026-07-24 — AutoQuant records OpenAlice origin fields as caller-supplied
  context. OpenAlice alone stamps authoritative Session and Inbox provenance.
- 2026-07-24 — Portfolio construction and RL remain full follow-up lanes, not
  hidden extras inside the handoff implementation.

## Verification

- `uv run python -m unittest discover -s tests -v` — 69 bounded tests passed,
  including request/Brief tampering, fabricated evidence ids, later Session
  evolution, and a fully rehashed forged-metric Report.
- `uv run python scripts/check_doc_links.py` — 153 repository links resolved.
- `uv run python -m compileall -q autoquant tests` — passed.
- `node --check autoquant/studio_assets/studio.js` — passed.
- `git diff --check` — passed.
- `uv build --out-dir /tmp/autoquant-handoff-build-20260724-2` — source and
  wheel built; inspection confirmed Brief, Report, Studio Core, and all browser
  assets are packaged.
- The CLI smoke starts a delegated Session from strict request JSON, publishes
  a Report from strict analysis, and verifies it through `report list/show`.
- No checked-in historical Run was regenerated. All acceptance evidence used
  temporary bounded synthetic Projects.

## Progress log

- 2026-07-24 — Plan created and the system-level research lifecycle documented.
- 2026-07-24 — Shipped Request/Brief derivation, Researcher projection,
  evidence-bound Reports, CLI/schema discovery, and Studio handoff cards with
  copy-only Core commands.

## Completion

AutoQuant now has one complete collaboration boundary for OpenAlice or local
callers: strict intent enters a governed Session, fixed evidence remains in
charge, and immutable JSON/Markdown decision support comes back out. AutoQuant
does not authenticate OpenAlice origin or gain trading authority. The
separately indexed portfolio and RL plans remain the next substantive
quantitative research lanes.
