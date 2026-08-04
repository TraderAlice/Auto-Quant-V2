import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  RESEARCH_STAGE_ORDER,
  buildFactorDefinitionDraft,
  buildExperimentDefinitionDraft,
  buildOperatorRequest,
  buildArtifactReviewDraft,
  buildReproductionRequestDraft,
  inspectResearchLedger,
  researchSessions,
  validateOperatorRequest,
} from "../lib/research-console.js";

function fixture() {
  const stages = RESEARCH_STAGE_ORDER.map((id) => ({
    id,
    label: id,
    state: id === "evidence" ? "partial" : "available",
    objects: [],
    blockers: [],
    nextValidActions: [],
    ...(id === "evidence" ? { widgets: { runs: { state: "available" }, replay: { state: "unavailable", reason: "ReplayBundle contract is not connected." } } } : {}),
  }));
  return {
    source: { rootDir: "C:/workspace" },
    projects: [{
      id: "factor-lab",
      rootDir: "C:/workspace/projects/factor-lab",
      sessions: [{
        session: { id: "session-1", status: "active", studyId: "quality" },
        researchLedger: { schemaVersion: 1, kind: "autoquant-research-ledger", sessionId: "session-1", sessionStatus: "active", authority: { valid: true }, stages, receipts: [] },
        researchLedgerDiagnostics: [],
        experiments: [], campaigns: [], progress: [], reports: [],
      }],
    }],
  };
}

test("research-console keeps the frozen ledger order and isolates missing replay", () => {
  const snapshot = fixture();
  const projection = inspectResearchLedger(snapshot.projects[0].sessions[0]);
  assert.equal(projection.state, "available");
  assert.deepEqual(projection.ledger.stages.map((stage) => stage.id), RESEARCH_STAGE_ORDER);
  assert.equal(projection.ledger.stages[5].state, "partial");
  assert.equal(projection.ledger.stages[5].widgets.replay.state, "unavailable");
  assert.equal(projection.ledger.stages[4].state, "available");
  const invalid = structuredClone(snapshot.projects[0].sessions[0]);
  invalid.researchLedger.stages.reverse();
  assert.equal(inspectResearchLedger(invalid).state, "invalid");
});

test("research-console resolves only connected Project Sessions without demo fallback", () => {
  const snapshot = fixture();
  assert.deepEqual(researchSessions(snapshot).map((item) => [item.project.id, item.bundle.session.id]), [["factor-lab", "session-1"]]);
  assert.deepEqual(researchSessions({ projects: [{ id: "empty", sessions: [] }] }), []);
});

test("research-console creates separate structured confirmation requests", () => {
  const snapshot = fixture();
  const project = snapshot.projects[0];
  const bundle = project.sessions[0];
  const proposed = buildOperatorRequest({ snapshot, project, bundle, intent: "definition.factor.create", input: { definition: {} }, requestId: "proposal-1" });
  assert.equal(proposed.authority.mode, "confirmation-bound");
  assert.equal(proposed.confirmationRef, null);
  const decision = buildOperatorRequest({ snapshot, project, bundle, intent: "confirmation.accept", input: { executionActor: proposed.actor }, confirmationRef: proposed.requestId, requestId: "decision-1", actor: { id: "local-user", kind: "user" } });
  assert.equal(decision.authority.mode, "approved-envelope");
  const confirmed = buildOperatorRequest({ snapshot, project, bundle, intent: proposed.intent, input: proposed.input, confirmationRef: decision.requestId, requestId: "confirmed-1" });
  assert.equal(confirmed.confirmationRef, "decision-1");
  assert.notEqual(confirmed.requestId, proposed.requestId);
  const inspect = buildOperatorRequest({ snapshot, project, bundle, intent: "research.inspect", requestId: "inspect-1" });
  assert.equal(inspect.authority.mode, "read-only");
  const stop = buildOperatorRequest({ snapshot, project, bundle, intent: "campaign.stop", objectRefs: [{ kind: "campaign", id: "campaign-1", version: null }], requestId: "stop-1" });
  assert.equal(stop.authority.mode, "approved-envelope");
});

test("research-console browser boundary rejects commands credentials paths and unknown intents", () => {
  const snapshot = fixture();
  const project = snapshot.projects[0];
  const bundle = project.sessions[0];
  assert.throws(() => buildOperatorRequest({ snapshot, project, bundle, intent: "chat.execute" }), /Unknown/);
  const valid = buildOperatorRequest({ snapshot, project, bundle, intent: "research.inspect", requestId: "inspect-safe" });
  assert.throws(() => validateOperatorRequest({ ...valid, input: { command: "whoami" } }, snapshot), /cannot carry/);
  assert.throws(() => validateOperatorRequest({ ...valid, input: { path: ".." } }, snapshot), /cannot carry/);
  assert.throws(() => validateOperatorRequest({ ...valid, input: { parameters: { brokerPassword: "not-real" } } }, snapshot), /cannot carry/);
  assert.throws(() => validateOperatorRequest({ ...valid, input: { authHeader: "not-real" } }, snapshot), /unsupported fields/);
  assert.throws(() => validateOperatorRequest({ ...valid, input: { privateKey: "not-real" } }, snapshot), /unsupported fields/);
  assert.throws(() => validateOperatorRequest({ ...valid, actor: { id: "browser", kind: "user" } }, snapshot), /studio actor/i);
});

// --- Component contract tests (v49) ---

test("ArtifactReviewEditor and ReproductionRequestEditor are exported and both builders are used", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.match(component, /export function ArtifactReviewEditor/);
  assert.match(component, /export function ReproductionRequestEditor/);
  assert.match(component, /buildArtifactReviewDraft/);
  assert.match(component, /buildReproductionRequestDraft/);
});

test("component has no rawJson, Core contract object, mutationInput(, StrategyDefinition or whole-contract fallback", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.doesNotMatch(component, /rawJson/);
  assert.doesNotMatch(component, /Core contract object/);
  assert.doesNotMatch(component, /mutationInput\(/);
  assert.doesNotMatch(component, /StrategyDefinition/);
  assert.doesNotMatch(component, /definition\.strategy\.create/);
  assert.doesNotMatch(component, /reviewMutation\(\)/);
});

test("reproduction editor has no outcome, environment, or differences input and mentions unavailable", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.match(component, /unavailable/);
  // ReproductionRequestEditor should NOT have inputs named outcome, environment, differences
  const reproStart = component.indexOf("function ReproductionRequestEditor");
  const reproEnd = component.indexOf("function ReviewInspector", reproStart);
  const reproSection = component.slice(reproStart, reproEnd);
  assert.doesNotMatch(reproSection, /\boutcome\b/);
  assert.doesNotMatch(reproSection, /\benvironment\b/);
  assert.doesNotMatch(reproSection, /\bdifferences\b/);
});

test("artifact editor has evidenceManifest Textarea and role=alert", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.match(component, /evidenceManifest/);
  assert.match(component, /role="alert"/);
  // The evidenceManifest field should be a Textarea
  const artStart = component.indexOf("function ArtifactReviewEditor");
  const artEnd = component.indexOf("function ReproductionRequestEditor", artStart);
  const artSection = component.slice(artStart, artEnd);
  assert.match(artSection, /Textarea.*evidenceManifest/);
});

test("ReviewInspector wires direct domain objects: onReview={(review) => onMutation({ review })} for artifact and onReview={(reproduction) => onMutation({ reproduction })} for reproduction", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // ArtifactReviewEditor calls onReview(review) directly (line 624)
  assert.match(component, /onReview\(review\);/);
  // ReproductionRequestEditor calls onReview(reproduction) directly (line 689)
  assert.match(component, /onReview\(reproduction\);/);
  // ReviewInspector wires: onReview={(review) => onMutation({ review })}
  assert.match(component, /onReview=\{\(review\) => onMutation\(\{ review \}\)\}/);
  // ReviewInspector wires: onReview={(reproduction) => onMutation({ reproduction })}
  assert.match(component, /onReview=\{\(reproduction\) => onMutation\(\{ reproduction \}\)\}/);
  // Confirm structured wire
  assert.match(component, /mutationIntent === "artifact\.decide"/);
  assert.match(component, /mutationIntent === "reproduction\.start"/);
});
test("research-console routes components adapter and CSS expose the approved responsive accessible shell", async () => {
  const [indexPage, detailPage, component, route, css, shell, packageJson] = await Promise.all([
    readFile(new URL("../app/research/page.jsx", import.meta.url), "utf8"),
    readFile(new URL("../app/research/[sessionId]/page.jsx", import.meta.url), "utf8"),
    readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8"),
    readFile(new URL("../app/api/studio/operator/route.js", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../components/studio-shell.jsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);
  assert.match(indexPage, /researchSessions\(source\.snapshot\)/);
  assert.match(indexPage, /DEMO ISOLATED/);
  assert.match(detailPage, /selectResearchSession\(source\.snapshot, sessionId\)/);
  assert.match(detailPage, /<ResearchConsole/);
  assert.match(component, /ResearchLedger stages/);
  assert.match(component, /OperationReceiptCard/);
  assert.match(component, /role="status" aria-live="polite">\{status\}/);
  assert.match(component, /Drawer/);
  assert.match(component, /reviewOnly/);
  assert.match(component, /returnFocus/);
  assert.match(component, /id: stoppableCampaign\.campaignId/);
  assert.match(component, /disabled=\{busy\}>Confirm exact request/);
  assert.match(component, /Save draft/);
  assert.match(component, /Return for revision/);
  assert.match(component, /stopCampaignRef/);
  assert.match(component, /stopDisabled/);
  assert.match(css, /grid-template-columns: minmax\(0, 1fr\)/);
  assert.match(css, /grid-template-columns: minmax\(230px, 300px\) minmax\(560px, 1fr\)/);
  assert.match(css, /grid-template-columns: minmax\(340px, 380px\) minmax\(560px, 1fr\) minmax\(320px, 380px\)/);
  assert.match(css, /@media \(min-width: 1024px\)/);
  assert.match(css, /@media \(min-width: 1440px\)/);
  assert.match(component, /window\.addEventListener\("resize", updateViewport\)/);
  assert.match(component, /viewportWidth >= 1024/);
  assert.match(component, /viewportWidth >= 1440/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(shell, /pathname\.startsWith\("\/research\/"\)/);
  assert.match(route, /valid Content-Length/);
  assert.match(route, /execFileAsync\(/);
  assert.match(route, /AbortSignal\.timeout\(15_000\)/);
  assert.match(route, /\["run", "aq", "operator", "invoke"/);
  assert.doesNotMatch(route, /shell\s*:/);
  assert.doesNotMatch(route, /request\.json\(\)/);
  const dependencies = JSON.parse(packageJson).dependencies;
  assert.deepEqual(Object.keys(dependencies).sort(), ["@mantine/core", "@mantine/hooks", "lightweight-charts", "next", "react", "react-dom"].sort());
  assert.doesNotMatch(`${indexPage}\n${detailPage}\n${component}`, /live trading|brokerage account|place order/i);
});

// --- Factor / Experiment draft builders ---

const FACTOR_EDITABLE = Object.freeze({
  hypothesis: "H₀: no drift",
  calculation: "sharpe",
  parameters: { window: 21 },
  output: { type: "scalar" },
  dataDependencies: [],
  missingDataPolicy: "drop",
  cohort: "SPX",
  expectedHorizon: "90d",
  requiredTests: ["stationarity"],
  failureGates: [{ metric: "pValue", threshold: 0.05 }],
});

const EXPERIMENT_EDITABLE = Object.freeze({
  definitionRef: { id: "factor-alpha", version: 1 },
  data: { source: "hdf5" },
  subject: "SPX equities",
  outcome: "sharpe drift",
  benchmark: "sp500-tr",
  costPolicy: { maxCost: 0 },
  splitPolicy: "time-series",
  robustness: "bootstrap",
  selectionAdjustment: "none",
  holdoutPolicy: "last-20pct",
  executorPolicy: { kind: "docker" },
  budget: { candidateLimit: 100 },
  stopConditions: [{ metric: "wallTime", value: 3600 }],
});

test("buildFactorDefinitionDraft produces exact Core-shaped v1 draft with canonical ISO timestamp and no parentVersion at top-level", () => {
  const identity = { id: "factor-alpha", version: 1, createdAt: "2026-04-01T12:00:00.000Z", parentVersion: null };
  const draft = buildFactorDefinitionDraft({ identity, editable: structuredClone(FACTOR_EDITABLE) });

  const topKeys = Object.keys(draft).sort();
  assert.deepEqual(topKeys, [
    "calculation", "cohort", "createdAt", "dataDependencies", "expectedHorizon",
    "failureGates", "hypothesis", "id", "kind", "lineage", "missingDataPolicy",
    "output", "parameters", "requiredTests", "schemaVersion", "status", "version",
  ]);
  assert.equal(draft.schemaVersion, 1);
  assert.equal(draft.kind, "autoquant-factor-definition");
  assert.equal(draft.status, "draft");
  assert.equal(draft.id, "factor-alpha");
  assert.equal(draft.version, 1);
  assert.equal(draft.createdAt, "2026-04-01T12:00:00.000Z");
  assert.deepEqual(draft.lineage, { parentVersion: null });
  assert.ok(!("parentVersion" in draft), "parentVersion must not be a top-level key");
  assert.equal(draft.hypothesis, "H₀: no drift");
  assert.equal(draft.requiredTests[0], "stationarity");
});

test("buildExperimentDefinitionDraft produces exact Core-shaped v2 draft with canonical ISO timestamp and lineage", () => {
  const identity = { id: "exp-beta", version: 2, createdAt: "2026-04-02T08:30:00.000Z", parentVersion: 1 };
  const draft = buildExperimentDefinitionDraft({ identity, editable: structuredClone(EXPERIMENT_EDITABLE) });

  const topKeys = Object.keys(draft).sort();
  assert.deepEqual(topKeys, [
    "benchmark", "budget", "costPolicy", "createdAt", "data", "definitionRef",
    "executorPolicy", "holdoutPolicy", "id", "kind", "lineage", "outcome",
    "robustness", "schemaVersion", "selectionAdjustment", "splitPolicy",
    "status", "stopConditions", "subject", "version",
  ]);
  assert.equal(draft.schemaVersion, 1);
  assert.equal(draft.kind, "autoquant-experiment-definition");
  assert.equal(draft.status, "draft");
  assert.equal(draft.id, "exp-beta");
  assert.equal(draft.version, 2);
  assert.equal(draft.createdAt, "2026-04-02T08:30:00.000Z");
  assert.deepEqual(draft.lineage, { parentVersion: 1 });
  assert.ok(!("parentVersion" in draft), "parentVersion must not be a top-level key");
  assert.equal(draft.subject, "SPX equities");
  assert.equal(draft.stopConditions.length, 1);
});

test("draft builder deep-clones editable so source mutation does not affect returned draft", () => {
  const mutable = structuredClone(FACTOR_EDITABLE);
  const identity = { id: "f", version: 1, createdAt: "2026-06-01T00:00:00.000Z", parentVersion: null };
  const draft = buildFactorDefinitionDraft({ identity, editable: mutable });
  mutable.hypothesis = "ALTERED";
  mutable.requiredTests.push("extra-test");
  assert.equal(draft.hypothesis, "H₀: no drift");
  assert.equal(draft.requiredTests.length, 1);
});

test("draft builder rejects missing identity keys, extra identity keys, and extra editable keys", () => {
  const identity = { id: "f", version: 1, createdAt: "2026-06-01T00:00:00.000Z", parentVersion: null };
  // missing key
  assert.throws(() => buildFactorDefinitionDraft({ identity: { id: "f", version: 1, createdAt: "2026-06-01T00:00:00.000Z" }, editable: FACTOR_EDITABLE }), /unsupported fields/);
  // extra key on identity
  assert.throws(() => buildFactorDefinitionDraft({ identity: { ...identity, label: "extra" }, editable: FACTOR_EDITABLE }), /unsupported fields/);
  // extra key on editable
  const bad = { ...FACTOR_EDITABLE, color: "red" };
  assert.throws(() => buildFactorDefinitionDraft({ identity, editable: bad }), /unsupported fields/);
});

test("draft builder rejects bad timestamp, invalid version, and invalid parentVersion", () => {
  // non-ISO timestamp
  assert.throws(() => buildFactorDefinitionDraft({ identity: { id: "f", version: 1, createdAt: "04/01/2026", parentVersion: null }, editable: FACTOR_EDITABLE }), /not a valid ISO timestamp/);
  // v0
  assert.throws(() => buildFactorDefinitionDraft({ identity: { id: "f", version: 0, createdAt: "2026-06-01T00:00:00.000Z", parentVersion: null }, editable: FACTOR_EDITABLE }), /version is invalid/);
  // parentVersion null but version != 1
  assert.throws(() => buildFactorDefinitionDraft({ identity: { id: "f", version: 2, createdAt: "2026-06-01T00:00:00.000Z", parentVersion: null }, editable: FACTOR_EDITABLE }), /parentVersion must be null only for version 1/);
  // parentVersion >= version
  assert.throws(() => buildExperimentDefinitionDraft({ identity: { id: "e", version: 2, createdAt: "2026-06-01T00:00:00.000Z", parentVersion: 3 }, editable: EXPERIMENT_EDITABLE }), /parentVersion is invalid/);
  // parentVersion not integer
  assert.throws(() => buildExperimentDefinitionDraft({ identity: { id: "e", version: 2, createdAt: "2026-06-01T00:00:00.000Z", parentVersion: 1.5 }, editable: EXPERIMENT_EDITABLE }), /parentVersion is invalid/);
});

// --- Campaign start/pause/resume ---

const HEX64 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

function campaignFixture() {
  const base = fixture();
  return { snapshot: base, project: base.projects[0], bundle: base.projects[0].sessions[0] };
}

test("campaign.start accepts exact experimentDefinitionRef with positive budget and object hashes, no normalization", () => {
  const { snapshot, project, bundle } = campaignFixture();
  const req = buildOperatorRequest({
    snapshot, project, bundle, intent: "campaign.start",
    input: { experimentDefinitionRef: { id: "exp-1", version: 3, contentHash: HEX64 } },
    budget: { candidateLimit: 5, wallTimeSeconds: 0, cpuSeconds: 0, gpuSeconds: 0, cost: null },
    objectHashes: { "ExpDef-Ab12": "a".repeat(64) },
    requestId: "start-1",
  });
  assert.equal(req.intent, "campaign.start");
  assert.equal(req.input.experimentDefinitionRef.id, "exp-1");
  assert.equal(req.input.experimentDefinitionRef.version, 3);
  assert.equal(req.input.experimentDefinitionRef.contentHash, HEX64);
  assert.equal(req.budget.candidateLimit, 5);
  // no normalization: mixed-case key preserved
  assert.ok("ExpDef-Ab12" in req.expectedState.objectHashes);
  assert.equal(req.expectedState.objectHashes["ExpDef-Ab12"], "a".repeat(64));
  assert.equal(req.authority.mode, "approved-envelope");
});

test("campaign.start rejects malformed contentHash (not 64 hex)", () => {
  const { snapshot, project, bundle } = campaignFixture();
  assert.throws(() => buildOperatorRequest({
    snapshot, project, bundle, intent: "campaign.start",
    input: { experimentDefinitionRef: { id: "exp-1", version: 1, contentHash: "short" } },
    budget: { candidateLimit: 1, wallTimeSeconds: 0, cpuSeconds: 0, gpuSeconds: 0, cost: null },
    requestId: "bad-hash",
  }), /contentHash is invalid/);
});

test("campaign.start rejects zero candidateLimit", () => {
  const { snapshot, project, bundle } = campaignFixture();
  assert.throws(() => buildOperatorRequest({
    snapshot, project, bundle, intent: "campaign.start",
    input: { experimentDefinitionRef: { id: "exp-1", version: 1, contentHash: HEX64 } },
    budget: { candidateLimit: 0, wallTimeSeconds: 0, cpuSeconds: 0, gpuSeconds: 0, cost: null },
    requestId: "zero-cand",
  }), /candidateLimit must be positive/);
});

test("campaign.start rejects extra cost key in experimentDefinitionRef", () => {
  const { snapshot, project, bundle } = campaignFixture();
  assert.throws(() => buildOperatorRequest({
    snapshot, project, bundle, intent: "campaign.start",
    input: { experimentDefinitionRef: { id: "exp-1", version: 1, contentHash: HEX64, cost: 999 } },
    budget: { candidateLimit: 1, wallTimeSeconds: 0, cpuSeconds: 0, gpuSeconds: 0, cost: null },
    requestId: "extra-cost",
  }), /unsupported fields/);
});

test("campaign.start rejects objectRefs", () => {
  const { snapshot, project, bundle } = campaignFixture();
  assert.throws(() => buildOperatorRequest({
    snapshot, project, bundle, intent: "campaign.start",
    input: { experimentDefinitionRef: { id: "exp-1", version: 1, contentHash: HEX64 } },
    objectRefs: [{ kind: "campaign", id: "c1", version: null }],
    budget: { candidateLimit: 1, wallTimeSeconds: 0, cpuSeconds: 0, gpuSeconds: 0, cost: null },
    requestId: "refs-start",
  }), /does not accept object references/);
});

test("campaign.pause and campaign.resume accept one unversioned campaign ref", () => {
  const { snapshot, project, bundle } = campaignFixture();
  for (const intent of ["campaign.pause", "campaign.resume"]) {
    const req = buildOperatorRequest({
      snapshot, project, bundle, intent,
      objectRefs: [{ kind: "campaign", id: "campaign-x", version: null }],
      requestId: `${intent}-1`,
    });
    assert.equal(req.intent, intent);
    assert.equal(req.objectRefs.length, 1);
    assert.equal(req.objectRefs[0].kind, "campaign");
    assert.equal(req.objectRefs[0].id, "campaign-x");
    assert.equal(req.objectRefs[0].version, null);
    assert.equal(req.authority.mode, "approved-envelope");
  }
});

test("campaign.pause/re resume rejects wrong kind, missing refs, and versioned ref", () => {
  const { snapshot, project, bundle } = campaignFixture();
  for (const intent of ["campaign.pause", "campaign.resume"]) {
    // wrong kind
    assert.throws(() => buildOperatorRequest({
      snapshot, project, bundle, intent,
      objectRefs: [{ kind: "experiment-definition", id: "exp-1", version: null }],
      requestId: "wrong-kind",
    }), /must be a campaign/);
    // zero refs
    assert.throws(() => buildOperatorRequest({
      snapshot, project, bundle, intent,
      objectRefs: [],
      requestId: "zero-refs",
    }), /requires exactly one/);
    // versioned ref
    assert.throws(() => buildOperatorRequest({
      snapshot, project, bundle, intent,
      objectRefs: [{ kind: "campaign", id: "c1", version: 3 }],
      requestId: "versioned-ref",
    }), /version must be null/);
    // missing id
    assert.throws(() => buildOperatorRequest({
      snapshot, project, bundle, intent,
      objectRefs: [{ kind: "campaign", id: "", version: null }],
      requestId: "no-id",
    }), /Object reference is invalid/);
  }
});

// --- ArtifactReview / ReproductionRequest builders ---

function validEvidenceManifest() {
  return {
    data: { source: "hdf5" },
    experimentDefinition: { kind: "tracked" },
    runs: [{ id: "run-1", status: "complete" }],
    assessment: { verdict: "pass" },
    costs: { total: 0.05 },
    holdout: { enabled: true },
    limitations: [],
    diagnostics: [],
    artifactHashes: { "model.pkl": HEX64 },
    metrics: { sharpe: 1.2 },
    environment: { os: "linux" },
    cpuEquivalentAllowed: false,
  };
}

function validArtifactReviewFields() {
  return {
    id: "review-01",
    decision: "approve",
    actor: { id: "alice", kind: "researcher" },
    definitionRef: { kind: "factor", id: "factor-alpha", version: 1 },
    definitionHash: HEX64,
    evidenceManifest: validEvidenceManifest(),
    reason: "All gates passed.",
  };
}

test("buildArtifactReviewDraft produces exact output and deep-clones input", () => {
  const fields = validArtifactReviewFields();
  const review = buildArtifactReviewDraft(fields);

  assert.equal(review.schemaVersion, 1);
  assert.equal(review.kind, "autoquant-artifact-review");
  assert.equal(review.id, "review-01");
  assert.equal(review.decision, "approve");
  assert.deepEqual(review.actor, { id: "alice", kind: "researcher" });
  assert.deepEqual(review.definitionRef, { kind: "factor", id: "factor-alpha", version: 1 });
  assert.equal(review.definitionHash, HEX64);
  assert.equal(review.reason, "All gates passed.");
  assert.ok(review.evidenceManifest.runs.length === 1);

  // deep-clone: mutate source, review unchanged
  fields.reason = "MUTATED";
  fields.evidenceManifest.runs.push({ id: "run-2", status: "running" });
  assert.equal(review.reason, "All gates passed.");
  assert.equal(review.evidenceManifest.runs.length, 1);
});

test("buildArtifactReviewDraft accepts all three decisions and rejects unknown", () => {
  for (const decision of ["approve", "return-for-revision", "retain-as-draft"]) {
    const fields = { ...validArtifactReviewFields(), decision };
    const review = buildArtifactReviewDraft(fields);
    assert.equal(review.decision, decision);
  }
  assert.throws(() => buildArtifactReviewDraft({ ...validArtifactReviewFields(), decision: "reject" }), /decision is invalid/);
  assert.throws(() => buildArtifactReviewDraft({ ...validArtifactReviewFields(), decision: "accept" }), /decision is invalid/);
  assert.throws(() => buildArtifactReviewDraft({ ...validArtifactReviewFields(), decision: "" }), /decision is invalid/);
});

test("buildArtifactReviewDraft rejects unknown fields", () => {
  assert.throws(() => buildArtifactReviewDraft({ ...validArtifactReviewFields(), extraField: true }), /unsupported fields/);
});

test("buildArtifactReviewDraft rejects missing fields", () => {
  const fields = validArtifactReviewFields();
  delete fields.evidenceManifest;
  assert.throws(() => buildArtifactReviewDraft(fields), /unsupported fields/);
});

test("buildArtifactReviewDraft rejects bad definitionHash (not 64 hex)", () => {
  const fields = { ...validArtifactReviewFields(), definitionHash: "short" };
  assert.throws(() => buildArtifactReviewDraft(fields), /definitionHash is invalid/);
  const fieldsUpper = { ...validArtifactReviewFields(), definitionHash: HEX64.toUpperCase() };
  assert.throws(() => buildArtifactReviewDraft(fieldsUpper), /definitionHash is invalid/);
});

test("buildArtifactReviewDraft rejects empty runs", () => {
  const fields = validArtifactReviewFields();
  fields.evidenceManifest.runs = [];
  assert.throws(() => buildArtifactReviewDraft(fields), /runs must be a non-empty array/);
});

test("buildArtifactReviewDraft rejects non-finite metrics", () => {
  const fields = validArtifactReviewFields();
  fields.evidenceManifest.metrics = { sharpe: NaN };
  assert.throws(() => buildArtifactReviewDraft(fields), /metrics value is not finite/);
  fields.evidenceManifest.metrics = { sharpe: Infinity };
  assert.throws(() => buildArtifactReviewDraft(fields), /metrics value is not finite/);
});

test("buildArtifactReviewDraft rejects empty environment", () => {
  const fields = validArtifactReviewFields();
  fields.evidenceManifest.environment = {};
  assert.throws(() => buildArtifactReviewDraft(fields), /environment must be a non-empty object/);
});

test("buildArtifactReviewDraft rejects bad definitionRef kind", () => {
  const fields = { ...validArtifactReviewFields(), definitionRef: { kind: "experiment", id: "e1", version: 1 } };
  assert.throws(() => buildArtifactReviewDraft(fields), /definitionRef kind is invalid/);
});

test("buildArtifactReviewDraft rejects invalid actor", () => {
  assert.throws(() => buildArtifactReviewDraft({ ...validArtifactReviewFields(), actor: { id: "", kind: "researcher" } }), /actor id is invalid/);
  assert.throws(() => buildArtifactReviewDraft({ ...validArtifactReviewFields(), actor: { id: "alice" } }), /unsupported fields/);
});

test("buildArtifactReviewDraft rejects bad artifactHashes", () => {
  const fields = validArtifactReviewFields();
  fields.evidenceManifest.artifactHashes = { bad: "not-hex" };
  assert.throws(() => buildArtifactReviewDraft(fields), /artifactHashes value is not 64-hex/);
});

test("buildArtifactReviewDraft rejects invalid id", () => {
  const fields = { ...validArtifactReviewFields(), id: "" };
  assert.throws(() => buildArtifactReviewDraft(fields), /id is invalid/);
});

test("buildArtifactReviewDraft rejects empty reason", () => {
  const fields = { ...validArtifactReviewFields(), reason: "   " };
  assert.throws(() => buildArtifactReviewDraft(fields), /reason must be a non-empty string/);
});

// --- ReproductionRequest ---

test("buildReproductionRequestDraft produces exact output with only schemaVersion, kind, id, approvalId", () => {
  const fields = { id: "repr-01", approvalId: "approval-abc" };
  const req = buildReproductionRequestDraft(fields);

  assert.equal(req.schemaVersion, 1);
  assert.equal(req.kind, "autoquant-reproduction-request");
  assert.equal(req.id, "repr-01");
  assert.equal(req.approvalId, "approval-abc");
  const keys = Object.keys(req).sort();
  assert.deepEqual(keys, ["approvalId", "id", "kind", "schemaVersion"]);
});

test("buildReproductionRequestDraft deep-clones input", () => {
  const fields = { id: "repr-01", approvalId: "approval-abc" };
  const req = buildReproductionRequestDraft(fields);
  fields.id = "MUTATED";
  assert.equal(req.id, "repr-01");
});

test("buildReproductionRequestDraft rejects extra fields like outcome, environment, differences", () => {
  for (const extra of ["outcome", "environment", "differences"]) {
    const fields = { id: "repr-01", approvalId: "approval-abc", [extra]: "some-value" };
    assert.throws(() => buildReproductionRequestDraft(fields), /unsupported fields/);
  }
});

test("buildReproductionRequestDraft rejects bad id", () => {
  assert.throws(() => buildReproductionRequestDraft({ id: "", approvalId: "approval-abc" }), /id is invalid/);
  assert.throws(() => buildReproductionRequestDraft({ id: "!!bad!!", approvalId: "approval-abc" }), /id is invalid/);
});

test("buildReproductionRequestDraft rejects bad approvalId", () => {
  assert.throws(() => buildReproductionRequestDraft({ id: "repr-01", approvalId: "" }), /approvalId is invalid/);
  assert.throws(() => buildReproductionRequestDraft({ id: "repr-01", approvalId: "!!bad!!" }), /approvalId is invalid/);
});

// --- Confirmation Inspector & SemanticDiff boundary (v64) ---

test("ConfirmationInspector has exactly one primary Confirm exact request and two distinct secondary actions", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.match(component, /Confirm exact request/);
  // Exactly one Confirm exact request
  const confirmMatches = component.match(/Confirm exact request/g);
  assert.equal(confirmMatches.length, 1, "Only one primary Confirm exact request button may exist");
  // Two distinct, named, non-confirm secondary actions
  assert.match(component, /Save draft/);
  assert.match(component, /Return for revision/);
  // Neither is "Return without mutation"
  assert.doesNotMatch(component, /Return without mutation/);
});

test("SemanticDiff uses pending receipt when confirmation is active and returns unavailable when empty", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.match(component, /pendingReceipt/);
  assert.match(component, /Current pending receipt has no semantic diff evidence from Core/);
  // Does not fall back to all receipts when pendingReceipt is set
  const semFn = component.match(/function SemanticDiff[\s\S]*?^}/m)?.[0] || "";
  assert.match(semFn, /pendingReceipt \? \[pendingReceipt\] : receipts/);
});

test("stopCampaign uses single-flight ref guard with state-driven stopDisabled shared between Inspector and task tray", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.match(component, /stopCampaignRef/);
  // stopCampaign reads the ref + stoppableCampaign before proceeding
  assert.match(component, /if \(stopCampaignRef\.current \|\| !stoppableCampaign\) return/);
  // stopDisabled is driven by state (stopBusy), never reads ref during render
  assert.match(component, /stopDisabled/);
  assert.doesNotMatch(component, /Boolean\(stopCampaignRef\.current\)/);
  // stopBusy set before try, cleared in finally
  assert.match(component, /setStopBusy\(true\)/);
  assert.match(component, /setStopBusy\(false\)/);
  // Both Inspector and tray buttons use the same onClick={stopCampaign}
  const onClickMatches = component.match(/onClick=\{stopCampaign\}/g) || [];
  assert.equal(onClickMatches.length, 2, "Both Inspector and task tray buttons must bind the same stopCampaign handler");
  // Inspector shows "Stop Campaign now", tray shows "Stop now"
  assert.match(component, /Stop Campaign now/);
  assert.match(component, /Stop now/);
  // No duplicate builder
  const matches = component.match(/buildOperatorRequest/g);
  assert.ok(matches, "Expected buildOperatorRequest references in component");
});

// --- v67 regression: stopCampaign request build + invoke inside try, finally clears lock ---

test("v67 stopCampaign builds request and invokes inside try; finally always clears ref and stopBusy", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // Extract the stopCampaign function body (from "async function" to the closing "}" before campaignRunning)
  const stopMatch = component.match(/async function stopCampaign\(\) \{[\s\S]*?\n  \}/);
  assert.ok(stopMatch, "stopCampaign function body must be extractable");
  const body = stopMatch[0];
  // buildOperatorRequest must appear after "try {" and before the "finally" block
  const tryToFinally = body.match(/try \{([\s\S]*?)finally \{([\s\S]*?)\n  \}/);
  assert.ok(tryToFinally, "stopCampaign must have try/finally structure");
  const tryBlock = tryToFinally[1];
  const finallyBlock = tryToFinally[2];
  // buildOperatorRequest inside try
  assert.match(tryBlock, /buildOperatorRequest/, "buildOperatorRequest must be called inside try block");
  assert.match(tryBlock, /invoke\(/, "invoke must be called inside try block");
  assert.match(tryBlock, /stopCampaignRef\.current = promise/, "ref assignment must be inside try block");
  // finally clears both
  assert.match(finallyBlock, /stopCampaignRef\.current = null;/, "finally must clear ref");
  assert.match(finallyBlock, /setStopBusy\(false\)/, "finally must clear stopBusy");
});

// --- v67 regression: no politeStatus state ---

test("v67 component has no politeStatus state", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  assert.doesNotMatch(component, /politeStatus/, "politeStatus state must not exist");
});

// --- v67 regression: Save draft and Return for revision use setStatus ---

test("v67 saveDraft and returnForRevision call setStatus, not politeStatus", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // saveDraft function
  const saveMatch = component.match(/function saveDraft\(\) \{[\s\S]*?\n  \}/);
  assert.ok(saveMatch, "saveDraft function body must be extractable");
  const saveBody = saveMatch[0];
  assert.match(saveBody, /setStatus/, "saveDraft must call setStatus");
  assert.doesNotMatch(saveBody, /politeStatus/, "saveDraft must not reference politeStatus");
  // returnForRevision function
  const returnMatch = component.match(/function returnForRevision\(\) \{[\s\S]*?\n  \}/);
  assert.ok(returnMatch, "returnForRevision function body must be extractable");
  const returnBody = returnMatch[0];
  assert.match(returnBody, /setStatus/, "returnForRevision must call setStatus");
  assert.doesNotMatch(returnBody, /politeStatus/, "returnForRevision must not reference politeStatus");
});

test("no new intent, no demo, no Strategy UI, no Alt+N/R/E/S global keys", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // No new intents beyond existing set
  assert.doesNotMatch(component, /definition\.strategy\.create/);
  assert.doesNotMatch(component, /StrategyDefinition/);
  assert.doesNotMatch(component, /rawJson/);
  assert.doesNotMatch(component, /demo/i);
  // No global keyboard shortcuts
  assert.doesNotMatch(component, /Alt\+[NRES]/i);
  // No candidate sorting / focus implementation
  assert.doesNotMatch(component, /candidateSort|focusCandidate/);
  // No 7.5 or 9.3 claims
  assert.doesNotMatch(component, /7\.5|9\.3/);
});

// --- v69: stoppableCampaign is a plain deterministic .find() derivation (no useMemo); campaignRunning derived from it ---

test("v70 stoppableCampaign is a plain deterministic .find() derivation (no useMemo) that finds first running progress not suppressed by matching stopped receipt with exact evidence kind gate [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // Must NOT be a useMemo — v70 removes the manual memo per react-hooks/preserve-manual-memoization
  assert.doesNotMatch(component, /const stoppableCampaign = useMemo/);
  // Must be a plain assignment (deterministic .find() derivation, no caching)
  assert.match(component, /const stoppableCampaign = \(bundle\.progress \|\| \[\]\)\.find/);
  // Uses .find() on progress, not .some() or .filter() — returns the matching item
  assert.match(component, /bundle\.progress \|\| \[\]\)\.find/);
  assert.doesNotMatch(component, /bundle\.progress \|\| \[\]\)\.some/);
  assert.doesNotMatch(component, /bundle\.progress \|\| \[\]\)\.filter/);
  // Guards on p.status === "running"
  assert.match(component, /p\.status === "running"/);
  // The stopped receipt gate checks exact kind === "autoquant-campaign-stop-request"
  assert.match(component, /e\?\.kind === "autoquant-campaign-stop-request"/);
  // Also checks status === "stopped" and campaignId match
  assert.match(component, /r\.status === "stopped"/);
  assert.match(component, /e\?\.campaignId === p\.campaignId/);
  // Returns null (not undefined) when nothing found — the || null fallback
  assert.match(component, /\|\| null/);
});

test("v69 campaignRunning is derived from stoppableCampaign — no independent progress scan [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // campaignRunning must be a direct Boolean derivation
  assert.match(component, /const campaignRunning = Boolean\(stoppableCampaign\)/);
  // Must NOT have an independent progress scan on campaignRunning
  // Check that the only .find() on bundle.progress is inside stoppableCampaign
  const scIdx = component.indexOf("const stoppableCampaign = (bundle.progress || []).find");
  assert.ok(scIdx >= 0, "stoppableCampaign declaration must exist with plain .find()");
  const crIdx = component.indexOf("const campaignRunning = Boolean");
  assert.ok(scIdx < crIdx, "stoppableCampaign must be defined before campaignRunning");
  // After campaignRunning declaration until stopCampaign definition, no second bundle.progress scan
  // stopCampaign is defined BEFORE campaignRunning in source order (lines 867-878 before 880-890);
  // the meaningful region for a dual-scan is between campaignRunning and stoppableCampaign,
  // and inside stopCampaign itself (already tested separately). Check that campaignRunning
  // is a genuine Boolean derivation, not a useMemo with its own .some()/.find().
  assert.doesNotMatch(component, /campaignRunning = useMemo/);
  assert.match(component, /const campaignRunning = Boolean\(stoppableCampaign\)/);
});

test("v69 stopCampaign guards both stopCampaignRef.current AND !stoppableCampaign [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  const stopMatch = component.match(/async function stopCampaign\(\) \{[\s\S]*?\n  \}/);
  assert.ok(stopMatch, "stopCampaign function body must be extractable");
  const body = stopMatch[0];
  // Dual guard: ref AND stoppableCampaign
  assert.match(body, /if \(stopCampaignRef\.current \|\| !stoppableCampaign\) return/);
  // Does NOT independently scan bundle.progress inside stopCampaign
  assert.doesNotMatch(body, /bundle\.progress/);
});

test("v69 stopCampaign builds request with stoppableCampaign.campaignId inside try block [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  const stopMatch = component.match(/async function stopCampaign\(\) \{[\s\S]*?\n  \}/);
  assert.ok(stopMatch, "stopCampaign function body must be extractable");
  const body = stopMatch[0];
  // Uses stoppableCampaign.campaignId, not a locally-scanned progress item
  assert.match(body, /stoppableCampaign\.campaignId/);
  // buildOperatorRequest for campaign.stop uses exact kind: "campaign"
  assert.match(body, /kind: "campaign"/);
  // No local .find() on bundle.progress inside stopCampaign
  assert.doesNotMatch(body, /bundle\.progress/);
  // try/finally structure preserved
  assert.match(body, /try \{/);
  assert.match(body, /finally \{/);
  assert.match(body, /stopCampaignRef\.current = null/);
  assert.match(body, /setStopBusy\(false\)/);
});

test("v70 multi-campaign source coverage: A stopped + B running → stoppableCampaign is B, not A [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // v70: stoppableCampaign is a plain .find(), not a useMemo
  assert.doesNotMatch(component, /const stoppableCampaign = useMemo/);
  assert.match(component, /const stoppableCampaign = \(bundle\.progress \|\| \[\]\)\.find/);
  // Uses .find() which returns the first match — so with multiple running campaigns,
  // the first one NOT suppressed by receipt wins
  assert.match(component, /\.find\(/);
  // The receipt gate checks kind === "autoquant-campaign-stop-request" exactly
  assert.match(component, /e\?\.kind === "autoquant-campaign-stop-request"/);
  // Each running progress item is tested against ALL receipts
  assert.match(component, /!receipts\.some/);
  // When A is stopped (receipt matches) but B is running (no matching receipt),
  // .find() will skip A and return B — source structure confirms this path
  // Real browser React re-render verification remains for the QA reviewer
});

test("v69 campaignRunning guards both Stop buttons with stopDisabled [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // stopDisabled still driven by campaignRunning (now derived from stoppableCampaign)
  assert.match(component, /stopDisabled\s*=\s*busy\s*\|\|\s*!campaignRunning\s*\|\|\s*stopBusy/);
  // Both Inspector and tray Stop buttons use the same handler
  const onClickMatches = component.match(/onClick=\{stopCampaign\}/g) || [];
  assert.equal(onClickMatches.length, 2, "Both Inspector and tray Stop buttons must bind same handler");
  // Both use disabled={stopDisabled}
  const stopDisabledMatches = component.match(/disabled=\{stopDisabled\}/g) || [];
  assert.ok(stopDisabledMatches.length >= 2, "stopDisabled must drive both Stop buttons");
});

test("v69 no independent dual-scan path: stopCampaign uses stoppableCampaign, campaignRunning is Boolean derivation; unique progress scan count = 1 [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // stopCampaign does NOT contain its own bundle.progress.find/filter/some
  const stopMatch = component.match(/async function stopCampaign\(\) \{[\s\S]*?\n  \}/);
  assert.ok(stopMatch);
  assert.doesNotMatch(stopMatch[0], /bundle\.progress/);
  // campaignRunning is NOT a useMemo with its own scan
  assert.match(component, /const campaignRunning = Boolean\(stoppableCampaign\)/);
  // The old v68 pattern (independent .some() in campaignRunning) is gone
  assert.doesNotMatch(component, /campaignRunning = useMemo/);
  // Unique progress scan count: extract the production declaration region
  // (stoppableCampaign + campaignRunning, lines 880-890) and count bundle.progress.
  // Exclude stopCampaign (lines 867-878, already verified clean above) and
  // test strings (this file). The only production scan must be the .find() inside
  // stoppableCampaign — exactly one.
  const scDecl = component.indexOf("const stoppableCampaign = (bundle.progress || []).find");
  assert.ok(scDecl >= 0, "stoppableCampaign declaration must be present");
  const crDecl = component.indexOf("const campaignRunning = Boolean(stoppableCampaign)");
  assert.ok(crDecl >= 0, "campaignRunning declaration must be present");
  // Extract the stoppableCampaign → campaignRunning span
  const declSpan = component.slice(scDecl, crDecl + "const campaignRunning = Boolean(stoppableCampaign)".length);
  const progressScanCount = (declSpan.match(/bundle\.progress/g) || []).length;
  assert.equal(progressScanCount, 1, `Expected exactly 1 bundle.progress scan in production declarations, got ${progressScanCount}`);
  // Additionally, assert that within the entire production body (excluding stopCampaign already verified),
  // no other function body contains bundle.progress
  const stopFnStart = component.indexOf("async function stopCampaign()");
  const stopFnEnd = component.indexOf("\n  }", component.indexOf("setStopBusy(false)", stopFnStart)) + 4;
  const afterStop = component.slice(stopFnEnd);
  // After the stopCampaign closing brace, count bundle.progress — must be exactly 1 (stoppableCampaign)
  const afterStopCount = (afterStop.match(/bundle\.progress/g) || []).length;
  assert.equal(afterStopCount, 1, `Expected exactly 1 bundle.progress reference after stopCampaign (stoppableCampaign .find()), got ${afterStopCount}`);
});

test("v70 failed/non-stopped/wrong-kind evidence does not gate stoppableCampaign [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // v70: stoppableCampaign is a plain .find(), not useMemo
  assert.doesNotMatch(component, /const stoppableCampaign = useMemo/);
  assert.match(component, /const stoppableCampaign = \(bundle\.progress \|\| \[\]\)\.find/);
  // Only r.status === "stopped", never "failed"
  const stoppedCheck = component.match(/r\.status === "stopped"/g);
  assert.equal(stoppedCheck.length, 1, "Only one stopped status check exists in the receipt filter");
  const failedMatch = component.match(/r\.status === "failed"/);
  assert.equal(failedMatch, null, "Must not match on failed status");
  // Only r.intent === "campaign.stop"
  assert.match(component, /r\.intent === "campaign\.stop"/);
  // Evidence kind must be exactly "autoquant-campaign-stop-request"
  assert.match(component, /e\?\.kind === "autoquant-campaign-stop-request"/);
});

test("v69 v67 regressions preserved: try/finally lock, no politeStatus, Save draft/Return for revision, no new intents [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // try/finally still intact with lock clearing
  assert.match(component, /finally \{/);
  assert.match(component, /stopCampaignRef\.current = null/);
  assert.match(component, /setStopBusy\(false\)/);
  // No politeStatus
  assert.doesNotMatch(component, /politeStatus/);
  // Save draft / Return for revision
  assert.match(component, /Save draft/);
  assert.match(component, /Return for revision/);
  // No new intents
  assert.doesNotMatch(component, /definition\.strategy\.create/);
  assert.doesNotMatch(component, /campaign\.start/);
  // No fake receipt, no demo data
  assert.doesNotMatch(component, /fake.*receipt/i);
  assert.doesNotMatch(component, /demo.*stop/i);
});

test("v69 Drawer close does not clear pending confirmation [source contract]", async () => {
  const component = await readFile(new URL("../components/research-console.jsx", import.meta.url), "utf8");
  // Drawer onClose only sets inspectorOpen false, does not touch pendingConfirmation
  assert.match(component, /onClose=\{\(\) => setInspectorOpen\(false\)\}/);
  const drawerLine = component.match(/<Drawer[\s\S]*?\/>/)?.[0] || "";
  assert.doesNotMatch(drawerLine, /setPendingConfirmation/);
});
