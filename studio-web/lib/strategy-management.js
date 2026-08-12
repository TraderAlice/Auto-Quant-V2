const LANE_IDS = ["portfolio", "rl"];

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function list(value) {
  return Array.isArray(value) ? value : [];
}

function sessionStats(project, studyId) {
  const wrappers = studyId
    ? list(project?.sessions).filter((item) => item?.session?.studyId === studyId)
    : [];
  return wrappers.reduce(
    (stats, item) => ({
      sessions: stats.sessions + 1,
      experiments: stats.experiments + list(item.experiments).length,
      liveCampaigns: stats.liveCampaigns + list(item.progress).length,
      terminalCampaigns: stats.terminalCampaigns + list(item.campaigns).length,
      reports: stats.reports + list(item.reports).length,
    }),
    { sessions: 0, experiments: 0, liveCampaigns: 0, terminalCampaigns: 0, reports: 0 },
  );
}

function emptyLane(id, optional) {
  return {
    id,
    optional,
    available: false,
    studyId: null,
    phase: "unannounced",
    currentAttempt: false,
    currentRun: false,
    latestRun: null,
    latestSession: null,
    primaryMetric: null,
    primaryValue: null,
    reportCount: 0,
    sessionCount: 0,
    experimentCount: 0,
    liveCampaignCount: 0,
    terminalCampaignCount: 0,
    editablePaths: [],
    dependencyPaths: [],
    commands: [],
    artifactCount: 0,
    liquidityCapacity: null,
    strategyViability: null,
    executedBookRisk: null,
    rlValueAdded: null,
    meanValidationAdvantage: null,
    failureRate: null,
    trialCount: null,
    meanValidationCostDrag: null,
    meanValidationOneWayTurnover: null,
    foldCount: 0,
    seedCount: 0,
  };
}

function laneProjection(project, lane, explorer, id) {
  if (!isObject(lane)) return emptyLane(id, id === "rl");
  const study = isObject(lane.study) ? lane.study : null;
  const stats = sessionStats(project, study?.id);
  const run = isObject(explorer?.run) ? explorer.run : null;
  const summary = isObject(explorer?.summary) ? explorer.summary : null;
  const protocol = isObject(explorer?.protocol) ? explorer.protocol : null;
  return {
    ...emptyLane(id, lane.optional === true || id === "rl"),
    id,
    available: true,
    studyId: study?.id || null,
    phase: lane.phase || "unspecified",
    currentAttempt: lane.currentAttempt === true,
    currentRun: lane.currentRun === true,
    latestRun: isObject(lane.latestRun) ? lane.latestRun : null,
    latestSession: isObject(lane.latestSession) ? lane.latestSession : null,
    primaryMetric: run?.primaryMetric || run?.objective?.metric || study?.objective?.metric || null,
    primaryValue: run?.primaryValue ?? lane.latestRun?.value ?? null,
    reportCount: list(lane.reports).length,
    sessionCount: stats.sessions,
    experimentCount: stats.experiments,
    liveCampaignCount: stats.liveCampaigns,
    terminalCampaignCount: stats.terminalCampaigns,
    editablePaths: list(lane.editablePaths),
    dependencyPaths: list(lane.dependencyPaths),
    commands: list(lane.commands),
    artifactCount: isObject(explorer?.artifacts) ? Object.keys(explorer.artifacts).length : 0,
    liquidityCapacity: isObject(explorer?.liquidityCapacity) ? explorer.liquidityCapacity : null,
    strategyViability: isObject(explorer?.strategyViability) ? explorer.strategyViability : null,
    executedBookRisk: isObject(explorer?.executedBookRisk) ? explorer.executedBookRisk : null,
    rlValueAdded: typeof summary?.rlAddedValidationValue === "boolean" ? summary.rlAddedValidationValue : null,
    meanValidationAdvantage: summary?.meanValidationAdvantageVsBestBaseline ?? null,
    failureRate: summary?.failureRate ?? null,
    trialCount: summary?.trialCount ?? null,
    meanValidationCostDrag: summary?.meanValidationCostDrag ?? null,
    meanValidationOneWayTurnover: summary?.meanValidationOneWayTurnover ?? null,
    foldCount: list(protocol?.folds).length,
    seedCount: list(protocol?.seeds).length,
  };
}

function laneBoundaries(program) {
  if (!isObject(program)) return [];
  const statusById = new Map(list(program.lanes).map((lane) => [lane?.id, lane]));
  return list(program.manifest?.lanes).map((lane) => {
    const status = statusById.get(lane?.id);
    return {
      id: lane?.id || null,
      name: lane?.name || status?.name || null,
      studyId: lane?.studyId || status?.study?.id || null,
      optional: lane?.optional === true,
      dependsOn: list(lane?.dependsOn),
      editablePaths: list(lane?.editablePaths),
      dependencyPaths: list(lane?.dependencyPaths),
    };
  });
}

function dossierProjection(value) {
  if (!isObject(value)) {
    return { available: false, ready: false, latestDossier: null, includedLaneIds: [], omittedOptionalLanes: [], blockers: [], nextAction: null };
  }
  return {
    available: true,
    ready: value.ready === true,
    latestDossier: isObject(value.latestDossier) ? value.latestDossier : null,
    includedLaneIds: list(value.includedLaneIds),
    omittedOptionalLanes: list(value.omittedOptionalLanes).map((item) => (
      isObject(item) ? { id: item.id || null, reason: item.reason || null } : item
    )),
    blockers: list(value.blockers),
    nextAction: isObject(value.nextAction) ? value.nextAction : null,
  };
}

export function strategyManagementFromProject(project) {
  const program = isObject(project?.researchProgramStatus) ? project.researchProgramStatus : null;
  const statusById = new Map(list(program?.lanes).map((lane) => [lane?.id, lane]));
  const portfolio = laneProjection(project, statusById.get("portfolio"), project?.portfolioExplorer, "portfolio");
  const rl = laneProjection(project, statusById.get("rl"), project?.rlExplorer, "rl");
  const progression = isObject(program?.progression) ? program.progression : null;
  const recommendedAction = isObject(program?.recommendedAction) ? program.recommendedAction : null;
  const studyIds = new Set([portfolio.studyId, rl.studyId].filter(Boolean));
  const modelRuntime = isObject(project?.modelRuntime) ? project.modelRuntime : null;
  const modelRuns = list(project?.modelRuns);
  const latestModelRun = modelRuns[modelRuns.length - 1] || null;
  const holdout = isObject(project?.externalHoldout) ? project.externalHoldout : null;

  return {
    projectId: project?.id || null,
    programAvailable: Boolean(program),
    progression: {
      method: progression?.method || null,
      stage: progression?.stage || null,
      focusLaneId: progression?.focusLaneId || null,
      optionalLaneId: progression?.optionalLaneId || null,
      explanation: progression?.explanation || null,
      selectionSplit: progression?.selectionSplit || null,
      gates: list(progression?.gates),
    },
    portfolio,
    rl,
    composition: isObject(program?.manifest?.integration) ? program.manifest.integration : null,
    laneBoundaries: laneBoundaries(program),
    recommended: {
      available: Boolean(recommendedAction),
      laneId: program?.recommendedLaneId || null,
      command: recommendedAction,
    },
    dossier: dossierProjection(project?.dossierStatus),
    model: {
      available: modelRuntime?.available === true,
      entrypoint: modelRuntime?.entrypoint || null,
      candidates: list(modelRuntime?.models),
      selectionAuthority: modelRuntime?.selectionAuthority || null,
      testUse: modelRuntime?.testUse || null,
      latestRun: isObject(latestModelRun) ? latestModelRun : null,
      selectedModel: latestModelRun?.result?.selectedModel || latestModelRun?.selectedModel || null,
    },
    holdout: {
      available: Boolean(holdout),
      state: holdout?.state || null,
      bindingId: holdout?.binding?.id || null,
      resultId: holdout?.result?.id || null,
      assessment: isObject(holdout?.assessment) ? holdout.assessment : null,
    },
    artifacts: {
      runs: list(project?.runs).filter((run) => studyIds.has(run?.studyId)).length,
      sessions: portfolio.sessionCount + rl.sessionCount,
      reports: portfolio.reportCount + rl.reportCount,
      explorations: Number(isObject(project?.portfolioExplorer)) + Number(isObject(project?.rlExplorer)),
    },
  };
}
