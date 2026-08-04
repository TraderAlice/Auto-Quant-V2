import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { compareCohorts, hiddenEventSummary, visibleEvents } from "../lib/research.js";
import { coreFactorFrom, resolveCoreSnapshotUrl, validateCoreSnapshot } from "../lib/core-snapshot.js";
import { researchSubjectFromProject } from "../lib/research-subject.js";
import { selectRunTarget, summarizeRunResult } from "../lib/core-run.js";
import { safeSourcePath, selectIntakeTarget, summarizeIntakeResult, validateIntakeDocuments } from "../lib/core-intake.js";

const records = [
  { id: "a", availableAt: "2024-01-01T09:00:00Z", adapter: "news", reaction: 2, tags: ["x"] },
  { id: "b", availableAt: "2024-01-01T10:00:00Z", adapter: "filing", reaction: -1, tags: ["y"], visibilityReason: "delay" },
];

test("point-in-time visibility excludes future evidence", () => {
  assert.deepEqual(visibleEvents(records, "2024-01-01T09:30:00Z").map(({ id }) => id), ["a"]);
  assert.deepEqual(hiddenEventSummary(records, "2024-01-01T09:30:00Z"), { total: 1, reasons: { delay: 1 } });
});

test("cohort comparison requires members on both sides", () => {
  const ready = compareCohorts(records, ["a"], ["b"]);
  assert.equal(ready.ready, true);
  assert.equal(ready.reactionSpread, 3);
  assert.equal(compareCohorts(records, ["a"], []).ready, false);
});

test("Core snapshot bridge accepts only the fixed loopback read boundary", () => {
  assert.equal(resolveCoreSnapshotUrl(), "http://127.0.0.1:8765/api/v1/snapshot");
  assert.equal(resolveCoreSnapshotUrl("http://localhost:8877"), "http://localhost:8877/api/v1/snapshot");
  assert.throws(() => resolveCoreSnapshotUrl("https://example.com"), /loopback/);
  assert.throws(() => resolveCoreSnapshotUrl("http://user:secret@127.0.0.1:8765"), /loopback/);
});

test("connected evidence requires the public Studio snapshot identity", () => {
  const snapshot = validateCoreSnapshot({
    schemaVersion: 1,
    kind: "autoquant-studio-snapshot",
    generatedAt: "2026-08-02T00:00:00Z",
    harness: { version: "0.9.31", commit: "adc6363", sourceHash: "a".repeat(64) },
    source: { scope: "workspace", workspace: null },
    valid: true,
    diagnostics: [],
    projects: [{
      id: "factor-lab",
      name: "Factor Lab",
      description: "Bounded factor research",
      valid: true,
      agentWorkBriefHash: null,
      diagnostics: [],
      studies: [{ id: "quality", name: "Factor Quality", subjectKind: "factor", datasetHash: "b".repeat(64), dataset: { id: "ohlcv", version: "v1" } }],
    }],
  });
  assert.equal(coreFactorFrom(snapshot).id, "quality");
  assert.throws(() => validateCoreSnapshot({ ...snapshot, kind: "plugin-payload" }), /unsupported/);
  assert.throws(() => validateCoreSnapshot({ ...snapshot, harness: { version: "0.9.31" } }), /unsupported/);
  assert.throws(() => validateCoreSnapshot({ ...snapshot, projects: [{ id: "incomplete" }] }), /unsupported/);
});

test("research subject routing follows verified market semantics", () => {
  const base = { id: "factor", name: "Factor", subjectKind: "factor", datasetHash: "b".repeat(64) };
  const aShare = researchSubjectFromProject({ studies: [{
    ...base,
    dataset: { id: "cn", version: "v1", asset_class: "equity", universe: ["600000"], time_range: { start: "2024-01-01", end: "2024-12-31" } },
    datasetContext: { market: { clock: "session", calendar: "XSHG", timezone: "Asia/Shanghai" }, frequency: "1d", baseInterval: "1d", venues: ["SSE"], currencies: ["CNY"] },
  }] });
  const crypto = researchSubjectFromProject({ studies: [{
    ...base,
    dataset: { id: "crypto", version: "v1", asset_class: "crypto", universe: ["BTC-USDT"], time_range: { start: "2024-01-01", end: "2024-12-31" } },
    datasetContext: { market: { clock: "continuous", calendar: "24/7", timezone: "UTC" }, baseInterval: "1h", venues: ["BINANCE"], currencies: ["USDT"] },
  }] });
  assert.equal(aShare.profileId, "a-share-equity");
  assert.deepEqual(aShare.adapters, ["A 股公告", "财经新闻"]);
  assert.match(aShare.replay[0], /交易日/);
  assert.match(aShare.diagnostics[0], /Rank IC/);
  assert.equal(crypto.profileId, "crypto");
  assert.equal(crypto.interval, "1h");
  assert.match(crypto.replay[0], /24\/7 UTC/);
});

test("unknown subject semantics remain explicit instead of inferred", () => {
  const subject = researchSubjectFromProject({ studies: [{
    id: "factor",
    name: "Synthetic factor",
    subjectKind: "factor",
    dataset: { id: "synthetic", version: "v1", asset_class: "synthetic-multi-asset", universe: ["ALPHA"], time_range: { start: "2024-01-01", end: "2024-12-31" } },
  }] });
  assert.equal(subject.profileId, "mixed");
  assert.ok(subject.unresolved.includes("市场时钟"));
  assert.ok(subject.unresolved.includes("场所"));
});

test("connected Results projects the verified Core explorer instead of demo evidence", async () => {
  const shell = await readFile(new URL("../components/studio-shell.jsx", import.meta.url), "utf8");
  const results = await readFile(new URL("../app/results/page.jsx", import.meta.url), "utf8");
  assert.match(shell, /connectedRoutes = new Set\(\[[^\]]*"\/results"/);
  assert.match(results, /const explorer = project\?\.factorExplorer/);
  assert.match(results, /<FactorIcChart path=\{explorer\.icPath\}/);
  assert.match(results, /Validation Rank IC/);
});

test("research execution accepts only a verified project Study and returns a compact receipt", () => {
  const snapshot = {
    projects: [{ id: "desk", valid: true, rootDir: "C:/desk", studies: [{ id: "factor-quality" }] }],
  };
  assert.equal(selectRunTarget({ projectId: "desk", studyId: "factor-quality" }, snapshot).studyId, "factor-quality");
  assert.throws(() => selectRunTarget({ projectId: "desk", studyId: "unknown" }, snapshot), /not part/);
  assert.throws(() => selectRunTarget({ projectId: "desk", studyId: "../bad" }, snapshot), /valid studyId/);
  assert.deepEqual(summarizeRunResult({ ok: true, data: { id: "run-1", status: "succeeded", summary: "done", study: { id: "factor-quality" }, objective: { metric: "ic" }, metrics: { ic: 0.12 } } }), {
    id: "run-1", studyId: "factor-quality", status: "succeeded", summary: "done", metric: "ic", value: 0.12,
  });
  assert.deepEqual(summarizeRunResult({ ok: true, command: "job.execute", data: { id: "job-1", status: "succeeded", study: { id: "factor-quality" }, runRef: { id: "run-2" }, executor: { kind: "cpu", provider: "builtin" }, tradingAuthority: "none" } }), {
    id: "run-2", studyId: "factor-quality", status: "succeeded", jobId: "job-1", executor: { kind: "cpu", provider: "builtin" }, tradingAuthority: "none",
  });
});

test("all approved research routes retain a connected Core projection", async () => {
  const shell = await readFile(new URL("../components/studio-shell.jsx", import.meta.url), "utf8");
  for (const route of ["/factors", "/strategies", "/events", "/lab", "/results", "/data", "/audit"]) {
    assert.match(shell, new RegExp(`connectedRoutes = new Set\\(\\[[^\\]]*"${route}"`));
  }
});

test("price-data intake accepts only declared confined files in a verified Workspace", () => {
  const workspaceRoot = path.resolve("workspace");
  const snapshot = {
    source: { scope: "workspace", rootDir: workspaceRoot, workspace: { projectsDir: path.join(workspaceRoot, "projects") } },
    projects: [{ id: "existing" }],
  };
  const target = selectIntakeTarget({ projectId: "strategy-audit", template: "ohlcv-research-desk" }, snapshot);
  assert.equal(target.workspaceRoot, workspaceRoot);
  assert.throws(() => selectIntakeTarget({ projectId: "existing", template: "ohlcv-factor-lab" }, snapshot), /already exists/);
  assert.throws(() => selectIntakeTarget({ projectId: "../escape", template: "ohlcv-factor-lab" }, snapshot), /projectId/);
  assert.equal(safeSourcePath("raw/AAPL.csv"), "raw/AAPL.csv");
  assert.throws(() => safeSourcePath("../AAPL.csv"), /Unsafe/);
  assert.throws(() => safeSourcePath("AAPL.exe"), /Unsupported/);

  const request = JSON.stringify({ kind: "autoquant-research-request" });
  const dataset = JSON.stringify({
    kind: "autoquant-ohlcv-dataset-package",
    provider: { name: "local export", terms: "user supplied for local research" },
    assets: [{ path: "AAPL.csv" }, { path: "MSFT.parquet" }],
  });
  assert.deepEqual(validateIntakeDocuments(request, dataset, ["AAPL.csv", "MSFT.parquet"]).references, ["AAPL.csv", "MSFT.parquet"]);
  assert.throws(() => validateIntakeDocuments(request, dataset, ["AAPL.csv"]), /missing files/);
  assert.throws(() => validateIntakeDocuments(request, dataset, ["AAPL.csv", "MSFT.parquet", "secret.json"]), /not declared/);
});

test("intake mutation boundary uses argv execution and returns a compact receipt", async () => {
  const route = await readFile(new URL("../app/api/studio/intake/route.js", import.meta.url), "utf8");
  assert.match(route, /execFileAsync\("uv", args/);
  assert.match(route, /valid Content-Length/);
  assert.ok(route.indexOf("valid Content-Length") < route.indexOf("request.formData()"));
  assert.doesNotMatch(route, /shell\s*:/);
  assert.doesNotMatch(route, /form\.get\("command"\)/);
  assert.deepEqual(summarizeIntakeResult({
    ok: true,
    command: "project.intake",
    data: {
      projectDir: "C:/workspace/projects/audit",
      manifest: { id: "audit" },
      intake: {
        study: { id: "ohlcv-factor-quality" },
        manifest: { datasetSnapshotHash: "abc" },
        dataset: { id: "market", version: "v1", assetClass: "equity", universe: ["AAPL"], timeRange: { start: "2024-01-01", end: "2024-12-31" } },
      },
    },
  }), {
    projectId: "audit",
    projectDir: "C:/workspace/projects/audit",
    studyId: "ohlcv-factor-quality",
    dataset: "market@v1",
    assetClass: "equity",
    universe: ["AAPL"],
    coverage: { start: "2024-01-01", end: "2024-12-31" },
    datasetHash: "abc",
  });
});

test("event intake keeps provider payloads local and invokes only the fixed Core command", async () => {
  const route = await readFile(new URL("../app/api/studio/event-intake/route.js", import.meta.url), "utf8");
  assert.match(route, /\["run", "aq", "event", "intake"/);
  assert.match(route, /ADAPTERS = new Set/);
  assert.match(route, /valid Content-Length/);
  assert.ok(route.indexOf("valid Content-Length") < route.indexOf("request.formData()"));
  assert.doesNotMatch(route, /shell\s*:/);
  assert.doesNotMatch(route, /form\.get\("command"\)/);
});

test("external claim verification invokes only the fixed factor evidence command", async () => {
  const route = await readFile(new URL("../app/api/studio/verify-factor/route.js", import.meta.url), "utf8");
  const results = await readFile(new URL("../app/results/page.jsx", import.meta.url), "utf8");
  assert.match(route, /\["run", "aq", "verify", "factor"/);
  assert.doesNotMatch(route, /shell\s*:/);
  assert.match(results, /<ClaimVerificationForm/);
  assert.match(results, /verificationAssessments/);
});

test("governed RL page exposes the Core supervised-model runtime without fake results", async () => {
  const lane = await readFile(new URL("../components/research-lane.jsx", import.meta.url), "utf8");
  assert.match(lane, /监督式 ML 运行时/);
  assert.match(lane, /modelRuntime\?\.entrypoint/);
  assert.match(lane, /Core 能力声明，不伪造模型结果/);
});

test("public Mantine primitives back generic UI without replacing AutoQuant domain semantics", async () => {
  const packageJson = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
  const layout = await readFile(new URL("../app/layout.jsx", import.meta.url), "utf8");
  const ui = await readFile(new URL("../components/ui.jsx", import.meta.url), "utf8");
  assert.equal(packageJson.dependencies["@mantine/core"], "9.5.1");
  assert.equal(packageJson.dependencies["@mantine/hooks"], "9.5.1");
  assert.match(layout, /<MantineProvider/);
  for (const primitive of ["Button", "ButtonLink", "EmptyState", "FormField", "DataTable"]) {
    assert.match(ui, new RegExp(`export function ${primitive}`));
  }
  assert.doesNotMatch(ui, /@katana|dockview|mcp__/i);
  });

test("Designer Pipeline nav groups replace legacy Research/Infrastructure sections", async () => {
  const shell = await readFile(new URL("../components/studio-shell.jsx", import.meta.url), "utf8");
  // Four group keys present in the designerPipeline object
  for (const group of ["Work", "Assets", "Evidence", "Operations"]) {
    assert.match(shell, new RegExp(`^\\s+${group}:\\s+\\[`, "m"), `${group} group missing from designerPipeline`);
  }
  // The nav renders sections dynamically via Object.entries, not hardcoded strings
  assert.match(shell, /Object\.entries\(designerPipeline\)\.map/);
  assert.match(shell, /<span className="nav-section">\{section\}<\/span>/);
  // All eight main hrefs are in the designerPipeline object
  for (const href of ["/research", "/data", "/factors", "/strategies", "/replay", "/results", "/jobs", "/audit"]) {
    assert.match(shell, new RegExp(`"${href}"`), `${href} missing from shell`);
  }
  // Legacy section titles are no longer rendered as static nav-section
  assert.doesNotMatch(shell, /<span className="nav-section">Research<\/span>/);
  assert.doesNotMatch(shell, /<span className="nav-section">Infrastructure<\/span>/);
  // connectedRoutes retains all existing routes unchanged
  for (const route of ["/", "/research", "/factors", "/strategies", "/replay", "/events", "/lab", "/results", "/portfolio", "/rl", "/jobs", "/data", "/audit"]) {
    assert.match(shell, new RegExp(`connectedRoutes = new Set\\(\\[[^\\]]*"${route}"`), `${route} missing from connectedRoutes`);
  }
});
