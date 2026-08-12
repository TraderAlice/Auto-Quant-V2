const SUPPORTED_STAGES = new Set([
  "decision-signal-positive",
  "factor-qualification-positive",
  "known-style-validation-positive",
  "risk-forecast-positive",
]);

const CONTRADICTED_STAGES = new Set([
  "blend-uplift-absent",
  "known-style-identity-mismatch",
  "raw-predictive-edge-absent",
  "style-neutral-edge-absent",
]);

const VERDICTS = {
  supported: { label: "证据支持", state: "known" },
  contradicted: { label: "证据反驳", state: "missing" },
  inconclusive: { label: "证据不足", state: "partial" },
  "invalid-test": { label: "测试无效", state: "restricted" },
};

function latestSelectionIntegrity(project, runId) {
  return [...(project?.sessions || [])]
    .reverse()
    .find((item) => item?.session?.leader?.runId === runId && item?.selectionIntegrity)
    ?.selectionIntegrity || null;
}

function qualificationVerdict(qualification, run, diagnostics) {
  if (diagnostics.length || (run && run.status !== "succeeded")) return "invalid-test";
  if (!run || !qualification?.available) return "inconclusive";
  if (qualification.tradingAuthority !== "none") return "invalid-test";
  const stage = qualification.diagnosis?.stage;
  if (SUPPORTED_STAGES.has(stage)) return "supported";
  if (CONTRADICTED_STAGES.has(stage)) return "contradicted";
  return "inconclusive";
}

export function factorVerificationFrom(project, snapshotDiagnostics = []) {
  const explorer = project?.factorExplorer;
  const run = explorer?.run || null;
  const qualification = explorer?.factorQualification || null;
  const selectionIntegrity = latestSelectionIntegrity(project, run?.id);
  const adjustment = selectionIntegrity?.selectionAdjustment || null;
  const holdout = project?.externalHoldout || null;
  const diagnostics = [...snapshotDiagnostics, ...(project?.diagnostics || [])];
  const verdictId = qualificationVerdict(qualification, run, diagnostics);
  const verdict = VERDICTS[verdictId];
  const validation = qualification?.validation;
  const weakestFold = validation?.weakestCandidateFold;
  const weakestNeutralFold = validation?.weakestStyleNeutralFold;

  return {
    verdict: {
      id: verdictId,
      ...verdict,
      detail: diagnostics.length
        ? `${diagnostics.length} 条 Core diagnostic 阻止有效裁决。`
        : qualification?.diagnosis?.explanation
          || (run ? "Core 未提供可裁决的因子资格证据。" : "尚无通过校验的 Factor Run。"),
    },
    qualification: {
      available: qualification?.available === true,
      stage: qualification?.diagnosis?.stage || qualification?.reason || "missing",
      qualifiesForPortfolio: qualification?.diagnosis?.qualifiesForPortfolio ?? null,
      selectionSplit: qualification?.diagnosis?.selectionSplit || null,
      testEntersDiagnosis: qualification?.diagnosis?.testEntersDiagnosis ?? null,
    },
    selection: {
      available: Boolean(adjustment),
      status: adjustment?.status || "missing",
      method: adjustment?.method || null,
      passes: adjustment?.passes ?? null,
      uniqueTrials: adjustment?.statistics?.uniqueTrials ?? null,
      externalHoldoutRequired: selectionIntegrity?.externalHoldoutRequired ?? null,
      testEntersSelection: selectionIntegrity?.testEntersSelection
        ?? qualification?.selection?.testEntersSelection
        ?? null,
    },
    robustness: {
      available: Boolean(validation),
      weakestFold: weakestFold?.meanRankIc ?? null,
      weakestFoldId: weakestFold?.id || null,
      weakestNeutralFold: weakestNeutralFold?.meanRankIc ?? null,
      weakestNeutralFoldId: weakestNeutralFold?.id || null,
    },
    holdout: {
      available: Boolean(holdout),
      state: holdout?.state || "missing",
      assessment: holdout?.assessment?.overallAssessment || null,
      candidateFrozen: holdout?.authority?.candidateFrozen ?? null,
    },
    authority: {
      tradingAuthority: qualification?.tradingAuthority
        || qualification?.claim?.tradingAuthority
        || holdout?.authority?.tradingAuthority
        || null,
    },
  };
}
