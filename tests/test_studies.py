from __future__ import annotations

import json
import tempfile
import unittest

from autoquant.studies import create_study, hash_json, list_studies, load_study
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition


class StudyContractTests(unittest.TestCase):
    def test_legacy_dataset_preserves_v1_serialization_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            definition = study_definition()
            self.assertNotIn("paths", definition.to_dict()["dataset"])
            study = create_study(project, definition)
            self.assertEqual(
                study.dataset_hash,
                hash_json(definition.to_dict()["dataset"]),
            )
            self.assertEqual(study.dataset_hashes, {})

    def test_content_locked_dataset_hash_tracks_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            data = project.root_dir / "data" / "bars"
            data.mkdir()
            source = data / "AAA.csv"
            source.write_text("timestamp,close\n2026-01-01,1\n", encoding="utf-8")
            create_study(
                project,
                study_definition(dataset_paths=["bars/**"]),
            )
            before = load_study(project, "factor-quality")
            self.assertEqual(list(before.dataset_hashes), ["bars/AAA.csv"])
            source.write_text("timestamp,close\n2026-01-01,2\n", encoding="utf-8")
            after = load_study(project, "factor-quality")
            self.assertNotEqual(before.dataset_hash, after.dataset_hash)
            self.assertNotEqual(before.input_hash, after.input_hash)

    def test_study_pins_program_judge_sources_editable_sources_and_dataset(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            study = create_study(project, study_definition())

            self.assertEqual(study.definition.id, "factor-quality")
            self.assertIn("judges/evaluate.py", study.judge_hashes)
            self.assertIn("factors/candidate.py", study.editable_hashes)
            self.assertEqual(len(study.study_hash), 64)
            self.assertEqual(len(study.program_hash), 64)
            self.assertEqual(len(study.judge_hash), 64)
            self.assertEqual(len(study.source_hash), 64)
            self.assertEqual(len(study.dataset_hash), 64)
            self.assertEqual(len(study.input_hash), 64)
            self.assertIn("fixed", study.program_path.read_text())

            summaries = list_studies(project)
            self.assertEqual([item.id for item in summaries], ["factor-quality"])
            self.assertEqual(summaries[0].subject_kind, "factor")
            self.assertEqual(summaries[0].primary_metric, "score")

    def test_editable_closure_cannot_contain_judge_or_study_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "strategy, factor, or model source directories",
            ):
                create_study(
                    project,
                    study_definition(editable=["judges/**"]),
                )

        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "strategy, factor, or model source directories",
            ):
                create_study(
                    project,
                    study_definition(editable=["studies/**"]),
                )

    def test_editable_closure_cannot_claim_data_runs_or_cache(self) -> None:
        for pattern in ("data/**", "runs/**", ".autoquant/**"):
            with self.subTest(pattern=pattern), tempfile.TemporaryDirectory() as directory:
                _, project = make_project(directory)
                with self.assertRaisesRegex(
                    AutoQuantValidationError,
                    "strategy, factor, or model source directories",
                ):
                    create_study(
                        project,
                        study_definition(editable=[pattern]),
                    )

    def test_study_hash_changes_only_for_the_identity_surface_that_changed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            first = create_study(project, study_definition())
            original_study_hash = first.study_hash
            original_judge_hash = first.judge_hash
            original_source_hash = first.source_hash

            (project.root_dir / "factors" / "candidate.py").write_text(
                "SCORE = 2.5\n",
                encoding="utf-8",
            )
            changed = load_study(project, "factor-quality")
            self.assertEqual(changed.study_hash, original_study_hash)
            self.assertEqual(changed.judge_hash, original_judge_hash)
            self.assertNotEqual(changed.source_hash, original_source_hash)
            self.assertNotEqual(changed.input_hash, first.input_hash)

    def test_unknown_keys_and_judge_outside_fixed_closure_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            study = create_study(project, study_definition())
            raw = json.loads(study.manifest_path.read_text())
            raw["unknown"] = True
            study.manifest_path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(AutoQuantValidationError, "Unknown field"):
                load_study(project, "factor-quality")

        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            definition = study_definition()
            definition = type(definition)(
                **{
                    **definition.__dict__,
                    "judge": type(definition.judge)(
                        "python",
                        "factors/candidate.py",
                        ["judges/**"],
                        [],
                        10,
                    ),
                }
            )
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "entrypoint must be included",
            ):
                create_study(project, definition)


if __name__ == "__main__":
    unittest.main()
