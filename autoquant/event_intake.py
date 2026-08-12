"""Provider-neutral, point-in-time event package intake."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

from .studies import hash_bytes, hash_file, hash_json
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


EVENT_PACKAGE_KIND = "autoquant-event-package"
EVENT_SNAPSHOT_KIND = "autoquant-event-snapshot"
EVENT_ADAPTER_KINDS = {
    "a-share-announcement",
    "crypto-event",
    "financial-news",
}
SAFE_EVENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._=-]{0,127}$")
MAX_EVENT_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_EVENT_RECORDS = 100_000
MAX_EVENT_CONTENT_BYTES = 256 * 1024

EVENT_PACKAGE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant provider-neutral point-in-time event package",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "id",
        "version",
        "adapterKind",
        "events",
    ],
    "properties": {
        "schemaVersion": {"const": 1},
        "kind": {"const": EVENT_PACKAGE_KIND},
        "id": {"type": "string", "pattern": SAFE_EVENT_ID.pattern},
        "version": {"type": "string", "pattern": SAFE_EVENT_ID.pattern},
        "adapterKind": {"enum": sorted(EVENT_ADAPTER_KINDS)},
        "events": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_EVENT_RECORDS,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "event_id",
                    "event_time",
                    "published_at",
                    "observed_at",
                    "available_at",
                    "source",
                    "license",
                    "content",
                ],
                "properties": {
                    "event_id": {
                        "type": "string",
                        "pattern": SAFE_EVENT_ID.pattern,
                    },
                    "event_time": {"type": "string", "format": "date-time"},
                    "published_at": {"type": "string", "format": "date-time"},
                    "observed_at": {"type": "string", "format": "date-time"},
                    "available_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": (
                            "Earliest research-safe visibility time; validator "
                            "requires it not precede published_at or observed_at."
                        ),
                    },
                    "source": {"type": "string", "minLength": 1},
                    "license": {"type": "string", "minLength": 1},
                    "content": {
                        "oneOf": [
                            {"type": "string", "minLength": 1},
                            {"type": "array", "minItems": 1},
                            {"type": "object", "minProperties": 1},
                        ]
                    },
                },
            },
        },
    },
}


@dataclass(frozen=True)
class PreparedEventPackage:
    source_path: Path
    package: dict[str, Any]
    package_hash: str
    events: tuple[dict[str, Any], ...]


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _fail(path: Path | str, code: str, message: str) -> NoReturn:
    raise AutoQuantValidationError([_issue(path, code, message)])


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"Non-standard JSON number: {value}")


def _non_empty(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(path, "schema.string", "Must be a non-empty string")
    return value.strip()


def _safe_id(value: Any, path: str) -> str:
    normalized = _non_empty(value, path)
    if not SAFE_EVENT_ID.fullmatch(normalized):
        _fail(path, "event.id", "Must be a path-safe identifier")
    return normalized


def _timestamp(value: Any, path: str) -> tuple[str, datetime]:
    raw = _non_empty(value, path)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        _fail(path, "event.timestamp", "Must be a timezone-aware ISO-8601 timestamp")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(path, "event.timestamp", "Must be a timezone-aware ISO-8601 timestamp")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _read_package(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_EVENT_PACKAGE_BYTES:
            _fail(path, "event-package.size", "Event package exceeds the 64 MiB limit")
        value = json.loads(
            path.read_bytes().decode("utf-8"),
            parse_constant=_reject_json_constant,
        )
    except FileNotFoundError:
        _fail(path, "event-package.missing", "Missing event package")
    except AutoQuantValidationError:
        raise
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as error:
        _fail(path, "event-package.json", f"Invalid event package JSON: {error}")
    if not isinstance(value, dict):
        _fail(path, "event-package.type", "Event package must be a JSON object")
    return value


def prepare_event_package(package_path: str | Path) -> PreparedEventPackage:
    """Validate one bounded event package and freeze its causal records."""

    path = Path(package_path).expanduser().absolute()
    package = _read_package(path)
    required = {"schemaVersion", "kind", "id", "version", "adapterKind", "events"}
    unknown = set(package) - required
    missing = required - set(package)
    if missing or unknown:
        _fail(
            path,
            "event-package.schema",
            "Event package fields differ from the fixed contract; "
            f"missing={sorted(missing)}, unknown={sorted(unknown)}",
        )
    if package["schemaVersion"] != 1 or package["kind"] != EVENT_PACKAGE_KIND:
        _fail(path, "event-package.contract", "Unsupported event package contract")
    package_id = _safe_id(package["id"], f"{path}/id")
    version = _safe_id(package["version"], f"{path}/version")
    adapter_kind = package["adapterKind"]
    if adapter_kind not in EVENT_ADAPTER_KINDS:
        _fail(
            f"{path}/adapterKind",
            "event-package.adapter",
            "adapterKind must be a-share-announcement, crypto-event, or financial-news",
        )
    raw_events = package["events"]
    if not isinstance(raw_events, list) or not raw_events:
        _fail(
            f"{path}/events",
            "event-package.events",
            "Events must be a non-empty array",
        )
    if len(raw_events) > MAX_EVENT_RECORDS:
        _fail(
            f"{path}/events",
            "event-package.event-limit",
            "Event package exceeds the 100,000 record limit",
        )

    event_fields = {
        "event_id",
        "event_time",
        "published_at",
        "observed_at",
        "available_at",
        "source",
        "license",
        "content",
    }
    events: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(raw_events):
        event_path = f"{path}/events/{index}"
        if not isinstance(raw, dict) or set(raw) != event_fields:
            _fail(
                event_path,
                "event.schema",
                "Event fields differ from the fixed contract",
            )
        event_id = _safe_id(raw["event_id"], f"{event_path}/event_id")
        if event_id in identifiers:
            _fail(
                f"{event_path}/event_id",
                "event.duplicate",
                "event_id must be unique",
            )
        identifiers.add(event_id)
        event_time, _ = _timestamp(raw["event_time"], f"{event_path}/event_time")
        published_at, published = _timestamp(
            raw["published_at"], f"{event_path}/published_at"
        )
        observed_at, observed = _timestamp(
            raw["observed_at"], f"{event_path}/observed_at"
        )
        available_at, available = _timestamp(
            raw["available_at"], f"{event_path}/available_at"
        )
        if observed < published:
            _fail(
                f"{event_path}/observed_at",
                "event.observed-before-published",
                "observed_at cannot precede published_at",
            )
        if available < max(published, observed):
            _fail(
                f"{event_path}/available_at",
                "event.available-before-observed",
                "available_at must be at or after both published_at and observed_at",
            )
        content = raw["content"]
        if not isinstance(content, (str, list, dict)) or content in ("", [], {}):
            _fail(
                f"{event_path}/content",
                "event.content",
                "content must be a non-empty string, array, or object",
            )
        if len(
            json.dumps(
                content,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            .encode("utf-8")
        ) > MAX_EVENT_CONTENT_BYTES:
            _fail(
                f"{event_path}/content",
                "event.content-size",
                "Event content exceeds the 256 KiB limit",
            )
        record = {
            "event_id": event_id,
            "event_time": event_time,
            "published_at": published_at,
            "observed_at": observed_at,
            "available_at": available_at,
            "source": _non_empty(raw["source"], f"{event_path}/source"),
            "license": _non_empty(raw["license"], f"{event_path}/license"),
            "content": content,
            "content_hash": hash_json(content),
        }
        record["record_hash"] = hash_json(record)
        events.append(record)

    events.sort(key=lambda item: (item["available_at"], item["event_id"]))
    normalized_package = {
        "schemaVersion": 1,
        "kind": EVENT_PACKAGE_KIND,
        "id": package_id,
        "version": version,
        "adapterKind": adapter_kind,
        "events": events,
    }
    return PreparedEventPackage(
        source_path=path,
        package=normalized_package,
        package_hash=hash_file(path),
        events=tuple(events),
    )


def materialize_event_package(
    project: ProjectContext,
    prepared: PreparedEventPackage,
) -> tuple[dict[str, Any], str]:
    """Materialize immutable JSONL event evidence below Project data/events."""

    if hash_file(prepared.source_path) != prepared.package_hash:
        _fail(
            prepared.source_path,
            "event-package.source-changed",
            "Event package changed after validation",
        )
    package_id = _safe_id(prepared.package.get("id"), "event-package/id")
    version = _safe_id(prepared.package.get("version"), "event-package/version")
    if prepared.package.get("adapterKind") not in EVENT_ADAPTER_KINDS:
        _fail(
            "event-package/adapterKind",
            "event-package.adapter",
            "Prepared adapterKind is unsupported",
        )
    if not prepared.events:
        _fail("event-package/events", "event-package.events", "Events cannot be empty")
    for index, event in enumerate(prepared.events):
        body = {key: value for key, value in event.items() if key != "record_hash"}
        if (
            event.get("content_hash") != hash_json(event.get("content"))
            or event.get("record_hash") != hash_json(body)
        ):
            _fail(
                f"event-package/events/{index}",
                "event-package.prepared-changed",
                "Prepared event content differs from its validation receipt",
            )
    data_root = confined_path(
        project.root_dir,
        project.manifest.directories["data"],
        "project/directories/data",
    )
    output = confined_path(
        data_root,
        f"events/{package_id}/{version}",
        "event-package/output",
    )
    if output.exists() or output.is_symlink():
        _fail(output, "event-package.collision", "Event package output already exists")

    event_bytes = b"".join(
        (
            json.dumps(
                event,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        for event in prepared.events
    )
    events_hash = hash_bytes(event_bytes)
    manifest = {
        "schemaVersion": 1,
        "kind": EVENT_SNAPSHOT_KIND,
        "id": prepared.package["id"],
        "version": prepared.package["version"],
        "adapterKind": prepared.package["adapterKind"],
        "eventCount": len(prepared.events),
        "availableStart": prepared.events[0]["available_at"],
        "availableEnd": prepared.events[-1]["available_at"],
        "sourcePackageHash": prepared.package_hash,
        "eventsPath": "events.jsonl",
        "eventsHash": events_hash,
        "contentHashes": [
            {
                "event_id": event["event_id"],
                "content_hash": event["content_hash"],
                "record_hash": event["record_hash"],
            }
            for event in prepared.events
        ],
    }
    manifest_hash = hash_json(manifest)
    manifest["snapshotHash"] = manifest_hash
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        (staging / "events.jsonl").write_bytes(event_bytes)
        (staging / "snapshot.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staging, output)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return manifest, manifest_hash


def load_event_snapshot(
    project: ProjectContext,
    package_id: str,
    version: str,
) -> dict[str, Any]:
    """Verify one materialized event snapshot and its immutable event bytes."""

    package_id = _safe_id(package_id, "event-package/id")
    version = _safe_id(version, "event-package/version")
    data_root = confined_path(
        project.root_dir,
        project.manifest.directories["data"],
        "project/directories/data",
    )
    root = confined_path(
        data_root,
        f"events/{package_id}/{version}",
        "event-package/snapshot",
    )
    if root.is_symlink() or not root.is_dir():
        _fail(root, "event-snapshot.missing", "Unknown event snapshot")
    try:
        snapshot = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(root, "event-snapshot.read", f"Cannot read event snapshot: {error}")
    required = {
        "schemaVersion", "kind", "id", "version", "adapterKind", "eventCount",
        "availableStart", "availableEnd", "sourcePackageHash", "eventsPath",
        "eventsHash", "contentHashes", "snapshotHash",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != required:
        _fail(root, "event-snapshot.schema", "Event snapshot fields differ from V1")
    payload = {key: snapshot[key] for key in required - {"snapshotHash"}}
    if (
        snapshot["schemaVersion"] != 1
        or snapshot["kind"] != EVENT_SNAPSHOT_KIND
        or snapshot["id"] != package_id
        or snapshot["version"] != version
        or snapshot["adapterKind"] not in EVENT_ADAPTER_KINDS
        or snapshot["eventsPath"] != "events.jsonl"
        or snapshot["snapshotHash"] != hash_json(payload)
        or snapshot["eventsHash"] != hash_file(root / "events.jsonl")
    ):
        _fail(root, "event-snapshot.tampered", "Event snapshot integrity check failed")
    return snapshot


def list_event_snapshots(project: ProjectContext) -> list[dict[str, Any]]:
    """Verify and list every Project event snapshot."""

    data_root = confined_path(
        project.root_dir,
        project.manifest.directories["data"],
        "project/directories/data",
    )
    root = confined_path(data_root, "events", "event-package/root")
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        _fail(root, "event-snapshot.root", "Event snapshot root must be a directory")
    snapshots: list[dict[str, Any]] = []
    for package_dir in sorted(root.iterdir(), key=lambda item: item.name):
        if package_dir.is_symlink() or not package_dir.is_dir() or not SAFE_EVENT_ID.fullmatch(package_dir.name):
            _fail(package_dir, "event-snapshot.entry", "Invalid event package directory")
        for version_dir in sorted(package_dir.iterdir(), key=lambda item: item.name):
            if version_dir.is_symlink() or not version_dir.is_dir() or not SAFE_EVENT_ID.fullmatch(version_dir.name):
                _fail(version_dir, "event-snapshot.entry", "Invalid event version directory")
            snapshots.append(load_event_snapshot(project, package_dir.name, version_dir.name))
    return snapshots
