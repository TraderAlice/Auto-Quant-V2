from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import jsonschema
import pandas as pd

from autoquant.briefs import load_research_request
from autoquant.checks import execute_candidate_check
from autoquant.factor_explorer import (
    FACTOR_DIAGNOSTICS_JSON_SCHEMA,
    load_factor_diagnostics,
)
from autoquant.factor_claims import FACTOR_CLAIM, load_factor_claim
from autoquant.horizons import (
    RESEARCH_HORIZON,
    load_research_horizon,
)
from autoquant.intake import (
    OHLCV_DATASET_PACKAGE_JSON_SCHEMA,
    load_project_intake,
    materialize_intake_dataset,
    prepare_project_intake,
)
from autoquant.mandates import (
    PORTFOLIO_MANDATE,
    load_portfolio_mandate,
)
from autoquant.intervals import load_multi_interval_asset
from autoquant.portfolio_explorer import (
    PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA,
    load_portfolio_diagnostics,
)
from autoquant.rl_explorer import (
    RL_DIAGNOSTICS_JSON_SCHEMA,
    load_rl_diagnostics,
)
from autoquant.reports import publish_report
from autoquant.runs import RUN_RESULT_JSON_SCHEMA, execute_study
from autoquant.sessions import start_session
from autoquant.studio import build_studio_snapshot
from autoquant.studies import hash_file, load_study
from autoquant.templates import (
    OHLCV_STUDY_ID,
    PORTFOLIO_STUDY_ID,
    RL_STUDY_ID,
)
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
    load_workspace,
)
from tests.intake_helpers import (
    write_configurable_continuous_inputs,
    write_intake_inputs,
    write_multi_interval_inputs,
    write_session_interval_inputs,
)


class RequestDrivenIntakeTests(unittest.TestCase):
    def test_complete_pre_factor_claim_intake_remains_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "legacy-factor-desk",
                template=prepared.template,
                template_intake=prepared,
            )

            claim_path = project.root_dir / FACTOR_CLAIM
            claim_bytes = claim_path.read_bytes()
            study_path = (
                project.root_dir
                / "studies"
                / OHLCV_STUDY_ID
                / "study.json"
            )
            study = json.loads(study_path.read_text(encoding="utf-8"))
            study["dependencies"]["paths"].remove(FACTOR_CLAIM)
            study_path.write_text(
                json.dumps(study, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            claim_path.unlink()

            legacy_study = load_study(project, OHLCV_STUDY_ID)
            intake_path = project.root_dir / "intake.json"
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            intake["studyHash"] = legacy_study.study_hash
            intake["studyInputHash"] = legacy_study.input_hash
            intake_path.write_text(
                json.dumps(intake, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            loaded = load_project_intake(project)
            self.assertTrue(loaded["study"]["current"])

            claim_path.write_bytes(claim_bytes)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_project_intake(project)
            self.assertIn(
                "intake.factor-claim-dependency",
                {issue.code for issue in captured.exception.issues},
            )

    def test_request_predeclares_and_locks_known_style_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(
                root,
                factor_policy={
                    "claim": "known-style-validation",
                    "knownStyle": "reversal_5",
                },
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "known-style-factor",
                template=prepared.template,
                template_intake=prepared,
            )
            claim = load_factor_claim(project.root_dir / FACTOR_CLAIM)
            self.assertEqual(claim["claim"], "known-style-validation")
            self.assertEqual(claim["knownStyle"], "reversal_5")
            self.assertEqual(
                claim["source"]["factorPolicy"],
                "caller-supplied",
            )
            candidate = (
                project.root_dir / "factors" / "candidate.py"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "KNOWN_STYLE = 'reversal_5'",
                candidate,
            )
            self.assertIn(
                "Generated by AutoQuant intake",
                candidate,
            )
            run = execute_study(project, OHLCV_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            self.assertEqual(run.result["metrics"]["factor_claim"], claim)
            projection = load_factor_diagnostics(project, run.result["id"])
            jsonschema.validate(
                projection,
                FACTOR_DIAGNOSTICS_JSON_SCHEMA,
            )
            self.assertEqual(
                projection["factorQualification"]["claim"],
                claim,
            )
            self.assertEqual(
                projection["factorQualification"]["selection"]["criterion"],
                "request-predeclared-known-style",
            )
            selected = next(
                item
                for item in projection["factorQualification"]["selection"][
                    "candidates"
                ]
                if item["style"] == "reversal_5"
            )
            self.assertAlmostEqual(
                selected["meanRankCorrelation"],
                1.0,
            )
            self.assertNotEqual(
                projection["factorQualification"]["diagnosis"]["stage"],
                "known-style-identity-mismatch",
            )

            claim_path = project.root_dir / FACTOR_CLAIM
            changed = json.loads(claim_path.read_text(encoding="utf-8"))
            changed["knownStyle"] = "momentum_20"
            claim_path.write_text(
                json.dumps(changed, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError):
                load_project_intake(project)

    def test_factor_policy_rejects_ambiguous_claims(self) -> None:
        cases = (
            {
                "claim": "novel-factor",
                "knownStyle": "reversal_5",
            },
            {
                "claim": "known-style-validation",
                "knownStyle": None,
            },
        )
        for index, policy in enumerate(cases):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request_path, package_path = write_intake_inputs(root)
                request = json.loads(request_path.read_text(encoding="utf-8"))
                request["factorPolicy"] = policy
                request_path.write_text(
                    json.dumps(request, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(AutoQuantValidationError):
                    prepare_project_intake(
                        request_path,
                        package_path,
                        "ohlcv-factor-lab",
                    )

    def test_intake_rejects_horizon_without_purged_split_capacity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(
                root,
                observations=260,
                horizon_policy={
                    "primaryForwardBars": 21,
                    "diagnosticForwardBars": [5, 21, 63],
                },
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-factor-lab",
                )
            self.assertIn(
                "horizon.insufficient-history",
                {item.code for item in captured.exception.issues},
            )

    def test_caller_horizon_governs_factor_selection_and_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = {
                "primaryForwardBars": 5,
                "diagnosticForwardBars": [1, 5, 20],
            }
            request_path, package_path = write_intake_inputs(
                root,
                horizon_policy=policy,
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "caller-horizon-factor",
                template=prepared.template,
                template_intake=prepared,
            )
            horizon = load_research_horizon(
                project.root_dir / RESEARCH_HORIZON
            )
            self.assertEqual(horizon["primaryForwardBars"], 5)
            self.assertEqual(horizon["diagnosticForwardBars"], [1, 5, 20])
            self.assertEqual(
                horizon["source"]["horizonPolicy"],
                "caller-supplied",
            )
            study = load_study(project, OHLCV_STUDY_ID)
            self.assertEqual(
                study.definition.dependencies,
                {
                    "paths": [
                        "strategies/factor-claim.json",
                        RESEARCH_HORIZON,
                    ]
                },
            )

            run = execute_study(project, OHLCV_STUDY_ID)
            self.assertEqual(
                run.result["status"],
                "succeeded",
                run.result["errors"],
            )
            metrics = run.result["metrics"]
            self.assertEqual(metrics["research_horizon"], horizon)
            self.assertEqual(
                metrics["validation"],
                metrics["horizon_quality"]["5"]["validation"],
            )
            self.assertAlmostEqual(
                metrics["validation_mean_ic"],
                metrics["horizon_quality"]["5"]["validation"]["mean_ic"],
            )
            self.assertEqual(
                set(metrics["split_protocol"]["horizons"]),
                {"1", "5", "20"},
            )

            projection = load_factor_diagnostics(
                project,
                run.result["id"],
            )
            self.assertEqual(projection["researchHorizon"], horizon)
            self.assertEqual(
                [item["horizon"] for item in projection["horizonProfile"]],
                [1, 5, 20],
            )
            self.assertEqual(projection["protocol"]["primaryHorizon"], 5)
            jsonschema.validate(
                projection,
                FACTOR_DIAGNOSTICS_JSON_SCHEMA,
            )

    def test_caller_portfolio_policy_governs_portfolio_and_rl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = {
                "grossLimit": 0.8,
                "maxAbsWeight": 0.2,
                "assetMaxAbsWeights": {
                    "AAPL": 0.12,
                    "MSFT": 0.08,
                },
                "annualizedVolatilityCeiling": 0.12,
                "baseCostBps": 17.5,
                "noTradeOneWay": 0.04,
                "referenceNav": 250_000.0,
                "decisionEveryBars": 4,
                "decisionAnchor": "dataset-start",
            }
            request_path, package_path = write_intake_inputs(
                root,
                portfolio_policy=policy,
                benchmark_policy={
                    "kind": "asset",
                    "symbol": "SPY",
                },
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "caller-policy-desk",
                template=prepared.template,
                template_intake=prepared,
            )
            mandate = load_portfolio_mandate(
                project.root_dir / PORTFOLIO_MANDATE
            )
            self.assertEqual(
                mandate["source"]["portfolioPolicy"],
                "caller-supplied",
            )
            self.assertEqual(
                mandate["implementationPolicy"]["baseCostBps"],
                17.5,
            )
            self.assertEqual(
                mandate["implementationPolicy"]["decisionPolicy"],
                {
                    "source": "caller-supplied",
                    "kind": "every-bars",
                    "bars": 4,
                    "anchor": "dataset-start",
                },
            )
            self.assertEqual(
                mandate["construction"]["assetMaxAbsWeights"],
                {
                    "AAPL": 0.12,
                    "MSFT": 0.08,
                    "NVDA": 0.0,
                    "QQQ": 0.0,
                    "SPY": 0.0,
                },
            )
            self.assertEqual(
                mandate["construction"]["benchmark"],
                {
                    "source": "caller-supplied",
                    "kind": "single-asset-long",
                    "asset": "SPY",
                    "weights": {
                        "AAPL": 0.0,
                        "MSFT": 0.0,
                        "NVDA": 0.0,
                        "QQQ": 0.0,
                        "SPY": 1.0,
                    },
                },
            )

            portfolio_run = execute_study(project, PORTFOLIO_STUDY_ID)
            rl_run = execute_study(project, RL_STUDY_ID)
            for run in (portfolio_run, rl_run):
                self.assertEqual(
                    run.result["status"],
                    "succeeded",
                    run.result["errors"],
                )
                self.assertEqual(
                    run.result["metrics"]["portfolio_mandate"],
                    mandate,
                )
                jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)
            portfolio_metrics = portfolio_run.result["metrics"]
            daily = pd.read_csv(
                portfolio_run.root_dir
                / "artifacts"
                / "daily-portfolio.csv"
            )
            spy = pd.read_csv(root / "external-data" / "SPY.csv")
            expected_spy_returns = (
                spy["close"].shift(-1) / spy["close"] - 1.0
            ).fillna(0.0)
            expected_by_date = dict(
                zip(
                    spy["date"],
                    expected_spy_returns,
                    strict=True,
                )
            )
            source_positions = {
                str(date): position
                for position, date in enumerate(spy["date"])
            }
            for _, row in daily.iterrows():
                decision_date = str(row["timestamp"])[:10]
                expected_eligible = (
                    source_positions[decision_date] % 4 == 0
                )
                self.assertEqual(
                    bool(row["decision_eligible"]),
                    expected_eligible,
                )
                self.assertEqual(int(row["decision_every_bars"]), 4)
                self.assertEqual(row["decision_anchor"], "dataset-start")
                self.assertEqual(row["decision_session"], "dataset")
                if not expected_eligible:
                    self.assertFalse(bool(row["ordinary_rebalance"]))
                    self.assertTrue(
                        abs(float(row["traded_notional"])) <= 1e-12
                        or bool(row["risk_rebalance_override"])
                    )
                    self.assertIn(
                        row["execution_reason"],
                        {
                            "decision_schedule_hold",
                            "risk_ceiling_override",
                        },
                    )
            self.assertEqual(len(daily), len(spy) - 1)
            for row_number in (0, 50, len(daily) - 2):
                decision_date = str(
                    daily.loc[row_number, "timestamp"]
                )[:10]
                self.assertAlmostEqual(
                    daily.loc[row_number, "benchmark_return"],
                    expected_by_date[decision_date],
                    places=10,
                )
            self.assertEqual(
                portfolio_metrics["signal_policy"]["parameters"],
                {
                    "long_entry_percentile": 0.75,
                    "long_exit_percentile": 0.55,
                    "short_exit_percentile": 0.45,
                    "short_entry_percentile": 0.25,
                    "volatility_window": 20,
                    "gross_target": 0.8,
                    "max_abs_weight": 0.2,
                    "no_trade_one_way": 0.04,
                    "decision_every_bars": 4,
                },
            )
            self.assertEqual(
                set(
                    portfolio_metrics["robustness"]["cost_stress"]
                ),
                {"0bps", "17.5bps", "35bps"},
            )
            self.assertEqual(
                portfolio_metrics["liquidity_capacity"]["policy"][
                    "reference_nav"
                ],
                250_000.0,
            )
            portfolio_projection = load_portfolio_diagnostics(
                project,
                portfolio_run.result["id"],
            )
            self.assertEqual(
                portfolio_projection["mandate"]["implementationPolicy"],
                mandate["implementationPolicy"],
            )
            self.assertEqual(
                portfolio_projection["mandate"]["assetMaxAbsWeights"],
                mandate["construction"]["assetMaxAbsWeights"],
            )
            self.assertEqual(
                portfolio_projection["mandate"]["benchmark"],
                mandate["construction"]["benchmark"],
            )
            for position in portfolio_projection["sizingAnatomy"][
                "positions"
            ]:
                self.assertEqual(
                    position["maxAbsWeight"],
                    mandate["construction"]["assetMaxAbsWeights"][
                        position["asset"]
                    ],
                )
            self.assertAlmostEqual(
                portfolio_projection["strategyViability"]["validation"][
                    "friction"
                ]["baseCostBps"],
                17.5,
            )
            self.assertEqual(
                {
                    key: portfolio_projection["decisionCadence"][key]
                    for key in ("source", "kind", "bars", "anchor")
                },
                mandate["implementationPolicy"]["decisionPolicy"],
            )
            jsonschema.validate(
                portfolio_projection,
                PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA,
            )

            self.assertEqual(
                rl_run.result["metrics"]["configuration"]["costBps"],
                17.5,
            )
            self.assertEqual(
                rl_run.result["metrics"]["configuration"][
                    "noTradeOneWay"
                ],
                0.04,
            )
            self.assertEqual(
                rl_run.result["metrics"]["configuration"][
                    "decisionEveryBars"
                ],
                4,
            )
            self.assertEqual(
                rl_run.result["metrics"]["configuration"]["decisionAnchor"],
                "dataset-start",
            )
            action_rows = pd.read_csv(
                rl_run.root_dir / "artifacts" / "policy-actions.csv"
            )
            for _, group in action_rows.groupby(
                ["fold", "seed", "split"],
                sort=False,
            ):
                previous_action = "balanced"
                for _, row in group.iterrows():
                    decision_date = str(row["timestamp"])[:10]
                    expected_eligible = (
                        source_positions[decision_date] % 4 == 0
                    )
                    self.assertEqual(
                        bool(row["decision_eligible"]),
                        expected_eligible,
                    )
                    self.assertEqual(
                        int(row["decision_every_bars"]),
                        4,
                    )
                    self.assertEqual(
                        row["decision_anchor"],
                        "dataset-start",
                    )
                    self.assertEqual(row["decision_session"], "dataset")
                    if not expected_eligible:
                        self.assertEqual(
                            row["action"],
                            previous_action,
                        )
                        self.assertFalse(
                            bool(row["risk_rebalance_override"])
                        )
                        self.assertEqual(
                            row["execution_reason"],
                            "decision_schedule_hold",
                        )
                    previous_action = row["action"]
            rl_projection = load_rl_diagnostics(
                project,
                rl_run.result["id"],
            )
            self.assertEqual(
                rl_projection["portfolioMandate"][
                    "implementationPolicy"
                ],
                mandate["implementationPolicy"],
            )
            self.assertEqual(
                rl_projection["portfolioMandate"][
                    "assetMaxAbsWeights"
                ],
                mandate["construction"]["assetMaxAbsWeights"],
            )
            self.assertEqual(
                rl_projection["portfolioMandate"]["benchmark"],
                mandate["construction"]["benchmark"],
            )
            self.assertEqual(
                {
                    key: rl_projection["decisionCadence"][key]
                    for key in ("source", "kind", "bars", "anchor")
                },
                mandate["implementationPolicy"]["decisionPolicy"],
            )
            for audit in rl_run.result["metrics"][
                "constraint_audit"
            ].values():
                self.assertTrue(audit["passed"])
                self.assertEqual(
                    audit["asset_max_abs_weights"],
                    mandate["construction"]["assetMaxAbsWeights"],
                )
            jsonschema.validate(
                rl_projection,
                RL_DIAGNOSTICS_JSON_SCHEMA,
            )
            studio_snapshot = build_studio_snapshot(project.root_dir)
            portfolio_summary = next(
                item
                for item in studio_snapshot["projects"][0]["runs"]
                if item["id"] == portfolio_run.result["id"]
            )
            self.assertEqual(
                portfolio_summary["metricLayers"]["mandate"]["benchmark"],
                mandate["construction"]["benchmark"],
            )
            self.assertEqual(
                portfolio_summary["metricLayers"]["decisionCadence"],
                mandate["implementationPolicy"]["decisionPolicy"],
            )

            delegated_request = load_research_request(
                project.root_dir / "request.json"
            )
            session = start_session(
                project,
                PORTFOLIO_STUDY_ID,
                request=delegated_request,
            )
            baseline_id = session.manifest["baseline"]["runId"]
            evidence_ref = {
                "kind": "run",
                "id": baseline_id,
                "artifactPath": "artifacts/portfolio-report.json",
            }
            report = publish_report(
                project,
                session.manifest["id"],
                {
                    "schemaVersion": 1,
                    "kind": "autoquant-research-report-analysis",
                    "title": "AAPL and MSFT versus SPY",
                    "executiveSummary": (
                        "The fixed research book is evaluated against SPY "
                        "without granting SPY position authority."
                    ),
                    "findings": [
                        {
                            "id": "caller-benchmark",
                            "claim": "SPY is the fixed opportunity-cost reference.",
                            "confidence": "high",
                            "evidenceRefs": [evidence_ref],
                        }
                    ],
                    "recommendations": [
                        {
                            "action": "Review relative and absolute evidence.",
                            "rationale": "The benchmark changes evaluation only.",
                            "conditions": ["No trading authority is implied."],
                            "evidenceRefs": [evidence_ref],
                        }
                    ],
                    "limitations": ["Synthetic deterministic fixture."],
                    "unresolvedQuestions": ["Does the edge survive new data?"],
                },
            )
            report_markdown = (
                report.root_dir / "report.md"
            ).read_text(encoding="utf-8")
            self.assertIn("`SPY long`", report_markdown)
            self.assertIn(
                "`caller-supplied` / evaluation-only",
                report_markdown,
            )
            self.assertIn(
                "Authorized positions: `AAPL`, `MSFT`",
                report_markdown,
            )
            self.assertIn(
                "Context-only research assets: `NVDA`, `QQQ`, `SPY`",
                report_markdown,
            )
            self.assertIn(
                "Decision cadence / anchor / source: every `4` base bars / "
                "`dataset-start` / `caller-supplied`",
                report_markdown,
            )
            self.assertIn(
                "only mandatory risk scale-down may trade",
                report_markdown,
            )

    def test_caller_asset_roles_are_shared_by_portfolio_and_rl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            roles = {
                "AAPL": "long-only",
                "MSFT": "long-only",
                "SPY": "short-only",
                "QQQ": "context-only",
            }
            policy = {
                "grossLimit": 0.8,
                "maxAbsWeight": 0.2,
                "assetMaxAbsWeights": {"SPY": 0.15},
                "annualizedVolatilityCeiling": 0.2,
                "baseCostBps": 12.0,
                "noTradeOneWay": 0.0,
                "referenceNav": 500_000.0,
                "decisionEveryBars": 1,
                "decisionAnchor": "dataset-start",
            }
            request_path, package_path = write_intake_inputs(
                root,
                request_assets=tuple(roles),
                asset_position_roles=roles,
                portfolio_policy=policy,
            )
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["direction"] = "relative-value"
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "asset-role-desk",
                template=prepared.template,
                template_intake=prepared,
            )
            mandate = load_portfolio_mandate(
                project.root_dir / PORTFOLIO_MANDATE
            )
            self.assertEqual(
                mandate["source"]["assetPositionRoles"],
                "caller-supplied",
            )
            self.assertEqual(mandate["construction"]["family"], "asset-role")
            self.assertEqual(
                mandate["construction"]["assetPositionRoles"],
                {
                    **roles,
                    "NVDA": "context-only",
                },
            )
            self.assertEqual(mandate["construction"]["longGrossLimit"], 0.4)
            self.assertEqual(mandate["construction"]["shortGrossLimit"], 0.4)

            portfolio_run = execute_study(project, PORTFOLIO_STUDY_ID)
            rl_run = execute_study(project, RL_STUDY_ID)
            for run in (portfolio_run, rl_run):
                self.assertEqual(
                    run.result["status"],
                    "succeeded",
                    run.result["errors"],
                )
                self.assertEqual(
                    run.result["metrics"]["portfolio_mandate"],
                    mandate,
                )
            decisions = pd.read_csv(
                portfolio_run.root_dir
                / "artifacts"
                / "portfolio-decisions.csv"
            )
            self.assertTrue(
                (
                    decisions.loc[
                        decisions["asset"].isin(["AAPL", "MSFT"]),
                        "proposed_target_weight",
                    ]
                    >= -1e-12
                ).all()
            )
            self.assertTrue(
                (
                    decisions.loc[
                        decisions["asset"] == "SPY",
                        "proposed_target_weight",
                    ]
                    <= 1e-12
                ).all()
            )
            self.assertTrue(
                (
                    decisions.loc[
                        decisions["asset"].isin(["QQQ", "NVDA"]),
                        "proposed_target_weight",
                    ].abs()
                    <= 1e-12
                ).all()
            )
            projection = load_portfolio_diagnostics(
                project,
                portfolio_run.result["id"],
            )
            self.assertEqual(
                projection["mandate"]["assetPositionRoles"],
                mandate["construction"]["assetPositionRoles"],
            )
            self.assertEqual(
                projection["mandate"]["positionRolesSource"],
                "caller-supplied",
            )
            self.assertEqual(
                {
                    item["asset"]: item["positionRole"]
                    for item in projection["mechanicalDecision"]["positions"]
                },
                mandate["construction"]["assetPositionRoles"],
            )
            jsonschema.validate(
                projection,
                PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA,
            )
            rl_projection = load_rl_diagnostics(
                project,
                rl_run.result["id"],
            )
            self.assertEqual(
                rl_projection["portfolioMandate"][
                    "assetPositionRoles"
                ],
                mandate["construction"]["assetPositionRoles"],
            )
            self.assertEqual(
                rl_projection["portfolioMandate"][
                    "positionRolesSource"
                ],
                "caller-supplied",
            )
            for audit in rl_run.result["metrics"][
                "constraint_audit"
            ].values():
                self.assertTrue(audit["passed"])
                self.assertEqual(
                    audit["asset_position_roles"],
                    mandate["construction"]["assetPositionRoles"],
                )
            studio = build_studio_snapshot(project.root_dir)
            observed = {
                item["id"]: item
                for item in studio["projects"][0]["runs"]
            }
            for run in (portfolio_run, rl_run):
                layer = observed[run.result["id"]]["metricLayers"][
                    "mandate"
                ]
                self.assertEqual(
                    layer["assetPositionRoles"],
                    mandate["construction"]["assetPositionRoles"],
                )
                self.assertEqual(
                    layer["positionRolesSource"],
                    "caller-supplied",
                )

    def test_v3_continuous_base_interval_is_configurable_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_configurable_continuous_inputs(
                root,
                horizon_policy={
                    "primaryForwardBars": 5,
                    "diagnosticForwardBars": [1, 5, 10],
                },
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            self.assertEqual(prepared.package["baseInterval"], "15m")
            self.assertEqual(prepared.annualization_periods, 365 * 24 * 4)
            self.assertEqual(
                prepared.interval_surface,
                {
                    "baseInterval": "15m",
                    "featureIntervals": ["30m", "1h", "4h"],
                    "timestampSemantics": "bar-close",
                    "marketClock": "continuous",
                    "calendar": "24/7",
                    "timezone": "UTC",
                    "anchor": "00:00",
                    "aggregationMethod": (
                        "complete-continuous-utc-midnight-bar-close-v2"
                    ),
                    "terminalBucketPolicy": "omit-incomplete",
                },
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "fifteen-minute-factor",
                template=prepared.template,
                template_intake=prepared,
            )
            run = execute_study(project, OHLCV_STUDY_ID)
            self.assertEqual(
                run.result["status"],
                "succeeded",
                run.result["errors"],
            )
            self.assertEqual(
                run.result["dataset"]["intervalSurface"],
                prepared.interval_surface,
            )
            self.assertEqual(
                run.result["metrics"]["research_horizon"][
                    "primaryForwardBars"
                ],
                5,
            )
            jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)

    def test_session_start_anchor_requires_xnys_intraday_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request_path, package_path = write_configurable_continuous_inputs(
                Path(directory)
            )
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["portfolioPolicy"] = {
                "grossLimit": 0.8,
                "maxAbsWeight": 0.3,
                "assetMaxAbsWeights": {},
                "annualizedVolatilityCeiling": 0.20,
                "baseCostBps": 12.0,
                "noTradeOneWay": 0.0,
                "referenceNav": 500_000.0,
                "decisionEveryBars": 4,
                "decisionAnchor": "session-start",
            }
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "session-start requires a V3 intraday XNYS",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-research-desk",
                )

    def test_v3_xnys_session_surface_runs_across_research_desk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_session_interval_inputs(root)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(
                OHLCV_DATASET_PACKAGE_JSON_SCHEMA,
                format_checker=jsonschema.FormatChecker(),
            ).validate(package)
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            self.assertEqual(prepared.package["schemaVersion"], 3)
            self.assertEqual(prepared.annualization_periods, 252 * 7)
            self.assertEqual(
                prepared.interval_surface,
                {
                    "baseInterval": "1h",
                    "featureIntervals": ["3h", "1d"],
                    "timestampSemantics": "bar-close",
                    "marketClock": "session",
                    "calendar": "XNYS",
                    "timezone": "America/New_York",
                    "anchor": "market-open",
                    "aggregationMethod": (
                        "complete-xnys-regular-session-bar-close-v1"
                    ),
                    "terminalBucketPolicy": "complete-at-session-close",
                },
            )
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "xnys-research-desk",
                template=prepared.template,
                template_intake=prepared,
            )
            intake = load_project_intake(project)
            self.assertIsNotNone(intake)
            mandate = load_portfolio_mandate(
                project.root_dir / PORTFOLIO_MANDATE
            )
            self.assertEqual(
                mandate["construction"]["riskPolicy"][
                    "annualizationPeriods"
                ],
                252 * 7,
            )
            runs = [
                execute_study(project, study_id)
                for study_id in (
                    OHLCV_STUDY_ID,
                    PORTFOLIO_STUDY_ID,
                    RL_STUDY_ID,
                )
            ]
            for run in runs:
                self.assertEqual(
                    run.result["status"],
                    "succeeded",
                    run.result["errors"],
                )
                self.assertEqual(
                    run.result["dataset"]["intervalSurface"],
                    prepared.interval_surface,
                )
                jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)
            self.assertEqual(
                runs[1].result["metrics"]["portfolio"]["validation"]["net"][
                    "annualization_periods"
                ],
                252 * 7,
            )
            observed = build_studio_snapshot(root / "workspace")[
                "projects"
            ][0]
            self.assertTrue(observed["valid"], observed["diagnostics"])
            self.assertEqual(
                observed["intake"]["dataset"]["intervalSurface"],
                prepared.interval_surface,
            )

    def test_v3_xnys_fifteen_minute_caller_cadence_governs_portfolio_and_rl(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = {
                "grossLimit": 0.8,
                "maxAbsWeight": 0.3,
                "assetMaxAbsWeights": {},
                "annualizedVolatilityCeiling": 0.20,
                "baseCostBps": 12.0,
                "noTradeOneWay": 0.0,
                "referenceNav": 500_000.0,
                "decisionEveryBars": 4,
                "decisionAnchor": "session-start",
            }
            request_path, package_path = write_session_interval_inputs(
                root,
                sessions=20,
                base_interval="15m",
                calendar_start="2026-11-09",
                portfolio_policy=policy,
            )
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            self.assertEqual(
                prepared.interval_surface,
                {
                    "baseInterval": "15m",
                    "featureIntervals": ["1h", "3h", "1d"],
                    "timestampSemantics": "bar-close",
                    "marketClock": "session",
                    "calendar": "XNYS",
                    "timezone": "America/New_York",
                    "anchor": "market-open",
                    "aggregationMethod": (
                        "complete-xnys-regular-session-bar-close-v1"
                    ),
                    "terminalBucketPolicy": "complete-at-session-close",
                },
            )
            self.assertEqual(prepared.annualization_periods, 252 * 26)
            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "xnys-fifteen-minute-cadence",
                template=prepared.template,
                template_intake=prepared,
            )
            mandate = load_portfolio_mandate(
                project.root_dir / PORTFOLIO_MANDATE
            )
            self.assertEqual(
                mandate["implementationPolicy"]["decisionPolicy"]["bars"],
                4,
            )
            portfolio_run = execute_study(project, PORTFOLIO_STUDY_ID)
            rl_run = execute_study(project, RL_STUDY_ID)
            for run in (portfolio_run, rl_run):
                self.assertEqual(
                    run.result["status"],
                    "succeeded",
                    run.result["errors"],
                )
                self.assertEqual(
                    run.result["dataset"]["intervalSurface"],
                    prepared.interval_surface,
                )
                self.assertEqual(
                    run.result["metrics"]["portfolio_mandate"],
                    mandate,
                )
                jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)

            source = pd.read_csv(
                package_path.parent / "AAPL.csv"
            )
            source["session"] = pd.to_datetime(
                source["timestamp"],
                utc=True,
            ).dt.strftime("%Y-%m-%d")
            source["session_ordinal"] = source.groupby(
                "session",
                sort=False,
            ).cumcount()
            source_positions = dict(
                zip(
                    source["timestamp"],
                    source["session_ordinal"],
                    strict=True,
                )
            )
            daily = pd.read_csv(
                portfolio_run.root_dir
                / "artifacts"
                / "daily-portfolio.csv"
            )
            for _, row in daily.iterrows():
                timestamp = str(row["timestamp"]).replace("+00:00", "Z")
                expected_eligible = (
                    source_positions[timestamp] % 4 == 0
                )
                self.assertEqual(
                    bool(row["decision_eligible"]),
                    expected_eligible,
                )
                self.assertEqual(row["decision_anchor"], "session-start")
                self.assertEqual(
                    row["decision_session"],
                    timestamp[:10],
                )
                if not expected_eligible:
                    self.assertFalse(bool(row["ordinary_rebalance"]))
                    self.assertTrue(
                        abs(float(row["traded_notional"])) <= 1e-12
                        or bool(row["risk_rebalance_override"])
                    )
            portfolio_projection = load_portfolio_diagnostics(
                project,
                portfolio_run.result["id"],
            )
            rl_projection = load_rl_diagnostics(
                project,
                rl_run.result["id"],
            )
            self.assertEqual(
                portfolio_projection["mandate"][
                    "implementationPolicy"
                ]["decisionPolicy"]["bars"],
                4,
            )
            self.assertEqual(
                portfolio_projection["decisionCadence"]["eligibleBars"],
                int(daily["decision_eligible"].sum()),
            )
            self.assertEqual(
                rl_projection["portfolioMandate"][
                    "implementationPolicy"
                ]["decisionPolicy"]["bars"],
                4,
            )
            self.assertEqual(rl_projection["decisionCadence"]["bars"], 4)
            action_rows = pd.read_csv(
                rl_run.root_dir / "artifacts" / "policy-actions.csv"
            )
            for _, row in action_rows.iterrows():
                timestamp = str(row["timestamp"]).replace("+00:00", "Z")
                self.assertEqual(
                    bool(row["decision_eligible"]),
                    source_positions[timestamp] % 4 == 0,
                )
                self.assertEqual(row["decision_anchor"], "session-start")
                self.assertEqual(row["decision_session"], timestamp[:10])
            first_source_rows = source.groupby(
                "session",
                sort=False,
            ).head(1)
            first_timestamps = set(first_source_rows["timestamp"])
            observed_portfolio = {
                str(row["timestamp"]).replace("+00:00", "Z")
                for _, row in daily[
                    daily["decision_eligible"]
                ].iterrows()
            }
            self.assertTrue(
                first_timestamps - {source.iloc[-1]["timestamp"]}
                <= observed_portfolio
            )
            jsonschema.validate(
                portfolio_projection,
                PORTFOLIO_DIAGNOSTICS_JSON_SCHEMA,
            )
            jsonschema.validate(
                rl_projection,
                RL_DIAGNOSTICS_JSON_SCHEMA,
            )

    def test_v2_multi_interval_package_prepares_complete_locked_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request_path, package_path = write_multi_interval_inputs(
                Path(directory)
            )
            jsonschema.Draft202012Validator(
                OHLCV_DATASET_PACKAGE_JSON_SCHEMA,
                format_checker=jsonschema.FormatChecker(),
            ).validate(json.loads(package_path.read_text(encoding="utf-8")))
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            self.assertTrue(prepared.multi_interval)
            self.assertEqual(
                prepared.interval_surface,
                {
                    "baseInterval": "1h",
                    "featureIntervals": ["3h", "4h", "6h", "12h", "1d"],
                    "timestampSemantics": "bar-close",
                    "marketClock": "continuous",
                    "timezone": "UTC",
                    "anchor": "00:00",
                    "aggregationMethod": "complete-utc-midnight-bar-close-v1",
                },
            )
            self.assertEqual(prepared.start, "2026-01-01T01:00:00Z")
            self.assertEqual(prepared.end, "2026-01-13T00:00:00Z")
            first = prepared.assets[0]
            self.assertIsNotNone(first.interval_frames)
            assert first.interval_frames is not None
            self.assertEqual(
                list(first.interval_frames),
                ["1h", "3h", "4h", "6h", "12h", "1d"],
            )
            self.assertEqual(len(first.interval_frames["1h"]), 288)
            self.assertEqual(len(first.interval_frames["1d"]), 12)
            workspace = initialize_workspace(Path(directory) / "workspace")
            project = create_project(workspace.root_dir, "hourly-lock")
            snapshot, snapshot_hash = materialize_intake_dataset(
                project,
                prepared,
                OHLCV_STUDY_ID,
            )
            self.assertEqual(snapshot["schemaVersion"], 2)
            self.assertEqual(
                snapshot["intervalSurface"],
                prepared.interval_surface,
            )
            self.assertEqual(len(snapshot_hash), 64)
            self.assertEqual(
                [item["interval"] for item in snapshot["assets"][0]["intervals"]],
                ["1h", "3h", "4h", "6h", "12h", "1d"],
            )
            self.assertTrue(
                (project.root_dir / "data" / "ohlcv" / "1d" / "BTC.csv").is_file()
            )
            aligned = load_multi_interval_asset(
                project.root_dir / "data",
                "BTC",
                start=prepared.start,
                end=prepared.end,
            )
            self.assertIsNotNone(aligned)
            assert aligned is not None
            self.assertIn("close__1d", aligned.columns)
            self.assertLessEqual(
                aligned["bar_close__1d"].dropna().max(),
                aligned["timestamp"].max(),
            )

    def test_v2_rehashed_derived_bar_cannot_bypass_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_multi_interval_inputs(root)
            workspace = initialize_workspace(root / "workspace")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            project = create_project(
                workspace.root_dir,
                "tampered-multi-interval",
                template=prepared.template,
                template_intake=prepared,
            )
            data_path = project.root_dir / "data" / "ohlcv" / "12h" / "BTC.csv"
            frame = pd.read_csv(data_path)
            frame.loc[0, "close"] *= 1.01
            frame.to_csv(
                data_path,
                index=False,
                lineterminator="\n",
                float_format="%.12g",
            )

            snapshot_path = project.root_dir / "data" / "ohlcv" / "snapshot.json"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            btc = next(
                item for item in snapshot["assets"] if item["symbol"] == "BTC"
            )
            row = next(
                item for item in btc["intervals"] if item["interval"] == "12h"
            )
            row["normalizedHash"] = hash_file(data_path)
            snapshot_path.write_text(
                json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            study = load_study(project, OHLCV_STUDY_ID)
            intake_path = project.root_dir / "intake.json"
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            intake.update(
                {
                    "datasetSnapshotHash": hash_file(snapshot_path),
                    "datasetHash": study.dataset_hash,
                    "studyHash": study.study_hash,
                    "studyInputHash": study.input_hash,
                }
            )
            intake_path.write_text(
                json.dumps(intake, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "does not reconcile to 1h bars",
            ):
                load_project_intake(project)

    def test_v2_research_desk_runs_one_shared_surface_across_all_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_multi_interval_inputs(
                root,
                observations=420,
            )
            workspace = initialize_workspace(root / "workspace")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                workspace.root_dir,
                "multi-interval-desk",
                template=prepared.template,
                template_intake=prepared,
            )

            intake = load_project_intake(project)
            self.assertIsNotNone(intake)
            mandate = load_portfolio_mandate(
                project.root_dir / PORTFOLIO_MANDATE
            )
            self.assertEqual(
                mandate["construction"]["riskPolicy"][
                    "annualizationPeriods"
                ],
                24 * 365,
            )
            session = start_session(
                project,
                OHLCV_STUDY_ID,
                request=load_research_request(
                    project.root_dir / "request.json"
                ),
            )
            candidate_path = (
                session.worktree_project.root_dir
                / "factors"
                / "candidate.py"
            )
            candidate_path.write_text(
                candidate_path.read_text(encoding="utf-8")
                + "\n# bounded V2 preflight candidate\n",
                encoding="utf-8",
            )
            preflight = execute_candidate_check(
                project,
                session.manifest["id"],
            )
            self.assertEqual(preflight.result["status"], "passed")

            runs = [
                execute_study(project, study_id)
                for study_id in (
                    OHLCV_STUDY_ID,
                    PORTFOLIO_STUDY_ID,
                    RL_STUDY_ID,
                )
            ]
            expected_surface = prepared.interval_surface
            self.assertIsNotNone(expected_surface)
            for run in runs:
                self.assertEqual(
                    run.result["status"],
                    "succeeded",
                    run.result["errors"],
                )
                self.assertEqual(
                    run.result["dataset"]["intervalSurface"],
                    expected_surface,
                )
                jsonschema.validate(run.result, RUN_RESULT_JSON_SCHEMA)
            factor_run = runs[0]
            factor_components = factor_run.result["metrics"][
                "factor_components"
            ]
            self.assertEqual(
                factor_components["trial_disclosure"],
                {
                    "materialized_components": 4,
                    "cross_sectional_score_components": 4,
                    "timestamp_context_components": 0,
                    "pairwise_comparisons": 6,
                    "component_diagnostics_enter_promotion_score": False,
                },
            )
            self.assertEqual(
                [
                    item["id"]
                    for item in factor_components["declaration"][
                        "components"
                    ]
                ],
                [
                    "base_momentum_10",
                    "momentum_3h_4",
                    "momentum_12h_2",
                    "momentum_1d_3",
                ],
            )
            factor_projection = load_factor_diagnostics(
                project,
                factor_run.result["id"],
                point_limit=40,
            )["factorComponents"]
            self.assertTrue(factor_projection["available"])
            self.assertEqual(
                factor_projection["semantics"]["ablationTarget"],
                "fixed-diagnostic-blend-not-candidate-factor",
            )
            self.assertFalse(
                factor_projection["trialDisclosure"][
                    "entersPromotionScore"
                ]
            )
            self.assertEqual(
                {run.result["dataset"]["hash"] for run in runs},
                {runs[0].result["dataset"]["hash"]},
            )
            self.assertEqual(
                runs[1].result["metrics"]["portfolio"]["validation"]["net"][
                    "annualization_periods"
                ],
                24 * 365,
            )
            self.assertEqual(
                runs[2].result["metrics"]["portfolio_mandate"]["construction"][
                    "riskPolicy"
                ]["annualizationPeriods"],
                24 * 365,
            )
            factor_diagnostics = load_factor_diagnostics(
                project,
                runs[0].result["id"],
            )
            portfolio_diagnostics = load_portfolio_diagnostics(
                project,
                runs[1].result["id"],
            )
            rl_diagnostics = load_rl_diagnostics(
                project,
                runs[2].result["id"],
            )
            self.assertTrue(
                factor_diagnostics["protocol"]["splits"]["splits"][
                    "validation"
                ]["end"].endswith("Z")
            )
            self.assertTrue(
                portfolio_diagnostics["currentBook"]["timestamp"].endswith(
                    "Z"
                )
            )
            self.assertEqual(
                rl_diagnostics["portfolioMandate"]["riskPolicy"][
                    "annualizationPeriods"
                ],
                24 * 365,
            )
            studio = build_studio_snapshot(workspace.root_dir)
            observed = studio["projects"][0]
            self.assertTrue(observed["valid"], observed["diagnostics"])
            self.assertEqual(observed["diagnostics"], [])
            self.assertEqual(
                observed["intake"]["dataset"]["intervalSurface"],
                expected_surface,
            )

    def test_v2_rejects_forming_semantics_clock_and_hourly_gaps(self) -> None:
        for mutate, expected in (
            (
                lambda package: package.update(
                    {"timestampSemantics": "bar-open"}
                ),
                "must mean bar-close",
            ),
            (
                lambda package: package["market"].update(
                    {"clock": "session"}
                ),
                "continuous 24/7 UTC",
            ),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                request_path, package_path = write_multi_interval_inputs(
                    Path(directory)
                )
                package = json.loads(package_path.read_text(encoding="utf-8"))
                mutate(package)
                package_path.write_text(json.dumps(package), encoding="utf-8")
                with self.assertRaisesRegex(AutoQuantValidationError, expected):
                    prepare_project_intake(
                        request_path,
                        package_path,
                        "ohlcv-factor-lab",
                    )

        with tempfile.TemporaryDirectory() as directory:
            request_path, package_path = write_multi_interval_inputs(Path(directory))
            package = json.loads(package_path.read_text(encoding="utf-8"))
            source = package_path.parent / package["assets"][0]["path"]
            frame = pd.read_csv(source).drop(index=10)
            frame.to_csv(source, index=False)
            with self.assertRaisesRegex(AutoQuantValidationError, "without gaps"):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-factor-lab",
                )

    def test_portfolio_intake_locks_request_data_study_and_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(root / "workspace", name="Quant Desk")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-portfolio-lab",
            )
            project = create_project(
                workspace.root_dir,
                "us-leadership",
                name=prepared.request["title"],
                description=prepared.request["question"],
                template=prepared.template,
                template_intake=prepared,
            )

            intake = load_project_intake(project)
            self.assertIsNotNone(intake)
            assert intake is not None
            self.assertEqual(intake["manifest"]["status"], "ready-for-session")
            self.assertEqual(intake["study"]["id"], PORTFOLIO_STUDY_ID)
            self.assertEqual(
                intake["dataset"]["requestedAssets"],
                ["AAPL", "MSFT"],
            )
            self.assertEqual(len(intake["dataset"]["universe"]), 5)
            self.assertEqual(
                intake["dataset"]["provider"]["name"],
                "deterministic-test-provider",
            )
            self.assertEqual(
                intake["dataset"]["priceAdjustment"],
                "provider-adjusted",
            )
            for asset in intake["dataset"]["assets"]:
                source = package_path.parent / asset["sourcePath"]
                normalized = (
                    project.root_dir
                    / project.manifest.directories["data"]
                    / asset["normalizedPath"]
                )
                self.assertEqual(asset["sourceHash"], hash_file(source))
                self.assertEqual(asset["normalizedHash"], hash_file(normalized))
            study = load_study(project, PORTFOLIO_STUDY_ID)
            mandate = load_portfolio_mandate(
                project.root_dir / PORTFOLIO_MANDATE
            )
            self.assertEqual(mandate["source"]["direction"], "long")
            self.assertEqual(mandate["tradableAssets"], ["AAPL", "MSFT"])
            self.assertEqual(
                mandate["contextAssets"],
                ["NVDA", "QQQ", "SPY"],
            )
            self.assertEqual(
                study.definition.dependencies,
                {
                    "paths": [
                        PORTFOLIO_MANDATE,
                        RESEARCH_HORIZON,
                    ]
                },
            )
            self.assertEqual(study.definition.dataset.universe, intake["dataset"]["universe"])
            self.assertEqual(
                study.definition.dataset.time_range.start,
                intake["dataset"]["timeRange"]["start"],
            )
            self.assertEqual(len(study.dataset_hashes), 7)

            snapshot = build_studio_snapshot(workspace.root_dir)
            observed = snapshot["projects"][0]
            self.assertEqual(
                observed["intake"]["request"]["title"],
                "US leadership durability",
            )
            self.assertEqual(
                observed["intake"]["commands"][0]["id"],
                "session.start",
            )
            self.assertEqual(observed["counts"]["sessions"], 0)

            run = execute_study(project, PORTFOLIO_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            self.assertEqual(
                run.result["dataset"]["universe"],
                list(prepared.universe),
            )
            self.assertEqual(
                run.result["metrics"]["portfolio_mandate"],
                mandate,
            )
            diagnostics = load_portfolio_diagnostics(
                project,
                run.result["id"],
            )
            self.assertEqual(diagnostics["mandate"]["direction"], "long")
            self.assertEqual(
                diagnostics["mandate"]["tradableAssets"],
                ["AAPL", "MSFT"],
            )
            decision = diagnostics["mechanicalDecision"]
            self.assertEqual(decision["signalGate"]["family"], "long-cash")
            sizing = diagnostics["sizingAnatomy"]
            self.assertEqual(
                sizing["construction"]["family"],
                "long-cash",
            )
            self.assertEqual(sizing["sides"][1]["configuredBudget"], 0.0)
            self.assertTrue(sizing["sides"][1]["allocationFeasible"])
            self.assertTrue(
                all(
                    position["side"] == "context"
                    for position in sizing["positions"]
                    if not position["tradable"]
                )
            )
            monetization = diagnostics["signalMonetization"]
            self.assertTrue(
                monetization["validation"]["reconciliation"]["passed"]
            )
            monetization_assets = {
                item["asset"]: item
                for item in monetization["validation"]["byAsset"]
            }
            for asset in ("NVDA", "QQQ", "SPY"):
                self.assertEqual(
                    monetization_assets[asset]["equalIntent"],
                    0.0,
                )
                self.assertEqual(
                    monetization_assets[asset]["preGovernorSizing"],
                    0.0,
                )
                self.assertEqual(
                    monetization_assets[asset]["governedTarget"],
                    0.0,
                )
            self.assertEqual(
                monetization["validation"]["reconciliation"][
                    "maximumEqualIntentGrossLimitExcess"
                ],
                0.0,
            )
            self.assertEqual(
                monetization["validation"]["reconciliation"][
                    "maximumEqualIntentCapExcess"
                ],
                0.0,
            )
            self.assertEqual(decision["tradingAuthority"], "none")
            decision_by_asset = {
                item["asset"]: item for item in decision["positions"]
            }
            for asset in ("AAPL", "MSFT"):
                position = decision_by_asset[asset]
                self.assertIn(position["signalState"], {0, 1})
                self.assertEqual(len(position["nextTriggers"]), 1)
                self.assertIn(
                    position["nextTriggers"][0]["event"],
                    {"enter_long", "exit_long"},
                )
            for position in diagnostics["currentBook"]["positions"]:
                if position["asset"] in {"NVDA", "QQQ", "SPY"}:
                    self.assertFalse(position["tradable"])
                    self.assertEqual(position["targetWeight"], 0.0)
                    self.assertEqual(position["allocationStatus"], "context_only")
                    decision_position = decision_by_asset[
                        position["asset"]
                    ]
                    self.assertEqual(
                        decision_position["nextTriggers"],
                        [],
                    )
                    self.assertIsNone(
                        decision_position["nearestTrigger"]
                    )
            session = start_session(
                project,
                PORTFOLIO_STUDY_ID,
                request=load_research_request(project.root_dir / "request.json"),
            )
            self.assertIsNotNone(session.delegation)
            self.assertEqual(
                session.delegation["request"]["assets"][0]["symbol"],
                "AAPL",
            )

    def test_factor_and_rl_templates_run_on_the_same_intake_contract(self) -> None:
        for template, study_id in (
            ("ohlcv-factor-lab", OHLCV_STUDY_ID),
            ("ohlcv-rl-factor-lab", RL_STUDY_ID),
        ):
            with self.subTest(template=template), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request_path, package_path = write_intake_inputs(root)
                workspace = initialize_workspace(root / "workspace")
                prepared = prepare_project_intake(
                    request_path,
                    package_path,
                    template,
                )
                project = create_project(
                    workspace.root_dir,
                    "market-lab",
                    template=template,
                    template_intake=prepared,
                )

                run = execute_study(project, study_id)

                self.assertEqual(run.result["status"], "succeeded")
                self.assertEqual(
                    run.result["dataset"]["id"],
                    "bounded-us-equities",
                )

    def test_request_bound_mandate_tampering_invalidates_intake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(root / "workspace")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-research-desk",
            )
            project = create_project(
                workspace.root_dir,
                "tamper-desk",
                template=prepared.template,
                template_intake=prepared,
            )
            mandate_path = project.root_dir / PORTFOLIO_MANDATE
            mandate = json.loads(mandate_path.read_text(encoding="utf-8"))
            mandate["tradableAssets"].append("NVDA")
            mandate_path.write_text(
                json.dumps(mandate, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Mandate id is not derived|differs from the normalized request",
            ):
                load_project_intake(project)

    def test_invalid_intakes_leave_workspace_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(root / "workspace")
            package = json.loads(package_path.read_text())
            package["assets"][-1]["path"] = "../outside.csv"
            package_path.write_text(json.dumps(package), encoding="utf-8")

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "confined POSIX relative path",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-portfolio-lab",
                )

            reloaded = load_workspace(workspace.root_dir)
            self.assertIsNone(reloaded.manifest.default_project)
            self.assertEqual(list(reloaded.projects_dir.iterdir()), [])

    def test_misalignment_and_request_mismatch_are_structured_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            package = json.loads(package_path.read_text())
            package["assetClass"] = "fund"
            package_path.write_text(json.dumps(package), encoding="utf-8")

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "requested asset class",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-portfolio-lab",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            package = json.loads(package_path.read_text())
            source = package_path.parent / package["assets"][-1]["path"]
            rows = source.read_text(encoding="utf-8").splitlines()
            source.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "exact daily timestamp panel",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-portfolio-lab",
                )

    def test_v4_factor_intake_preserves_ragged_daily_availability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(
                root,
                observations=260,
                factor_policy={
                    "claim": "known-style-validation",
                    "knownStyle": "reversal_5",
                },
            )
            package = json.loads(
                package_path.read_text(encoding="utf-8")
            )
            package["schemaVersion"] = 4
            package["panelPolicy"] = {
                "alignment": "observed-only",
                "missingObservation": "absent-no-fill",
            }
            package_path.write_text(
                json.dumps(package, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            jsonschema.validate(
                package,
                OHLCV_DATASET_PACKAGE_JSON_SCHEMA,
            )
            source = package_path.parent / package["assets"][-1]["path"]
            frame = pd.read_csv(source).drop(index=[0, 25, 100])
            frame.to_csv(source, index=False)

            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            self.assertEqual(prepared.start, "2024-01-02")
            self.assertEqual(prepared.end, "2024-12-30")
            self.assertEqual(len(prepared.assets[-1].frame), 257)

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "supported only by the ohlcv-factor-lab",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-portfolio-lab",
                )

            project = create_project(
                initialize_workspace(root / "workspace").root_dir,
                "ragged-factor",
                template=prepared.template,
                template_intake=prepared,
            )
            intake = load_project_intake(project)
            assert intake is not None
            availability = intake["dataset"]["availability"]
            self.assertEqual(availability["unionObservations"], 260)
            self.assertEqual(
                availability["intersectionObservations"],
                257,
            )
            self.assertEqual(
                availability["eligibleFactorObservations"],
                260,
            )
            self.assertEqual(
                availability["assetsPerTimestamp"],
                {"minimum": 4, "median": 5.0, "maximum": 5},
            )
            self.assertAlmostEqual(
                availability["observationCoverage"],
                1297 / 1300,
            )
            self.assertEqual(
                intake["dataset"]["assets"][-1]["start"],
                "2024-01-03",
            )
            run = execute_study(project, OHLCV_STUDY_ID)
            self.assertEqual(
                run.result["status"],
                "succeeded",
                run.result["errors"],
            )
            self.assertEqual(
                run.result["metrics"]["factor_api"]["shape"],
                "ragged-observed-only",
            )
            self.assertAlmostEqual(
                run.result["metrics"]["input_availability"][
                    "observation_coverage"
                ],
                1297 / 1300,
            )
            diagnostics = load_factor_diagnostics(
                project,
                run.result["id"],
            )
            self.assertTrue(
                diagnostics["inputAvailability"]["available"]
            )
            self.assertEqual(
                diagnostics["inputAvailability"][
                    "assetsPerTimestamp"
                ]["input"],
                {"minimum": 4, "median": 5.0, "maximum": 5},
            )

    def test_duplicate_non_positive_and_weekend_rows_are_rejected(self) -> None:
        def duplicate(frame: pd.DataFrame) -> pd.DataFrame:
            return pd.concat([frame, frame.iloc[[-1]]], ignore_index=True)

        def non_positive(frame: pd.DataFrame) -> pd.DataFrame:
            frame.loc[0, "volume"] = 0.0
            return frame

        def weekend(frame: pd.DataFrame) -> pd.DataFrame:
            frame.loc[0, "date"] = "2024-01-06"
            return frame

        for label, mutate, expected in (
            ("duplicate", duplicate, "duplicate candle timestamps"),
            ("non-positive", non_positive, "strictly positive"),
            ("weekend", weekend, "cannot contain weekend"),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request_path, package_path = write_intake_inputs(root)
                workspace = initialize_workspace(root / "workspace")
                package = json.loads(package_path.read_text(encoding="utf-8"))
                source = package_path.parent / package["assets"][0]["path"]
                frame = pd.read_csv(source)
                mutate(frame).to_csv(source, index=False)

                with self.assertRaisesRegex(AutoQuantValidationError, expected):
                    prepare_project_intake(
                        request_path,
                        package_path,
                        "ohlcv-portfolio-lab",
                    )

                reloaded = load_workspace(workspace.root_dir)
                self.assertIsNone(reloaded.manifest.default_project)
                self.assertEqual(list(reloaded.projects_dir.iterdir()), [])

    def test_source_symlinks_and_malformed_asset_types_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            source = package_path.parent / package["assets"][0]["path"]
            outside = root / "outside.csv"
            shutil.copyfile(source, outside)
            source.unlink()
            source.symlink_to(outside)

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "cannot be symlinks",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-portfolio-lab",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            package["assets"][0]["symbol"] = {"not": "a string"}
            package_path.write_text(
                json.dumps(package),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "non-empty string",
            ):
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-portfolio-lab",
                )

    def test_tampering_with_snapshot_or_normalized_bytes_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(root / "workspace")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            project = create_project(
                workspace.root_dir,
                "tamper-lab",
                template=prepared.template,
                template_intake=prepared,
            )
            normalized = project.root_dir / "data" / "ohlcv" / "AAPL.csv"
            normalized.write_text(
                normalized.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Normalized asset hash mismatch",
            ):
                load_project_intake(project)

    def test_rehashed_snapshot_cannot_diverge_from_the_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            workspace = initialize_workspace(root / "workspace")
            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )
            project = create_project(
                workspace.root_dir,
                "snapshot-chain",
                template=prepared.template,
                template_intake=prepared,
            )
            snapshot_path = project.root_dir / "data" / "ohlcv" / "snapshot.json"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot["requestedAssets"] = ["NVDA"]
            snapshot_path.write_text(
                json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            intake_path = project.root_dir / "intake.json"
            manifest = json.loads(intake_path.read_text(encoding="utf-8"))
            manifest["datasetSnapshotHash"] = hash_file(snapshot_path)
            intake_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "requested assets differ",
            ):
                load_project_intake(project)


if __name__ == "__main__":
    unittest.main()
