"""Audit one staged AutoQuant OHLCV package without mutating its bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")
SAFE_VERSIONS = {1, 2, 3, 4, 5}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def confined(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ValueError(f"asset path is not a confined POSIX descendant: {relative}")
    path = root.joinpath(*pure.parts)
    if path.is_symlink():
        raise ValueError(f"asset path cannot be a symlink: {path}")
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved_root not in resolved.parents:
        raise ValueError(f"asset path escapes manifest root: {relative}")
    if not resolved.is_file():
        raise ValueError(f"asset file is unavailable: {resolved}")
    return resolved


def load_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix == ".parquet":
        frame = pd.read_parquet(path)
    elif suffix == ".feather":
        frame = pd.read_feather(path)
    else:
        raise ValueError(f"unsupported asset format: {path}")
    frame = frame.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    if "date" not in frame:
        for alias in ("timestamp", "datetime", "time"):
            if alias in frame:
                frame = frame.rename(columns={alias: "date"})
                break
    missing = [column for column in REQUIRED_COLUMNS if column not in frame]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    frame = frame.loc[:, REQUIRED_COLUMNS]
    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
    for column in REQUIRED_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame.empty or frame.isna().any().any():
        raise ValueError(f"{path}: empty, null, or unparsable OHLCV")
    if not frame["date"].is_monotonic_increasing:
        raise ValueError(f"{path}: timestamps are not increasing")
    if frame["date"].duplicated().any():
        raise ValueError(f"{path}: duplicate timestamps")
    if (frame["volume"] < 0).any():
        raise ValueError(f"{path}: negative volume")
    bad_bounds = (
        frame["high"].lt(frame[["open", "low", "close"]].max(axis=1))
        | frame["low"].gt(frame[["open", "high", "close"]].min(axis=1))
    )
    if bad_bounds.any():
        raise ValueError(f"{path}: inconsistent OHLC bounds")
    return frame


def audit(package_path: Path) -> dict[str, Any]:
    if package_path.is_symlink() or not package_path.is_file():
        raise ValueError(f"package must be a real JSON file: {package_path}")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    if not isinstance(package, dict):
        raise ValueError("package root must be an object")
    if package.get("kind") != "autoquant-ohlcv-dataset-package":
        raise ValueError("unexpected package kind")
    version = package.get("schemaVersion")
    if version not in SAFE_VERSIONS:
        raise ValueError(f"unsupported schemaVersion: {version!r}")
    provider = package.get("provider")
    if not isinstance(provider, dict):
        raise ValueError("provider must be an object")
    if set(provider) != {"name", "retrievedAt", "sourceUri", "terms"}:
        raise ValueError("provider must contain the exact AutoQuant claim fields")
    assets = package.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("assets must be a non-empty array")

    root = package_path.parent
    summaries: dict[str, Any] = {}
    timestamp_sets: list[set[int]] = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("asset entries must be objects")
        symbol = asset.get("symbol")
        relative = asset.get("path")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("asset symbol must be a non-empty string")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"{symbol}: asset path must be a non-empty string")
        path = confined(root, relative)
        frame = load_frame(path)
        timestamps = set(frame["date"].astype("int64"))
        timestamp_sets.append(timestamps)
        spacing = frame["date"].diff().dropna().dt.total_seconds()
        summaries[symbol] = {
            "path": relative,
            "sha256": sha256(path),
            "rows": len(frame),
            "firstTimestamp": frame["date"].iloc[0].isoformat(),
            "lastTimestamp": frame["date"].iloc[-1].isoformat(),
            "zeroVolumeRows": int(frame["volume"].eq(0).sum()),
            "minimumSpacingSeconds": (
                float(spacing.min()) if not spacing.empty else None
            ),
            "maximumSpacingSeconds": (
                float(spacing.max()) if not spacing.empty else None
            ),
        }
    if len(summaries) != len(assets):
        raise ValueError("asset symbols must be unique")
    union = set.union(*timestamp_sets)
    intersection = set.intersection(*timestamp_sets)
    return {
        "schemaVersion": 1,
        "kind": "autoquant-ohlcv-package-audit",
        "package": str(package_path),
        "packageSha256": sha256(package_path),
        "datasetId": package.get("id"),
        "datasetSchemaVersion": version,
        "priceAdjustment": package.get("priceAdjustment"),
        "provider": provider,
        "assets": summaries,
        "panel": {
            "unionTimestamps": len(union),
            "intersectionTimestamps": len(intersection),
            "fullyAligned": len(union) == len(intersection),
        },
        "limitations": [
            "This audit checks files and basic OHLCV invariants, not provider truth.",
            "Strict aq project intake or atomic aq study create intake remains required.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--write-audit", type=Path)
    args = parser.parse_args()
    result = audit(args.package.expanduser().absolute())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write_audit:
        output = args.write_audit.expanduser().absolute()
        if output.exists() or output.is_symlink():
            parser.error(f"--write-audit target already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
