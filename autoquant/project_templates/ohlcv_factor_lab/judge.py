"""Fixed no-lookahead Judge for the OHLCV Factor Lab reference Project."""

from __future__ import annotations

import importlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
MIN_ASSETS_PER_DATE = 4
MIN_IC_DATES_PER_SPLIT = 20


class JudgeFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _write_output(value: dict[str, Any]) -> None:
    Path(os.environ["AUTOQUANT_RUN_OUTPUT"]).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_contract() -> tuple[dict[str, Any], Path]:
    study = json.loads(
        Path(os.environ["AUTOQUANT_STUDY_PATH"]).read_text(encoding="utf-8")
    )
    data_root = Path(os.environ["AUTOQUANT_DATA_ROOT"]).resolve()
    if not data_root.is_dir():
        raise JudgeFailure("dataset.root", "AUTOQUANT_DATA_ROOT is not a directory")
    return study, data_root


def _load_asset(data_root: Path, asset: str, start: str, end: str) -> pd.DataFrame:
    source = (data_root / "ohlcv" / f"{asset}.csv").resolve()
    if data_root not in source.parents or not source.is_file():
        raise JudgeFailure("dataset.asset", f"Missing confined OHLCV file for {asset}")
    frame = pd.read_csv(source)
    if tuple(frame.columns) != REQUIRED_COLUMNS:
        raise JudgeFailure(
            "dataset.columns",
            f"{asset} columns must be exactly {', '.join(REQUIRED_COLUMNS)}",
        )
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        format="%Y-%m-%d",
        errors="raise",
    )
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
        raise JudgeFailure(
            "dataset.time-order",
            f"{asset} timestamps must be unique and chronological",
        )
    for column in REQUIRED_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    numeric = frame[list(REQUIRED_COLUMNS[1:])].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise JudgeFailure("dataset.non-finite", f"{asset} contains non-finite OHLCV")
    if (frame[["open", "high", "low", "close", "volume"]] <= 0).any().any():
        raise JudgeFailure("dataset.non-positive", f"{asset} contains non-positive OHLCV")
    if (
        (frame["high"] < frame[["open", "close"]].max(axis=1)).any()
        or (frame["low"] > frame[["open", "close"]].min(axis=1)).any()
    ):
        raise JudgeFailure("dataset.bar-shape", f"{asset} contains invalid bars")
    selected = frame[
        (frame["timestamp"] >= pd.Timestamp(start))
        & (frame["timestamp"] <= pd.Timestamp(end))
    ].copy()
    if len(selected) < 120:
        raise JudgeFailure(
            "dataset.observations",
            f"{asset} has fewer than 120 observations in the Study range",
        )
    return selected.reset_index(drop=True)


def _factor_series(module: Any, frame: pd.DataFrame, asset: str) -> pd.Series:
    before = frame.copy(deep=True)
    result = module.compute_factor(frame)
    if not frame.equals(before):
        raise JudgeFailure("factor.mutation", f"compute_factor mutated {asset} input")
    if not isinstance(result, pd.Series):
        raise JudgeFailure("factor.type", "compute_factor must return pandas.Series")
    if len(result) != len(frame) or not result.index.equals(frame.index):
        raise JudgeFailure(
            "factor.alignment",
            "Factor Series must preserve the input length and index",
        )
    try:
        numeric = pd.to_numeric(result, errors="raise").astype(float)
    except (TypeError, ValueError) as error:
        raise JudgeFailure("factor.numeric", f"Factor must be numeric: {error}") from error
    if np.isinf(numeric.to_numpy()).any():
        raise JudgeFailure("factor.non-finite", "Factor cannot contain infinity")
    return numeric


def _audit_causality(
    module: Any,
    frame: pd.DataFrame,
    full: pd.Series,
    asset: str,
) -> list[int]:
    cuts = sorted({len(frame) // 2, (len(frame) * 3) // 4, len(frame) - 2})
    for cut in cuts:
        prefix_frame = frame.iloc[: cut + 1].copy()
        prefix = _factor_series(module, prefix_frame, asset)
        start = max(0, cut - 4)
        expected = full.iloc[start : cut + 1].to_numpy(dtype=float)
        actual = prefix.iloc[start : cut + 1].to_numpy(dtype=float)
        if not np.isclose(
            expected,
            actual,
            rtol=1e-10,
            atol=1e-12,
            equal_nan=True,
        ).all():
            raise JudgeFailure(
                "factor.lookahead",
                f"{asset} past factor values change when future rows are withheld",
            )
    return cuts


def _daily_ic(factors: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    values: dict[pd.Timestamp, float] = {}
    for timestamp in factors.index.intersection(returns.index):
        pair = pd.DataFrame(
            {
                "factor": factors.loc[timestamp],
                "forward_return": returns.loc[timestamp],
            }
        ).dropna()
        if len(pair) < MIN_ASSETS_PER_DATE:
            continue
        if pair["factor"].nunique() < 2 or pair["forward_return"].nunique() < 2:
            continue
        value = pair["factor"].rank(method="average").corr(
            pair["forward_return"].rank(method="average")
        )
        if value is not None and math.isfinite(float(value)):
            values[timestamp] = float(value)
    return pd.Series(values, dtype=float).sort_index()


def _split_metrics(values: pd.Series) -> dict[str, float | int]:
    if len(values) < MIN_IC_DATES_PER_SPLIT:
        raise JudgeFailure(
            "judge.population",
            f"Chronological split has only {len(values)} valid IC dates",
        )
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    return {
        "mean_ic": mean,
        "icir": mean / std if std > 1e-12 else 0.0,
        "hit_rate": float((values > 0).mean()),
        "observations": int(len(values)),
    }


def _evaluate() -> tuple[dict[str, Any], dict[str, Any]]:
    study, data_root = _load_contract()
    dataset = study["dataset"]
    universe = dataset["universe"]
    time_range = dataset["time_range"]
    module = importlib.import_module("factors.candidate")
    if not callable(getattr(module, "compute_factor", None)):
        raise JudgeFailure(
            "factor.api",
            "factors.candidate must export callable compute_factor(frame)",
        )

    factor_by_asset: dict[str, pd.Series] = {}
    forward_by_asset: dict[str, pd.Series] = {}
    audited: dict[str, list[int]] = {}
    coverage: dict[str, float] = {}
    for asset in universe:
        frame = _load_asset(
            data_root,
            asset,
            time_range["start"],
            time_range["end"],
        )
        factor = _factor_series(module, frame, asset)
        audited[asset] = _audit_causality(module, frame, factor, asset)
        timestamp = pd.DatetimeIndex(frame["timestamp"])
        factor.index = timestamp
        forward = frame["close"].shift(-1) / frame["close"] - 1.0
        forward.index = timestamp
        factor_by_asset[asset] = factor
        forward_by_asset[asset] = forward
        coverage[asset] = float(factor.notna().mean())

    factor_panel = pd.DataFrame(factor_by_asset)
    forward_panel = pd.DataFrame(forward_by_asset)
    daily_ic = _daily_ic(factor_panel, forward_panel)
    if len(daily_ic) < 3 * MIN_IC_DATES_PER_SPLIT:
        raise JudgeFailure(
            "judge.population",
            "Too few valid cross-sectional dates for chronological evaluation",
        )
    train_end = int(len(daily_ic) * 0.60)
    validation_end = int(len(daily_ic) * 0.80)
    splits = {
        "train": _split_metrics(daily_ic.iloc[:train_end]),
        "validation": _split_metrics(daily_ic.iloc[train_end:validation_end]),
        "test": _split_metrics(daily_ic.iloc[validation_end:]),
    }
    score = min(
        float(splits["validation"]["mean_ic"]),
        float(splits["test"]["mean_ic"]),
    )
    ranked = factor_panel.rank(axis=1, pct=True)
    turnover = float(ranked.diff().abs().mean(axis=1).dropna().mean())
    metrics = {
        "score": score,
        "train": splits["train"],
        "validation": splits["validation"],
        "test": splits["test"],
        "mean_coverage": float(sum(coverage.values()) / len(coverage)),
        "mean_rank_turnover": turnover,
        "assets": int(len(universe)),
        "ic_dates": int(len(daily_ic)),
    }
    if not all(
        math.isfinite(float(value))
        for value in (
            score,
            metrics["mean_coverage"],
            metrics["mean_rank_turnover"],
        )
    ):
        raise JudgeFailure("judge.non-finite", "Judge produced non-finite metrics")
    report = {
        "schemaVersion": 1,
        "inputHash": os.environ["AUTOQUANT_INPUT_HASH"],
        "dataset": {
            "id": dataset["id"],
            "version": dataset["version"],
            "universe": universe,
            "timeRange": time_range,
        },
        "semantics": {
            "target": "next-bar close-to-close return",
            "measure": "per-date cross-sectional Spearman IC",
            "split": "chronological 60/20/20",
            "score": "minimum of validation and test mean IC",
        },
        "causalityAuditCuts": audited,
        "coverageByAsset": coverage,
        "metrics": metrics,
    }
    return metrics, report


def main() -> None:
    try:
        metrics, report = _evaluate()
        artifacts = Path(os.environ["AUTOQUANT_ARTIFACTS_DIR"])
        report_path = artifacts / "factor-report.json"
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_output(
            {
                "schema_version": 1,
                "status": "succeeded",
                "summary": (
                    "Causal factor evaluated on chronological "
                    f"validation/test splits; score={metrics['score']:.6f}"
                ),
                "metrics": metrics,
                "artifacts": [
                    {
                        "kind": "factor-report",
                        "path": "factor-report.json",
                        "description": (
                            "Factor semantics, split metrics, coverage, and causality audit"
                        ),
                    }
                ],
                "errors": [],
            }
        )
    except JudgeFailure as error:
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": str(error),
                "metrics": {},
                "artifacts": [],
                "errors": [{"code": error.code, "message": str(error)}],
            }
        )
    except Exception as error:  # Preserve candidate/Judge diagnostics as evidence.
        _write_output(
            {
                "schema_version": 1,
                "status": "failed",
                "summary": f"Factor evaluation raised {type(error).__name__}",
                "metrics": {},
                "artifacts": [],
                "errors": [
                    {
                        "code": "factor.exception",
                        "message": f"{type(error).__name__}: {error}",
                    }
                ],
            }
        )


if __name__ == "__main__":
    main()
