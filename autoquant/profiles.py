"""Versioned Harness and asset-profile configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_ASSET_CLASSES = {"crypto", "equity", "forex", "futures"}
SUPPORTED_MARKET_CLOCKS = {"continuous", "session"}
SUPPORTED_DATA_PROVIDERS = {"freqtrade", "local"}


class ManifestError(ValueError):
    """Raised when ``harness.json`` does not satisfy the local contract."""


@dataclass(frozen=True)
class AssetProfile:
    """One bounded market/data arena handled by the Harness."""

    id: str
    asset_class: str
    venue: str
    trading_mode: str
    market_clock: str
    calendar: str
    timezone: str
    session: str
    pairs: tuple[str, ...]
    base_timeframe: str
    timeframes: tuple[str, ...]
    timerange: str
    stake_currency: str
    fee: float
    max_open_trades: int
    annualization_days: int
    data_provider: str
    data_directory: str
    data_format: str
    fill_missing: bool
    offline_exchange: bool
    price_tick: float | None
    amount_step: float | None

    @property
    def is_session_based(self) -> bool:
        return self.market_clock == "session"

    def data_dir(self, project_dir: Path) -> Path:
        """Resolve and contain the profile data directory inside the project."""

        project_dir = project_dir.resolve()
        resolved = (project_dir / self.data_directory).resolve()
        if not resolved.is_relative_to(project_dir):
            raise ManifestError(
                f"profile {self.id!r} data.directory escapes the project: "
                f"{self.data_directory!r}"
            )
        return resolved


@dataclass(frozen=True)
class HarnessInterfaces:
    prepare: str
    validate: str
    run: str
    output_schema_version: int
    output_format: str
    output_identity_fields: tuple[str, ...]


@dataclass(frozen=True)
class HarnessManifest:
    schema_version: int
    harness_id: str
    harness_version: str
    engine_name: str
    engine_version: str
    interfaces: HarnessInterfaces
    default_profile: str
    profiles: dict[str, AssetProfile]

    def profile(self, profile_id: str | None = None) -> AssetProfile:
        selected = profile_id or os.environ.get("AUTOQUANT_PROFILE") or self.default_profile
        try:
            return self.profiles[selected]
        except KeyError as exc:
            available = ", ".join(sorted(self.profiles))
            raise ManifestError(
                f"unknown asset profile {selected!r}; available: {available}"
            ) from exc


def _required(mapping: dict[str, Any], key: str, context: str) -> Any:
    try:
        return mapping[key]
    except KeyError as exc:
        raise ManifestError(f"{context} is missing required field {key!r}") from exc


def _parse_profile(profile_id: str, raw: dict[str, Any]) -> AssetProfile:
    context = f"profile {profile_id!r}"
    market = _required(raw, "market", context)
    data = _required(raw, "data", context)

    asset_class = str(_required(raw, "asset_class", context))
    if asset_class not in SUPPORTED_ASSET_CLASSES:
        raise ManifestError(
            f"{context} asset_class must be one of {sorted(SUPPORTED_ASSET_CLASSES)}"
        )

    market_clock = str(_required(market, "clock", context))
    if market_clock not in SUPPORTED_MARKET_CLOCKS:
        raise ManifestError(
            f"{context} market.clock must be one of {sorted(SUPPORTED_MARKET_CLOCKS)}"
        )

    data_provider = str(_required(data, "provider", context))
    if data_provider not in SUPPORTED_DATA_PROVIDERS:
        raise ManifestError(
            f"{context} data.provider must be one of {sorted(SUPPORTED_DATA_PROVIDERS)}"
        )

    pairs = tuple(str(pair) for pair in _required(raw, "pairs", context))
    if not pairs or len(set(pairs)) != len(pairs):
        raise ManifestError(f"{context} pairs must be a non-empty unique list")
    if any("/" not in pair for pair in pairs):
        raise ManifestError(f"{context} pairs must use BASE/QUOTE names")

    timeframes = tuple(str(tf) for tf in _required(raw, "timeframes", context))
    base_timeframe = str(_required(raw, "base_timeframe", context))
    if base_timeframe not in timeframes:
        raise ManifestError(f"{context} base_timeframe must appear in timeframes")

    timerange = str(_required(raw, "timerange", context))
    if "-" not in timerange:
        raise ManifestError(f"{context} timerange must use Freqtrade start-stop syntax")

    fill_missing = bool(_required(data, "fill_missing", context))
    if market_clock == "session" and fill_missing:
        raise ManifestError(
            f"{context} is session-based and must not fill market-closure gaps"
        )

    price_tick = raw.get("price_tick")
    amount_step = raw.get("amount_step")

    return AssetProfile(
        id=profile_id,
        asset_class=asset_class,
        venue=str(_required(raw, "venue", context)),
        trading_mode=str(raw.get("trading_mode", "spot")),
        market_clock=market_clock,
        calendar=str(_required(market, "calendar", context)),
        timezone=str(_required(market, "timezone", context)),
        session=str(market.get("session", "all")),
        pairs=pairs,
        base_timeframe=base_timeframe,
        timeframes=timeframes,
        timerange=timerange,
        stake_currency=str(_required(raw, "stake_currency", context)),
        fee=float(_required(raw, "fee", context)),
        max_open_trades=int(raw.get("max_open_trades", len(pairs))),
        annualization_days=int(_required(raw, "annualization_days", context)),
        data_provider=data_provider,
        data_directory=str(_required(data, "directory", context)),
        data_format=str(data.get("format", "feather")),
        fill_missing=fill_missing,
        offline_exchange=bool(raw.get("offline_exchange", data_provider == "local")),
        price_tick=float(price_tick) if price_tick is not None else None,
        amount_step=float(amount_step) if amount_step is not None else None,
    )


def load_manifest(path: Path | str | None = None) -> HarnessManifest:
    """Load and validate the versioned Harness manifest."""

    if path is None:
        path = Path(__file__).resolve().parents[1] / "harness.json"
    path = Path(path)
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ManifestError(f"harness manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in harness manifest {path}: {exc}") from exc

    schema_version = int(_required(raw, "schema_version", "manifest"))
    if schema_version != 1:
        raise ManifestError(f"unsupported harness schema_version {schema_version}")

    harness = _required(raw, "harness", "manifest")
    engine = _required(harness, "engine", "manifest.harness")
    raw_interfaces = _required(raw, "interfaces", "manifest")
    raw_output = _required(raw_interfaces, "output", "manifest.interfaces")
    raw_profiles = _required(raw, "profiles", "manifest")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ManifestError("manifest profiles must be a non-empty object")

    profiles = {
        str(profile_id): _parse_profile(str(profile_id), profile_raw)
        for profile_id, profile_raw in raw_profiles.items()
    }
    default_profile = str(_required(raw, "default_profile", "manifest"))
    if default_profile not in profiles:
        raise ManifestError("manifest default_profile must name a configured profile")

    return HarnessManifest(
        schema_version=schema_version,
        harness_id=str(_required(harness, "id", "manifest.harness")),
        harness_version=str(_required(harness, "version", "manifest.harness")),
        engine_name=str(_required(engine, "name", "manifest.harness.engine")),
        engine_version=str(_required(engine, "version", "manifest.harness.engine")),
        interfaces=HarnessInterfaces(
            prepare=str(_required(raw_interfaces, "prepare", "manifest.interfaces")),
            validate=str(_required(raw_interfaces, "validate", "manifest.interfaces")),
            run=str(_required(raw_interfaces, "run", "manifest.interfaces")),
            output_schema_version=int(
                _required(raw_output, "schema_version", "manifest.interfaces.output")
            ),
            output_format=str(
                _required(raw_output, "format", "manifest.interfaces.output")
            ),
            output_identity_fields=tuple(
                str(field)
                for field in _required(
                    raw_output,
                    "identity_fields",
                    "manifest.interfaces.output",
                )
            ),
        ),
        default_profile=default_profile,
        profiles=profiles,
    )
