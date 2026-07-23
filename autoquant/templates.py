"""Self-contained Project construction templates."""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from importlib import resources
from pathlib import Path

from .studies import (
    StudyDataset,
    StudyDefinition,
    StudyJudge,
    StudyObjective,
    StudySubject,
    StudyTimeRange,
    create_study,
    load_study,
)
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
)


PROJECT_TEMPLATE_IDS = ("blank", "ohlcv-factor-lab")
OHLCV_STUDY_ID = "ohlcv-factor-quality"
OHLCV_ASSETS = ("ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT")
OHLCV_START = date(2024, 1, 2)
OHLCV_OBSERVATIONS = 320


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _template_text(relative: str) -> str:
    source = (
        resources.files("autoquant")
        .joinpath("project_templates")
        .joinpath("ohlcv_factor_lab")
        .joinpath(relative)
    )
    return source.read_text(encoding="utf-8")


def _business_dates(start: date, observations: int) -> list[date]:
    result: list[date] = []
    current = start
    while len(result) < observations:
        if current.weekday() < 5:
            result.append(current)
        current += timedelta(days=1)
    return result


def _write_demo_ohlcv(project: ProjectContext) -> date:
    """Generate a small causal multi-asset fixture without external downloads."""

    output = project.root_dir / project.manifest.directories["data"] / "ohlcv"
    output.mkdir()
    dates = _business_dates(OHLCV_START, OHLCV_OBSERVATIONS)
    random_source = random.Random(20260724)
    closes = {
        asset: 70.0 + 13.0 * index
        for index, asset in enumerate(OHLCV_ASSETS)
    }
    prior_signals = {asset: 0.0 for asset in OHLCV_ASSETS}
    rows = {asset: [] for asset in OHLCV_ASSETS}

    for step, timestamp in enumerate(dates):
        raw_signals = {
            asset: random_source.gauss(0.0, 1.0)
            + 0.35 * math.sin(step / 9.0 + index * 0.8)
            for index, asset in enumerate(OHLCV_ASSETS)
        }
        mean_signal = sum(raw_signals.values()) / len(raw_signals)
        current_signals = {
            asset: value - mean_signal for asset, value in raw_signals.items()
        }
        market_return = 0.00015 + 0.0025 * math.sin(step / 31.0)
        for index, asset in enumerate(OHLCV_ASSETS):
            previous_close = closes[asset]
            overnight = random_source.gauss(0.0, 0.0015)
            open_price = previous_close * math.exp(overnight)
            close_return = (
                market_return
                + 0.010 * prior_signals[asset]
                + random_source.gauss(0.0, 0.004)
            )
            close_price = previous_close * math.exp(close_return)
            spread = abs(random_source.gauss(0.005, 0.0015))
            high = max(open_price, close_price) * (1.0 + spread)
            low = min(open_price, close_price) * (1.0 - spread)
            base_volume = 900_000.0 * (1.0 + index * 0.22)
            volume = base_volume * math.exp(
                0.55 * current_signals[asset]
                + 0.08 * math.sin(step / 17.0 + index)
            )
            rows[asset].append(
                [
                    timestamp.isoformat(),
                    f"{open_price:.8f}",
                    f"{high:.8f}",
                    f"{low:.8f}",
                    f"{close_price:.8f}",
                    f"{volume:.2f}",
                ]
            )
            closes[asset] = close_price
        prior_signals = current_signals

    for asset in OHLCV_ASSETS:
        with (output / f"{asset}.csv").open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            writer.writerows(rows[asset])
    (output / "README.md").write_text(
        _template_text("data-readme.md"),
        encoding="utf-8",
    )
    return dates[-1]


def _write_template_source(project: ProjectContext, relative: str, source: str) -> None:
    target = project.root_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_template_text(source), encoding="utf-8")


def _apply_ohlcv_factor_lab(project: ProjectContext) -> None:
    end = _write_demo_ohlcv(project)
    _write_template_source(project, "factors/candidate.py", "candidate.py")
    _write_template_source(project, "judges/ohlcv_factor.py", "judge.py")
    (project.root_dir / project.manifest.research_program).write_text(
        _template_text("research.md"),
        encoding="utf-8",
    )
    definition = StudyDefinition(
        schema_version=1,
        id=OHLCV_STUDY_ID,
        name="OHLCV Factor Quality",
        description=(
            "Mine a causal cross-sectional factor on a fixed synthetic OHLCV fixture"
        ),
        program="program.md",
        subject=StudySubject("factor", "candidate-factor", "working"),
        editable={"paths": ["factors/**"]},
        judge=StudyJudge(
            "python",
            "judges/ohlcv_factor.py",
            ["judges/**"],
            [],
            10,
        ),
        objective=StudyObjective("score", "maximize", 0.01),
        dataset=StudyDataset(
            "synthetic-ohlcv-factor-fixture",
            "v1",
            "synthetic-multi-asset",
            list(OHLCV_ASSETS),
            StudyTimeRange(OHLCV_START.isoformat(), end.isoformat()),
            ["ohlcv/**"],
        ),
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md"),
        encoding="utf-8",
    )
    load_study(project, OHLCV_STUDY_ID)


def apply_project_template(project: ProjectContext, template_id: str) -> None:
    if template_id not in PROJECT_TEMPLATE_IDS:
        raise AutoQuantValidationError(
            [
                _issue(
                    template_id,
                    "project.template",
                    "Unknown Project template. Expected one of: "
                    + ", ".join(PROJECT_TEMPLATE_IDS),
                )
            ]
        )
    if template_id == "blank":
        return
    _apply_ohlcv_factor_lab(project)
