"""Preflight validation for researchBinding before Run directory creation."""

from __future__ import annotations

import tempfile
import unittest

from autoquant.runs import execute_study, list_runs
from autoquant.research_definitions import (
    approve_factor_definition,
    create_experiment_definition_version,
    create_factor_definition_version,
    freeze_experiment_definition,
)
from autoquant.sessions import start_session
from autoquant.studies import create_study
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition
from tests.test_runs import MINIMAL_EXPERIMENT_DEFINITION, MINIMAL_FACTOR_DEFINITION


def _make_approved_factor(project, factor_id="momentum-factor", version=1):
    """Create + approve a minimal factor definition; return the approved context."""
    value = dict(MINIMAL_FACTOR_DEFINITION)
    value["id"] = factor_id
    create_factor_definition_version(project, value)
    return approve_factor_definition(project, factor_id, version)


def _make_frozen_experiment(
    project, session, experiment_id, definition_ref, exp_value=None
):
    """Create + freeze an experiment definition; return the frozen context."""
    if exp_value is None:
        exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
    exp_value["id"] = experiment_id
    exp_value["definitionRef"] = definition_ref
    ctx = create_experiment_definition_version(
        project, session.manifest["id"], exp_value
    )
    return freeze_experiment_definition(
        project, session.manifest["id"], experiment_id, ctx.definition["version"]
    )


def _valid_binding(approved, frozen, session):
    """Return a structurally valid researchBinding dict."""
    return {
        "definitionRef": {
            "kind": approved.definition["kind"].split("-")[1],
            "id": approved.definition["id"],
            "version": approved.definition["version"],
            "contentHash": approved.manifest["contentHash"],
        },
        "experimentDefinitionRef": {
            "kind": "experiment",
            "sessionId": session.manifest["id"],
            "id": frozen.definition["id"],
            "version": frozen.definition["version"],
            "contentHash": frozen.manifest["contentHash"],
        },
    }


def _setup_project_and_baseline(directory):
    """Create workspace/project, study, baseline, session, approved factor, frozen experiment."""
    _, project = make_project(directory)
    approved = _make_approved_factor(project)
    create_study(project, study_definition(study_id="factor-quality"))
    execute_study(project, "factor-quality")  # baseline
    session = start_session(project, "factor-quality")
    exp_def_ref = {
        "kind": "factor",
        "id": approved.definition["id"],
        "version": approved.definition["version"],
    }
    frozen = _make_frozen_experiment(project, session, "momentum-test", exp_def_ref)
    return project, approved, frozen, session


class ResearchBindingPreflightTests(unittest.TestCase):
    """Preflight behaviour tested before a Run directory is created."""

    # ---- None / list / string ----

    def test_none_binding_is_legacy_legal(self):
        """None research_binding is legal (legacy path) and creates a Run."""
        with tempfile.TemporaryDirectory() as directory:
            project, _, _, _ = _setup_project_and_baseline(directory)
            runs_before = len(list_runs(project))
            run = execute_study(project, "factor-quality", research_binding=None)
            self.assertIsNotNone(run.result.get("id"))
            self.assertEqual(len(list_runs(project)), runs_before + 1)

    def test_list_binding_raises_and_creates_no_run(self):
        """A list research_binding must raise AutoQuantValidationError."""
        with tempfile.TemporaryDirectory() as directory:
            project, _, _, _ = _setup_project_and_baseline(directory)
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=[])
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_string_binding_raises_and_creates_no_run(self):
        """A string research_binding must raise AutoQuantValidationError."""
        with tempfile.TemporaryDirectory() as directory:
            project, _, _, _ = _setup_project_and_baseline(directory)
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding="not-an-object")
            self.assertEqual(len(list_runs(project)), runs_before)

    # ---- top-level missing / extra fields ----

    def test_binding_missing_definition_ref_rejected(self):
        """ResearchBinding missing definitionRef is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["definitionRef"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_binding_missing_experiment_definition_ref_rejected(self):
        """ResearchBinding missing experimentDefinitionRef is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["experimentDefinitionRef"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_binding_extra_top_level_field_rejected(self):
        """ResearchBinding with unknown top-level field is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            binding["extraField"] = "should-not-be-here"
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    # ---- definitionRef missing / extra fields ----

    def test_definition_ref_missing_version_rejected(self):
        """definitionRef missing 'version' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["definitionRef"]["version"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_definition_ref_missing_content_hash_rejected(self):
        """definitionRef missing 'contentHash' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["definitionRef"]["contentHash"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_definition_ref_missing_kind_rejected(self):
        """definitionRef missing 'kind' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["definitionRef"]["kind"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_definition_ref_missing_id_rejected(self):
        """definitionRef missing 'id' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["definitionRef"]["id"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_definition_ref_extra_field_rejected(self):
        """definitionRef with unknown field is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            binding["definitionRef"]["extra"] = "nope"
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    # ---- experimentDefinitionRef missing / extra fields ----

    def test_experiment_definition_ref_missing_session_id_rejected(self):
        """experimentDefinitionRef missing 'sessionId' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["experimentDefinitionRef"]["sessionId"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_experiment_definition_ref_missing_kind_rejected(self):
        """experimentDefinitionRef missing 'kind' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["experimentDefinitionRef"]["kind"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_experiment_definition_ref_missing_id_rejected(self):
        """experimentDefinitionRef missing 'id' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["experimentDefinitionRef"]["id"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_experiment_definition_ref_missing_version_rejected(self):
        """experimentDefinitionRef missing 'version' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["experimentDefinitionRef"]["version"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_experiment_definition_ref_missing_content_hash_rejected(self):
        """experimentDefinitionRef missing 'contentHash' is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            del binding["experimentDefinitionRef"]["contentHash"]
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_experiment_definition_ref_extra_field_rejected(self):
        """experimentDefinitionRef with unknown field is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            project, approved, frozen, session = _setup_project_and_baseline(directory)
            binding = _valid_binding(approved, frozen, session)
            binding["experimentDefinitionRef"]["extra"] = "nope"
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    # ---- ExperimentDefinition.definitionRef version mismatch ----

    def test_experiment_definition_ref_version_mismatch_rejected(self):
        """ExperimentDefinition.definitionRef same kind/id but different version is rejected."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            # Create factor v1 and approve
            v1_val = dict(MINIMAL_FACTOR_DEFINITION)
            v1_val["id"] = "momentum-factor"
            create_factor_definition_version(project, v1_val)
            approved_v1 = approve_factor_definition(project, "momentum-factor", 1)

            # Create factor v2 (next version) and approve
            from autoquant.research_definitions import new_definition_version
            v2_val = new_definition_version(approved_v1.definition, {}, status="draft")
            create_factor_definition_version(project, v2_val)
            approved_v2 = approve_factor_definition(project, "momentum-factor", v2_val["version"])

            create_study(project, study_definition(study_id="factor-quality"))
            execute_study(project, "factor-quality")  # baseline
            session = start_session(project, "factor-quality")

            # Experiment references factor v1
            exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
            exp_value["id"] = "momentum-test"
            exp_value["definitionRef"] = {
                "kind": "factor",
                "id": "momentum-factor",
                "version": approved_v1.definition["version"],
            }
            exp_ctx = create_experiment_definition_version(
                project, session.manifest["id"], exp_value
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "momentum-test",
                exp_ctx.definition["version"]
            )

            # Binding references factor v2 — same kind/id, different version
            binding = {
                "definitionRef": {
                    "kind": "factor",
                    "id": "momentum-factor",
                    "version": approved_v2.definition["version"],
                    "contentHash": approved_v2.manifest["contentHash"],
                },
                "experimentDefinitionRef": {
                    "kind": "experiment",
                    "sessionId": session.manifest["id"],
                    "id": "momentum-test",
                    "version": frozen.definition["version"],
                    "contentHash": frozen.manifest["contentHash"],
                },
            }
            runs_before = len(list_runs(project))
            with self.assertRaises(AutoQuantValidationError):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)


if __name__ == "__main__":
    unittest.main()
