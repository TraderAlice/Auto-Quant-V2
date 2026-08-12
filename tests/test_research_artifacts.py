from __future__ import annotations

import copy
import tempfile
import unittest

from autoquant.research_artifacts import (
    artifact_review_readiness,
    list_artifact_decisions,
    list_reproduction_receipts,
    load_artifact_decision,
    publish_artifact_decision,
    publish_reproduction_receipt,
    validate_reproduction_request,
)
from autoquant.research_definitions import (
    approve_factor_definition,
    create_experiment_definition_version,
    create_factor_definition_version,
    freeze_experiment_definition,
)
from autoquant.runs import execute_study, list_runs
from autoquant.sessions import start_session
from autoquant.studies import create_study
from autoquant.verification import (
    build_research_claim,
    publish_verification_assessment,
)
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition
from tests.test_research_definitions import factor_definition, experiment_definition

HASH = "a" * 64


def artifact_review(definition_hash: str, *, decision: str = "approve", definition_version: int) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-artifact-review",
        "id": "approval-quality-momentum-v1",
        "decision": decision,
        "actor": {"id": "research-owner", "kind": "user"},
        "definitionRef": {"kind": "factor", "id": "quality-momentum", "version": definition_version},
        "definitionHash": definition_hash,
        "evidenceManifest": {
            "data": {"packageId": "us-equities", "version": "2026-07-31"},
            "experimentDefinition": {"id": "quality-momentum-validation", "version": 1},
            "runs": [
                {"id": "run-negative", "status": "contradicted"},
                {"id": "run-selected", "status": "supported"},
            ],
            "assessment": {"verdict": "supported"},
            "costs": {"known": True, "currency": "USD", "amount": 1.5},
            "holdout": {"state": "assessed", "id": "holdout-1"},
            "limitations": ["small-cap coverage is limited"],
            "diagnostics": [],
            "artifactHashes": {"result.json": "b" * 64},
            "metrics": {"netSharpe": 1.2},
            "environment": {"executor": "cpu", "runtime": "cpython-3.13"},
            "cpuEquivalentAllowed": False,
        },
        "reason": "Evidence closure is complete for this exact factor version.",
    }


def reproduction_request(approval_id: str, *, reproduction_id: str = "repro-1") -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-reproduction-request",
        "id": reproduction_id,
        "approvalId": approval_id,
    }


def _complete_closure(project, session, factor):
    """Build a complete positive evidence closure: frozen experiment + real Run
    + published verification assessment + exact artifact review.

    Returns (frozen, run, review).
    """
    # 1. Create and freeze experiment that references the exact approved factor
    # "autoquant-factor-definition" → "factor", "autoquant-strategy-definition" → "strategy"
    definition_kind = factor.definition["kind"].split("-")[1]
    exp = experiment_definition(status="draft")
    exp["definitionRef"] = {
        "kind": definition_kind,
        "id": factor.definition["id"],
        "version": factor.definition["version"],
    }
    exp["data"] = {"packageId": "us-equities", "version": "2026-07-31"}
    created_exp = create_experiment_definition_version(
        project, session.manifest["id"], exp
    )
    frozen = freeze_experiment_definition(
        project, session.manifest["id"], exp["id"], created_exp.definition["version"]
    )

    # 2. Exact researchBinding → execute_study
    binding = {
        "definitionRef": {
            "kind": definition_kind,
            "id": factor.definition["id"],
            "version": factor.definition["version"],
            "contentHash": factor.manifest["contentHash"],
        },
        "experimentDefinitionRef": {
            "kind": "experiment",
            "sessionId": session.manifest["id"],
            "id": frozen.definition["id"],
            "version": frozen.definition["version"],
            "contentHash": frozen.manifest["contentHash"],
        },
    }
    run = execute_study(project, "factor-quality", research_binding=binding)

    # 3. Publish verification assessment with real Run evidence
    claim = build_research_claim(
        statement="Candidate has positive out-of-sample rank IC versus baseline.",
        metric="rank_ic",
        direction="maximize",
        minimum_effect=0.01,
        minimum_sample_size=50,
    )
    # Run evidence with integrity fields exactly as required by the contract
    run_evidence = {
        "id": run.result["id"],
        "hash": run.manifest["resultHash"],
        "integrity": {
            "tampered": False,
            "lookaheadDetected": False,
            "schemaValid": True,
            "authorityValid": True,
        },
    }
    explorer_evidence = {
        "id": "explorer-1",
        "hash": HASH,
        "metric": "rank_ic",
        "primaryValue": 0.08,
        "baselineValue": 0.01,
        "sampleSize": 100,
    }
    holdout_evidence = {
        "id": "holdout-1",
        "hash": HASH,
        "metric": "rank_ic",
        "primaryValue": 0.05,
        "baselineValue": 0.01,
        "sampleSize": 100,
    }
    selection_evidence = {"id": "selection-1", "hash": HASH, "passed": True}
    published = publish_verification_assessment(
        project,
        claim,
        run_evidence=run_evidence,
        explorer_evidence=explorer_evidence,
        holdout_evidence=holdout_evidence,
        selection_evidence=selection_evidence,
    )

    # 4. Build the artifact review
    definition_hash = factor.manifest["contentHash"]
    definition_version = factor.definition["version"]
    review = artifact_review(definition_hash, definition_version=definition_version)
    # Override with exact evidence from the closure
    review["evidenceManifest"]["data"] = frozen.definition["data"]
    review["evidenceManifest"]["experimentDefinition"] = {
        "id": frozen.definition["id"],
        "version": frozen.definition["version"],
        "contentHash": frozen.manifest["contentHash"],
    }
    review["evidenceManifest"]["runs"] = [
        {
            "id": run.result["id"],
            "hash": run.manifest["resultHash"],
            "status": "contradicted",
            "negativeEvidence": "retained",
        }
    ]
    review["evidenceManifest"]["assessment"] = published["assessment"]
    # Keep existing costs/holdout/limitations/diagnostics/artifactHashes/metrics/environment/cpuEquivalentAllowed
    # from the artifact_review helper — they are already set.

    return frozen, run, review


class ResearchArtifactTests(unittest.TestCase):
    def _setup(self, directory: str):
        _, project = make_project(directory)
        create_study(project, study_definition())
        session = start_session(project, "factor-quality")
        draft_value = factor_definition(status="draft")
        created = create_factor_definition_version(project, draft_value)
        approved = approve_factor_definition(
            project, created.definition["id"], created.definition["version"]
        )
        return project, session, approved

    def test_unverified_closure_cannot_approve_or_reproduce(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session, factor = self._setup(directory)
            review = artifact_review(factor.manifest["contentHash"], definition_version=factor.definition["version"])
            self.assertIn("coreEvidenceAssessment", artifact_review_readiness(review)["unresolved"])
            with self.assertRaises(AutoQuantValidationError):
                publish_artifact_decision(project, session.manifest["id"], review)

            review["decision"] = "retain-as-draft"
            draft = publish_artifact_decision(project, session.manifest["id"], review)
            self.assertEqual(draft["review"], review)
            with self.assertRaises(AutoQuantValidationError):
                publish_reproduction_receipt(
                    project,
                    session.manifest["id"],
                    reproduction_request(draft["decision"]["id"]),
                )

            self.assertIsNone(draft["decision"]["artifactId"])
            self.assertEqual(len(list_artifact_decisions(project, session.manifest["id"])), 1)
            self.assertEqual(len(list_reproduction_receipts(project, session.manifest["id"])), 0)

    def test_incomplete_closure_disables_approval_but_return_preserves_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session, factor = self._setup(directory)
            incomplete = artifact_review(factor.manifest["contentHash"], definition_version=factor.definition["version"])
            incomplete["evidenceManifest"]["holdout"] = None
            self.assertFalse(artifact_review_readiness(incomplete)["ready"])
            with self.assertRaises(AutoQuantValidationError):
                publish_artifact_decision(project, session.manifest["id"], incomplete)

            incomplete["id"] = "return-quality-momentum-v1"
            incomplete["decision"] = "return-for-revision"
            returned = publish_artifact_decision(project, session.manifest["id"], incomplete)
            self.assertEqual(returned["decision"]["decision"], "return-for-revision")
            self.assertEqual(returned["review"], incomplete)
            self.assertIsNone(returned["decision"]["artifactId"])

    def test_stale_review_and_private_environment_substitution_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session, factor = self._setup(directory)
            stale = artifact_review("c" * 64, definition_version=factor.definition["version"])
            with self.assertRaises(AutoQuantValidationError):
                publish_artifact_decision(project, session.manifest["id"], stale)

            review = artifact_review(factor.manifest["contentHash"], decision="retain-as-draft", definition_version=factor.definition["version"])
            review["evidenceManifest"]["environment"] = {
                "executor": "private-gpu",
                "runtime": "moss-v1",
            }
            retained = publish_artifact_decision(project, session.manifest["id"], review)
            self.assertIsNone(retained["decision"]["artifactId"])

    def test_reproduction_request_cannot_self_report_results(self) -> None:
        request = reproduction_request("approval-1")
        request["available"] = True
        request["artifactHashes"] = {"result.json": "b" * 64}
        with self.assertRaises(AutoQuantValidationError):
            validate_reproduction_request(request)

    def test_reproduction_is_truthfully_unavailable_and_creates_no_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session, factor = self._setup(directory)
            _, _, review = _complete_closure(project, session, factor)
            approval = publish_artifact_decision(project, session.manifest["id"], review)

            before = len(list_runs(project))

            receipt = publish_reproduction_receipt(
                project,
                session.manifest["id"],
                reproduction_request(approval["decision"]["id"]),
            )

            self.assertEqual(receipt["receipt"]["outcome"], "unavailable")

            differences = receipt["receipt"]["differences"]
            self.assertTrue(
                any(d["field"] == "executor" and d["actual"] == "unavailable" for d in differences),
                f"No executor=unavailable difference found in {differences}",
            )

            self.assertEqual(receipt["receipt"]["artifactId"], approval["decision"]["artifactId"])
            self.assertEqual(
                receipt["receipt"]["originalEvidenceHash"],
                approval["decision"]["evidenceManifestHash"],
            )

            self.assertEqual(len(list_runs(project)), before)

            receipts = list_reproduction_receipts(project, session.manifest["id"])
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0], receipt)

    def test_exact_published_closure_approves_and_preserves_negative_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session, factor = self._setup(directory)
            frozen, run, review = _complete_closure(project, session, factor)

            # Review must be ready with zero unresolved items
            readiness = artifact_review_readiness(review)
            self.assertTrue(readiness["ready"], msg=f"unresolved: {readiness['unresolved']}")
            self.assertEqual(readiness["unresolved"], [])

            # Record run count before approval
            runs_before = list_runs(project)
            num_runs_before = len(runs_before)

            # Publish the artifact decision
            result = publish_artifact_decision(project, session.manifest["id"], review)
            self.assertEqual(result["decision"]["decision"], "approve")
            self.assertIsNotNone(result["decision"]["artifactId"])
            self.assertNotEqual(result["decision"]["artifactId"], "")

            # definitionRef / version / hash are exact
            decision = result["decision"]
            self.assertEqual(
                decision["definitionRef"],
                {"kind": "factor", "id": factor.definition["id"], "version": factor.definition["version"]},
            )
            self.assertEqual(decision["definitionHash"], factor.manifest["contentHash"])

            # load_artifact_decision round-trip
            loaded = load_artifact_decision(project, session.manifest["id"], decision["id"])
            self.assertEqual(loaded["decision"], decision)
            self.assertEqual(loaded["review"], review)

            # list_artifact_decisions round-trip
            decisions = list_artifact_decisions(project, session.manifest["id"])
            self.assertIn(loaded, decisions)

            # The published assessment in review.evidenceManifest.assessment equals
            # what was published via verification
            published_assessment = review["evidenceManifest"]["assessment"]
            self.assertEqual(loaded["review"]["evidenceManifest"]["assessment"], published_assessment)

            # Run ref status/negativeEvidence round-trips exactly
            run_ref = loaded["review"]["evidenceManifest"]["runs"][0]
            self.assertEqual(run_ref["id"], run.result["id"])
            self.assertEqual(run_ref["hash"], run.manifest["resultHash"])
            self.assertEqual(run_ref["status"], "contradicted")
            self.assertEqual(run_ref["negativeEvidence"], "retained")

            # Approving does not execute new research
            runs_after = list_runs(project)
            self.assertEqual(len(runs_after), num_runs_before)


    def test_approval_gates_fail_before_decision_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session, factor = self._setup(directory)
            _, bound_run, valid = _complete_closure(project, session, factor)

            def assert_gate_fails(review: dict) -> None:
                with self.assertRaises(AutoQuantValidationError):
                    publish_artifact_decision(project, session.manifest["id"], review)
                self.assertEqual(list_artifact_decisions(project, session.manifest["id"]), [])

            # Case 1: experiment definition contentHash mismatch
            case1 = copy.deepcopy(valid)
            case1["id"] = "reject-experiment-hash"
            case1["evidenceManifest"]["experimentDefinition"]["contentHash"] = "c" * 64
            assert_gate_fails(case1)

            # Case 2: run hash mismatch
            case2 = copy.deepcopy(valid)
            case2["id"] = "reject-run-hash"
            case2["evidenceManifest"]["runs"][0]["hash"] = "c" * 64
            assert_gate_fails(case2)

            # Case 3: unbound run (no research_binding) → run-binding gate fails
            legacy = execute_study(project, "factor-quality")
            case3 = copy.deepcopy(valid)
            case3["id"] = "reject-unbound-run"
            case3["evidenceManifest"]["runs"][0] = {
                "id": legacy.result["id"],
                "hash": legacy.manifest["resultHash"],
                "status": "failed",
            }
            assert_gate_fails(case3)

            # Case 4: run belongs to a different study execution;
            # Run gate passes but assessment-runs gate fails because the
            # published assessment was computed against the original run.
            binding = bound_run.result["researchBinding"]
            other = execute_study(project, "factor-quality", research_binding=binding)
            case4 = copy.deepcopy(valid)
            case4["id"] = "reject-assessment-run-mismatch"
            case4["evidenceManifest"]["runs"][0] = {
                "id": other.result["id"],
                "hash": other.manifest["resultHash"],
                "status": "contradicted",
                "negativeEvidence": "retained",
            }
            assert_gate_fails(case4)


if __name__ == "__main__":
    unittest.main()
