from __future__ import annotations

import json
import tempfile
import unittest
from importlib import resources
from pathlib import Path

from autoquant.templates import PROJECT_TEMPLATE_IDS
from autoquant.workspace import (
    PROJECT_MANIFEST,
    WORKSPACE_MANIFEST,
    AutoQuantValidationError,
    create_project,
    initialize_workspace,
    list_workspace_projects,
    load_project,
    load_workspace,
    resolve_project_directory,
    set_default_project,
)


class WorkspaceProjectTests(unittest.TestCase):
    def test_workspace_resolves_default_and_explicit_isolated_projects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(directory, name="Research Desk")
            first = create_project(
                workspace.root_dir,
                "factor-lab",
                name="Factor Lab",
                description="Mine robust factors",
            )
            second = create_project(workspace.root_dir, "ml-lab", name="ML Lab")

            projects = list_workspace_projects(workspace.root_dir)
            self.assertEqual([item.id for item in projects], ["factor-lab", "ml-lab"])
            self.assertTrue(projects[0].is_default)
            self.assertEqual(
                resolve_project_directory(workspace.root_dir),
                first.root_dir,
            )
            self.assertEqual(
                resolve_project_directory(workspace.root_dir, "ml-lab"),
                second.root_dir,
            )

            set_default_project(workspace.root_dir, "ml-lab")
            self.assertEqual(
                resolve_project_directory(workspace.root_dir),
                second.root_dir,
            )
            self.assertNotEqual(first.root_dir, second.root_dir)
            (first.root_dir / "factors" / "alpha.py").write_text("ALPHA = 1\n")
            self.assertFalse((second.root_dir / "factors" / "alpha.py").exists())

    def test_created_project_is_a_complete_self_contained_construction_site(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(directory)
            project = create_project(
                workspace.root_dir,
                "equity-research",
                description="Study session-market behavior",
            )

            self.assertTrue((project.root_dir / PROJECT_MANIFEST).is_file())
            self.assertIn(
                "Study session-market behavior",
                (project.root_dir / "research.md").read_text(),
            )
            research = (project.root_dir / "research.md").read_text()
            normalized_research = " ".join(research.split())
            self.assertIn("## Research brief and clarification", research)
            self.assertIn(
                "English is the internal working language of the AutoQuant desk",
                normalized_research,
            )
            self.assertIn(
                "ask the delegating Agent or user",
                normalized_research,
            )
            for relative in project.manifest.directories.values():
                self.assertTrue((project.root_dir / relative).is_dir(), relative)
            self.assertEqual(
                (project.root_dir / "data" / ".gitignore").read_text(),
                "*\n!.gitignore\n",
            )
            self.assertEqual(
                (project.root_dir / ".autoquant" / ".gitignore").read_text(),
                "*\n!.gitignore\n",
            )

    def test_every_builtin_template_requires_the_same_research_start_gate(
        self,
    ) -> None:
        template_root = resources.files("autoquant").joinpath("project_templates")
        for template in PROJECT_TEMPLATE_IDS:
            if template == "blank":
                continue
            with self.subTest(template=template):
                research = (
                    template_root
                    .joinpath(template.replace("-", "_"))
                    .joinpath("research.md")
                    .read_text(encoding="utf-8")
                )
                normalized_research = " ".join(research.split())
                self.assertIn("## Research brief and clarification", research)
                self.assertIn(
                    "English is the internal working language of the AutoQuant desk",
                    normalized_research,
                )
                self.assertIn(
                    "ask the delegating Agent or user",
                    normalized_research,
                )

    def test_workspace_projects_directory_cannot_escape_or_be_a_symlink(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_workspace(root)
            manifest_path = root / WORKSPACE_MANIFEST
            manifest = json.loads(manifest_path.read_text())
            manifest["projects_directory"] = "../outside"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "confined POSIX relative path",
            ):
                load_workspace(root)

        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside,
        ):
            root = Path(directory)
            initialize_workspace(root)
            projects = root / "projects"
            projects.rmdir()
            projects.symlink_to(Path(outside), target_is_directory=True)
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "cannot be symlinks",
            ):
                load_workspace(root)

    def test_workspace_rejects_symlink_project_entries(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside,
        ):
            workspace = initialize_workspace(directory)
            (workspace.projects_dir / "unsafe").symlink_to(
                Path(outside),
                target_is_directory=True,
            )
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "real directories",
            ):
                list_workspace_projects(workspace.root_dir)

    def test_project_rejects_symlink_components_in_owned_paths(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside,
        ):
            workspace = initialize_workspace(directory)
            project = create_project(workspace.root_dir, "confined-project")
            manifest_path = project.root_dir / PROJECT_MANIFEST
            manifest = json.loads(manifest_path.read_text())
            manifest["research_program"] = "guidance/research.md"
            manifest_path.write_text(json.dumps(manifest))
            (project.root_dir / "guidance").symlink_to(
                Path(outside),
                target_is_directory=True,
            )
            (Path(outside) / "research.md").write_text("escaped")

            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "components cannot be symlinks",
            ):
                load_project(project.root_dir)

    def test_project_rejects_unknown_fields_mismatched_id_and_missing_paths(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(directory)
            project = create_project(workspace.root_dir, "strict-project")
            manifest_path = project.root_dir / PROJECT_MANIFEST

            manifest = json.loads(manifest_path.read_text())
            manifest["surprise"] = True
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AutoQuantValidationError, "Unknown field"):
                load_project(project.root_dir)

            manifest.pop("surprise")
            manifest["id"] = "another-id"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "must match directory",
            ):
                load_project(project.root_dir)

            manifest["id"] = "strict-project"
            manifest_path.write_text(json.dumps(manifest))
            (project.root_dir / "models").rmdir()
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "Missing Project-owned 'models'",
            ):
                load_project(project.root_dir)

    def test_direct_project_rejects_redundant_workspace_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(directory)
            project = create_project(workspace.root_dir, "direct-project")
            with self.assertRaisesRegex(
                AutoQuantValidationError,
                "--project cannot be used",
            ):
                resolve_project_directory(project.root_dir, "direct-project")


if __name__ == "__main__":
    unittest.main()
