import test from "node:test";
import assert from "node:assert/strict";
import { compareCohorts, hiddenEventSummary, visibleEvents } from "../lib/research.js";
import { coreFactorFrom, resolveCoreSnapshotUrl, validateCoreSnapshot } from "../lib/core-snapshot.js";

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
