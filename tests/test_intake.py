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
from autoquant.factor_explorer import load_factor_diagnostics
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
from autoquant.portfolio_explorer import load_portfolio_diagnostics
from autoquant.rl_explorer import load_rl_diagnostics
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
from tests.intake_helpers import write_intake_inputs, write_multi_interval_inputs


class RequestDrivenIntakeTests(unittest.TestCase):
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
                {"paths": [PORTFOLIO_MANDATE]},
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
