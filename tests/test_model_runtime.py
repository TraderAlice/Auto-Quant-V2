from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from autoquant.cli import build_parser, dispatch
from autoquant.model_runtime import ModelRuntimeError, load_model_run, run_supervised_model
from autoquant.studies import StudySubject, create_study
from autoquant.workspace import AutoQuantValidationError
from tests.study_helpers import make_project, study_definition


def model_frame(rows: int = 30) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=rows, freq="1h", tz="UTC")
    feature = np.linspace(-2.0, 3.0, rows)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "available_at": timestamps,
            "label_at": timestamps + pd.Timedelta(minutes=30),
            "feature": feature,
            "label": 1.5 + 2.25 * feature,
        }
    )


class SupervisedModelRuntimeTests(unittest.TestCase):
    def test_timestamp_split_is_validation_selected_and_test_blind(self) -> None:
        frame = model_frame()
        arguments = {
            "label_column": "label",
            "feature_columns": ["feature"],
            "split_timestamps": {
                "trainEnd": frame.loc[12, "timestamp"],
                "validationEnd": frame.loc[22, "timestamp"],
            },
            "purge_gap": 1,
            "ridge_alpha": 0.0,
            "seed": 17,
        }
        result = run_supervised_model(frame, **arguments)

        changed_test = frame.copy()
        changed_test.loc[22:, "label"] = 1_000_000.0
        after_test_change = run_supervised_model(changed_test, **arguments)

        self.assertEqual(result["selectedModel"], "ridge-linear")
        self.assertEqual(result["tradingAuthority"], "none")
        self.assertEqual(result["selectionAuthority"], "validation-only")
        self.assertEqual(result["testUse"], "terminal-audit-only")
        self.assertLess(result["metrics"]["validation"]["selected"]["rmse"], 1e-10)
        self.assertEqual(result["artifacts"], after_test_change["artifacts"])
        self.assertEqual(result["selectedModel"], after_test_change["selectedModel"])

    def test_fixed_split_column_and_baseline_are_json_friendly(self) -> None:
        frame = model_frame()
        frame["split"] = ["train"] * 12 + ["validation"] * 10 + ["test"] * 8
        frame.loc[12:, "label"] = 4.0
        result = run_supervised_model(
            frame,
            label_column="label",
            feature_columns=["feature"],
            split_column="split",
            purge_gap=1,
            ridge_alpha=10_000.0,
            seed=3,
        )

        self.assertEqual(result["splitProtocol"]["method"], "fixed-column")
        self.assertEqual(result["splitProtocol"]["rows"], {
            "train": 11,
            "validation": 9,
            "test": 8,
        })
        self.assertIsInstance(result["artifacts"]["modelSha256"], str)
        self.assertEqual(len(result["artifacts"]["modelSha256"]), 64)
        json.dumps(result, allow_nan=False, sort_keys=True)

    def test_rejects_lookahead_overlap_and_nonfinite_input(self) -> None:
        frame = model_frame()
        frame["split"] = ["train"] * 12 + ["validation"] * 10 + ["test"] * 8
        base = {
            "label_column": "label",
            "feature_columns": ["feature"],
            "split_column": "split",
            "purge_gap": 1,
        }

        lookahead = frame.copy()
        lookahead.loc[3, "available_at"] = lookahead.loc[3, "timestamp"] + pd.Timedelta(seconds=1)
        with self.assertRaisesRegex(ModelRuntimeError, "Feature availability") as caught:
            run_supervised_model(lookahead, **base)
        self.assertEqual(caught.exception.code, "model.lookahead")

        overlap = frame.copy()
        overlap.loc[10, "label_at"] = overlap.loc[12, "timestamp"]
        with self.assertRaisesRegex(ModelRuntimeError, "labels overlap") as caught:
            run_supervised_model(overlap, **base)
        self.assertEqual(caught.exception.code, "model.target-overlap")

        nonfinite = frame.copy()
        nonfinite.loc[5, "feature"] = np.inf
        with self.assertRaisesRegex(ModelRuntimeError, "non-finite") as caught:
            run_supervised_model(nonfinite, **base)
        self.assertEqual(caught.exception.code, "model.non-finite")

    def test_rejects_interleaved_fixed_splits(self) -> None:
        frame = model_frame()
        frame["split"] = ["train"] * 12 + ["validation"] * 10 + ["test"] * 8
        frame.loc[20, "split"] = "train"
        with self.assertRaisesRegex(ModelRuntimeError, "non-overlapping") as caught:
            run_supervised_model(
                frame,
                label_column="label",
                feature_columns=["feature"],
                split_column="split",
                purge_gap=1,
            )
        self.assertEqual(caught.exception.code, "model.split-overlap")

    def test_cli_publishes_lists_and_shows_immutable_model_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, project = make_project(directory)
            frame = model_frame()
            frame["split"] = ["train"] * 12 + ["validation"] * 10 + ["test"] * 8
            relative_path = "model-frame.csv"
            frame_path = project.root_dir / project.manifest.directories["data"] / Path(relative_path)
            frame_path.parent.mkdir(exist_ok=True)
            frame.to_csv(frame_path, index=False)
            definition = replace(
                study_definition(
                    study_id="model-quality",
                    dataset_paths=[relative_path],
                ),
                subject=StudySubject("model", "ridge-linear", "v1"),
            )
            create_study(project, definition)
            parser = build_parser()

            executed = dispatch(parser.parse_args([
                "model", "run", str(project.root_dir),
                "--study", "model-quality",
                "--frame", relative_path,
                "--label", "label",
                "--feature", "feature",
                "--split-column", "split",
                "--purge-gap", "1",
            ]))
            listed = dispatch(parser.parse_args(["model", "list", str(project.root_dir)]))
            shown = dispatch(parser.parse_args([
                "model", "show", str(project.root_dir),
                "--model-run", executed.data["id"],
            ]))

            self.assertEqual(executed.command, "model.run")
            self.assertEqual(executed.data["tradingAuthority"], "none")
            self.assertEqual(listed.data["modelRuns"], [executed.data])
            self.assertEqual(shown.data["receipt"], executed.data)
            self.assertEqual(executed.data["result"]["selectionAuthority"], "validation-only")

            receipt_path = (
                project.root_dir
                / "model-runs"
                / executed.data["id"]
                / "receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["tradingAuthority"] = "live"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(AutoQuantValidationError):
                load_model_run(project, executed.data["id"])


if __name__ == "__main__":
    unittest.main()
