from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch

from autoquant.cli import build_parser, dispatch
from autoquant.compute_jobs import (
    ComputeResourcePolicy,
    compute_executor_declarations,
    execute_compute_job,
    load_compute_job,
)
from autoquant.runs import load_run
from autoquant.studies import create_study
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition


class ComputeJobTests(unittest.TestCase):
    def test_cli_executes_lists_and_shows_compute_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            study = create_study(project, study_definition())
            parser = build_parser()

            executed = dispatch(parser.parse_args([
                "job", "execute", str(project.root_dir), "--study", study.definition.id,
            ]))
            listed = dispatch(parser.parse_args(["job", "list", str(project.root_dir)]))
            shown = dispatch(parser.parse_args([
                "job", "show", str(project.root_dir), "--job", executed.data["id"],
            ]))

            self.assertEqual(executed.command, "job.execute")
            self.assertEqual(listed.data["jobs"][0]["id"], executed.data["id"])
            self.assertEqual(shown.data["receipt"], executed.data)

    def test_builtin_cpu_publishes_verified_terminal_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            study = create_study(project, study_definition())

            job = execute_compute_job(
                project,
                study.definition.id,
                resource_policy=ComputeResourcePolicy(memory_mb=512),
            )

            self.assertEqual(job.receipt["status"], "succeeded")
            self.assertEqual(job.receipt["project"], {"id": project.manifest.id})
            self.assertEqual(job.receipt["study"]["id"], study.definition.id)
            self.assertEqual(job.receipt["inputHash"], study.input_hash)
            self.assertEqual(
                job.receipt["executor"], {"kind": "cpu", "provider": "builtin"}
            )
            self.assertEqual(job.receipt["resourcePolicy"]["memoryMb"], 512)
            self.assertEqual(
                [item["state"] for item in job.receipt["stateHistory"]],
                ["queued", "running", "succeeded"],
            )
            self.assertEqual(job.receipt["tradingAuthority"], "none")
            self.assertIsNone(job.receipt["error"])
            self.assertEqual(len(job.receipt["outputRefs"]), 1)
            run = load_run(project, job.receipt["runRef"]["id"])
            self.assertEqual(run.result["studyInputHash"], study.input_hash)
            self.assertEqual(load_compute_job(project, job.receipt["id"]), job)

    def test_retry_preserves_input_and_records_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            first = execute_compute_job(project, "factor-quality")
            second = execute_compute_job(
                project,
                "factor-quality",
                retry_of=first.receipt["id"],
            )

            self.assertEqual(
                second.receipt["retry"],
                {
                    "rootJobId": first.receipt["id"],
                    "parentJobId": first.receipt["id"],
                    "attempt": 2,
                },
            )
            self.assertNotEqual(
                first.receipt["runRef"]["id"], second.receipt["runRef"]["id"]
            )

    def test_private_executors_are_declared_but_cannot_fake_execution(self) -> None:
        declarations = compute_executor_declarations()
        self.assertEqual([item["kind"] for item in declarations], ["cpu", "gpu", "moss"])
        self.assertTrue(declarations[0]["available"])
        self.assertFalse(declarations[1]["available"])
        self.assertFalse(declarations[2]["available"])
        self.assertNotIn("credential", json.dumps(declarations).lower())

        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            with self.assertRaisesRegex(AutoQuantValidationError, "No GPU provider"):
                execute_compute_job(project, "factor-quality", executor_kind="gpu")
            self.assertFalse((project.root_dir / "compute-jobs").exists())

    def test_executor_exception_publishes_sanitized_failed_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            with patch(
                "autoquant.compute_jobs.execute_study",
                side_effect=RuntimeError("secret-token=must-not-leak"),
            ):
                job = execute_compute_job(project, "factor-quality")

            self.assertEqual(job.receipt["status"], "failed")
            self.assertEqual(
                [item["state"] for item in job.receipt["stateHistory"]],
                ["queued", "running", "failed"],
            )
            self.assertIsNone(job.receipt["runRef"])
            self.assertNotIn("secret-token", json.dumps(job.receipt))

    def test_loader_rejects_bad_ids_and_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            job = execute_compute_job(project, "factor-quality")
            receipt_path = job.root_dir / "receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["tradingAuthority"] = "orders"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            with self.assertRaisesRegex(AutoQuantValidationError, "manifest"):
                load_compute_job(project, job.receipt["id"])
            with self.assertRaisesRegex(AutoQuantValidationError, "Invalid ComputeJob id"):
                load_compute_job(project, "../escape")


if __name__ == "__main__":
    unittest.main()
