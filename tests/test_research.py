from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from autoquant.research import list_campaigns, load_campaign, run_campaign
from autoquant.research_definitions import (
    approve_factor_definition,
    create_experiment_definition_version,
    create_factor_definition_version,
    freeze_experiment_definition,
    load_experiment_definition,
)
from autoquant.sessions import list_experiments, load_session, start_session
from autoquant.studies import create_study, hash_file
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import SUCCESS_JUDGE, make_project, study_definition
from tests.test_research_definitions import experiment_definition, factor_definition


RESEARCHER = """\
import json
import os
from pathlib import Path

brief = json.loads(input())
candidate = Path(os.environ["AUTOQUANT_WORKTREE"]) / "factors/candidate.py"
turn = brief["turn"]
if turn == 1:
    candidate.write_text("SCORE = 2.0\\n")
    response = {
        "schema_version": 1,
        "action": "propose",
        "strategy": "increase-score",
        "hypothesis": "Increase the synthetic score.",
        "expected_effect": "Beat the locked baseline.",
    }
elif turn == 2:
    candidate.write_text("SCORE = 1.0\\n")
    response = {
        "schema_version": 1,
        "action": "propose",
        "strategy": "decrease-score",
        "hypothesis": "Test a weaker synthetic score.",
        "expected_effect": "Challenge the current leader.",
    }
else:
    response = {
        "schema_version": 1,
        "action": "stop",
        "reason": "The bounded demonstration is complete.",
    }
print(json.dumps(response))
"""


class ExternalResearchCampaignTests(unittest.TestCase):
    def _setup(self, directory: str):
        _, project = make_project(directory)
        create_study(project, study_definition())
        session = start_session(project, "factor-quality")
        return project, session

    def _script(self, directory: str, source: str) -> str:
        path = Path(directory) / "researcher.py"
        path.write_text(source, encoding="utf-8")
        return f"{shlex.quote(sys.executable)} {shlex.quote(str(path))}"

    def test_campaign_drives_keep_revert_then_stop_and_verifies_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=5,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )

            self.assertEqual(campaign.result["status"], "stopped")
            self.assertEqual(campaign.result["turnsCompleted"], 3)
            self.assertEqual(campaign.result["verdicts"]["KEEP"], 1)
            self.assertEqual(campaign.result["verdicts"]["REVERT"], 1)
            self.assertEqual(len(campaign.result["experiments"]), 2)
            progress = json.loads(
                (campaign.root_dir / "progress.json").read_text()
            )
            self.assertEqual(progress["status"], "stopped")
            self.assertEqual(progress["phase"], "terminal")
            self.assertEqual(progress["experiments"], campaign.result["experiments"])
            current = load_session(project, session.manifest["id"])
            self.assertEqual(current.manifest["leader"]["value"], 2.0)
            self.assertEqual(
                (
                    current.worktree_project.root_dir / "factors/candidate.py"
                ).read_text(),
                "SCORE = 2.0\n",
            )
            self.assertEqual(
                (project.root_dir / "factors/candidate.py").read_text(),
                "SCORE = 1.25\n",
            )
            self.assertEqual(
                [item.verdict for item in list_experiments(project, current)],
                ["KEEP", "REVERT"],
            )
            summaries = list_campaigns(project, current)
            self.assertEqual([item.id for item in summaries], [campaign.result["id"]])
            loaded = load_campaign(project, current, campaign.result["id"])
            self.assertEqual(loaded.result, campaign.result)
            first_brief = json.loads(
                (campaign.root_dir / "turns/turn-0001/input.json").read_text()
            )
            third_brief = json.loads(
                (campaign.root_dir / "turns/turn-0003/input.json").read_text()
            )
            self.assertEqual(first_brief["editablePaths"], ["factors/**"])
            self.assertEqual(third_brief["leader"]["value"], 2.0)
            self.assertEqual(
                [item["verdict"] for item in third_brief["campaignHistory"]],
                ["KEEP", "REVERT"],
            )
            self.assertNotIn(
                self._script(directory, RESEARCHER),
                json.dumps(campaign.result),
            )

    def test_turn_budget_is_terminal_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )

            self.assertEqual(campaign.result["status"], "budget_exhausted")
            self.assertEqual(campaign.result["turnsCompleted"], 1)
            self.assertEqual(campaign.result["verdicts"]["KEEP"], 1)
            self.assertEqual(campaign.result["budget"]["maxTurns"], 1)

        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=5,
                max_wall_seconds=1,
                turn_timeout_seconds=1,
            )

            self.assertEqual(campaign.result["status"], "budget_exhausted")
            self.assertEqual(campaign.result["turnsCompleted"], 0)
            self.assertEqual(campaign.result["experiments"], [])
            self.assertIn("wall-clock", campaign.result["reason"])

    def test_candidate_compute_cost_provider_and_holdout_budgets_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=5,
                max_candidates=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )
            self.assertEqual(campaign.result["status"], "budget_exhausted")
            self.assertEqual(campaign.result["budget"]["used"]["candidates"], 1)
            self.assertEqual(campaign.result["budget"]["remaining"]["candidates"], 0)
            self.assertEqual(
                list_campaigns(project, load_session(project, session.manifest["id"]))[0].to_dict()["budget"],
                campaign.result["budget"],
            )
            self.assertIn("candidate", campaign.result["reason"])

        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                private_executor_requested=True,
                private_executor_available=False,
            )
            self.assertEqual(campaign.result["status"], "blocked")
            self.assertEqual(campaign.result["experiments"], [])
            self.assertEqual(campaign.result["budget"]["executorPolicy"]["default"], "cpu")

        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_cost=10.0,
                cost_currency="USD",
                cost_telemetry_available=False,
            )
            self.assertEqual(campaign.result["status"], "blocked")
            self.assertEqual(campaign.result["budget"]["costTelemetry"], "unknown")
            self.assertFalse(campaign.result["budget"]["used"]["cost"]["known"])
            self.assertIsNone(campaign.result["budget"]["used"]["cost"]["amount"])

        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            with self.assertRaises(AutoQuantValidationError):
                run_campaign(
                    project,
                    session.manifest["id"],
                    self._script(directory, RESEARCHER),
                    holdout_sealed=False,
                )

    def test_protocol_and_command_failures_restore_the_leader(self) -> None:
        cases = {
            "exit": (
                """\
from pathlib import Path
import os
Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text("SCORE = 8.0\\n")
raise SystemExit(7)
""",
                "researcher.exit",
                5,
            ),
            "timeout": (
                """\
from pathlib import Path
import os
import time
Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text("SCORE = 8.0\\n")
time.sleep(2)
""",
                "researcher.timeout",
                1,
            ),
            "malformed": (
                'print("{not json")\n',
                "researcher.response-json",
                5,
            ),
            "fixed-mutation": (
                """\
import json
import os
from pathlib import Path
root = Path(os.environ["AUTOQUANT_WORKTREE"])
(root / "factors/candidate.py").write_text("SCORE = 8.0\\n")
(root / "judges/evaluate.py").write_text("raise SystemExit(9)\\n")
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "cheat",
    "hypothesis": "Change the locked Judge.",
    "expected_effect": "Illegally improve the result.",
}))
""",
                "session.lock-stale",
                5,
            ),
            "unchanged": (
                """\
import json
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "no-op",
    "hypothesis": "Submit the unchanged source.",
    "expected_effect": "No change.",
}))
""",
                "experiment.unchanged",
                5,
            ),
            "authority-claim": (
                """\
import json
import os
from pathlib import Path
Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text("SCORE = 8.0\\n")
print(json.dumps({
    "schema_version": 1,
    "action": "propose",
    "strategy": "self-judged",
    "hypothesis": "Claim authority the Researcher does not have.",
    "expected_effect": "Attempt to bypass the fixed Judge.",
    "verdict": "KEEP",
}))
""",
                "schema.unknown",
                5,
            ),
            "changed-stop": (
                """\
import json
import os
from pathlib import Path
Path(os.environ["AUTOQUANT_WORKTREE"], "factors/candidate.py").write_text("SCORE = 8.0\\n")
print(json.dumps({
    "schema_version": 1,
    "action": "stop",
    "reason": "Stop after an unreviewed edit.",
}))
""",
                "researcher.stop-changed-source",
                5,
            ),
        }
        for name, (source, code, timeout) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                project, session = self._setup(directory)
                campaign = run_campaign(
                    project,
                    session.manifest["id"],
                    self._script(directory, source),
                    max_turns=2,
                    max_wall_seconds=30,
                    turn_timeout_seconds=timeout,
                )

                self.assertEqual(campaign.result["status"], "failed")
                self.assertEqual(campaign.result["errors"][0]["code"], code)
                current = load_session(project, session.manifest["id"])
                self.assertEqual(
                    (
                        current.worktree_project.root_dir / "factors/candidate.py"
                    ).read_text(),
                    "SCORE = 1.25\n",
                )
                self.assertEqual(
                    (
                        current.worktree_project.root_dir / "judges/evaluate.py"
                    ).read_text(),
                    SUCCESS_JUDGE,
                )
                load_campaign(project, current, campaign.result["id"])

    def test_campaign_loader_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )
            result_path = campaign.root_dir / "result.json"
            value = json.loads(result_path.read_text())
            value["reason"] = "tampered"
            result_path.write_text(json.dumps(value))

            with self.assertRaisesRegex(AutoQuantValidationError, "files changed"):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )

    def test_campaign_loader_rejects_rehashed_invalid_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )
            result_path = campaign.root_dir / "result.json"
            result = json.loads(result_path.read_text())
            result["verdicts"]["KEEP"] = 9
            result_path.write_text(json.dumps(result))
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            result_hash = hash_file(result_path)
            manifest["files"]["result.json"] = result_hash
            manifest["resultHash"] = result_hash
            manifest_path.write_text(json.dumps(manifest))

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Verdict counts differ",
            ):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )

    def test_campaign_with_exact_frozen_experiment_definition(self) -> None:
        """Campaign starts and persists the exact frozen ExperimentDefinition reference."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            self.assertIn("experimentDefinitionRef", campaign.result)
            self.assertEqual(campaign.result["experimentDefinitionRef"], ref)
            self.assertEqual(campaign.result["status"], "budget_exhausted")
            # Verify the progress also contains it
            progress = json.loads(
                (campaign.root_dir / "progress.json").read_text()
            )
            self.assertIn("experimentDefinitionRef", progress)
            self.assertEqual(progress["experimentDefinitionRef"], ref)
            # Reload still validates
            loaded = load_campaign(
                project,
                load_session(project, session.manifest["id"]),
                campaign.result["id"],
            )
            self.assertEqual(loaded.result["experimentDefinitionRef"], ref)

    def test_campaign_rejects_non_frozen_experiment_definition(self) -> None:
        """Draft ExperimentDefinition must be rejected before any file is created."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            draft = create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            self.assertEqual(draft.definition["status"], "draft")
            ref = {
                "id": draft.definition["id"],
                "version": draft.definition["version"],
                "contentHash": draft.manifest["contentHash"],
            }
            with self.assertRaises(AutoQuantValidationError) as caught:
                run_campaign(
                    project,
                    session.manifest["id"],
                    self._script(directory, RESEARCHER),
                    experiment_definition_ref=ref,
                )
            self.assertIn("frozen", str(caught.exception))

    def test_campaign_rejects_wrong_hash_experiment_definition(self) -> None:
        """Wrong contentHash fails before campaign/staging directories change."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": "b" * 64,  # Wrong hash
            }
            with self.assertRaises(AutoQuantValidationError) as caught:
                run_campaign(
                    project,
                    session.manifest["id"],
                    self._script(directory, RESEARCHER),
                    experiment_definition_ref=ref,
                )
            self.assertIn("contentHash", str(caught.exception))

    def test_campaign_rejects_unknown_experiment_definition(self) -> None:
        """Fully unknown id/version reference fails before any file is created."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            ref = {
                "id": "nonexistent-experiment",
                "version": 99,
                "contentHash": "a" * 64,
            }
            with self.assertRaises(AutoQuantValidationError):
                run_campaign(
                    project,
                    session.manifest["id"],
                    self._script(directory, RESEARCHER),
                    experiment_definition_ref=ref,
                )

    def test_campaign_rejects_invalid_ref_shape(self) -> None:
        """Extra keys, missing keys, wrong types all fail validation."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            bad_refs = [
                {"id": "x", "version": 1},  # missing contentHash
                {"id": "x", "contentHash": "a" * 64},  # missing version
                {"version": 1, "contentHash": "a" * 64},  # missing id
                {"id": "x", "version": 1, "contentHash": "a" * 64, "extra": True},  # extra key
                {"id": "", "version": 1, "contentHash": "a" * 64},  # empty id
                {"id": "x", "version": 0, "contentHash": "a" * 64},  # version < 1
                {"id": "x", "version": 1, "contentHash": "NOT_HEX"},  # bad hash
            ]
            for bad_ref in bad_refs:
                with self.subTest(ref=bad_ref), self.assertRaises(AutoQuantValidationError):
                    run_campaign(
                        project,
                        session.manifest["id"],
                        self._script(directory, RESEARCHER),
                        experiment_definition_ref=bad_ref,
                    )

    def test_experiment_definition_tamper_fails_on_reload(self) -> None:
        """Later tampering of referenced ExperimentDefinition fails on load."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            self.assertIn("experimentDefinitionRef", campaign.result)
            # Tamper with the definition on disk
            def_path = frozen.root_dir / "definition.json"
            original = def_path.read_text()
            def_path.write_text('{"tampered": true}')
            try:
                with self.assertRaises(AutoQuantValidationError) as caught:
                    load_campaign(
                        project,
                        load_session(project, session.manifest["id"]),
                        campaign.result["id"],
                    )
                self.assertIn("hash", str(caught.exception).lower())
            finally:
                def_path.write_text(original)

    def test_newer_experiment_definition_version_does_not_move_bound_campaign(self) -> None:
        """Creating a newer version never moves or re-interprets an older bound Campaign."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref_v1 = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref_v1,
            )
            self.assertEqual(campaign.result["experimentDefinitionRef"]["version"], 2)
            # Create a newer version (v3)
            newer = experiment_definition(version=3, status="draft")
            newer["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            newer["id"] = "quality-momentum-validation"
            create_experiment_definition_version(
                project, session.manifest["id"], newer
            )
            freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 3
            )
            # Reload the Campaign — it must still reference version 2
            loaded = load_campaign(
                project,
                load_session(project, session.manifest["id"]),
                campaign.result["id"],
            )
            self.assertEqual(loaded.result["experimentDefinitionRef"]["version"], 2)
            self.assertEqual(loaded.result["experimentDefinitionRef"]["contentHash"], ref_v1["contentHash"])

    # ----------------------------------------------------------------
    # Focused gap-fix tests
    # ----------------------------------------------------------------

    def test_legacy_no_ref_has_no_experiment_definition_ref_anywhere(self) -> None:
        """When experiment_definition_ref is None, identity/result/progress/manifest
        MUST NOT contain the key at all."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )
            # experiment_definition_ref must be absent from result
            self.assertNotIn("experimentDefinitionRef", campaign.result)
            # absent from progress
            progress = json.loads(
                (campaign.root_dir / "progress.json").read_text()
            )
            self.assertNotIn("experimentDefinitionRef", progress)
            # absent from manifest
            manifest = json.loads(
                (campaign.root_dir / "manifest.json").read_text()
            )
            self.assertNotIn("experimentDefinitionRef", manifest)

    def test_bound_ref_equality_across_result_progress_manifest(self) -> None:
        """A bound Campaign MUST persist identical experimentDefinitionRef in
        result, terminal progress, and manifest."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            progress = json.loads(
                (campaign.root_dir / "progress.json").read_text()
            )
            manifest = json.loads(
                (campaign.root_dir / "manifest.json").read_text()
            )
            self.assertEqual(campaign.result["experimentDefinitionRef"], ref)
            self.assertEqual(progress["experimentDefinitionRef"], ref)
            self.assertEqual(manifest["experimentDefinitionRef"], ref)

    def test_referenced_def_reverted_to_draft_fails_load(self) -> None:
        """Rewrite definition.json → rehash manifest → update Campaign refs
        so the hash gate passes, then prove load_campaign fails specifically
        because the status is no longer frozen."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            self.assertIn("experimentDefinitionRef", campaign.result)
            # ─ 1. Rewrite definition.json with status=draft ─
            def_path = frozen.root_dir / "definition.json"
            original_def = json.loads(def_path.read_text())
            tampered_def = dict(original_def)
            tampered_def["status"] = "draft"
            with open(def_path, "w", encoding="utf-8") as fh:
                json.dump(tampered_def, fh)
            # ─ 2. Recompute the new content hash ─
            new_content_hash = hash_file(def_path)
            # ─ 3. Update the ExperimentDefinition manifest so hash gate
            #     and identity check both pass (consistent hash, status now
            #     "draft" so the frozen gate in load_campaign is exercised) ─
            exp_manifest_path = frozen.root_dir / "manifest.json"
            original_exp_manifest = json.loads(exp_manifest_path.read_text())
            updated_exp_manifest = dict(original_exp_manifest)
            updated_exp_manifest["contentHash"] = new_content_hash
            updated_exp_manifest["files"]["definition.json"] = new_content_hash
            updated_exp_manifest["status"] = "draft"  # must match definition.json
            exp_manifest_path.write_text(json.dumps(updated_exp_manifest))
            # ─ 4. Update the Campaign refs (result, progress, manifest) to
            #     the new content hash so the Campaign hash guard also passes ─
            new_ref = {
                "id": ref["id"],
                "version": ref["version"],
                "contentHash": new_content_hash,
            }
            # Update result.json and rehash into manifest.files
            result_path = campaign.root_dir / "result.json"
            result = json.loads(result_path.read_text())
            result["experimentDefinitionRef"] = new_ref
            result_path.write_text(json.dumps(result))
            # Update progress.json
            progress_path = campaign.root_dir / "progress.json"
            progress = json.loads(progress_path.read_text())
            progress["experimentDefinitionRef"] = new_ref
            progress_path.write_text(json.dumps(progress))
            # Update manifest.json with new refs and consistent file hashes
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["experimentDefinitionRef"] = new_ref
            new_files = dict(manifest["files"])
            new_files["result.json"] = hash_file(result_path)
            new_files["progress.json"] = hash_file(progress_path)
            manifest["files"] = new_files
            manifest["resultHash"] = new_files["result.json"]
            manifest_path.write_text(json.dumps(manifest))
            try:
                with self.assertRaisesRegex(
                    AutoQuantValidationError, "no longer frozen"
                ):
                    load_campaign(
                        project,
                        load_session(project, session.manifest["id"]),
                        campaign.result["id"],
                    )
            finally:
                # Restore original state
                with open(def_path, "w", encoding="utf-8") as fh:
                    json.dump(original_def, fh)
                exp_manifest_path.write_text(json.dumps(original_exp_manifest))

    def test_manifest_result_ref_mismatch_fails_closed(self) -> None:
        """If the manifest experimentDefinitionRef differs from the result,
        load_campaign MUST fail closed."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            # Inject a divergent reference into the manifest.
            # The manifest file is excluded from the file-hash set,
            # so modifying it does not trigger the tamper check.
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            bad_ref = dict(ref)
            bad_ref["contentHash"] = "b" * 64
            manifest["experimentDefinitionRef"] = bad_ref
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AutoQuantValidationError, "does not match result"):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )

    def test_progress_only_ref_forged_on_bound_campaign_fails_closed(
        self,
    ) -> None:
        """If result/manifest omit experimentDefinitionRef but progress
        has one, load_campaign must reject the asymmetry."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            # Remove experimentDefinitionRef from result and manifest.
            # Forge progress.json to keep the ref by itself, rehashing
            # manifest.files so the tamper guard does not intercept.
            result_path = campaign.root_dir / "result.json"
            result = json.loads(result_path.read_text())
            del result["experimentDefinitionRef"]
            result_path.write_text(json.dumps(result))
            progress_path = campaign.root_dir / "progress.json"
            # progress already has experimentDefinitionRef — leave it.
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            del manifest["experimentDefinitionRef"]
            new_files = dict(manifest["files"])
            new_files["result.json"] = hash_file(result_path)
            new_files["progress.json"] = hash_file(progress_path)
            manifest["files"] = new_files
            manifest["resultHash"] = new_files["result.json"]
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "progress has experimentDefinitionRef but result"
            ):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )

    def test_result_only_ref_forged_on_legacy_campaign_fails_closed(
        self,
    ) -> None:
        """If progress/manifest omit experimentDefinitionRef but result
        has one, load_campaign must reject the asymmetry."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            # Run a legacy Campaign without any ref
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
            )
            self.assertNotIn("experimentDefinitionRef", campaign.result)
            # Forge result.json with a bogus experimentDefinitionRef.
            # Rehash manifest.files so tamper detection is bypassed.
            result_path = campaign.root_dir / "result.json"
            result = json.loads(result_path.read_text())
            result["experimentDefinitionRef"] = {
                "id": "nonexistent",
                "version": 1,
                "contentHash": "a" * 64,
            }
            result_path.write_text(json.dumps(result))
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            new_files = dict(manifest["files"])
            new_files["result.json"] = hash_file(result_path)
            manifest["files"] = new_files
            manifest["resultHash"] = new_files["result.json"]
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "result has experimentDefinitionRef but manifest"
            ):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )

    def test_progress_malformed_ref_rejected_by_validation(self) -> None:
        """Malformed experimentDefinitionRef in progress is caught by
        _validate_campaign_progress, not by generic tamper."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            # Inject a malformed contentHash into progress while keeping
            # file hashes consistent so tamper passes.
            progress_path = campaign.root_dir / "progress.json"
            progress = json.loads(progress_path.read_text())
            progress["experimentDefinitionRef"]["contentHash"] = "NOT_HEX_123"
            progress_path.write_text(json.dumps(progress))
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            new_files = dict(manifest["files"])
            new_files["progress.json"] = hash_file(progress_path)
            manifest["files"] = new_files
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "contentHash must be a lowercase SHA-256"
            ):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )

    def test_progress_empty_ref_id_rejected_by_validation(self) -> None:
        """Empty id in progress experimentDefinitionRef must be caught
        by _validate_campaign_progress."""
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(
                project, session.manifest["id"], exp_def
            )
            frozen = freeze_experiment_definition(
                project, session.manifest["id"], "quality-momentum-validation", 1
            )
            ref = {
                "id": frozen.definition["id"],
                "version": frozen.definition["version"],
                "contentHash": frozen.manifest["contentHash"],
            }
            campaign = run_campaign(
                project,
                session.manifest["id"],
                self._script(directory, RESEARCHER),
                max_turns=1,
                max_wall_seconds=30,
                turn_timeout_seconds=5,
                experiment_definition_ref=ref,
            )
            # Inject empty id into progress, keeping file hashes consistent.
            progress_path = campaign.root_dir / "progress.json"
            progress = json.loads(progress_path.read_text())
            progress["experimentDefinitionRef"]["id"] = ""
            progress_path.write_text(json.dumps(progress))
            manifest_path = campaign.root_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            new_files = dict(manifest["files"])
            new_files["progress.json"] = hash_file(progress_path)
            manifest["files"] = new_files
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError, "id must be non-empty"
            ):
                load_campaign(
                    project,
                    load_session(project, session.manifest["id"]),
                    campaign.result["id"],
                )


if __name__ == "__main__":
    unittest.main()
