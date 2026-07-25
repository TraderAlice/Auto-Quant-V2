"""Point-in-time decision-support snapshots for immutable handoff artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .portfolio_explorer import load_portfolio_diagnostics
from .runs import load_run
from .studies import hash_json
from .templates import PORTFOLIO_STUDY_ID
from .workspace import (
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
)


LEADER_DECISION_SUPPORT_KIND = "autoquant-leader-decision-support"


def build_leader_decision_support(
    project: ProjectContext,
    run_id: str,
) -> dict[str, Any]:
    """Rebuild the bounded decision snapshot for one exact leader Run."""

    run = load_run(project, run_id)
    mechanical_decision = (
        load_portfolio_diagnostics(
            project,
            run_id,
            point_limit=40,
        )["mechanicalDecision"]
        if run.result["study"]["id"] == PORTFOLIO_STUDY_ID
        else None
    )
    return {
        "kind": LEADER_DECISION_SUPPORT_KIND,
        "runId": run.result["id"],
        "resultHash": run.manifest["resultHash"],
        "portfolioMechanicalDecisionHash": (
            hash_json(mechanical_decision)
            if mechanical_decision is not None
            else None
        ),
        "portfolioMechanicalDecision": mechanical_decision,
    }


def verify_leader_decision_support(
    project: ProjectContext,
    value: Any,
    run_id: str,
    path: Path | str,
) -> dict[str, Any]:
    """Require one frozen snapshot to equal the current immutable Run bytes."""

    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [
                ValidationIssue(
                    str(path),
                    "decision-support.type",
                    "Leader decision support must be an object",
                )
            ]
        )
    expected = build_leader_decision_support(project, run_id)
    if value != expected:
        raise AutoQuantValidationError(
            [
                ValidationIssue(
                    str(path),
                    "decision-support.mismatch",
                    "Frozen leader decision support differs from the immutable Run",
                )
            ]
        )
    return expected


def summarize_leader_decision_support(value: Any) -> dict[str, Any]:
    """Return a bounded Report-list/Studio projection without inventing evidence."""

    if not isinstance(value, dict):
        return {
            "available": False,
            "reason": "legacy-report",
            "runId": None,
            "resultHash": None,
            "portfolioMechanicalDecisionHash": None,
            "portfolio": None,
        }
    decision = value.get("portfolioMechanicalDecision")
    if not isinstance(decision, dict):
        return {
            "available": False,
            "reason": "not-portfolio-leader",
            "runId": value.get("runId"),
            "resultHash": value.get("resultHash"),
            "portfolioMechanicalDecisionHash": value.get(
                "portfolioMechanicalDecisionHash"
            ),
            "portfolio": None,
        }
    signal = decision["signalGate"]
    target = decision["targetGate"]
    execution = decision["executionGate"]
    return {
        "available": True,
        "reason": None,
        "runId": value["runId"],
        "resultHash": value["resultHash"],
        "portfolioMechanicalDecisionHash": value[
            "portfolioMechanicalDecisionHash"
        ],
        "portfolio": {
            "timestamp": decision["timestamp"],
            "family": signal["family"],
            "stateChanges": signal["stateChanges"],
            "riskGovernorScale": target["riskGovernorScale"],
            "proposedOneWayTurnover": execution[
                "proposedOneWayTurnover"
            ],
            "noTradeOneWay": execution["noTradeOneWay"],
            "rebalanced": execution["rebalanced"],
            "reason": execution["reason"],
            "positions": len(decision["positions"]),
            "tradingAuthority": decision["tradingAuthority"],
        },
    }


def _signed_percent(value: float) -> str:
    return f"{value:+.2%}"


def _signal_state(value: int) -> str:
    if value == 1:
        return "LONG"
    if value == -1:
        return "SHORT"
    return "FLAT"


def _trigger_label(trigger: dict[str, Any]) -> str:
    threshold = trigger["threshold"] * 100.0
    distance = trigger["distance"]
    buffer = (
        "rank unavailable"
        if distance is None
        else f"{distance * 100.0:.1f}pp buffer"
    )
    return (
        f"`{trigger['event']} {trigger['comparator']} P{threshold:.0f}` "
        f"({buffer})"
    )


def mechanical_decision_markdown_lines(
    support: dict[str, Any],
    *,
    heading: str,
    lane_name: str | None = None,
) -> list[str]:
    """Render the same frozen decision table for Report and Dossier Markdown."""

    decision = support.get("portfolioMechanicalDecision")
    if not isinstance(decision, dict):
        return []
    signal = decision["signalGate"]
    target = decision["targetGate"]
    execution = decision["executionGate"]
    prefix = f"{lane_name}: " if lane_name else ""
    ordinary = (
        "legacy unavailable"
        if execution["ordinaryRebalance"] is None
        else str(execution["ordinaryRebalance"])
    )
    risk_override = (
        "legacy unavailable"
        if execution["riskOverride"] is None
        else str(execution["riskOverride"])
    )
    lines = [
        heading,
        "",
        f"- {prefix}Leader Run / result hash: `{support['runId']}` / "
        f"`{support['resultHash']}`",
        f"- Decision timestamp / construction: `{decision['timestamp']}` / "
        f"`{signal['family']}`",
        f"- Signal state changes / unavailable scores / context assets: "
        f"`{signal['stateChanges']}` / `{signal['unavailableScores']}` / "
        f"`{signal['contextAssets']}`",
        f"- Pre-governor / governed target gross; risk scale / status: "
        f"`{target['preGovernorGross']}` / "
        f"`{target['governedTargetGross']}`; "
        f"`{target['riskGovernorScale']}` / "
        f"`{target['riskGovernorStatus']}`",
        f"- Proposed one-way turnover / no-trade band: "
        f"`{execution['proposedOneWayTurnover']}` / "
        f"`{execution['noTradeOneWay']}`",
        f"- Ordinary rebalance / risk override / final rebalance: "
        f"`{ordinary}` / `{risk_override}` / `{execution['rebalanced']}` "
        f"(`{execution['reason']}`)",
        f"- Decision hash: "
        f"`{support['portfolioMechanicalDecisionHash']}`",
        "- Authority: `quantitative-decision-support`; trading authority: "
        "`none`. Percentile buffers hold peer ranks fixed and are not price "
        "targets, forecasts, probabilities, orders, or account positions.",
        "",
        "| Asset / state | Score / event | Next permitted state conditions | "
        "Raw → governed target | Pretrade → executed | Historical action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for position in decision["positions"]:
        triggers = (
            "; ".join(
                _trigger_label(trigger)
                for trigger in position["nextTriggers"]
            )
            if position["nextTriggers"]
            else "none — context-only, no position authority"
        )
        score = (
            f"P{position['score'] * 100.0:.0f}"
            if position["scoreAvailable"]
            else "unavailable"
        )
        state = (
            _signal_state(position["signalState"])
            if position["tradable"]
            else "CONTEXT"
        )
        lines.append(
            f"| `{position['asset']}` / {state} | {score} / "
            f"`{position['signalEvent']}` | {triggers} | "
            f"{_signed_percent(position['preGovernorTargetWeight'])} → "
            f"{_signed_percent(position['targetWeight'])} | "
            f"{_signed_percent(position['pretradeWeight'])} → "
            f"{_signed_percent(position['executedWeight'])} | "
            f"`{position['executionAction']}` / "
            f"`{position['executionReason']}` |"
        )
    lines.append("")
    return lines
