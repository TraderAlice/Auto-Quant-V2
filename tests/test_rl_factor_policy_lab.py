from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from autoquant.project_templates.ohlcv_rl_factor_lab.rl_core import (
    ACTIONS,
    BASE_STATE_COLUMNS,
    fixed_selector,
    rollout_policy,
)
from autoquant.research import run_campaign
from autoquant.runs import execute_study
from autoquant.sessions import evaluate_experiment, start_session
from autoquant.studio import build_studio_snapshot
from autoquant.studies import load_study
from autoquant.templates import RL_STUDY_ID
from autoquant.workspace import create_project, initialize_workspace


IMPROVED_ENCODER = """\
from __future__ import annotations

FEATURE_NAMES = (
    "bias",
    "volume_regime",
    "previous_activity",
    "previous_intraday",
    "previous_reversal",
    "previous_balanced",
)


def encode_state(state: dict[str, float]) -> list[float]:
    return [
        1.0,
        state["volume_regime"] * 2.0,
        state["previous_activity"],
        state["previous_intraday"],
        state["previous_reversal"],
        state["previous_balanced"],
    ]
"""


NONDETERMINISTIC_ENCODER = """\
from __future__ import annotations

FEATURE_NAMES = ("counter",)
counter = 0


def encode_state(state: dict[str, float]) -> list[float]:
    global counter
    counter += 1
    return [float(counter)]
"""


DELAYED_NONFINITE_ENCODER = """\
from __future__ import annotations

FEATURE_NAMES = ("bias",)
calls = 0


def encode_state(state: dict[str, float]) -> list[float]:
    global calls
    calls += 1
    return [float("nan") if calls > 40 else 1.0]
"""


def make_rl_lab(directory: str | Path):
    workspace = initialize_workspace(
        Path(directory) / "workspace",
        name="RL Research Desk",
    )
    project = create_project(
        workspace.root_dir,
        "rl-factor-lab",
        name="RL Factor Lab",
        template="ohlcv-rl-factor-lab",
    )
    return workspace, project


class RlEnvironmentTests(unittest.TestCase):
    def test_action_reward_begins_after_the_decision_close(self) -> None:
        dates = pd.bdate_range("2026-01-01", periods=26)
        columns = ["A", "B"]
        targets = pd.DataFrame(
            [[0.5, -0.5]] * len(dates),
            index=dates,
            columns=columns,
        )
        action_targets = {action: targets.copy() for action in ACTIONS}
        closes = pd.DataFrame(
            {"A": [100.0, 200.0, 200.0, 220.0] + [220.0] * 22, "B": 100.0},
            index=dates,
        )
        volumes = pd.DataFrame(1_000_000.0, index=dates, columns=columns)
        raw_states = pd.DataFrame(
            0.0,
            index=dates,
            columns=list(BASE_STATE_COLUMNS),
        )

        rollout = rollout_policy(
            fixed_selector("activity"),
            raw_states,
            action_targets,
            closes,
            volumes,
            dates[1:25],
        )

        first = rollout.simulation.daily.loc[dates[1]]
        second = rollout.simulation.daily.loc[dates[2]]
        self.assertEqual(first["gross_return"], 0.0)
        self.assertAlmostEqual(first["net_return"], -0.001)
        self.assertAlmostEqual(first["reward"], -0.001)
        self.assertAlmostEqual(second["gross_return"], 0.05)
        self.assertAlmostEqual(second["reward"], 0.04975)


class GovernedRlFactorPolicyLabTests(unittest.TestCase):
    def test_template_is_reproducible_and_preserves_every_seed_fold_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = make_rl_lab(directory)
            study = load_study(project, RL_STUDY_ID)
            self.assertEqual(study.definition.editable["paths"], ["models/**"])
            self.assertEqual(study.definition.judge.paths, ["judges/**"])
            self.assertEqual(len(study.dataset_hashes), 7)

            first = execute_study(project, RL_STUDY_ID)
            second = execute_study(project, RL_STUDY_ID)

            self.assertEqual(first.result["status"], "succeeded")
            self.assertEqual(second.result["status"], "succeeded")
            self.assertEqual(first.result["metrics"], second.result["metrics"])
            metrics = first.result["metrics"]
            self.assertEqual(metrics["configuration"]["seeds"], [11, 29, 47])
            self.assertEqual(metrics["configuration"]["folds"], ["fold-1", "fold-2"])
            self.assertEqual(
                metrics["rl"]["aggregate"]["validation_net_sharpe"][
                    "observations"
                ],
                6,
            )
            self.assertEqual(metrics["rl"]["aggregate"]["failure_rate"], 0.0)
            self.assertFalse(
                metrics["research_integrity"]["test_enters_selection"]
            )
            self.assertLess(
                metrics["comparison"][
                    "mean_validation_advantage_vs_best_baseline"
                ],
                0.0,
            )
            self.assertEqual(
                {item["kind"] for item in first.result["artifacts"]},
                {
                    "rl-report",
                    "policy-models",
                    "training-history",
                    "policy-actions",
                },
            )
            first_models = next(
                item
                for item in first.result["artifacts"]
                if item["kind"] == "policy-models"
            )
            second_models = next(
                item
                for item in second.result["artifacts"]
                if item["kind"] == "policy-models"
            )
            self.assertEqual(
                json.loads(
                    (first.root_dir / first_models["path"]).read_text()
                ),
                json.loads(
                    (second.root_dir / second_models["path"]).read_text()
                ),
            )
            snapshot = build_studio_snapshot(workspace.root_dir)
            layers = snapshot["projects"][0]["runs"][0]["metricLayers"]
            self.assertEqual(layers["kind"], "rl-policy")
            self.assertEqual(layers["folds"], 2)
            self.assertEqual(layers["seeds"], 3)

    def test_campaign_keeps_regime_encoder_and_rejects_nondeterminism(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, project = make_rl_lab(directory)
            session = start_session(project, RL_STUDY_ID)
            researcher = Path(directory) / "rl_researcher.py"
            researcher.write_text(
                f"""\
import json
import os
from pathlib import Path

Path(os.environ["AUTOQUANT_WORKTREE"], "models/candidate.py").write_text(
    {IMPROVED_ENCODER!r}
)
print(json.dumps({{
    "schema_version": 1,
    "action": "propose",
    "strategy": "causal-volume-regime-state",
    "hypothesis": "A causal market-volume regime helps choose factor mixtures.",
    "expected_effect": "Improve aggregate validation net Sharpe across all seeds.",
}}))
""",
                encoding="utf-8",
            )
            campaign = run_campaign(
                project,
                session.manifest["id"],
                f"{shlex.quote(sys.executable)} {shlex.quote(str(researcher))}",
                max_turns=1,
                max_wall_seconds=60,
                turn_timeout_seconds=30,
            )

            self.assertEqual(campaign.result["verdicts"]["KEEP"], 1)
            self.assertGreater(
                campaign.result["finalLeader"]["value"]
                - campaign.result["initialLeader"]["value"],
                20.0,
            )
            observed = build_studio_snapshot(workspace.root_dir)["projects"][0]
            self.assertEqual(observed["counts"]["campaigns"], 1)
            self.assertTrue(
                all(
                    run["metricLayers"]["kind"] == "rl-policy"
                    for run in observed["runs"]
                )
            )

            candidate = (
                session.worktree_project.root_dir / "models" / "candidate.py"
            )
            candidate.write_text(NONDETERMINISTIC_ENCODER, encoding="utf-8")
            crashed = evaluate_experiment(
                project,
                session.manifest["id"],
                "Mutable global state must fail deterministic policy evidence.",
            )
            self.assertEqual(crashed.result["verdict"], "CRASH")
            self.assertEqual(
                crashed.result["errors"][0]["code"],
                "policy.nondeterministic",
            )

            candidate.write_text(DELAYED_NONFINITE_ENCODER, encoding="utf-8")
            seed_failure = evaluate_experiment(
                project,
                session.manifest["id"],
                "A failed seed must fail the Run instead of disappearing.",
            )
            self.assertEqual(seed_failure.result["verdict"], "CRASH")
            self.assertEqual(len(seed_failure.result["errors"]), 6)
            self.assertEqual(
                {item["code"] for item in seed_failure.result["errors"]},
                {"policy.non-finite"},
            )
            self.assertTrue(
                all(
                    "fold-" in item["message"] and "seed" in item["message"]
                    for item in seed_failure.result["errors"]
                )
            )


if __name__ == "__main__":
    unittest.main()
