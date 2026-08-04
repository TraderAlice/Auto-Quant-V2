import path from "node:path";

export const INTAKE_TEMPLATES = new Set([
  "ohlcv-factor-lab",
  "ohlcv-portfolio-lab",
  "ohlcv-rl-factor-lab",
  "ohlcv-book-risk-lab",
  "ohlcv-event-study-lab",
  "ohlcv-book-path-stress-lab",
  "ohlcv-allocation-lab",
  "ohlcv-research-desk",
]);

export const INTAKE_LIMITS = {
  jsonBytes: 2 * 1024 * 1024,
  sourceBytes: 64 * 1024 * 1024,
  totalBytes: 256 * 1024 * 1024,
  sourceFiles: 128,
};

const PROJECT_ID = /^[a-z0-9][a-z0-9-]{0,63}$/;
const SOURCE_SUFFIXES = new Set([".csv", ".json", ".parquet", ".feather"]);

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function selectIntakeTarget(fields, snapshot) {
  if (!isRecord(fields) || typeof fields.projectId !== "string" || !PROJECT_ID.test(fields.projectId)) {
    throw new Error("projectId must contain lowercase letters, numbers, or hyphens");
  }
  if (typeof fields.template !== "string" || !INTAKE_TEMPLATES.has(fields.template)) {
    throw new Error("Unsupported intake template");
  }
  if (fields.name !== undefined && (typeof fields.name !== "string" || fields.name.trim().length > 120)) {
    throw new Error("Project name must be at most 120 characters");
  }
  if (snapshot?.source?.scope !== "workspace") {
    throw new Error("Price-data intake requires a verified Workspace snapshot");
  }
  const workspaceRoot = snapshot.source.rootDir;
  const projectsDir = snapshot.source.workspace?.projectsDir;
  if (!path.isAbsolute(workspaceRoot || "") || !path.isAbsolute(projectsDir || "")) {
    throw new Error("Core snapshot has no executable Workspace boundary");
  }
  if (snapshot.projects.some((project) => project.id === fields.projectId)) {
    throw new Error("The target Project already exists");
  }
  return {
    projectId: fields.projectId,
    template: fields.template,
    name: fields.name?.trim() || null,
    workspaceRoot,
    projectsDir,
  };
}

export function safeSourcePath(value) {
  if (typeof value !== "string" || !value || value.includes("\\") || value.includes("\0")) {
    throw new Error("Every uploaded data file needs a portable relative path");
  }
  if (path.posix.isAbsolute(value) || path.posix.normalize(value) !== value) {
    throw new Error(`Unsafe data-file path: ${value}`);
  }
  const segments = value.split("/");
  if (segments.some((segment) => !segment || segment === "." || segment === "..")) {
    throw new Error(`Unsafe data-file path: ${value}`);
  }
  if (!SOURCE_SUFFIXES.has(path.posix.extname(value).toLowerCase())) {
    throw new Error(`Unsupported data-file type: ${value}`);
  }
  return value;
}

export function validateIntakeDocuments(requestText, packageText, uploadedPaths) {
  let researchRequest;
  let datasetPackage;
  try {
    researchRequest = JSON.parse(requestText);
  } catch {
    throw new Error("Research Request is not valid JSON");
  }
  try {
    datasetPackage = JSON.parse(packageText);
  } catch {
    throw new Error("Dataset package is not valid JSON");
  }
  if (!isRecord(researchRequest) || researchRequest.kind !== "autoquant-research-request") {
    throw new Error("Research Request has an unsupported contract kind");
  }
  if (!isRecord(datasetPackage) || datasetPackage.kind !== "autoquant-ohlcv-dataset-package") {
    throw new Error("Dataset package has an unsupported contract kind");
  }
  if (!Array.isArray(datasetPackage.assets) || datasetPackage.assets.length === 0) {
    throw new Error("Dataset package must declare at least one asset");
  }

  const references = datasetPackage.assets.map((asset) => safeSourcePath(asset?.path));
  if (new Set(references).size !== references.length) {
    throw new Error("Dataset package contains duplicate asset paths");
  }
  const uploads = uploadedPaths.map(safeSourcePath);
  if (new Set(uploads).size !== uploads.length) {
    throw new Error("Uploaded data-file paths must be unique");
  }
  const uploaded = new Set(uploads);
  const missing = references.filter((reference) => !uploaded.has(reference));
  if (missing.length) throw new Error(`Dataset package references missing files: ${missing.join(", ")}`);
  const extra = uploads.filter((upload) => !references.includes(upload));
  if (extra.length) throw new Error(`Uploaded files are not declared by the dataset package: ${extra.join(", ")}`);

  const providers = Array.isArray(datasetPackage.sources)
    ? datasetPackage.sources.map((source) => source?.provider)
    : [datasetPackage.provider];
  if (providers.some((provider) => !isRecord(provider) || typeof provider.name !== "string" || typeof provider.terms !== "string")) {
    throw new Error("Every dataset source must declare provider name and license/terms");
  }
  return { researchRequest, datasetPackage, references };
}

export function summarizeIntakeResult(value) {
  const data = value?.data;
  const intake = data?.intake;
  const dataset = intake?.dataset;
  if (value?.ok !== true || value.command !== "project.intake" || typeof data?.manifest?.id !== "string" || !isRecord(dataset)) {
    throw new Error("Core did not return a successful Project intake receipt");
  }
  return {
    projectId: data.manifest.id,
    projectDir: data.projectDir,
    studyId: intake.study?.id || null,
    dataset: `${dataset.id}@${dataset.version}`,
    assetClass: dataset.assetClass,
    universe: dataset.universe,
    coverage: dataset.timeRange,
    datasetHash: intake.manifest?.datasetSnapshotHash || null,
  };
}
