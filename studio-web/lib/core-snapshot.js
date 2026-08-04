export const STUDIO_SNAPSHOT_KIND = "autoquant-studio-snapshot";
export const DEFAULT_CORE_ORIGIN = "http://127.0.0.1:8765";

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isDiagnostic(value) {
  return isRecord(value)
    && typeof value.code === "string"
    && typeof value.message === "string"
    && typeof value.category === "string";
}

function isStudy(value) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.name === "string"
    && typeof value.subjectKind === "string";
}

function isProject(value) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.name === "string"
    && typeof value.valid === "boolean"
    && Array.isArray(value.studies)
    && value.studies.every(isStudy)
    && Array.isArray(value.diagnostics)
    && value.diagnostics.every(isDiagnostic);
}

export function resolveCoreSnapshotUrl(rawOrigin = DEFAULT_CORE_ORIGIN) {
  const origin = new URL(rawOrigin);
  if (
    origin.protocol !== "http:"
    || !LOOPBACK_HOSTS.has(origin.hostname)
    || origin.username
    || origin.password
    || origin.search
    || origin.hash
    || !["", "/"].includes(origin.pathname)
  ) {
    throw new Error("Core origin must be an unauthenticated loopback HTTP origin");
  }
  return new URL("/api/v1/snapshot", origin).toString();
}

export function validateCoreSnapshot(value) {
  if (!isRecord(value)) {
    throw new Error("Core returned a non-object snapshot");
  }
  if (
    value.kind !== STUDIO_SNAPSHOT_KIND
    || value.schemaVersion !== 1
    || typeof value.generatedAt !== "string"
    || Number.isNaN(Date.parse(value.generatedAt))
    || !isRecord(value.harness)
    || typeof value.harness.version !== "string"
    || typeof value.harness.commit !== "string"
    || typeof value.harness.sourceHash !== "string"
    || !isRecord(value.source)
    || !Array.isArray(value.projects)
    || !value.projects.every(isProject)
    || !Array.isArray(value.diagnostics)
    || !value.diagnostics.every(isDiagnostic)
    || typeof value.valid !== "boolean"
  ) {
    throw new Error("Core returned an unsupported Studio snapshot");
  }
  return value;
}

export function coreFactorFrom(snapshot) {
  const project = snapshot?.projects?.[0];
  const study = project?.studies?.find((item) => item.subjectKind === "factor")
    || project?.studies?.[0];
  if (!project) return null;
  const dataset = study?.dataset;
  return {
    id: study?.id || project.id,
    name: study?.name || project.name,
    version: `AQ ${snapshot.harness.version}`,
    status: project.valid ? "Core verified" : "Core diagnostics",
    owner: project.name,
    description: study?.description || project.description,
    frameId: project.agentWorkBriefHash
      ? `brief:${project.agentWorkBriefHash.slice(0, 12)}`
      : `snapshot:${snapshot.generatedAt}`,
    bundleId: study?.datasetHash
      ? `dataset:${study.datasetHash.slice(0, 12)}`
      : `source:${snapshot.harness.sourceHash.slice(0, 12)}`,
    dataset: dataset ? `${dataset.id}@${dataset.version}` : "Core snapshot",
  };
}
