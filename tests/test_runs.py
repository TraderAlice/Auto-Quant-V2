from __future__ import annotations

import json
import tempfile
import unittest

from autoquant.runs import execute_study, list_runs, load_run
from autoquant.studies import create_study, hash_file
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import (
    FAILURE_JUDGE,
    MALFORMED_JUDGE,
    TIMEOUT_JUDGE,
    make_project,
    study_definition,
)


class ImmutableRunTests(unittest.TestCase):
    def test_successful_run_freezes_complete_identity_metrics_and_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            study = create_study(project, study_definition())
            run = execute_study(project, study.definition.id)

            self.assertEqual(run.result["status"], "succeeded")
            self.assertEqual(run.result["metrics"]["score"], 1.25)
            self.assertEqual(
                run.result["metrics"]["per_asset"]["AAA/USD"]["score"],
                1.25,
            )
            self.assertEqual(run.result["subject"]["kind"], "factor")
            self.assertEqual(run.result["subject"]["version"], "working")
            self.assertEqual(run.result["dataset"]["id"], "synthetic-bars")
            self.assertEqual(run.result["dataset"]["universe"], ["AAA/USD"])
            self.assertEqual(
                run.result["dataset"]["time_range"],
                {"start": "2026-01-01", "end": "2026-01-31"},
            )
            self.assertEqual(run.result["studyInputHash"], study.input_hash)
            self.assertNotEqual(run.result["inputHash"], study.input_hash)
            self.assertEqual(run.result["harness"]["id"], "autoquant.python-judge")
            self.assertIn("sourceHash", run.result["harness"])
            self.assertIn("dirty", run.result["harness"])
            self.assertEqual(run.result["execution"]["exitCode"], 0)
            self.assertFalse(run.result["execution"]["timedOut"])
            self.assertEqual(
                run.result["execution"]["evaluationRole"],
                "research-selection",
            )
            self.assertTrue((run.root_dir / "sources/factors/candidate.py").is_file())
            self.assertTrue(
                (run.root_dir / "inputs/judge-sources/judges/evaluate.py").is_file()
            )
            self.assertTrue((run.root_dir / "artifacts/report.json").is_file())
            self.assertIn("evaluated 1.25", (run.root_dir / "stdout.txt").read_text())
            self.assertTrue(run.manifest["completed"])
            self.assertNotIn("manifest.json", run.manifest["files"])
            self.assertEqual(
                run.manifest["resultHash"],
                run.manifest["files"]["result.json"],
            )
            self.assertEqual(load_run(project, run.result["id"]), run)

    def test_identical_inputs_create_distinct_runs_with_same_input_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            first = execute_study(project, "factor-quality")
            second = execute_study(project, "factor-quality")

            self.assertNotEqual(first.result["id"], second.result["id"])
            self.assertEqual(first.result["inputHash"], second.result["inputHash"])
            self.assertEqual(first.result["metrics"], second.result["metrics"])
            self.assertEqual(
                [item.id for item in list_runs(project)],
                [first.result["id"], second.result["id"]],
            )

    def test_run_freezes_fixed_dependency_separately_from_candidate_source(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            (project.root_dir / "models" / "policy.py").write_text(
                "POLICY = 'v1'\n",
                encoding="utf-8",
            )
            study = create_study(
                project,
                study_definition(
                    editable=["models/**"],
                    dependencies=["factors/candidate.py"],
                ),
            )
            run = execute_study(project, study.definition.id)

            self.assertEqual(
                run.result["dependencies"]["paths"],
                ["factors/candidate.py"],
            )
            self.assertEqual(
                run.result["dependencies"]["hash"],
                study.dependency_hash,
            )
            self.assertTrue(
                (
                    run.root_dir
                    / "inputs"
                    / "dependency-sources"
                    / "factors"
                    / "candidate.py"
                ).is_file()
            )
            self.assertFalse(
                (run.root_dir / "sources" / "factors" / "candidate.py").exists()
            )
            self.assertEqual(load_run(project, run.result["id"]), run)

    def test_exit_malformed_output_and_timeout_publish_failed_evidence(self) -> None:
        cases = [
            ("exit-study", FAILURE_JUDGE, 10, "judge.exit"),
            ("malformed-study", MALFORMED_JUDGE, 10, "judge.output-json"),
            ("timeout-study", TIMEOUT_JUDGE, 1, "judge.timeout"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            for study_id, source, timeout, expected_code in cases:
                judge_name = f"{study_id}.py"
                (project.root_dir / "judges" / judge_name).write_text(source)
                create_study(
                    project,
                    study_definition(
                        study_id=study_id,
                        judge=f"judges/{judge_name}",
                        timeout=timeout,
                    ),
                )
                run = execute_study(project, study_id)
                self.assertEqual(run.result["status"], "failed")
                self.assertEqual(run.result["errors"][0]["code"], expected_code)
                self.assertTrue((run.root_dir / "stdout.txt").is_file())
                self.assertTrue((run.root_dir / "stderr.txt").is_file())
                self.assertTrue(run.manifest["completed"])
                self.assertEqual(load_run(project, run.result["id"]), run)

            self.assertEqual(len(list_runs(project)), 3)

    def test_run_listing_ignores_incomplete_directories_and_rejects_tampering(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            run = execute_study(project, "factor-quality")
            incomplete = project.root_dir / "runs" / "run-incomplete"
            incomplete.mkdir()
            (incomplete / "partial.txt").write_text("not published")

            self.assertEqual(len(list_runs(project)), 1)
            result_path = run.root_dir / "result.json"
            result = json.loads(result_path.read_text())
            result["summary"] = "tampered"
            result_path.write_text(json.dumps(result))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "do not match the terminal manifest",
            ):
                load_run(project, run.result["id"])

    def test_run_loader_rejects_a_rehashed_but_invalid_result_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            run = execute_study(project, "factor-quality")
            result_path = run.root_dir / "result.json"
            manifest_path = run.root_dir / "manifest.json"

            result = json.loads(result_path.read_text())
            result["undeclared"] = True
            result_path.write_text(json.dumps(result))
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["result.json"] = hash_file(result_path)
            manifest["resultHash"] = manifest["files"]["result.json"]
            manifest_path.write_text(json.dumps(manifest))

            with self.assertRaisesRegex(AutoQuantValidationError, "Unknown field"):
                load_run(project, run.result["id"])


if __name__ == "__main__":
    unittest.main()
