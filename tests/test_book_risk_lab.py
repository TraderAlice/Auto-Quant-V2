from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

from autoquant.book_risk_explorer import (
    BOOK_RISK_DIAGNOSTICS_JSON_SCHEMA,
    load_book_risk_diagnostics,
)
from autoquant.intake import load_project_intake, prepare_project_intake
from autoquant.orientation import (
    AGENT_WORK_BRIEF_JSON_SCHEMA,
    build_agent_work_brief,
)
from autoquant.position_snapshots import (
    POSITION_SNAPSHOT,
    load_position_snapshot,
)
from autoquant.runs import execute_study
from autoquant.sessions import start_session
from autoquant.studies import hash_file
from autoquant.studio import build_studio_snapshot
from autoquant.templates import BOOK_RISK_STUDY_ID
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)
from tests.intake_helpers import write_intake_inputs


PROJECT_DIR = Path(__file__).resolve().parents[1]


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "autoquant", *arguments],
        cwd=PROJECT_DIR,
        capture_output=True,
        check=False,
        text=True,
    )


def _book_request(path: Path) -> None:
    request = json.loads(path.read_text(encoding="utf-8"))
    request["assets"] = [
        {
            "symbol": symbol,
            "assetClass": "equity",
            "venue": "US-COMPOSITE",
            "positionRole": "long-only",
        }
        for symbol in ("AAPL", "MSFT", "NVDA", "QQQ")
    ]
    request["direction"] = "research-only"
    request["positionSnapshot"] = {
        "kind": "reported-weights",
        "asOf": "2024-12-30T21:00:00Z",
        "baseCurrency": "USD",
        "weights": {
            "AAPL": 0.20,
            "MSFT": 0.25,
            "NVDA": 0.30,
            "QQQ": 0.25,
        },
        "cashWeight": 0.0,
    }
    path.write_text(
        json.dumps(request, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _book_scenario_request(path: Path) -> None:
    _book_request(path)
    request = json.loads(path.read_text(encoding="utf-8"))
    request["assets"].append(
        {
            "symbol": "TSLA",
            "assetClass": "equity",
            "venue": "US-COMPOSITE",
            "positionRole": "long-only",
        }
    )
    request["positionScenarios"] = [
        {
            "id": "fund-tsla-from-nvda",
            "name": "Fund TSLA from NVDA",
            "kind": "hypothetical-weights",
            "asOf": "2024-12-30T21:00:00Z",
            "baseCurrency": "USD",
            "weights": {
                "AAPL": 0.20,
                "MSFT": 0.25,
                "NVDA": 0.20,
                "QQQ": 0.25,
                "TSLA": 0.10,
            },
            "cashWeight": 0.0,
        },
        {
            "id": "fund-tsla-from-qqq",
            "name": "Fund TSLA from QQQ",
            "kind": "hypothetical-weights",
            "asOf": "2024-12-30T21:00:00Z",
            "baseCurrency": "USD",
            "weights": {
                "AAPL": 0.20,
                "MSFT": 0.25,
                "NVDA": 0.30,
                "QQQ": 0.15,
                "TSLA": 0.10,
            },
            "cashWeight": 0.0,
        },
    ]
    path.write_text(
        json.dumps(request, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _book_sizing_request(path: Path, *, ceiling: float = 0.15) -> None:
    _book_request(path)
    request = json.loads(path.read_text(encoding="utf-8"))
    request["positionSizing"] = {
        "kind": "reduce-one-asset-to-cash-for-volatility-ceiling",
        "asset": "NVDA",
        "destination": "cash",
        "annualizedVolatilityCeiling": ceiling,
        "lookbackBars": 252,
    }
    path.write_text(
        json.dumps(request, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rehash_run(run_root: Path) -> None:
    manifest_path = run_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = {
        path.relative_to(run_root).as_posix(): hash_file(path)
        for path in sorted(run_root.rglob("*"))
        if path.is_file() and path != manifest_path
    }
    manifest["resultHash"] = manifest["files"]["result.json"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class BookRiskLabTests(unittest.TestCase):
    def _real_project(self, root: Path):
        request_path, package_path = write_intake_inputs(
            root,
            observations=260,
            request_assets=("AAPL", "MSFT", "NVDA", "QQQ"),
            asset_position_roles={
                "AAPL": "long-only",
                "MSFT": "long-only",
                "NVDA": "long-only",
                "QQQ": "long-only",
            },
        )
        _book_request(request_path)
        prepared = prepare_project_intake(
            request_path,
            package_path,
            "ohlcv-book-risk-lab",
        )
        workspace = initialize_workspace(root / "workspace")
        return create_project(
            workspace.root_dir,
            "reported-book",
            template=prepared.template,
            template_intake=prepared,
        )

    def _scenario_project(self, root: Path):
        request_path, package_path = write_intake_inputs(
            root,
            observations=260,
            assets=("AAPL", "MSFT", "NVDA", "QQQ", "TSLA"),
            request_assets=("AAPL", "MSFT", "NVDA", "QQQ", "TSLA"),
            asset_position_roles={
                "AAPL": "long-only",
                "MSFT": "long-only",
                "NVDA": "long-only",
                "QQQ": "long-only",
                "TSLA": "long-only",
            },
        )
        _book_scenario_request(request_path)
        prepared = prepare_project_intake(
            request_path,
            package_path,
            "ohlcv-book-risk-lab",
        )
        workspace = initialize_workspace(root / "workspace")
        return create_project(
            workspace.root_dir,
            "reported-book-scenarios",
            template=prepared.template,
            template_intake=prepared,
        )

    def _sizing_project(self, root: Path, *, ceiling: float = 0.15):
        request_path, package_path = write_intake_inputs(
            root,
            observations=260,
            request_assets=("AAPL", "MSFT", "NVDA", "QQQ"),
            asset_position_roles={
                "AAPL": "long-only",
                "MSFT": "long-only",
                "NVDA": "long-only",
                "QQQ": "long-only",
            },
        )
        _book_sizing_request(request_path, ceiling=ceiling)
        prepared = prepare_project_intake(
            request_path,
            package_path,
            "ohlcv-book-risk-lab",
        )
        workspace = initialize_workspace(root / "workspace")
        return create_project(
            workspace.root_dir,
            "reported-book-sizing",
            template=prepared.template,
            template_intake=prepared,
        )

    def test_position_sizing_freezes_one_bounded_caller_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._sizing_project(Path(directory))
            snapshot = load_position_snapshot(
                project.root_dir / POSITION_SNAPSHOT
            )
            self.assertEqual(snapshot["scenarios"], [])
            self.assertEqual(
                snapshot["sizingPolicy"],
                {
                    "kind": (
                        "reduce-one-asset-to-cash-for-volatility-ceiling"
                    ),
                    "asset": "NVDA",
                    "destination": "cash",
                    "annualizedVolatilityCeiling": 0.15,
                    "lookbackBars": 252,
                    "authority": {
                        "decisionPath": (
                            "caller-bounded-historical-sizing"
                        ),
                        "tradingAuthority": "none",
                    },
                },
            )

    def test_position_sizing_rejects_ambiguous_or_unauthorized_paths(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(
                root,
                observations=260,
                request_assets=("AAPL", "MSFT", "NVDA", "QQQ"),
                asset_position_roles={
                    "AAPL": "long-only",
                    "MSFT": "long-only",
                    "NVDA": "long-only",
                    "QQQ": "long-only",
                },
            )
            _book_sizing_request(request_path)
            request = json.loads(
                request_path.read_text(encoding="utf-8")
            )
            request["positionSizing"]["asset"] = "UNREQUESTED"
            request["positionSizing"]["destination"] = "AAPL"
            request["positionSizing"]["lookbackBars"] = 100
            request["positionSizing"][
                "annualizedVolatilityCeiling"
            ] = 0
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            codes = {issue.code for issue in captured.exception.issues}
            self.assertIn("request.position-sizing-held-long", codes)
            self.assertIn("request.position-sizing-destination", codes)
            self.assertIn("request.position-sizing-lookback", codes)
            self.assertIn("request.position-sizing-ceiling", codes)

            _book_scenario_request(request_path)
            request = json.loads(
                request_path.read_text(encoding="utf-8")
            )
            request["positionSizing"] = {
                "kind": (
                    "reduce-one-asset-to-cash-for-volatility-ceiling"
                ),
                "asset": "NVDA",
                "destination": "cash",
                "annualizedVolatilityCeiling": 0.15,
                "lookbackBars": 252,
            }
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            self.assertIn(
                "request.position-sizing-scenarios",
                {issue.code for issue in captured.exception.issues},
            )

    def test_position_sizing_solves_exact_boundary_and_infeasible_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._sizing_project(
                Path(directory),
                ceiling=0.027,
            )
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            diagnostics = load_book_risk_diagnostics(
                project,
                run.result["id"],
            )
            sizing = diagnostics["positionSizing"]
            self.assertEqual(sizing["status"], "sized")
            self.assertGreater(sizing["result"]["weightReduction"], 0)
            self.assertLess(
                sizing["result"]["resultingWeight"],
                sizing["result"]["startingWeight"],
            )
            self.assertAlmostEqual(
                sizing["result"]["annualizedVolatility"],
                0.027,
                places=10,
            )
            self.assertTrue(sizing["result"]["ceilingSatisfied"])
            human = _run_cli(
                "run",
                "book-risk",
                str(project.root_dir),
                "--run",
                run.result["id"],
            )
            self.assertEqual(human.returncode, 0, human.stderr)
            self.assertIn(
                "Caller-bounded position sizing: sized",
                human.stdout,
            )
            self.assertIn(
                "not a future-volatility guarantee",
                human.stdout,
            )
            brief = build_agent_work_brief(project)
            self.assertIn(
                "target-position sizing evidence",
                brief["primaryAction"]["description"],
            )
            studio = build_studio_snapshot(project.root_dir)
            observed = studio["projects"][0]["bookRiskExplorer"]
            self.assertEqual(
                observed["positionSizing"]["status"],
                "sized",
            )

        with tempfile.TemporaryDirectory() as directory:
            project = self._sizing_project(
                Path(directory),
                ceiling=0.02,
            )
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            diagnostics = load_book_risk_diagnostics(
                project,
                run.result["id"],
            )
            sizing = diagnostics["positionSizing"]
            self.assertEqual(sizing["status"], "infeasible")
            self.assertFalse(sizing["result"]["ceilingSatisfied"])
            self.assertEqual(
                sizing["resultMeaning"],
                "constrained-minimum-evidence-not-recommendation",
            )

    def test_position_sizing_explorer_rejects_rehashed_solution_tamper(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._sizing_project(
                Path(directory),
                ceiling=0.027,
            )
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            report_path = (
                run.root_dir / "artifacts" / "book-risk-report.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["positionSizing"]["quadratic"][
                "coefficientB"
            ] += 0.001
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "book-risk.reconcile",
                {issue.code for issue in captured.exception.issues},
            )

    def test_request_bound_snapshot_runs_and_projects_strict_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._real_project(Path(directory))
            intake = load_project_intake(project)
            assert intake is not None
            self.assertTrue(intake["study"]["current"])
            self.assertEqual(intake["manifest"]["status"], "ready-for-run")
            snapshot = load_position_snapshot(
                project.root_dir / POSITION_SNAPSHOT
            )
            self.assertEqual(snapshot["weights"]["NVDA"], 0.30)
            self.assertEqual(
                snapshot["authority"]["tradingAuthority"],
                "none",
            )

            run = execute_study(project, BOOK_RISK_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            diagnostics = load_book_risk_diagnostics(
                project,
                run.result["id"],
                point_limit=20,
            )
            jsonschema.validate(
                diagnostics,
                BOOK_RISK_DIAGNOSTICS_JSON_SCHEMA,
            )
            self.assertEqual(
                {row["asset"] for row in diagnostics["riskContributions"]},
                {"AAPL", "MSFT", "NVDA", "QQQ"},
            )
            self.assertEqual(
                [row["rank"] for row in diagnostics["reductionPriority"]],
                [1, 2, 3, 4],
            )
            self.assertEqual(len(diagnostics["lookbacks"]), 3)
            self.assertTrue(
                all(
                    row["firstReductionAsset"]
                    in {"AAPL", "MSFT", "NVDA", "QQQ"}
                    for row in diagnostics["lookbacks"]
                )
            )
            self.assertEqual(
                diagnostics["authority"]["tradingAuthority"],
                "none",
            )

            brief = build_agent_work_brief(project)
            jsonschema.validate(brief, AGENT_WORK_BRIEF_JSON_SCHEMA)
            self.assertEqual(brief["primaryAction"]["id"], "run.book-risk")
            self.assertEqual(
                brief["primaryAction"]["expectedEvidenceKind"],
                "book-risk-diagnostics",
            )
            self.assertEqual(brief["review"]["status"], "complete")
            self.assertEqual(
                brief["researchAgenda"]["status"],
                "descriptive-audit-complete",
            )
            self.assertEqual(brief["researchAgenda"]["moves"], [])
            self.assertEqual(
                brief["authority"]["researchAuthority"],
                "fixed-descriptive-audit",
            )

            studio = build_studio_snapshot(project.root_dir)
            observed = studio["projects"][0]
            self.assertEqual(
                observed["bookRiskExplorer"]["run"]["id"],
                run.result["id"],
            )
            self.assertIn(
                "run.book-risk",
                {command["id"] for command in observed["commands"]},
            )
            self.assertEqual(
                [command["id"] for command in observed["intake"]["commands"]],
                ["run.execute"],
            )
            self.assertIsNone(observed["factorExplorer"])
            self.assertIsNone(observed["portfolioExplorer"])

            with self.assertRaises(AutoQuantValidationError) as captured:
                start_session(project, BOOK_RISK_STUDY_ID)
            self.assertIn(
                "session.descriptive-study",
                {issue.code for issue in captured.exception.issues},
            )

    def test_cli_intake_routes_book_risk_to_fixed_run_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(
                root,
                observations=260,
                request_assets=("AAPL", "MSFT", "NVDA", "QQQ"),
                asset_position_roles={
                    "AAPL": "long-only",
                    "MSFT": "long-only",
                    "NVDA": "long-only",
                    "QQQ": "long-only",
                },
            )
            _book_request(request_path)
            workspace = root / "workspace"
            initialized = _run_cli(
                "workspace",
                "init",
                str(workspace),
                "--json",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            created = _run_cli(
                "project",
                "intake",
                str(workspace),
                "reported-book",
                "--request",
                str(request_path),
                "--dataset",
                str(package_path),
                "--template",
                "ohlcv-book-risk-lab",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            envelope = json.loads(created.stdout)
            self.assertEqual(
                envelope["data"]["intake"]["manifest"]["status"],
                "ready-for-run",
            )
            self.assertEqual(
                [action["id"] for action in envelope["nextActions"]],
                ["study.inspect", "run.execute"],
            )

    def test_caller_supplied_funded_scenarios_share_one_fixed_run(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._scenario_project(Path(directory))
            snapshot = load_position_snapshot(
                project.root_dir / POSITION_SNAPSHOT
            )
            self.assertEqual(
                [item["id"] for item in snapshot["scenarios"]],
                ["fund-tsla-from-nvda", "fund-tsla-from-qqq"],
            )
            self.assertEqual(
                {
                    item["authority"]["positionTruth"]
                    for item in snapshot["scenarios"]
                },
                {"caller-hypothetical-not-authenticated"},
            )
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            self.assertEqual(run.result["status"], "succeeded")
            self.assertEqual(run.result["metrics"]["scenario_count"], 2)
            diagnostics = load_book_risk_diagnostics(
                project,
                run.result["id"],
                point_limit=20,
            )
            jsonschema.validate(
                diagnostics,
                BOOK_RISK_DIAGNOSTICS_JSON_SCHEMA,
            )
            comparison = diagnostics["scenarioComparison"]
            self.assertEqual(
                comparison["comparisonUniverse"],
                ["AAPL", "MSFT", "NVDA", "QQQ", "TSLA"],
            )
            self.assertEqual(len(comparison["baselineLookbacks"]), 3)
            self.assertEqual(len(comparison["scenarios"]), 2)
            for lookback_index in range(3):
                self.assertEqual(
                    sorted(
                        int(scenario["lookbacks"][lookback_index][
                            "volatilityRank"
                        ])
                        for scenario in comparison["scenarios"]
                    ),
                    [1, 2],
                )
            for scenario in comparison["scenarios"]:
                self.assertEqual(
                    len(scenario["primaryContributions"]),
                    5,
                )
                self.assertAlmostEqual(
                    sum(
                        row["scenarioAbsoluteRiskShare"]
                        for row in scenario["primaryContributions"]
                    ),
                    1.0,
                )
            observed = build_studio_snapshot(project.root_dir)["projects"][0]
            self.assertEqual(
                len(
                    observed["bookRiskExplorer"][
                        "scenarioComparison"
                    ]["scenarios"]
                ),
                2,
            )
            brief = build_agent_work_brief(project)
            self.assertEqual(
                brief["researchAgenda"]["status"],
                "descriptive-audit-complete",
            )
            self.assertEqual(brief["researchAgenda"]["moves"], [])

    def test_position_scenarios_reject_ambiguous_or_unauthorized_books(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(
                root,
                assets=("AAPL", "MSFT", "NVDA", "QQQ", "TSLA"),
                request_assets=("AAPL", "MSFT", "NVDA", "QQQ", "TSLA"),
                asset_position_roles={
                    "AAPL": "long-only",
                    "MSFT": "long-only",
                    "NVDA": "long-only",
                    "QQQ": "long-only",
                    "TSLA": "long-only",
                },
            )
            _book_scenario_request(request_path)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["positionScenarios"][1]["id"] = request[
                "positionScenarios"
            ][0]["id"]
            request["positionScenarios"][1]["asOf"] = (
                "2024-12-29T21:00:00Z"
            )
            request["positionScenarios"][1]["weights"] = dict(
                request["positionSnapshot"]["weights"]
            )
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            codes = {issue.code for issue in captured.exception.issues}
            self.assertIn("request.position-scenario-duplicate-id", codes)
            self.assertIn("request.position-scenario-time", codes)
            self.assertIn("request.position-scenario-duplicate-book", codes)

            _book_scenario_request(request_path)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["positionScenarios"][0]["weights"]["UNREQUESTED"] = 0.10
            request["positionScenarios"][0]["weights"]["NVDA"] -= 0.10
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            self.assertIn(
                "request.position-scenario-unrequested",
                {issue.code for issue in captured.exception.issues},
            )

    def test_book_risk_intake_requires_funded_position_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            self.assertIn(
                "request.position-snapshot-required",
                {issue.code for issue in captured.exception.issues},
            )

            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["positionSnapshot"] = {
                "kind": "reported-weights",
                "asOf": "2024-12-30T21:00:00Z",
                "baseCurrency": "USD",
                "weights": {"AAPL": 0.6, "MSFT": 0.5},
                "cashWeight": 0.0,
            }
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            self.assertIn(
                "request.position-snapshot-funded",
                {issue.code for issue in captured.exception.issues},
            )

            request["positionSnapshot"] = {
                "kind": "reported-weights",
                "asOf": "2025-01-30T21:00:00Z",
                "baseCurrency": "USD",
                "weights": {"AAPL": 0.5, "MSFT": 0.5},
                "cashWeight": 0.0,
            }
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-book-risk-lab",
                )
            self.assertIn(
                "request.position-snapshot-range",
                {issue.code for issue in captured.exception.issues},
            )

            request["positionSnapshot"]["asOf"] = "2024-12-30T21:00:00Z"
            request_path.write_text(
                json.dumps(request, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(AutoQuantValidationError) as captured:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-factor-lab",
                )
            self.assertIn(
                "request.position-snapshot-template",
                {issue.code for issue in captured.exception.issues},
            )

    def test_explorer_rejects_rehashed_cross_artifact_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._real_project(Path(directory))
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            report_path = (
                run.root_dir / "artifacts" / "book-risk-report.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["contributions"][0]["absoluteRiskShare"] += 0.01
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "book-risk.contributions",
                {issue.code for issue in captured.exception.issues},
            )

    def test_explorer_rejects_rehashed_snapshot_and_method_tampering(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._real_project(Path(directory))
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            report_path = (
                run.root_dir / "artifacts" / "book-risk-report.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            frozen_path = (
                run.root_dir
                / "inputs"
                / "dependency-sources"
                / "strategies"
                / "position-snapshot.json"
            )
            frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
            frozen["asOf"] = "2024-12-30"
            report["positionSnapshot"] = frozen
            frozen_path.write_text(
                json.dumps(frozen, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "position-snapshot.identity",
                {issue.code for issue in captured.exception.issues},
            )

        with tempfile.TemporaryDirectory() as directory:
            project = self._real_project(Path(directory))
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            report_path = (
                run.root_dir / "artifacts" / "book-risk-report.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["method"]["selectionAuthority"] = "invented"
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "book-risk.schema",
                {issue.code for issue in captured.exception.issues},
            )

    def test_explorer_rejects_rehashed_scenario_delta_and_csv_tampering(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._scenario_project(Path(directory))
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            report_path = (
                run.root_dir / "artifacts" / "book-risk-report.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["scenarioComparison"]["scenarios"][0]["lookbacks"][0][
                "annualizedVolatilityDelta"
            ] += 0.01
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "book-risk.reconcile",
                {issue.code for issue in captured.exception.issues},
            )

        with tempfile.TemporaryDirectory() as directory:
            project = self._scenario_project(Path(directory))
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            csv_path = (
                run.root_dir
                / "artifacts"
                / "book-risk-scenario-comparisons.csv"
            )
            with csv_path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                fields = list(reader.fieldnames or [])
            rows[0]["annualizedVolatilityDelta"] = str(
                float(rows[0]["annualizedVolatilityDelta"]) + 0.01
            )
            with csv_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "book-risk.scenario-comparisons",
                {issue.code for issue in captured.exception.issues},
            )

        with tempfile.TemporaryDirectory() as directory:
            project = self._scenario_project(Path(directory))
            run = execute_study(project, BOOK_RISK_STUDY_ID)
            report_path = (
                run.root_dir / "artifacts" / "book-risk-report.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            primary = next(
                row
                for row in report["scenarioComparison"]["scenarios"][0][
                    "lookbacks"
                ]
                if row["lookbackBars"]
                == report["method"]["primaryLookbackBars"]
            )
            replacement = next(
                asset
                for asset in report["scenarioComparison"][
                    "comparisonUniverse"
                ]
                if asset
                != primary["largestAbsoluteRiskContributor"]
            )
            primary["largestAbsoluteRiskContributor"] = replacement
            comparison_path = (
                run.root_dir
                / "artifacts"
                / "book-risk-scenario-comparisons.csv"
            )
            with comparison_path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                fields = list(reader.fieldnames or [])
            for row in rows:
                if (
                    row["scenarioId"]
                    == report["scenarioComparison"]["scenarios"][0]["id"]
                    and int(row["lookbackBars"])
                    == report["method"]["primaryLookbackBars"]
                ):
                    row["largestAbsoluteRiskContributor"] = replacement
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with comparison_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            _rehash_run(run.root_dir)
            with self.assertRaises(AutoQuantValidationError) as captured:
                load_book_risk_diagnostics(project, run.result["id"])
            self.assertIn(
                "book-risk.scenario-contributor",
                {issue.code for issue in captured.exception.issues},
            )
