import test from "node:test";
import assert from "node:assert/strict";
import { factorVerificationFrom } from "../lib/verification.js";

function projectWith(stage, overrides = {}) {
  return {
    valid: true,
    diagnostics: [],
    factorExplorer: {
      run: { id: "run-1", status: "succeeded" },
      factorQualification: {
        available: true,
        tradingAuthority: "none",
        diagnosis: { stage, explanation: stage, selectionSplit: "validation", testEntersDiagnosis: false },
        selection: { testEntersSelection: false },
        validation: {
          weakestCandidateFold: { id: "validation_1", meanRankIc: 0.01 },
          weakestStyleNeutralFold: { id: "validation_2", meanRankIc: 0.02 },
        },
      },
    },
    externalHoldout: null,
    sessions: [],
    ...overrides,
  };
}

test("factor verdict is deterministic and does not use visible test evidence", () => {
  assert.equal(factorVerificationFrom(projectWith("factor-qualification-positive")).verdict.id, "supported");
  assert.equal(factorVerificationFrom(projectWith("raw-predictive-edge-absent")).verdict.id, "contradicted");
  assert.equal(factorVerificationFrom(projectWith("raw-statistical-evidence-weak")).verdict.id, "inconclusive");
});

test("diagnostics invalidate the test and missing evidence stays inconclusive", () => {
  assert.equal(factorVerificationFrom(projectWith("factor-qualification-positive"), [{ code: "run.tampered" }]).verdict.id, "invalid-test");
  assert.equal(factorVerificationFrom({ valid: true, diagnostics: [] }).verdict.id, "inconclusive");
});

test("selection adjustment and holdout are reported only when present", () => {
  const missing = factorVerificationFrom(projectWith("factor-qualification-positive"));
  assert.equal(missing.selection.available, false);
  assert.equal(missing.holdout.state, "missing");

  const projected = factorVerificationFrom(projectWith("factor-qualification-positive", {
    sessions: [{ session: { leader: { runId: "run-1" } }, selectionIntegrity: { testEntersSelection: false, externalHoldoutRequired: true, selectionAdjustment: { status: "available", method: "bonferroni-hac-v1", passes: false, statistics: { uniqueTrials: 4 } } } }],
    externalHoldout: { state: "assessed", assessment: { overallAssessment: "supported" }, authority: { candidateFrozen: true, tradingAuthority: "none" } },
  }));
  assert.equal(projected.selection.passes, false);
  assert.equal(projected.selection.uniqueTrials, 4);
  assert.equal(projected.holdout.state, "assessed");
  assert.equal(projected.authority.tradingAuthority, "none");
});

test("selection adjustment from a different Run is not attached to the verdict", () => {
  const projected = factorVerificationFrom(projectWith("factor-qualification-positive", {
    sessions: [{ session: { leader: { runId: "run-other" } }, selectionIntegrity: { selectionAdjustment: { status: "available", method: "bonferroni-hac-v1", passes: true } } }],
  }));
  assert.equal(projected.selection.available, false);
});
