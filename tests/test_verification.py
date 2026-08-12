from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from autoquant.verification import (
    assess_research_claim,
    build_research_claim,
    list_verification_assessments,
    load_verification_assessment,
    publish_verification_assessment,
    validate_research_claim,
    validate_verification_assessment,
)
from autoquant.cli import build_parser, dispatch
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project


HASH = "a" * 64


def run_evidence(**integrity: bool) -> dict:
    return {
        "id": "run-1",
        "hash": HASH,
        "integrity": {
            "tampered": False,
            "lookaheadDetected": False,
            "schemaValid": True,
            "authorityValid": True,
            **integrity,
        },
    }


def metric_evidence(kind: str, primary: float, baseline: float, samples: int = 100) -> dict:
    return {
        "id": f"{kind}-1",
        "hash": HASH,
        "metric": "rank_ic",
        "primaryValue": primary,
        "baselineValue": baseline,
        "sampleSize": samples,
    }


def selection(passed: bool = True) -> dict:
    return {"id": "selection-1", "hash": HASH, "passed": passed}


class VerificationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.claim = build_research_claim(
            statement="Candidate has positive out-of-sample rank IC versus baseline.",
            metric="rank_ic",
            direction="maximize",
            minimum_effect=0.01,
            minimum_sample_size=50,
        )

    def assess(self, **overrides: object) -> dict:
        evidence = {
            "run_evidence": run_evidence(),
            "explorer_evidence": metric_evidence("explorer", 0.08, 0.01),
            "holdout_evidence": metric_evidence("holdout", 0.05, 0.01),
            "selection_evidence": selection(),
            **overrides,
        }
        return assess_research_claim(self.claim, **evidence)

    def test_supported_assessment_is_content_addressed_and_has_no_authority(self) -> None:
        observed = self.assess()

        self.assertEqual(observed["verdict"], "supported")
        self.assertEqual(observed["limitations"], [])
        self.assertEqual(observed["tradingAuthority"], "none")
        self.assertEqual(
            [item["kind"] for item in observed["evidenceRefs"]],
            ["run", "explorer", "holdout", "selection"],
        )
        self.assertEqual(observed, self.assess())

        changed = copy.deepcopy(observed)
        changed["verdict"] = "contradicted"
        with self.assertRaises(AutoQuantValidationError):
            validate_verification_assessment(changed)

    def test_invalid_integrity_precedes_missing_and_contradicting_evidence(self) -> None:
        observed = self.assess(
            run_evidence=run_evidence(tampered=True),
            explorer_evidence=metric_evidence("explorer", -0.03, 0.01),
            holdout_evidence=None,
        )

        self.assertEqual(observed["verdict"], "invalid-test")
        self.assertIn("run-integrity-tampered-or-unverified", observed["limitations"])
        self.assertIn("holdout-missing", observed["limitations"])

    def test_missing_low_sample_and_required_holdout_are_inconclusive(self) -> None:
        for overrides, limitation in (
            ({"explorer_evidence": None}, "primary-missing"),
            ({"explorer_evidence": metric_evidence("explorer", 0.08, 0.01, 10)}, "primary-low-sample"),
            ({"holdout_evidence": None}, "holdout-missing"),
            ({"selection_evidence": None}, "required-selection-evidence-missing"),
        ):
            with self.subTest(limitation=limitation):
                observed = self.assess(**overrides)
                self.assertEqual(observed["verdict"], "inconclusive")
                self.assertIn(limitation, observed["limitations"])

    def test_adequate_primary_or_holdout_direction_contradiction_is_reported(self) -> None:
        for overrides in (
            {"explorer_evidence": metric_evidence("explorer", -0.02, 0.01)},
            {"holdout_evidence": metric_evidence("holdout", 0.00, 0.01)},
        ):
            with self.subTest(overrides=overrides):
                observed = self.assess(**overrides)
                self.assertEqual(observed["verdict"], "contradicted")
                self.assertNotIn("fraud", str(observed).lower())

    def test_below_minimum_effect_and_failed_selection_are_inconclusive(self) -> None:
        below = self.assess(
            explorer_evidence=metric_evidence("explorer", 0.015, 0.01)
        )
        failed_selection = self.assess(selection_evidence=selection(False))

        self.assertEqual(below["verdict"], "inconclusive")
        self.assertIn("primary-below-effect", below["limitations"])
        self.assertEqual(failed_selection["verdict"], "inconclusive")
        self.assertIn("selection-gate-failed", failed_selection["limitations"])

    def test_contradiction_is_not_hidden_by_non_missing_gate_failures(self) -> None:
        observed = self.assess(
            explorer_evidence=metric_evidence("explorer", -0.02, 0.01),
            holdout_evidence=metric_evidence("holdout", 0.015, 0.01),
            selection_evidence=selection(False),
        )

        self.assertEqual(observed["verdict"], "contradicted")
        self.assertIn("holdout-below-effect", observed["limitations"])
        self.assertIn("selection-gate-failed", observed["limitations"])

    def test_missing_required_holdout_still_blocks_contradiction(self) -> None:
        observed = self.assess(
            explorer_evidence=metric_evidence("explorer", -0.02, 0.01),
            holdout_evidence=None,
        )

        self.assertEqual(observed["verdict"], "inconclusive")
        self.assertIn("holdout-missing", observed["limitations"])

    def test_claim_validation_rejects_authority_and_content_tampering(self) -> None:
        changed = copy.deepcopy(self.claim)
        changed["tradingAuthority"] = "live"
        with self.assertRaises(AutoQuantValidationError):
            validate_research_claim(changed)

    def test_publishes_and_verifies_immutable_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            published = publish_verification_assessment(
                project,
                self.claim,
                run_evidence=run_evidence(),
                explorer_evidence=metric_evidence("explorer", 0.08, 0.01),
                holdout_evidence=metric_evidence("holdout", 0.05, 0.01),
                selection_evidence=selection(),
            )

            self.assertEqual(published["assessment"]["verdict"], "supported")
            self.assertEqual(
                load_verification_assessment(project, published["assessment"]["id"]),
                published,
            )
            self.assertEqual(list_verification_assessments(project), [published])

    def test_cli_assesses_lists_and_shows_external_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, project = make_project(root)
            claim_path = root / "claim.json"
            evidence_path = root / "evidence.json"
            claim_path.write_text(json.dumps(self.claim), encoding="utf-8")
            evidence_path.write_text(json.dumps({
                "run": run_evidence(),
                "explorer": metric_evidence("explorer", 0.08, 0.01),
                "holdout": metric_evidence("holdout", 0.05, 0.01),
                "selection": selection(),
            }), encoding="utf-8")
            parser = build_parser()

            assessed = dispatch(parser.parse_args([
                "verify", "assess", str(project.root_dir), "--claim", str(claim_path), "--evidence", str(evidence_path),
            ]))
            listed = dispatch(parser.parse_args(["verify", "list", str(project.root_dir)]))
            shown = dispatch(parser.parse_args([
                "verify", "show", str(project.root_dir), "--assessment", assessed.data["assessment"]["id"],
            ]))

            self.assertEqual(assessed.data["assessment"]["verdict"], "supported")
            self.assertEqual(listed.data["assessments"], [assessed.data])
            self.assertEqual(shown.data, assessed.data)

        changed = copy.deepcopy(self.claim)
        changed["minimumEffect"] = 0.02
        with self.assertRaises(AutoQuantValidationError):
            validate_research_claim(changed)


if __name__ == "__main__":
    unittest.main()
