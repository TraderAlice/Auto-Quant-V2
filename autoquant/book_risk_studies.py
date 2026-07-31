"""Append independently fixed Book Risk Studies to an existing Project."""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .briefs import load_research_request
from .intake import PROJECT_REQUEST, load_project_intake
from .position_snapshots import (
    build_position_snapshot,
    validate_position_snapshot,
)
from .studies import (
    STUDY_ID,
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
    confined_path,
)


BOOK_RISK_TEMPLATE = "ohlcv-book-risk-lab"
BOOK_RISK_STUDY_SOURCES = "strategies/book-risk-studies"
BOOK_RISK_STUDY_JUDGES = "judges/book-risk-studies"
DEFAULT_METHOD = "strategies/book-risk-scenarios.json"


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _book_risk_judge_source() -> bytes:
    return (
        Path(__file__).parent
        / "project_templates"
        / "ohlcv_book_risk_lab"
        / "judge.py"
    ).read_bytes()


def _same_dataset_request(
    request: dict[str, Any],
    original_request: dict[str, Any],
    primary: StudyContext,
    request_path: Path,
) -> None:
    issues: list[ValidationIssue] = []
    if request["assets"] != original_request["assets"]:
        issues.append(
            _issue(
                f"{request_path}/assets",
                "study-intake.dataset-assets",
                "A same-Project Book Risk Study must preserve the original "
                "request asset descriptions exactly; acquire a task-complete "
                "new Project dataset when the universe or roles differ",
            )
        )
    snapshot = request.get("positionSnapshot")
    if not isinstance(snapshot, dict):
        issues.append(
            _issue(
                f"{request_path}/positionSnapshot",
                "request.position-snapshot-required",
                "Book Risk Study intake requires one explicit positionSnapshot",
            )
        )
    else:
        try:
            as_of = datetime.fromisoformat(
                snapshot["asOf"].replace("Z", "+00:00")
            )
            if len(primary.definition.dataset.time_range.start) == 10:
                as_of = as_of.date()
                start = date.fromisoformat(
                    primary.definition.dataset.time_range.start
                )
                end = date.fromisoformat(
                    primary.definition.dataset.time_range.end
                )
            else:
                start = datetime.fromisoformat(
                    primary.definition.dataset.time_range.start.replace(
                        "Z", "+00:00"
                    )
                )
                end = datetime.fromisoformat(
                    primary.definition.dataset.time_range.end.replace(
                        "Z", "+00:00"
                    )
                )
            if not start <= as_of <= end:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            issues.append(
                _issue(
                    f"{request_path}/positionSnapshot/asOf",
                    "study-intake.dataset-range",
                    "Position snapshot asOf must lie inside the retained "
                    "content-locked Study dataset range",
                )
            )
    if issues:
        raise AutoQuantValidationError(issues)


def create_book_risk_study_intake(
    project: ProjectContext,
    study_id: str,
    request_path: str | Path,
    *,
    name: str | None = None,
) -> tuple[StudyContext, dict[str, Any]]:
    """Add one request-owned fixed Book Risk Study over the retained dataset."""

    if not STUDY_ID.fullmatch(study_id):
        raise AutoQuantValidationError(
            [
                _issue(
                    study_id,
                    "schema.id",
                    "Study id must use lowercase kebab-case",
                )
            ]
        )
    intake = load_project_intake(project)
    if intake is None or intake["manifest"]["template"] != BOOK_RISK_TEMPLATE:
        raise AutoQuantValidationError(
            [
                _issue(
                    project.root_dir,
                    "study-intake.project-template",
                    "Book Risk Study intake requires an existing request-bound "
                    "ohlcv-book-risk-lab Project",
                )
            ]
        )
    primary = load_study(project, intake["manifest"]["studyId"])
    raw_request_path = Path(request_path).expanduser().absolute()
    if raw_request_path.is_symlink():
        raise AutoQuantValidationError(
            [
                _issue(
                    raw_request_path,
                    "path.symlink",
                    "Research Request cannot be a symlink",
                )
            ]
        )
    request = load_research_request(raw_request_path)
    original_request = load_research_request(project.root_dir / PROJECT_REQUEST)
    _same_dataset_request(
        request,
        original_request,
        primary,
        raw_request_path,
    )
    position_snapshot = build_position_snapshot(request)
    validate_position_snapshot(position_snapshot, raw_request_path)

    source_relative = f"{BOOK_RISK_STUDY_SOURCES}/{study_id}"
    judge_relative = f"{BOOK_RISK_STUDY_JUDGES}/{study_id}"
    source_root = confined_path(project.root_dir, source_relative, source_relative)
    judge_root = confined_path(project.root_dir, judge_relative, judge_relative)
    study_root = confined_path(
        project.root_dir / project.manifest.directories["studies"],
        study_id,
        f"study/{study_id}",
    )
    occupied = [
        path
        for path in (source_root, judge_root, study_root)
        if path.exists() or path.is_symlink()
    ]
    if occupied:
        raise AutoQuantValidationError(
            [
                _issue(
                    occupied[0],
                    "study.exists",
                    f"Study-owned path already exists: {occupied[0]}",
                )
            ]
        )

    request_relative = f"{source_relative}/request.json"
    snapshot_relative = f"{source_relative}/position-snapshot.json"
    method_relative = f"{source_relative}/book-risk-scenarios.json"
    entrypoint_relative = f"{judge_relative}/judge.py"
    method_source = confined_path(project.root_dir, DEFAULT_METHOD, DEFAULT_METHOD)
    if method_source.is_symlink() or not method_source.is_file():
        raise AutoQuantValidationError(
            [
                _issue(
                    method_source,
                    "study-intake.method",
                    "The retained Book Risk method must be a real file",
                )
            ]
        )

    try:
        source_root.mkdir(parents=True)
        judge_root.mkdir(parents=True)
        _write_json(project.root_dir / request_relative, request)
        _write_json(project.root_dir / snapshot_relative, position_snapshot)
        (project.root_dir / method_relative).write_bytes(method_source.read_bytes())
        (project.root_dir / entrypoint_relative).write_bytes(
            _book_risk_judge_source()
        )
        definition = StudyDefinition(
            schema_version=SCHEMA_VERSION,
            id=study_id,
            name=name or request["title"],
            description=request["question"],
            program="program.md",
            subject=StudySubject(
                "research",
                "reported-book-risk",
                "working",
            ),
            editable={"paths": []},
            judge=StudyJudge(
                "python",
                entrypoint_relative,
                [entrypoint_relative],
                [
                    "--position-snapshot",
                    snapshot_relative,
                    "--scenarios",
                    method_relative,
                ],
                30,
            ),
            objective=StudyObjective(
                "current_component_risk_hhi",
                "minimize",
                0.01,
            ),
            dataset=StudyDataset(
                primary.definition.dataset.id,
                primary.definition.dataset.version,
                primary.definition.dataset.asset_class,
                list(primary.definition.dataset.universe),
                StudyTimeRange(
                    primary.definition.dataset.time_range.start,
                    primary.definition.dataset.time_range.end,
                ),
                (
                    list(primary.definition.dataset.paths)
                    if primary.definition.dataset.paths is not None
                    else None
                ),
            ),
            dependencies={
                "paths": [
                    request_relative,
                    snapshot_relative,
                    method_relative,
                ]
            },
        )
        study = create_study(project, definition)
        study.program_path.write_text(
            "# Fixed Book Risk follow-up\n\n"
            "This Study evaluates the canonical request, position snapshot, "
            "and covariance method bound in its fixed dependencies over the "
            "retained content-locked Project dataset. It has no editable "
            "candidate, selection loop, account, Order, or trading authority.\n",
            encoding="utf-8",
        )
        study = load_study(project, study_id)
    except Exception:
        if study_root.exists():
            shutil.rmtree(study_root)
        if source_root.exists():
            shutil.rmtree(source_root)
        if judge_root.exists():
            shutil.rmtree(judge_root)
        for parent in (source_root.parent, judge_root.parent):
            try:
                parent.rmdir()
            except OSError:
                pass
        raise

    return study, {
        "requestPath": request_relative,
        "requestHash": position_snapshot["source"]["requestHash"],
        "positionSnapshotPath": snapshot_relative,
        "positionSnapshotId": position_snapshot["id"],
        "methodPath": method_relative,
        "datasetHash": study.dataset_hash,
        "sourceProjectStudyId": primary.definition.id,
    }
