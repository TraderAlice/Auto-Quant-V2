const FACTOR_LANE_ID = "factor";
const FACTOR_GATE_ID = "factor-to-portfolio";

const PHASE_TONES = {
  reported: "known", "baseline-ready": "known",
  researching: "delayed", stale: "delayed",
  "scientific-limit": "restricted", "repair-required": "restricted",
  "not-started": "partial",
};

const NULL_EVIDENCE = {
  available: false, runId: null, runStatus: null, runStudyId: null,
  validationMeanIc: null, validationIcir: null, validationHacT: null,
  primaryMetric: null, meanCoverage: null, meanRankTurnover: null, observationCoverage: null,
  coverage: [], qualificationAvailable: false, qualificationStage: null,
  qualificationExplanation: null, weakestCandidateFoldId: null,
  weakestCandidateFoldIc: null, weakestStyleNeutralFoldId: null,
  weakestStyleNeutralFoldIc: null, eligibleFactorTimestamps: [], warning: null,
};

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
function pickArray(value) {
  return Array.isArray(value) ? value : [];
}

function resolveLane(program) {
  if (!isObject(program)) return null;
  return pickArray(program.lanes).find((item) => isObject(item) && item.id === FACTOR_LANE_ID) || null;
}

function isFactorSession(item, lane) {
  const session = isObject(item?.session) ? item.session : null;
  if (!session?.studyId || !lane?.study?.id) return false;
  return session.studyId === lane.study.id;
}

function resolveProgress(project, lane) {
  const items = pickArray(project?.sessions).filter((item) => isFactorSession(item, lane));
  let activeSessions = 0, completedSessions = 0, experimentCount = 0, activeCampaigns = 0;
  for (const item of items) {
    const isActive = item.session?.status === "active";
    if (isActive) activeSessions += 1;
    else completedSessions += 1;
    experimentCount += pickArray(item.experiments).length;
    if (isActive) activeCampaigns += pickArray(item.progress).length;
  }
  const latestSession = isObject(lane?.latestSession) ? lane.latestSession : null;
  return {
    activeSessions, completedSessions, experimentCount, activeCampaigns,
    laneLatestSession: latestSession,
    laneLatestSessionActive: latestSession?.status === "active",
  };
}
function resolveReports(project, lane) {
  const items = [];
  for (const [label, list] of [["lane", pickArray(lane?.reports)], ["run", pickArray(project?.runReports)]]) {
    for (const report of list) {
      if (!isObject(report) || (label === "run" && report.studyId !== lane?.study?.id)) continue;
      items.push({
        id: report.id || null, studyId: report.studyId || null, title: report.title || null,
        leaderRunId: report.leaderRunId || null, publishedAt: report.publishedAt || null, source: label,
      });
    }
  }
  return items.sort((left, right) => (Date.parse(right.publishedAt || "") || 0) - (Date.parse(left.publishedAt || "") || 0));
}

function resolveCohorts(explorer) {
  if (!isObject(explorer)) return null;
  const universe = isObject(explorer.predictionUniverse) ? explorer.predictionUniverse : null;
  if (!universe) {
    return { available: false, evaluationMode: null, predictionAssets: [], contextAssets: [], assetCount: 0 };
  }
  const predictionAssets = pickArray(universe.predictionAssets);
  const contextAssets = pickArray(universe.contextAssets);
  return {
    available: true, evaluationMode: universe.evaluationMode || null,
    predictionAssets, contextAssets,
    assetCount: predictionAssets.length + contextAssets.length,
  };
}

function resolveEvidence(explorer) {
  if (!isObject(explorer)) return { ...NULL_EVIDENCE };
  const run = isObject(explorer.run) ? explorer.run : null;
  const summary = isObject(explorer.summary) ? explorer.summary : null;
  const qualification = isObject(explorer.factorQualification) ? explorer.factorQualification : null;
  const availability = isObject(explorer.inputAvailability) ? explorer.inputAvailability : null;
  const validation = isObject(qualification?.validation) ? qualification.validation : null;
  const candidate = isObject(validation?.weakestCandidateFold) ? validation.weakestCandidateFold : null;
  const neutral = isObject(validation?.weakestStyleNeutralFold) ? validation.weakestStyleNeutralFold : null;
  return {
    ...NULL_EVIDENCE, available: true,
    runId: run?.id || null, runStatus: run?.status || null, runStudyId: run?.studyId || null,
    primaryMetric: run?.primaryMetric || run?.objective?.metric || null,
    validationMeanIc: summary?.validation?.meanRankIc ?? null,
    validationIcir: summary?.validation?.rankIcir ?? null,
    validationHacT: summary?.validation?.hacTStatistic ?? null,
    meanCoverage: summary?.meanCoverage ?? null, meanRankTurnover: summary?.meanRankTurnover ?? null,
    observationCoverage: availability?.observationCoverage ?? null,
    coverage: pickArray(explorer.coverage),
    eligibleFactorTimestamps: pickArray(availability?.eligibleFactorTimestamps),
    qualificationAvailable: qualification?.available === true,
    qualificationStage: qualification?.diagnosis?.stage || null,
    qualificationExplanation: qualification?.diagnosis?.explanation || null,
    weakestCandidateFoldId: candidate?.id || null, weakestCandidateFoldIc: candidate?.meanRankIc ?? null,
    weakestStyleNeutralFoldId: neutral?.id || null, weakestStyleNeutralFoldIc: neutral?.meanRankIc ?? null,
    warning: typeof explorer.warning === "string" ? explorer.warning : null,
  };
}

function resolveCurrentReportId(lane) {
  if (!isObject(lane) || !isObject(lane.latestRun) || lane.currentRun !== true) return null;
  const reports = pickArray(lane.reports);
  for (let index = reports.length - 1; index >= 0; index -= 1) {
    const report = reports[index];
    if (isObject(report) && report.leaderRunId === lane.latestRun.id) return report.id || null;
  }
  return null;
}

function resolveRecommendedAction(program) {
  if (!isObject(program)) return null;
  if (program.recommendedLaneId === FACTOR_LANE_ID && isObject(program.recommendedAction)) {
    return program.recommendedAction;
  }
  return null;
}

function buildStudy(study) {
  return {
    id: study.id, name: study.name || null, description: study.description || null,
    inputHash: study.inputHash || null, sourceHash: study.sourceHash || null,
    sourceHashes: isObject(study.sourceHashes) ? study.sourceHashes : {},
    dependencyHash: study.dependencyHash || null,
    dependencySourceHashes: isObject(study.dependencySourceHashes) ? study.dependencySourceHashes : {},
    datasetHash: study.datasetHash || null,
    objective: isObject(study.objective) ? study.objective : null,
    dataset: isObject(study.dataset) ? study.dataset : null,
    datasetTimeRange: study.dataset?.timeRange || study.dataset?.time_range || null,
  };
}

export function projectFactorManagement(project) {
  const program = isObject(project?.researchProgramStatus) ? project.researchProgramStatus : null;
  const lane = program ? resolveLane(program) : null;
  const explorer = isObject(project?.factorExplorer) ? project.factorExplorer : null;
  const study = isObject(lane?.study) ? lane.study : null;
  const progression = isObject(program?.progression) ? program.progression : null;
  const editablePaths = pickArray(lane?.editablePaths);
  const dependencyPaths = pickArray(lane?.dependencyPaths);
  const sourceStudy = pickArray(project?.studies).find(
    (item) => isObject(item) && (item.id === study?.id || item.subjectKind === "factor"),
  ) || null;
  const phase = lane?.phase || (program ? "unspecified" : "unannounced");
  const factorGate = pickArray(progression?.gates).find((item) => isObject(item) && item.id === FACTOR_GATE_ID) || null;

  return {
    project: project ? { id: project.id || null, name: project.name || null, description: project.description || null, rootDir: project.rootDir || null, valid: project.valid === true } : null,
    programAvailable: Boolean(program),
    program: program ? { stage: progression?.stage || null, focusLaneId: progression?.focusLaneId || null, explanation: progression?.explanation || null, method: progression?.method || null, selectionSplit: progression?.selectionSplit || null } : null,
    factorDefinition: {
      studyId: study?.id || sourceStudy?.id || null,
      studyName: study?.name || sourceStudy?.name || null,
      description: study?.description || sourceStudy?.description || null,
      subjectKind: sourceStudy?.subjectKind || "factor",
    },
    study: study ? buildStudy(study) : null,
    dependencies: { editablePaths, dependencyPaths, editableCount: editablePaths.length, dependencyCount: dependencyPaths.length },
    cohorts: resolveCohorts(explorer),
    evidence: resolveEvidence(explorer),
    progress: resolveProgress(project, lane),
    immutableReports: resolveReports(project, lane),
    commands: pickArray(lane?.commands),
    recommendedAction: resolveRecommendedAction(program),
    gates: { factorToPortfolio: factorGate, focusLaneId: progression?.focusLaneId || null },
    warnings: pickArray(program?.warnings),
    status: {
      phase, tone: PHASE_TONES[phase] || "partial",
      currentRun: lane?.currentRun === true, currentAttempt: lane?.currentAttempt === true,
      currentReportId: resolveCurrentReportId(lane),
      latestSessionId: lane?.latestSession?.id || null,
      latestSessionActive: lane?.latestSession?.status === "active",
    },
  };
}
