"""Request-driven, content-locked OHLCV Project intake."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np
import pandas as pd

from .briefs import load_research_request, validate_research_request
from .ohlcv import normalize_ohlcv
from .horizons import (
    RESEARCH_HORIZON,
    build_research_horizon,
    load_research_horizon,
    normalize_horizon_policy,
    validate_horizon_capacity,
)
from .intervals import (
    AGGREGATION_METHOD,
    BASE_INTERVAL,
    CONTINUOUS_AGGREGATION_METHOD,
    CONTINUOUS_TERMINAL_POLICY,
    IntervalContractError,
    SESSION_TERMINAL_POLICY,
    SUPPORTED_BASE_INTERVALS,
    SUPPORTED_FEATURE_INTERVALS,
    SUPPORTED_INTERVALS,
    XNYS_AGGREGATION_METHOD,
    aggregate_interval_ohlcv,
    aggregate_completed_ohlcv,
    annualization_periods as infer_annualization_periods,
    canonical_interval_surface,
    configurable_interval_surface,
    interval_surface,
    load_multi_interval_asset,
    normalize_feature_intervals,
    validate_base_ohlcv,
    validate_continuous_hourly_ohlcv,
)
from .mandates import (
    PORTFOLIO_MANDATE,
    build_portfolio_mandate,
    load_portfolio_mandate,
)
from .studies import StudyContext, hash_file, hash_json, load_study
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


DATASET_PACKAGE_KIND = "autoquant-ohlcv-dataset-package"
DATASET_SNAPSHOT_KIND = "autoquant-ohlcv-dataset-snapshot"
PROJECT_INTAKE_KIND = "autoquant-project-intake"
PROJECT_REQUEST = "request.json"
PROJECT_INTAKE = "intake.json"
DATASET_SNAPSHOT = "data/ohlcv/snapshot.json"
SAFE_SYMBOL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SUPPORTED_SOURCE_SUFFIXES = {".csv", ".parquet", ".feather"}
PRICE_ADJUSTMENTS = {
    "raw",
    "split-adjusted",
    "split-and-dividend-adjusted",
    "provider-adjusted",
}
INTAKE_TEMPLATE_REQUIREMENTS = {
    "ohlcv-factor-lab": (4, 180),
    "ohlcv-portfolio-lab": (5, 180),
    "ohlcv-rl-factor-lab": (5, 240),
    "ohlcv-research-desk": (5, 240),
}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _strict_keys(
    value: dict[str, Any],
    required: set[str],
    path: Path | str,
) -> list[ValidationIssue]:
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - value.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(value.keys() - required)
    )
    return issues


def _non_empty(value: Any, path: Path | str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.strip():
        return [_issue(path, "schema.string", "Must be a non-empty string")]
    return []


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.missing", f"Missing {label}: {path}")]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    f"{label}.json",
                    f"Invalid JSON at line {error.lineno}, column "
                    f"{error.colno}: {error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, f"{label}.type", f"{label} must be a JSON object")]
        )
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _read_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    try:
        if suffix == ".parquet":
            return pd.read_parquet(path)
        if suffix == ".feather":
            return pd.read_feather(path)
    except ImportError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "dataset.columnar-runtime",
                    "Parquet and Feather intake require the optional "
                    "'columnar' dependency; run `uv sync --extra columnar` "
                    "or supply CSV",
                )
            ]
        ) from error
    raise AutoQuantValidationError(
        [
            _issue(
                path,
                "dataset.format",
                "OHLCV source must be CSV, Parquet, or Feather",
            )
        ]
    )


def _canonical_frame(path: Path, *, market_clock: str) -> pd.DataFrame:
    try:
        frame = normalize_ohlcv(_read_source(path), source=str(path))
    except (ValueError, TypeError) as error:
        raise AutoQuantValidationError(
            [_issue(path, "dataset.ohlcv", str(error))]
        ) from error
    numeric = frame[["open", "high", "low", "close", "volume"]].to_numpy(
        dtype=float
    )
    if not np.isfinite(numeric).all() or (numeric <= 0).any():
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "dataset.non-positive",
                    "Daily OHLCV values must be finite and strictly positive",
                )
            ]
        )
    timestamps = pd.DatetimeIndex(frame["date"])
    if market_clock == "session" and (timestamps.weekday >= 5).any():
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "dataset.weekend",
                    "Session dataset cannot contain weekend rows",
                )
            ]
        )
    dates = pd.Index(timestamps.date, dtype="object")
    if dates.duplicated().any():
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "dataset.daily-duplicate",
                    "Daily source contains more than one row for a session date",
                )
            ]
        )
    result = frame[["open", "high", "low", "close", "volume"]].copy()
    result.insert(0, "timestamp", [value.isoformat() for value in dates])
    return result.reset_index(drop=True)


@dataclass(frozen=True)
class PreparedAsset:
    symbol: str
    venue: str
    currency: str
    source_relative_path: str
    source_path: Path
    source_hash: str
    frame: pd.DataFrame
    interval_frames: dict[str, pd.DataFrame] | None = None


@dataclass(frozen=True)
class PreparedIntake:
    template: str
    request: dict[str, Any]
    request_hash: str
    package: dict[str, Any]
    package_path: Path
    assets: tuple[PreparedAsset, ...]
    start: str
    end: str

    @property
    def universe(self) -> list[str]:
        return [asset.symbol for asset in self.assets]

    @property
    def multi_interval(self) -> bool:
        return self.package["schemaVersion"] in {2, 3}

    @property
    def interval_surface(self) -> dict[str, Any] | None:
        if not self.multi_interval:
            return None
        if self.package["schemaVersion"] == 2:
            return interval_surface(
                self.package["featureIntervals"]
            ).to_dict()
        return configurable_interval_surface(
            self.package["baseInterval"],
            self.package["featureIntervals"],
            self.package["market"],
        ).to_dict()

    @property
    def annualization_periods(self) -> int:
        if not self.multi_interval:
            return 252
        return infer_annualization_periods(self.assets[0].frame["timestamp"])


def _validate_v1_package_manifest(
    value: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "frequency",
        "market",
        "priceAdjustment",
        "provider",
        "assets",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(
            _issue(f"{path}/schemaVersion", "schema.version", "Expected V1")
        )
    if value.get("kind") != DATASET_PACKAGE_KIND:
        issues.append(
            _issue(
                f"{path}/kind",
                "dataset.kind",
                f"Expected {DATASET_PACKAGE_KIND}",
            )
        )
    for key in ("id", "version", "assetClass"):
        issues.extend(_non_empty(value.get(key), f"{path}/{key}"))
    if value.get("frequency") != "1d":
        issues.append(
            _issue(
                f"{path}/frequency",
                "dataset.frequency",
                "V1 intake supports frequency '1d' only",
            )
        )
    if value.get("priceAdjustment") not in PRICE_ADJUSTMENTS:
        issues.append(
            _issue(
                f"{path}/priceAdjustment",
                "dataset.adjustment",
                "Unsupported priceAdjustment",
            )
        )

    market = value.get("market")
    if not isinstance(market, dict):
        issues.append(
            _issue(f"{path}/market", "schema.type", "Market must be an object")
        )
        market = {}
    else:
        issues.extend(
            _strict_keys(
                market,
                {"clock", "calendar", "timezone"},
                f"{path}/market",
            )
        )
    if market.get("clock") != "session":
        issues.append(
            _issue(
                f"{path}/market/clock",
                "dataset.market-clock",
                "V1 intake supports session markets only",
            )
        )
    for key in ("calendar", "timezone"):
        issues.extend(_non_empty(market.get(key), f"{path}/market/{key}"))
    if isinstance(market.get("timezone"), str):
        try:
            ZoneInfo(market["timezone"])
        except (ValueError, ZoneInfoNotFoundError):
            issues.append(
                _issue(
                    f"{path}/market/timezone",
                    "dataset.timezone",
                    "Timezone must be an IANA timezone name",
                )
            )

    provider = value.get("provider")
    if not isinstance(provider, dict):
        issues.append(
            _issue(
                f"{path}/provider",
                "schema.type",
                "Provider must be an object",
            )
        )
        provider = {}
    else:
        issues.extend(
            _strict_keys(
                provider,
                {"name", "retrievedAt", "sourceUri", "terms"},
                f"{path}/provider",
            )
        )
    for key in ("name", "retrievedAt", "terms"):
        issues.extend(_non_empty(provider.get(key), f"{path}/provider/{key}"))
    if isinstance(provider.get("retrievedAt"), str):
        try:
            retrieved_at = datetime.fromisoformat(
                provider["retrievedAt"].replace("Z", "+00:00")
            )
            if retrieved_at.tzinfo is None:
                raise ValueError("timezone required")
        except ValueError:
            issues.append(
                _issue(
                    f"{path}/provider/retrievedAt",
                    "dataset.retrieved-at",
                    "retrievedAt must be a timezone-aware ISO-8601 timestamp",
                )
            )
    source_uri = provider.get("sourceUri")
    if source_uri is not None:
        issues.extend(_non_empty(source_uri, f"{path}/provider/sourceUri"))

    assets = value.get("assets")
    if not isinstance(assets, list) or not assets:
        issues.append(
            _issue(
                f"{path}/assets",
                "schema.array",
                "Assets must be a non-empty array",
            )
        )
        assets = []
    symbols: list[str] = []
    source_paths: list[str] = []
    for index, asset in enumerate(assets):
        asset_path = f"{path}/assets/{index}"
        if not isinstance(asset, dict):
            issues.append(
                _issue(asset_path, "schema.type", "Asset must be an object")
            )
            continue
        issues.extend(
            _strict_keys(
                asset,
                {"symbol", "venue", "currency", "path"},
                asset_path,
            )
        )
        for key in ("symbol", "venue", "currency", "path"):
            issues.extend(_non_empty(asset.get(key), f"{asset_path}/{key}"))
        symbol = asset.get("symbol")
        if isinstance(symbol, str) and not SAFE_SYMBOL.fullmatch(symbol):
            issues.append(
                _issue(
                    f"{asset_path}/symbol",
                    "dataset.symbol",
                    "Symbol must be a path-safe 1-64 character identifier",
                )
            )
        relative = asset.get("path")
        if isinstance(relative, str):
            try:
                confined_path(path.parent, relative, f"{asset_path}/path")
            except AutoQuantValidationError as error:
                issues.extend(error.issues)
            if Path(relative).suffix.lower() not in SUPPORTED_SOURCE_SUFFIXES:
                issues.append(
                    _issue(
                        f"{asset_path}/path",
                        "dataset.format",
                        "Asset path must end in .csv, .parquet, or .feather",
                    )
                )
        if isinstance(symbol, str):
            symbols.append(symbol)
        if isinstance(relative, str):
            source_paths.append(relative)
    if len(symbols) != len(set(symbols)):
        issues.append(
            _issue(f"{path}/assets", "dataset.duplicate-symbol", "Symbols must be unique")
        )
    if len(source_paths) != len(set(source_paths)):
        issues.append(
            _issue(
                f"{path}/assets",
                "dataset.duplicate-path",
                "Asset source paths must be unique",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return {
        **value,
        "id": value["id"].strip(),
        "version": value["version"].strip(),
        "assetClass": value["assetClass"].strip(),
        "market": {
            "clock": market["clock"],
            "calendar": market["calendar"].strip(),
            "timezone": market["timezone"].strip(),
        },
        "provider": {
            "name": provider["name"].strip(),
            "retrievedAt": provider["retrievedAt"].strip(),
            "sourceUri": (
                provider["sourceUri"].strip()
                if isinstance(provider["sourceUri"], str)
                else None
            ),
            "terms": provider["terms"].strip(),
        },
        "assets": [
            {
                key: asset[key].strip()
                for key in ("symbol", "venue", "currency", "path")
            }
            for asset in assets
        ],
    }


def _validate_v2_package_manifest(
    value: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "baseInterval",
        "featureIntervals",
        "timestampSemantics",
        "aggregation",
        "market",
        "priceAdjustment",
        "provider",
        "assets",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != 2:
        issues.append(_issue(path, "schema.version", "Expected V2 dataset package"))
    if value.get("kind") != DATASET_PACKAGE_KIND:
        issues.append(
            _issue(
                f"{path}/kind",
                "dataset.kind",
                f"Expected {DATASET_PACKAGE_KIND}",
            )
        )
    for key in ("id", "version", "assetClass"):
        issues.extend(_non_empty(value.get(key), f"{path}/{key}"))
    if value.get("baseInterval") != BASE_INTERVAL:
        issues.append(
            _issue(
                f"{path}/baseInterval",
                "dataset.base-interval",
                "V2 intake currently requires baseInterval '1h'",
            )
        )
    try:
        feature_intervals = normalize_feature_intervals(
            value.get("featureIntervals", [])
        )
        if not feature_intervals:
            raise IntervalContractError(
                "interval.empty",
                "featureIntervals must contain at least one higher interval",
            )
    except IntervalContractError as error:
        issues.append(
            _issue(
                f"{path}/featureIntervals",
                error.code,
                str(error),
            )
        )
        feature_intervals = ()
    if value.get("timestampSemantics") != "bar-close":
        issues.append(
            _issue(
                f"{path}/timestampSemantics",
                "dataset.timestamp-semantics",
                "V2 timestamps must mean bar-close",
            )
        )
    aggregation = value.get("aggregation")
    if not isinstance(aggregation, dict):
        issues.append(
            _issue(
                f"{path}/aggregation",
                "schema.type",
                "aggregation must be an object",
            )
        )
        aggregation = {}
    else:
        issues.extend(
            _strict_keys(
                aggregation,
                {"method", "anchor"},
                f"{path}/aggregation",
            )
        )
    if aggregation.get("method") != AGGREGATION_METHOD:
        issues.append(
            _issue(
                f"{path}/aggregation/method",
                "dataset.aggregation",
                f"V2 aggregation method must be {AGGREGATION_METHOD}",
            )
        )
    if aggregation.get("anchor") != "00:00":
        issues.append(
            _issue(
                f"{path}/aggregation/anchor",
                "dataset.anchor",
                "V2 continuous aggregation anchor must be UTC 00:00",
            )
        )
    market = value.get("market")
    if not isinstance(market, dict):
        issues.append(_issue(f"{path}/market", "schema.type", "Market must be an object"))
        market = {}
    else:
        issues.extend(
            _strict_keys(
                market,
                {"clock", "calendar", "timezone"},
                f"{path}/market",
            )
        )
    expected_market = {
        "clock": "continuous",
        "calendar": "24/7",
        "timezone": "UTC",
    }
    if market != expected_market:
        issues.append(
            _issue(
                f"{path}/market",
                "dataset.market-clock",
                "V2 currently requires continuous 24/7 UTC market authority",
            )
        )
    if value.get("priceAdjustment") not in PRICE_ADJUSTMENTS:
        issues.append(
            _issue(
                f"{path}/priceAdjustment",
                "dataset.adjustment",
                "Unsupported priceAdjustment",
            )
        )

    provider = value.get("provider")
    if not isinstance(provider, dict):
        issues.append(_issue(f"{path}/provider", "schema.type", "Provider must be an object"))
        provider = {}
    else:
        issues.extend(
            _strict_keys(
                provider,
                {"name", "retrievedAt", "sourceUri", "terms"},
                f"{path}/provider",
            )
        )
    for key in ("name", "retrievedAt", "terms"):
        issues.extend(_non_empty(provider.get(key), f"{path}/provider/{key}"))
    if isinstance(provider.get("retrievedAt"), str):
        try:
            retrieved_at = datetime.fromisoformat(
                provider["retrievedAt"].replace("Z", "+00:00")
            )
            if retrieved_at.tzinfo is None:
                raise ValueError("timezone required")
        except ValueError:
            issues.append(
                _issue(
                    f"{path}/provider/retrievedAt",
                    "dataset.retrieved-at",
                    "retrievedAt must be timezone-aware ISO-8601",
                )
            )
    source_uri = provider.get("sourceUri")
    if source_uri is not None:
        issues.extend(_non_empty(source_uri, f"{path}/provider/sourceUri"))

    assets = value.get("assets")
    if not isinstance(assets, list) or not assets:
        issues.append(_issue(f"{path}/assets", "schema.array", "Assets must be non-empty"))
        assets = []
    symbols: list[str] = []
    source_paths: list[str] = []
    for index, asset in enumerate(assets):
        asset_path = f"{path}/assets/{index}"
        if not isinstance(asset, dict):
            issues.append(_issue(asset_path, "schema.type", "Asset must be an object"))
            continue
        issues.extend(
            _strict_keys(
                asset,
                {"symbol", "venue", "currency", "path"},
                asset_path,
            )
        )
        for key in ("symbol", "venue", "currency", "path"):
            issues.extend(_non_empty(asset.get(key), f"{asset_path}/{key}"))
        symbol = asset.get("symbol")
        relative = asset.get("path")
        if isinstance(symbol, str):
            if not SAFE_SYMBOL.fullmatch(symbol):
                issues.append(
                    _issue(f"{asset_path}/symbol", "dataset.symbol", "Invalid symbol")
                )
            symbols.append(symbol)
        if isinstance(relative, str):
            try:
                confined_path(path.parent, relative, f"{asset_path}/path")
            except AutoQuantValidationError as error:
                issues.extend(error.issues)
            if Path(relative).suffix.lower() not in SUPPORTED_SOURCE_SUFFIXES:
                issues.append(
                    _issue(
                        f"{asset_path}/path",
                        "dataset.format",
                        "Asset path must end in .csv, .parquet, or .feather",
                    )
                )
            source_paths.append(relative)
    if len(symbols) != len(set(symbols)):
        issues.append(_issue(f"{path}/assets", "dataset.duplicate-symbol", "Symbols must be unique"))
    if len(source_paths) != len(set(source_paths)):
        issues.append(_issue(f"{path}/assets", "dataset.duplicate-path", "Paths must be unique"))
    if issues:
        raise AutoQuantValidationError(issues)
    return {
        **value,
        "id": value["id"].strip(),
        "version": value["version"].strip(),
        "assetClass": value["assetClass"].strip(),
        "featureIntervals": list(feature_intervals),
        "aggregation": {
            "method": aggregation["method"],
            "anchor": aggregation["anchor"],
        },
        "market": expected_market,
        "provider": {
            "name": provider["name"].strip(),
            "retrievedAt": provider["retrievedAt"].strip(),
            "sourceUri": (
                provider["sourceUri"].strip()
                if isinstance(provider["sourceUri"], str)
                else None
            ),
            "terms": provider["terms"].strip(),
        },
        "assets": [
            {
                key: asset[key].strip()
                for key in ("symbol", "venue", "currency", "path")
            }
            for asset in assets
        ],
    }


def _validate_v3_package_manifest(
    value: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "baseInterval",
        "featureIntervals",
        "timestampSemantics",
        "aggregation",
        "market",
        "priceAdjustment",
        "provider",
        "assets",
    }
    issues = _strict_keys(value, required, path)
    if value.get("schemaVersion") != 3:
        issues.append(_issue(path, "schema.version", "Expected V3 dataset package"))
    if value.get("kind") != DATASET_PACKAGE_KIND:
        issues.append(
            _issue(
                f"{path}/kind",
                "dataset.kind",
                f"Expected {DATASET_PACKAGE_KIND}",
            )
        )
    market = value.get("market")
    if not isinstance(market, dict):
        issues.append(
            _issue(f"{path}/market", "schema.type", "Market must be an object")
        )
        market = {}
    else:
        issues.extend(
            _strict_keys(
                market,
                {"clock", "calendar", "timezone"},
                f"{path}/market",
            )
        )
    try:
        surface = configurable_interval_surface(
            value.get("baseInterval"),
            value.get("featureIntervals", []),
            market,
        ).to_dict()
    except IntervalContractError as error:
        issues.append(
            _issue(f"{path}/featureIntervals", error.code, str(error))
        )
        surface = None
    if value.get("timestampSemantics") != "bar-close":
        issues.append(
            _issue(
                f"{path}/timestampSemantics",
                "dataset.timestamp-semantics",
                "V3 timestamps must mean bar-close",
            )
        )
    aggregation = value.get("aggregation")
    if not isinstance(aggregation, dict):
        issues.append(
            _issue(
                f"{path}/aggregation",
                "schema.type",
                "aggregation must be an object",
            )
        )
        aggregation = {}
    else:
        issues.extend(
            _strict_keys(
                aggregation,
                {"method", "anchor", "terminalBucketPolicy"},
                f"{path}/aggregation",
            )
        )
    if surface is not None:
        expected_aggregation = {
            "method": surface["aggregationMethod"],
            "anchor": surface["anchor"],
            "terminalBucketPolicy": surface["terminalBucketPolicy"],
        }
        if aggregation != expected_aggregation:
            issues.append(
                _issue(
                    f"{path}/aggregation",
                    "dataset.aggregation",
                    "V3 aggregation must match its canonical interval surface",
                )
            )
    common_projection = {
        **{
            key: value.get(key)
            for key in (
                "kind",
                "id",
                "version",
                "assetClass",
                "priceAdjustment",
                "provider",
                "assets",
            )
        },
        "schemaVersion": 2,
        "baseInterval": BASE_INTERVAL,
        "featureIntervals": ["3h"],
        "timestampSemantics": "bar-close",
        "aggregation": {
            "method": AGGREGATION_METHOD,
            "anchor": "00:00",
        },
        "market": {
            "clock": "continuous",
            "calendar": "24/7",
            "timezone": "UTC",
        },
    }
    normalized_common = None
    try:
        normalized_common = _validate_v2_package_manifest(
            common_projection,
            path,
        )
    except AutoQuantValidationError as error:
        issues.extend(error.issues)
    if issues:
        raise AutoQuantValidationError(issues)
    assert normalized_common is not None and surface is not None
    return {
        **value,
        "id": normalized_common["id"],
        "version": normalized_common["version"],
        "assetClass": normalized_common["assetClass"],
        "baseInterval": surface["baseInterval"],
        "featureIntervals": surface["featureIntervals"],
        "aggregation": {
            "method": surface["aggregationMethod"],
            "anchor": surface["anchor"],
            "terminalBucketPolicy": surface["terminalBucketPolicy"],
        },
        "market": {
            "clock": surface["marketClock"],
            "calendar": surface["calendar"],
            "timezone": surface["timezone"],
        },
        "provider": normalized_common["provider"],
        "assets": normalized_common["assets"],
    }


def _validate_package_manifest(
    value: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    if value.get("schemaVersion") == 3:
        return _validate_v3_package_manifest(value, path)
    if value.get("schemaVersion") == 2:
        return _validate_v2_package_manifest(value, path)
    return _validate_v1_package_manifest(value, path)


def prepare_project_intake(
    request_path: str | Path,
    package_path: str | Path,
    template: str,
) -> PreparedIntake:
    """Validate external request/data before a Project staging directory exists."""

    if template not in INTAKE_TEMPLATE_REQUIREMENTS:
        raise AutoQuantValidationError(
            [
                _issue(
                    template,
                    "intake.template",
                    "Intake template must be one of: "
                    + ", ".join(INTAKE_TEMPLATE_REQUIREMENTS),
                )
            ]
        )
    request = load_research_request(request_path)
    manifest_path = Path(package_path).expanduser().absolute()
    if manifest_path.is_symlink():
        raise AutoQuantValidationError(
            [_issue(manifest_path, "path.symlink", "Dataset manifest cannot be a symlink")]
        )
    manifest_path = manifest_path.resolve()
    package = _validate_package_manifest(
        _read_json(manifest_path, "dataset package"),
        manifest_path,
    )
    prepared: list[PreparedAsset] = []
    issues: list[ValidationIssue] = []
    expected_dates: list[Any] | None = None
    package_surface = (
        configurable_interval_surface(
            package["baseInterval"],
            package["featureIntervals"],
            package["market"],
        ).to_dict()
        if package["schemaVersion"] == 3
        else None
    )
    portfolio_policy = request.get("portfolioPolicy")
    if (
        isinstance(portfolio_policy, dict)
        and portfolio_policy.get("decisionAnchor") == "session-start"
        and (
            package["schemaVersion"] != 3
            or not isinstance(package_surface, dict)
            or package_surface.get("marketClock") != "session"
            or package_surface.get("calendar") != "XNYS"
            or package_surface.get("baseInterval") == "1d"
        )
    ):
        issues.append(
            _issue(
                "request/portfolioPolicy/decisionAnchor",
                "request.dataset-decision-anchor",
                "session-start requires a V3 intraday XNYS "
                "regular-session package",
            )
        )
    for index, asset in enumerate(package["assets"]):
        source = confined_path(
            manifest_path.parent,
            asset["path"],
            f"{manifest_path}/assets/{index}/path",
        )
        if not source.is_file():
            issues.append(
                _issue(source, "dataset.source-missing", f"Missing asset source: {source}")
            )
            continue
        interval_frames = None
        if package["schemaVersion"] in {2, 3}:
            try:
                frame = (
                    validate_continuous_hourly_ohlcv(
                        _read_source(source),
                        label=asset["symbol"],
                    )
                    if package["schemaVersion"] == 2
                    else validate_base_ohlcv(
                        _read_source(source),
                        package_surface,
                        label=asset["symbol"],
                    )
                )
                interval_frames = {
                    package["baseInterval"]: frame,
                    **{
                        interval: (
                            aggregate_completed_ohlcv(frame, interval)
                            if package["schemaVersion"] == 2
                            else aggregate_interval_ohlcv(
                                frame,
                                package_surface,
                                interval,
                            )
                        )
                        for interval in package["featureIntervals"]
                    },
                }
            except IntervalContractError as error:
                issues.append(_issue(source, error.code, str(error)))
                continue
        else:
            frame = _canonical_frame(
                source,
                market_clock=package["market"]["clock"],
            )
        dates = frame["timestamp"].tolist()
        if expected_dates is None:
            expected_dates = dates
        elif dates != expected_dates:
            panel = (
                "exact base timestamp panel"
                if package["schemaVersion"] in {2, 3}
                else "exact daily timestamp panel"
            )
            issues.append(
                _issue(
                    source,
                    "dataset.panel-misaligned",
                    f"Every asset must share the {panel}",
                )
            )
        prepared.append(
            PreparedAsset(
                symbol=asset["symbol"],
                venue=asset["venue"],
                currency=asset["currency"],
                source_relative_path=asset["path"],
                source_path=source,
                source_hash=hash_file(source),
                frame=frame,
                interval_frames=interval_frames,
            )
        )
    minimum_assets, minimum_observations = INTAKE_TEMPLATE_REQUIREMENTS[template]
    if len(prepared) < minimum_assets:
        issues.append(
            _issue(
                manifest_path,
                "dataset.breadth",
                f"{template} requires at least {minimum_assets} aligned assets",
            )
        )
    observations = len(expected_dates or [])
    if observations < minimum_observations:
        unit = (
            f"base {package['baseInterval']}"
            if package["schemaVersion"] in {2, 3}
            else "daily"
        )
        issues.append(
            _issue(
                manifest_path,
                "dataset.observations",
                f"{template} requires at least {minimum_observations} {unit} rows",
            )
        )

    package_by_symbol = {asset.symbol: asset for asset in prepared}
    requested_classes = {item["assetClass"] for item in request["assets"]}
    if requested_classes != {package["assetClass"]}:
        issues.append(
            _issue(
                "request/assets",
                "request.dataset-asset-class",
                "Every requested asset class must equal dataset assetClass "
                f"'{package['assetClass']}'",
            )
        )
    for item in request["assets"]:
        source = package_by_symbol.get(item["symbol"])
        if source is None:
            issues.append(
                _issue(
                    "request/assets",
                    "request.dataset-universe",
                    f"Requested asset is absent from dataset: {item['symbol']}",
                )
            )
        elif item["venue"] is not None and item["venue"] != source.venue:
            issues.append(
                _issue(
                    "request/assets",
                    "request.dataset-venue",
                    f"Requested venue for {item['symbol']} differs from dataset",
                )
            )
    if expected_dates is not None:
        try:
            validate_horizon_capacity(
                normalize_horizon_policy(request.get("horizonPolicy")),
                len(expected_dates),
                "request/horizonPolicy",
            )
        except AutoQuantValidationError as error:
            issues.extend(error.issues)
    if issues:
        raise AutoQuantValidationError(issues)
    assert expected_dates is not None
    start = expected_dates[0]
    end = expected_dates[-1]
    if isinstance(start, pd.Timestamp):
        start = start.isoformat().replace("+00:00", "Z")
        end = end.isoformat().replace("+00:00", "Z")
    return PreparedIntake(
        template=template,
        request=request,
        request_hash=hash_json(request),
        package=package,
        package_path=manifest_path,
        assets=tuple(prepared),
        start=str(start),
        end=str(end),
    )


def materialize_intake_dataset(
    project: ProjectContext,
    intake: PreparedIntake,
    study_id: str,
) -> tuple[dict[str, Any], str]:
    """Write canonical Project-local OHLCV and its content snapshot."""

    output = project.root_dir / project.manifest.directories["data"] / "ohlcv"
    output.mkdir()
    asset_records: list[dict[str, Any]] = []
    for asset in intake.assets:
        common = {
            "symbol": asset.symbol,
            "venue": asset.venue,
            "currency": asset.currency,
            "sourcePath": asset.source_relative_path,
            "sourceHash": asset.source_hash,
            "start": intake.start,
            "end": intake.end,
        }
        if intake.multi_interval:
            assert asset.interval_frames is not None
            interval_records = []
            for interval, raw_frame in asset.interval_frames.items():
                target_directory = output / interval
                target_directory.mkdir(exist_ok=True)
                target = target_directory / f"{asset.symbol}.csv"
                frame = raw_frame.copy()
                frame["timestamp"] = frame["timestamp"].map(
                    lambda value: pd.Timestamp(value)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                frame.to_csv(
                    target,
                    index=False,
                    lineterminator="\n",
                    float_format="%.12g",
                )
                interval_records.append(
                    {
                        "interval": interval,
                        "normalizedPath": f"ohlcv/{interval}/{asset.symbol}.csv",
                        "normalizedHash": hash_file(target),
                        "observations": len(frame),
                        "start": (
                            str(frame["timestamp"].iloc[0])
                            if len(frame)
                            else None
                        ),
                        "end": (
                            str(frame["timestamp"].iloc[-1])
                            if len(frame)
                            else None
                        ),
                    }
                )
            asset_records.append({**common, "intervals": interval_records})
        else:
            target = output / f"{asset.symbol}.csv"
            asset.frame.to_csv(
                target,
                index=False,
                lineterminator="\n",
                float_format="%.12g",
            )
            asset_records.append(
                {
                    **common,
                    "normalizedPath": f"ohlcv/{asset.symbol}.csv",
                    "normalizedHash": hash_file(target),
                    "observations": len(asset.frame),
                }
            )
    snapshot = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": DATASET_SNAPSHOT_KIND,
        "id": intake.package["id"],
        "version": intake.package["version"],
        "assetClass": intake.package["assetClass"],
        "market": intake.package["market"],
        "priceAdjustment": intake.package["priceAdjustment"],
        "provider": intake.package["provider"],
        "packageManifestHash": hash_file(intake.package_path),
        "requestHash": intake.request_hash,
        "requestedAssets": [
            item["symbol"] for item in intake.request["assets"]
        ],
        "universe": intake.universe,
        "timeRange": {"start": intake.start, "end": intake.end},
        "template": intake.template,
        "studyId": study_id,
        "assets": asset_records,
    }
    if intake.multi_interval:
        snapshot["schemaVersion"] = intake.package["schemaVersion"]
        snapshot["intervalSurface"] = intake.interval_surface
    else:
        snapshot["frequency"] = intake.package["frequency"]
    snapshot_path = output / "snapshot.json"
    _write_json(snapshot_path, snapshot)
    interval_line = (
        "- Interval surface: `"
        + " / ".join(
            [
                intake.package["baseInterval"],
                *intake.package["featureIntervals"],
            ]
        )
        + "`\n"
        if intake.multi_interval
        else f"- Frequency: `{snapshot['frequency']}`\n"
    )
    readme = (
        "# Content-locked external OHLCV snapshot\n\n"
        f"- Dataset: `{snapshot['id']}@{snapshot['version']}`\n"
        f"- Provider claim: `{snapshot['provider']['name']}`\n"
        f"- Price adjustment claim: `{snapshot['priceAdjustment']}`\n"
        f"- Calendar claim: `{snapshot['market']['calendar']}`\n"
        f"{interval_line}"
        f"- Coverage: `{intake.start}` through `{intake.end}`\n"
        f"- Universe: {', '.join(intake.universe)}\n\n"
        "The fixed Study hashes every file in this directory. Provider, "
        "calendar, adjustment, venue, and terms values are caller-supplied "
        "claims, not authenticated by AutoQuant.\n"
    )
    (output / "README.md").write_text(readme, encoding="utf-8")
    _write_json(project.root_dir / PROJECT_REQUEST, intake.request)
    return snapshot, hash_file(snapshot_path)


def finalize_project_intake(
    project: ProjectContext,
    intake: PreparedIntake,
    study: StudyContext,
    snapshot_hash: str,
) -> dict[str, Any]:
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": PROJECT_INTAKE_KIND,
        "template": intake.template,
        "requestPath": PROJECT_REQUEST,
        "requestHash": intake.request_hash,
        "datasetSnapshotPath": DATASET_SNAPSHOT,
        "datasetSnapshotHash": snapshot_hash,
        "studyId": study.definition.id,
        "studyHash": study.study_hash,
        "studyInputHash": study.input_hash,
        "datasetHash": study.dataset_hash,
        "status": "ready-for-session",
    }
    _write_json(project.root_dir / PROJECT_INTAKE, manifest)
    return manifest


def _validate_v1_snapshot(
    snapshot: dict[str, Any],
    path: Path,
) -> list[ValidationIssue]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "frequency",
        "market",
        "priceAdjustment",
        "provider",
        "packageManifestHash",
        "requestHash",
        "requestedAssets",
        "universe",
        "timeRange",
        "template",
        "studyId",
        "assets",
    }
    issues = _strict_keys(snapshot, required, path)
    if (
        snapshot.get("schemaVersion") != SCHEMA_VERSION
        or snapshot.get("kind") != DATASET_SNAPSHOT_KIND
    ):
        issues.append(_issue(path, "intake.snapshot-schema", "Invalid dataset snapshot"))
    for key in ("id", "version", "assetClass", "template", "studyId"):
        issues.extend(_non_empty(snapshot.get(key), f"{path}/{key}"))
    if snapshot.get("frequency") != "1d":
        issues.append(
            _issue(
                f"{path}/frequency",
                "intake.snapshot-frequency",
                "Snapshot frequency must be '1d'",
            )
        )
    if snapshot.get("priceAdjustment") not in PRICE_ADJUSTMENTS:
        issues.append(
            _issue(
                f"{path}/priceAdjustment",
                "intake.snapshot-adjustment",
                "Snapshot priceAdjustment is unsupported",
            )
        )
    for key in ("packageManifestHash", "requestHash"):
        if not _valid_hash(snapshot.get(key)):
            issues.append(
                _issue(f"{path}/{key}", "schema.hash", f"Invalid {key}")
            )

    market = snapshot.get("market")
    if not isinstance(market, dict):
        issues.append(
            _issue(f"{path}/market", "schema.type", "Market must be an object")
        )
    else:
        issues.extend(
            _strict_keys(
                market,
                {"clock", "calendar", "timezone"},
                f"{path}/market",
            )
        )
        if market.get("clock") != "session":
            issues.append(
                _issue(
                    f"{path}/market/clock",
                    "intake.snapshot-market",
                    "Snapshot market clock must be 'session'",
                )
            )
        for key in ("calendar", "timezone"):
            issues.extend(_non_empty(market.get(key), f"{path}/market/{key}"))

    provider = snapshot.get("provider")
    if not isinstance(provider, dict):
        issues.append(
            _issue(f"{path}/provider", "schema.type", "Provider must be an object")
        )
    else:
        issues.extend(
            _strict_keys(
                provider,
                {"name", "retrievedAt", "sourceUri", "terms"},
                f"{path}/provider",
            )
        )
        for key in ("name", "retrievedAt", "terms"):
            issues.extend(_non_empty(provider.get(key), f"{path}/provider/{key}"))
        source_uri = provider.get("sourceUri")
        if source_uri is not None:
            issues.extend(_non_empty(source_uri, f"{path}/provider/sourceUri"))

    requested_assets = snapshot.get("requestedAssets")
    if (
        not isinstance(requested_assets, list)
        or not requested_assets
        or not all(isinstance(item, str) and item for item in requested_assets)
        or len(requested_assets) != len(set(requested_assets))
    ):
        issues.append(
            _issue(
                f"{path}/requestedAssets",
                "schema.array",
                "requestedAssets must be unique non-empty strings",
            )
        )
        requested_assets = []
    universe = snapshot.get("universe")
    if (
        not isinstance(universe, list)
        or not universe
        or not all(isinstance(item, str) and item for item in universe)
        or len(universe) != len(set(universe))
    ):
        issues.append(
            _issue(
                f"{path}/universe",
                "schema.array",
                "Universe must be unique non-empty strings",
            )
        )
        universe = []
    if not set(requested_assets).issubset(universe):
        issues.append(
            _issue(
                f"{path}/requestedAssets",
                "intake.snapshot-requested-assets",
                "Requested assets must be a subset of the research universe",
            )
        )

    time_range = snapshot.get("timeRange")
    if not isinstance(time_range, dict):
        issues.append(
            _issue(
                f"{path}/timeRange",
                "schema.type",
                "timeRange must be an object",
            )
        )
        time_range = {}
    else:
        issues.extend(
            _strict_keys(time_range, {"start", "end"}, f"{path}/timeRange")
        )
    for key in ("start", "end"):
        issues.extend(_non_empty(time_range.get(key), f"{path}/timeRange/{key}"))

    assets = snapshot.get("assets")
    if not isinstance(assets, list) or not assets:
        issues.append(
            _issue(f"{path}/assets", "schema.array", "Snapshot assets must be non-empty")
        )
        assets = []
    asset_symbols: list[str] = []
    for index, asset in enumerate(assets):
        asset_path = f"{path}/assets/{index}"
        if not isinstance(asset, dict):
            issues.append(_issue(asset_path, "schema.type", "Asset must be an object"))
            continue
        issues.extend(
            _strict_keys(
                asset,
                {
                    "symbol",
                    "venue",
                    "currency",
                    "sourcePath",
                    "sourceHash",
                    "normalizedPath",
                    "normalizedHash",
                    "observations",
                    "start",
                    "end",
                },
                asset_path,
            )
        )
        for key in (
            "symbol",
            "venue",
            "currency",
            "sourcePath",
            "normalizedPath",
            "start",
            "end",
        ):
            issues.extend(_non_empty(asset.get(key), f"{asset_path}/{key}"))
        for key in ("sourceHash", "normalizedHash"):
            if not _valid_hash(asset.get(key)):
                issues.append(
                    _issue(
                        f"{asset_path}/{key}",
                        "schema.hash",
                        f"Invalid {key}",
                    )
                )
        observations = asset.get("observations")
        if (
            not isinstance(observations, int)
            or isinstance(observations, bool)
            or observations < 1
        ):
            issues.append(
                _issue(
                    f"{asset_path}/observations",
                    "schema.integer",
                    "observations must be a positive integer",
                )
            )
        symbol = asset.get("symbol")
        if isinstance(symbol, str):
            asset_symbols.append(symbol)
        if (
            asset.get("start") != time_range.get("start")
            or asset.get("end") != time_range.get("end")
        ):
            issues.append(
                _issue(
                    asset_path,
                    "intake.snapshot-coverage",
                    "Every asset must match snapshot timeRange",
                )
            )
    if asset_symbols != universe:
        issues.append(
            _issue(
                f"{path}/assets",
                "intake.snapshot-universe",
                "Snapshot asset order must exactly match the research universe",
            )
        )
    return issues


def _validate_multi_interval_snapshot(
    snapshot: dict[str, Any],
    path: Path,
    *,
    schema_version: int,
) -> list[ValidationIssue]:
    required = {
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "intervalSurface",
        "market",
        "priceAdjustment",
        "provider",
        "packageManifestHash",
        "requestHash",
        "requestedAssets",
        "universe",
        "timeRange",
        "template",
        "studyId",
        "assets",
    }
    issues = _strict_keys(snapshot, required, path)
    if (
        snapshot.get("schemaVersion") != schema_version
        or snapshot.get("kind") != DATASET_SNAPSHOT_KIND
    ):
        issues.append(
            _issue(
                path,
                "intake.snapshot-schema",
                f"Invalid V{schema_version} dataset snapshot",
            )
        )
    for key in ("id", "version", "assetClass", "template", "studyId"):
        issues.extend(_non_empty(snapshot.get(key), f"{path}/{key}"))
    for key in ("packageManifestHash", "requestHash"):
        if not _valid_hash(snapshot.get(key)):
            issues.append(_issue(f"{path}/{key}", "schema.hash", f"Invalid {key}"))
    if snapshot.get("priceAdjustment") not in PRICE_ADJUSTMENTS:
        issues.append(
            _issue(
                f"{path}/priceAdjustment",
                "intake.snapshot-adjustment",
                "Snapshot priceAdjustment is unsupported",
            )
        )
    surface = snapshot.get("intervalSurface")
    if not isinstance(surface, dict):
        issues.append(
            _issue(
                f"{path}/intervalSurface",
                "schema.type",
                "intervalSurface must be an object",
            )
        )
        surface = {}
    else:
        surface_keys = {
            "baseInterval",
            "featureIntervals",
            "timestampSemantics",
            "marketClock",
            "timezone",
            "anchor",
            "aggregationMethod",
        }
        if schema_version == 3:
            surface_keys |= {"calendar", "terminalBucketPolicy"}
        issues.extend(
            _strict_keys(
                surface,
                surface_keys,
                f"{path}/intervalSurface",
            )
        )
    try:
        expected_surface = canonical_interval_surface(
            surface,
            schema_version=schema_version,
        )
        if surface != expected_surface:
            issues.append(
                _issue(
                    f"{path}/intervalSurface",
                    "intake.snapshot-interval-surface",
                    "Snapshot interval surface differs from fixed authority",
                )
            )
    except IntervalContractError as error:
        issues.append(
            _issue(f"{path}/intervalSurface", error.code, str(error))
        )
        expected_surface = (
            interval_surface([]).to_dict()
            if schema_version == 2
            else {
                "baseInterval": snapshot.get("baseInterval", BASE_INTERVAL),
                "featureIntervals": [],
            }
        )
    expected_intervals = [
        expected_surface["baseInterval"],
        *expected_surface["featureIntervals"],
    ]
    expected_market = (
        {
            "clock": "continuous",
            "calendar": "24/7",
            "timezone": "UTC",
        }
        if schema_version == 2
        else {
            "clock": expected_surface.get("marketClock"),
            "calendar": expected_surface.get("calendar"),
            "timezone": expected_surface.get("timezone"),
        }
    )
    if snapshot.get("market") != expected_market:
        issues.append(
            _issue(
                f"{path}/market",
                "intake.snapshot-market",
                f"V{schema_version} snapshot market differs from interval authority",
            )
        )
    provider = snapshot.get("provider")
    if not isinstance(provider, dict):
        issues.append(_issue(f"{path}/provider", "schema.type", "Provider must be an object"))
    else:
        issues.extend(
            _strict_keys(
                provider,
                {"name", "retrievedAt", "sourceUri", "terms"},
                f"{path}/provider",
            )
        )
        for key in ("name", "retrievedAt", "terms"):
            issues.extend(_non_empty(provider.get(key), f"{path}/provider/{key}"))

    requested_assets = snapshot.get("requestedAssets")
    universe = snapshot.get("universe")
    for key, value in (
        ("requestedAssets", requested_assets),
        ("universe", universe),
    ):
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item for item in value)
            or len(value) != len(set(value))
        ):
            issues.append(
                _issue(
                    f"{path}/{key}",
                    "schema.array",
                    f"{key} must contain unique non-empty strings",
                )
            )
    requested_assets = requested_assets if isinstance(requested_assets, list) else []
    universe = universe if isinstance(universe, list) else []
    if not set(requested_assets).issubset(universe):
        issues.append(
            _issue(
                f"{path}/requestedAssets",
                "intake.snapshot-requested-assets",
                "Requested assets must be a subset of the research universe",
            )
        )
    time_range = snapshot.get("timeRange")
    if not isinstance(time_range, dict):
        issues.append(_issue(f"{path}/timeRange", "schema.type", "timeRange must be an object"))
        time_range = {}
    else:
        issues.extend(_strict_keys(time_range, {"start", "end"}, f"{path}/timeRange"))
    for key in ("start", "end"):
        issues.extend(_non_empty(time_range.get(key), f"{path}/timeRange/{key}"))

    assets = snapshot.get("assets")
    if not isinstance(assets, list) or not assets:
        issues.append(_issue(f"{path}/assets", "schema.array", "Snapshot assets must be non-empty"))
        assets = []
    symbols: list[str] = []
    for asset_index, asset in enumerate(assets):
        asset_path = f"{path}/assets/{asset_index}"
        if not isinstance(asset, dict):
            issues.append(_issue(asset_path, "schema.type", "Asset must be an object"))
            continue
        issues.extend(
            _strict_keys(
                asset,
                {
                    "symbol",
                    "venue",
                    "currency",
                    "sourcePath",
                    "sourceHash",
                    "start",
                    "end",
                    "intervals",
                },
                asset_path,
            )
        )
        for key in ("symbol", "venue", "currency", "sourcePath", "start", "end"):
            issues.extend(_non_empty(asset.get(key), f"{asset_path}/{key}"))
        if not _valid_hash(asset.get("sourceHash")):
            issues.append(_issue(f"{asset_path}/sourceHash", "schema.hash", "Invalid sourceHash"))
        symbol = asset.get("symbol")
        if isinstance(symbol, str):
            symbols.append(symbol)
        if (
            asset.get("start") != time_range.get("start")
            or asset.get("end") != time_range.get("end")
        ):
            issues.append(
                _issue(
                    asset_path,
                    "intake.snapshot-coverage",
                    "Base asset coverage must match snapshot timeRange",
                )
            )
        rows = asset.get("intervals")
        if not isinstance(rows, list) or not rows:
            issues.append(
                _issue(f"{asset_path}/intervals", "schema.array", "Missing interval inventory")
            )
            rows = []
        observed_intervals: list[str] = []
        for row_index, row in enumerate(rows):
            row_path = f"{asset_path}/intervals/{row_index}"
            if not isinstance(row, dict):
                issues.append(_issue(row_path, "schema.type", "Interval row must be an object"))
                continue
            issues.extend(
                _strict_keys(
                    row,
                    {
                        "interval",
                        "normalizedPath",
                        "normalizedHash",
                        "observations",
                        "start",
                        "end",
                    },
                    row_path,
                )
            )
            for key in ("interval", "normalizedPath", "start", "end"):
                issues.extend(_non_empty(row.get(key), f"{row_path}/{key}"))
            if not _valid_hash(row.get("normalizedHash")):
                issues.append(
                    _issue(f"{row_path}/normalizedHash", "schema.hash", "Invalid normalizedHash")
                )
            observations = row.get("observations")
            if (
                not isinstance(observations, int)
                or isinstance(observations, bool)
                or observations < 1
            ):
                issues.append(
                    _issue(
                        f"{row_path}/observations",
                        "schema.integer",
                        "observations must be a positive integer",
                    )
                )
            observed_intervals.append(row.get("interval"))
            if (
                isinstance(symbol, str)
                and isinstance(row.get("interval"), str)
                and row.get("normalizedPath")
                != f"ohlcv/{row['interval']}/{symbol}.csv"
            ):
                issues.append(
                    _issue(
                        f"{row_path}/normalizedPath",
                        "intake.snapshot-interval-path",
                        "Interval path must match its canonical asset inventory",
                    )
                )
        if observed_intervals != expected_intervals:
            issues.append(
                _issue(
                    f"{asset_path}/intervals",
                    "intake.snapshot-interval-inventory",
                    "Asset interval inventory must match intervalSurface order",
                )
            )
    if symbols != universe:
        issues.append(
            _issue(
                f"{path}/assets",
                "intake.snapshot-universe",
                "Snapshot asset order must exactly match the research universe",
            )
        )
    return issues


def _validate_v2_snapshot(
    snapshot: dict[str, Any],
    path: Path,
) -> list[ValidationIssue]:
    return _validate_multi_interval_snapshot(
        snapshot,
        path,
        schema_version=2,
    )


def _validate_v3_snapshot(
    snapshot: dict[str, Any],
    path: Path,
) -> list[ValidationIssue]:
    return _validate_multi_interval_snapshot(
        snapshot,
        path,
        schema_version=3,
    )


def _validate_snapshot(
    snapshot: dict[str, Any],
    path: Path,
) -> list[ValidationIssue]:
    if snapshot.get("schemaVersion") == 3:
        return _validate_v3_snapshot(snapshot, path)
    if snapshot.get("schemaVersion") == 2:
        return _validate_v2_snapshot(snapshot, path)
    return _validate_v1_snapshot(snapshot, path)


def load_project_intake(project: ProjectContext) -> dict[str, Any] | None:
    """Verify and project optional request-driven Project intake state."""

    manifest_path = project.root_dir / PROJECT_INTAKE
    if not manifest_path.exists():
        return None
    manifest = _read_json(manifest_path, "project intake")
    required = {
        "schemaVersion",
        "kind",
        "template",
        "requestPath",
        "requestHash",
        "datasetSnapshotPath",
        "datasetSnapshotHash",
        "studyId",
        "studyHash",
        "studyInputHash",
        "datasetHash",
        "status",
    }
    issues = _strict_keys(manifest, required, manifest_path)
    if (
        manifest.get("schemaVersion") != SCHEMA_VERSION
        or manifest.get("kind") != PROJECT_INTAKE_KIND
        or manifest.get("status") != "ready-for-session"
    ):
        issues.append(_issue(manifest_path, "intake.schema", "Invalid Project intake"))
    for key in (
        "requestHash",
        "datasetSnapshotHash",
        "studyHash",
        "studyInputHash",
        "datasetHash",
    ):
        if not _valid_hash(manifest.get(key)):
            issues.append(
                _issue(f"{manifest_path}/{key}", "schema.hash", f"Invalid {key}")
            )
    request_path = confined_path(
        project.root_dir,
        manifest.get("requestPath", ""),
        f"{manifest_path}/requestPath",
    )
    snapshot_path = confined_path(
        project.root_dir,
        manifest.get("datasetSnapshotPath", ""),
        f"{manifest_path}/datasetSnapshotPath",
    )
    request = validate_research_request(
        _read_json(request_path, "research request"),
        request_path,
    )
    snapshot = _read_json(snapshot_path, "dataset snapshot")
    issues.extend(_validate_snapshot(snapshot, snapshot_path))
    surface = snapshot.get("intervalSurface")
    portfolio_policy = request.get("portfolioPolicy")
    if (
        isinstance(portfolio_policy, dict)
        and portfolio_policy.get("decisionAnchor") == "session-start"
        and (
            snapshot.get("schemaVersion") != 3
            or not isinstance(surface, dict)
            or surface.get("marketClock") != "session"
            or surface.get("calendar") != "XNYS"
            or surface.get("baseInterval") == "1d"
        )
    ):
        issues.append(
            _issue(
                f"{request_path}/portfolioPolicy/decisionAnchor",
                "request.dataset-decision-anchor",
                "session-start requires a V3 intraday XNYS "
                "regular-session package",
            )
        )
    if hash_json(request) != manifest.get("requestHash"):
        issues.append(_issue(request_path, "intake.request-hash", "Request hash mismatch"))
    if hash_file(snapshot_path) != manifest.get("datasetSnapshotHash"):
        issues.append(
            _issue(snapshot_path, "intake.snapshot-hash", "Dataset snapshot hash mismatch")
        )
    if snapshot.get("requestHash") != manifest.get("requestHash"):
        issues.append(
            _issue(snapshot_path, "intake.snapshot-request", "Snapshot request mismatch")
        )
    if snapshot.get("template") != manifest.get("template"):
        issues.append(
            _issue(
                snapshot_path,
                "intake.snapshot-template",
                "Snapshot template differs from Project intake",
            )
        )
    if snapshot.get("studyId") != manifest.get("studyId"):
        issues.append(
            _issue(
                snapshot_path,
                "intake.snapshot-study",
                "Snapshot Study differs from Project intake",
            )
        )
    requested_symbols = [item["symbol"] for item in request["assets"]]
    if snapshot.get("requestedAssets") != requested_symbols:
        issues.append(
            _issue(
                snapshot_path,
                "intake.snapshot-request-assets",
                "Snapshot requested assets differ from the Research Request",
            )
        )
    for asset in snapshot.get("assets", []):
        if not isinstance(asset, dict):
            continue
        normalized_rows = (
            asset.get("intervals", [])
            if snapshot.get("schemaVersion") in {2, 3}
            else [asset]
        )
        for row in normalized_rows:
            if not isinstance(row, dict):
                continue
            normalized_path = confined_path(
                project.root_dir / project.manifest.directories["data"],
                row.get("normalizedPath", ""),
                f"{snapshot_path}/assets/normalizedPath",
            )
            if not normalized_path.is_file():
                issues.append(
                    _issue(
                        normalized_path,
                        "intake.data-missing",
                        "Normalized asset is missing",
                    )
                )
            elif hash_file(normalized_path) != row.get("normalizedHash"):
                issues.append(
                    _issue(
                        normalized_path,
                        "intake.data-hash",
                        "Normalized asset hash mismatch",
                    )
                )
        if (
            snapshot.get("schemaVersion") in {2, 3}
            and isinstance(asset.get("symbol"), str)
            and isinstance(snapshot.get("timeRange"), dict)
        ):
            try:
                load_multi_interval_asset(
                    project.root_dir / project.manifest.directories["data"],
                    asset["symbol"],
                    start=snapshot["timeRange"].get("start", ""),
                    end=snapshot["timeRange"].get("end", ""),
                )
            except (IntervalContractError, TypeError, ValueError) as error:
                issues.append(
                    _issue(
                        snapshot_path,
                        getattr(error, "code", "interval.reconciliation"),
                        str(error),
                    )
                )
    study = load_study(project, manifest.get("studyId", ""))
    if study.study_hash != manifest.get("studyHash"):
        issues.append(
            _issue(study.manifest_path, "intake.study-hash", "Study hash mismatch")
        )
    # `studyInputHash` is the immutable identity created at intake time. The
    # editable Study subject is expected to evolve after that handoff, so a
    # different current input hash is evidence staleness, not intake
    # corruption. Run/Session/Report projections compare against the current
    # Study identity and surface that state explicitly.
    if study.dataset_hash != manifest.get("datasetHash"):
        issues.append(
            _issue(
                study.manifest_path,
                "intake.dataset-hash",
                "Study dataset hash mismatch",
            )
        )
    time_range = (
        snapshot.get("timeRange")
        if isinstance(snapshot.get("timeRange"), dict)
        else {}
    )
    expected_dataset = {
        "id": snapshot.get("id"),
        "version": snapshot.get("version"),
        "assetClass": snapshot.get("assetClass"),
        "universe": snapshot.get("universe"),
        "timeRange": time_range,
    }
    actual_dataset = study.definition.dataset
    if (
        actual_dataset.id != expected_dataset["id"]
        or actual_dataset.version != expected_dataset["version"]
        or actual_dataset.asset_class != expected_dataset["assetClass"]
        or actual_dataset.universe != expected_dataset["universe"]
        or actual_dataset.time_range.start
        != expected_dataset["timeRange"].get("start")
        or actual_dataset.time_range.end
        != expected_dataset["timeRange"].get("end")
    ):
        issues.append(
            _issue(study.manifest_path, "intake.study-dataset", "Study differs from snapshot")
        )
    mandate_studies = {
        "ohlcv-portfolio-lab": ("ohlcv-portfolio-quality",),
        "ohlcv-rl-factor-lab": ("ohlcv-rl-factor-policy",),
        "ohlcv-research-desk": (
            "ohlcv-portfolio-quality",
            "ohlcv-rl-factor-policy",
        ),
    }.get(manifest.get("template"), ())
    requires_mandate = False
    for mandate_study_id in mandate_studies:
        mandate_study = load_study(project, mandate_study_id)
        if (
            mandate_study.definition.dependencies is not None
            and PORTFOLIO_MANDATE
            in mandate_study.definition.dependencies["paths"]
        ):
            requires_mandate = True
    mandate_path = project.root_dir / PORTFOLIO_MANDATE
    if requires_mandate or mandate_path.exists() or mandate_path.is_symlink():
        mandate = load_portfolio_mandate(mandate_path)
        annualization = 252
        if snapshot.get("schemaVersion") in {2, 3} and snapshot.get("assets"):
            first_asset = snapshot["assets"][0]
            if isinstance(first_asset, dict):
                base_interval = snapshot["intervalSurface"]["baseInterval"]
                base_record = next(
                    (
                        row
                        for row in first_asset.get("intervals", [])
                        if row.get("interval") == base_interval
                    ),
                    None,
                )
                if isinstance(base_record, dict):
                    normalized_path = confined_path(
                        project.root_dir
                        / project.manifest.directories["data"],
                        base_record.get("normalizedPath", ""),
                        f"{snapshot_path}/assets/0/intervals",
                    )
                    annualization = infer_annualization_periods(
                        _read_source(normalized_path)["timestamp"]
                    )
        expected_mandate = build_portfolio_mandate(
            request,
            list(snapshot.get("universe", [])),
            annualization_periods=annualization,
        )
        if mandate != expected_mandate:
            issues.append(
                _issue(
                    mandate_path,
                    "intake.portfolio-mandate",
                    "Portfolio Mandate differs from the normalized request",
                )
            )
    horizon_studies = {
        "ohlcv-factor-lab": ("ohlcv-factor-quality",),
        "ohlcv-portfolio-lab": ("ohlcv-portfolio-quality",),
        "ohlcv-rl-factor-lab": ("ohlcv-rl-factor-policy",),
        "ohlcv-research-desk": (
            "ohlcv-factor-quality",
            "ohlcv-portfolio-quality",
            "ohlcv-rl-factor-policy",
        ),
    }.get(manifest.get("template"), ())
    requires_horizon = False
    for horizon_study_id in horizon_studies:
        horizon_study = load_study(project, horizon_study_id)
        if (
            horizon_study.definition.dependencies is not None
            and RESEARCH_HORIZON
            in horizon_study.definition.dependencies["paths"]
        ):
            requires_horizon = True
        else:
            issues.append(
                _issue(
                    horizon_study.manifest_path,
                    "intake.research-horizon-dependency",
                    "Study does not bind the fixed research horizon",
                )
            )
    horizon_path = project.root_dir / RESEARCH_HORIZON
    if requires_horizon or horizon_path.exists() or horizon_path.is_symlink():
        horizon = load_research_horizon(horizon_path)
        expected_horizon = build_research_horizon(request)
        if horizon != expected_horizon:
            issues.append(
                _issue(
                    horizon_path,
                    "intake.research-horizon",
                    "Horizon Mandate differs from the normalized request",
                )
            )
    if issues:
        raise AutoQuantValidationError(issues)
    return {
        "manifest": manifest,
        "request": request,
        "dataset": snapshot,
        "study": {
            "id": study.definition.id,
            "name": study.definition.name,
            "hash": study.study_hash,
            "inputHash": study.input_hash,
            "intakeInputHash": manifest["studyInputHash"],
            "current": study.input_hash == manifest["studyInputHash"],
        },
    }


OHLCV_DATASET_PACKAGE_V1_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant external OHLCV dataset package",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "frequency",
        "market",
        "priceAdjustment",
        "provider",
        "assets",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": DATASET_PACKAGE_KIND},
        "id": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "assetClass": {"type": "string", "minLength": 1},
        "frequency": {"const": "1d"},
        "market": {
            "type": "object",
            "additionalProperties": False,
            "required": ["clock", "calendar", "timezone"],
            "properties": {
                "clock": {"const": "session"},
                "calendar": {"type": "string", "minLength": 1},
                "timezone": {"type": "string", "minLength": 1},
            },
        },
        "priceAdjustment": {"enum": sorted(PRICE_ADJUSTMENTS)},
        "provider": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "retrievedAt", "sourceUri", "terms"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "retrievedAt": {"type": "string", "minLength": 1},
                "sourceUri": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "minLength": 1},
                    ]
                },
                "terms": {"type": "string", "minLength": 1},
            },
        },
        "assets": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["symbol", "venue", "currency", "path"],
                "properties": {
                    "symbol": {
                        "type": "string",
                        "pattern": SAFE_SYMBOL.pattern,
                    },
                    "venue": {"type": "string", "minLength": 1},
                    "currency": {"type": "string", "minLength": 1},
                    "path": {"type": "string", "minLength": 1},
                },
            },
        },
    },
}

OHLCV_DATASET_PACKAGE_V2_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant causal multi-interval OHLCV dataset package",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "baseInterval",
        "featureIntervals",
        "timestampSemantics",
        "aggregation",
        "market",
        "priceAdjustment",
        "provider",
        "assets",
    ],
    "properties": {
        "schemaVersion": {"const": 2},
        "kind": {"const": DATASET_PACKAGE_KIND},
        "id": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "assetClass": {"type": "string", "minLength": 1},
        "baseInterval": {"const": BASE_INTERVAL},
        "featureIntervals": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"enum": list(SUPPORTED_FEATURE_INTERVALS)},
        },
        "timestampSemantics": {"const": "bar-close"},
        "aggregation": {
            "type": "object",
            "additionalProperties": False,
            "required": ["method", "anchor"],
            "properties": {
                "method": {"const": AGGREGATION_METHOD},
                "anchor": {"const": "00:00"},
            },
        },
        "market": {
            "const": {
                "clock": "continuous",
                "calendar": "24/7",
                "timezone": "UTC",
            }
        },
        "priceAdjustment": {"enum": sorted(PRICE_ADJUSTMENTS)},
        "provider": OHLCV_DATASET_PACKAGE_V1_JSON_SCHEMA["properties"]["provider"],
        "assets": OHLCV_DATASET_PACKAGE_V1_JSON_SCHEMA["properties"]["assets"],
    },
}
OHLCV_DATASET_PACKAGE_V3_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant configurable session-aware OHLCV dataset package",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "id",
        "version",
        "assetClass",
        "baseInterval",
        "featureIntervals",
        "timestampSemantics",
        "aggregation",
        "market",
        "priceAdjustment",
        "provider",
        "assets",
    ],
    "properties": {
        "schemaVersion": {"const": 3},
        "kind": {"const": DATASET_PACKAGE_KIND},
        "id": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "assetClass": {"type": "string", "minLength": 1},
        "baseInterval": {"enum": list(SUPPORTED_BASE_INTERVALS)},
        "featureIntervals": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"enum": list(SUPPORTED_INTERVALS)},
        },
        "timestampSemantics": {"const": "bar-close"},
        "aggregation": {
            "type": "object",
            "additionalProperties": False,
            "required": ["method", "anchor", "terminalBucketPolicy"],
            "properties": {
                "method": {
                    "enum": [
                        CONTINUOUS_AGGREGATION_METHOD,
                        XNYS_AGGREGATION_METHOD,
                    ]
                },
                "anchor": {"enum": ["00:00", "market-open"]},
                "terminalBucketPolicy": {
                    "enum": [
                        CONTINUOUS_TERMINAL_POLICY,
                        SESSION_TERMINAL_POLICY,
                    ]
                },
            },
        },
        "market": {
            "oneOf": [
                {
                    "const": {
                        "clock": "continuous",
                        "calendar": "24/7",
                        "timezone": "UTC",
                    }
                },
                {
                    "const": {
                        "clock": "session",
                        "calendar": "XNYS",
                        "timezone": "America/New_York",
                    }
                },
            ]
        },
        "priceAdjustment": {"enum": sorted(PRICE_ADJUSTMENTS)},
        "provider": OHLCV_DATASET_PACKAGE_V1_JSON_SCHEMA["properties"]["provider"],
        "assets": OHLCV_DATASET_PACKAGE_V1_JSON_SCHEMA["properties"]["assets"],
    },
}
OHLCV_DATASET_PACKAGE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant external OHLCV dataset package",
    "type": "object",
    "properties": {
        "schemaVersion": {"enum": [1, 2, 3]},
        "kind": {"const": DATASET_PACKAGE_KIND},
        "frequency": {"const": "1d"},
        "baseInterval": {"enum": list(SUPPORTED_BASE_INTERVALS)},
        "featureIntervals": {
            "type": "array",
            "items": {"enum": list(SUPPORTED_INTERVALS)},
        },
    },
    "oneOf": [
        OHLCV_DATASET_PACKAGE_V1_JSON_SCHEMA,
        OHLCV_DATASET_PACKAGE_V2_JSON_SCHEMA,
        OHLCV_DATASET_PACKAGE_V3_JSON_SCHEMA,
    ],
}
