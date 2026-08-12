from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import jsonschema
import pandas as pd

from autoquant.cli import build_parser, dispatch
from autoquant.event_intake import (
    EVENT_PACKAGE_JSON_SCHEMA,
    list_event_snapshots,
    load_event_snapshot,
    materialize_event_package,
    prepare_event_package,
)
from autoquant.intake import prepare_project_intake
from autoquant.studies import hash_bytes, hash_json
from autoquant.workspace import (
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
)
from tests.intake_helpers import write_intake_inputs


class JsonOhlcvIntakeTests(unittest.TestCase):
    def test_array_and_records_envelope_reuse_canonical_ohlcv_intake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            for index, asset in enumerate(package["assets"]):
                csv_path = package_path.parent / asset["path"]
                records = pd.read_csv(csv_path).to_dict(orient="records")
                json_path = csv_path.with_suffix(".json")
                json_path.write_text(
                    json.dumps(
                        records if index % 2 == 0 else {"records": records},
                        separators=(",", ":"),
                    ),
                    encoding="utf-8",
                )
                asset["path"] = json_path.name
            package_path.write_text(json.dumps(package), encoding="utf-8")

            prepared = prepare_project_intake(
                request_path,
                package_path,
                "ohlcv-factor-lab",
            )

            self.assertEqual(len(prepared.assets), 5)
            self.assertEqual(
                tuple(prepared.assets[0].frame.columns),
                ("timestamp", "open", "high", "low", "close", "volume"),
            )
            self.assertEqual(len(prepared.assets[0].frame), 260)

    def test_json_rejects_non_tabular_or_extended_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, package_path = write_intake_inputs(root)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            first = package["assets"][0]
            json_path = package_path.parent / "bad.json"
            json_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {"date": "2024-01-02", "open": {"raw": 1}}
                        ],
                        "meta": {},
                    }
                ),
                encoding="utf-8",
            )
            first["path"] = json_path.name
            package_path.write_text(json.dumps(package), encoding="utf-8")

            with self.assertRaises(AutoQuantValidationError) as raised:
                prepare_project_intake(
                    request_path,
                    package_path,
                    "ohlcv-factor-lab",
                )

            self.assertIn(
                "dataset.json-envelope",
                {issue.code for issue in raised.exception.issues},
            )


class EventPackageIntakeTests(unittest.TestCase):
    def _write_package(self, root: Path, **event_overrides: object) -> Path:
        event = {
            "event_id": "news-2",
            "event_time": "2026-08-02T10:00:00+08:00",
            "published_at": "2026-08-02T02:01:00Z",
            "observed_at": "2026-08-02T02:02:00Z",
            "available_at": "2026-08-02T02:03:00Z",
            "source": "licensed-wire",
            "license": "internal-research-only",
            "content": {
                "headline": "Issuer updates guidance",
                "symbols": ["600000.SH"],
            },
        }
        event.update(event_overrides)
        package = {
            "schemaVersion": 1,
            "kind": "autoquant-event-package",
            "id": "claims-audit",
            "version": "2026-08-02",
            "adapterKind": "financial-news",
            "events": [
                event,
                {
                    **event,
                    "event_id": "news-1",
                    "available_at": "2026-08-02T02:02:30Z",
                    "content": "Earlier observable report",
                },
            ],
        }
        path = root / "events.json"
        path.write_text(json.dumps(package), encoding="utf-8")
        return path

    def test_materializes_causal_content_addressed_event_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = self._write_package(root)
            jsonschema.Draft202012Validator(
                EVENT_PACKAGE_JSON_SCHEMA,
                format_checker=jsonschema.FormatChecker(),
            ).validate(json.loads(package_path.read_text(encoding="utf-8")))
            prepared = prepare_event_package(package_path)
            workspace = initialize_workspace(root / "workspace")
            project = create_project(workspace.root_dir, "event-research")

            snapshot, snapshot_hash = materialize_event_package(project, prepared)

            output = (
                project.root_dir
                / "data"
                / "events"
                / "claims-audit"
                / "2026-08-02"
            )
            event_bytes = (output / "events.jsonl").read_bytes()
            rows = [json.loads(line) for line in event_bytes.splitlines()]
            self.assertEqual([row["event_id"] for row in rows], ["news-1", "news-2"])
            self.assertEqual(rows[1]["event_time"], "2026-08-02T02:00:00Z")
            self.assertEqual(rows[1]["content_hash"], hash_json(rows[1]["content"]))
            self.assertEqual(snapshot["eventsHash"], hash_bytes(event_bytes))
            self.assertEqual(snapshot["snapshotHash"], snapshot_hash)
            self.assertEqual(snapshot["adapterKind"], "financial-news")
            self.assertEqual(snapshot["eventCount"], 2)
            self.assertEqual(
                load_event_snapshot(project, "claims-audit", "2026-08-02"),
                snapshot,
            )
            self.assertEqual(list_event_snapshots(project), [snapshot])

    def test_cli_intakes_lists_and_shows_event_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = self._write_package(root)
            workspace = initialize_workspace(root / "workspace")
            project = create_project(workspace.root_dir, "event-research")
            parser = build_parser()

            intake = dispatch(parser.parse_args([
                "event", "intake", str(project.root_dir), "--package", str(package_path),
            ]))
            listed = dispatch(parser.parse_args(["event", "list", str(project.root_dir)]))
            shown = dispatch(parser.parse_args([
                "event", "show", str(project.root_dir), "--event-package", "claims-audit", "--version", "2026-08-02",
            ]))

            self.assertEqual(intake.command, "event.intake")
            self.assertEqual(listed.data["eventSnapshots"], [intake.data])
            self.assertEqual(shown.data, intake.data)

    def test_rejects_events_available_before_they_were_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_package(
                Path(directory),
                available_at="2026-08-02T02:01:30Z",
            )

            with self.assertRaises(AutoQuantValidationError) as raised:
                prepare_event_package(path)

            self.assertIn(
                "event.available-before-observed",
                {issue.code for issue in raised.exception.issues},
            )

    def test_materialization_rejects_changed_source_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = self._write_package(root)
            prepared = prepare_event_package(package_path)
            package_path.write_text("{}\n", encoding="utf-8")
            workspace = initialize_workspace(root / "workspace")
            project = create_project(workspace.root_dir, "event-research")

            with self.assertRaises(AutoQuantValidationError) as raised:
                materialize_event_package(project, prepared)

            self.assertIn(
                "event-package.source-changed",
                {issue.code for issue in raised.exception.issues},
            )


if __name__ == "__main__":
    unittest.main()
