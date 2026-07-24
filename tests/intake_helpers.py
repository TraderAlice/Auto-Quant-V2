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
) -> tuple[Path, Path]:
    source = root / "external-data"
    source.mkdir()
    dates = pd.bdate_range("2024-01-02", periods=observations)
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
        "id": "bounded-us-equities",
        "version": "2024-v1",
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
        "question": "Does relative activity improve a costed US equity basket?",
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
        "direction": "relative-value",
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
