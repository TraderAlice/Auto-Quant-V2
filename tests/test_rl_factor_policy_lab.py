from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from autoquant.mandates import build_portfolio_mandate
from autoquant.project_templates.ohlcv_portfolio_lab.portfolio_core import (
    construct_signal_policy,
    execution_risk_metrics,
)
from autoquant.project_templates.ohlcv_rl_factor_lab.rl_core import (
    ACTIONS,
    BASE_STATE_COLUMNS,
    EXPERTS,
    build_action_targets,
    fixed_selector,
    one_step_action_opportunities,
    rollout_policy,
)
from autoquant.research import run_campaign
from autoquant.runs import execute_study
from autoquant.sessions import (
    evaluate_experiment,
    load_session,
    session_snapshot,
    start_session,
)
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
    def test_every_rl_action_inherits_the_fixed_portfolio_risk_governor(
        self,
    ) -> None:
        dates = pd.bdate_range("2026-01-01", periods=100)
        columns = list("ABCDE")
        time = np.arange(len(dates), dtype=float)
        closes = pd.DataFrame(
            {
                asset: 100.0
                * np.exp(
                    np.cumsum(
                        0.001
                        + 0.06
                        * np.sin(
                            time / (2.0 + number * 0.35) + number
                        )
                    )
                )
                for number, asset in enumerate(columns)
            },
            index=dates,
        )
        base = np.tile(
            np.arange(len(columns), dtype=float),
            (len(dates), 1),
        )
        factor_panels = {
            expert: pd.DataFrame(
                np.roll(base, shift=number, axis=1),
                index=dates,
                columns=columns,
            )
            for number, expert in enumerate(EXPERTS)
        }
        mandate = build_portfolio_mandate(None, columns)

        action_targets = build_action_targets(
            factor_panels,
            closes,
            mandate=mandate,
        )
        expected_candidate = construct_signal_policy(
            factor_panels["candidate"],
            closes,
            mandate=mandate,
        ).targets
        ungoverned_candidate = construct_signal_policy(
            factor_panels["candidate"],
            closes,
            mandate=mandate,
            apply_risk_governor=False,
        ).targets

        self.assertEqual(set(action_targets), set(ACTIONS))
        pd.testing.assert_frame_equal(
            action_targets["candidate"],
            expected_candidate,
        )
        self.assertTrue(
            (
                action_targets["candidate"].abs().sum(axis=1)
                <= ungoverned_candidate.abs().sum(axis=1) + 1e-12
            ).all()
        )
        self.assertTrue(
            (
                action_targets["candidate"].abs().sum(axis=1)
                < ungoverned_candidate.abs().sum(axis=1) - 1e-12
            ).any()
        )

        volumes = pd.DataFrame(
            1_000_000.0,
            index=dates,
            columns=columns,
        )
        raw_states = pd.DataFrame(
            0.0,
            index=dates,
            columns=list(BASE_STATE_COLUMNS),
        )
        rollout = rollout_policy(
            fixed_selector("candidate"),
            raw_states,
            action_targets,
            closes,
            volumes,
            dates[-30:-1],
            mandate=mandate,
        )
        compliance = execution_risk_metrics(
            rollout.simulation,
            rollout.simulation.daily.index,
        )
        self.assertEqual(compliance["executed_breach_dates"], 0)
        self.assertTrue(
            (
                rollout.simulation.daily[
                    "executed_risk_forecast_annualized"
                ]
                <= rollout.simulation.daily[
                    "execution_risk_ceiling_annualized"
                ]
                + 1e-12
            ).all()
        )
        opportunities = one_step_action_opportunities(
            rollout,
            action_targets,
            closes,
            volumes,
            rollout.actions.index,
            mandate=mandate,
        )
        self.assertEqual(len(opportunities), len(rollout.actions))
        for timestamp, opportunity in zip(
            rollout.actions.index,
            opportunities,
        ):
            self.assertEqual(opportunity["selectedAction"], "candidate")
            self.assertEqual(set(opportunity["actions"]), set(ACTIONS))
            np.testing.assert_allclose(
                list(
                    opportunity["actions"]["candidate"][
                        "executedWeights"
                    ].values()
                ),
                rollout.simulation.weights.loc[timestamp].to_numpy(),
                rtol=0.0,
                atol=1e-12,
            )
            np.testing.assert_allclose(
                list(
                    opportunity["actions"]["candidate"]["trades"].values()
                ),
                rollout.simulation.trades.loc[timestamp].to_numpy(),
                rtol=0.0,
                atol=1e-12,
            )

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
            self.assertEqual(
                study.definition.dependencies,
                {
                    "paths": [
                        "factors/**",
                        "strategies/portfolio-mandate.json",
                    ]
                },
            )
            self.assertEqual(
                set(study.dependency_hashes),
                {
                    "factors/candidate.py",
                    "strategies/portfolio-mandate.json",
                },
            )
            self.assertEqual(study.definition.judge.paths, ["judges/**"])
            self.assertEqual(study.definition.judge.timeout_seconds, 90)
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
            self.assertIn("candidate", metrics["configuration"]["actions"])
            self.assertEqual(
                metrics["configuration"]["factorExperts"][0],
                "candidate",
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
                    "policy-rationales",
                    "policy-opportunities",
                },
            )
            rationale = metrics["policy_rationale"]
            self.assertEqual(
                rationale["policy"]["selection_authority"],
                "context-only",
            )
            self.assertEqual(
                rationale["validation"]["decisions"],
                360,
            )
            self.assertEqual(
                rationale["validation"]["reconciliation"]["action_rows"],
                360,
            )
            self.assertEqual(
                set(rationale["validation"]["by_action"]),
                set(metrics["configuration"]["actions"]),
            )
            self.assertEqual(
                set(rationale["validation"]["by_feature"]),
                set(metrics["configuration"]["featureNames"]),
            )
            opportunity = metrics["factor_opportunity"]
            self.assertEqual(
                opportunity["policy"]["method"],
                "actual-pretrade-one-step-governed-action-audit-v1",
            )
            self.assertEqual(
                opportunity["policy"]["selection_authority"],
                "context-only",
            )
            self.assertEqual(
                opportunity["validation"]["decisions"],
                360,
            )
            self.assertEqual(
                opportunity["validation"]["reconciliation"][
                    "action_evaluations"
                ],
                1800,
            )
            self.assertTrue(
                opportunity["validation"]["reconciliation"]["passed"]
            )
            self.assertGreaterEqual(
                opportunity["validation"]["mean_selected_rank"],
                1.0,
            )
            self.assertLessEqual(
                opportunity["validation"]["mean_selected_rank"],
                5.0,
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
            self.assertEqual(
                layers["policyBehavior"]["selectionAuthority"],
                "context-only",
            )
            self.assertEqual(
                layers["factorOpportunity"]["selectionAuthority"],
                "context-only",
            )

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
                max_wall_seconds=180,
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
            integrity = session_snapshot(
                project,
                load_session(project, session.manifest["id"]),
            )["selectionIntegrity"]
            self.assertEqual(
                integrity["researchFamily"]["uniqueSourceTrials"],
                2,
            )
            self.assertEqual(
                integrity["selectionAdjustment"]["status"],
                "unsupported",
            )
            self.assertEqual(
                integrity["selectionAdjustment"]["reason"],
                "aggregate-dependent-fold-seed-objective",
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
