import test from "node:test";
import assert from "node:assert/strict";
import { projectFactorManagement } from "../lib/factor-management.js";

function baseProject(overrides = {}) {
  return {
    id: "sample",
    name: "Sample",
    description: "sample project",
    rootDir: "/tmp/sample",
    valid: true,
    studies: [{ id: "ohlcv-factor-quality", name: "Factor", subjectKind: "factor" }],
    researchProgramStatus: null,
    factorExplorer: null,
    sessions: [],
    runReports: [],
    ...overrides,
  };
}

function lane() {
  return {
    id: "factor",
    name: "Factor quality",
    editablePaths: ["factors/**"],
    dependencyPaths: ["strategies/factor-claim.json"],
    study: {
      id: "ohlcv-factor-quality",
      name: "Factor Study",
      description: "study",
      inputHash: "input-hash",
      sourceHash: "source-hash",
      sourceHashes: { "factors/candidate.py": "src-file" },
      dependencyHash: "dependency-hash",
      dependencySourceHashes: { "strategies/factor-claim.json": "claim-hash" },
      datasetHash: "dataset-hash",
      objective: { metric: "validation_mean_ic", direction: "maximize", minimumImprovement: 0.01 },
      dataset: { id: "cn-equity", version: "2026.08", assetClass: "equity", universe: ["AAPL", "MSFT"], timeRange: { start: "2020-01-01", end: "2026-07-31" } },
    },
    latestRun: null,
    latestSession: null,
    currentAttempt: false,
    currentRun: false,
    reports: [],
    commands: [
      { id: "study.inspect", description: "Inspect factor study", display: "aq study inspect", effect: "read-only" },
      { id: "run.execute", description: "Create baseline Run", display: "aq run execute", effect: "creates-artifact" },
    ],
  };
}

function programBase(overrides = {}) {
  return {
    schemaVersion: "V1",
    kind: "autoquant-research-program-status",
    manifest: { id: "factor-portfolio-rl" },
    progression: { stage: "factor-evidence-required", focusLaneId: "factor", explanation: "factor gate pending", method: "report-bound-factor-portfolio-rl-admission-v1", selectionSplit: "validation", gates: [{ id: "factor-to-portfolio", upstreamLaneId: "factor", downstreamLaneId: "portfolio", status: "waiting-current-evidence", explanation: "no current run yet", selectionSplit: "validation" }] },
    lanes: [lane()],
    recommendedLaneId: "factor",
    recommendedAction: null,
    warnings: [],
    ...overrides,
  };
}

test("empty project returns honest empty state with no invented evidence", () => {
  const view = projectFactorManagement(baseProject());
  assert.equal(view.project?.id, "sample");
  assert.equal(view.programAvailable, false);
  assert.equal(view.status.phase, "unannounced");
  assert.equal(view.evidence.available, false);
  assert.equal(view.evidence.runId, null);
  assert.equal(view.cohorts, null);
  assert.equal(view.study, null);
  assert.equal(view.factorDefinition.studyId, "ohlcv-factor-quality");
  assert.equal(view.factorDefinition.subjectKind, "factor");
  assert.ok(!view.immutableReports.length);
  assert.equal(view.recommendedAction, null);
});

test("active Session filters factor activity by Study id and counts live campaigns from progress", () => {
  const program = programBase();
  const factorLane = program.lanes[0];
  factorLane.phase = "researching";
  factorLane.latestRun = { id: "RUN-1", status: "succeeded", studyId: "ohlcv-factor-quality" };
  factorLane.latestSession = { id: "SES-1", status: "active" };
  factorLane.currentAttempt = true;
  factorLane.currentRun = true;
  program.recommendedAction = factorLane.commands[1];
  const view = projectFactorManagement(baseProject({
    researchProgramStatus: program,
    sessions: [
      { session: { id: "SES-1", status: "active", studyId: "ohlcv-factor-quality" }, experiments: [{ id: "EXP-1", status: "running" }], campaigns: [{ id: "CAM-OLD", status: "completed" }], progress: [{ id: "CAM-1", status: "queued" }], reports: [] },
      { session: { id: "SES-OTHER", status: "active", studyId: "ohlcv-portfolio-quality" }, progress: [{ id: "CAM-9", status: "running" }], reports: [] },
    ],
  }));
  assert.equal(view.programAvailable, true);
  assert.equal(view.status.phase, "researching");
  assert.equal(view.status.currentRun, true);
  assert.equal(view.status.latestSessionActive, true);
  assert.equal(view.progress.activeSessions, 1);
  assert.equal(view.progress.experimentCount, 1);
  assert.equal(view.progress.activeCampaigns, 1);
  assert.equal(view.dependencies.editableCount, 1);
  assert.equal(view.dependencies.dependencyCount, 1);
  assert.equal(view.recommendedAction?.id, "run.execute");
  assert.equal(view.gates.factorToPortfolio?.id, "factor-to-portfolio");
});

test("reported lane records an immutable Report and reads cohort + qualification from the explorer", () => {
  const program = programBase();
  const factorLane = program.lanes[0];
  factorLane.phase = "reported";
  factorLane.latestRun = { id: "RUN-99", status: "succeeded", studyId: "ohlcv-factor-quality" };
  factorLane.latestSession = { id: "SES-9", status: "completed", leaderRunId: "RUN-99" };
  factorLane.currentAttempt = true;
  factorLane.currentRun = true;
  factorLane.reports = [{ id: "REP-9", studyId: "ohlcv-factor-quality", title: "Factor qualification", leaderRunId: "RUN-99", publishedAt: "2026-07-01T00:00:00Z" }];
  program.recommendedAction = factorLane.commands[1];
  const view = projectFactorManagement(baseProject({
    researchProgramStatus: program,
    factorExplorer: {
      run: { id: "RUN-99", status: "succeeded", studyId: "ohlcv-factor-quality" },
      summary: { validation: { meanRankIc: 0.04, rankIcir: 0.9, hacTStatistic: 2.1 }, testAudit: { meanRankIc: 0.03 }, meanCoverage: 0.8, meanRankTurnover: 0.2 },
      predictionUniverse: { evaluationMode: "cross-sectional", predictionAssets: ["AAPL", "MSFT"], contextAssets: ["SPY"], assetPredictionRoles: { AAPL: "tradable", MSFT: "tradable", SPY: "context" } },
      factorQualification: { available: true, diagnosis: { stage: "factor-qualification-positive", explanation: "raw + style-neutral + blend all positive", selectionSplit: "validation" }, validation: { weakestCandidateFold: { id: "validation_1", meanRankIc: 0.02 }, weakestStyleNeutralFold: { id: "validation_1", meanRankIc: 0.01 } } },
      inputAvailability: { observationCoverage: 0.97, minimumAssetsPerFactorTimestamp: 4, eligibleFactorTimestamps: [{ horizon: 1, timestamps: 100 }] },
      coverage: [{ asset: "AAPL", factorCoverage: 0.95 }],
    },
    runReports: [
      { id: "RUN-REP-1", studyId: "ohlcv-portfolio-quality", title: "Other lane", leaderRunId: "RUN-50", publishedAt: "2026-07-02T00:00:00Z" },
      { id: "RUN-REP-2", studyId: "ohlcv-factor-quality", title: "Factor run report", leaderRunId: "RUN-99", publishedAt: "2026-07-03T00:00:00Z" },
    ],
  }));
  assert.equal(view.status.phase, "reported");
  assert.equal(view.status.currentReportId, "REP-9");
  assert.equal(view.evidence.validationMeanIc, 0.04);
  assert.equal(view.evidence.qualificationStage, "factor-qualification-positive");
  assert.equal(view.cohorts.predictionAssets.join(","), "AAPL,MSFT");
  assert.equal(view.cohorts.contextAssets.join(","), "SPY");
  assert.equal(view.cohorts.evaluationMode, "cross-sectional");
  assert.deepEqual(view.immutableReports.map((report) => report.id), ["RUN-REP-2", "REP-9"]);
  assert.equal(view.evidence.primaryMetric, null);
  assert.equal(view.evidence.weakestCandidateFoldId, "validation_1");
});

test("missing explorer fills evidence with null fields and keeps the Study definition intact", () => {
  const program = programBase();
  program.recommendedLaneId = null;
  program.recommendedAction = null;
  const view = projectFactorManagement(baseProject({ researchProgramStatus: program, factorExplorer: null }));
  assert.equal(view.programAvailable, true);
  assert.equal(view.evidence.available, false);
  assert.equal(view.evidence.runId, null);
  assert.equal(view.evidence.validationMeanIc, null);
  assert.equal(view.evidence.qualificationStage, null);
  assert.equal(view.evidence.weakestCandidateFoldId, null);
  assert.equal(view.study?.id, "ohlcv-factor-quality");
  assert.equal(view.study?.dataset?.id, "cn-equity");
  assert.equal(view.study?.objective?.metric, "validation_mean_ic");
  assert.equal(view.cohorts, null);
  assert.equal(view.recommendedAction, null);
});
