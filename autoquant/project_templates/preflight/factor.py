"""Fast bounded contract checks for an editable OHLCV factor candidate."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pandas as pd

from autoquant.factor_runtime import (
    FactorRuntimeError,
    build_factor_panel,
    evaluate_factor,
)
from autoquant.intervals import IntervalContractError, load_multi_interval_asset

OUTPUT = Path(os.environ["AUTOQUANT_CHECK_OUTPUT"])
PROJECT = Path(os.environ["AUTOQUANT_PROJECT_ROOT"])
DATA = Path(os.environ["AUTOQUANT_DATA_ROOT"])
STUDY = Path(os.environ["AUTOQUANT_STUDY_PATH"])


class CheckFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _write(status: str, checks: list[dict[str, str]], errors: list[dict[str, str]]) -> None:
    summary = (
        "Candidate satisfies the bounded factor contract"
        if status == "passed"
        else errors[0]["message"]
    )
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": status,
                "summary": summary,
                "checks": checks,
                "errors": errors,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    checks: list[dict[str, str]] = []
    try:
        study = json.loads(STUDY.read_text(encoding="utf-8"))
        universe = study["dataset"]["universe"][:2]
        if not universe:
            raise CheckFailure("data.universe", "Study universe is empty")
        module = importlib.import_module("factors.candidate")
        frames: dict[str, pd.DataFrame] = {}
        for symbol in universe:
            time_range = study["dataset"]["time_range"]
            try:
                frame = load_multi_interval_asset(
                    DATA,
                    symbol,
                    start=time_range["start"],
                    end=time_range["end"],
                )
            except IntervalContractError as error:
                raise CheckFailure(error.code, str(error)) from error
            if frame is None:
                frame = pd.read_csv(DATA / "ohlcv" / f"{symbol}.csv")
                frame["timestamp"] = pd.to_datetime(
                    frame["timestamp"],
                    utc=True,
                    errors="raise",
                )
            frames[symbol] = frame.iloc[:256].reset_index(drop=True)
        try:
            panel = build_factor_panel(frames, universe=universe)
            evaluate_factor(module, panel)
        except FactorRuntimeError as error:
            raise CheckFailure(error.code, str(error)) from error
        checks.append(
            {
                "id": "factor-contract",
                "status": "passed",
                "message": (
                    "Panel API, identity, immutability, alignment, numeric, "
                    "deterministic, component declaration, and bounded "
                    "panel-prefix causality checks passed"
                ),
            }
        )
        _write("passed", checks, [])
    except CheckFailure as error:
        checks.append(
            {"id": error.code, "status": "failed", "message": str(error)}
        )
        _write("failed", checks, [{"code": error.code, "message": str(error)}])
    except Exception as error:
        message = f"Unexpected preflight error: {type(error).__name__}: {error}"
        _write(
            "failed",
            [{"id": "preflight-error", "status": "failed", "message": message}],
            [{"code": "preflight.error", "message": message}],
        )


if __name__ == "__main__":
    main()
