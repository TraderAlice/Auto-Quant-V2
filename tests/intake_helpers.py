from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


INTAKE_ASSETS = ("AAPL", "MSFT", "NVDA", "QQQ", "SPY")


def write_intake_inputs(
    root: Path,
    *,
    observations: int = 260,
    assets: tuple[str, ...] = INTAKE_ASSETS,
    start: str = "2024-01-02",
    dataset_id: str = "bounded-us-equities",
    dataset_version: str = "2024-v1",
) -> tuple[Path, Path]:
    source = root / "external-data"
    source.mkdir()
    dates = pd.bdate_range(start, periods=observations)
    time = np.arange(observations, dtype=float)
    asset_entries = []
    for number, symbol in enumerate(assets):
        log_returns = (
            0.00025
            + 0.0045 * np.sin(time / (5.0 + number))
            + 0.0020 * np.cos(time / (11.0 + number * 0.7))
        )
        close = (90.0 + number * 25.0) * np.exp(np.cumsum(log_returns))
        open_price = close * np.exp(
            -0.0015 * np.sin(time / (3.0 + number))
        )
        spread = 0.004 + 0.001 * np.cos(time / (7.0 + number))
        frame = pd.DataFrame(
            {
                "date": dates.strftime("%Y-%m-%d"),
                "open": open_price,
                "high": np.maximum(open_price, close) * (1.0 + spread),
                "low": np.minimum(open_price, close) * (1.0 - spread),
                "close": close,
                "volume": (
                    1_000_000.0
                    * (1.0 + number * 0.15)
                    * np.exp(
                        0.35 * np.sin(time / (8.0 + number) + number)
                    )
                ),
            }
        )
        filename = f"{symbol}.csv"
        frame.to_csv(source / filename, index=False)
        asset_entries.append(
            {
                "symbol": symbol,
                "venue": "US-COMPOSITE",
                "currency": "USD",
                "path": filename,
            }
        )
    package = {
        "schemaVersion": 1,
        "kind": "autoquant-ohlcv-dataset-package",
        "id": dataset_id,
        "version": dataset_version,
        "assetClass": "equity",
        "frequency": "1d",
        "market": {
            "clock": "session",
            "calendar": "XNYS",
            "timezone": "America/New_York",
        },
        "priceAdjustment": "provider-adjusted",
        "provider": {
            "name": "deterministic-test-provider",
            "retrievedAt": "2026-07-24T00:00:00Z",
            "sourceUri": None,
            "terms": "test fixture only",
        },
        "assets": asset_entries,
    }
    package_path = source / "dataset.json"
    package_path.write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    request = {
        "schemaVersion": 1,
        "kind": "autoquant-research-request",
        "title": "US leadership durability",
        "question": "Does relative activity support a costed long allocation?",
        "decisionContext": "OpenAlice is reviewing a medium-term equity posture.",
        "assets": [
            {
                "symbol": "AAPL",
                "assetClass": "equity",
                "venue": "US-COMPOSITE",
            },
            {
                "symbol": "MSFT",
                "assetClass": "equity",
                "venue": "US-COMPOSITE",
            },
        ],
        "direction": "long",
        "horizon": "one to four weeks",
        "hypotheses": ["Relative activity may identify persistent leadership."],
        "constraints": ["No live trading authority."],
        "deliverables": ["Factor and portfolio evidence", "Decision-support report"],
        "source": {
            "system": "openalice",
            "workspaceId": "workspace-equities",
            "sessionId": "session-intake",
            "artifactPath": "research/us-leadership.md",
            "artifactRevision": "sha256:test-request",
        },
    }
    request_path = root / "request.json"
    request_path.write_text(
        json.dumps(request, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return request_path, package_path


def write_multi_interval_inputs(
    root: Path,
    *,
    observations: int = 288,
    assets: tuple[str, ...] = ("BTC", "ETH", "SOL", "XRP", "ADA"),
) -> tuple[Path, Path]:
    source = root / "external-hourly-data"
    source.mkdir()
    timestamps = pd.date_range(
        "2026-01-01T01:00:00Z",
        periods=observations,
        freq="1h",
    )
    time = np.arange(observations, dtype=float)
    asset_entries = []
    for number, symbol in enumerate(assets):
        log_returns = (
            0.00008
            + 0.0025 * np.sin(time / (9.0 + number))
            + 0.0012 * np.cos(time / (21.0 + number))
        )
        close = (80.0 + number * 17.0) * np.exp(np.cumsum(log_returns))
        open_price = close * np.exp(-0.001 * np.sin(time / (4.0 + number)))
        spread = 0.0025 + 0.0005 * np.cos(time / (8.0 + number))
        frame = pd.DataFrame(
            {
                "timestamp": timestamps.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": open_price,
                "high": np.maximum(open_price, close) * (1.0 + spread),
                "low": np.minimum(open_price, close) * (1.0 - spread),
                "close": close,
                "volume": (
                    2_000_000.0
                    * (1.0 + number * 0.18)
                    * np.exp(0.25 * np.sin(time / (13.0 + number)))
                ),
            }
        )
        filename = f"{symbol}.csv"
        frame.to_csv(source / filename, index=False)
        asset_entries.append(
            {
                "symbol": symbol,
                "venue": "CRYPTO-COMPOSITE",
                "currency": "USD",
                "path": filename,
            }
        )
    package = {
        "schemaVersion": 2,
        "kind": "autoquant-ohlcv-dataset-package",
        "id": "bounded-crypto-hourly",
        "version": "2026-v1",
        "assetClass": "crypto",
        "baseInterval": "1h",
        "featureIntervals": ["3h", "4h", "6h", "12h", "1d"],
        "timestampSemantics": "bar-close",
        "aggregation": {
            "method": "complete-utc-midnight-bar-close-v1",
            "anchor": "00:00",
        },
        "market": {
            "clock": "continuous",
            "calendar": "24/7",
            "timezone": "UTC",
        },
        "priceAdjustment": "raw",
        "provider": {
            "name": "deterministic-hourly-test-provider",
            "retrievedAt": "2026-07-26T00:00:00Z",
            "sourceUri": None,
            "terms": "test fixture only",
        },
        "assets": asset_entries,
    }
    package_path = source / "dataset.json"
    package_path.write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    request = {
        "schemaVersion": 1,
        "kind": "autoquant-research-request",
        "title": "Crypto multi-horizon persistence",
        "question": "Do completed higher-horizon bars improve hourly ranking?",
        "decisionContext": "OpenAlice is reviewing a conditional crypto posture.",
        "assets": [
            {
                "symbol": "BTC",
                "assetClass": "crypto",
                "venue": "CRYPTO-COMPOSITE",
            },
            {
                "symbol": "ETH",
                "assetClass": "crypto",
                "venue": "CRYPTO-COMPOSITE",
            },
        ],
        "direction": "long",
        "horizon": "one day to four weeks",
        "hypotheses": [
            "Completed daily and intraday trends may add causal information."
        ],
        "constraints": ["Use only completed bars and no live trading authority."],
        "deliverables": ["Multi-interval factor and portfolio evidence"],
        "source": {
            "system": "openalice",
            "workspaceId": "workspace-crypto",
            "sessionId": "session-multi-interval",
            "artifactPath": "research/crypto-multi-horizon.md",
            "artifactRevision": "sha256:test-multi-interval-request",
        },
    }
    request_path = root / "request.json"
    request_path.write_text(
        json.dumps(request, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return request_path, package_path
