from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from autoquant.operator_port import (
    build_research_ledger,
    execute_operator_request,
    list_operator_receipts,
    validate_operator_request,
)
from autoquant.research import list_campaign_progress, run_campaign
from autoquant.research_definitions import create_factor_definition_version
from autoquant.sessions import start_session
from autoquant.studies import create_study
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition
from tests.test_research_definitions import factor_definition


def operator_request(project_id: str, session_id: str, *, request_id: str = "inspect-1", intent: str = "research.inspect") -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-operator-request",
        "requestId": request_id,
        "actor": {"id": "codex-local", "kind": "codex"},
        "workspaceRef": "test-workspace",
        "projectId": project_id,
        "sessionId": session_id,
        "intent": intent,
        "objectRefs": [],
        "authority": {"mode": "read-only"},
        "budget": {
            "candidateLimit": 0,
            "wallTimeSeconds": 0,
            "cpuSeconds": 0,
            "gpuSeconds": 0,
            "cost": None,
        },
        "confirmationRef": None,
        "expectedState": {"sessionStatus": "active", "objectHashes": {}},
        "input": {},
    }


def confirmation_decision(project, proposal: dict, *, request_id: str) -> dict:
    request = operator_request(
        project.manifest.id,
        proposal["sessionId"],
        request_id=request_id,
        intent="confirmation.accept",
    )
    request["actor"] = {"id": "research-owner", "kind": "user"}
    request["authority"] = {"mode": "approved-envelope"}
    request["confirmationRef"] = proposal["requestId"]
    request["input"] = {"executionActor": proposal["actor"]}
    receipt = execute_operator_request(project, request)
    if receipt["status"] != "completed":
        raise AssertionError(receipt)
    return request


class OperatorPortTests(unittest.TestCase):
    def _setup(self, directory: str):
        _, project = make_project(directory)
        create_study(project, study_definition())
        session = start_session(project, "factor-quality")
        return project, session

    def test_shared_read_only_request_publishes_immutable_receipt_and_retry_replays(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            request = operator_request(project.manifest.id, session.manifest["id"])

            receipt = execute_operator_request(project, request)
            replayed = execute_operator_request(project, request)

            self.assertEqual(receipt, replayed)
            self.assertEqual(receipt["status"], "completed")
            self.assertEqual(receipt["operations"], [{"intent": "research.inspect", "completed": True}])
            self.assertEqual(len(list_operator_receipts(project, session.manifest["id"])), 1)
            ledger = receipt["evidence"][0]
            self.assertEqual(
                [stage["id"] for stage in ledger["stages"]],
                ["data", "question", "factor", "experiment", "campaign", "evidence", "approval", "reproduction"],
            )
            evidence = next(stage for stage in ledger["stages"] if stage["id"] == "evidence")
            self.assertEqual(evidence["widgets"]["replay"]["state"], "unavailable")

    def test_cli_json_uses_the_same_operator_schema_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            request = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="cli-inspect-1",
            )
            request_path = project.root_dir.parent.parent / "operator-request.json"
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "autoquant",
                    "operator",
                    "invoke",
                    str(project.root_dir),
                    "--request",
                    str(request_path),
                    "--json",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            envelope = json.loads(completed.stdout)
            self.assertEqual(envelope["command"], "operator.invoke")
            self.assertEqual(
                envelope["data"]["receipt"],
                execute_operator_request(project, request),
            )

    def test_conflicting_retry_fails_closed_without_second_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            request = operator_request(project.manifest.id, session.manifest["id"])
            execute_operator_request(project, request)
            conflict = operator_request(project.manifest.id, session.manifest["id"])
            conflict["expectedState"]["sessionStatus"] = "completed"

            with self.assertRaises(AutoQuantValidationError) as caught:
                execute_operator_request(project, conflict)

            self.assertIn("different bytes", str(caught.exception))
            self.assertEqual(len(list_operator_receipts(project, session.manifest["id"])), 1)

    def test_stale_expected_state_and_unknown_intent_receive_terminal_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            stale = operator_request(project.manifest.id, session.manifest["id"], request_id="stale-1")
            stale["expectedState"]["sessionStatus"] = "completed"
            unknown = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="unknown-1",
                intent="chat.run-shell",
            )

            stale_receipt = execute_operator_request(project, stale)
            unknown_receipt = execute_operator_request(project, unknown)

            self.assertEqual(stale_receipt["status"], "stale")
            self.assertEqual(stale_receipt["failedGates"], ["expected-prior-state"])
            self.assertEqual(unknown_receipt["status"], "failed")
            self.assertEqual(unknown_receipt["errors"][0]["code"], "operator.unknown-intent")

    def test_boundary_rejects_commands_credentials_paths_and_chat_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            cases = []
            shell = operator_request(project.manifest.id, session.manifest["id"])
            shell["input"] = {"shell": "echo unsafe"}
            cases.append(shell)
            credential = operator_request(project.manifest.id, session.manifest["id"])
            credential["input"] = {"apiKey": "not-a-real-key"}
            cases.append(credential)
            nested_credential = operator_request(project.manifest.id, session.manifest["id"])
            nested_credential["input"] = {"parameters": {"brokerPassword": "not-a-real-password"}}
            cases.append(nested_credential)
            for field in ("authHeader", "privateKey"):
                unknown_credential = operator_request(project.manifest.id, session.manifest["id"])
                unknown_credential["input"] = {field: "not-a-real-credential"}
                cases.append(unknown_credential)
            for field in ("authHeader", "privateKey"):
                nested_definition = operator_request(
                    project.manifest.id,
                    session.manifest["id"],
                    intent="definition.factor.create",
                )
                nested_definition["authority"] = {"mode": "confirmation-bound"}
                nested_definition["input"] = {"definition": factor_definition(status="draft")}
                nested_definition["input"]["definition"]["parameters"] = {
                    field: "not-a-real-credential"
                }
                cases.append(nested_definition)
            path = operator_request(project.manifest.id, session.manifest["id"])
            path["input"] = {"path": "../../outside"}
            cases.append(path)
            chat = operator_request(project.manifest.id, session.manifest["id"])
            chat["authority"] = {"mode": "chat-admin"}
            cases.append(chat)

            for request in cases:
                with self.subTest(request=request["input"]):
                    with self.assertRaises(AutoQuantValidationError):
                        validate_operator_request(request)

    def test_ledger_remains_navigable_when_connected_replay_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            ledger = build_research_ledger(project, session.manifest["id"])

            self.assertEqual(ledger["kind"], "autoquant-research-ledger")
            self.assertEqual(len(ledger["stages"]), 8)
            self.assertTrue(ledger["authority"]["valid"])
            evidence = ledger["stages"][5]
            self.assertEqual(evidence["state"], "empty")
            self.assertEqual(evidence["widgets"]["runs"]["state"], "empty")
            self.assertEqual(evidence["widgets"]["replay"]["state"], "unavailable")

    def test_definition_mutation_requires_matching_semantic_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            proposal = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="factor-proposal-1",
                intent="definition.factor.create",
            )
            proposal["authority"] = {"mode": "confirmation-bound"}
            proposal["input"] = {"definition": factor_definition(status="draft")}

            awaiting = execute_operator_request(project, proposal)
            self.assertEqual(awaiting["status"], "confirmation-required")
            decision = confirmation_decision(
                project,
                proposal,
                request_id="factor-decision-1",
            )

            confirmed = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="factor-confirmed-1",
                intent="definition.factor.create",
            )
            confirmed["authority"] = {"mode": "confirmation-bound"}
            confirmed["confirmationRef"] = decision["requestId"]
            confirmed["input"] = proposal["input"]
            receipt = execute_operator_request(project, confirmed)

            self.assertEqual(receipt["status"], "completed")
            self.assertEqual(receipt["artifacts"][0]["kind"], "factor-definition")
            self.assertEqual(receipt["artifacts"][0]["version"], 1)

    def test_confirmation_is_actor_bound_and_expected_hashes_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            create_factor_definition_version(project, factor_definition(status="draft"))
            stale = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="incomplete-state",
            )
            stale["objectRefs"] = [
                {"kind": "factor-definition", "id": "quality-momentum", "version": 1}
            ]
            self.assertEqual(execute_operator_request(project, stale)["status"], "stale")

            proposal = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="actor-proposal",
                intent="definition.factor.create",
            )
            proposal["authority"] = {"mode": "confirmation-bound"}
            draft = factor_definition(version=2, status="draft")
            draft["lineage"] = {"parentVersion": 1}
            proposal["input"] = {"definition": draft}
            execute_operator_request(project, proposal)
            decision = confirmation_decision(
                project,
                proposal,
                request_id="actor-decision",
            )

            hijacked = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="actor-hijack",
                intent="definition.factor.create",
            )
            hijacked["actor"] = {"id": "hermes-local", "kind": "hermes"}
            hijacked["authority"] = {"mode": "confirmation-bound"}
            hijacked["confirmationRef"] = decision["requestId"]
            hijacked["input"] = proposal["input"]
            receipt = execute_operator_request(project, hijacked)
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(receipt["failedGates"], ["semantic-confirmation"])

    def test_pending_request_recovers_landed_mutation_without_repeating_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            proposal = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="recovery-proposal",
                intent="definition.factor.create",
            )
            proposal["authority"] = {"mode": "confirmation-bound"}
            proposal["input"] = {"definition": factor_definition(status="draft")}
            execute_operator_request(project, proposal)
            decision = confirmation_decision(
                project,
                proposal,
                request_id="recovery-decision",
            )

            confirmed = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="recovery-confirmed",
                intent="definition.factor.create",
            )
            confirmed["authority"] = {"mode": "confirmation-bound"}
            confirmed["confirmationRef"] = decision["requestId"]
            confirmed["input"] = proposal["input"]
            pending = session.root_dir / "operator-receipts" / ".recovery-confirmed.pending"
            pending.mkdir()
            (pending / "request.json").write_text(
                json.dumps(confirmed, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            create_factor_definition_version(project, factor_definition(status="draft"))

            receipt = execute_operator_request(project, confirmed)
            self.assertEqual(receipt["status"], "completed")
            self.assertFalse(pending.exists())

    def test_confirmation_mismatch_and_version_race_publish_failed_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            proposal = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="factor-proposal-race",
                intent="definition.factor.create",
            )
            proposal["authority"] = {"mode": "confirmation-bound"}
            proposal["input"] = {"definition": factor_definition(status="draft")}
            execute_operator_request(project, proposal)
            decision = confirmation_decision(
                project,
                proposal,
                request_id="factor-race-decision",
            )

            mismatched = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="factor-mismatch",
                intent="definition.factor.create",
            )
            mismatched["authority"] = {"mode": "confirmation-bound"}
            mismatched["confirmationRef"] = decision["requestId"]
            changed = factor_definition(status="draft")
            changed["hypothesis"] = "Changed after confirmation."
            mismatched["input"] = {"definition": changed}
            mismatch_receipt = execute_operator_request(project, mismatched)
            self.assertEqual(mismatch_receipt["status"], "failed")
            self.assertEqual(mismatch_receipt["failedGates"], ["semantic-confirmation"])

            confirmed = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="factor-first-write",
                intent="definition.factor.create",
            )
            confirmed["authority"] = {"mode": "confirmation-bound"}
            confirmed["confirmationRef"] = decision["requestId"]
            confirmed["input"] = proposal["input"]
            self.assertEqual(execute_operator_request(project, confirmed)["status"], "completed")

            raced = dict(confirmed)
            raced["requestId"] = "factor-raced-write"
            race_receipt = execute_operator_request(project, raced)
            self.assertEqual(race_receipt["status"], "failed")
            self.assertEqual(race_receipt["errors"][0]["code"], "definition.collision")

    def test_missing_confirmation_reference_publishes_failed_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            request = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="factor-missing-confirmation",
                intent="definition.factor.create",
            )
            request["authority"] = {"mode": "confirmation-bound"}
            request["confirmationRef"] = "does-not-exist"
            request["input"] = {"definition": factor_definition(status="draft")}

            receipt = execute_operator_request(project, request)

            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(receipt["failedGates"], ["semantic-confirmation"])
            self.assertEqual(receipt["errors"][0]["code"], "operator.confirmation-missing")

    def test_immediate_campaign_stop_preserves_completed_evidence_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            script = Path(directory) / "slow-researcher.py"
            script.write_text(
                "import json, os, time\n"
                "from pathlib import Path\n"
                "brief = json.loads(input())\n"
                "Path(os.environ['AUTOQUANT_WORKTREE'], 'factors/candidate.py').write_text(f\"SCORE = {brief['turn'] + 1}.0\\n\")\n"
                "time.sleep(0.4)\n"
                "print(json.dumps({'schema_version': 1, 'action': 'propose', 'strategy': 'bounded', 'hypothesis': 'bounded candidate', 'expected_effect': 'collect one result'}))\n",
                encoding="utf-8",
            )
            result: list[object] = []

            def drive() -> None:
                try:
                    result.append(
                        run_campaign(
                            project,
                            session.manifest["id"],
                            f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}",
                            max_turns=4,
                            max_wall_seconds=30,
                            turn_timeout_seconds=5,
                        )
                    )
                except Exception as error:  # pragma: no cover - asserted below
                    result.append(error)

            thread = threading.Thread(target=drive)
            thread.start()
            progress = []
            for _ in range(100):
                progress = list_campaign_progress(session)
                if progress:
                    break
                time.sleep(0.05)
            self.assertTrue(progress, "Campaign did not publish mutable progress")

            request = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="campaign-stop-1",
                intent="campaign.stop",
            )
            request["authority"] = {"mode": "approved-envelope"}
            request["objectRefs"] = [
                {
                    "kind": "campaign",
                    "id": progress[0]["campaignId"],
                    "version": None,
                }
            ]
            receipt = execute_operator_request(project, request)
            thread.join(timeout=15)

            self.assertFalse(thread.is_alive())
            self.assertEqual(list_campaign_progress(session), [])
            self.assertEqual(receipt["status"], "stopped")
            self.assertEqual(receipt["evidence"][0]["kind"], "autoquant-campaign-stop-request")
            self.assertEqual(receipt["evidence"][1]["status"], "stopped_by_user")
            self.assertTrue(
                set(receipt["evidence"][0]["lastCompletedExperiments"]).issubset(
                    receipt["evidence"][1]["experiments"]
                )
            )
            self.assertEqual(len(result), 1)
            if isinstance(result[0], Exception):
                raise result[0]
            self.assertEqual(result[0].result["status"], "stopped_by_user")

    def test_persisted_stop_wins_over_inflight_researcher_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            script = Path(directory) / "failing-researcher.py"
            script.write_text(
                "import json, time\n"
                "json.loads(input())\n"
                "time.sleep(0.4)\n"
                "print(json.dumps({'schema_version': 1, 'action': 'propose', 'strategy': 'invalid', 'hypothesis': 'invalid after stop', 'expected_effect': 'none', 'verdict': 'KEEP'}))\n",
                encoding="utf-8",
            )
            result: list[object] = []

            def drive() -> None:
                try:
                    result.append(
                        run_campaign(
                            project,
                            session.manifest["id"],
                            f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}",
                            max_turns=2,
                            max_wall_seconds=30,
                            turn_timeout_seconds=5,
                        )
                    )
                except Exception as error:  # pragma: no cover - asserted below
                    result.append(error)

            thread = threading.Thread(target=drive)
            thread.start()
            progress = []
            for _ in range(100):
                progress = list_campaign_progress(session)
                if progress and progress[0]["phase"] == "researcher":
                    break
                time.sleep(0.05)
            self.assertTrue(progress, "Campaign did not enter the Researcher phase")

            request = operator_request(
                project.manifest.id,
                session.manifest["id"],
                request_id="campaign-stop-after-failure",
                intent="campaign.stop",
            )
            request["authority"] = {"mode": "approved-envelope"}
            request["objectRefs"] = [
                {"kind": "campaign", "id": progress[0]["campaignId"], "version": None}
            ]
            receipt = execute_operator_request(project, request)
            thread.join(timeout=15)

            self.assertFalse(thread.is_alive())
            self.assertEqual(receipt["status"], "stopped")
            self.assertEqual(receipt["evidence"][1]["status"], "stopped_by_user")
            self.assertTrue(receipt["evidence"][1]["errors"])
            self.assertEqual(len(result), 1)
            if isinstance(result[0], Exception):
                raise result[0]
            self.assertEqual(result[0].result, receipt["evidence"][1])


    def test_campaign_executor_start_validates_ref_and_budget_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            from autoquant.research_definitions import (
                approve_factor_definition,
                create_experiment_definition_version,
                freeze_experiment_definition,
                load_experiment_definition,
            )
            from tests.test_research_definitions import experiment_definition, factor_definition

            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(project, session.manifest["id"], exp_def)
            freeze_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 1)

            # Load real content hashes for v1 (draft) and v2 (frozen).
            v1_draft = load_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 1)
            v2_frozen = load_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 2)
            v1_hash = v1_draft.manifest["contentHash"]
            v2_hash = v2_frozen.manifest["contentHash"]
            WRONG_HASH = "b" * 64  # valid SHA-256 hex but matches no definition

            # ---- 1. None ref ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-none-ref", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": None}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-ref")
            self.assertEqual(r["warnings"], [])

            # ---- 2. Empty dict ref (partial, missing all keys) ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-empty-ref", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {}}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-ref")
            self.assertEqual(r["warnings"], [])

            # ---- 3. Extra field beyond {id, version, contentHash} ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-extra-field", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 1,
                "contentHash": v1_hash, "extra": True,
            }}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-ref")
            self.assertEqual(r["warnings"], [])

            # ---- 4. Missing contentHash (partial fields) ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-missing-hash", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 1,
            }}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-ref")
            self.assertEqual(r["warnings"], [])

            # ---- 5. Malformed hash (not 64 hex) ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-malformed-hash", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 1,
                "contentHash": "not-a-valid-sha256-hash",
            }}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-ref")
            self.assertEqual(r["warnings"], [])

            # ---- 6. Wrong valid SHA256 hash (matches format but not the definition) ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-wrong-hash", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 2,
                "contentHash": WRONG_HASH,
            }}
            start["budget"] = {"candidateLimit": 8, "wallTimeSeconds": 900, "cpuSeconds": 600, "gpuSeconds": 0, "cost": None}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-hash")
            self.assertEqual(r["warnings"], [])

            # ---- 7. v1 draft with real contentHash → not frozen ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-draft-def", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 1,
                "contentHash": v1_hash,
            }}
            start["budget"] = {"candidateLimit": 8, "wallTimeSeconds": 900, "cpuSeconds": 600, "gpuSeconds": 0, "cost": None}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.definition-status")
            self.assertEqual(r["warnings"], [])

            # ---- 8. Zero candidateLimit budget ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-no-budget", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 2,
                "contentHash": v2_hash,
            }}
            start["budget"] = {"candidateLimit": 0, "wallTimeSeconds": 0, "cpuSeconds": 0, "gpuSeconds": 0, "cost": None}
            r = execute_operator_request(project, start)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.budget")
            self.assertEqual(r["warnings"], [])

            # ---- 9. Valid preflight: frozen v2, real hash, positive budget ----
            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-valid-preflight", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 2,
                "contentHash": v2_hash,
            }}
            start["budget"] = {"candidateLimit": 8, "wallTimeSeconds": 900, "cpuSeconds": 600, "gpuSeconds": 0, "cost": None}
            valid = execute_operator_request(project, start)

            self.assertEqual(valid["status"], "unavailable")
            self.assertEqual(valid["operations"], [{"intent": "campaign.start", "completed": False}])
            # Error code must be in errors, not warnings.
            self.assertEqual(valid["errors"][0]["code"], "campaign.structured-executor-unavailable")
            self.assertEqual(valid["warnings"], [])
            evidence = valid["evidence"][0]
            self.assertEqual(evidence["kind"], "autoquant-campaign-preflight")
            self.assertEqual(evidence["intent"], "campaign.start")
            self.assertTrue(evidence["validated"])
            self.assertIsNone(evidence["executor"])
            # No staging side effect — no campaign or progress was created.
            from autoquant.research import list_campaign_progress
            self.assertEqual(list_campaign_progress(session), [])

    def test_campaign_executor_pause_resume_validates_active_campaign_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)

            # ---- 1. pause without active Campaign ----
            request = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="pause-no-campaign", intent="campaign.pause",
            )
            request["authority"] = {"mode": "approved-envelope"}
            request["objectRefs"] = [
                {"kind": "campaign", "id": "nonexistent-campaign", "version": None}
            ]
            r = execute_operator_request(project, request)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.not-running")

            # ---- 2. resume without active Campaign ----
            request = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="resume-no-campaign", intent="campaign.resume",
            )
            request["authority"] = {"mode": "approved-envelope"}
            request["objectRefs"] = [
                {"kind": "campaign", "id": "nonexistent-campaign", "version": None}
            ]
            r = execute_operator_request(project, request)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "campaign.not-running")

            # ---- 3. pause with wrong objectRef kind ----
            request = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="pause-bad-ref", intent="campaign.pause",
            )
            request["authority"] = {"mode": "approved-envelope"}
            request["objectRefs"] = [
                {"kind": "session", "id": session.manifest["id"], "version": None}
            ]
            from autoquant.operator_port import _current_object_hashes
            request["expectedState"] = {
                "sessionStatus": "active",
                "objectHashes": _current_object_hashes(
                    project, session.manifest["id"], request["objectRefs"],
                ),
            }
            r = execute_operator_request(project, request)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(r["errors"][0]["code"], "operator.campaign-ref")

            # ---- 4. With a running campaign, pause/resume validate and return unavailable ----
            import shlex, sys, threading, time
            from autoquant.research import list_campaign_progress, run_campaign

            script = Path(directory) / "slow-researcher.py"
            script.write_text(
                "import json, os, time\n"
                "from pathlib import Path\n"
                "brief = json.loads(input())\n"
                "Path(os.environ['AUTOQUANT_WORKTREE'], 'factors/candidate.py').write_text(f\"SCORE = {brief['turn'] + 1}.0\\n\")\n"
                "time.sleep(0.4)\n"
                "print(json.dumps({'schema_version': 1, 'action': 'propose', 'strategy': 'bounded', 'hypothesis': 'bounded candidate', 'expected_effect': 'collect one result'}))\n",
                encoding="utf-8",
            )

            def drive() -> None:
                run_campaign(
                    project, session.manifest["id"],
                    f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}",
                    max_turns=4, max_wall_seconds=30, turn_timeout_seconds=5,
                )

            thread = threading.Thread(target=drive)
            thread.start()
            progress = []
            for _ in range(100):
                progress = list_campaign_progress(session)
                if progress:
                    break
                time.sleep(0.05)
            self.assertTrue(progress, "Campaign did not publish mutable progress")
            campaign_id = progress[0]["campaignId"]

            # pause while running
            pause_req = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="pause-running", intent="campaign.pause",
            )
            pause_req["authority"] = {"mode": "approved-envelope"}
            pause_req["objectRefs"] = [
                {"kind": "campaign", "id": campaign_id, "version": None}
            ]
            pause_r = execute_operator_request(project, pause_req)
            self.assertEqual(pause_r["status"], "unavailable")
            self.assertEqual(pause_r["operations"], [{"intent": "campaign.pause", "completed": False}])
            self.assertEqual(pause_r["errors"][0]["code"], "campaign.structured-executor-unavailable")
            self.assertEqual(pause_r["warnings"], [])
            evidence = pause_r["evidence"][0]
            self.assertEqual(evidence["kind"], "autoquant-campaign-preflight")
            self.assertTrue(evidence["validated"])
            self.assertIsNone(evidence["executor"])

            # resume while running
            resume_req = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="resume-running", intent="campaign.resume",
            )
            resume_req["authority"] = {"mode": "approved-envelope"}
            resume_req["objectRefs"] = [
                {"kind": "campaign", "id": campaign_id, "version": None}
            ]
            resume_r = execute_operator_request(project, resume_req)
            self.assertEqual(resume_r["status"], "unavailable")
            self.assertEqual(resume_r["operations"], [{"intent": "campaign.resume", "completed": False}])
            self.assertEqual(resume_r["errors"][0]["code"], "campaign.structured-executor-unavailable")
            self.assertEqual(resume_r["warnings"], [])
            evidence = resume_r["evidence"][0]
            self.assertEqual(evidence["kind"], "autoquant-campaign-preflight")
            self.assertTrue(evidence["validated"])
            self.assertIsNone(evidence["executor"])

            # Stop the campaign to clean up.
            stop = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="pause-test-stop", intent="campaign.stop",
            )
            stop["authority"] = {"mode": "approved-envelope"}
            stop["objectRefs"] = [
                {"kind": "campaign", "id": campaign_id, "version": None}
            ]
            execute_operator_request(project, stop)
            thread.join(timeout=15)

    def test_campaign_executor_start_rejects_with_active_campaign(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            from autoquant.research_definitions import (
                approve_factor_definition,
                create_experiment_definition_version,
                freeze_experiment_definition,
                load_experiment_definition,
            )
            from tests.test_research_definitions import experiment_definition, factor_definition

            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(project, session.manifest["id"], exp_def)
            freeze_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 1)

            v2_frozen = load_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 2)
            v2_hash = v2_frozen.manifest["contentHash"]

            import shlex, sys, threading, time
            from autoquant.research import list_campaign_progress, run_campaign

            # Start a campaign to make the session active.
            script = Path(directory) / "running-researcher.py"
            script.write_text(
                "import json, os, time\n"
                "from pathlib import Path\n"
                "brief = json.loads(input())\n"
                "Path(os.environ['AUTOQUANT_WORKTREE'], 'factors/candidate.py').write_text(f\"SCORE = {brief['turn'] + 1}.0\\n\")\n"
                "time.sleep(0.3)\n"
                "print(json.dumps({'schema_version': 1, 'action': 'propose', 'strategy': 'bounded', 'hypothesis': 'active campaign', 'expected_effect': 'block second start'}))\n",
                encoding="utf-8",
            )

            def drive() -> None:
                run_campaign(
                    project, session.manifest["id"],
                    f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}",
                    max_turns=4, max_wall_seconds=30, turn_timeout_seconds=5,
                )

            thread = threading.Thread(target=drive)
            thread.start()
            for _ in range(100):
                if list_campaign_progress(session):
                    break
                time.sleep(0.05)

            start = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="start-while-active", intent="campaign.start",
            )
            start["authority"] = {"mode": "approved-envelope"}
            start["input"] = {"experimentDefinitionRef": {
                "id": "quality-momentum-validation", "version": 2,
                "contentHash": v2_hash,
            }}
            start["budget"] = {"candidateLimit": 8, "wallTimeSeconds": 900, "cpuSeconds": 600, "gpuSeconds": 0, "cost": None}
            active_receipt = execute_operator_request(project, start)
            self.assertEqual(active_receipt["status"], "failed")
            self.assertEqual(active_receipt["errors"][0]["code"], "campaign.already-running")

            # Stop the campaign to clean up.
            progress = list_campaign_progress(session)
            stop = operator_request(
                project.manifest.id, session.manifest["id"],
                request_id="active-test-stop", intent="campaign.stop",
            )
            stop["authority"] = {"mode": "approved-envelope"}
            stop["objectRefs"] = [
                {"kind": "campaign", "id": progress[0]["campaignId"], "version": None}
            ]
            execute_operator_request(project, stop)
            thread.join(timeout=15)

    def test_campaign_executor_intents_require_approved_envelope_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._setup(directory)
            from autoquant.research_definitions import (
                approve_factor_definition,
                create_experiment_definition_version,
                freeze_experiment_definition,
                load_experiment_definition,
            )
            from tests.test_research_definitions import experiment_definition, factor_definition

            create_factor_definition_version(project, factor_definition(status="draft"))
            approve_factor_definition(project, "quality-momentum", 1)
            exp_def = experiment_definition(status="draft")
            exp_def["definitionRef"] = {"kind": "factor", "id": "quality-momentum", "version": 2}
            create_experiment_definition_version(project, session.manifest["id"], exp_def)
            freeze_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 1)

            v2_frozen = load_experiment_definition(project, session.manifest["id"], "quality-momentum-validation", 2)
            v2_hash = v2_frozen.manifest["contentHash"]

            for intent in ("campaign.start", "campaign.pause", "campaign.resume"):
                with self.subTest(intent=intent):
                    request = operator_request(
                        project.manifest.id, session.manifest["id"],
                        request_id=f"auth-test-{intent.replace('.', '-')}",
                        intent=intent,
                    )
                    request["authority"] = {"mode": "read-only"}
                    if intent == "campaign.start":
                        request["input"] = {"experimentDefinitionRef": {
                            "id": "quality-momentum-validation", "version": 2,
                            "contentHash": v2_hash,
                        }}
                        request["budget"] = {"candidateLimit": 8, "wallTimeSeconds": 900, "cpuSeconds": 600, "gpuSeconds": 0, "cost": None}
                    else:
                        request["objectRefs"] = [
                            {"kind": "campaign", "id": "any-campaign", "version": None}
                        ]

                    receipt = execute_operator_request(project, request)
                    self.assertEqual(receipt["status"], "failed", f"{intent} should reject read-only authority")
                    self.assertEqual(receipt["errors"][0]["code"], "operator.authority")


if __name__ == "__main__":
    unittest.main()
