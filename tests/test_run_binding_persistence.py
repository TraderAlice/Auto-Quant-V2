from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoquant.runs import execute_study, load_run
from autoquant.research_definitions import (
    approve_factor_definition,
    create_experiment_definition_version,
    create_factor_definition_version,
    freeze_experiment_definition,
)
from autoquant.studies import create_study, hash_file
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition
from tests.test_runs import MINIMAL_FACTOR_DEFINITION, MINIMAL_EXPERIMENT_DEFINITION


RESULT_FILENAME = "result.json"
MANIFEST_FILENAME = "manifest.json"
BINDING_KEY = "researchBinding"


class RunBindingPersistenceTests(unittest.TestCase):
    # ----------------------------------------------------------------
    # minimal helpers
    # ----------------------------------------------------------------

    def _create_binding_run(
        self, directory: str
    ) -> tuple[object, object, dict]:
        """Create a project with approved factor, frozen experiment,
        and a Run that carries a valid researchBinding.

        Returns ``(project, run, binding_dict)``.
        """
        _, project = make_project(directory)

        # approved factor
        factor_ctx = create_factor_definition_version(
            project, dict(MINIMAL_FACTOR_DEFINITION)
        )
        approved = approve_factor_definition(
            project, "momentum-factor",
            factor_ctx.definition["version"],
        )

        # study + session
        create_study(project, study_definition(study_id="factor-quality"))
        execute_study(project, "factor-quality")  # baseline

        from autoquant.sessions import start_session

        session = start_session(project, "factor-quality")

        # frozen experiment
        exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
        exp_value["definitionRef"] = {
            "kind": "factor",
            "id": "momentum-factor",
            "version": approved.definition["version"],
        }
        experiment_ctx = create_experiment_definition_version(
            project, session.manifest["id"], exp_value,
        )
        frozen = freeze_experiment_definition(
            project, session.manifest["id"], "momentum-test",
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
        return project, run, binding

    @staticmethod
    def _read_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.write_text(json.dumps(data), encoding="utf-8")

    @staticmethod
    def _sync_result_hashes(
        result_path: Path, manifest_path: Path,
    ) -> None:
        """Re-hash the tampered result.json and update manifest
        ``files['result.json']`` and ``resultHash`` so the file-
        integrity check passes and the fault reaches the
        researchBinding symmetry / consistency boundary."""
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        new_hash = hash_file(result_path)
        manifest["files"][RESULT_FILENAME] = new_hash
        manifest["resultHash"] = new_hash
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # ----------------------------------------------------------------
    # 1. legacy Run – no researchBinding anywhere
    # ----------------------------------------------------------------

    def test_legacy_run_no_binding_all_locations_loads(self) -> None:
        """A legacy Run whose in-memory result, result.json, and
        manifest.json all lack researchBinding must load_run
        successfully."""
        with tempfile.TemporaryDirectory() as tmp:
            _, project = make_project(tmp)
            create_study(project, study_definition(study_id="factor-quality"))
            run = execute_study(project, "factor-quality")

            # in-memory
            self.assertNotIn(BINDING_KEY, run.result,
                             "in-memory result must have no researchBinding")

            # result.json on disk
            result_on_disk = self._read_json(
                run.root_dir / RESULT_FILENAME
            )
            self.assertNotIn(
                BINDING_KEY, result_on_disk,
                "result.json must have no researchBinding",
            )

            # manifest.json on disk
            manifest_on_disk = self._read_json(
                run.root_dir / MANIFEST_FILENAME
            )
            self.assertNotIn(
                BINDING_KEY, manifest_on_disk,
                "manifest.json must have no researchBinding",
            )

            # load_run must succeed
            reloaded = load_run(project, run.result["id"])
            self.assertNotIn(BINDING_KEY, reloaded.result)

    # ----------------------------------------------------------------
    # 2. valid binding – equal in all three locations
    # ----------------------------------------------------------------

    def test_valid_binding_persists_all_locations(self) -> None:
        """A legal researchBinding must be exactly equal in the in-
        memory result, on-disk result.json, and on-disk manifest.json;
        load_run must succeed and preserve the binding."""
        with tempfile.TemporaryDirectory() as tmp:
            project, run, binding = self._create_binding_run(tmp)

            # in-memory
            self.assertEqual(
                run.result[BINDING_KEY], binding,
                "in-memory result must carry the exact binding",
            )

            # result.json on disk
            result_on_disk = self._read_json(
                run.root_dir / RESULT_FILENAME
            )
            self.assertEqual(
                result_on_disk[BINDING_KEY], binding,
                "result.json must carry the exact binding",
            )

            # manifest.json on disk
            manifest_on_disk = self._read_json(
                run.root_dir / MANIFEST_FILENAME
            )
            self.assertEqual(
                manifest_on_disk[BINDING_KEY], binding,
                "manifest.json must carry the exact binding",
            )

            # load_run succeeds
            reloaded = load_run(project, run.result["id"])
            self.assertEqual(reloaded.result[BINDING_KEY], binding)

    # ----------------------------------------------------------------
    # 3. manifest-only – result.json is missing researchBinding
    # ----------------------------------------------------------------

    def test_binding_manifest_only_fails(self) -> None:
        """When researchBinding exists only in manifest.json (missing
        from result.json), load_run raises AutoQuantValidationError."""
        with tempfile.TemporaryDirectory() as tmp:
            project, run, _ = self._create_binding_run(tmp)

            result_path = run.root_dir / RESULT_FILENAME
            manifest_path = run.root_dir / MANIFEST_FILENAME

            result = self._read_json(result_path)
            del result[BINDING_KEY]
            self._write_json(result_path, result)

            self._sync_result_hashes(result_path, manifest_path)

            with self.assertRaises(AutoQuantValidationError) as ctx:
                load_run(project, run.result["id"])
            self.assertIn("researchBinding", str(ctx.exception))
    # ----------------------------------------------------------------
    # 4. result-only – manifest.json is missing researchBinding
    # ----------------------------------------------------------------

    def test_binding_result_only_fails(self) -> None:
        """When researchBinding exists only in result.json (missing
        from manifest.json), load_run raises AutoQuantValidationError."""
        with tempfile.TemporaryDirectory() as tmp:
            project, run, _ = self._create_binding_run(tmp)

            manifest_path = run.root_dir / MANIFEST_FILENAME

            manifest = self._read_json(manifest_path)
            del manifest[BINDING_KEY]
            self._write_json(manifest_path, manifest)

            with self.assertRaises(AutoQuantValidationError) as ctx:
                load_run(project, run.result["id"])
            self.assertIn("researchBinding", str(ctx.exception))

    # ----------------------------------------------------------------
    # 5. mismatched values – result.json binding ≠ manifest.json binding
    # ----------------------------------------------------------------

    def test_binding_mismatched_values_fails(self) -> None:
        """When result.json and manifest.json carry different
        researchBinding payloads, load_run raises AutoQuantValidationError."""
        with tempfile.TemporaryDirectory() as tmp:
            project, run, binding = self._create_binding_run(tmp)

            result_path = run.root_dir / RESULT_FILENAME
            manifest_path = run.root_dir / MANIFEST_FILENAME

            result = self._read_json(result_path)
            result[BINDING_KEY]["definitionRef"]["version"] = 999
            self._write_json(result_path, result)

            self._sync_result_hashes(result_path, manifest_path)

            with self.assertRaises(AutoQuantValidationError) as ctx:
                load_run(project, run.result["id"])
            self.assertIn("researchBinding", str(ctx.exception))

    # ----------------------------------------------------------------
    # 6. both present-null – researchBinding is JSON null in both files
    # ----------------------------------------------------------------

    def test_binding_both_present_null_fails(self) -> None:
        """When both result.json and manifest.json carry
        ``researchBinding: null``, load_run raises
        AutoQuantValidationError."""
        with tempfile.TemporaryDirectory() as tmp:
            project, run, _ = self._create_binding_run(tmp)

            result_path = run.root_dir / RESULT_FILENAME
            manifest_path = run.root_dir / MANIFEST_FILENAME

            result = self._read_json(result_path)
            result[BINDING_KEY] = None
            self._write_json(result_path, result)

            manifest = self._read_json(manifest_path)
            manifest[BINDING_KEY] = None
            self._write_json(manifest_path, manifest)

            self._sync_result_hashes(result_path, manifest_path)

            with self.assertRaises(AutoQuantValidationError) as ctx:
                load_run(project, run.result["id"])
            self.assertIn("researchBinding", str(ctx.exception))
