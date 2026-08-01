from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoquant.runs import list_runs, load_run
from autoquant.sessions import list_sessions
from autoquant.skill_bundle import verify_materialized_workspace_skills
from autoquant.studies import list_studies
from autoquant.studio import build_studio_snapshot
from autoquant.workspace import create_project, initialize_workspace, load_project
from autoquant.version import current_version


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = REPOSITORY_ROOT / "projects" / "sample-research-desk"
SAMPLE_RUN_ID = "run-20260729T075403870227Z-6b7cf30b394f"
PRIOR_SAMPLE_RUN_ID = "run-20260730T035544913232Z-4b19e3a63890"
PREVIOUS_SAMPLE_RUN_ID = "run-20260731T120304794599Z-6d6cdab313fe"
CURRENT_SAMPLE_RUN_ID = "run-20260731T131547748789Z-d99c9e66a888"
LATEST_SAMPLE_RUN_ID = "run-20260731T151103497628Z-f9adc26d1b95"
PRIOR_PORTFOLIO_SAMPLE_RUN_ID = "run-20260731T162132298210Z-e541f48086ba"
PORTFOLIO_SAMPLE_RUN_ID = "run-20260731T172357866325Z-4f640b413ddf"
CURRENT_FACTOR_SAMPLE_RUN_ID = "run-20260801T145000180368Z-1fd810b3fe0e"
NEW_FACTOR_SAMPLE_RUN_ID = "run-20260801T153801145739Z-a387a53aff40"
LATEST_FACTOR_SAMPLE_RUN_ID = "run-20260801T170126912006Z-b163fe166951"
CURRENT_HARNESS_FACTOR_RUN_ID = "run-20260801T175812734661Z-2105d3af241b"
CLOSE_TIME_FACTOR_RUN_ID = "run-20260801T184617432326Z-503eb77b044e"
SOURCE_AVAILABILITY_FACTOR_RUN_ID = "run-20260801T190954461897Z-2e8462aa4547"
CALENDAR_PACKAGE_FACTOR_RUN_ID = "run-20260801T200541529080Z-beb54535a432"
MULTI_SOURCE_FACTOR_RUN_ID = "run-20260801T212920787441Z-4fafdd0a9412"
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
    def test_repository_skill_bundle_matches_current_harness(self) -> None:
        manifest = verify_materialized_workspace_skills(REPOSITORY_ROOT)

        self.assertEqual(manifest["harnessVersion"], current_version())
        self.assertEqual(len(manifest["skills"]), 16)

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
            [
                SAMPLE_RUN_ID,
                PRIOR_SAMPLE_RUN_ID,
                PREVIOUS_SAMPLE_RUN_ID,
                CURRENT_SAMPLE_RUN_ID,
                LATEST_SAMPLE_RUN_ID,
                PRIOR_PORTFOLIO_SAMPLE_RUN_ID,
                PORTFOLIO_SAMPLE_RUN_ID,
                CURRENT_FACTOR_SAMPLE_RUN_ID,
                NEW_FACTOR_SAMPLE_RUN_ID,
                LATEST_FACTOR_SAMPLE_RUN_ID,
                CURRENT_HARNESS_FACTOR_RUN_ID,
                CLOSE_TIME_FACTOR_RUN_ID,
                SOURCE_AVAILABILITY_FACTOR_RUN_ID,
                CALENDAR_PACKAGE_FACTOR_RUN_ID,
                MULTI_SOURCE_FACTOR_RUN_ID,
            ],
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
        prior = load_run(project, PRIOR_SAMPLE_RUN_ID)
        self.assertEqual(prior.result["status"], "succeeded")
        self.assertEqual(prior.result["harness"]["version"], "0.8.28")
        self.assertEqual(
            prior.result["harness"]["commit"],
            "b5881b6a81db665afa96dbcdcaaa16d114eb53c0",
        )
        self.assertFalse(prior.result["harness"]["dirty"])
        previous = load_run(project, PREVIOUS_SAMPLE_RUN_ID)
        self.assertEqual(previous.result["status"], "succeeded")
        self.assertEqual(previous.result["harness"]["version"], "0.9.0")
        self.assertEqual(
            previous.result["harness"]["commit"],
            "37b002921ad2caaba2fbc0d78fc8cb5c4e7c524e",
        )
        self.assertFalse(previous.result["harness"]["dirty"])
        current = load_run(project, CURRENT_SAMPLE_RUN_ID)
        self.assertEqual(current.result["status"], "succeeded")
        self.assertEqual(current.result["harness"]["version"], "0.9.1")
        self.assertEqual(
            current.result["harness"]["commit"],
            "39a2e382ee4413f576812b0234bddd396dfd3b58",
        )
        self.assertFalse(current.result["harness"]["dirty"])
        self.assertEqual(
            current.result["metrics"]["factor_components"]["method"],
            "candidate-declared-components-v3",
        )
        self.assertEqual(
            [
                item["id"]
                for item in current.result["metrics"]["factor_components"][
                    "declaration"
                ]["components"]
            ],
            ["base_momentum_10"],
        )
        latest = load_run(project, LATEST_SAMPLE_RUN_ID)
        self.assertEqual(latest.result["status"], "succeeded")
        self.assertEqual(latest.result["harness"]["version"], "0.9.2")
        self.assertEqual(
            latest.result["harness"]["commit"],
            "1166a780272e4ff7be62503ef96d1c4cbae64a74",
        )
        self.assertFalse(latest.result["harness"]["dirty"])
        self.assertEqual(
            latest.result["metrics"]["prediction_universe"][
                "evaluation_mode"
            ],
            "cross-sectional",
        )
        prior_portfolio = load_run(project, PRIOR_PORTFOLIO_SAMPLE_RUN_ID)
        self.assertEqual(prior_portfolio.result["status"], "succeeded")
        self.assertEqual(
            prior_portfolio.result["study"]["id"],
            "ohlcv-portfolio-quality",
        )
        self.assertEqual(
            prior_portfolio.result["harness"]["version"], "0.9.3"
        )
        self.assertEqual(
            prior_portfolio.result["harness"]["commit"],
            "ed61378d51b940892353ff39035e458cce255030",
        )
        self.assertFalse(prior_portfolio.result["harness"]["dirty"])
        self.assertFalse(
            prior_portfolio.result["metrics"]["translation_robustness"][
                "applicable"
            ]
        )
        self.assertEqual(
            prior_portfolio.result["metrics"]["translation_robustness"][
                "reason"
            ],
            "cross-sectional-mode-has-no-temporal-window",
        )
        portfolio = load_run(project, PORTFOLIO_SAMPLE_RUN_ID)
        self.assertEqual(portfolio.result["status"], "succeeded")
        self.assertEqual(
            portfolio.result["study"]["id"],
            "ohlcv-portfolio-quality",
        )
        self.assertEqual(portfolio.result["harness"]["version"], "0.9.4")
        self.assertEqual(
            portfolio.result["harness"]["commit"],
            "f17d261c49f8b5895a8147446e05ae7bfe9fe9b7",
        )
        self.assertFalse(portfolio.result["harness"]["dirty"])
        current_factor = load_run(project, CURRENT_FACTOR_SAMPLE_RUN_ID)
        self.assertEqual(current_factor.result["status"], "succeeded")
        self.assertEqual(
            current_factor.result["study"]["id"], "ohlcv-factor-quality"
        )
        self.assertEqual(current_factor.result["harness"]["version"], "0.9.20")
        self.assertEqual(
            current_factor.result["harness"]["commit"],
            "58f69fa5124d9d66a686e4cece6f5dfad1871f1f",
        )
        self.assertFalse(current_factor.result["harness"]["dirty"])
        self.assertEqual(
            current_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        new_factor = load_run(project, NEW_FACTOR_SAMPLE_RUN_ID)
        self.assertEqual(new_factor.result["status"], "succeeded")
        self.assertEqual(
            new_factor.result["study"]["id"], "ohlcv-factor-quality"
        )
        self.assertEqual(new_factor.result["harness"]["version"], "0.9.21")
        self.assertEqual(
            new_factor.result["harness"]["commit"],
            "df13d137e5d75941b8f25f4bf7fb1b91a365fcdb",
        )
        self.assertFalse(new_factor.result["harness"]["dirty"])
        self.assertEqual(
            new_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        latest_factor = load_run(project, LATEST_FACTOR_SAMPLE_RUN_ID)
        self.assertEqual(latest_factor.result["status"], "succeeded")
        self.assertEqual(
            latest_factor.result["study"]["id"], "ohlcv-factor-quality"
        )
        self.assertEqual(latest_factor.result["harness"]["version"], "0.9.22")
        self.assertEqual(
            latest_factor.result["harness"]["commit"],
            "eebbd1b4ac7ebfd80e0b9b392606e149444fc935",
        )
        self.assertFalse(latest_factor.result["harness"]["dirty"])
        self.assertEqual(
            latest_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        current_harness_factor = load_run(project, CURRENT_HARNESS_FACTOR_RUN_ID)
        self.assertEqual(current_harness_factor.result["status"], "succeeded")
        self.assertEqual(
            current_harness_factor.result["study"]["id"], "ohlcv-factor-quality"
        )
        self.assertEqual(
            current_harness_factor.result["harness"]["version"], "0.9.23"
        )
        self.assertEqual(
            current_harness_factor.result["harness"]["commit"],
            "f4843fa42b38f33cc05d81a0b401d4395409cc22",
        )
        self.assertFalse(current_harness_factor.result["harness"]["dirty"])
        self.assertEqual(
            current_harness_factor.result["harness"]["buildProvenance"],
            "source-checkout",
        )
        self.assertEqual(
            current_harness_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        close_time_factor = load_run(project, CLOSE_TIME_FACTOR_RUN_ID)
        self.assertEqual(close_time_factor.result["status"], "succeeded")
        self.assertEqual(
            close_time_factor.result["study"]["id"], "ohlcv-factor-quality"
        )
        self.assertEqual(
            close_time_factor.result["harness"]["version"], "0.9.24"
        )
        self.assertEqual(
            close_time_factor.result["harness"]["commit"],
            "ea9a01ea379d0c7f030344eafbca5d39f5c54dba",
        )
        self.assertFalse(close_time_factor.result["harness"]["dirty"])
        self.assertEqual(
            close_time_factor.result["metrics"]["factor_api"][
                "cross_asset_context"
            ],
            "same-or-prior-timestamp-explicit-candidate",
        )
        self.assertEqual(
            close_time_factor.result["metrics"]["input_availability"][
                "prediction_universe"
            ]["timeline_timestamps"],
            420,
        )
        self.assertEqual(
            close_time_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        source_availability_factor = load_run(
            project,
            SOURCE_AVAILABILITY_FACTOR_RUN_ID,
        )
        self.assertEqual(source_availability_factor.result["status"], "succeeded")
        self.assertEqual(
            source_availability_factor.result["study"]["id"],
            "ohlcv-factor-quality",
        )
        self.assertEqual(
            source_availability_factor.result["harness"]["version"],
            "0.9.24",
        )
        self.assertEqual(
            source_availability_factor.result["harness"]["commit"],
            "ef3b9c230de346bb5923f983d2f728487e0d5c7a",
        )
        self.assertFalse(source_availability_factor.result["harness"]["dirty"])
        self.assertEqual(
            source_availability_factor.result["metrics"]["input_availability"][
                "timestamps"
            ],
            420,
        )
        self.assertEqual(
            source_availability_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        calendar_package_factor = load_run(
            project,
            CALENDAR_PACKAGE_FACTOR_RUN_ID,
        )
        self.assertEqual(calendar_package_factor.result["status"], "succeeded")
        self.assertEqual(
            calendar_package_factor.result["study"]["id"],
            "ohlcv-factor-quality",
        )
        self.assertEqual(
            calendar_package_factor.result["harness"]["version"],
            "0.9.25",
        )
        self.assertEqual(
            calendar_package_factor.result["harness"]["commit"],
            "643b71313a674559dc474afb20ee5be92384e876",
        )
        self.assertFalse(calendar_package_factor.result["harness"]["dirty"])
        self.assertEqual(
            calendar_package_factor.result["harness"]["buildProvenance"],
            "source-checkout",
        )
        self.assertEqual(
            calendar_package_factor.result["harness"]["sourceHash"],
            "b1b83f033c20cb5a8bd4bcd269bd2338e8b9cd8ee2463a11bb1ec28663d4a93f",
        )
        self.assertEqual(
            calendar_package_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )
        multi_source_factor = load_run(project, MULTI_SOURCE_FACTOR_RUN_ID)
        self.assertEqual(multi_source_factor.result["status"], "succeeded")
        self.assertEqual(
            multi_source_factor.result["study"]["id"],
            "ohlcv-factor-quality",
        )
        self.assertEqual(
            multi_source_factor.result["harness"]["version"],
            "0.9.26",
        )
        self.assertEqual(
            multi_source_factor.result["harness"]["commit"],
            "3cd8cd99de9602b1903dc6bbd8ec8714c64026cc",
        )
        self.assertFalse(multi_source_factor.result["harness"]["dirty"])
        self.assertEqual(
            multi_source_factor.result["harness"]["sourceHash"],
            "40d5e322eee382f54471d8787ffed3bca69d8540f31e2ef0446e79d445cb7d21",
        )
        self.assertEqual(
            multi_source_factor.result["metrics"]["validation_mean_ic"],
            -0.031325301204819286,
        )

        research = (project.root_dir / "research.md").read_text(encoding="utf-8")
        self.assertIn("## About this sample", research)
        self.assertIn(SAMPLE_RUN_ID, research)
        self.assertIn(CURRENT_SAMPLE_RUN_ID, research)
        self.assertIn(LATEST_SAMPLE_RUN_ID, research)
        self.assertIn(PORTFOLIO_SAMPLE_RUN_ID, research)
        self.assertIn(CURRENT_FACTOR_SAMPLE_RUN_ID, research)
        self.assertIn(NEW_FACTOR_SAMPLE_RUN_ID, research)
        self.assertIn(LATEST_FACTOR_SAMPLE_RUN_ID, research)
        self.assertIn(CURRENT_HARNESS_FACTOR_RUN_ID, research)
        self.assertIn(CLOSE_TIME_FACTOR_RUN_ID, research)
        self.assertIn(SOURCE_AVAILABILITY_FACTOR_RUN_ID, research)
        self.assertIn(CALENDAR_PACKAGE_FACTOR_RUN_ID, research)
        self.assertIn(MULTI_SOURCE_FACTOR_RUN_ID, research)
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
        self.assertEqual(sample["counts"]["runs"], 15)
        self.assertEqual(sample["counts"]["sessions"], 0)
        self.assertIsNotNone(sample["factorExplorer"])
        self.assertEqual(
            sample["factorExplorer"]["run"]["id"],
            MULTI_SOURCE_FACTOR_RUN_ID,
        )
        self.assertEqual(
            sample["researchProgramStatus"]["lanes"][0]["latestRun"]["id"],
            MULTI_SOURCE_FACTOR_RUN_ID,
        )
        self.assertIsNotNone(sample["portfolioExplorer"])
        self.assertEqual(
            sample["portfolioExplorer"]["run"]["id"],
            PORTFOLIO_SAMPLE_RUN_ID,
        )
        self.assertEqual(
            sample["portfolioExplorer"]["translationRobustness"]["reason"],
            "cross-sectional-mode-has-no-temporal-window",
        )
        self.assertEqual(
            sample["portfolioExplorer"]["signalMonetization"]["semantics"],
            {
                "contribution": "additive-weight-times-next-bar-return",
                "evaluationMode": "cross-sectional",
                "intentConstruction": "mandate-equal-active-side-budget",
                "equalIntent": (
                    "prediction-mode-aware-mandate-constrained-"
                    "signal-state-diagnostic"
                ),
                "counterfactualCompounding": False,
                "entersSelection": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
