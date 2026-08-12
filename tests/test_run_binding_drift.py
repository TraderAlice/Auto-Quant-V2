"""Test that load_run detects status drift on bound definitions.

Scenario A: FactorDefinition was approved at bind time; later its on-disk
definition.json is changed to retired (with manifest + Run hashes updated
consistently).  load_run must fail because the referenced definition is
no longer approved — not merely a hash mismatch.

Scenario B: ExperimentDefinition was frozen at bind time; later its on-disk
definition.json is changed to draft (with manifest + Run hashes updated
consistently).  load_run must fail because the referenced experiment is
no longer frozen.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoquant.research_definitions import (
    approve_factor_definition,
    create_experiment_definition_version,
    create_factor_definition_version,
    freeze_experiment_definition,
)
from autoquant.runs import execute_study, load_run
from autoquant.sessions import start_session
from autoquant.studies import create_study, hash_file
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition
from tests.test_runs import MINIMAL_EXPERIMENT_DEFINITION, MINIMAL_FACTOR_DEFINITION


def _hash_file(path: Path) -> str:
    return hash_file(path)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class DriftFactorDefinitionStatus(unittest.TestCase):
    """load_run refuses a Run whose bound FactorDefinition is no longer approved."""

    def test_retired_factor_definition_rejected_on_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            # --- establish approved factor definition ---
            factor_ctx = create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(
                project, "momentum-factor", factor_ctx.definition["version"]
            )

            # --- establish frozen experiment definition ---
            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            session = start_session(project, "factor-quality")

            exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
            exp_value["definitionRef"] = {
                "kind": "factor",
                "id": "momentum-factor",
                "version": approved.definition["version"],
            }
            experiment_ctx = create_experiment_definition_version(
                project, session.manifest["id"], exp_value
            )
            frozen = freeze_experiment_definition(
                project,
                session.manifest["id"],
                "momentum-test",
                experiment_ctx.definition["version"],
            )

            binding = {
                "definitionRef": {
                    "kind": "factor",
                    "id": "momentum-factor",
                    "version": approved.definition["version"],
                    "contentHash": approved.manifest["contentHash"],
                },
                "experimentDefinitionRef": {
                    "kind": "experiment",
                    "sessionId": session.manifest["id"],
                    "id": "momentum-test",
                    "version": frozen.definition["version"],
                    "contentHash": frozen.manifest["contentHash"],
                },
            }

            run = execute_study(
                project, "factor-quality", research_binding=binding,
            )

            # --- drift: change factor definition status to retired ---
            factor_root = approved.root_dir
            factor_def_path = factor_root / "definition.json"
            factor_manifest_path = factor_root / "manifest.json"

            defn = _read_json(factor_def_path)
            self.assertEqual(defn["status"], "approved")
            defn["status"] = "retired"
            _write_json(factor_def_path, defn)

            new_factor_hash = _hash_file(factor_def_path)
            factor_manifest = _read_json(factor_manifest_path)
            factor_manifest["status"] = "retired"
            factor_manifest["contentHash"] = new_factor_hash
            factor_manifest["files"] = {"definition.json": new_factor_hash}
            _write_json(factor_manifest_path, factor_manifest)

            # --- update Run result.json + manifest.json to close the hash closure ---
            run_root = run.root_dir
            result_path = run_root / "result.json"
            manifest_path = run_root / "manifest.json"

            result = _read_json(result_path)
            result["researchBinding"]["definitionRef"]["contentHash"] = (
                new_factor_hash
            )
            _write_json(result_path, result)

            new_result_hash = _hash_file(result_path)
            run_manifest = _read_json(manifest_path)
            run_manifest["files"]["result.json"] = new_result_hash
            run_manifest["resultHash"] = new_result_hash
            run_manifest["researchBinding"]["definitionRef"]["contentHash"] = (
                new_factor_hash
            )
            _write_json(manifest_path, run_manifest)

            # --- load_run must now fail on the un-approved status ---
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "not approved",
            ):
                load_run(project, run.result["id"])


class DriftExperimentDefinitionStatus(unittest.TestCase):
    """load_run refuses a Run whose bound ExperimentDefinition is no longer frozen."""

    def test_draft_experiment_definition_rejected_on_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            # --- establish approved factor definition ---
            factor_ctx = create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(
                project, "momentum-factor", factor_ctx.definition["version"]
            )

            # --- establish frozen experiment definition ---
            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            session = start_session(project, "factor-quality")

            exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
            exp_value["definitionRef"] = {
                "kind": "factor",
                "id": "momentum-factor",
                "version": approved.definition["version"],
            }
            experiment_ctx = create_experiment_definition_version(
                project, session.manifest["id"], exp_value
            )
            frozen = freeze_experiment_definition(
                project,
                session.manifest["id"],
                "momentum-test",
                experiment_ctx.definition["version"],
            )

            binding = {
                "definitionRef": {
                    "kind": "factor",
                    "id": "momentum-factor",
                    "version": approved.definition["version"],
                    "contentHash": approved.manifest["contentHash"],
                },
                "experimentDefinitionRef": {
                    "kind": "experiment",
                    "sessionId": session.manifest["id"],
                    "id": "momentum-test",
                    "version": frozen.definition["version"],
                    "contentHash": frozen.manifest["contentHash"],
                },
            }

            run = execute_study(
                project, "factor-quality", research_binding=binding,
            )

            # --- drift: change experiment definition status to draft ---
            exp_root = frozen.root_dir
            exp_def_path = exp_root / "definition.json"
            exp_manifest_path = exp_root / "manifest.json"

            defn = _read_json(exp_def_path)
            self.assertEqual(defn["status"], "frozen")
            defn["status"] = "draft"
            _write_json(exp_def_path, defn)

            new_exp_hash = _hash_file(exp_def_path)
            exp_manifest = _read_json(exp_manifest_path)
            exp_manifest["status"] = "draft"
            exp_manifest["contentHash"] = new_exp_hash
            exp_manifest["files"] = {"definition.json": new_exp_hash}
            _write_json(exp_manifest_path, exp_manifest)

            # --- update Run result.json + manifest.json to close the hash closure ---
            run_root = run.root_dir
            result_path = run_root / "result.json"
            manifest_path = run_root / "manifest.json"

            result = _read_json(result_path)
            result["researchBinding"]["experimentDefinitionRef"]["contentHash"] = (
                new_exp_hash
            )
            _write_json(result_path, result)

            new_result_hash = _hash_file(result_path)
            run_manifest = _read_json(manifest_path)
            run_manifest["files"]["result.json"] = new_result_hash
            run_manifest["resultHash"] = new_result_hash
            run_manifest["researchBinding"]["experimentDefinitionRef"][
                "contentHash"
            ] = new_exp_hash
            _write_json(manifest_path, run_manifest)

            # --- load_run must now fail on the not-frozen status ---
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "not frozen",
            ):
                load_run(project, run.result["id"])


if __name__ == "__main__":
    unittest.main()
