"""Fast bounded contract checks for an editable OHLCV factor candidate."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


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


def _series(module: object, frame: pd.DataFrame) -> pd.Series:
    candidate = getattr(module, "compute_factor", None)
    if not callable(candidate):
        raise CheckFailure(
            "factor.api",
            "factors.candidate must export callable compute_factor(frame)",
        )
    before = frame.copy(deep=True)
    try:
        result = candidate(frame)
    except Exception as error:
        raise CheckFailure(
            "factor.execution",
            f"compute_factor raised {type(error).__name__}: {error}",
        ) from error
    try:
        pd.testing.assert_frame_equal(frame, before)
    except AssertionError as error:
        raise CheckFailure("factor.mutation", "compute_factor mutated its input") from error
    if not isinstance(result, pd.Series):
        raise CheckFailure("factor.type", "compute_factor must return a pandas Series")
    if not result.index.equals(frame.index):
        raise CheckFailure(
            "factor.alignment",
            "Factor Series index must exactly match the input frame",
        )
    if not pd.api.types.is_numeric_dtype(result.dtype):
        raise CheckFailure("factor.numeric", "Factor Series must be numeric")
    values = result.to_numpy(dtype=float)
    if np.isinf(values).any():
        raise CheckFailure("factor.non-finite", "Factor Series contains infinity")
    if not np.isfinite(values).any():
        raise CheckFailure("factor.empty", "Factor Series has no finite observation")
    return result.astype(float)


def main() -> None:
    checks: list[dict[str, str]] = []
    try:
        study = json.loads(STUDY.read_text(encoding="utf-8"))
        universe = study["dataset"]["universe"][:2]
        if not universe:
            raise CheckFailure("data.universe", "Study universe is empty")
        module = importlib.import_module("factors.candidate")
        for symbol in universe:
            frame = pd.read_csv(DATA / "ohlcv" / f"{symbol}.csv").iloc[:256].copy()
            first = _series(module, frame.copy(deep=True))
            second = _series(module, frame.copy(deep=True))
            try:
                pd.testing.assert_series_equal(first, second)
            except AssertionError as error:
                raise CheckFailure(
                    "factor.nondeterministic",
                    "compute_factor returned different values for one input",
                ) from error
            for cut in sorted({max(24, len(frame) // 2), len(frame) - 1}):
                prefix = frame.iloc[:cut].copy()
                prefix_result = _series(module, prefix)
                try:
                    pd.testing.assert_series_equal(
                        first.iloc[:cut],
                        prefix_result,
                        check_names=False,
                    )
                except AssertionError as error:
                    raise CheckFailure(
                        "factor.lookahead",
                        "Earlier factor values changed when future rows were removed",
                    ) from error
        checks.append(
            {
                "id": "factor-contract",
                "status": "passed",
                "message": (
                    "API, immutability, alignment, numeric, deterministic, "
                    "and bounded prefix-causality checks passed"
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
