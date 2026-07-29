from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import jsonschema

from autoquant.checks import (
    CANDIDATE_CHECK_RESULT_JSON_SCHEMA,
    CHECK_OUTPUT_JSON_SCHEMA,
    PREFLIGHT_JSON_SCHEMA,
    candidate_check_state,
    execute_candidate_check,
    load_candidate_check,
    load_candidate_preflight,
)
from autoquant.intake import prepare_project_intake
from autoquant.orientation import (
    AGENT_WORK_BRIEF_JSON_SCHEMA,
    build_agent_work_brief,
)
from autoquant.reports import publish_report
from autoquant.sessions import evaluate_experiment, load_session, start_session
from autoquant.sessions import complete_session
from autoquant.studies import StudyJudge, create_study, load_study
from autoquant.templates import TEMPLATE_STUDY_IDS
from autoquant.workspace import AutoQuantValidationError
from autoquant.workspace import create_project, initialize_workspace
from tests.study_helpers import make_project, study_definition
from tests.intake_helpers import write_intake_inputs


PREFLIGHT = """\
import json
import math
import os
from pathlib import Path

from factors.candidate import SCORE

passed = isinstance(SCORE, (int, float)) and math.isfinite(float(SCORE))
message = "finite candidate score" if passed else "candidate score must be finite"
Path(os.environ["AUTOQUANT_CHECK_OUTPUT"]).write_text(json.dumps({
    "schema_version": 1,
    "status": "passed" if passed else "failed",
    "summary": message,
    "checks": [{
        "id": "score-contract",
        "status": "passed" if passed else "failed",
        "message": message,
    }],
    "errors": [] if passed else [{
        "code": "score.non-finite",
        "message": message,
    }],
}))
"""


def delegated_request() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-request",
        "title": "Review one bounded AAA factor",
        "question": "Does the candidate improve the fixed AAA factor score?",
        "decisionContext": "OpenAlice needs bounded quantitative evidence.",
        "assets": [
            {
                "symbol": "AAA/USD",
                "assetClass": "equity",
                "venue": "TEST",
            }
        ],
        "direction": "long",
        "horizon": "one month",
        "hypotheses": ["One declared candidate may improve the score."],
        "constraints": ["No trading authority."],
        "deliverables": ["Factor evidence and limitations."],
        "source": {
            "system": "openalice",
            "workspaceId": "check-workspace",
            "sessionId": "check-session",
            "artifactPath": "requests/check.md",
            "artifactRevision": "sha256:check-request",
        },
    }


def baseline_report_analysis(run_id: str) -> dict:
    evidence = {
        "kind": "run",
        "id": run_id,
        "artifactPath": "artifacts/report.json",
    }
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-report-analysis",
        "title": "Bounded AAA factor result",
        "executiveSummary": (
            "The bounded candidate reverted, so the fixed baseline remains."
        ),
        "findings": [
            {
                "id": "baseline-retained",
                "claim": "The immutable trial did not improve the baseline.",
                "confidence": "high",
                "evidenceRefs": [evidence],
            }
        ],
        "recommendations": [
            {
                "action": "Retain the baseline for this bounded assignment.",
                "rationale": "The candidate REVERTed under the fixed objective.",
                "conditions": ["Use fresh evidence for any new claim."],
                "evidenceRefs": [evidence],
            }
        ],
        "limitations": ["Synthetic fixture only."],
        "unresolvedQuestions": ["Does another predeclared factor add value?"],
    }


class CandidateCheckTests(unittest.TestCase):
    def _session(self, directory: str, *, request: dict | None = None):
        _, project = make_project(directory)
        (project.root_dir / "judges" / "preflight.py").write_text(
            PREFLIGHT,
            encoding="utf-8",
        )
        definition = study_definition()
        definition = replace(
            definition,
            judge=StudyJudge(
                "python",
                "judges/evaluate.py",
                ["judges/evaluate.py"],
                [],
                10,
            ),
        )
        create_study(project, definition)
        study = load_study(project, definition.id)
        preflight = {
            "schemaVersion": 1,
            "kind": "autoquant-candidate-preflight",
            "runner": {
                "kind": "python",
                "entrypoint": "judges/preflight.py",
                "paths": ["judges/preflight.py"],
                "arguments": [],
                "timeoutSeconds": 5,
            },
        }
        (study.root_dir / "preflight.json").write_text(
            json.dumps(preflight),
            encoding="utf-8",
        )
        loaded = load_candidate_preflight(project, load_study(project, definition.id))
        self.assertIsNotNone(loaded)
        jsonschema.validate(preflight, PREFLIGHT_JSON_SCHEMA)
        return project, start_session(
            project,
            definition.id,
            request=request,
        )

    def test_pass_fail_stale_and_non_selection_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._session(directory)
            fresh_brief = build_agent_work_brief(project)
            jsonschema.validate(fresh_brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                fresh_brief["reasons"][0]["code"],
                "candidate-edit-required",
            )
            self.assertIsNone(fresh_brief["primaryAction"])
            with self.assertRaises(AutoQuantValidationError):
                execute_candidate_check(project, session.manifest["id"])

            candidate = session.worktree_project.root_dir / "factors" / "candidate.py"
            candidate.write_text("SCORE = 2.0\n", encoding="utf-8")
            changed_brief = build_agent_work_brief(project)
            self.assertEqual(
                changed_brief["primaryAction"]["id"],
                "session.check",
            )
            before = {
                "runs": sorted((project.root_dir / "runs").iterdir()),
                "experiments": sorted((session.root_dir / "experiments").iterdir()),
                "next": session.manifest["nextExperiment"],
                "leader": dict(session.manifest["leader"]),
            }
            passed = execute_candidate_check(project, session.manifest["id"])
            jsonschema.validate(
                json.loads((passed.root_dir / "raw-output.json").read_text()),
                CHECK_OUTPUT_JSON_SCHEMA,
            )
            jsonschema.validate(passed.result, CANDIDATE_CHECK_RESULT_JSON_SCHEMA)
            self.assertEqual(passed.result["status"], "passed")
            self.assertEqual(
                passed.result["authority"],
                {
                    "selectionAuthority": "none",
                    "promotionAuthority": "none",
                    "tradingAuthority": "none",
                },
            )
            start_state = candidate_check_state(project, session)
            self.assertEqual(start_state["current"]["status"], "passed")
            passed_brief = build_agent_work_brief(project)
            self.assertEqual(
                passed_brief["primaryAction"]["id"],
                "experiment.evaluate",
            )
            self.assertEqual(
                passed_brief["evidence"]["candidateCheckId"],
                passed.result["id"],
            )
            self.assertEqual(
                sorted((project.root_dir / "runs").iterdir()),
                before["runs"],
            )
            self.assertEqual(
                sorted((session.root_dir / "experiments").iterdir()),
                before["experiments"],
            )
            self.assertEqual(session.manifest["nextExperiment"], before["next"])
            self.assertEqual(session.manifest["leader"], before["leader"])

            candidate.write_text("SCORE = float('nan')\n", encoding="utf-8")
            stale = candidate_check_state(project, session)
            self.assertIsNone(stale["current"])
            self.assertEqual(stale["latest"]["id"], passed.result["id"])

            failed = execute_candidate_check(project, session.manifest["id"])
            self.assertEqual(failed.result["status"], "failed")
            current = candidate_check_state(project, session)
            self.assertEqual(current["current"]["id"], failed.result["id"])
            self.assertEqual(current["current"]["status"], "failed")
            failed_brief = build_agent_work_brief(project)
            self.assertEqual(
                failed_brief["reasons"][0]["code"],
                "candidate-check-failed",
            )
            self.assertIsNone(failed_brief["primaryAction"])

            result_path = failed.root_dir / "result.json"
            result_path.write_text(result_path.read_text() + " ", encoding="utf-8")
            with self.assertRaises(AutoQuantValidationError):
                load_candidate_check(
                    project,
                    session.manifest["id"],
                    failed.result["id"],
                )

    def test_keep_handoff_retains_exact_passed_check_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._session(directory)
            candidate = (
                session.worktree_project.root_dir / "factors" / "candidate.py"
            )
            candidate.write_text("SCORE = 2.0\n", encoding="utf-8")
            passed = execute_candidate_check(project, session.manifest["id"])
            experiment = evaluate_experiment(
                project,
                session.manifest["id"],
                "Raise the bounded checked score.",
            )
            self.assertEqual(experiment.result["verdict"], "KEEP")

            state = candidate_check_state(
                project,
                load_session(project, session.manifest["id"]),
            )
            self.assertIsNone(state["current"])
            self.assertEqual(
                state["exactCandidate"]["id"],
                passed.result["id"],
            )
            brief = build_agent_work_brief(project)

            self.assertEqual(brief["primaryAction"]["id"], "session.promote")
            self.assertIn(
                "terminally close this Session as promoted",
                brief["primaryAction"]["description"],
            )
            self.assertEqual(
                brief["evidence"]["candidateCheckId"],
                passed.result["id"],
            )
            self.assertEqual(
                brief["evidence"]["candidateCheckStatus"],
                "passed",
            )

    def test_reverted_trial_retains_check_and_offers_evidence_handoff(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._session(
                directory,
                request=delegated_request(),
            )
            candidate = (
                session.worktree_project.root_dir / "factors" / "candidate.py"
            )
            candidate.write_text("SCORE = 0.5\n", encoding="utf-8")
            passed = execute_candidate_check(project, session.manifest["id"])
            experiment = evaluate_experiment(
                project,
                session.manifest["id"],
                "Test one lower bounded score.",
            )
            self.assertEqual(experiment.result["verdict"], "REVERT")

            review = build_agent_work_brief(project)
            jsonschema.validate(review, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                review["reasons"][0]["code"],
                "trial-review-required",
            )
            self.assertIsNone(review["primaryAction"])
            self.assertEqual(
                [item["id"] for item in review["supportingActions"]],
                ["session.show", "report.publish"],
            )
            self.assertIsNone(review["evidence"]["candidateCheckId"])
            self.assertEqual(
                review["evidence"]["latestExperiment"],
                {
                    "id": experiment.result["id"],
                    "verdict": "REVERT",
                    "runId": experiment.result["candidate"]["runId"],
                    "candidateSourceHash": experiment.result["candidate"][
                        "sourceHash"
                    ],
                    "completedAt": experiment.result["completedAt"],
                    "verdictAuthority": "session-objective-only",
                    "candidateCheck": {
                        "id": passed.result["id"],
                        "status": "passed",
                    },
                },
            )

            report = publish_report(
                project,
                session.manifest["id"],
                baseline_report_analysis(
                    session.manifest["baseline"]["runId"]
                ),
            )
            ready = build_agent_work_brief(project)
            self.assertEqual(
                ready["reasons"][0]["code"],
                "baseline-completion-ready",
            )
            self.assertEqual(
                ready["primaryAction"]["id"],
                "session.complete",
            )
            complete_session(
                project,
                session.manifest["id"],
                report.report["id"],
            )
            completed = build_agent_work_brief(project)
            jsonschema.validate(completed, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(
                completed["evidence"]["latestExperiment"],
                review["evidence"]["latestExperiment"],
            )
            self.assertEqual(
                completed["evidence"]["sessionStatus"],
                "completed",
            )

    def test_later_same_source_check_is_not_attributed_to_prior_trial(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._session(directory)
            candidate = (
                session.worktree_project.root_dir / "factors" / "candidate.py"
            )
            candidate.write_text("SCORE = 0.5\n", encoding="utf-8")
            experiment = evaluate_experiment(
                project,
                session.manifest["id"],
                "Evaluate without a prior optional Check.",
            )
            self.assertEqual(experiment.result["verdict"], "REVERT")

            candidate.write_text("SCORE = 0.5\n", encoding="utf-8")
            later = execute_candidate_check(project, session.manifest["id"])
            brief = build_agent_work_brief(project)

            self.assertEqual(
                brief["evidence"]["candidateCheckId"],
                later.result["id"],
            )
            self.assertIsNone(
                brief["evidence"]["latestExperiment"]["candidateCheck"]
            )

    def test_worktree_preserves_fixed_preflight_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, session = self._session(directory)
            study = load_study(
                session.worktree_project,
                session.manifest["studyId"],
                data_root=project.root_dir / "data",
            )
            preflight = load_candidate_preflight(session.worktree_project, study)
            self.assertIsNotNone(preflight)
            self.assertEqual(
                preflight.definition["runner"]["entrypoint"],
                "judges/preflight.py",
            )

    def test_factor_portfolio_and_rl_templates_have_fast_passing_preflights(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            templates = (
                "ohlcv-factor-lab",
                "ohlcv-portfolio-lab",
                "ohlcv-rl-factor-lab",
            )
            for template in templates:
                project = create_project(
                    workspace.root_dir,
                    template,
                    template=template,
                )
                study = load_study(project, TEMPLATE_STUDY_IDS[template])
                preflight = load_candidate_preflight(project, study)
                self.assertIsNotNone(preflight)
                self.assertFalse(
                    set(preflight.source_hashes) & set(study.judge_hashes)
                )
                output = project.root_dir / f".{template}-preflight.json"
                environment = dict(os.environ)
                environment.update(
                    {
                        "AUTOQUANT_PROJECT_ROOT": str(project.root_dir),
                        "AUTOQUANT_DATA_ROOT": str(project.root_dir / "data"),
                        "AUTOQUANT_STUDY_PATH": str(study.manifest_path),
                        "AUTOQUANT_CHECK_OUTPUT": str(output),
                        "AUTOQUANT_CHECK_INPUT_HASH": "0" * 64,
                        "PYTHONPATH": os.pathsep.join(
                            [
                                str(project.root_dir),
                                environment.get("PYTHONPATH", ""),
                            ]
                        ),
                    }
                )
                completed = subprocess.run(
                    [
                        sys.executable,
                        preflight.definition["runner"]["entrypoint"],
                    ],
                    cwd=project.root_dir,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                result = json.loads(output.read_text(encoding="utf-8"))
                jsonschema.validate(result, CHECK_OUTPUT_JSON_SCHEMA)
                self.assertEqual(result["status"], "passed", result)
                if template == "ohlcv-factor-lab":
                    self.assertIn(
                        "bounded decision sample ALPHA, BRAVO (2 of 6 "
                        "position-capable assets); fixed "
                        "context/benchmark assets none; at most 256 timestamps",
                        result["checks"][0]["message"],
                    )
                output.unlink()
                if template == "ohlcv-factor-lab":
                    candidate = project.root_dir / "factors" / "candidate.py"
                    candidate.write_text(
                        "import pandas as pd\n\n"
                        "def compute_factor(panel):\n"
                        "    return pd.Series(panel['close'].iloc[-1], "
                        "index=panel.index)\n",
                        encoding="utf-8",
                    )
                    expected_code = "factor.lookahead"
                elif template == "ohlcv-portfolio-lab":
                    candidate = project.root_dir / "factors" / "candidate.py"
                    candidate.write_text(
                        "def compute_factor(panel):\n"
                        "    return ['not', 'a', 'series']\n",
                        encoding="utf-8",
                    )
                    expected_code = "factor.type"
                else:
                    candidate = project.root_dir / "models" / "candidate.py"
                    candidate.write_text(
                        "FEATURE_NAMES = ('bad',)\n\n"
                        "def encode_state(state):\n"
                        "    return [float('inf')]\n",
                        encoding="utf-8",
                    )
                    expected_code = "policy.non-finite"
                failed = subprocess.run(
                    [
                        sys.executable,
                        preflight.definition["runner"]["entrypoint"],
                    ],
                    cwd=project.root_dir,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                )
                self.assertEqual(failed.returncode, 0, failed.stderr)
                failure = json.loads(output.read_text(encoding="utf-8"))
                jsonschema.validate(failure, CHECK_OUTPUT_JSON_SCHEMA)
                self.assertEqual(failure["status"], "failed")
                self.assertEqual(failure["errors"][0]["code"], expected_code)

    def test_factor_preflight_includes_fixed_context_and_benchmark_assets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            roles = {
                "AAPL": "long-only",
                "MSFT": "long-only",
                "SPY": "context-only",
            }
            request_path, package_path = write_intake_inputs(
                root,
                request_assets=tuple(roles),
                asset_position_roles=roles,
                benchmark_policy={"kind": "asset", "symbol": "SPY"},
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "reference-aware-factor",
                template=prepared.template,
                template_intake=prepared,
            )
            request = json.loads(request_path.read_text(encoding="utf-8"))
            session = start_session(
                project,
                TEMPLATE_STUDY_IDS["ohlcv-factor-lab"],
                request=request,
            )
            candidate = (
                session.worktree_project.root_dir
                / "factors"
                / "candidate.py"
            )
            candidate.write_text(
                "import numpy as np\n"
                "import pandas as pd\n\n"
                "def compute_factor(panel):\n"
                "    close = panel.pivot("
                "index='timestamp', columns='asset', values='close')\n"
                "    if 'SPY' not in close.columns:\n"
                "        raise ValueError('SPY reference is required')\n"
                "    returns = close.pct_change(5, fill_method=None)\n"
                "    relative = returns.sub(returns['SPY'], axis=0)\n"
                "    relative['SPY'] = np.nan\n"
                "    long = relative.stack(future_stack=True)\n"
                "    long.index = long.index.set_names(['timestamp', 'asset'])\n"
                "    keys = pd.MultiIndex.from_frame("
                "panel[['timestamp', 'asset']])\n"
                "    return pd.Series("
                "long.reindex(keys).to_numpy(dtype=float), "
                "index=panel.index, name='spy_relative_5')\n",
                encoding="utf-8",
            )

            checked = execute_candidate_check(
                project,
                session.manifest["id"],
            )

            self.assertEqual(checked.result["status"], "passed")
            self.assertIn(
                "bounded decision sample AAPL, MSFT (2 of 2 "
                "position-capable assets); fixed context/benchmark assets "
                "NVDA, QQQ, SPY; at most 256 timestamps",
                checked.result["checks"][0]["message"],
            )

    def test_factor_preflight_rejects_partial_and_lookahead_components(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            project = create_project(
                workspace.root_dir,
                "factor-components",
                template="ohlcv-factor-lab",
            )
            session = start_session(
                project,
                TEMPLATE_STUDY_IDS["ohlcv-factor-lab"],
            )
            candidate = (
                session.worktree_project.root_dir
                / "factors"
                / "candidate.py"
            )
            candidate.write_text(
                "import pandas as pd\n\n"
                "FACTOR_COMPONENTS = {\n"
                "    'invalid_role': {\n"
                "        'label': 'Invalid role',\n"
                "        'role': 'context-state',\n"
                "        'intervals': ['base'],\n"
                "        'hypothesis': 'Static metadata fails first.',\n"
                "    },\n"
                "}\n\n"
                "def compute_factor(panel):\n"
                "    return pd.Series(float('nan'), index=panel.index)\n\n"
                "def compute_factor_components(panel):\n"
                "    return pd.DataFrame({'invalid_role': panel['close']}, "
                "index=panel.index)\n",
                encoding="utf-8",
            )
            illegal_role = execute_candidate_check(
                project,
                session.manifest["id"],
            )
            self.assertEqual(illegal_role.result["status"], "failed")
            self.assertEqual(
                illegal_role.result["errors"][0]["code"],
                "factor.component-role",
            )

            candidate.write_text(
                "import pandas as pd\n\n"
                "def compute_factor(panel):\n"
                "    return panel.groupby('asset', sort=False)"
                "['close'].pct_change(fill_method=None)\n\n"
                "def compute_factor_components(panel):\n"
                "    return pd.DataFrame({'base': panel['close']}, "
                "index=panel.index)\n",
                encoding="utf-8",
            )
            partial = execute_candidate_check(
                project,
                session.manifest["id"],
            )
            self.assertEqual(partial.result["status"], "failed")
            self.assertEqual(
                partial.result["errors"][0]["code"],
                "factor.components-api",
            )

            candidate.write_text(
                "import pandas as pd\n\n"
                "FACTOR_COMPONENTS = {\n"
                "    'future_base': {\n"
                "        'label': 'Future base close',\n"
                "        'role': 'cross-sectional-score',\n"
                "        'intervals': ['base'],\n"
                "        'hypothesis': 'Invalid lookahead fixture.',\n"
                "    },\n"
                "}\n\n"
                "def compute_factor(panel):\n"
                "    return panel.groupby('asset', sort=False)"
                "['close'].pct_change(fill_method=None)\n\n"
                "def compute_factor_components(panel):\n"
                "    return pd.DataFrame({\n"
                "        'future_base': panel.groupby('asset', sort=False)"
                "['close'].shift(-1),\n"
                "    }, index=panel.index)\n",
                encoding="utf-8",
            )
            lookahead = execute_candidate_check(
                project,
                session.manifest["id"],
            )
            self.assertEqual(lookahead.result["status"], "failed")
            self.assertEqual(
                lookahead.result["errors"][0]["code"],
                "factor.components-lookahead",
            )
