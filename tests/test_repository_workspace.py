from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoquant.runs import list_runs, load_run
from autoquant.sessions import list_sessions
from autoquant.studies import list_studies
from autoquant.studio import build_studio_snapshot
from autoquant.workspace import create_project, initialize_workspace, load_project


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = REPOSITORY_ROOT / "projects" / "sample-research-desk"
SAMPLE_RUN_ID = "run-20260729T075403870227Z-6b7cf30b394f"
CURRENT_SAMPLE_RUN_ID = "run-20260730T035544913232Z-4b19e3a63890"
SAMPLE_DESCRIPTION = (
    "A deterministic three-lane reference Project for learning AutoQuant "
    "before starting real research."
)


def _template_owned_files(root: Path) -> dict[str, bytes]:
    excluded_roots = {"runs", "sessions"}
    result: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts[0] in excluded_roots or relative.as_posix() == "research.md":
            continue
        result[relative.as_posix()] = path.read_bytes()
    return result


class RepositoryWorkspaceTests(unittest.TestCase):
    def test_repository_ignores_workspace_staging(self) -> None:
        ignore_rules = (
            (REPOSITORY_ROOT / ".gitignore")
            .read_text(encoding="utf-8")
            .splitlines()
        )

        self.assertIn("/staging/", ignore_rules)

    def test_sample_is_a_complete_three_lane_project_with_historical_evidence(
        self,
    ) -> None:
        project = load_project(SAMPLE_ROOT, expected_id="sample-research-desk")

        self.assertEqual(
            [item.id for item in list_studies(project)],
            [
                "ohlcv-factor-quality",
                "ohlcv-portfolio-quality",
                "ohlcv-rl-factor-policy",
            ],
        )
        self.assertEqual(list_sessions(project), [])
        runs = list_runs(project)
        self.assertEqual(
            [item.id for item in runs],
            [SAMPLE_RUN_ID, CURRENT_SAMPLE_RUN_ID],
        )
        run = load_run(project, SAMPLE_RUN_ID)
        self.assertEqual(run.result["status"], "succeeded")
        self.assertEqual(run.result["study"]["id"], "ohlcv-factor-quality")
        self.assertEqual(run.result["harness"]["version"], "0.8.7")
        self.assertEqual(
            run.result["harness"]["commit"],
            "0c9de83ea237c23d1eda43621bf2d58c2f45df7a",
        )
        self.assertFalse(run.result["harness"]["dirty"])
        self.assertEqual(len(run.result["artifacts"]), 6)
        current = load_run(project, CURRENT_SAMPLE_RUN_ID)
        self.assertEqual(current.result["status"], "succeeded")
        self.assertEqual(current.result["harness"]["version"], "0.8.28")
        self.assertEqual(
            current.result["harness"]["commit"],
            "b5881b6a81db665afa96dbcdcaaa16d114eb53c0",
        )
        self.assertFalse(current.result["harness"]["dirty"])
        self.assertEqual(
            [
                item["id"]
                for item in current.result["metrics"]["factor_components"][
                    "declaration"
                ]["components"]
            ],
            ["base_momentum_10"],
        )

        research = (project.root_dir / "research.md").read_text(encoding="utf-8")
        self.assertIn("## About this sample", research)
        self.assertIn(SAMPLE_RUN_ID, research)
        self.assertIn(CURRENT_SAMPLE_RUN_ID, research)
        self.assertIn("not relabeled as a", research)

    def test_sample_template_owned_files_match_a_fresh_research_desk(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "workspace")
            generated = create_project(
                workspace.root_dir,
                "sample-research-desk",
                name="Sample Research Desk",
                description=SAMPLE_DESCRIPTION,
                template="ohlcv-research-desk",
            )

            self.assertEqual(
                _template_owned_files(load_project(SAMPLE_ROOT).root_dir),
                _template_owned_files(generated.root_dir),
            )

    def test_sample_projects_real_factor_evidence_into_studio(self) -> None:
        snapshot = build_studio_snapshot(SAMPLE_ROOT)

        self.assertEqual(snapshot["source"]["scope"], "project")
        self.assertEqual(len(snapshot["projects"]), 1)
        sample = snapshot["projects"][0]
        self.assertTrue(sample["valid"])
        self.assertEqual(sample["counts"]["studies"], 3)
        self.assertEqual(sample["counts"]["runs"], 2)
        self.assertEqual(sample["counts"]["sessions"], 0)
        self.assertIsNotNone(sample["factorExplorer"])
        self.assertEqual(
            sample["researchProgramStatus"]["lanes"][0]["latestRun"]["id"],
            CURRENT_SAMPLE_RUN_ID,
        )


if __name__ == "__main__":
    unittest.main()
