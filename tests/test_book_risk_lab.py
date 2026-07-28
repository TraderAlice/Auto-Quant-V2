from __future__ import annotations

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
