"""Workspace and self-contained Project boundaries for AutoQuant V2."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


WORKSPACE_MANIFEST = "autoquant-workspace.json"
PROJECT_MANIFEST = "autoquant.json"
SCHEMA_VERSION = 1
PROJECT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROJECT_DIRECTORY_KEYS = (
    "strategies",
    "factors",
    "models",
    "judges",
    "studies",
    "sessions",
    "data",
    "runs",
    "cache",
)
DEFAULT_PROJECT_DIRECTORIES = {
    "strategies": "strategies",
    "factors": "factors",
    "models": "models",
    "judges": "judges",
    "studies": "studies",
    "sessions": "sessions",
    "data": "data",
    "runs": "runs",
    "cache": ".autoquant",
}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class AutoQuantValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


@dataclass(frozen=True)
class WorkspaceManifest:
    schema_version: int
    name: str
    projects_directory: str
    default_project: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectManifest:
    schema_version: int
    id: str
    name: str
    description: str
    research_program: str
    directories: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkspaceContext:
    root_dir: Path
    manifest: WorkspaceManifest
    projects_dir: Path


@dataclass(frozen=True)
class ProjectContext:
    root_dir: Path
    manifest: ProjectManifest


@dataclass(frozen=True)
class ProjectSummary:
    id: str
    name: str
    description: str
    path: str
    is_default: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "isDefault": self.is_default,
        }


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AutoQuantValidationError(
            [_issue(path, "manifest.missing", f"Missing manifest: {path}")]
        ) from None
    except json.JSONDecodeError as error:
        raise AutoQuantValidationError(
            [
                _issue(
                    path,
                    "json.invalid",
                    f"Invalid JSON at line {error.lineno}, column {error.colno}: "
                    f"{error.msg}",
                )
            ]
        ) from None
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "schema.type", "Manifest root must be a JSON object")]
        )
    return value


def _strict_keys(
    raw: dict[str, Any],
    *,
    required: set[str],
    path: Path | str,
) -> list[ValidationIssue]:
    issues = [
        _issue(f"{path}/{key}", "schema.missing", f"Missing required field '{key}'")
        for key in sorted(required - raw.keys())
    ]
    issues.extend(
        _issue(f"{path}/{key}", "schema.unknown", f"Unknown field '{key}'")
        for key in sorted(raw.keys() - required)
    )
    return issues


def _valid_id(value: Any, path: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not PROJECT_ID.fullmatch(value):
        return [_issue(path, "schema.id", "Must be a lowercase kebab-case id")]
    return []


def _valid_non_empty_string(value: Any, path: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.strip():
        return [_issue(path, "schema.string", "Must be a non-empty string")]
    return []


def _valid_relative_path(value: Any, path: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value or "\\" in value:
        return [_issue(path, "schema.path", "Must be a confined POSIX relative path")]
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or value in {".", ".."} or ".." in candidate.parts:
        return [_issue(path, "schema.path", "Must be a confined POSIX relative path")]
    return []


def parse_workspace_manifest(raw: dict[str, Any], path: Path) -> WorkspaceManifest:
    required = {
        "schema_version",
        "name",
        "projects_directory",
        "default_project",
    }
    issues = _strict_keys(raw, required=required, path=path)
    if raw.get("schema_version") != SCHEMA_VERSION:
        issues.append(
            _issue(
                f"{path}/schema_version",
                "schema.version",
                f"Expected schema_version {SCHEMA_VERSION}",
            )
        )
    issues.extend(_valid_non_empty_string(raw.get("name"), f"{path}/name"))
    issues.extend(
        _valid_relative_path(
            raw.get("projects_directory"),
            f"{path}/projects_directory",
        )
    )
    default_project = raw.get("default_project")
    if default_project is not None:
        issues.extend(_valid_id(default_project, f"{path}/default_project"))
    if issues:
        raise AutoQuantValidationError(issues)
    return WorkspaceManifest(
        schema_version=SCHEMA_VERSION,
        name=raw["name"].strip(),
        projects_directory=raw["projects_directory"],
        default_project=default_project,
    )


def parse_project_manifest(raw: dict[str, Any], path: Path) -> ProjectManifest:
    required = {
        "schema_version",
        "id",
        "name",
        "description",
        "research_program",
        "directories",
    }
    issues = _strict_keys(raw, required=required, path=path)
    if raw.get("schema_version") != SCHEMA_VERSION:
        issues.append(
            _issue(
                f"{path}/schema_version",
                "schema.version",
                f"Expected schema_version {SCHEMA_VERSION}",
            )
        )
    issues.extend(_valid_id(raw.get("id"), f"{path}/id"))
    issues.extend(_valid_non_empty_string(raw.get("name"), f"{path}/name"))
    description = raw.get("description")
    if not isinstance(description, str):
        issues.append(
            _issue(f"{path}/description", "schema.string", "Must be a string")
        )
    issues.extend(
        _valid_relative_path(
            raw.get("research_program"),
            f"{path}/research_program",
        )
    )

    directories = raw.get("directories")
    if not isinstance(directories, dict):
        issues.append(
            _issue(
                f"{path}/directories",
                "schema.type",
                "Must be an object of Project-owned directory paths",
            )
        )
        directories = {}
    else:
        issues.extend(
            _strict_keys(
                directories,
                required=set(PROJECT_DIRECTORY_KEYS),
                path=f"{path}/directories",
            )
        )
        for key in PROJECT_DIRECTORY_KEYS:
            issues.extend(
                _valid_relative_path(
                    directories.get(key),
                    f"{path}/directories/{key}",
                )
            )
        paths = [
            directories[key]
            for key in PROJECT_DIRECTORY_KEYS
            if isinstance(directories.get(key), str)
        ]
        if len(paths) != len(set(paths)):
            issues.append(
                _issue(
                    f"{path}/directories",
                    "project.duplicate-directory",
                    "Project-owned directory paths must be unique",
                )
            )

    if issues:
        raise AutoQuantValidationError(issues)
    return ProjectManifest(
        schema_version=SCHEMA_VERSION,
        id=raw["id"],
        name=raw["name"].strip(),
        description=description,
        research_program=raw["research_program"],
        directories={key: directories[key] for key in PROJECT_DIRECTORY_KEYS},
    )


def _confined_path(root: Path, relative: str, issue_path: str) -> Path:
    raw_path = root / relative
    current = root
    for segment in PurePosixPath(relative).parts:
        current /= segment
        if current.is_symlink():
            raise AutoQuantValidationError(
                [
                    _issue(
                        issue_path,
                        "path.symlink",
                        f"Owned path components cannot be symlinks: {current}",
                    )
                ]
            )
    target = raw_path.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise AutoQuantValidationError(
            [_issue(issue_path, "path.escape", f"Path escapes its owner root: {relative}")]
        ) from None
    return target


def confined_path(root: Path, relative: str, issue_path: str) -> Path:
    """Resolve one owned relative path without following symlink components."""

    issues = _valid_relative_path(relative, issue_path)
    if issues:
        raise AutoQuantValidationError(issues)
    return _confined_path(root.resolve(), relative, issue_path)


def load_workspace(directory: str | Path) -> WorkspaceContext:
    root = Path(directory).expanduser().absolute()
    if root.is_symlink():
        raise AutoQuantValidationError(
            [_issue(root, "workspace.symlink", "Workspace root cannot be a symlink")]
        )
    root = root.resolve()
    manifest_path = root / WORKSPACE_MANIFEST
    manifest = parse_workspace_manifest(_read_json_object(manifest_path), manifest_path)
    projects_dir = _confined_path(
        root,
        manifest.projects_directory,
        f"{manifest_path}/projects_directory",
    )
    if not projects_dir.is_dir():
        raise AutoQuantValidationError(
            [
                _issue(
                    projects_dir,
                    "workspace.projects-directory",
                    f"Missing Workspace projects directory: {projects_dir}",
                )
            ]
        )
    return WorkspaceContext(root, manifest, projects_dir)


def load_project(directory: str | Path, *, expected_id: str | None = None) -> ProjectContext:
    raw_root = Path(directory).expanduser().absolute()
    if raw_root.is_symlink():
        raise AutoQuantValidationError(
            [_issue(raw_root, "project.symlink", "Project root cannot be a symlink")]
        )
    root = raw_root.resolve()
    manifest_path = root / PROJECT_MANIFEST
    manifest = parse_project_manifest(_read_json_object(manifest_path), manifest_path)
    directory_id = expected_id or root.name
    if manifest.id != directory_id:
        raise AutoQuantValidationError(
            [
                _issue(
                    f"{manifest_path}/id",
                    "project.directory-id",
                    f"Project id '{manifest.id}' must match directory '{directory_id}'",
                )
            ]
        )

    research_path = _confined_path(
        root,
        manifest.research_program,
        f"{manifest_path}/research_program",
    )
    issues: list[ValidationIssue] = []
    if not research_path.is_file():
        issues.append(
            _issue(
                research_path,
                "project.research-program",
                f"Missing Project research program: {research_path}",
            )
        )
    for key, relative in manifest.directories.items():
        directory_path = _confined_path(
            root,
            relative,
            f"{manifest_path}/directories/{key}",
        )
        if not directory_path.is_dir():
            issues.append(
                _issue(
                    directory_path,
                    "project.directory",
                    f"Missing Project-owned '{key}' directory: {directory_path}",
                )
            )
    if issues:
        raise AutoQuantValidationError(issues)
    return ProjectContext(root, manifest)


def list_workspace_projects(directory: str | Path) -> list[ProjectSummary]:
    workspace = load_workspace(directory)
    projects: list[ProjectSummary] = []
    issues: list[ValidationIssue] = []
    for entry in sorted(workspace.projects_dir.iterdir(), key=lambda path: path.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir():
            issues.append(
                _issue(
                    entry,
                    "workspace.project-entry",
                    "Workspace Project entries must be real directories",
                )
            )
            continue
        try:
            project = load_project(entry, expected_id=entry.name)
        except AutoQuantValidationError as error:
            issues.extend(error.issues)
            continue
        projects.append(
            ProjectSummary(
                id=project.manifest.id,
                name=project.manifest.name,
                description=project.manifest.description,
                path=str(project.root_dir),
                is_default=workspace.manifest.default_project == project.manifest.id,
            )
        )
    if workspace.manifest.default_project and not any(
        project.id == workspace.manifest.default_project for project in projects
    ):
        issues.append(
            _issue(
                f"{workspace.root_dir / WORKSPACE_MANIFEST}/default_project",
                "workspace.default-project",
                f"Default Project '{workspace.manifest.default_project}' does not exist",
            )
        )
    if issues:
        raise AutoQuantValidationError(issues)
    return projects


def resolve_project_directory(
    input_directory: str | Path,
    project_id: str | None = None,
) -> Path:
    raw_root = Path(input_directory).expanduser().absolute()
    if raw_root.is_symlink():
        raise AutoQuantValidationError(
            [_issue(raw_root, "path.symlink", "Input root cannot be a symlink")]
        )
    root = raw_root.resolve()
    has_project = (root / PROJECT_MANIFEST).is_file()
    has_workspace = (root / WORKSPACE_MANIFEST).is_file()
    if has_project and has_workspace:
        raise AutoQuantValidationError(
            [
                _issue(
                    root,
                    "path.ambiguous",
                    "Directory cannot be both an AutoQuant Project and Workspace",
                )
            ]
        )
    if has_project:
        if project_id is not None:
            raise AutoQuantValidationError(
                [
                    _issue(
                        root,
                        "project.unexpected-selection",
                        "--project cannot be used with a direct Project directory",
                    )
                ]
            )
        return load_project(root).root_dir
    if not has_workspace:
        raise AutoQuantValidationError(
            [
                _issue(
                    root,
                    "path.not-autoquant",
                    f"Not an AutoQuant Project or Workspace: {root}",
                )
            ]
        )

    workspace = load_workspace(root)
    selected = project_id or workspace.manifest.default_project
    if selected is None:
        raise AutoQuantValidationError(
            [
                _issue(
                    root / WORKSPACE_MANIFEST,
                    "workspace.selection-required",
                    "Workspace has no default Project; pass --project ID",
                )
            ]
        )
    projects = list_workspace_projects(root)
    project = next((item for item in projects if item.id == selected), None)
    if project is None:
        available = ", ".join(item.id for item in projects) or "none"
        raise AutoQuantValidationError(
            [
                _issue(
                    root / WORKSPACE_MANIFEST,
                    "workspace.unknown-project",
                    f"Unknown Workspace Project '{selected}'. Available: {available}",
                )
            ]
        )
    return Path(project.path)


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _require_empty_target(target: Path) -> None:
    if target.is_symlink():
        raise AutoQuantValidationError(
            [_issue(target, "path.symlink", "Target cannot be a symlink")]
        )
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise AutoQuantValidationError(
            [_issue(target, "path.not-empty", f"Target directory is not empty: {target}")]
        )


def initialize_workspace(
    directory: str | Path,
    *,
    name: str | None = None,
) -> WorkspaceContext:
    target = Path(directory).expanduser().absolute()
    _require_empty_target(target)
    target.mkdir(parents=True, exist_ok=True)
    manifest = WorkspaceManifest(
        schema_version=SCHEMA_VERSION,
        name=(name or target.name or "AutoQuant Workspace").strip(),
        projects_directory="projects",
        default_project=None,
    )
    if not manifest.name:
        raise AutoQuantValidationError(
            [_issue(target, "workspace.name", "Workspace name cannot be empty")]
        )
    (target / manifest.projects_directory).mkdir()
    _atomic_write_json(target / WORKSPACE_MANIFEST, manifest.to_dict())
    return load_workspace(target)


def _research_program(name: str, description: str) -> str:
    purpose = description.strip() or "Describe the quantitative research question here."
    return f"""# {name}

## Research brief and clarification

Before downloading data, editing research code, training a model, or running a
backtest, rewrite the assignment in this file as a bounded English research
brief. The caller may use any language; English is the internal working
language of the AutoQuant desk.

Use researcher judgment for methods, but do not invent caller-owned intent. If
an ambiguity could materially change the decision being supported, universe,
horizon or cadence, direction, risk constraints, benchmark, evaluation
meaning, or expected deliverable, record it under **Open questions** and ask
the delegating Agent or user. Repeat until the question is falsifiable and
safe to turn into fixed Study authority.

## Research question

{purpose}

## Decision context and motivation

Describe the decision this research should inform and why the answer matters.

## Scope, evidence, and constraints

Record the known asset scope, horizon or cadence, available data and evidence,
material constraints, evaluation meaning, and any relevant source context.

## Assumptions

Distinguish provisional researcher assumptions from confirmed caller intent.

## Open questions

Record material questions and their answers. Do not begin quantitative work
while a caller-owned ambiguity here could change the Study.

## Proposed bounded route

Describe the initial research approach, fast checks, evaluation boundary, and
the evidence needed to support or reject the hypothesis.

## Completion and deliverable

State what a useful answer should contain and who will consume it.

## Evidence contract

- Record the asset universe, dataset identity or time range, and Harness version.
- Keep evaluation inputs and acceptance criteria fixed while comparing candidates.
- Treat completed Runs as immutable evidence.
- Separate measured findings from forward-looking trading decisions.

## Agent instructions

Keep this brief current as the research evolves. Once it is clear enough to
start, work only inside this Project. Propose one falsifiable change at a time,
run the bounded Project evaluation contract, inspect structured evidence, and
KEEP, REVERT, or BRANCH explicitly. Do not change the Harness or locked Judge
to make a candidate win.
"""


def create_project(
    workspace_directory: str | Path,
    project_id: str,
    *,
    name: str | None = None,
    description: str = "",
    template: str = "blank",
    template_intake: Any | None = None,
) -> ProjectContext:
    from .templates import PROJECT_TEMPLATE_IDS

    if template not in PROJECT_TEMPLATE_IDS:
        raise AutoQuantValidationError(
            [
                _issue(
                    template,
                    "project.template",
                    "Unknown Project template. Expected one of: "
                    + ", ".join(PROJECT_TEMPLATE_IDS),
                )
            ]
        )
    id_issues = _valid_id(project_id, "project_id")
    if id_issues:
        raise AutoQuantValidationError(id_issues)
    workspace = load_workspace(workspace_directory)
    target = workspace.projects_dir / project_id
    if target.exists() or target.is_symlink():
        raise AutoQuantValidationError(
            [_issue(target, "project.exists", f"Project already exists: {target}")]
        )

    display_name = (name or project_id).strip()
    if not display_name:
        raise AutoQuantValidationError(
            [_issue("name", "schema.string", "Project name cannot be empty")]
        )
    manifest = ProjectManifest(
        schema_version=SCHEMA_VERSION,
        id=project_id,
        name=display_name,
        description=description,
        research_program="research.md",
        directories=dict(DEFAULT_PROJECT_DIRECTORIES),
    )
    temporary = workspace.projects_dir / f".{project_id}.creating"
    if temporary.exists():
        shutil.rmtree(temporary)
    try:
        temporary.mkdir()
        _atomic_write_json(temporary / PROJECT_MANIFEST, manifest.to_dict())
        (temporary / manifest.research_program).write_text(
            _research_program(display_name, description),
            encoding="utf-8",
        )
        for relative in manifest.directories.values():
            (temporary / relative).mkdir(parents=True)
        (temporary / manifest.directories["data"] / ".gitignore").write_text(
            "*\n!.gitignore\n",
            encoding="utf-8",
        )
        (temporary / manifest.directories["cache"] / ".gitignore").write_text(
            "*\n!.gitignore\n",
            encoding="utf-8",
        )
        if template != "blank":
            from .templates import apply_project_template

            staged = load_project(temporary, expected_id=project_id)
            apply_project_template(
                staged,
                template,
                intake=template_intake,
            )
        elif template_intake is not None:
            raise AutoQuantValidationError(
                [
                    _issue(
                        template,
                        "intake.template",
                        "Blank Projects cannot receive OHLCV intake",
                    )
                ]
            )
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    if workspace.manifest.default_project is None:
        updated = WorkspaceManifest(
            schema_version=workspace.manifest.schema_version,
            name=workspace.manifest.name,
            projects_directory=workspace.manifest.projects_directory,
            default_project=project_id,
        )
        _atomic_write_json(workspace.root_dir / WORKSPACE_MANIFEST, updated.to_dict())
    return load_project(target, expected_id=project_id)


def set_default_project(
    workspace_directory: str | Path,
    project_id: str,
) -> WorkspaceContext:
    workspace = load_workspace(workspace_directory)
    projects = list_workspace_projects(workspace.root_dir)
    if not any(project.id == project_id for project in projects):
        available = ", ".join(project.id for project in projects) or "none"
        raise AutoQuantValidationError(
            [
                _issue(
                    f"{workspace.root_dir / WORKSPACE_MANIFEST}/default_project",
                    "workspace.unknown-project",
                    f"Unknown Workspace Project '{project_id}'. Available: {available}",
                )
            ]
        )
    updated = WorkspaceManifest(
        schema_version=workspace.manifest.schema_version,
        name=workspace.manifest.name,
        projects_directory=workspace.manifest.projects_directory,
        default_project=project_id,
    )
    _atomic_write_json(workspace.root_dir / WORKSPACE_MANIFEST, updated.to_dict())
    return load_workspace(workspace.root_dir)


def inspect_project(project: ProjectContext) -> dict[str, Any]:
    directories: dict[str, dict[str, Any]] = {}
    for key, relative in project.manifest.directories.items():
        path = project.root_dir / relative
        entries = sorted(
            entry.name for entry in path.iterdir() if not entry.name.startswith(".")
        )
        directories[key] = {
            "path": str(path),
            "relativePath": relative,
            "entries": len(entries),
        }
    return {
        "project": {
            "id": project.manifest.id,
            "name": project.manifest.name,
            "description": project.manifest.description,
            "rootDir": str(project.root_dir),
        },
        "researchProgram": {
            "path": str(project.root_dir / project.manifest.research_program),
            "relativePath": project.manifest.research_program,
        },
        "directories": directories,
    }


WORKSPACE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant Workspace",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "name",
        "projects_directory",
        "default_project",
    ],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "name": {"type": "string", "minLength": 1},
        "projects_directory": {"type": "string", "minLength": 1},
        "default_project": {
            "anyOf": [
                {"type": "null"},
                {"type": "string", "pattern": PROJECT_ID.pattern},
            ]
        },
    },
}


PROJECT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant Project",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "id",
        "name",
        "description",
        "research_program",
        "directories",
    ],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "pattern": PROJECT_ID.pattern},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "research_program": {"type": "string", "minLength": 1},
        "directories": {
            "type": "object",
            "additionalProperties": False,
            "required": list(PROJECT_DIRECTORY_KEYS),
            "properties": {
                key: {"type": "string", "minLength": 1}
                for key in PROJECT_DIRECTORY_KEYS
            },
        },
    },
}


def schema_for(kind: str) -> dict[str, Any]:
    schemas = {"workspace": WORKSPACE_JSON_SCHEMA, "project": PROJECT_JSON_SCHEMA}
    try:
        return schemas[kind]
    except KeyError:
        raise AutoQuantValidationError(
            [
                _issue(
                    kind,
                    "schema.unknown-kind",
                    f"Unknown schema kind '{kind}'. Expected: "
                    f"{', '.join(sorted(schemas))}",
                )
            ]
        ) from None
