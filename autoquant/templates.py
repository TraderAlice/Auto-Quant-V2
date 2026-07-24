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


PROJECT_TEMPLATE_IDS = (
    "blank",
    "ohlcv-factor-lab",
    "ohlcv-portfolio-lab",
    "ohlcv-rl-factor-lab",
)
OHLCV_STUDY_ID = "ohlcv-factor-quality"
PORTFOLIO_STUDY_ID = "ohlcv-portfolio-quality"
RL_STUDY_ID = "ohlcv-rl-factor-policy"
TEMPLATE_STUDY_IDS = {
    "ohlcv-factor-lab": OHLCV_STUDY_ID,
    "ohlcv-portfolio-lab": PORTFOLIO_STUDY_ID,
    "ohlcv-rl-factor-lab": RL_STUDY_ID,
}
OHLCV_ASSETS = ("ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT")
OHLCV_START = date(2024, 1, 2)
OHLCV_OBSERVATIONS = 320
RL_OBSERVATIONS = 420


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _template_text(relative: str, *, template: str = "ohlcv_factor_lab") -> str:
    source = (
        resources.files("autoquant")
        .joinpath("project_templates")
        .joinpath(template)
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


def _write_demo_ohlcv(
    project: ProjectContext,
    *,
    readme_template: str = "ohlcv_factor_lab",
) -> date:
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
        _template_text("data-readme.md", template=readme_template),
        encoding="utf-8",
    )
    return dates[-1]


def _write_rl_ohlcv(project: ProjectContext) -> date:
    """Generate causal alternating regimes for bounded policy verification."""

    output = project.root_dir / project.manifest.directories["data"] / "ohlcv"
    output.mkdir()
    dates = _business_dates(OHLCV_START, RL_OBSERVATIONS)
    random_source = random.Random(20260725)
    closes = {
        asset: 80.0 + 11.0 * index
        for index, asset in enumerate(OHLCV_ASSETS)
    }
    prior_activity = {asset: 0.0 for asset in OHLCV_ASSETS}
    prior_intraday = {asset: 0.0 for asset in OHLCV_ASSETS}
    prior_regime = 1
    rows = {asset: [] for asset in OHLCV_ASSETS}

    for step, timestamp in enumerate(dates):
        regime = 1 if (step // 42) % 2 == 0 else -1
        activity_raw = {
            asset: random_source.gauss(0.0, 1.0)
            + 0.20 * math.sin(step / 8.0 + index)
            for index, asset in enumerate(OHLCV_ASSETS)
        }
        intraday_raw = {
            asset: random_source.gauss(0.0, 1.0)
            + 0.20 * math.cos(step / 11.0 + index * 0.7)
            for index, asset in enumerate(OHLCV_ASSETS)
        }
        activity_mean = sum(activity_raw.values()) / len(activity_raw)
        intraday_mean = sum(intraday_raw.values()) / len(intraday_raw)
        activity = {
            asset: value - activity_mean
            for asset, value in activity_raw.items()
        }
        intraday = {
            asset: value - intraday_mean
            for asset, value in intraday_raw.items()
        }
        market_return = 0.00010 + 0.0015 * math.sin(step / 37.0)
        for index, asset in enumerate(OHLCV_ASSETS):
            previous_close = closes[asset]
            selected_signal = (
                prior_activity[asset]
                if prior_regime > 0
                else prior_intraday[asset]
            )
            close_return = (
                market_return
                + 0.012 * selected_signal
                + random_source.gauss(0.0, 0.003)
            )
            close_price = previous_close * math.exp(close_return)
            open_price = close_price / math.exp(0.010 * intraday[asset])
            spread = 0.003 + abs(random_source.gauss(0.0, 0.001))
            high = max(open_price, close_price) * (1.0 + spread)
            low = min(open_price, close_price) * (1.0 - spread)
            base_volume = 850_000.0 * (1.0 + index * 0.18)
            volume = base_volume * math.exp(
                0.55 * regime + 0.50 * activity[asset]
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
        prior_activity = activity
        prior_intraday = intraday
        prior_regime = regime

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
        _template_text("data-readme.md", template="ohlcv_rl_factor_lab"),
        encoding="utf-8",
    )
    return dates[-1]


def _write_template_source(
    project: ProjectContext,
    relative: str,
    source: str,
    *,
    template: str = "ohlcv_factor_lab",
) -> None:
    target = project.root_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        _template_text(source, template=template),
        encoding="utf-8",
    )


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


def _apply_ohlcv_portfolio_lab(project: ProjectContext) -> None:
    template = "ohlcv_portfolio_lab"
    end = _write_demo_ohlcv(project, readme_template=template)
    _write_template_source(
        project,
        "factors/candidate.py",
        "candidate.py",
        template=template,
    )
    _write_template_source(
        project,
        "judges/ohlcv_portfolio.py",
        "judge.py",
        template=template,
    )
    _write_template_source(
        project,
        "judges/portfolio_core.py",
        "portfolio_core.py",
        template=template,
    )
    (project.root_dir / project.manifest.research_program).write_text(
        _template_text("research.md", template=template),
        encoding="utf-8",
    )
    definition = StudyDefinition(
        schema_version=1,
        id=PORTFOLIO_STUDY_ID,
        name="OHLCV Portfolio Quality",
        description=(
            "Translate a causal factor into constrained, costed target weights"
        ),
        program="program.md",
        subject=StudySubject("factor", "portfolio-factor", "working"),
        editable={"paths": ["factors/**"]},
        judge=StudyJudge(
            "python",
            "judges/ohlcv_portfolio.py",
            ["judges/**"],
            [],
            15,
        ),
        objective=StudyObjective("robust_net_sharpe", "maximize", 0.05),
        dataset=StudyDataset(
            "synthetic-ohlcv-portfolio-fixture",
            "v1",
            "synthetic-multi-asset",
            list(OHLCV_ASSETS),
            StudyTimeRange(OHLCV_START.isoformat(), end.isoformat()),
            ["ohlcv/**"],
        ),
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md", template=template),
        encoding="utf-8",
    )
    load_study(project, PORTFOLIO_STUDY_ID)


def _apply_ohlcv_rl_factor_lab(project: ProjectContext) -> None:
    template = "ohlcv_rl_factor_lab"
    end = _write_rl_ohlcv(project)
    _write_template_source(
        project,
        "models/candidate.py",
        "candidate.py",
        template=template,
    )
    _write_template_source(
        project,
        "judges/ohlcv_rl_factor.py",
        "judge.py",
        template=template,
    )
    _write_template_source(
        project,
        "judges/rl_core.py",
        "rl_core.py",
        template=template,
    )
    _write_template_source(
        project,
        "judges/portfolio_core.py",
        "portfolio_core.py",
        template="ohlcv_portfolio_lab",
    )
    (project.root_dir / project.manifest.research_program).write_text(
        _template_text("research.md", template=template),
        encoding="utf-8",
    )
    definition = StudyDefinition(
        schema_version=1,
        id=RL_STUDY_ID,
        name="Governed RL Factor Policy",
        description=(
            "Test causal state representations for a fixed factor-mixture policy"
        ),
        program="program.md",
        subject=StudySubject("model", "rl-state-encoder", "working"),
        editable={"paths": ["models/**"]},
        judge=StudyJudge(
            "python",
            "judges/ohlcv_rl_factor.py",
            ["judges/**"],
            [],
            45,
        ),
        objective=StudyObjective(
            "validation_mean_net_sharpe",
            "maximize",
            0.20,
        ),
        dataset=StudyDataset(
            "synthetic-ohlcv-rl-regime-fixture",
            "v1",
            "synthetic-multi-asset",
            list(OHLCV_ASSETS),
            StudyTimeRange(OHLCV_START.isoformat(), end.isoformat()),
            ["ohlcv/**"],
        ),
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md", template=template),
        encoding="utf-8",
    )
    load_study(project, RL_STUDY_ID)


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
    if template_id == "ohlcv-factor-lab":
        _apply_ohlcv_factor_lab(project)
    elif template_id == "ohlcv-portfolio-lab":
        _apply_ohlcv_portfolio_lab(project)
    else:
        _apply_ohlcv_rl_factor_lab(project)
