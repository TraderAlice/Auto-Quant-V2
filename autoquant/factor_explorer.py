"""Bounded, verified diagnostics for immutable Factor Runs."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .runs import RunContext, load_run
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


FACTOR_DIAGNOSTICS_KIND = "autoquant-factor-diagnostics"
DEFAULT_FACTOR_POINTS = 180
MIN_FACTOR_POINTS = 40
MAX_FACTOR_POINTS = 400
MAX_ARTIFACT_BYTES = 32 * 1024 * 1024
MAX_DAILY_ROWS = 100_000
MAX_QUANTILE_ROWS = 300_000
MAX_UNIVERSE = 256
HORIZONS = (1, 5, 10)
SPLITS = ("train", "validation", "test")
SPLIT_ROLES = {
    "train": "training",
    "validation": "selection",
    "test": "visible-audit",
}
REGIMES = {
    "up-calm",
    "up-stressed",
    "down-calm",
    "down-stressed",
    "unavailable",
}
STYLES = {
    "momentum_20",
    "reversal_5",
    "realized_volatility_20",
    "relative_volume_20",
}
EXPECTED_ARTIFACT_KINDS = {
    "factor-report",
    "factor-daily",
    "factor-quantiles",
}
DAILY_COLUMNS = [
    "timestamp",
    "split",
    "regime",
    *[
        f"{measure}_ic_h{horizon}"
        for horizon in HORIZONS
        for measure in ("rank", "pearson")
    ],
]
QUANTILE_COLUMNS = [
    "timestamp",
    "split",
    "horizon",
    "low",
    "middle",
    "high",
    "high_minus_low",
]


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _fail(path: Path | str, code: str, message: str) -> None:
    raise AutoQuantValidationError([_issue(path, code, message)])


def _finite(value: Any, path: Path | str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        _fail(path, "factor.number", "Expected a finite numeric value")
    if not math.isfinite(number):
        _fail(path, "factor.number", "Expected a finite numeric value")
    return number


def _optional_finite(value: Any, path: Path | str) -> float | None:
    if value is None or value == "":
        return None
    return _finite(value, path)


def _bounded(
    value: Any,
    path: Path | str,
    *,
    minimum: float,
    maximum: float,
) -> float:
    number = _finite(value, path)
    if number < minimum - 1e-12 or number > maximum + 1e-12:
        _fail(
            path,
            "factor.bound",
            f"Expected a value from {minimum} through {maximum}",
        )
    return number


def _integer(value: Any, path: Path | str, *, minimum: int = 0) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
    ):
        _fail(path, "factor.integer", f"Expected an integer >= {minimum}")
    return value


def _session_date(value: Any, path: Path | str) -> str:
    if not isinstance(value, str):
        _fail(path, "factor.timestamp", "Timestamp must be an ISO session date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        _fail(path, "factor.timestamp", "Timestamp must be an ISO session date")
    if parsed.isoformat() != value:
        _fail(path, "factor.timestamp", "Timestamp must be an ISO session date")
    return value


def _close(
    actual: float | None,
    expected: Any,
    path: Path | str,
    label: str,
) -> None:
    if expected is None:
        if actual is not None:
            _fail(path, "factor.reconciliation", f"{label} must be null")
        return
    expected_number = _finite(expected, path)
    if actual is None or not math.isclose(
        actual,
        expected_number,
        rel_tol=1e-9,
        abs_tol=1e-10,
    ):
        _fail(
            path,
            "factor.reconciliation",
            f"Artifact does not reconcile {label}",
        )


def _artifact_paths(
    run: RunContext,
) -> tuple[dict[str, Path], dict[str, dict[str, str]]]:
    if run.result["status"] != "succeeded":
        _fail(
            run.root_dir,
            "factor.run-status",
            "Factor diagnostics require a successful immutable Run",
        )
    artifacts = run.result.get("artifacts")
    if not isinstance(artifacts, list):
        _fail(run.root_dir, "factor.artifacts", "Run artifacts must be an array")
    paths: dict[str, Path] = {}
    identities: dict[str, dict[str, str]] = {}
    for index, artifact in enumerate(artifacts):
        artifact_path = f"{run.root_dir}/result.json/artifacts/{index}"
        if not isinstance(artifact, dict):
            _fail(artifact_path, "factor.artifact", "Artifact must be an object")
        kind = artifact.get("kind")
        if kind not in EXPECTED_ARTIFACT_KINDS:
            continue
        if kind in paths:
            _fail(
                artifact_path,
                "factor.duplicate-artifact",
                f"Factor artifact kind must be unique: {kind}",
            )
        relative = artifact.get("path")
        if not isinstance(relative, str):
            _fail(
                artifact_path,
                "factor.artifact-path",
                "Factor artifact path must be a string",
            )
        path = confined_path(run.root_dir, relative, artifact_path)
        if not path.is_file():
            _fail(path, "factor.artifact-missing", f"Missing artifact: {kind}")
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            _fail(
                path,
                "factor.artifact-size",
                f"Factor artifact exceeds {MAX_ARTIFACT_BYTES} bytes",
            )
        content_hash = run.manifest["files"].get(relative)
        if not isinstance(content_hash, str):
            _fail(
                path,
                "factor.artifact-identity",
                "Artifact is absent from immutable Run identity",
            )
        paths[kind] = path
        identities[kind] = {"path": relative, "sha256": content_hash}
    missing = EXPECTED_ARTIFACT_KINDS - paths.keys()
    if missing:
        _fail(
            run.root_dir,
            "factor.artifacts",
            "Run does not declare the fixed Factor artifact set: "
            + ", ".join(sorted(missing)),
        )
    return paths, identities


def _read_csv(
    path: Path,
    *,
    columns: list[str],
    maximum_rows: int,
) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != columns:
                _fail(
                    path,
                    "factor.csv-columns",
                    "CSV columns must exactly match the fixed Factor contract",
                )
            rows: list[dict[str, str]] = []
            for row_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    _fail(
                        f"{path}:{row_number}",
                        "factor.csv-width",
                        "CSV row width must match its header",
                    )
                rows.append(row)
                if len(rows) > maximum_rows:
                    _fail(
                        path,
                        "factor.row-limit",
                        f"CSV exceeds the {maximum_rows}-row diagnostics limit",
                    )
    except UnicodeDecodeError:
        _fail(path, "factor.csv-encoding", "CSV must be UTF-8")
    if not rows:
        _fail(path, "factor.csv-empty", "CSV must contain data rows")
    return rows


def _split_protocol(metrics: dict[str, Any]) -> dict[str, Any]:
    protocol = metrics.get("split_protocol")
    if not isinstance(protocol, dict):
        _fail(
            "RunResult/metrics/split_protocol",
            "factor.split-protocol",
            "Factor Run is missing its fixed split protocol",
        )
    splits = protocol.get("splits")
    horizons = protocol.get("horizons")
    if (
        not isinstance(splits, dict)
        or set(splits) != set(SPLITS)
        or not isinstance(horizons, dict)
        or set(horizons) != {str(item) for item in HORIZONS}
    ):
        _fail(
            "RunResult/metrics/split_protocol",
            "factor.split-protocol",
            "Expected fixed train/validation/test and 1/5/10-bar protocol",
        )
    normalized_splits: dict[str, Any] = {}
    prior_end: str | None = None
    for split_name in SPLITS:
        raw = splits[split_name]
        if not isinstance(raw, dict):
            _fail(
                f"RunResult/metrics/split_protocol/splits/{split_name}",
                "factor.split-protocol",
                "Split protocol must be an object",
            )
        start = _session_date(raw.get("start"), f"{split_name}/start")
        end = _session_date(raw.get("end"), f"{split_name}/end")
        rows = _integer(raw.get("rows"), f"{split_name}/rows", minimum=1)
        if start > end or (prior_end is not None and start <= prior_end):
            _fail(
                f"RunResult/metrics/split_protocol/splits/{split_name}",
                "factor.split-order",
                "Factor splits must be strictly chronological",
            )
        normalized_splits[split_name] = {
            "start": start,
            "end": end,
            "rows": rows,
            "role": SPLIT_ROLES[split_name],
        }
        prior_end = end
    normalized_horizons: dict[str, Any] = {}
    for horizon in HORIZONS:
        raw_horizon = horizons[str(horizon)]
        if not isinstance(raw_horizon, dict) or set(raw_horizon) != set(SPLITS):
            _fail(
                f"RunResult/metrics/split_protocol/horizons/{horizon}",
                "factor.split-protocol",
                "Every horizon must declare all fixed splits",
            )
        normalized_horizons[str(horizon)] = {}
        for split_name in SPLITS:
            raw = raw_horizon[split_name]
            if not isinstance(raw, dict):
                _fail(
                    f"horizons/{horizon}/{split_name}",
                    "factor.split-protocol",
                    "Horizon split must be an object",
                )
            signal_start = _session_date(
                raw.get("signalStart"),
                f"horizons/{horizon}/{split_name}/signalStart",
            )
            signal_end = _session_date(
                raw.get("signalEnd"),
                f"horizons/{horizon}/{split_name}/signalEnd",
            )
            target_end = _session_date(
                raw.get("targetEnd"),
                f"horizons/{horizon}/{split_name}/targetEnd",
            )
            if not (
                normalized_splits[split_name]["start"]
                <= signal_start
                <= signal_end
                <= target_end
                <= normalized_splits[split_name]["end"]
            ):
                _fail(
                    f"horizons/{horizon}/{split_name}",
                    "factor.horizon-order",
                    "Purged horizon dates must stay inside their fixed split",
                )
            normalized_horizons[str(horizon)][split_name] = {
                "signalStart": signal_start,
                "signalEnd": signal_end,
                "targetEnd": target_end,
                "eligibleSignalRows": _integer(
                    raw.get("eligibleSignalRows"),
                    f"horizons/{horizon}/{split_name}/eligibleSignalRows",
                    minimum=1,
                ),
                "purgedBoundaryRows": _integer(
                    raw.get("purgedBoundaryRows"),
                    f"horizons/{horizon}/{split_name}/purgedBoundaryRows",
                    minimum=1,
                ),
                "role": SPLIT_ROLES[split_name],
            }
    return {
        "method": protocol.get("method"),
        "candidateDependent": protocol.get("candidateDependent"),
        "targetCrossesBoundary": protocol.get("targetCrossesBoundary"),
        "splits": normalized_splits,
        "horizons": normalized_horizons,
    }


@dataclass(frozen=True)
class ParsedDaily:
    dates: list[str]
    rows: list[dict[str, Any]]
    by_date: dict[str, dict[str, Any]]


def _parse_daily(
    path: Path,
    protocol: dict[str, Any],
) -> ParsedDaily:
    raw_rows = _read_csv(
        path,
        columns=DAILY_COLUMNS,
        maximum_rows=MAX_DAILY_ROWS,
    )
    rows: list[dict[str, Any]] = []
    prior: str | None = None
    split_positions: list[int] = []
    for row_number, raw in enumerate(raw_rows, start=2):
        row_path = f"{path}:{row_number}"
        timestamp = _session_date(raw["timestamp"], f"{row_path}/timestamp")
        if prior is not None and timestamp <= prior:
            _fail(
                row_path,
                "factor.daily-order",
                "Daily Factor timestamps must be unique and increasing",
            )
        split = raw["split"]
        if split not in SPLIT_ROLES:
            _fail(row_path, "factor.split", "Unknown Factor split")
        contract = protocol["splits"][split]
        if not contract["start"] <= timestamp <= contract["end"]:
            _fail(
                row_path,
                "factor.split-membership",
                "Daily split label contradicts the fixed split protocol",
            )
        regime = raw["regime"]
        if regime not in REGIMES:
            _fail(row_path, "factor.regime", "Unknown causal regime label")
        values = {
            f"{measure}IcH{horizon}": (
                None
                if raw[f"{measure}_ic_h{horizon}"] == ""
                else _bounded(
                    raw[f"{measure}_ic_h{horizon}"],
                    f"{row_path}/{measure}_ic_h{horizon}",
                    minimum=-1.0,
                    maximum=1.0,
                )
            )
            for horizon in HORIZONS
            for measure in ("rank", "pearson")
        }
        rows.append(
            {
                "timestamp": timestamp,
                "split": split,
                "role": SPLIT_ROLES[split],
                "regime": regime,
                **values,
            }
        )
        split_positions.append(SPLITS.index(split))
        prior = timestamp
    if split_positions != sorted(split_positions):
        _fail(path, "factor.split-order", "Daily split labels must be chronological")
    for split_name in SPLITS:
        observed = sum(row["split"] == split_name for row in rows)
        if observed != protocol["splits"][split_name]["rows"]:
            _fail(
                path,
                "factor.split-rows",
                f"Daily rows do not reconcile {split_name} split size",
            )
    return ParsedDaily(
        dates=[row["timestamp"] for row in rows],
        rows=rows,
        by_date={row["timestamp"]: row for row in rows},
    )


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _reconcile_daily(
    daily: ParsedDaily,
    metrics: dict[str, Any],
) -> None:
    quality = metrics.get("horizon_quality")
    if not isinstance(quality, dict) or set(quality) != {
        str(item) for item in HORIZONS
    }:
        _fail(
            "RunResult/metrics/horizon_quality",
            "factor.horizon-quality",
            "Factor Run must declare fixed 1/5/10-bar quality",
        )
    for horizon in HORIZONS:
        raw_horizon = quality[str(horizon)]
        if not isinstance(raw_horizon, dict) or set(raw_horizon) != set(SPLITS):
            _fail(
                f"RunResult/metrics/horizon_quality/{horizon}",
                "factor.horizon-quality",
                "Every horizon must declare all fixed splits",
            )
        for split_name in SPLITS:
            expected = raw_horizon[split_name]
            if not isinstance(expected, dict):
                _fail(
                    f"RunResult/metrics/horizon_quality/{horizon}/{split_name}",
                    "factor.horizon-quality",
                    "Horizon evidence must be an object",
                )
            rank = [
                row[f"rankIcH{horizon}"]
                for row in daily.rows
                if row["split"] == split_name
                and row[f"rankIcH{horizon}"] is not None
            ]
            pearson = [
                row[f"pearsonIcH{horizon}"]
                for row in daily.rows
                if row["split"] == split_name
                and row[f"pearsonIcH{horizon}"] is not None
            ]
            if len(rank) != expected.get("observations"):
                _fail(
                    f"{split_name}/{horizon}/rank",
                    "factor.reconciliation",
                    "Daily rank-IC observations do not reconcile Run metrics",
                )
            _close(
                _mean(rank),
                expected.get("mean_ic"),
                f"{split_name}/{horizon}/rank",
                "mean rank IC",
            )
            expected_pearson = expected.get("pearson_ic")
            if (
                not isinstance(expected_pearson, dict)
                or len(pearson) != expected_pearson.get("observations")
            ):
                _fail(
                    f"{split_name}/{horizon}/pearson",
                    "factor.reconciliation",
                    "Daily Pearson-IC observations do not reconcile Run metrics",
                )
            _close(
                _mean(pearson),
                expected_pearson.get("mean_ic"),
                f"{split_name}/{horizon}/pearson",
                "mean Pearson IC",
            )


def _parse_quantiles(
    path: Path,
    daily: ParsedDaily,
) -> list[dict[str, Any]]:
    raw_rows = _read_csv(
        path,
        columns=QUANTILE_COLUMNS,
        maximum_rows=MAX_QUANTILE_ROWS,
    )
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for row_number, raw in enumerate(raw_rows, start=2):
        row_path = f"{path}:{row_number}"
        timestamp = _session_date(raw["timestamp"], f"{row_path}/timestamp")
        daily_row = daily.by_date.get(timestamp)
        if daily_row is None:
            _fail(
                row_path,
                "factor.quantile-date",
                "Quantile timestamp is absent from daily Factor evidence",
            )
        split = raw["split"]
        if split != daily_row["split"]:
            _fail(
                row_path,
                "factor.quantile-split",
                "Quantile split contradicts daily Factor evidence",
            )
        try:
            horizon = int(raw["horizon"])
        except ValueError:
            _fail(row_path, "factor.quantile-horizon", "Invalid quantile horizon")
        if str(horizon) != raw["horizon"] or horizon not in HORIZONS:
            _fail(row_path, "factor.quantile-horizon", "Invalid quantile horizon")
        key = (timestamp, split, horizon)
        if key in seen:
            _fail(
                row_path,
                "factor.quantile-duplicate",
                "Quantile timestamp/split/horizon must be unique",
            )
        values = {
            label: _finite(raw[source], f"{row_path}/{source}")
            for label, source in (
                ("low", "low"),
                ("middle", "middle"),
                ("high", "high"),
                ("highMinusLow", "high_minus_low"),
            )
        }
        if not math.isclose(
            values["high"] - values["low"],
            values["highMinusLow"],
            rel_tol=1e-9,
            abs_tol=1e-10,
        ):
            _fail(
                row_path,
                "factor.quantile-spread",
                "Quantile high-minus-low does not reconcile group returns",
            )
        seen.add(key)
        rows.append(
            {
                "timestamp": timestamp,
                "split": split,
                "role": SPLIT_ROLES[split],
                "horizon": horizon,
                **values,
            }
        )
    return rows


def _average_ranks(values: list[float]) -> list[float]:
    result = [0.0] * len(values)
    order = sorted(range(len(values)), key=lambda index: values[index])
    position = 0
    while position < len(order):
        end = position + 1
        while end < len(order) and math.isclose(
            values[order[end]],
            values[order[position]],
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            end += 1
        rank = (position + end - 1) / 2.0
        for cursor in range(position, end):
            result[order[cursor]] = rank
        position = end
    return result


def _monotonicity(means: list[float]) -> float | None:
    ranks = _average_ranks(means)
    center_x = 1.0
    center_y = sum(ranks) / 3.0
    numerator = sum(
        (index - center_x) * (rank - center_y)
        for index, rank in enumerate(ranks)
    )
    left = sum((index - center_x) ** 2 for index in range(3))
    right = sum((rank - center_y) ** 2 for rank in ranks)
    denominator = math.sqrt(left * right)
    return numerator / denominator if denominator > 1e-15 else None


def _reconcile_quantiles(
    rows: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    analysis = metrics.get("quantile_analysis")
    if not isinstance(analysis, dict) or set(analysis) != {
        str(item) for item in HORIZONS
    }:
        _fail(
            "RunResult/metrics/quantile_analysis",
            "factor.quantiles",
            "Factor Run must declare fixed quantile analysis",
        )
    for horizon in HORIZONS:
        raw_horizon = analysis[str(horizon)]
        if not isinstance(raw_horizon, dict) or set(raw_horizon) != set(SPLITS):
            _fail(
                f"RunResult/metrics/quantile_analysis/{horizon}",
                "factor.quantiles",
                "Every quantile horizon must declare all fixed splits",
            )
        for split_name in SPLITS:
            selected = [
                row
                for row in rows
                if row["horizon"] == horizon and row["split"] == split_name
            ]
            expected = raw_horizon[split_name]
            if (
                not isinstance(expected, dict)
                or len(selected) != expected.get("observations")
            ):
                _fail(
                    f"quantiles/{horizon}/{split_name}",
                    "factor.reconciliation",
                    "Quantile observations do not reconcile Run metrics",
                )
            means = {
                label: _mean([row[label] for row in selected])
                for label in ("low", "middle", "high")
            }
            expected_means = expected.get("mean_return_by_quantile")
            if not isinstance(expected_means, dict):
                _fail(
                    f"quantiles/{horizon}/{split_name}",
                    "factor.quantiles",
                    "Quantile means must be an object",
                )
            for label in means:
                _close(
                    means[label],
                    expected_means.get(label),
                    f"quantiles/{horizon}/{split_name}/{label}",
                    f"mean {label} quantile return",
                )
            spread = _mean([row["highMinusLow"] for row in selected])
            _close(
                spread,
                expected.get("high_minus_low"),
                f"quantiles/{horizon}/{split_name}/spread",
                "mean high-minus-low spread",
            )
            monotonicity = (
                _monotonicity([means["low"], means["middle"], means["high"]])
                if all(value is not None for value in means.values())
                else None
            )
            _close(
                monotonicity,
                expected.get("monotonicity"),
                f"quantiles/{horizon}/{split_name}/monotonicity",
                "quantile monotonicity",
            )


def _rank_summary(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "factor.ic-summary", "IC summary must be an object")
    hac = value.get("hac")
    if not isinstance(hac, dict):
        _fail(path, "factor.ic-summary", "IC summary is incomplete")
    return {
        "meanRankIc": _optional_finite(value.get("mean_ic"), f"{path}/mean_ic"),
        "rankIcStandardDeviation": _optional_finite(
            value.get("standard_deviation"),
            f"{path}/standard_deviation",
        ),
        "rankIcir": _optional_finite(value.get("icir"), f"{path}/icir"),
        "rankHitRate": _optional_finite(
            value.get("hit_rate"),
            f"{path}/hit_rate",
        ),
        "observations": _integer(
            value.get("observations"),
            f"{path}/observations",
        ),
        "minimumObservations": _integer(
            value.get("minimum_observations"),
            f"{path}/minimum_observations",
            minimum=1,
        ),
        "sufficient": value.get("sufficient") is True,
        "hacTStatistic": _optional_finite(
            hac.get("t_statistic"),
            f"{path}/hac/t_statistic",
        ),
        "hacNormalPValue": _optional_finite(
            hac.get("normal_approximation_p_value"),
            f"{path}/hac/normal_approximation_p_value",
        ),
    }


def _ic_summary(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "factor.ic-summary", "IC summary must be an object")
    pearson = value.get("pearson_ic")
    if not isinstance(pearson, dict):
        _fail(path, "factor.ic-summary", "Pearson IC summary is incomplete")
    return {
        **_rank_summary(value, path),
        "meanPearsonIc": _optional_finite(
            pearson.get("mean_ic"),
            f"{path}/pearson_ic/mean_ic",
        ),
        "pearsonIcir": _optional_finite(
            pearson.get("icir"),
            f"{path}/pearson_ic/icir",
        ),
    }


def _summary(metrics: dict[str, Any]) -> dict[str, Any]:
    validation = _ic_summary(metrics.get("validation"), "metrics/validation")
    test = _ic_summary(metrics.get("test"), "metrics/test")
    folds = metrics.get("stability", {}).get("chronological_folds")
    styles = metrics.get("style_correlations", {}).get("validation")
    if not isinstance(folds, dict) or not isinstance(styles, dict):
        _fail(
            "RunResult/metrics",
            "factor.stability",
            "Factor Run is missing fold/style stability",
        )
    validation_folds = [
        (name, _optional_finite(value.get("mean_ic"), f"folds/{name}/mean_ic"))
        for name, value in folds.items()
        if name.startswith("validation_") and isinstance(value, dict)
    ]
    finite_folds = [
        (name, value) for name, value in validation_folds if value is not None
    ]
    worst_fold = min(finite_folds, key=lambda item: item[1]) if finite_folds else None
    style_values = [
        (
            name,
            _optional_finite(
                value.get("mean_rank_correlation"),
                f"styles/{name}/mean_rank_correlation",
            ),
        )
        for name, value in styles.items()
        if isinstance(value, dict)
    ]
    finite_styles = [
        (name, value) for name, value in style_values if value is not None
    ]
    maximum_style = (
        max(finite_styles, key=lambda item: abs(item[1]))
        if finite_styles
        else None
    )
    mean_coverage = _bounded(
        metrics.get("mean_coverage"),
        "metrics/mean_coverage",
        minimum=0.0,
        maximum=1.0,
    )
    mean_turnover = _bounded(
        metrics.get("mean_rank_turnover"),
        "metrics/mean_rank_turnover",
        minimum=0.0,
        maximum=1.0,
    )
    return {
        "validation": validation,
        "testAudit": test,
        "meanCoverage": mean_coverage,
        "meanRankTurnover": mean_turnover,
        "weakestValidationFold": (
            {"id": worst_fold[0], "meanRankIc": worst_fold[1]}
            if worst_fold
            else None
        ),
        "maximumValidationStyleOverlap": (
            {
                "style": maximum_style[0],
                "meanRankCorrelation": maximum_style[1],
                "absoluteMeanRankCorrelation": abs(maximum_style[1]),
            }
            if maximum_style
            else None
        ),
    }


def _horizon_profile(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    quality = metrics["horizon_quality"]
    return [
        {
            "horizon": horizon,
            **{
                split_name: {
                    **_ic_summary(
                        quality[str(horizon)][split_name],
                        f"metrics/horizon_quality/{horizon}/{split_name}",
                    ),
                    "role": SPLIT_ROLES[split_name],
                }
                for split_name in SPLITS
            },
        }
        for horizon in HORIZONS
    ]


def _quantile_summary(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    analysis = metrics["quantile_analysis"]
    for horizon in HORIZONS:
        for split_name in SPLITS:
            value = analysis[str(horizon)][split_name]
            means = value["mean_return_by_quantile"]
            output.append(
                {
                    "horizon": horizon,
                    "split": split_name,
                    "role": SPLIT_ROLES[split_name],
                    "low": _optional_finite(
                        means.get("low"),
                        f"quantiles/{horizon}/{split_name}/low",
                    ),
                    "middle": _optional_finite(
                        means.get("middle"),
                        f"quantiles/{horizon}/{split_name}/middle",
                    ),
                    "high": _optional_finite(
                        means.get("high"),
                        f"quantiles/{horizon}/{split_name}/high",
                    ),
                    "highMinusLow": _optional_finite(
                        value.get("high_minus_low"),
                        f"quantiles/{horizon}/{split_name}/spread",
                    ),
                    "monotonicity": _optional_finite(
                        value.get("monotonicity"),
                        f"quantiles/{horizon}/{split_name}/monotonicity",
                    ),
                    "observations": _integer(
                        value.get("observations"),
                        f"quantiles/{horizon}/{split_name}/observations",
                    ),
                }
            )
    return output


def _stability(metrics: dict[str, Any], universe: list[str]) -> dict[str, Any]:
    stability = metrics.get("stability")
    styles = metrics.get("style_correlations")
    if not isinstance(stability, dict) or not isinstance(styles, dict):
        _fail("RunResult/metrics", "factor.stability", "Missing stability evidence")
    folds = stability.get("chronological_folds")
    regimes = stability.get("causal_regimes")
    assets = stability.get("per_asset")
    if not all(isinstance(value, dict) for value in (folds, regimes, assets)):
        _fail("RunResult/metrics/stability", "factor.stability", "Invalid stability")
    expected_folds = {
        f"{split_name}_{number}"
        for split_name in SPLITS
        for number in (1, 2)
    }
    if set(folds) != expected_folds:
        _fail(
            "RunResult/metrics/stability/chronological_folds",
            "factor.stability-folds",
            "Expected exactly two chronological folds per split",
        )
    fold_rows = []
    for name, value in folds.items():
        if not isinstance(value, dict):
            _fail(f"stability/folds/{name}", "factor.stability", "Invalid fold")
        split_name = name.split("_", 1)[0]
        if split_name not in SPLIT_ROLES:
            _fail(f"stability/folds/{name}", "factor.stability", "Invalid fold split")
        fold_rows.append(
            {
                "id": name,
                "split": split_name,
                "role": SPLIT_ROLES[split_name],
                **_rank_summary(value, f"stability/folds/{name}"),
            }
        )
    regime_rows = []
    for split_name in SPLITS:
        split = regimes.get(split_name)
        if (
            not isinstance(split, dict)
            or set(split) != REGIMES - {"unavailable"}
        ):
            _fail(
                f"stability/regimes/{split_name}",
                "factor.stability",
                "Expected the complete fixed causal-regime dictionary",
            )
        for regime, value in split.items():
            if regime not in REGIMES - {"unavailable"} or not isinstance(value, dict):
                _fail(
                    f"stability/regimes/{split_name}/{regime}",
                    "factor.stability",
                    "Invalid regime evidence",
                )
            regime_rows.append(
                {
                    "split": split_name,
                    "role": SPLIT_ROLES[split_name],
                    "regime": regime,
                    **_rank_summary(
                        value,
                        f"stability/regimes/{split_name}/{regime}",
                    ),
                }
            )
    asset_rows = []
    for split_name in SPLITS:
        split = assets.get(split_name)
        if not isinstance(split, dict) or set(split) != set(universe):
            _fail(
                f"stability/assets/{split_name}",
                "factor.stability-universe",
                "Per-asset stability must match the Run universe",
            )
        for asset in universe:
            value = split[asset]
            if not isinstance(value, dict):
                _fail(
                    f"stability/assets/{split_name}/{asset}",
                    "factor.stability",
                    "Invalid per-asset evidence",
                )
            asset_rows.append(
                {
                    "split": split_name,
                    "role": SPLIT_ROLES[split_name],
                    "asset": asset,
                    "rankCorrelation": _optional_finite(
                        value.get("rank_correlation"),
                        f"stability/assets/{split_name}/{asset}/rank_correlation",
                    ),
                    "observations": _integer(
                        value.get("observations"),
                        f"stability/assets/{split_name}/{asset}/observations",
                    ),
                }
            )
    style_rows = []
    for split_name in SPLITS:
        split = styles.get(split_name)
        if not isinstance(split, dict) or set(split) != STYLES:
            _fail(
                f"styles/{split_name}",
                "factor.styles",
                "Expected the complete fixed style-overlap dictionary",
            )
        for style, value in split.items():
            if not isinstance(value, dict):
                _fail(f"styles/{split_name}/{style}", "factor.styles", "Invalid style")
            style_rows.append(
                {
                    "split": split_name,
                    "role": SPLIT_ROLES[split_name],
                    "style": style,
                    "meanRankCorrelation": _optional_finite(
                        value.get("mean_rank_correlation"),
                        f"styles/{split_name}/{style}/mean_rank_correlation",
                    ),
                    "meanAbsoluteRankCorrelation": _optional_finite(
                        value.get("mean_absolute_rank_correlation"),
                        f"styles/{split_name}/{style}/mean_absolute_rank_correlation",
                    ),
                    "observations": _integer(
                        value.get("observations"),
                        f"styles/{split_name}/{style}/observations",
                    ),
                }
            )
    return {
        "chronologicalFolds": fold_rows,
        "causalRegimes": regime_rows,
        "assets": asset_rows,
        "styles": style_rows,
    }


def _sample_indices(
    total: int,
    limit: int,
    required: set[int],
    preferred: set[int],
) -> list[int]:
    if total <= limit:
        return list(range(total))
    selected = {index for index in required if 0 <= index < total}
    if len(selected) > limit:
        _fail(
            "factor sampling",
            "factor.sample-limit",
            "Point limit is smaller than required Factor anchors",
        )
    preferred_candidates = sorted(
        index
        for index in preferred
        if 0 <= index < total and index not in selected
    )
    preferred_slots = min(limit - len(selected), len(preferred_candidates))
    if preferred_slots and preferred_slots < len(preferred_candidates):
        positions = {
            round(
                position
                * (len(preferred_candidates) - 1)
                / max(1, preferred_slots - 1)
            )
            for position in range(preferred_slots)
        }
        selected.update(preferred_candidates[position] for position in positions)
    else:
        selected.update(preferred_candidates[:preferred_slots])
    candidates = [index for index in range(total) if index not in selected]
    slots = limit - len(selected)
    if slots >= len(candidates):
        selected.update(candidates)
    elif slots == 1:
        selected.add(candidates[len(candidates) // 2])
    elif slots > 1:
        positions = {
            round(position * (len(candidates) - 1) / (slots - 1))
            for position in range(slots)
        }
        selected.update(candidates[position] for position in positions)
        if len(selected) < limit:
            selected.update(candidates[: limit - len(selected)])
    return sorted(selected)


def _paths(
    daily: ParsedDaily,
    quantiles: list[dict[str, Any]],
    point_limit: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    required = {0, len(daily.rows) - 1}
    preferred: set[int] = set()
    maximum = max(
        range(len(daily.rows)),
        key=lambda index: abs(daily.rows[index]["rankIcH1"] or 0.0),
    )
    required.add(maximum)
    for index in range(1, len(daily.rows)):
        before = daily.rows[index - 1]
        current = daily.rows[index]
        if before["split"] != current["split"]:
            required.update({index - 1, index})
        if before["regime"] != current["regime"]:
            preferred.update({index - 1, index})
    selected = _sample_indices(
        len(daily.rows),
        point_limit,
        required,
        preferred,
    )
    selected_dates = {daily.dates[index] for index in selected}
    ic_path = {
        "totalRows": len(daily.rows),
        "sampledRows": len(selected),
        "pointLimit": point_limit,
        "sampling": "deterministic-even-with-split-regime-extreme-anchors",
        "points": [daily.rows[index] for index in selected],
    }
    quantile_points = [
        row for row in quantiles if row["timestamp"] in selected_dates
    ]
    return ic_path, {
        "totalRows": len(quantiles),
        "sampledRows": len(quantile_points),
        "timestampAnchors": len(selected_dates),
        "sampling": "aligned-to-ic-path-timestamps",
        "points": quantile_points,
    }


def _coverage(report: dict[str, Any], universe: list[str]) -> list[dict[str, Any]]:
    coverage = report.get("coverageByAsset")
    if not isinstance(coverage, dict) or set(coverage) != set(universe):
        _fail(
            "factor-report/coverageByAsset",
            "factor.coverage-universe",
            "Factor coverage must exactly match the Run universe",
        )
    return [
        {
            "asset": asset,
            "coverage": _bounded(
                coverage[asset],
                f"factor-report/coverageByAsset/{asset}",
                minimum=0.0,
                maximum=1.0,
            ),
        }
        for asset in universe
    ]


def load_factor_diagnostics(
    project: ProjectContext,
    run_id: str,
    *,
    point_limit: int = DEFAULT_FACTOR_POINTS,
) -> dict[str, Any]:
    """Verify and project one immutable Factor Run into a bounded read model."""

    if (
        not isinstance(point_limit, int)
        or isinstance(point_limit, bool)
        or not MIN_FACTOR_POINTS <= point_limit <= MAX_FACTOR_POINTS
    ):
        _fail(
            point_limit,
            "factor.point-limit",
            f"point_limit must be {MIN_FACTOR_POINTS}..{MAX_FACTOR_POINTS}",
        )
    run = load_run(project, run_id)
    if run.result["objective"]["metric"] != "validation_mean_ic":
        _fail(
            run.root_dir,
            "factor.run-kind",
            "Run is not a fixed Factor Lab evaluation",
        )
    universe = run.result["dataset"].get("universe")
    if (
        not isinstance(universe, list)
        or not universe
        or len(universe) > MAX_UNIVERSE
        or not all(isinstance(asset, str) and asset for asset in universe)
        or len(universe) != len(set(universe))
    ):
        _fail(
            run.root_dir,
            "factor.universe",
            f"Factor universe must contain 1..{MAX_UNIVERSE} unique assets",
        )
    paths, artifacts = _artifact_paths(run)
    try:
        report = json.loads(paths["factor-report"].read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail(
            paths["factor-report"],
            "factor.report-json",
            "Factor report must be one UTF-8 JSON object",
        )
    if not isinstance(report, dict):
        _fail(paths["factor-report"], "factor.report-json", "Report must be an object")
    if report.get("inputHash") != run.result["inputHash"]:
        _fail(
            paths["factor-report"],
            "factor.report-identity",
            "Factor report input identity differs from RunResult",
        )
    if report.get("metrics") != run.result["metrics"]:
        _fail(
            paths["factor-report"],
            "factor.report-metrics",
            "Factor report metrics differ from immutable RunResult",
        )
    report_dataset = report.get("dataset")
    if (
        not isinstance(report_dataset, dict)
        or report_dataset.get("universe") != universe
        or report_dataset.get("id") != run.result["dataset"].get("id")
        or report_dataset.get("version") != run.result["dataset"].get("version")
    ):
        _fail(
            paths["factor-report"],
            "factor.report-dataset",
            "Factor report dataset differs from immutable RunResult",
        )
    metrics = run.result["metrics"]
    protocol = _split_protocol(metrics)
    daily = _parse_daily(paths["factor-daily"], protocol)
    _reconcile_daily(daily, metrics)
    quantiles = _parse_quantiles(paths["factor-quantiles"], daily)
    _reconcile_quantiles(quantiles, metrics)
    ic_path, quantile_path = _paths(daily, quantiles, point_limit)
    semantics = report.get("semantics")
    declared_styles = (
        semantics.get("styles") if isinstance(semantics, dict) else None
    )
    if (
        not isinstance(semantics, dict)
        or semantics.get("horizons") != list(HORIZONS)
        or not isinstance(declared_styles, list)
        or set(declared_styles) != STYLES
    ):
        _fail(
            paths["factor-report"],
            "factor.report-semantics",
            "Factor report must declare the fixed horizon and style semantics",
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": FACTOR_DIAGNOSTICS_KIND,
        "run": {
            "id": run.result["id"],
            "status": run.result["status"],
            "summary": run.result["summary"],
            "startedAt": run.result["startedAt"],
            "completedAt": run.result["completedAt"],
            "inputHash": run.result["inputHash"],
            "studyId": run.result["study"]["id"],
            "studyHash": run.result["study"]["hash"],
            "sourceHash": run.result["subject"]["sourceHash"],
            "objective": run.result["objective"],
        },
        "dataset": {
            "id": run.result["dataset"]["id"],
            "version": run.result["dataset"]["version"],
            "hash": run.result["dataset"]["hash"],
            "timeRange": run.result["dataset"]["time_range"],
            "universe": universe,
        },
        "harness": run.result["harness"],
        "artifacts": artifacts,
        "protocol": {
            "selectionSplit": "validation",
            "testRole": "visible-diagnostic",
            "testEntersSelection": False,
            "horizons": list(HORIZONS),
            "semantics": semantics,
            "splits": protocol,
        },
        "summary": _summary(metrics),
        "horizonProfile": _horizon_profile(metrics),
        "quantileSummary": _quantile_summary(metrics),
        "stability": _stability(metrics, universe),
        "coverage": _coverage(report, universe),
        "icPath": ic_path,
        "quantilePath": quantile_path,
        "warning": (
            "Validation one-bar rank IC is the fixed selection objective. "
            "Test, longer-horizon, quantile, stability, and style evidence are "
            "diagnostic and do not change the immutable verdict."
        ),
    }


FACTOR_DIAGNOSTICS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant bounded Factor diagnostics",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "run",
        "dataset",
        "harness",
        "artifacts",
        "protocol",
        "summary",
        "horizonProfile",
        "quantileSummary",
        "stability",
        "coverage",
        "icPath",
        "quantilePath",
        "warning",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": FACTOR_DIAGNOSTICS_KIND},
        "run": {"type": "object"},
        "dataset": {
            "type": "object",
            "required": ["id", "version", "hash", "timeRange", "universe"],
        },
        "harness": {"type": "object"},
        "artifacts": {
            "type": "object",
            "required": sorted(EXPECTED_ARTIFACT_KINDS),
        },
        "protocol": {
            "type": "object",
            "required": [
                "selectionSplit",
                "testRole",
                "testEntersSelection",
                "horizons",
                "semantics",
                "splits",
            ],
            "properties": {
                "selectionSplit": {"const": "validation"},
                "testRole": {"const": "visible-diagnostic"},
                "testEntersSelection": {"const": False},
                "horizons": {
                    "type": "array",
                    "prefixItems": [
                        {"const": 1},
                        {"const": 5},
                        {"const": 10},
                    ],
                    "items": False,
                },
                "semantics": {"type": "object"},
                "splits": {"type": "object"},
            },
        },
        "summary": {"type": "object"},
        "horizonProfile": {
            "type": "array",
            "minItems": len(HORIZONS),
            "maxItems": len(HORIZONS),
        },
        "quantileSummary": {
            "type": "array",
            "minItems": len(HORIZONS) * len(SPLITS),
            "maxItems": len(HORIZONS) * len(SPLITS),
        },
        "stability": {"type": "object"},
        "coverage": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_UNIVERSE,
        },
        "icPath": {
            "type": "object",
            "required": [
                "totalRows",
                "sampledRows",
                "pointLimit",
                "sampling",
                "points",
            ],
            "properties": {
                "totalRows": {"type": "integer", "minimum": 1},
                "sampledRows": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_FACTOR_POINTS,
                },
                "pointLimit": {
                    "type": "integer",
                    "minimum": MIN_FACTOR_POINTS,
                    "maximum": MAX_FACTOR_POINTS,
                },
                "sampling": {"type": "string"},
                "points": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_FACTOR_POINTS,
                },
            },
        },
        "quantilePath": {
            "type": "object",
            "required": [
                "totalRows",
                "sampledRows",
                "timestampAnchors",
                "sampling",
                "points",
            ],
        },
        "warning": {"type": "string", "minLength": 1},
    },
}
