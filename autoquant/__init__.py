"""Auto-Quant harness primitives.

The autonomous research loop still lives in ``program.md``.  This package
contains the stable, non-strategy parts that make the loop portable across
asset profiles.
"""

from .profiles import AssetProfile, HarnessInterfaces, HarnessManifest, load_manifest
from .workspace import (
    PROJECT_MANIFEST,
    WORKSPACE_MANIFEST,
    ProjectContext,
    ProjectManifest,
    WorkspaceContext,
    WorkspaceManifest,
    create_project,
    initialize_workspace,
    list_workspace_projects,
    resolve_project_directory,
)

__all__ = [
    "AssetProfile",
    "HarnessInterfaces",
    "HarnessManifest",
    "PROJECT_MANIFEST",
    "ProjectContext",
    "ProjectManifest",
    "WORKSPACE_MANIFEST",
    "WorkspaceContext",
    "WorkspaceManifest",
    "create_project",
    "initialize_workspace",
    "list_workspace_projects",
    "load_manifest",
    "resolve_project_directory",
]
