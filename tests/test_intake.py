from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from autoquant.briefs import load_research_request
from autoquant.intake import (
    load_project_intake,
    prepare_project_intake,
)
from autoquant.runs import execute_study
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
from tests.intake_helpers import write_intake_inputs


class RequestDrivenIntakeTests(unittest.TestCase):
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
