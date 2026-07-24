"""Verified read-only snapshots and local HTTP presentation for AutoQuant."""

from __future__ import annotations

import json
import shlex
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from .decision_matrix import (
    STUDIO_COMPARISON_TRIALS,
    load_session_decision_matrix,
)
from .dossiers import list_dossiers, load_dossier_status
from .factor_explorer import (
    DEFAULT_FACTOR_POINTS,
    load_factor_diagnostics,
)
from .intake import load_project_intake
from .portfolio_explorer import (
    DEFAULT_PORTFOLIO_POINTS,
    load_portfolio_diagnostics,
)
from .rl_explorer import DEFAULT_RL_POINTS, load_rl_diagnostics
from .research import list_campaign_progress, list_campaigns
from .research_program import load_research_program
from .reports import list_reports
from .runs import list_runs, load_run
from .sessions import list_sessions, load_session, session_snapshot
from .studies import list_studies
from .workspace import (
    PROJECT_MANIFEST,
    SCHEMA_VERSION,
    WORKSPACE_MANIFEST,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
    load_project,
    load_workspace,
)


STUDIO_KIND = "autoquant-studio-snapshot"
STUDIO_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/assets/studio.css": ("studio.css", "text/css; charset=utf-8"),
    "/assets/studio.js": ("studio.js", "text/javascript; charset=utf-8"),
}
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _diagnostics(
    category: str,
    error: AutoQuantValidationError,
) -> list[dict[str, str]]:
    return [
        {
            "category": category,
            **issue.to_dict(),
        }
        for issue in error.issues
    ]


def _read_category(
    category: str,
    operation: Callable[[], Any],
) -> tuple[Any, list[dict[str, str]]]:
    try:
        return operation(), []
    except AutoQuantValidationError as error:
        return [], _diagnostics(category, error)


def _workspace_projects(
    root: Path,
    selected_project: str | None,
) -> tuple[dict[str, Any], list[ProjectContext], list[dict[str, str]]]:
    workspace = load_workspace(root)
    projects: list[ProjectContext] = []
    discovered_ids: set[str] = set()
    diagnostics: list[dict[str, str]] = []
    for entry in sorted(workspace.projects_dir.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir():
            diagnostics.append(
                {
                    "category": "workspace",
                    **_issue(
                        entry,
                        "workspace.project-entry",
                        "Workspace Project entries must be real directories",
                    ).to_dict(),
                }
            )
            continue
        try:
            project = load_project(entry, expected_id=entry.name)
        except AutoQuantValidationError as error:
            diagnostics.extend(_diagnostics("workspace", error))
            continue
        discovered_ids.add(project.manifest.id)
        if selected_project is None or project.manifest.id == selected_project:
            projects.append(project)
    default_project = workspace.manifest.default_project
    if default_project is not None and default_project not in discovered_ids:
        diagnostics.append(
            {
                "category": "workspace",
                **_issue(
                    root / WORKSPACE_MANIFEST,
                    "workspace.default-project",
                    f"Default Project '{default_project}' does not exist",
                ).to_dict(),
            }
        )
    if selected_project is not None and not any(
        project.manifest.id == selected_project for project in projects
    ):
        raise AutoQuantValidationError(
            [
                _issue(
                    selected_project,
                    "workspace.project-missing",
                    f"Unknown Workspace Project: {selected_project}",
                )
            ]
        )
    return (
        {
            "name": workspace.manifest.name,
            "rootDir": str(workspace.root_dir),
            "defaultProject": workspace.manifest.default_project,
        },
        projects,
        diagnostics,
    )


def _resolve_source(
    directory: str | Path,
    selected_project: str | None,
) -> tuple[str, Path, dict[str, Any] | None, list[ProjectContext], list[dict[str, str]]]:
    raw = Path(directory).expanduser().absolute()
    if raw.is_symlink():
        raise AutoQuantValidationError(
            [_issue(raw, "path.symlink", "Studio input root cannot be a symlink")]
        )
    root = raw.resolve()
    is_project = (root / PROJECT_MANIFEST).is_file()
    is_workspace = (root / WORKSPACE_MANIFEST).is_file()
    if is_project and is_workspace:
        raise AutoQuantValidationError(
            [_issue(root, "path.ambiguous", "Studio root cannot be both types")]
        )
    if is_project:
        if selected_project is not None:
            raise AutoQuantValidationError(
                [
                    _issue(
                        selected_project,
                        "project.unexpected-selection",
                        "--project cannot select inside a direct Project",
                    )
                ]
            )
        return "project", root, None, [load_project(root)], []
    if is_workspace:
        workspace, projects, diagnostics = _workspace_projects(
            root,
            selected_project,
        )
        return "workspace", root, workspace, projects, diagnostics
    raise AutoQuantValidationError(
        [
            _issue(
                root,
                "path.not-autoquant",
                f"Not an AutoQuant Project or Workspace: {root}",
            )
        ]
    )


def _timeline(
    runs: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    dossiers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for run in runs:
        events.append(
            {
                "kind": "run",
                "id": run["id"],
                "at": run["startedAt"],
                "status": run["status"],
                "title": f"{run['studyId']} · {run['primaryMetric']}",
                "value": run["primaryValue"],
            }
        )
    for item in sessions:
        session = item["session"]
        events.append(
            {
                "kind": "session",
                "id": session["id"],
                "at": session["updatedAt"],
                "status": session["status"],
                "title": session["studyId"],
                "value": session["leader"]["value"],
            }
        )
        for experiment in item["experiments"]:
            events.append(
                {
                    "kind": "experiment",
                    "id": experiment["id"],
                    "at": experiment["completedAt"],
                    "status": experiment["verdict"],
                    "title": experiment["hypothesis"],
                    "value": experiment["candidateValue"],
                }
            )
        for campaign in item["campaigns"]:
            events.append(
                {
                    "kind": "campaign",
                    "id": campaign["id"],
                    "at": campaign["completedAt"],
                    "status": campaign["status"],
                    "title": campaign["reason"],
                    "value": campaign["experiments"],
                }
            )
        for report in item["reports"]:
            events.append(
                {
                    "kind": "report",
                    "id": report["id"],
                    "at": report["publishedAt"],
                    "status": "published",
                    "title": report["title"],
                    "value": report["findings"],
                }
            )
        for progress in item["progress"]:
            events.append(
                {
                    "kind": "progress",
                    "id": progress["campaignId"],
                    "at": progress["updatedAt"],
                    "status": progress["phase"],
                    "title": progress["message"],
                    "value": progress["turn"],
                    "mutable": True,
                }
            )
    for dossier in dossiers:
        events.append(
            {
                "kind": "dossier",
                "id": dossier["id"],
                "at": dossier["publishedAt"],
                "status": "published",
                "title": dossier["title"],
                "value": dossier["findings"],
            }
        )
    return sorted(
        events,
        key=lambda event: (event["at"], event["id"]),
        reverse=True,
    )[:100]


def _portfolio_metric_layers(result: dict[str, Any]) -> dict[str, Any] | None:
    metrics = result["metrics"]
    required = ("factor", "portfolio", "implementation", "robustness")
    if not all(isinstance(metrics.get(key), dict) for key in required):
        return None
    try:
        layers = {
            "kind": "portfolio",
            "mandate": (
                {
                    "id": metrics["portfolio_mandate"]["id"],
                    "direction": metrics["portfolio_mandate"]["source"][
                        "direction"
                    ],
                    "family": metrics["portfolio_mandate"]["construction"][
                        "family"
                    ],
                    "tradableAssets": metrics["portfolio_mandate"][
                        "tradableAssets"
                    ],
                    "contextAssets": metrics["portfolio_mandate"][
                        "contextAssets"
                    ],
                    "riskPolicy": metrics["portfolio_mandate"][
                        "construction"
                    ]["riskPolicy"],
                }
                if isinstance(metrics.get("portfolio_mandate"), dict)
                else None
            ),
            "factor": {
                "validationRankIc": metrics["factor"]["validation"]["mean_rank_ic"],
                "testRankIc": metrics["factor"]["test"]["mean_rank_ic"],
            },
            "portfolio": {
                "validationNetSharpe": metrics["portfolio"]["validation"]["net"][
                    "sharpe"
                ],
                "testNetSharpe": metrics["portfolio"]["test"]["net"]["sharpe"],
                "testAnnualReturn": metrics["portfolio"]["test"]["net"][
                    "annual_return"
                ],
                "testMaximumDrawdown": metrics["portfolio"]["test"]["net"][
                    "maximum_drawdown"
                ],
            },
            "selection": metrics.get("research_integrity"),
            "implementation": {
                "testAnnualizedTurnover": metrics["implementation"]["test"][
                    "annualized_one_way_turnover"
                ],
                "testCostDrag": metrics["implementation"]["test"][
                    "total_cost_drag"
                ],
                "testMaximumParticipation": metrics["implementation"]["test"][
                    "maximum_volume_participation"
                ],
            },
            "robustness": {
                "test25bpsSharpe": metrics["robustness"]["cost_stress"]["25bps"][
                    "test"
                ]["sharpe"],
                "testExtraDelaySharpe": metrics["robustness"]["extra_delay"][
                    "test"
                ]["sharpe"],
            },
            "constraintsPassed": metrics["constraint_audit"]["passed"],
        }
        signal_policy = metrics.get("signal_policy")
        attribution = metrics.get("attribution")
        layers["signalPolicy"] = None
        layers["attribution"] = None
        layers["liquidityCapacity"] = None
        if isinstance(signal_policy, dict):
            validation_policy = signal_policy.get("validation", {})
            comparison = signal_policy.get(
                "hysteresis_comparison",
                {},
            ).get("validation", {})
            if isinstance(validation_policy, dict) and isinstance(
                comparison,
                dict,
            ):
                layers["signalPolicy"] = {
                    "validationStateChangeRate": validation_policy.get(
                        "state_change_rate"
                    ),
                    "validationEntries": validation_policy.get("entries"),
                    "validationExits": validation_policy.get("exits"),
                    "validationReversals": validation_policy.get("reversals"),
                    "validationTransitionReductionRate": comparison.get(
                        "transition_reduction_rate"
                    ),
                    "validationImplementationTurnoverReduction": comparison.get(
                        "implementation_turnover_reduction"
                    ),
                }
        if isinstance(attribution, dict):
            validation_attribution = attribution.get("validation", {})
            if isinstance(validation_attribution, dict):
                reconciliation = validation_attribution.get(
                    "reconciliation",
                    {},
                )
                concentration = validation_attribution.get(
                    "concentration",
                    {},
                )
                layers["attribution"] = {
                    "validationReconciliationPassed": reconciliation.get(
                        "passed"
                    ),
                    "validationMaximumAbsoluteNetContributionShare": (
                        concentration.get(
                            "maximum_absolute_net_contribution_share"
                        )
                    ),
                    "validationAbsoluteNetContributionHhi": concentration.get(
                        "absolute_net_contribution_hhi"
                    ),
                    "validationMaximumAbsoluteRiskContributionShare": (
                        concentration.get(
                            "maximum_absolute_variance_contribution_share"
                        )
                    ),
                }
        capacity = metrics.get("liquidity_capacity")
        if isinstance(capacity, dict):
            validation_capacity = capacity.get("validation", {})
            conservative = (
                validation_capacity.get("capacity_1pct", {})
                if isinstance(validation_capacity, dict)
                else {}
            )
            if isinstance(conservative, dict):
                layers["liquidityCapacity"] = {
                    "validationTradeDateCoverage": validation_capacity.get(
                        "trade_date_coverage"
                    ),
                    "validationTenthPercentileNav1Pct": conservative.get(
                        "tenth_percentile_nav"
                    ),
                    "validationReferenceNavBreachRate1Pct": conservative.get(
                        "reference_nav_breach_rate"
                    ),
                    "selectionAuthority": capacity.get("policy", {}).get(
                        "selection_authority"
                    ),
                }
        return layers
    except (KeyError, TypeError):
        return None


def _factor_metric_layers(result: dict[str, Any]) -> dict[str, Any] | None:
    metrics = result["metrics"]
    if not all(
        isinstance(metrics.get(key), dict)
        for key in ("validation", "test")
    ):
        return None
    try:
        layers = {
            "kind": "factor",
            "validationMeanIc": metrics["validation"]["mean_ic"],
            "validationPearsonIc": (
                metrics["validation"].get("pearson_ic", {}).get("mean_ic")
            ),
            "validationIcir": metrics["validation"]["icir"],
            "testMeanIc": metrics["test"]["mean_ic"],
            "testIcir": metrics["test"]["icir"],
            "meanCoverage": metrics["mean_coverage"],
            "meanRankTurnover": metrics["mean_rank_turnover"],
            "selection": metrics.get("research_integrity"),
        }
        horizon_quality = metrics.get("horizon_quality")
        quantiles = metrics.get("quantile_analysis")
        stability = metrics.get("stability")
        styles = metrics.get("style_correlations")
        layers.update(
            {
                "validationHacTStatistic": None,
                "validationHorizon5MeanIc": None,
                "validationQuantileSpread": None,
                "validationQuantileMonotonicity": None,
                "validationWorstFoldMeanIc": None,
                "validationMaximumAbsoluteStyleCorrelation": None,
                "validationRegimesObserved": None,
            }
        )
        hac = metrics["validation"].get("hac")
        if isinstance(hac, dict):
            layers["validationHacTStatistic"] = hac.get("t_statistic")
        if isinstance(horizon_quality, dict):
            layers["validationHorizon5MeanIc"] = (
                horizon_quality.get("5", {})
                .get("validation", {})
                .get("mean_ic")
            )
        if isinstance(quantiles, dict):
            validation_quantiles = (
                quantiles.get("1", {}).get("validation", {})
            )
            layers["validationQuantileSpread"] = validation_quantiles.get(
                "high_minus_low"
            )
            layers["validationQuantileMonotonicity"] = (
                validation_quantiles.get("monotonicity")
            )
        if isinstance(stability, dict):
            folds = stability.get("chronological_folds", {})
            fold_values = [
                item.get("mean_ic")
                for name, item in folds.items()
                if name.startswith("validation_") and isinstance(item, dict)
            ]
            finite_folds = [
                float(value)
                for value in fold_values
                if isinstance(value, (int, float))
            ]
            if finite_folds:
                layers["validationWorstFoldMeanIc"] = min(finite_folds)
            regimes = (
                stability.get("causal_regimes", {}).get("validation", {})
            )
            if isinstance(regimes, dict):
                layers["validationRegimesObserved"] = sum(
                    1
                    for item in regimes.values()
                    if isinstance(item, dict)
                    and isinstance(item.get("mean_ic"), (int, float))
                )
        if isinstance(styles, dict):
            validation_styles = styles.get("validation", {})
            style_values = [
                item.get("mean_rank_correlation")
                for item in validation_styles.values()
                if isinstance(item, dict)
            ]
            finite_styles = [
                abs(float(value))
                for value in style_values
                if isinstance(value, (int, float))
            ]
            if finite_styles:
                layers["validationMaximumAbsoluteStyleCorrelation"] = max(
                    finite_styles
                )
        return layers
    except (KeyError, TypeError):
        return None


def _rl_metric_layers(result: dict[str, Any]) -> dict[str, Any] | None:
    metrics = result["metrics"]
    if not all(
        isinstance(metrics.get(key), dict)
        for key in ("rl", "baselines", "comparison", "configuration")
    ):
        return None
    try:
        aggregate = metrics["rl"]["aggregate"]
        comparison = metrics["comparison"]
        return {
            "kind": "rl-policy",
            "mandate": (
                {
                    "id": metrics["portfolio_mandate"]["id"],
                    "direction": metrics["portfolio_mandate"]["source"][
                        "direction"
                    ],
                    "family": metrics["portfolio_mandate"]["construction"][
                        "family"
                    ],
                    "tradableAssets": metrics["portfolio_mandate"][
                        "tradableAssets"
                    ],
                    "contextAssets": metrics["portfolio_mandate"][
                        "contextAssets"
                    ],
                    "riskPolicy": metrics["portfolio_mandate"][
                        "construction"
                    ]["riskPolicy"],
                }
                if isinstance(metrics.get("portfolio_mandate"), dict)
                else None
            ),
            "validationMeanNetSharpe": metrics[
                "validation_mean_net_sharpe"
            ],
            "testMeanNetSharpe": aggregate["test_net_sharpe"]["mean"],
            "validationSeedFoldStd": aggregate["validation_net_sharpe"][
                "standard_deviation"
            ],
            "testSeedFoldStd": aggregate["test_net_sharpe"][
                "standard_deviation"
            ],
            "validationBaselineAdvantage": comparison[
                "mean_validation_advantage_vs_best_baseline"
            ],
            "validationCandidateFactorAdvantage": comparison.get(
                "mean_validation_advantage_vs_candidate_factor"
            ),
            "validationCandidateActionFrequency": comparison.get(
                "mean_validation_candidate_action_frequency"
            ),
            "failureRate": aggregate["failure_rate"],
            "folds": len(metrics["configuration"]["folds"]),
            "seeds": len(metrics["configuration"]["seeds"]),
        }
    except (KeyError, TypeError):
        return None


def _run_metric_layers(result: dict[str, Any]) -> dict[str, Any] | None:
    return (
        _portfolio_metric_layers(result)
        or _rl_metric_layers(result)
        or _factor_metric_layers(result)
    )


def _project_snapshot(project: ProjectContext) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    program_path = confined_path(
        project.root_dir,
        project.manifest.research_program,
        "project/research_program",
    )
    studies_raw, issues = _read_category("studies", lambda: list_studies(project))
    diagnostics.extend(issues)
    runs_raw, issues = _read_category("runs", lambda: list_runs(project))
    diagnostics.extend(issues)
    sessions_raw, issues = _read_category("sessions", lambda: list_sessions(project))
    diagnostics.extend(issues)
    intake_raw, issues = _read_category(
        "intake",
        lambda: load_project_intake(project),
    )
    diagnostics.extend(issues)
    intake = intake_raw if isinstance(intake_raw, dict) else None
    if intake is not None:
        intake = {
            **intake,
            "commands": [
                _command(
                    "session.start",
                    [
                        "aq",
                        "session",
                        "start",
                        str(project.root_dir),
                        "--study",
                        intake["study"]["id"],
                        "--request",
                        str(project.root_dir / intake["manifest"]["requestPath"]),
                        "--json",
                    ],
                    "creates-artifact",
                )
            ],
        }
    research_program_status = None
    try:
        research_program_status = load_research_program(
            project,
            optional=True,
        )
    except AutoQuantValidationError as error:
        diagnostics.extend(_diagnostics("research-program", error))
    dossier_bundle, issues = _read_category(
        "dossiers",
        lambda: {
            "status": load_dossier_status(project, optional=True),
            "items": [item.to_dict() for item in list_dossiers(project)],
        },
    )
    diagnostics.extend(issues)
    if isinstance(dossier_bundle, dict):
        dossier_status = dossier_bundle["status"]
        dossiers = dossier_bundle["items"]
    else:
        dossier_status = None
        dossiers = []
    studies = [item.to_dict() for item in studies_raw]
    runs: list[dict[str, Any]] = []
    for item in runs_raw:
        summary = item.to_dict()
        metric_layers = _run_metric_layers(
            load_run(project, item.id).result
        )
        if metric_layers is not None:
            summary["metricLayers"] = metric_layers
        runs.append(summary)

    def current_program_run(lane_id: str):
        if research_program_status is None:
            return None
        lane = next(
            (
                item
                for item in research_program_status["lanes"]
                if item["id"] == lane_id
            ),
            None,
        )
        if (
            lane is None
            or not lane["currentRun"]
            or lane["latestRun"] is None
            or lane["latestRun"]["status"] != "succeeded"
        ):
            return None
        return next(
            (
                item
                for item in runs_raw
                if item.id == lane["latestRun"]["id"]
            ),
            None,
        )

    factor_explorer = None
    factor_candidate = current_program_run("factor")
    if research_program_status is None:
        factor_candidate = next(
            (
                item
                for item in reversed(runs_raw)
                if item.status == "succeeded"
                and item.primary_metric == "validation_mean_ic"
            ),
            None,
        )
    if factor_candidate is not None:
        try:
            factor_explorer = load_factor_diagnostics(
                project,
                factor_candidate.id,
                point_limit=DEFAULT_FACTOR_POINTS,
            )
        except AutoQuantValidationError as error:
            diagnostics.extend(
                _diagnostics(
                    f"factor-explorer:{factor_candidate.id}",
                    error,
                )
            )
    portfolio_explorer = None
    portfolio_candidate = current_program_run("portfolio")
    if research_program_status is None:
        portfolio_candidate = next(
            (
                item
                for item in reversed(runs_raw)
                if item.status == "succeeded"
                and item.primary_metric == "validation_net_sharpe"
            ),
            None,
        )
    if portfolio_candidate is not None:
        try:
            portfolio_explorer = load_portfolio_diagnostics(
                project,
                portfolio_candidate.id,
                point_limit=DEFAULT_PORTFOLIO_POINTS,
            )
        except AutoQuantValidationError as error:
            diagnostics.extend(
                _diagnostics(
                    f"portfolio-explorer:{portfolio_candidate.id}",
                    error,
                )
            )
    rl_explorer = None
    rl_candidate = current_program_run("rl")
    if research_program_status is None:
        rl_candidate = next(
            (
                item
                for item in reversed(runs_raw)
                if item.status == "succeeded"
                and item.primary_metric == "validation_mean_net_sharpe"
            ),
            None,
        )
    if rl_candidate is not None:
        try:
            rl_explorer = load_rl_diagnostics(
                project,
                rl_candidate.id,
                point_limit=DEFAULT_RL_POINTS,
            )
        except AutoQuantValidationError as error:
            diagnostics.extend(
                _diagnostics(
                    f"rl-explorer:{rl_candidate.id}",
                    error,
                )
            )
    sessions: list[dict[str, Any]] = []
    for summary in sessions_raw:
        try:
            session = load_session(project, summary.id)
            snapshot = session_snapshot(project, session)
            campaigns = [
                item.to_dict() for item in list_campaigns(project, session)
            ]
            reports = [
                item.to_dict() for item in list_reports(project, session)
            ]
            progress = list_campaign_progress(session)
            decision_matrix = None
            try:
                decision_matrix = load_session_decision_matrix(
                    project,
                    session.manifest["id"],
                    trial_limit=STUDIO_COMPARISON_TRIALS,
                )
            except AutoQuantValidationError as error:
                diagnostics.extend(
                    _diagnostics(
                        f"session-comparison:{session.manifest['id']}",
                        error,
                    )
                )
            authority = snapshot["authority"]
            if not authority["valid"]:
                diagnostics.extend(
                    {
                        "category": "session-authority",
                        **issue,
                    }
                    for issue in authority["issues"]
                )
            sessions.append(
                {
                    "session": snapshot["session"],
                    "worktree": snapshot["worktree"],
                    "candidate": snapshot["candidate"],
                    "delegation": snapshot["delegation"],
                    "selectionIntegrity": snapshot["selectionIntegrity"],
                    "decisionMatrix": decision_matrix,
                    "authority": authority,
                    "experiments": snapshot["experiments"],
                    "campaigns": campaigns,
                    "reports": reports,
                    "progress": progress,
                    "commands": _session_commands(project, session, reports),
                }
            )
        except AutoQuantValidationError as error:
            diagnostics.extend(_diagnostics(f"session:{summary.id}", error))
    verdicts = {"KEEP": 0, "REVERT": 0, "CRASH": 0}
    for item in sessions:
        for experiment in item["experiments"]:
            verdict = experiment["verdict"]
            verdicts[verdict] += 1
    commands: list[dict[str, Any]] = []
    if factor_explorer is not None:
        commands.append(
            _command(
                "run.factor",
                [
                    "aq",
                    "run",
                    "factor",
                    str(project.root_dir),
                    "--run",
                    factor_explorer["run"]["id"],
                    "--json",
                ],
                "read-only",
            )
        )
    if portfolio_explorer is not None:
        commands.append(
            _command(
                "run.portfolio",
                [
                    "aq",
                    "run",
                    "portfolio",
                    str(project.root_dir),
                    "--run",
                    portfolio_explorer["run"]["id"],
                    "--json",
                ],
                "read-only",
            )
        )
    if rl_explorer is not None:
        commands.append(
            _command(
                "run.rl",
                [
                    "aq",
                    "run",
                    "rl",
                    str(project.root_dir),
                    "--run",
                    rl_explorer["run"]["id"],
                    "--json",
                ],
                "read-only",
            )
        )
    if research_program_status is not None:
        commands.append(
            _command(
                "project.program",
                [
                    "aq",
                    "project",
                    "program",
                    str(project.root_dir),
                    "--json",
                ],
                "read-only",
            )
        )
    if dossier_status is not None and dossier_status["nextAction"] is not None:
        commands.append(dossier_status["nextAction"])
    return {
        "id": project.manifest.id,
        "name": project.manifest.name,
        "description": project.manifest.description,
        "rootDir": str(project.root_dir),
        "researchProgram": {
            "path": str(program_path),
            "text": program_path.read_text(encoding="utf-8"),
        },
        "researchProgramStatus": research_program_status,
        "dossierStatus": dossier_status,
        "dossiers": dossiers,
        "intake": intake,
        "factorExplorer": factor_explorer,
        "portfolioExplorer": portfolio_explorer,
        "rlExplorer": rl_explorer,
        "commands": commands,
        "valid": not diagnostics,
        "diagnostics": diagnostics,
        "counts": {
            "studies": len(studies),
            "runs": len(runs),
            "sessions": len(sessions),
            "activeSessions": sum(
                item["session"]["status"] == "active" for item in sessions
            ),
            "campaigns": sum(len(item["campaigns"]) for item in sessions),
            "runningCampaigns": sum(len(item["progress"]) for item in sessions),
            "delegatedSessions": sum(
                item["delegation"] is not None for item in sessions
            ),
            "reports": sum(len(item["reports"]) for item in sessions),
            "dossiers": len(dossiers),
            "verdicts": verdicts,
        },
        "studies": studies,
        "runs": runs,
        "sessions": sessions,
        "timeline": _timeline(runs, sessions, dossiers),
    }


def _command(command_id: str, argv: list[str], effect: str) -> dict[str, Any]:
    return {
        "id": command_id,
        "argv": argv,
        "display": shlex.join(argv),
        "effect": effect,
    }


def _session_commands(
    project: ProjectContext,
    session,
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    commands = [
        _command(
            "session.show",
            [
                "aq",
                "session",
                "show",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--json",
            ],
            "read-only",
        ),
        _command(
            "session.compare",
            [
                "aq",
                "session",
                "compare",
                str(project.root_dir),
                "--session",
                session.manifest["id"],
                "--json",
            ],
            "read-only",
        ),
    ]
    if (
        session.delegation is not None
        and session.manifest["status"] == "active"
    ):
        commands.append(
            _command(
                "report.publish",
                [
                    "aq",
                    "report",
                    "publish",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--analysis",
                    "report-analysis.json",
                    "--json",
                ],
                "creates-artifact",
            )
        )
    if reports:
        commands.append(
            _command(
                "report.show",
                [
                    "aq",
                    "report",
                    "show",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--report",
                    reports[-1]["id"],
                    "--json",
                ],
                "read-only",
            )
        )
        if (
            session.manifest["status"] == "active"
            and session.manifest["leader"] == session.manifest["baseline"]
            and reports[-1]["leaderRunId"]
            == session.manifest["leader"]["runId"]
        ):
            commands.append(
                _command(
                    "session.complete",
                    [
                        "aq",
                        "session",
                        "complete",
                        str(project.root_dir),
                        "--session",
                        session.manifest["id"],
                        "--report",
                        reports[-1]["id"],
                        "--json",
                    ],
                    "creates-artifact",
                )
            )
    return commands


def build_studio_snapshot(
    directory: str | Path,
    *,
    project_id: str | None = None,
) -> dict[str, Any]:
    scope, root, workspace, projects, diagnostics = _resolve_source(
        directory,
        project_id,
    )
    observations = [_project_snapshot(project) for project in projects]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": STUDIO_KIND,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "scope": scope,
            "rootDir": str(root),
            "workspace": workspace,
        },
        "valid": not diagnostics and all(
            project["valid"] for project in observations
        ),
        "diagnostics": diagnostics,
        "projects": observations,
    }


def _asset_bytes(name: str) -> bytes:
    return files("autoquant").joinpath("studio_assets", name).read_bytes()


def _error_payload(error: Exception) -> tuple[int, dict[str, Any]]:
    if isinstance(error, AutoQuantValidationError):
        return (
            HTTPStatus.UNPROCESSABLE_ENTITY,
            {
                "schemaVersion": SCHEMA_VERSION,
                "ok": False,
                "error": {
                    "code": "validation.failed",
                    "message": str(error),
                    "issues": [issue.to_dict() for issue in error.issues],
                },
            },
        )
    return (
        HTTPStatus.INTERNAL_SERVER_ERROR,
        {
            "schemaVersion": SCHEMA_VERSION,
            "ok": False,
            "error": {
                "code": "studio.failed",
                "message": str(error),
                "issues": [],
            },
        },
    )


def _handler(
    directory: Path,
    project_id: str | None,
) -> type[BaseHTTPRequestHandler]:
    class StudioHandler(BaseHTTPRequestHandler):
        server_version = "AutoQuantStudio/0.1"

        def _headers(
            self,
            status: int,
            content_type: str,
            length: int,
            *,
            cache_control: str = "no-store",
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", cache_control)
            for key, value in SECURITY_HEADERS.items():
                self.send_header(key, value)
            self.end_headers()

        def _send(
            self,
            status: int,
            content_type: str,
            body: bytes,
            *,
            cache_control: str = "no-store",
            head_only: bool = False,
        ) -> None:
            self._headers(
                status,
                content_type,
                len(body),
                cache_control=cache_control,
            )
            if not head_only:
                self.wfile.write(body)

        def _route(self, *, head_only: bool = False) -> None:
            path = urlsplit(self.path).path
            try:
                if path == "/api/v1/health":
                    body = json.dumps(
                        {
                            "schemaVersion": SCHEMA_VERSION,
                            "ok": True,
                            "service": "autoquant-studio",
                            "mode": "read-only",
                        },
                        separators=(",", ":"),
                    ).encode()
                    self._send(
                        HTTPStatus.OK,
                        "application/json; charset=utf-8",
                        body,
                        head_only=head_only,
                    )
                    return
                if path == "/api/v1/snapshot":
                    body = json.dumps(
                        build_studio_snapshot(
                            directory,
                            project_id=project_id,
                        ),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode()
                    self._send(
                        HTTPStatus.OK,
                        "application/json; charset=utf-8",
                        body,
                        head_only=head_only,
                    )
                    return
                asset = STUDIO_ASSETS.get(path)
                if asset is not None:
                    name, content_type = asset
                    body = _asset_bytes(name)
                    self._send(
                        HTTPStatus.OK,
                        content_type,
                        body,
                        cache_control="no-cache",
                        head_only=head_only,
                    )
                    return
                self._send(
                    HTTPStatus.NOT_FOUND,
                    "text/plain; charset=utf-8",
                    b"Not found\n",
                    head_only=head_only,
                )
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as error:
                status, payload = _error_payload(error)
                body = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode()
                self._send(
                    status,
                    "application/json; charset=utf-8",
                    body,
                    head_only=head_only,
                )

        def do_GET(self) -> None:
            self._route()

        def do_HEAD(self) -> None:
            self._route(head_only=True)

        def _read_only(self) -> None:
            self._send(
                HTTPStatus.METHOD_NOT_ALLOWED,
                "application/json; charset=utf-8",
                b'{"schemaVersion":1,"ok":false,"error":{"code":"studio.read-only","message":"Studio routes are read-only","issues":[]}}',
            )

        def do_POST(self) -> None:
            self._read_only()

        def do_PUT(self) -> None:
            self._read_only()

        def do_PATCH(self) -> None:
            self._read_only()

        def do_DELETE(self) -> None:
            self._read_only()

        def do_OPTIONS(self) -> None:
            self._read_only()

        def log_message(self, format: str, *args: Any) -> None:
            return

    return StudioHandler


class AutoQuantStudioServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def create_studio_server(
    directory: str | Path,
    *,
    project_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> AutoQuantStudioServer:
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        raise AutoQuantValidationError(
            [_issue(port, "studio.port", "Studio port must be from 0 to 65535")]
        )
    root = Path(directory).expanduser().absolute()
    build_studio_snapshot(root, project_id=project_id)
    return AutoQuantStudioServer(
        (host, port),
        _handler(root, project_id),
    )


def serve_studio(
    directory: str | Path,
    *,
    project_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    server = create_studio_server(
        directory,
        project_id=project_id,
        host=host,
        port=port,
    )
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{display_host}:{server.server_port}"
    print(f"AutoQuant Studio: {url}", flush=True)
    print("Mode: local read-only observation", flush=True)
    if open_browser:
        threading.Thread(
            target=webbrowser.open,
            args=(url,),
            daemon=True,
        ).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


STUDIO_SNAPSHOT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant Studio snapshot",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "generatedAt",
        "source",
        "valid",
        "diagnostics",
        "projects",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": STUDIO_KIND},
        "generatedAt": {"type": "string", "minLength": 1},
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": ["scope", "rootDir", "workspace"],
            "properties": {
                "scope": {"enum": ["workspace", "project"]},
                "rootDir": {"type": "string", "minLength": 1},
                "workspace": {"type": ["object", "null"]},
            },
        },
        "valid": {"type": "boolean"},
        "diagnostics": {
            "type": "array",
            "items": {"$ref": "#/$defs/diagnostic"},
        },
        "projects": {
            "type": "array",
            "items": {"$ref": "#/$defs/project"},
        },
    },
    "$defs": {
        "diagnostic": {
            "type": "object",
            "additionalProperties": False,
            "required": ["category", "path", "code", "message"],
            "properties": {
                "category": {"type": "string", "minLength": 1},
                "path": {"type": "string", "minLength": 1},
                "code": {"type": "string", "minLength": 1},
                "message": {"type": "string", "minLength": 1},
            },
        },
        "project": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "id",
                "name",
                "description",
                "rootDir",
                "researchProgram",
                "researchProgramStatus",
                "dossierStatus",
                "dossiers",
                "intake",
                "factorExplorer",
                "portfolioExplorer",
                "rlExplorer",
                "commands",
                "valid",
                "diagnostics",
                "counts",
                "studies",
                "runs",
                "sessions",
                "timeline",
            ],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "name": {"type": "string", "minLength": 1},
                "description": {"type": "string"},
                "rootDir": {"type": "string", "minLength": 1},
                "researchProgram": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "text"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "text": {"type": "string"},
                    },
                },
                "researchProgramStatus": {"type": ["object", "null"]},
                "dossierStatus": {"type": ["object", "null"]},
                "dossiers": {"type": "array"},
                "intake": {"type": ["object", "null"]},
                "factorExplorer": {"type": ["object", "null"]},
                "portfolioExplorer": {"type": ["object", "null"]},
                "rlExplorer": {"type": ["object", "null"]},
                "commands": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "valid": {"type": "boolean"},
                "diagnostics": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/diagnostic"},
                },
                "counts": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "studies",
                        "runs",
                        "sessions",
                        "activeSessions",
                        "campaigns",
                        "runningCampaigns",
                        "delegatedSessions",
                        "reports",
                        "dossiers",
                        "verdicts",
                    ],
                    "properties": {
                        "studies": {"type": "integer", "minimum": 0},
                        "runs": {"type": "integer", "minimum": 0},
                        "sessions": {"type": "integer", "minimum": 0},
                        "activeSessions": {"type": "integer", "minimum": 0},
                        "campaigns": {"type": "integer", "minimum": 0},
                        "runningCampaigns": {"type": "integer", "minimum": 0},
                        "delegatedSessions": {"type": "integer", "minimum": 0},
                        "reports": {"type": "integer", "minimum": 0},
                        "dossiers": {"type": "integer", "minimum": 0},
                        "verdicts": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["KEEP", "REVERT", "CRASH"],
                            "properties": {
                                "KEEP": {"type": "integer", "minimum": 0},
                                "REVERT": {"type": "integer", "minimum": 0},
                                "CRASH": {"type": "integer", "minimum": 0},
                            },
                        },
                    },
                },
                "studies": {"type": "array"},
                "runs": {"type": "array"},
                "sessions": {"type": "array"},
                "timeline": {"type": "array"},
            },
        },
    },
}
