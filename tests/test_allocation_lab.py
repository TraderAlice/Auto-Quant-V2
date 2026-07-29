from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import jsonschema
import numpy as np
import pandas as pd

from autoquant.allocation_explorer import (
    ALLOCATION_DIAGNOSTICS_JSON_SCHEMA,
    load_allocation_diagnostics,
)
from autoquant.allocation_policies import (
    ALLOCATION_POLICY,
    load_allocation_contract,
)
from autoquant.briefs import validate_research_request
from autoquant.project_templates.ohlcv_allocation_lab.allocation_core import (
    construct_erc_targets,
    solve_equal_risk_contribution,
)
from autoquant.runs import execute_study
from autoquant.studio import build_studio_snapshot
from autoquant.templates import ALLOCATION_STUDY_ID
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)


def _rehash_run(run_root: Path) -> None:
    manifest_path = run_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = {
        path.relative_to(run_root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(run_root.rglob("*"))
        if path.is_file() and path != manifest_path
    }
    manifest["resultHash"] = manifest["files"]["result.json"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class AllocationContractTests(unittest.TestCase):
    def test_request_accepts_only_funded_fixed_weight_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            project = create_project(
                workspace.root_dir,
                "allocation",
                template="ohlcv-allocation-lab",
            )
            request = json.loads(
                (project.root_dir / "request.json").read_text(encoding="utf-8")
            )
            normalized = validate_research_request(request)
            self.assertEqual(
                normalized["allocationPolicy"]["kind"],
                "equal-risk-contribution",
            )
            self.assertEqual(
                normalized["benchmarkPolicy"]["weights"],
                {"ALPHA": 0.6, "BRAVO": 0.4},
            )
            malformed = json.loads(json.dumps(request))
            malformed["benchmarkPolicy"]["weights"] = {
                "ALPHA": 0.6,
                "BRAVO": 0.3,
            }
            with self.assertRaises(AutoQuantValidationError) as caught:
                validate_research_request(malformed)
            self.assertIn(
                "request.benchmark-funded",
                {issue.code for issue in caught.exception.issues},
            )
            unknown = json.loads(json.dumps(request))
            unknown["allocationPolicy"]["optimizer"] = "magic"
            with self.assertRaises(AutoQuantValidationError) as caught:
                validate_research_request(unknown)
            self.assertIn(
                "schema.unknown",
                {issue.code for issue in caught.exception.issues},
            )


class EqualRiskContributionTests(unittest.TestCase):
    def test_solver_discloses_cap_induced_parity_gap(self) -> None:
        assets = pd.Index(["LOW", "MID", "HIGH"])
        covariance = pd.DataFrame(
            np.diag([0.01, 0.04, 0.09]),
            index=assets,
            columns=assets,
        )
        unconstrained = solve_equal_risk_contribution(
            covariance,
            pd.Series(1.0, index=assets),
            tolerance=1e-5,
        )
        self.assertTrue(unconstrained.converged)
        np.testing.assert_allclose(
            unconstrained.risk_contribution_shares.to_numpy(),
            np.repeat(1.0 / 3.0, 3),
            atol=1e-8,
        )
        capped = solve_equal_risk_contribution(
            covariance,
            pd.Series({"LOW": 0.35, "MID": 1.0, "HIGH": 1.0}),
            tolerance=0.01,
        )
        self.assertEqual(capped.cap_binding_assets, ("LOW",))
        self.assertFalse(capped.converged)
        self.assertGreater(capped.maximum_contribution_error, 0.01)

    def test_target_construction_is_prefix_causal(self) -> None:
        index = pd.bdate_range("2024-01-02", periods=90)
        returns = pd.DataFrame(
            {
                "A": 0.001 + 0.004 * np.sin(np.arange(90) / 5),
                "B": 0.0005 + 0.003 * np.cos(np.arange(90) / 7),
                "C": 0.0002 + 0.005 * np.sin(np.arange(90) / 9),
            },
            index=index,
        )
        closes = 100 * (1 + returns).cumprod()
        contract = {
            "universe": ["A", "B", "C"],
            "tradableAssets": ["A", "B", "C"],
            "method": {
                "covarianceWindow": 20,
                "minimumObservations": 10,
                "contributionTolerance": 0.20,
            },
            "portfolioPolicy": {
                "maxAbsWeight": 0.60,
                "assetMaxAbsWeights": {},
            },
        }
        mask = pd.Series(False, index=index)
        mask.iloc[[20, 40, 60, 80]] = True
        full, _ = construct_erc_targets(closes, contract, mask)
        changed = closes.copy()
        changed.iloc[61:] *= pd.Series({"A": 1.8, "B": 0.7, "C": 1.2})
        changed_targets, _ = construct_erc_targets(changed, contract, mask)
        pd.testing.assert_frame_equal(
            full.loc[: index[60]],
            changed_targets.loc[: index[60]],
        )


class AllocationLabTests(unittest.TestCase):
    def test_template_run_explorer_and_studio_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            project = create_project(
                workspace.root_dir,
                "allocation",
                template="ohlcv-allocation-lab",
            )
            study = json.loads(
                (
                    project.root_dir
                    / "studies"
                    / ALLOCATION_STUDY_ID
                    / "study.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(study["editable"]["paths"], [])
            self.assertEqual(
                study["dependencies"]["paths"],
                [ALLOCATION_POLICY],
            )
            contract = load_allocation_contract(
                project.root_dir / ALLOCATION_POLICY
            )
            self.assertEqual(contract["tradingAuthority"], "none")
            run = execute_study(project, ALLOCATION_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            self.assertEqual(
                {item["kind"] for item in run.result["artifacts"]},
                {
                    "allocation-report",
                    "allocation-daily",
                    "allocation-targets",
                    "allocation-weights",
                    "allocation-reference-weights",
                    "allocation-decisions",
                },
            )
            diagnostics = load_allocation_diagnostics(
                project,
                run.result["id"],
                points=60,
            )
            jsonschema.validate(
                diagnostics,
                ALLOCATION_DIAGNOSTICS_JSON_SCHEMA,
            )
            self.assertTrue(diagnostics["verification"]["strict"])
            self.assertFalse(
                diagnostics["conclusion"]["testUsedForSelection"]
            )
            self.assertEqual(
                diagnostics["latestDecision"]["tradingAuthority"],
                "none",
            )
            self.assertTrue(
                diagnostics["verification"]["riskContributionsReconciled"]
            )
            self.assertTrue(
                diagnostics["verification"]["currentStateReconciled"]
            )
            self.assertEqual(
                diagnostics["currentState"]["tradingAuthority"],
                "none",
            )
            self.assertEqual(
                set(diagnostics["currentState"]["candidatePretradeWeights"]),
                set(contract["universe"]),
            )
            snapshot = build_studio_snapshot(project.root_dir)
            observed = snapshot["projects"][0]
            request_path = project.root_dir / "request.json"
            self.assertEqual(
                observed["agentWorkBrief"]["question"],
                {
                    "title": "Synthetic equal-risk-contribution allocation",
                    "text": (
                        "Does fixed ERC improve on a fixed 60/40 reference?"
                    ),
                    "origin": "project-request",
                    "sourcePath": str(request_path),
                    "requestPath": str(request_path),
                },
            )
            self.assertEqual(
                observed["allocationExplorer"]["run"]["id"],
                run.result["id"],
            )
            self.assertTrue(observed["valid"])

    def test_explorer_rejects_rehashed_accounting_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            project = create_project(
                workspace.root_dir,
                "allocation",
                template="ohlcv-allocation-lab",
            )
            run = execute_study(project, ALLOCATION_STUDY_ID)
            daily_path = (
                run.root_dir / "artifacts" / "allocation-daily.csv"
            )
            daily = pd.read_csv(daily_path)
            daily.loc[50, "excess_net_return"] += 0.01
            daily.to_csv(daily_path, index=False)
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as caught:
                load_allocation_diagnostics(project, run.result["id"])
            self.assertIn(
                "allocation.excess",
                {issue.code for issue in caught.exception.issues},
            )

    def test_explorer_rejects_rehashed_risk_contribution_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            project = create_project(
                workspace.root_dir,
                "allocation",
                template="ohlcv-allocation-lab",
            )
            run = execute_study(project, ALLOCATION_STUDY_ID)
            decisions_path = (
                run.root_dir / "artifacts" / "allocation-decisions.csv"
            )
            decisions = pd.read_csv(decisions_path)
            eligible = decisions[
                decisions["solver_status"] != "insufficient-history"
            ]
            latest = eligible["timestamp"].max()
            row = decisions.index[
                (decisions["timestamp"] == latest)
                & (decisions["asset"] == "ALPHA")
            ][0]
            decisions.loc[row, "target_risk_contribution_share"] += 0.01
            decisions.to_csv(decisions_path, index=False)
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as caught:
                load_allocation_diagnostics(project, run.result["id"])
            self.assertIn(
                "allocation.reconcile",
                {issue.code for issue in caught.exception.issues},
            )
