from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import jsonschema

from autoquant.runs import (
    RUN_RESULT_JSON_SCHEMA,
    _harness_source_hash,
    execute_study,
    harness_identity,
    list_runs,
    load_run,
    same_harness_runtime,
)
from autoquant.research_definitions import (
    approve_factor_definition,
    create_experiment_definition_version,
    create_factor_definition_version,
    freeze_experiment_definition,
)
from autoquant.studies import (
    StudyResearchRequest,
    bind_upstream_evidence,
    create_study,
    hash_file,
)
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import (
    FAILURE_JUDGE,
    MALFORMED_JUDGE,
    TIMEOUT_JUDGE,
    make_project,
    request_definition,
    study_definition,
)

# ---- factor definition helpers ----

MINIMAL_FACTOR_DEFINITION = {
    "schemaVersion": 1,
    "kind": "autoquant-factor-definition",
    "id": "momentum-factor",
    "version": 1,
    "status": "draft",
    "createdAt": "2026-06-01T00:00:00Z",
    "lineage": {"parentVersion": None},
    "hypothesis": "Price momentum predicts future returns.",
    "calculation": {
        "kind": "source",
        "identity": "factors/momentum.py:Momentum",
        "sourceHash": "a" * 64,
    },
    "parameters": {"window": 20},
    "output": {"direction": "higher", "unit": "annualized-return"},
    "dataDependencies": [
        {
            "packageId": "core-prices",
            "version": "v1",
            "fields": ["close"],
            "availability": {
                "pointInTime": True,
                "marketClock": {"id": "XNYS", "version": "v1"},
            },
        }
    ],
    "missingDataPolicy": "drop-row",
    "cohort": {"kind": "equity", "identity": "US-common-stock"},
    "expectedHorizon": "1-month",
    "requiredTests": ["monotonicity"],
    "failureGates": ["negative-sharpe"],
}

MINIMAL_EXPERIMENT_DEFINITION = {
    "schemaVersion": 1,
    "kind": "autoquant-experiment-definition",
    "id": "momentum-test",
    "version": 1,
    "status": "draft",
    "createdAt": "2026-06-01T00:00:00Z",
    "lineage": {"parentVersion": None},
    "definitionRef": {"kind": "factor", "id": "momentum-factor", "version": 1},
    "data": {"packageId": "core-prices", "version": "v1"},
    "subject": {"kind": "factor", "id": "momentum-factor", "version": 1},
    "outcome": {"name": "sharpe-ratio", "horizon": "1-month"},
    "benchmark": {"id": "spx-equal-weight", "version": "v1"},
    "costPolicy": {"model": "fixed", "bps": 5},
    "splitPolicy": {"kind": "time-series", "train": 0.7},
    "robustness": {"checks": ["out-of-time"]},
    "selectionAdjustment": {"method": "none"},
    "holdoutPolicy": {"kind": "external-temporal", "sealed": True},
    "executorPolicy": {"kind": "python-judge"},
    "budget": {
        "candidateLimit": 10,
        "wallTimeSeconds": 600,
        "cpuSeconds": 600,
        "gpuSeconds": 0,
        "cost": {"currency": "USD", "amount": 1000},
    },
    "stopConditions": ["candidate-limit"],
}


def _hash_sha256(value: str) -> str:
    from hashlib import sha256
    return sha256(value.encode()).hexdigest()


class ImmutableRunTests(unittest.TestCase):
    def test_harness_source_hash_covers_complete_runtime_closure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "autoquant"
            (package / "project_templates" / "factor").mkdir(parents=True)
            (package / "studio_assets").mkdir()
            (package / "workspace_skills" / "fetch").mkdir(parents=True)
            (package / "runtime.py").write_text("VALUE = 1\n")
            template = package / "project_templates" / "factor" / "program.md"
            template.write_text("factor contract\n")
            studio = package / "studio_assets" / "studio.js"
            studio.write_text("export const value = 1;\n")
            skill = package / "workspace_skills" / "fetch" / "SKILL.md"
            skill.write_text("fetch contract\n")

            baseline = _harness_source_hash(package)
            for path, replacement in (
                (package / "runtime.py", "VALUE = 2\n"),
                (template, "factor contract v2\n"),
                (studio, "export const value = 2;\n"),
                (skill, "fetch contract v2\n"),
            ):
                original = path.read_text()
                path.write_text(replacement)
                changed = _harness_source_hash(package)
                self.assertNotEqual(changed, baseline, path)
                path.write_text(original)
                self.assertEqual(_harness_source_hash(package), baseline)

            (package / "_build_identity.py").write_text(
                "BUILD_COMMIT = 'a' * 40\n"
            )
            cache = package / "__pycache__"
            cache.mkdir()
            (cache / "runtime.cpython-311.pyc").write_bytes(b"cache")
            self.assertEqual(_harness_source_hash(package), baseline)

    def test_run_freezes_study_request_and_exact_upstream_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition(study_id="path-stress"))
            prior = execute_study(project, "path-stress")
            requests = project.root_dir / "requests"
            requests.mkdir()
            (requests / "recovery.json").write_text(
                json.dumps(request_definition()) + "\n",
                encoding="utf-8",
            )
            upstream = bind_upstream_evidence(
                project,
                prior.result["id"],
                ["artifacts/report.json"],
            )
            study = create_study(
                project,
                study_definition(
                    study_id="drawdown-recovery",
                    dependencies=["requests/recovery.json"],
                    research_request=StudyResearchRequest(
                        "requests/recovery.json"
                    ),
                    upstream_evidence=upstream,
                ),
            )
            run = execute_study(project, study.definition.id)
            evidence_root = (
                run.root_dir
                / "inputs"
                / "upstream-evidence"
                / prior.result["id"]
            )

            self.assertEqual(
                run.result["researchRequest"]["path"],
                "requests/recovery.json",
            )
            self.assertEqual(
                run.result["upstreamEvidence"]["run_id"],
                prior.result["id"],
            )
            self.assertTrue((evidence_root / "binding.json").is_file())
            frozen_artifact = evidence_root / "artifacts" / "report.json"
            self.assertEqual(
                frozen_artifact.read_bytes(),
                (prior.root_dir / "artifacts" / "report.json").read_bytes(),
            )
            self.assertTrue(
                (
                    run.root_dir
                    / "inputs"
                    / "dependency-sources"
                    / "requests"
                    / "recovery.json"
                ).is_file()
            )
            self.assertEqual(load_run(project, run.result["id"]), run)
            jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)

            frozen_artifact.write_text("tampered\n", encoding="utf-8")
            manifest_path = run.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            relative = frozen_artifact.relative_to(run.root_dir).as_posix()
            manifest["files"][relative] = hash_file(frozen_artifact)
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Frozen upstream artifact differs",
            ):
                load_run(project, run.result["id"])

    def test_harness_runtime_identity_excludes_repository_provenance(self) -> None:
        recorded = {
            "id": "autoquant.python-judge",
            "version": "0.9.0",
            "commit": "a" * 40,
            "dirty": False,
            "sourceHash": "b" * 64,
            "python": "3.11.14",
        }
        research_commit = {
            **recorded,
            "commit": "c" * 40,
            "dirty": True,
        }

        self.assertTrue(same_harness_runtime(recorded, research_commit))
        self.assertFalse(
            same_harness_runtime(
                recorded,
                {**research_commit, "sourceHash": "d" * 64},
            )
        )

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
            self.assertEqual(run.result["harness"], harness_identity())
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

    # ---- researchBinding tests ----

    def test_legacy_run_unchanged_without_research_binding(self) -> None:
        """Legacy Run is byte-compatible when research_binding is None."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            create_study(project, study_definition())
            run = execute_study(project, "factor-quality")
            self.assertNotIn("researchBinding", run.result)
            self.assertEqual(load_run(project, run.result["id"]), run)
            jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)

    def test_exact_approved_frozen_binding_persists_and_loads(self) -> None:
        """researchBinding with exact approved factor and frozen experiment persists and loads."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            # Create + approve a factor definition
            factor_ctx = create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(
                project, "momentum-factor", factor_ctx.definition["version"]
            )

            # Load a session (required for experiment definition storage)
            from autoquant.sessions import start_session

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            session = start_session(project, "factor-quality")

            # Create + freeze an experiment definition
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
                project,
                "factor-quality",
                research_binding=binding,
            )
            self.assertEqual(run.result["researchBinding"], binding)
            reloaded = load_run(project, run.result["id"])
            self.assertEqual(reloaded.result["researchBinding"], binding)
            jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)

    def test_binding_fails_on_draft_experiment(self) -> None:
        """Binding fails before Run creation when experiment is still draft."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(project, "momentum-factor", 1)

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
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
            # experiment is draft, NOT frozen
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
                    "version": experiment_ctx.definition["version"],
                    "contentHash": experiment_ctx.manifest["contentHash"],
                },
            }
            runs_before = len(list_runs(project))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "not frozen"
            ):
                execute_study(project, "factor-quality", research_binding=binding)
            # No new Run directory was created
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_binding_fails_on_wrong_hash(self) -> None:
        """Binding fails with tampered contentHash."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(project, "momentum-factor", 1)

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
            session = start_session(project, "factor-quality")

            binding = {
                "definitionRef": {
                    "kind": "factor",
                    "id": "momentum-factor",
                    "version": approved.definition["version"],
                    "contentHash": "f" * 64,  # wrong
                },
                "experimentDefinitionRef": {
                    "kind": "experiment",
                    "sessionId": session.manifest["id"],
                    "id": "momentum-test",
                    "version": 1,
                    "contentHash": approved.manifest["contentHash"],
                },
            }
            runs_before = len(list_runs(project))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "contentHash does not match"
            ):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_binding_fails_on_unapproved_definition(self) -> None:
        """Binding fails when factor definition is draft, not approved."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            factor_ctx = create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            # NOT approved

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
            session = start_session(project, "factor-quality")

            binding = {
                "definitionRef": {
                    "kind": "factor",
                    "id": "momentum-factor",
                    "version": 1,
                    "contentHash": factor_ctx.manifest["contentHash"],
                },
                "experimentDefinitionRef": {
                    "kind": "experiment",
                    "sessionId": session.manifest["id"],
                    "id": "momentum-test",
                    "version": 1,
                    "contentHash": factor_ctx.manifest["contentHash"],
                },
            }
            runs_before = len(list_runs(project))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "not approved"
            ):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_binding_fails_on_link_mismatch(self) -> None:
        """Binding fails when experiment's definitionRef doesn't match the definitionRef."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            # Create factor "alpha-v1" and approve it
            alpha = dict(MINIMAL_FACTOR_DEFINITION)
            alpha["id"] = "alpha-v1"
            create_factor_definition_version(project, alpha)
            approved_alpha = approve_factor_definition(project, "alpha-v1", 1)

            # Create factor "beta-v2" and approve it
            beta = dict(MINIMAL_FACTOR_DEFINITION)
            beta["id"] = "beta-v2"
            beta["version"] = 1
            create_factor_definition_version(project, beta)
            approved_beta = approve_factor_definition(project, "beta-v2", 1)

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
            session = start_session(project, "factor-quality")

            # Experiment references alpha-v1
            exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
            exp_value["id"] = "alpha-experiment"
            exp_value["definitionRef"] = {
                "kind": "factor",
                "id": "alpha-v1",
                "version": approved_alpha.definition["version"],
            }
            experiment_ctx = create_experiment_definition_version(
                project, session.manifest["id"], exp_value,
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "alpha-experiment",
                experiment_ctx.definition["version"],
            )

            # Binding says beta-v2 — link mismatch
            binding = {
                "definitionRef": {
                    "kind": "factor",
                    "id": "beta-v2",
                    "version": approved_beta.definition["version"],
                    "contentHash": approved_beta.manifest["contentHash"],
                },
                "experimentDefinitionRef": {
                    "kind": "experiment",
                    "sessionId": session.manifest["id"],
                    "id": "alpha-experiment",
                    "version": frozen.definition["version"],
                    "contentHash": frozen.manifest["contentHash"],
                },
            }
            runs_before = len(list_runs(project))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "definitionRef does not match",
            ):
                execute_study(project, "factor-quality", research_binding=binding)
            self.assertEqual(len(list_runs(project)), runs_before)

    def test_run_file_tamper_fails(self) -> None:
        """Tampering Run result file fails load."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(project, "momentum-factor", 1)

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
            session = start_session(project, "factor-quality")

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

            result_path = run.root_dir / "result.json"
            manifest_path = run.root_dir / "manifest.json"
            result = json.loads(result_path.read_text())
            result["researchBinding"]["definitionRef"]["version"] = 999
            result_path.write_text(json.dumps(result))
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["result.json"] = hash_file(result_path)
            manifest["resultHash"] = manifest["files"]["result.json"]
            manifest_path.write_text(json.dumps(manifest))

            with self.assertRaisesRegex(
                AutoQuantValidationError, "must equal the terminal manifest"
            ):
                load_run(project, run.result["id"])

    def test_referenced_artifact_tamper_fails(self) -> None:
        """Tampering the definition on disk after the Run fails load."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved = approve_factor_definition(project, "momentum-factor", 1)

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
            session = start_session(project, "factor-quality")

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

            # Tamper the factor definition on disk
            factor_def_dir = approved.root_dir / "definition.json"
            definition = json.loads(factor_def_dir.read_text())
            definition["hypothesis"] = "tampered hypothesis"
            factor_def_dir.write_text(json.dumps(definition))

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                r"content hash mismatch",
            ):
                load_run(project, run.result["id"])

    def test_newer_definition_version_does_not_move_old_run(self) -> None:
        """A newer approved definition version doesn't move the old bound Run."""
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)

            create_factor_definition_version(
                project, dict(MINIMAL_FACTOR_DEFINITION)
            )
            approved_v1 = approve_factor_definition(project, "momentum-factor", 1)

            create_study(project, study_definition(study_id="factor-quality"))
            baseline = execute_study(project, "factor-quality")
            from autoquant.sessions import start_session
            session = start_session(project, "factor-quality")

            exp_value = dict(MINIMAL_EXPERIMENT_DEFINITION)
            exp_value["definitionRef"] = {
                "kind": "factor",
                "id": "momentum-factor",
                "version": approved_v1.definition["version"],
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
                    "version": approved_v1.definition["version"],
                    "contentHash": approved_v1.manifest["contentHash"],
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

            # Create v2 (approved as well)
            from autoquant.research_definitions import new_definition_version
            v2_def = new_definition_version(
                approved_v1.definition, {"hypothesis": "Revised momentum hypothesis"},
                status="draft",
            )
            create_factor_definition_version(project, v2_def)
            approve_factor_definition(project, "momentum-factor", v2_def["version"])

            # The old Run still loads with v1 bound
            reloaded = load_run(project, run.result["id"])
            self.assertEqual(reloaded.result["researchBinding"]["definitionRef"]["version"], approved_v1.definition["version"])
            self.assertEqual(
                reloaded.result["researchBinding"]["definitionRef"]["contentHash"],
                approved_v1.manifest["contentHash"],
            )


if __name__ == "__main__":
    unittest.main()
