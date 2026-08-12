import test from "node:test";
import assert from "node:assert/strict";
import { strategyManagementFromProject } from "../lib/strategy-management.js";

function project(overrides = {}) {
  return {
    id: "sample",
    runs: [],
    sessions: [],
    researchProgramStatus: null,
    portfolioExplorer: null,
    rlExplorer: null,
    dossierStatus: null,
    ...overrides,
  };
}

function lane(id, studyId, optional = false) {
  return {
    id,
    name: id,
    optional,
    phase: "reported",
    editablePaths: [`${id}/**`],
    dependencyPaths: ["factors/**"],
    study: { id: studyId, objective: { metric: id === "portfolio" ? "validation_net_sharpe" : "validation_mean_net_sharpe" } },
    latestRun: { id: `RUN-${id}`, status: "succeeded", value: 0.4 },
    latestSession: { id: `SES-${id}`, status: "completed" },
    currentAttempt: true,
    currentRun: true,
    reports: [{ id: `REP-${id}` }],
    commands: [{ id: "run.show", display: "aq run show", effect: "read-only" }],
  };
}

function program() {
  return {
    manifest: {
      lanes: [
        { id: "factor", name: "Factor", studyId: "factor-study", optional: false, dependsOn: [], editablePaths: ["factors/**"], dependencyPaths: [] },
        { id: "portfolio", name: "Portfolio", studyId: "portfolio-study", optional: false, dependsOn: ["factor"], editablePaths: ["portfolio/**"], dependencyPaths: ["factors/**"] },
        { id: "rl", name: "RL", studyId: "rl-study", optional: true, dependsOn: ["portfolio"], editablePaths: ["rl/**"], dependencyPaths: ["factors/**"] },
      ],
      integration: { factorToPortfolio: "shared-candidate-source", rlFactorDependency: "content-locked-candidate-source" },
    },
    lanes: [lane("factor", "factor-study"), lane("portfolio", "portfolio-study"), lane("rl", "rl-study", true)],
    progression: {
      method: "report-bound",
      stage: "required-research-complete",
      focusLaneId: null,
      optionalLaneId: "rl",
      explanation: "required chain complete",
      selectionSplit: "validation",
      gates: [{ id: "portfolio-to-rl", status: "passed" }],
    },
    recommendedLaneId: "rl",
    recommendedAction: { id: "study.inspect", display: "aq study inspect", effect: "read-only" },
  };
}

test("missing program stays unannounced without invented contracts", () => {
  const view = strategyManagementFromProject(project());
  assert.equal(view.programAvailable, false);
  assert.equal(view.progression.stage, null);
  assert.equal(view.composition, null);
  assert.deepEqual(view.laneBoundaries, []);
  assert.equal(view.portfolio.available, false);
  assert.equal(view.rl.available, false);
});

test("projects portfolio and optional RL lanes from Core", () => {
  const view = strategyManagementFromProject(project({ researchProgramStatus: program() }));
  assert.equal(view.portfolio.studyId, "portfolio-study");
  assert.equal(view.portfolio.primaryMetric, "validation_net_sharpe");
  assert.equal(view.rl.optional, true);
  assert.equal(view.progression.stage, "required-research-complete");
  assert.equal(view.composition.factorToPortfolio, "shared-candidate-source");
  assert.equal(view.laneBoundaries.length, 3);
  assert.equal(view.recommended.command.id, "study.inspect");
});

test("counts immutable session history and active campaign progress separately", () => {
  const view = strategyManagementFromProject(project({
    researchProgramStatus: program(),
    sessions: [
      { session: { studyId: "portfolio-study" }, experiments: [{ id: "E1" }], progress: [{ id: "LIVE" }], campaigns: [{ id: "DONE-1" }, { id: "DONE-2" }] },
      { session: { studyId: "rl-study" }, experiments: [], progress: [], campaigns: [{ id: "DONE-3" }] },
      { session: { studyId: "factor-study" }, progress: [{ id: "OTHER" }] },
    ],
  }));
  assert.equal(view.portfolio.sessionCount, 1);
  assert.equal(view.portfolio.experimentCount, 1);
  assert.equal(view.portfolio.liveCampaignCount, 1);
  assert.equal(view.portfolio.terminalCampaignCount, 2);
  assert.equal(view.rl.terminalCampaignCount, 1);
  assert.equal(view.artifacts.sessions, 2);
});

test("uses explorer evidence only when Core provides it", () => {
  const view = strategyManagementFromProject(project({
    researchProgramStatus: program(),
    portfolioExplorer: {
      run: { id: "RUN-portfolio", primaryMetric: "validation_net_sharpe", primaryValue: 0.61 },
      artifacts: { report: {}, weights: {} },
      liquidityCapacity: { status: "bounded" },
      strategyViability: { status: "positive" },
    },
    rlExplorer: {
      run: { id: "RUN-rl", objective: { metric: "validation_mean_net_sharpe" } },
      artifacts: { policy: {} },
      protocol: { folds: ["F1", "F2"], seeds: [7, 11, 13] },
      summary: { rlAddedValidationValue: true, meanValidationAdvantageVsBestBaseline: 0.03, trialCount: 6 },
    },
    modelRuntime: { available: true, models: ["ridge-linear"], selectionAuthority: "validation-only", testUse: "terminal-audit-only" },
    modelRuns: [{ id: "MODEL-1", result: { selectedModel: "ridge-linear" } }],
    externalHoldout: { state: "assessed", binding: { id: "HOLD-1" }, result: { id: "HOLD-RUN-1" }, assessment: { verdict: "stable" } },
  }));
  assert.equal(view.portfolio.primaryValue, 0.61);
  assert.equal(view.portfolio.artifactCount, 2);
  assert.equal(view.rl.rlValueAdded, true);
  assert.equal(view.rl.meanValidationAdvantage, 0.03);
  assert.equal(view.rl.foldCount, 2);
  assert.equal(view.rl.seedCount, 3);
  assert.equal(view.artifacts.explorations, 2);
  assert.equal(view.model.selectedModel, "ridge-linear");
  assert.equal(view.holdout.state, "assessed");
});

test("projects dossier status without synthesizing readiness", () => {
  const view = strategyManagementFromProject(project({
    dossierStatus: {
      ready: false,
      latestDossier: { id: "DOS-1" },
      includedLaneIds: ["factor", "portfolio"],
      omittedOptionalLanes: ["rl"],
      blockers: [{ code: "rl-optional" }],
      nextAction: null,
    },
  }));
  assert.equal(view.dossier.available, true);
  assert.equal(view.dossier.ready, false);
  assert.equal(view.dossier.latestDossier.id, "DOS-1");
  assert.deepEqual(view.dossier.omittedOptionalLanes, ["rl"]);
});
