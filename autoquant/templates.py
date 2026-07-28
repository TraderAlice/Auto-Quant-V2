"""Self-contained Project construction templates."""

from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from .checks import PREFLIGHT_KIND, PREFLIGHT_MANIFEST
from .factor_claims import (
    FACTOR_CLAIM,
    build_factor_claim,
    known_style_candidate_source,
)
from .horizons import (
    RESEARCH_HORIZON,
    build_research_horizon,
)
from .mandates import (
    PORTFOLIO_MANDATE,
    build_portfolio_mandate,
)
from .position_snapshots import (
    POSITION_SNAPSHOT,
    build_position_snapshot,
)
from .studies import (
    StudyContext,
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
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
)

if TYPE_CHECKING:
    from .intake import PreparedIntake


PROJECT_TEMPLATE_IDS = (
    "blank",
    "ohlcv-factor-lab",
    "ohlcv-portfolio-lab",
    "ohlcv-rl-factor-lab",
    "ohlcv-book-risk-lab",
    "ohlcv-research-desk",
)
OHLCV_STUDY_ID = "ohlcv-factor-quality"
PORTFOLIO_STUDY_ID = "ohlcv-portfolio-quality"
RL_STUDY_ID = "ohlcv-rl-factor-policy"
BOOK_RISK_STUDY_ID = "ohlcv-book-risk"
TEMPLATE_STUDY_IDS = {
    "ohlcv-factor-lab": OHLCV_STUDY_ID,
    "ohlcv-portfolio-lab": PORTFOLIO_STUDY_ID,
    "ohlcv-rl-factor-lab": RL_STUDY_ID,
    "ohlcv-book-risk-lab": BOOK_RISK_STUDY_ID,
    "ohlcv-research-desk": OHLCV_STUDY_ID,
}
TEMPLATE_STUDY_SEQUENCES = {
    "ohlcv-factor-lab": (OHLCV_STUDY_ID,),
    "ohlcv-portfolio-lab": (PORTFOLIO_STUDY_ID,),
    "ohlcv-rl-factor-lab": (RL_STUDY_ID,),
    "ohlcv-book-risk-lab": (BOOK_RISK_STUDY_ID,),
    "ohlcv-research-desk": (
        OHLCV_STUDY_ID,
        PORTFOLIO_STUDY_ID,
        RL_STUDY_ID,
    ),
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


def _write_preflight_source(project: ProjectContext, lane: str) -> str:
    relative = f"judges/preflight_{lane}.py"
    path = project.root_dir / relative
    path.write_text(
        _template_text(f"{lane}.py", template="preflight"),
        encoding="utf-8",
    )
    return relative


def _write_preflight_manifest(
    study: StudyContext,
    *,
    entrypoint: str,
    timeout_seconds: int = 8,
) -> None:
    value = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": PREFLIGHT_KIND,
        "runner": {
            "kind": "python",
            "entrypoint": entrypoint,
            "paths": [entrypoint],
            "arguments": [],
            "timeoutSeconds": timeout_seconds,
        },
    }
    (study.root_dir / PREFLIGHT_MANIFEST).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def _write_portfolio_mandate(
    project: ProjectContext,
    intake: PreparedIntake | None,
    universe: list[str],
) -> dict[str, object]:
    mandate = build_portfolio_mandate(
        intake.request if intake is not None else None,
        universe,
        annualization_periods=(
            intake.annualization_periods if intake is not None else 252
        ),
    )
    (project.root_dir / PORTFOLIO_MANDATE).write_text(
        json.dumps(mandate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return mandate


def _write_research_horizon(
    project: ProjectContext,
    intake: PreparedIntake | None,
) -> dict[str, object]:
    horizon = build_research_horizon(
        intake.request if intake is not None else None
    )
    (project.root_dir / RESEARCH_HORIZON).write_text(
        json.dumps(horizon, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return horizon


def _write_factor_claim(
    project: ProjectContext,
    intake: PreparedIntake | None,
) -> dict[str, object]:
    claim = build_factor_claim(
        intake.request if intake is not None else None
    )
    (project.root_dir / FACTOR_CLAIM).write_text(
        json.dumps(claim, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return claim


def _write_position_snapshot(
    project: ProjectContext,
    request: dict[str, object],
) -> dict[str, object]:
    snapshot = build_position_snapshot(request)
    (project.root_dir / POSITION_SNAPSHOT).write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return snapshot


def _seed_known_style_candidate(
    project: ProjectContext,
    intake: PreparedIntake | None,
) -> None:
    if intake is None:
        return
    source = known_style_candidate_source(intake.request)
    if source is not None:
        (project.root_dir / "factors" / "candidate.py").write_text(
            source,
            encoding="utf-8",
        )


def _intake_dataset(
    project: ProjectContext,
    intake: PreparedIntake,
    study_id: str,
) -> tuple[str, dict[str, object], str]:
    from .intake import materialize_intake_dataset

    _, snapshot_hash = materialize_intake_dataset(project, intake, study_id)
    return (
        intake.end,
        {
            "id": intake.package["id"],
            "version": intake.package["version"],
            "asset_class": intake.package["assetClass"],
            "universe": intake.universe,
            "start": intake.start,
        },
        snapshot_hash,
    )


def _time_range_value(value: date | str) -> str:
    return value if isinstance(value, str) else value.isoformat()


def _finalize_intake(
    project: ProjectContext,
    intake: PreparedIntake | None,
    study,
    snapshot_hash: str | None,
) -> None:
    if intake is None:
        return
    from .intake import finalize_project_intake

    assert snapshot_hash is not None
    finalize_project_intake(project, intake, study, snapshot_hash)


def _externalize_intake_guidance(
    project: ProjectContext,
    intake: PreparedIntake | None,
    program_path: Path,
) -> None:
    if intake is None:
        return
    replacements = {
        (
            "Do not modify the Study, Judge, program, dataset, or AutoQuant "
            "Core to improve a\ncandidate. Do not treat this synthetic "
            "benchmark as a real-market alpha claim."
        ): (
            "Do not modify the Study, Judge, program, dataset, or AutoQuant "
            "Core to improve a\ncandidate. These historical provider-supplied "
            "bars are research evidence, not proof of\nfuture alpha."
        ),
        (
            "This is a synthetic bar-target-weight simulation, not an L2 fill "
            "model, order\ninstruction, or live-trading recommendation."
        ): (
            "This is a historical bar-target-weight simulation, not an L2 fill "
            "model, order\ninstruction, or live-trading recommendation."
        ),
        (
            "The checked-in construction recipe\ngenerates a small "
            "deterministic synthetic fixture; it is a Harness benchmark,\nnot "
            "evidence about real markets."
        ): (
            "This Project was transactionally constructed from a caller-"
            "supplied, content-locked\ndaily OHLCV snapshot. Provider, "
            "calendar, and price-adjustment metadata are\ndisclosed claims, "
            "not authenticated by AutoQuant."
        ),
    }
    disclosure = (
        "\n\n## External dataset authority\n\n"
        f"- Dataset: `{intake.package['id']}@{intake.package['version']}`\n"
        f"- Research universe: {', '.join(intake.universe)}\n"
        f"- Coverage: `{intake.start}` through `{intake.end}`\n"
        f"- Provider claim: `{intake.package['provider']['name']}`\n"
        f"- Adjustment claim: `{intake.package['priceAdjustment']}`\n\n"
        "The Study hashes canonical Project-local bytes. Do not add newer rows "
        "or replace the\nsnapshot during one Session; create a new intake/"
        "Study identity for a fresh holdout.\n"
    )
    for path in (
        project.root_dir / project.manifest.research_program,
        program_path,
    ):
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        if "## External dataset authority" not in text:
            text = text.rstrip() + disclosure
        path.write_text(text, encoding="utf-8")


def _apply_ohlcv_factor_lab(
    project: ProjectContext,
    intake: PreparedIntake | None = None,
) -> None:
    if intake is None:
        end = _write_demo_ohlcv(project)
        dataset = {
            "id": "synthetic-ohlcv-factor-fixture",
            "version": "v1",
            "asset_class": "synthetic-multi-asset",
            "universe": list(OHLCV_ASSETS),
            "start": OHLCV_START.isoformat(),
        }
        snapshot_hash = None
    else:
        end, dataset, snapshot_hash = _intake_dataset(
            project,
            intake,
            OHLCV_STUDY_ID,
        )
    _write_research_horizon(project, intake)
    _write_factor_claim(project, intake)
    _write_portfolio_mandate(
        project,
        intake,
        list(dataset["universe"]),
    )
    _write_template_source(project, "factors/candidate.py", "candidate.py")
    _seed_known_style_candidate(project, intake)
    _write_template_source(project, "judges/ohlcv_factor.py", "judge.py")
    _write_template_source(
        project,
        "judges/factor_diagnostics.py",
        "factor_diagnostics.py",
    )
    preflight_entrypoint = _write_preflight_source(project, "factor")
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
            if intake is None
            else "Mine a causal cross-sectional factor on a content-locked market snapshot"
        ),
        program="program.md",
        subject=StudySubject("factor", "candidate-factor", "working"),
        editable={"paths": ["factors/**"]},
        judge=StudyJudge(
            "python",
            "judges/ohlcv_factor.py",
            [
                "judges/ohlcv_factor.py",
                "judges/factor_diagnostics.py",
            ],
            [],
            60,
        ),
        objective=StudyObjective("validation_mean_ic", "maximize", 0.01),
        dataset=StudyDataset(
            str(dataset["id"]),
            str(dataset["version"]),
            str(dataset["asset_class"]),
            list(dataset["universe"]),
            StudyTimeRange(str(dataset["start"]), _time_range_value(end)),
            ["ohlcv/**"],
        ),
        dependencies={
            "paths": [
                FACTOR_CLAIM,
                PORTFOLIO_MANDATE,
                RESEARCH_HORIZON,
            ]
        },
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md"),
        encoding="utf-8",
    )
    _write_preflight_manifest(study, entrypoint=preflight_entrypoint)
    _externalize_intake_guidance(project, intake, study.program_path)
    study = load_study(project, OHLCV_STUDY_ID)
    _finalize_intake(project, intake, study, snapshot_hash)


def _apply_ohlcv_portfolio_lab(
    project: ProjectContext,
    intake: PreparedIntake | None = None,
) -> None:
    template = "ohlcv_portfolio_lab"
    if intake is None:
        end = _write_demo_ohlcv(project, readme_template=template)
        dataset = {
            "id": "synthetic-ohlcv-portfolio-fixture",
            "version": "v1",
            "asset_class": "synthetic-multi-asset",
            "universe": list(OHLCV_ASSETS),
            "start": OHLCV_START.isoformat(),
        }
        snapshot_hash = None
    else:
        end, dataset, snapshot_hash = _intake_dataset(
            project,
            intake,
            PORTFOLIO_STUDY_ID,
        )
    _write_portfolio_mandate(
        project,
        intake,
        list(dataset["universe"]),
    )
    _write_research_horizon(project, intake)
    _write_template_source(
        project,
        "factors/candidate.py",
        "candidate.py",
        template=template,
    )
    _seed_known_style_candidate(project, intake)
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
    preflight_entrypoint = _write_preflight_source(project, "factor")
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
            [
                "judges/ohlcv_portfolio.py",
                "judges/portfolio_core.py",
            ],
            [],
            180,
        ),
        objective=StudyObjective("validation_net_sharpe", "maximize", 0.05),
        dataset=StudyDataset(
            str(dataset["id"]),
            str(dataset["version"]),
            str(dataset["asset_class"]),
            list(dataset["universe"]),
            StudyTimeRange(str(dataset["start"]), _time_range_value(end)),
            ["ohlcv/**"],
        ),
        dependencies={
            "paths": [PORTFOLIO_MANDATE, RESEARCH_HORIZON]
        },
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md", template=template),
        encoding="utf-8",
    )
    _write_preflight_manifest(study, entrypoint=preflight_entrypoint)
    _externalize_intake_guidance(project, intake, study.program_path)
    study = load_study(project, PORTFOLIO_STUDY_ID)
    _finalize_intake(project, intake, study, snapshot_hash)


def _apply_ohlcv_rl_factor_lab(
    project: ProjectContext,
    intake: PreparedIntake | None = None,
) -> None:
    template = "ohlcv_rl_factor_lab"
    if intake is None:
        end = _write_rl_ohlcv(project)
        dataset = {
            "id": "synthetic-ohlcv-rl-regime-fixture",
            "version": "v1",
            "asset_class": "synthetic-multi-asset",
            "universe": list(OHLCV_ASSETS),
            "start": OHLCV_START.isoformat(),
        }
        snapshot_hash = None
    else:
        end, dataset, snapshot_hash = _intake_dataset(
            project,
            intake,
            RL_STUDY_ID,
        )
    _write_portfolio_mandate(
        project,
        intake,
        list(dataset["universe"]),
    )
    _write_research_horizon(project, intake)
    _write_template_source(
        project,
        "models/candidate.py",
        "candidate.py",
        template=template,
    )
    _write_template_source(
        project,
        "factors/candidate.py",
        "candidate.py",
        template="ohlcv_portfolio_lab",
    )
    _seed_known_style_candidate(project, intake)
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
    preflight_entrypoint = _write_preflight_source(project, "rl")
    (project.root_dir / project.manifest.research_program).write_text(
        _template_text("research.md", template=template),
        encoding="utf-8",
    )
    definition = StudyDefinition(
        schema_version=1,
        id=RL_STUDY_ID,
        name="Governed RL Factor Policy",
        description=(
            "Test causal state representations across a locked candidate "
            "factor and fixed reference sleeves"
        ),
        program="program.md",
        subject=StudySubject("model", "rl-state-encoder", "working"),
        editable={"paths": ["models/**"]},
        judge=StudyJudge(
            "python",
            "judges/ohlcv_rl_factor.py",
            [
                "judges/ohlcv_rl_factor.py",
                "judges/rl_core.py",
                "judges/portfolio_core.py",
            ],
            [],
            90,
        ),
        objective=StudyObjective(
            "validation_mean_net_sharpe",
            "maximize",
            0.20,
        ),
        dataset=StudyDataset(
            str(dataset["id"]),
            str(dataset["version"]),
            str(dataset["asset_class"]),
            list(dataset["universe"]),
            StudyTimeRange(str(dataset["start"]), _time_range_value(end)),
            ["ohlcv/**"],
        ),
        dependencies={
            "paths": [
                "factors/**",
                PORTFOLIO_MANDATE,
                RESEARCH_HORIZON,
            ]
        },
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md", template=template),
        encoding="utf-8",
    )
    _write_preflight_manifest(study, entrypoint=preflight_entrypoint)
    _externalize_intake_guidance(project, intake, study.program_path)
    study = load_study(project, RL_STUDY_ID)
    _finalize_intake(project, intake, study, snapshot_hash)


def _apply_ohlcv_book_risk_lab(
    project: ProjectContext,
    intake: PreparedIntake | None = None,
) -> None:
    """Create a fixed reported-book and supplied-scenario covariance audit."""

    template = "ohlcv_book_risk_lab"
    if intake is None:
        end = _write_demo_ohlcv(project, readme_template=template)
        dataset = {
            "id": "synthetic-ohlcv-book-risk-fixture",
            "version": "v1",
            "asset_class": "synthetic-multi-asset",
            "universe": list(OHLCV_ASSETS),
            "start": OHLCV_START.isoformat(),
        }
        snapshot_hash = None
        request = {
            "schemaVersion": 1,
            "kind": "autoquant-research-request",
            "title": "Synthetic reported-book risk audit",
            "question": (
                "How concentrated is the reported model book and which "
                "one-percent reduction most reduces covariance risk?"
            ),
            "decisionContext": (
                "Harness fixture for a non-authenticated reported weight snapshot."
            ),
            "assets": [
                {
                    "symbol": asset,
                    "assetClass": "other",
                    "venue": None,
                    "positionRole": (
                        "long-only"
                        if asset in OHLCV_ASSETS[:4]
                        else "context-only"
                    ),
                }
                for asset in OHLCV_ASSETS
            ],
            "direction": "research-only",
            "positionSnapshot": {
                "kind": "hypothetical-weights",
                "asOf": f"{_time_range_value(end)}T00:00:00Z",
                "baseCurrency": "USD",
                "weights": {
                    asset: 0.25 for asset in OHLCV_ASSETS[:4]
                },
                "cashWeight": 0.0,
            },
            "horizon": "Current covariance state through the final closed bar.",
            "hypotheses": [
                "The reported assets share materially overlapping risk."
            ],
            "constraints": [
                "No Broker, account reconciliation, or order authority."
            ],
            "deliverables": [
                "Risk contribution, effective-risk-bet, and reduction evidence."
            ],
            "source": {
                "system": "local",
                "workspaceId": None,
                "sessionId": None,
                "artifactPath": None,
                "artifactRevision": None,
            },
        }
        (project.root_dir / "request.json").write_text(
            json.dumps(request, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        if intake.request.get("positionSnapshot") is None:
            raise AutoQuantValidationError(
                [
                    _issue(
                        "request/positionSnapshot",
                        "request.position-snapshot-required",
                        "ohlcv-book-risk-lab requires one explicit reported "
                        "or hypothetical position snapshot",
                    )
                ]
            )
        end, dataset, snapshot_hash = _intake_dataset(
            project,
            intake,
            BOOK_RISK_STUDY_ID,
        )
        request = intake.request
    _write_position_snapshot(project, request)
    _write_template_source(
        project,
        "strategies/book-risk-scenarios.json",
        "scenarios.json",
        template=template,
    )
    _write_template_source(
        project,
        "judges/ohlcv_book_risk.py",
        "judge.py",
        template=template,
    )
    (project.root_dir / project.manifest.research_program).write_text(
        _template_text("research.md", template=template),
        encoding="utf-8",
    )
    definition = StudyDefinition(
        schema_version=1,
        id=BOOK_RISK_STUDY_ID,
        name="OHLCV Reported Book Risk",
        description=(
            "Audit one explicit reported book plus any caller-supplied "
            "complete scenarios under one fixed covariance model"
        ),
        program="program.md",
        subject=StudySubject("research", "reported-book-risk", "working"),
        editable={"paths": ["strategies/book-risk-scenarios.json"]},
        judge=StudyJudge(
            "python",
            "judges/ohlcv_book_risk.py",
            ["judges/ohlcv_book_risk.py"],
            [],
            30,
        ),
        objective=StudyObjective(
            "current_component_risk_hhi",
            "minimize",
            0.01,
        ),
        dataset=StudyDataset(
            str(dataset["id"]),
            str(dataset["version"]),
            str(dataset["asset_class"]),
            list(dataset["universe"]),
            StudyTimeRange(str(dataset["start"]), _time_range_value(end)),
            ["ohlcv/**"],
        ),
        dependencies={"paths": [POSITION_SNAPSHOT]},
    )
    study = create_study(project, definition)
    study.program_path.write_text(
        _template_text("program.md", template=template),
        encoding="utf-8",
    )
    _externalize_intake_guidance(project, intake, study.program_path)
    study = load_study(project, BOOK_RISK_STUDY_ID)
    _finalize_intake(project, intake, study, snapshot_hash)


def _apply_ohlcv_research_desk(
    project: ProjectContext,
    intake: PreparedIntake | None = None,
) -> None:
    """Create one shared-data Project with Factor, Portfolio, and RL Studies."""

    if intake is None:
        end = _write_rl_ohlcv(project)
        dataset = {
            "id": "synthetic-ohlcv-research-desk-fixture",
            "version": "v1",
            "asset_class": "synthetic-multi-asset",
            "universe": list(OHLCV_ASSETS),
            "start": OHLCV_START.isoformat(),
        }
        snapshot_hash = None
    else:
        end, dataset, snapshot_hash = _intake_dataset(
            project,
            intake,
            OHLCV_STUDY_ID,
        )
    _write_portfolio_mandate(
        project,
        intake,
        list(dataset["universe"]),
    )
    _write_research_horizon(project, intake)
    _write_factor_claim(project, intake)

    # Write every fixed/editable source before creating any Study identity.
    _write_template_source(
        project,
        "factors/candidate.py",
        "candidate.py",
        template="ohlcv_portfolio_lab",
    )
    _seed_known_style_candidate(project, intake)
    _write_template_source(
        project,
        "models/candidate.py",
        "candidate.py",
        template="ohlcv_rl_factor_lab",
    )
    _write_template_source(
        project,
        "judges/ohlcv_factor.py",
        "judge.py",
        template="ohlcv_factor_lab",
    )
    _write_template_source(
        project,
        "judges/factor_diagnostics.py",
        "factor_diagnostics.py",
        template="ohlcv_factor_lab",
    )
    _write_template_source(
        project,
        "judges/ohlcv_portfolio.py",
        "judge.py",
        template="ohlcv_portfolio_lab",
    )
    _write_template_source(
        project,
        "judges/portfolio_core.py",
        "portfolio_core.py",
        template="ohlcv_portfolio_lab",
    )
    _write_template_source(
        project,
        "judges/ohlcv_rl_factor.py",
        "judge.py",
        template="ohlcv_rl_factor_lab",
    )
    _write_template_source(
        project,
        "judges/rl_core.py",
        "rl_core.py",
        template="ohlcv_rl_factor_lab",
    )
    factor_preflight = _write_preflight_source(project, "factor")
    rl_preflight = _write_preflight_source(project, "rl")
    (project.root_dir / project.manifest.research_program).write_text(
        _template_text("research.md", template="ohlcv_research_desk"),
        encoding="utf-8",
    )

    shared_dataset = StudyDataset(
        str(dataset["id"]),
        str(dataset["version"]),
        str(dataset["asset_class"]),
        list(dataset["universe"]),
        StudyTimeRange(str(dataset["start"]), _time_range_value(end)),
        ["ohlcv/**"],
    )
    definitions = (
        (
            StudyDefinition(
                schema_version=1,
                id=OHLCV_STUDY_ID,
                name="OHLCV Factor Quality",
                description="Mine causal factor evidence on the shared research snapshot",
                program="program.md",
                subject=StudySubject("factor", "candidate-factor", "working"),
                editable={"paths": ["factors/**"]},
                judge=StudyJudge(
                    "python",
                    "judges/ohlcv_factor.py",
                    [
                        "judges/ohlcv_factor.py",
                        "judges/factor_diagnostics.py",
                    ],
                    [],
                    60,
                ),
                objective=StudyObjective(
                    "validation_mean_ic",
                    "maximize",
                    0.01,
                ),
                dataset=shared_dataset,
                dependencies={
                    "paths": [
                        FACTOR_CLAIM,
                        PORTFOLIO_MANDATE,
                        RESEARCH_HORIZON,
                    ]
                },
            ),
            "ohlcv_factor_lab",
        ),
        (
            StudyDefinition(
                schema_version=1,
                id=PORTFOLIO_STUDY_ID,
                name="OHLCV Portfolio Quality",
                description=(
                    "Translate the shared candidate factor into constrained, "
                    "costed target weights"
                ),
                program="program.md",
                subject=StudySubject("factor", "portfolio-factor", "working"),
                editable={"paths": ["factors/**"]},
                judge=StudyJudge(
                    "python",
                    "judges/ohlcv_portfolio.py",
                    [
                        "judges/ohlcv_portfolio.py",
                        "judges/portfolio_core.py",
                    ],
                    [],
                    180,
                ),
                objective=StudyObjective(
                    "validation_net_sharpe",
                    "maximize",
                    0.05,
                ),
                dataset=shared_dataset,
                dependencies={
                    "paths": [PORTFOLIO_MANDATE, RESEARCH_HORIZON]
                },
            ),
            "ohlcv_portfolio_lab",
        ),
        (
            StudyDefinition(
                schema_version=1,
                id=RL_STUDY_ID,
                name="Governed RL Factor Policy",
                description=(
                    "Challenge a locked candidate factor and fixed reference "
                    "sleeves with a bounded adaptive state representation"
                ),
                program="program.md",
                subject=StudySubject("model", "rl-state-encoder", "working"),
                editable={"paths": ["models/**"]},
                judge=StudyJudge(
                    "python",
                    "judges/ohlcv_rl_factor.py",
                    [
                        "judges/ohlcv_rl_factor.py",
                        "judges/rl_core.py",
                        "judges/portfolio_core.py",
                    ],
                    [],
                    90,
                ),
                objective=StudyObjective(
                    "validation_mean_net_sharpe",
                    "maximize",
                    0.20,
                ),
                dataset=shared_dataset,
                dependencies={
                    "paths": [
                        "factors/**",
                        PORTFOLIO_MANDATE,
                        RESEARCH_HORIZON,
                    ]
                },
            ),
            "ohlcv_rl_factor_lab",
        ),
    )
    studies = []
    for definition, source_template in definitions:
        study = create_study(project, definition)
        study.program_path.write_text(
            _template_text("program.md", template=source_template),
            encoding="utf-8",
        )
        _write_preflight_manifest(
            study,
            entrypoint=(
                rl_preflight
                if definition.id == RL_STUDY_ID
                else factor_preflight
            ),
        )
        _externalize_intake_guidance(project, intake, study.program_path)
        studies.append(load_study(project, definition.id))

    _finalize_intake(project, intake, studies[0], snapshot_hash)
    from .research_program import create_research_program_manifest

    create_research_program_manifest(project)


def apply_project_template(
    project: ProjectContext,
    template_id: str,
    *,
    intake: PreparedIntake | None = None,
) -> None:
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
        if intake is not None:
            raise AutoQuantValidationError(
                [
                    _issue(
                        template_id,
                        "intake.template",
                        "Blank Projects cannot receive OHLCV intake",
                    )
                ]
            )
        return
    if template_id == "ohlcv-factor-lab":
        _apply_ohlcv_factor_lab(project, intake)
    elif template_id == "ohlcv-portfolio-lab":
        _apply_ohlcv_portfolio_lab(project, intake)
    elif template_id == "ohlcv-rl-factor-lab":
        _apply_ohlcv_rl_factor_lab(project, intake)
    elif template_id == "ohlcv-book-risk-lab":
        _apply_ohlcv_book_risk_lab(project, intake)
    else:
        _apply_ohlcv_research_desk(project, intake)
