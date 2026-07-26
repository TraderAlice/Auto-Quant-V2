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
from autoquant.orientation import (
    AGENT_WORK_BRIEF_JSON_SCHEMA,
    build_agent_work_brief,
)
from autoquant.sessions import start_session
from autoquant.studies import StudyJudge, create_study, load_study
from autoquant.templates import TEMPLATE_STUDY_IDS
from autoquant.workspace import AutoQuantValidationError
from autoquant.workspace import create_project, initialize_workspace
from tests.study_helpers import make_project, study_definition


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


class CandidateCheckTests(unittest.TestCase):
    def _session(self, directory: str):
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
        return project, start_session(project, definition.id)

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
                output.unlink()
                if template == "ohlcv-factor-lab":
                    candidate = project.root_dir / "factors" / "candidate.py"
                    candidate.write_text(
                        "import pandas as pd\n\n"
                        "def compute_factor(frame):\n"
                        "    return pd.Series(frame['close'].iloc[-1], "
                        "index=frame.index)\n",
                        encoding="utf-8",
                    )
                    expected_code = "factor.lookahead"
                elif template == "ohlcv-portfolio-lab":
                    candidate = project.root_dir / "factors" / "candidate.py"
                    candidate.write_text(
                        "def compute_factor(frame):\n"
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
                "def compute_factor(frame):\n"
                "    return frame['close'].pct_change()\n\n"
                "def compute_factor_components(frame):\n"
                "    return pd.DataFrame({'base': frame['close']}, "
                "index=frame.index)\n",
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
                "        'intervals': ['base'],\n"
                "        'hypothesis': 'Invalid lookahead fixture.',\n"
                "    },\n"
                "}\n\n"
                "def compute_factor(frame):\n"
                "    return frame['close'].pct_change()\n\n"
                "def compute_factor_components(frame):\n"
                "    return pd.DataFrame({\n"
                "        'future_base': frame['close'].shift(-1),\n"
                "    }, index=frame.index)\n",
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
