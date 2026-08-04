export const RESEARCH_STAGE_ORDER = [
  "data",
  "question",
  "factor",
  "experiment",
  "campaign",
  "evidence",
  "approval",
  "reproduction",
];

export const READ_ONLY_INTENTS = [
  "research.inspect",
  "research.explain",
  "research.compare",
  "research.reproduction-readiness",
];

export const CONFIRMATION_INTENTS = [
  "definition.factor.create",
  "definition.strategy.create",
  "definition.experiment.create",
  "artifact.decide",
  "reproduction.start",
];

export const CONFIRMATION_DECISION_INTENTS = ["confirmation.accept"];
export const IMMEDIATE_INTENTS = ["campaign.stop"];
export const CAMPAIGN_EXECUTOR_INTENTS = ["campaign.start", "campaign.pause", "campaign.resume"];
const INPUT_FIELDS = new Map([
  ...READ_ONLY_INTENTS.map((intent) => [intent, new Set()]),
  ["definition.factor.create", new Set(["definition"])],
  ["definition.strategy.create", new Set(["definition"])],
  ["definition.experiment.create", new Set(["definition"])],
  ["artifact.decide", new Set(["review"])],
  ["reproduction.start", new Set(["reproduction"])],
  ["confirmation.accept", new Set(["executionActor"])],
  ["campaign.stop", new Set()],
  ["campaign.start", new Set(["experimentDefinitionRef"])],
  ["campaign.pause", new Set()],
  ["campaign.resume", new Set()],
]);

const APPROVED_ENVELOPE_INTENTS = new Set([
  ...CONFIRMATION_DECISION_INTENTS,
  ...IMMEDIATE_INTENTS,
  ...CAMPAIGN_EXECUTOR_INTENTS,
]);
const INTENTS = new Set([...READ_ONLY_INTENTS, ...CONFIRMATION_INTENTS, ...APPROVED_ENVELOPE_INTENTS]);
const REQUEST_FIELDS = new Set([
  "schemaVersion", "kind", "requestId", "actor", "workspaceRef", "projectId",
  "sessionId", "intent", "objectRefs", "authority", "budget", "confirmationRef",
  "expectedState", "input",
]);
const FORBIDDEN_KEYS = new Set([
  "command", "shell", "argv", "providercommand", "apikey", "password", "secret",
  "credential", "credentials", "token", "path", "filepath", "directory",
]);
const REQUEST_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const ALLOWED_OBJECT_REF_KINDS = new Set(["session", "factor-definition", "strategy-definition", "experiment-definition", "campaign", "artifact-approval", "reproduction-receipt"]);

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value, expected, label) {
  if (!isRecord(value) || Object.keys(value).length !== expected.size || Object.keys(value).some((key) => !expected.has(key))) {
    throw new Error(`${label} has unsupported fields`);
  }
}

function rejectForbidden(value) {
  if (Array.isArray(value)) {
    value.forEach(rejectForbidden);
    return;
  }
  if (!isRecord(value)) return;
  for (const [key, item] of Object.entries(value)) {
    const normalized = key.toLowerCase().replaceAll("-", "").replaceAll("_", "");
    if (FORBIDDEN_KEYS.has(key.toLowerCase()) || [...FORBIDDEN_KEYS].some((item) => normalized === item || normalized.endsWith(item))) {
      throw new Error("Operator requests cannot carry commands, credentials, or paths");
    }
    rejectForbidden(item);
  }
}

export function inspectResearchLedger(bundle) {
  const ledger = bundle?.researchLedger;
  const diagnostics = Array.isArray(bundle?.researchLedgerDiagnostics) ? bundle.researchLedgerDiagnostics : [];
  if (!isRecord(ledger)) return { state: diagnostics.length ? "invalid" : "unavailable", ledger: null, diagnostics };
  if (ledger.schemaVersion !== 1 || ledger.kind !== "autoquant-research-ledger" || !Array.isArray(ledger.stages) || !Array.isArray(ledger.receipts)) {
    return { state: "invalid", ledger: null, diagnostics: [...diagnostics, { code: "studio.ledger.invalid", message: "Core returned an unsupported ResearchLedger projection.", category: "research-ledger" }] };
  }
  const ids = ledger.stages.map((stage) => stage?.id);
  if (ids.length !== RESEARCH_STAGE_ORDER.length || ids.some((id, index) => id !== RESEARCH_STAGE_ORDER[index])) {
    return { state: "invalid", ledger: null, diagnostics: [...diagnostics, { code: "studio.ledger.order", message: "ResearchLedger stage order is invalid.", category: "research-ledger" }] };
  }
  return { state: diagnostics.length ? "partial" : "available", ledger, diagnostics };
}

export function researchSessions(snapshot) {
  const sessions = [];
  for (const project of snapshot?.projects || []) {
    for (const bundle of project?.sessions || []) {
      if (typeof bundle?.session?.id !== "string") continue;
      sessions.push({ project, bundle, projection: inspectResearchLedger(bundle) });
    }
  }
  return sessions;
}

export function selectResearchSession(snapshot, sessionId) {
  const matches = researchSessions(snapshot).filter((item) => item.bundle.session.id === sessionId);
  if (matches.length !== 1) throw new Error(matches.length ? "Session id is ambiguous across Projects" : "Session is not part of the connected Core snapshot");
  return matches[0];
}

export function parseJsonObject(value) {
  const parsed = JSON.parse(value);
  if (!isRecord(parsed)) throw new Error("Input must be one JSON object");
  return parsed;
}

const FACTOR_EDITABLE_KEYS = new Set(["hypothesis", "calculation", "parameters", "output", "dataDependencies", "missingDataPolicy", "cohort", "expectedHorizon", "requiredTests", "failureGates"]);
const EXPERIMENT_EDITABLE_KEYS = new Set(["definitionRef", "data", "subject", "outcome", "benchmark", "costPolicy", "splitPolicy", "robustness", "selectionAdjustment", "holdoutPolicy", "executorPolicy", "budget", "stopConditions"]);
const IDENTITY_KEYS = new Set(["id", "version", "createdAt", "parentVersion"]);
const ID_CONVENTION = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;

function validateDraftIdentity(identity) {
  exactKeys(identity, IDENTITY_KEYS, "Identity");
  if (typeof identity.id !== "string" || !ID_CONVENTION.test(identity.id)) throw new Error("Identity id is invalid");
  if (!Number.isInteger(identity.version) || identity.version < 1) throw new Error("Identity version is invalid");
  if (identity.parentVersion !== null) {
    if (!Number.isInteger(identity.parentVersion) || identity.parentVersion < 1 || identity.parentVersion >= identity.version) throw new Error("Identity parentVersion is invalid");
  } else if (identity.version !== 1) {
    throw new Error("Identity parentVersion must be null only for version 1");
  }
  if (typeof identity.createdAt !== "string" || !identity.createdAt) throw new Error("Identity createdAt is invalid");
  const parsed = new Date(identity.createdAt);
  if (isNaN(parsed.getTime()) || parsed.toISOString() !== identity.createdAt) throw new Error("Identity createdAt is not a valid ISO timestamp");
}

export function buildFactorDefinitionDraft({ identity, editable }) {
  validateDraftIdentity(identity);
  exactKeys(editable, FACTOR_EDITABLE_KEYS, "Factor editable");
  const cloned = structuredClone(editable);
  return {
    schemaVersion: 1,
    kind: "autoquant-factor-definition",
    status: "draft",
    lineage: { parentVersion: identity.parentVersion },
    id: identity.id,
    version: identity.version,
    createdAt: identity.createdAt,
    ...cloned,
  };
}

export function buildExperimentDefinitionDraft({ identity, editable }) {
  validateDraftIdentity(identity);
  exactKeys(editable, EXPERIMENT_EDITABLE_KEYS, "Experiment editable");
  const cloned = structuredClone(editable);
  return {
    schemaVersion: 1,
    kind: "autoquant-experiment-definition",
    status: "draft",
    lineage: { parentVersion: identity.parentVersion },
    id: identity.id,
    version: identity.version,
    createdAt: identity.createdAt,
    ...cloned,
  };
}

export function buildOperatorRequest({ snapshot, project, bundle, intent, input = {}, objectRefs = [], confirmationRef = null, requestId, actor = { id: "autoquant-studio-local", kind: "studio" }, budget, objectHashes }) {
  if (!INTENTS.has(intent)) throw new Error("Unknown closed Operator intent");
  const id = requestId || `studio-${Date.now()}-${globalThis.crypto.randomUUID()}`;
  const authorityMode = CONFIRMATION_INTENTS.includes(intent)
    ? "confirmation-bound"
    : APPROVED_ENVELOPE_INTENTS.has(intent)
    ? "approved-envelope"
    : "read-only";
  const request = {
    schemaVersion: 1,
    kind: "autoquant-operator-request",
    requestId: id,
    actor,
    workspaceRef: snapshot?.source?.rootDir,
    projectId: project?.id,
    sessionId: bundle?.session?.id,
    intent,
    objectRefs,
    authority: { mode: authorityMode },
    budget: budget ?? { candidateLimit: 0, wallTimeSeconds: 0, cpuSeconds: 0, gpuSeconds: 0, cost: null },
    confirmationRef,
    expectedState: { sessionStatus: bundle?.session?.status, objectHashes: objectHashes ?? {} },
    input,
  };
  validateOperatorRequest(request, snapshot);
  return request;
}

export function validateOperatorRequest(request, snapshot) {
  exactKeys(request, REQUEST_FIELDS, "Operator request");
  rejectForbidden(request);
  if (request.schemaVersion !== 1 || request.kind !== "autoquant-operator-request" || !REQUEST_ID.test(request.requestId) || !INTENTS.has(request.intent)) {
    throw new Error("Unsupported Operator request identity or intent");
  }
  exactKeys(request.actor, new Set(["id", "kind"]), "Operator actor");
  const confirmationDecision = CONFIRMATION_DECISION_INTENTS.includes(request.intent);
  const expectedActor = confirmationDecision ? "user" : "studio";
  if (request.actor.kind !== expectedActor || typeof request.actor.id !== "string" || !request.actor.id) throw new Error(`${expectedActor} actor is required`);
  if (!isRecord(request.input) || !Array.isArray(request.objectRefs)) throw new Error("Operator input and objectRefs are invalid");
  exactKeys(request.input, INPUT_FIELDS.get(request.intent), "Operator input");
  for (const reference of request.objectRefs) {
    exactKeys(reference, new Set(["kind", "id", "version"]), "Object reference");
    if (typeof reference.id !== "string" || !reference.id || (reference.version !== null && (!Number.isInteger(reference.version) || reference.version < 1))) throw new Error("Object reference is invalid");
    if (!ALLOWED_OBJECT_REF_KINDS.has(reference.kind)) throw new Error("Object reference kind is not allowed");
  }
  exactKeys(request.authority, new Set(["mode"]), "Operator authority");
  const expectedMode = CONFIRMATION_INTENTS.includes(request.intent)
    ? "confirmation-bound"
    : APPROVED_ENVELOPE_INTENTS.has(request.intent)
    ? "approved-envelope"
    : "read-only";
  if (request.authority.mode !== expectedMode) throw new Error("Operator authority does not match intent");
  exactKeys(request.budget, new Set(["candidateLimit", "wallTimeSeconds", "cpuSeconds", "gpuSeconds", "cost"]), "Operator budget");
  for (const key of ["candidateLimit", "wallTimeSeconds", "cpuSeconds", "gpuSeconds"]) {
    const val = request.budget[key];
    if (!Number.isInteger(val) || val < 0) throw new Error("Operator budget is invalid");
  }
  const cost = request.budget.cost;
  if (cost !== null) {
    if (!isRecord(cost)) throw new Error("Operator budget cost is invalid");
    exactKeys(cost, new Set(["currency", "amount"]), "Operator budget cost");
    if (typeof cost.currency !== "string" || !cost.currency.trim()) throw new Error("Operator budget cost currency is invalid");
    if (typeof cost.amount !== "number" || !Number.isFinite(cost.amount) || cost.amount < 0) throw new Error("Operator budget cost amount is invalid");
  }
  if (request.intent === "campaign.start") {
    if (request.objectRefs.length !== 0) throw new Error("campaign.start does not accept object references");
    const experimentDefinitionRef = request.input.experimentDefinitionRef;
    if (!isRecord(experimentDefinitionRef)) throw new Error("campaign.start experimentDefinitionRef is invalid");
    exactKeys(experimentDefinitionRef, new Set(["id", "version", "contentHash"]), "campaign.start experimentDefinitionRef");
    if (typeof experimentDefinitionRef.id !== "string" || !experimentDefinitionRef.id) throw new Error("campaign.start experimentDefinitionRef id is invalid");
    if (!Number.isInteger(experimentDefinitionRef.version) || experimentDefinitionRef.version < 1) throw new Error("campaign.start experimentDefinitionRef version is invalid");
    if (typeof experimentDefinitionRef.contentHash !== "string" || !/^[0-9a-f]{64}$/.test(experimentDefinitionRef.contentHash)) throw new Error("campaign.start experimentDefinitionRef contentHash is invalid");
    if (request.budget.candidateLimit <= 0) throw new Error("campaign.start candidateLimit must be positive");
  }
  if (request.intent === "campaign.pause" || request.intent === "campaign.resume") {
    if (request.objectRefs.length !== 1) throw new Error("campaign.pause/resume requires exactly one object reference");
    const ref = request.objectRefs[0];
    if (ref.kind !== "campaign") throw new Error("campaign.pause/resume object reference must be a campaign");
    if (typeof ref.id !== "string" || !ref.id) throw new Error("campaign.pause/resume object reference id is invalid");
    if (ref.version !== null) throw new Error("campaign.pause/resume object reference version must be null");
  }
  if (request.confirmationRef !== null && !REQUEST_ID.test(request.confirmationRef)) throw new Error("Confirmation reference is invalid");
  exactKeys(request.expectedState, new Set(["sessionStatus", "objectHashes"]), "Expected state");
  if (!["active", "promoted", "completed"].includes(request.expectedState.sessionStatus)) throw new Error("Expected state is invalid");
  if (!isRecord(request.expectedState.objectHashes)) throw new Error("Expected state objectHashes is invalid");
  for (const [key, hash] of Object.entries(request.expectedState.objectHashes)) {
    if (typeof key !== "string" || !key) throw new Error("Expected state objectHashes key is invalid");
    if (typeof hash !== "string" || !/^[0-9a-f]{64}$/.test(hash)) throw new Error("Expected state objectHashes value is not a 64-hex sha256");
  }
  if (typeof request.workspaceRef !== "string" || request.workspaceRef !== snapshot?.source?.rootDir) throw new Error("Workspace reference does not match the connected snapshot");
  const project = snapshot?.projects?.find((item) => item.id === request.projectId);
  if (!project || typeof project.rootDir !== "string" || !project.rootDir) throw new Error("Project is not part of the connected snapshot");
  if (!project.sessions?.some((item) => item?.session?.id === request.sessionId)) throw new Error("Session is not part of the connected Project");
  return { project, request };
}

export function receiptFromEnvelope(payload) {
  const receipt = payload?.data?.receipt;
  if (!isRecord(receipt) || receipt.kind !== "autoquant-agent-operation-receipt" || receipt.schemaVersion !== 1) {
    throw new Error(payload?.error?.message || "Core returned an unsupported Operator receipt");
  }
  return receipt;
}

export function latestCampaignBudget(bundle) {
  const progress = Array.isArray(bundle?.progress) ? bundle.progress.at(-1) : null;
  const campaign = Array.isArray(bundle?.campaigns) ? bundle.campaigns.at(-1) : null;
  return progress?.budget || campaign?.budget || null;
}

// --- ArtifactReview / ReproductionRequest builders ---

const ARTIFACT_REVIEW_FIELDS = new Set(["id", "decision", "actor", "definitionRef", "definitionHash", "evidenceManifest", "reason"]);
const ARTIFACT_DECISIONS = new Set(["approve", "return-for-revision", "retain-as-draft"]);
const DEFINITION_REF_KINDS = new Set(["factor", "strategy"]);
const HEX64_REGEX = /^[0-9a-f]{64}$/;
const EVIDENCE_MANIFEST_KEYS = new Set([
  "data", "experimentDefinition", "runs", "assessment", "costs",
  "holdout", "limitations", "diagnostics", "artifactHashes", "metrics",
  "environment", "cpuEquivalentAllowed",
]);

function validateEvidenceManifest(em, label) {
  exactKeys(em, EVIDENCE_MANIFEST_KEYS, label);
  if (!Array.isArray(em.runs) || em.runs.length === 0) throw new Error(`${label} runs must be a non-empty array`);
  if (!Array.isArray(em.limitations)) throw new Error(`${label} limitations must be an array`);
  if (!Array.isArray(em.diagnostics)) throw new Error(`${label} diagnostics must be an array`);
  if (!isRecord(em.artifactHashes)) throw new Error(`${label} artifactHashes must be a record`);
  for (const [key, hash] of Object.entries(em.artifactHashes)) {
    if (typeof key !== "string" || !key) throw new Error(`${label} artifactHashes key is invalid`);
    if (typeof hash !== "string" || !HEX64_REGEX.test(hash)) throw new Error(`${label} artifactHashes value is not 64-hex`);
  }
  if (!isRecord(em.metrics)) throw new Error(`${label} metrics must be a record`);
  for (const [key, val] of Object.entries(em.metrics)) {
    if (typeof key !== "string" || !key) throw new Error(`${label} metrics key is invalid`);
    if (typeof val !== "number" || !Number.isFinite(val)) throw new Error(`${label} metrics value is not finite`);
  }
  if (!isRecord(em.environment) || Object.keys(em.environment).length === 0) throw new Error(`${label} environment must be a non-empty object`);
  if (typeof em.cpuEquivalentAllowed !== "boolean") throw new Error(`${label} cpuEquivalentAllowed must be a boolean`);
}

export function buildArtifactReviewDraft(fields) {
  exactKeys(fields, ARTIFACT_REVIEW_FIELDS, "ArtifactReview fields");
  if (typeof fields.id !== "string" || !ID_CONVENTION.test(fields.id)) throw new Error("ArtifactReview id is invalid");
  if (!ARTIFACT_DECISIONS.has(fields.decision)) throw new Error("ArtifactReview decision is invalid");
  exactKeys(fields.actor, new Set(["id", "kind"]), "ArtifactReview actor");
  if (typeof fields.actor.id !== "string" || !fields.actor.id) throw new Error("ArtifactReview actor id is invalid");
  if (typeof fields.actor.kind !== "string" || !fields.actor.kind) throw new Error("ArtifactReview actor kind is invalid");
  exactKeys(fields.definitionRef, new Set(["kind", "id", "version"]), "ArtifactReview definitionRef");
  if (!DEFINITION_REF_KINDS.has(fields.definitionRef.kind)) throw new Error("ArtifactReview definitionRef kind is invalid");
  if (typeof fields.definitionRef.id !== "string" || !ID_CONVENTION.test(fields.definitionRef.id)) throw new Error("ArtifactReview definitionRef id is invalid");
  if (!Number.isInteger(fields.definitionRef.version) || fields.definitionRef.version < 1) throw new Error("ArtifactReview definitionRef version is invalid");
  if (typeof fields.definitionHash !== "string" || !HEX64_REGEX.test(fields.definitionHash)) throw new Error("ArtifactReview definitionHash is invalid");
  if (typeof fields.reason !== "string" || !fields.reason.trim()) throw new Error("ArtifactReview reason must be a non-empty string");
  validateEvidenceManifest(fields.evidenceManifest, "ArtifactReview evidenceManifest");
  const cloned = structuredClone(fields);
  return {
    schemaVersion: 1,
    kind: "autoquant-artifact-review",
    ...cloned,
  };
}

export function buildReproductionRequestDraft(fields) {
  exactKeys(fields, new Set(["id", "approvalId"]), "ReproductionRequest fields");
  if (typeof fields.id !== "string" || !ID_CONVENTION.test(fields.id)) throw new Error("ReproductionRequest id is invalid");
  if (typeof fields.approvalId !== "string" || !ID_CONVENTION.test(fields.approvalId)) throw new Error("ReproductionRequest approvalId is invalid");
  const cloned = structuredClone(fields);
  return {
    schemaVersion: 1,
    kind: "autoquant-reproduction-request",
    ...cloned,
  };
}
