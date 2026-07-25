"""Point-in-time decision-support snapshots for immutable handoff artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .portfolio_explorer import load_portfolio_diagnostics
from .rl_explorer import load_rl_diagnostics
from .runs import load_run
from .studies import hash_json
from .templates import PORTFOLIO_STUDY_ID, RL_STUDY_ID
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
    portfolio_diagnostics = (
        load_portfolio_diagnostics(
            project,
            run_id,
            point_limit=40,
        )
        if run.result["study"]["id"] == PORTFOLIO_STUDY_ID
        else None
    )
    mechanical_decision = (
        portfolio_diagnostics["mechanicalDecision"]
        if portfolio_diagnostics is not None
        else None
    )
    sizing_anatomy = (
        portfolio_diagnostics["sizingAnatomy"]
        if portfolio_diagnostics is not None
        else None
    )
    strategy_viability = (
        portfolio_diagnostics["strategyViability"]
        if portfolio_diagnostics is not None
        else None
    )
    signal_monetization = (
        portfolio_diagnostics["signalMonetization"]
        if portfolio_diagnostics is not None
        else None
    )
    rl_diagnostics = (
        load_rl_diagnostics(
            project,
            run_id,
            point_limit=40,
        )
        if run.result["study"]["id"] == RL_STUDY_ID
        else None
    )
    rl_factor_fusion_diagnosis = (
        rl_diagnostics["factorFusionDiagnosis"]
        if rl_diagnostics is not None
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
        "portfolioSizingAnatomyHash": (
            hash_json(sizing_anatomy)
            if sizing_anatomy is not None
            else None
        ),
        "portfolioSizingAnatomy": sizing_anatomy,
        "portfolioStrategyViabilityHash": (
            hash_json(strategy_viability)
            if strategy_viability is not None
            else None
        ),
        "portfolioStrategyViability": strategy_viability,
        "portfolioSignalMonetizationHash": (
            hash_json(signal_monetization)
            if signal_monetization is not None
            else None
        ),
        "portfolioSignalMonetization": signal_monetization,
        "rlFactorFusionDiagnosisHash": (
            hash_json(rl_factor_fusion_diagnosis)
            if rl_factor_fusion_diagnosis is not None
            else None
        ),
        "rlFactorFusionDiagnosis": rl_factor_fusion_diagnosis,
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
    optional_pairs = (
        (
            "portfolioSizingAnatomyHash",
            "portfolioSizingAnatomy",
        ),
        (
            "portfolioStrategyViabilityHash",
            "portfolioStrategyViability",
        ),
        (
            "portfolioSignalMonetizationHash",
            "portfolioSignalMonetization",
        ),
        (
            "rlFactorFusionDiagnosisHash",
            "rlFactorFusionDiagnosis",
        ),
    )
    compatible_expected = dict(expected)
    complete_pairs = True
    for hash_key, object_key in optional_pairs:
        hash_present = hash_key in value
        object_present = object_key in value
        if hash_present != object_present:
            complete_pairs = False
            break
        if not hash_present:
            compatible_expected.pop(hash_key)
            compatible_expected.pop(object_key)
    if not complete_pairs or value != compatible_expected:
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
            "portfolioSizingAnatomyHash": None,
            "portfolioStrategyViabilityHash": None,
            "portfolioSignalMonetizationHash": None,
            "rlFactorFusionDiagnosisHash": None,
            "portfolio": None,
            "rl": None,
        }
    decision = value.get("portfolioMechanicalDecision")
    rl_diagnosis = value.get("rlFactorFusionDiagnosis")
    rl_summary = None
    if isinstance(rl_diagnosis, dict) and rl_diagnosis.get("available"):
        validation = rl_diagnosis["validation"]
        candidate = validation["candidateFactor"]
        transmission = validation["adaptiveTransmission"]
        stability = validation["stability"]
        rl_summary = {
            "method": rl_diagnosis["method"],
            "stage": rl_diagnosis["diagnosis"]["stage"],
            "iterationFocus": rl_diagnosis["diagnosis"][
                "iterationFocus"
            ],
            "candidateAssessment": candidate["assessment"],
            "candidateFixedSharpeDeltaVsBalanced": candidate[
                "fixedSleeveSharpeDeltaVsBalanced"
            ],
            "candidateLocalRewardDeltaVsBalanced": candidate[
                "meanLocalRewardDeltaVsBalanced"
            ],
            "candidateSelectedFrequency": candidate[
                "selectedFrequency"
            ],
            "candidateLocalBestFrequency": candidate[
                "localBestFrequency"
            ],
            "candidateOracleCaptureRate": candidate[
                "oracleCaptureRate"
            ],
            "grossActiveReturn": transmission[
                "meanTrialGrossActiveReturn"
            ],
            "incrementalCost": transmission[
                "meanTrialIncrementalCost"
            ],
            "netActiveReturn": transmission[
                "meanTrialNetActiveReturn"
            ],
            "sharpeAdvantage": transmission[
                "meanSharpeAdvantageVsSelectedBaseline"
            ],
            "positiveNetTrialRate": stability[
                "positiveNetTrialRate"
            ],
            "worstRegime": validation["lossLocator"][
                "worstRegime"
            ]["key"],
            "worstActionPair": validation["lossLocator"][
                "worstActionPair"
            ]["key"],
        }
    if not isinstance(decision, dict):
        if rl_summary is not None:
            return {
                "available": True,
                "reason": None,
                "runId": value["runId"],
                "resultHash": value["resultHash"],
                "portfolioMechanicalDecisionHash": value.get(
                    "portfolioMechanicalDecisionHash"
                ),
                "portfolioSizingAnatomyHash": value.get(
                    "portfolioSizingAnatomyHash"
                ),
                "portfolioStrategyViabilityHash": value.get(
                    "portfolioStrategyViabilityHash"
                ),
                "portfolioSignalMonetizationHash": value.get(
                    "portfolioSignalMonetizationHash"
                ),
                "rlFactorFusionDiagnosisHash": value.get(
                    "rlFactorFusionDiagnosisHash"
                ),
                "portfolio": None,
                "rl": rl_summary,
            }
        return {
            "available": False,
            "reason": "no-supported-leader-diagnosis",
            "runId": value.get("runId"),
            "resultHash": value.get("resultHash"),
            "portfolioMechanicalDecisionHash": value.get(
                "portfolioMechanicalDecisionHash"
            ),
            "portfolioSizingAnatomyHash": value.get(
                "portfolioSizingAnatomyHash"
            ),
            "portfolioStrategyViabilityHash": value.get(
                "portfolioStrategyViabilityHash"
            ),
            "portfolioSignalMonetizationHash": value.get(
                "portfolioSignalMonetizationHash"
            ),
            "rlFactorFusionDiagnosisHash": value.get(
                "rlFactorFusionDiagnosisHash"
            ),
            "portfolio": None,
            "rl": None,
        }
    signal = decision["signalGate"]
    target = decision["targetGate"]
    execution = decision["executionGate"]
    sizing = value.get("portfolioSizingAnatomy")
    sizing_summary = None
    if isinstance(sizing, dict):
        construction = sizing["construction"]
        sizing_summary = {
            "method": sizing["method"],
            "rawGross": construction["rawGross"],
            "governedGross": construction["governedGross"],
            "executedGross": construction["executedGross"],
            "unfundedGross": construction["unfundedGross"],
            "atCapAssets": sum(
                len(side["atCapAssets"]) for side in sizing["sides"]
            ),
            "componentRiskAvailable": sizing["componentRisk"][
                "available"
            ],
            "componentRiskConcentrationHhi": sizing["componentRisk"][
                "absoluteConcentrationHhi"
            ],
            "largestAbsoluteComponentRiskContributor": sizing[
                "componentRisk"
            ]["largestAbsoluteContributor"],
        }
    viability = value.get("portfolioStrategyViability")
    viability_summary = None
    if isinstance(viability, dict):
        validation = viability["validation"]
        test = viability["test"]
        friction = validation["friction"]
        temporal = validation["temporal"]
        viability_summary = {
            "method": viability["method"],
            "stage": viability["diagnosis"]["stage"],
            "iterationFocus": viability["diagnosis"][
                "iterationFocus"
            ],
            "factorRankIc": validation["factorRankIc"],
            "grossSharpe": validation["gross"]["sharpe"],
            "netSharpe": validation["net"]["sharpe"],
            "grossToNetSharpeDelta": friction[
                "grossToNetSharpeDelta"
            ],
            "baseCostBps": friction["baseCostBps"],
            "breakEvenCost": friction["breakEvenCost"],
            "annualizedOneWayTurnover": friction[
                "annualizedOneWayTurnover"
            ],
            "positiveNetMonthRate": temporal[
                "positiveNetMonthRate"
            ],
            "maximumUnderwaterBars": temporal[
                "maximumUnderwaterBars"
            ],
            "netTotalReturnWithoutBestDays": temporal[
                "netTotalReturnWithoutBestDays"
            ],
            "testNetSharpe": test["net"]["sharpe"],
        }
    monetization = value.get("portfolioSignalMonetization")
    monetization_summary = None
    if isinstance(monetization, dict):
        validation = monetization["validation"]
        stages = {
            item["id"]: item for item in validation["stages"]
        }
        monetization_summary = {
            "method": monetization["method"],
            "outcome": monetization["diagnosis"]["outcome"],
            "iterationFocus": monetization["diagnosis"][
                "iterationFocus"
            ],
            "largestAdverseStage": monetization["diagnosis"][
                "largestAdverseStage"
            ],
            "largestAdverseAnnualizedDelta": monetization["diagnosis"][
                "largestAdverseAnnualizedDelta"
            ],
            "equalIntentAnnualizedContribution": stages[
                "equalIntent"
            ]["annualizedContribution"],
            "executedGrossAnnualizedContribution": stages[
                "executedGross"
            ]["annualizedContribution"],
            "executedNetAnnualizedContribution": stages[
                "executedNet"
            ]["annualizedContribution"],
            "noTradeRetentionDates": validation["coverage"][
                "noTradeRetentionDates"
            ],
            "decisionDates": validation["coverage"]["decisionDates"],
        }
    return {
        "available": True,
        "reason": None,
        "runId": value["runId"],
        "resultHash": value["resultHash"],
        "portfolioMechanicalDecisionHash": value[
            "portfolioMechanicalDecisionHash"
        ],
        "portfolioSizingAnatomyHash": value.get(
            "portfolioSizingAnatomyHash"
        ),
        "portfolioStrategyViabilityHash": value.get(
            "portfolioStrategyViabilityHash"
        ),
        "portfolioSignalMonetizationHash": value.get(
            "portfolioSignalMonetizationHash"
        ),
        "rlFactorFusionDiagnosisHash": value.get(
            "rlFactorFusionDiagnosisHash"
        ),
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
            "sizing": sizing_summary,
            "viability": viability_summary,
            "monetization": monetization_summary,
        },
        "rl": None,
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


def sizing_anatomy_markdown_lines(
    support: dict[str, Any],
    *,
    heading: str,
    lane_name: str | None = None,
) -> list[str]:
    """Render the frozen unequal-weight construction and risk anatomy."""

    sizing = support.get("portfolioSizingAnatomy")
    if not isinstance(sizing, dict):
        return []
    construction = sizing["construction"]
    component = sizing["componentRisk"]
    prefix = f"{lane_name}: " if lane_name else ""
    lines = [
        heading,
        "",
        f"- {prefix}Sizing method / timestamp: `{sizing['method']}` / "
        f"`{sizing['timestamp']}`",
        "- Fixed rule: percentile-distance conviction ÷ causal trailing "
        "volatility, then same-side capped water-fill.",
        f"- Raw / governed / executed gross; unfunded gross: "
        f"`{construction['rawGross']}` / "
        f"`{construction['governedGross']}` / "
        f"`{construction['executedGross']}`; "
        f"`{construction['unfundedGross']}`",
        f"- Per-asset cap / covariance risk scale: "
        f"`{construction['maxAbsWeight']}` / "
        f"`{construction['riskGovernorScale']}`",
        f"- Executed component-risk availability / absolute HHI / largest "
        f"contributor: `{component['available']}` / "
        f"`{component['absoluteConcentrationHhi']}` / "
        f"`{component['largestAbsoluteContributor'] or 'none'}`",
    ]
    for side in sizing["sides"]:
        lines.append(
            f"- {side['side'].title()} side: "
            f"`{side['activeAssets']}` active; "
            f"`{side['fundedRawBudget']}` / "
            f"`{side['configuredBudget']}` funded; "
            f"cap capacity `{side['capCapacity']}`; at cap "
            + (
                ", ".join(f"`{asset}`" for asset in side["atCapAssets"])
                if side["atCapAssets"]
                else "none"
            )
            + f"; feasible `{side['allocationFeasible']}`"
        )
    lines.extend(
        [
            f"- Sizing hash: `{support['portfolioSizingAnatomyHash']}`",
            "- Authority: `quantitative-decision-support`; trading authority: "
            "`none`. Diagonal risk budget is a sizing heuristic; component "
            "risk is a covariance decomposition of the historical executed "
            "book. Neither is a live account risk forecast.",
            "",
            "| Asset / side | Score / conviction / trailing vol | "
            "Same-side strength | Proportional → raw | Governor → executed | "
            "Diagonal risk → component risk |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for position in sizing["positions"]:
        score = (
            f"P{position['score'] * 100.0:.0f}"
            if position["score"] is not None
            else "unavailable"
        )
        volatility = (
            f"{position['trailingVolatility']:.2%}"
            if position["trailingVolatility"] is not None
            else "unavailable"
        )
        cap_note = (
            " · at cap"
            if position["atCap"]
            else " · proportional exceeded cap"
            if position["proportionalWeightExceedsCap"]
            else ""
        )
        component_risk = (
            f"{position['componentRiskShare']:+.2%}"
            if position["componentRiskAvailable"]
            else "unavailable"
        )
        lines.append(
            f"| `{position['asset']}` / {position['side'].upper()} | "
            f"{score} / `{position['conviction']:.4f}` / {volatility} | "
            f"`{position['riskStrength']:.4f}` "
            f"({position['sameSideStrengthShare']:.2%}) | "
            f"{_signed_percent(position['proportionalWeightBeforeCap'])} → "
            f"{_signed_percent(position['rawWeight'])}{cap_note} | "
            f"{_signed_percent(position['governedWeight'])} → "
            f"{_signed_percent(position['executedWeight'])} | "
            f"{position['diagonalRiskBudgetShare']:+.2%} → "
            f"{component_risk} |"
        )
    lines.append("")
    return lines


def strategy_viability_markdown_lines(
    support: dict[str, Any],
    *,
    heading: str,
    lane_name: str | None = None,
) -> list[str]:
    """Render the frozen factor → gross → friction → net diagnosis."""

    viability = support.get("portfolioStrategyViability")
    if not isinstance(viability, dict):
        return []
    diagnosis = viability["diagnosis"]
    prefix = f"{lane_name}: " if lane_name else ""
    lines = [
        heading,
        "",
        f"- {prefix}Validation diagnosis / next research focus: "
        f"`{diagnosis['stage']}` / `{diagnosis['iterationFocus']}`",
        f"- Interpretation: {diagnosis['explanation']}",
        "- Diagnosis authority: `research-prioritization-only`; selection "
        "split: `validation`; test enters diagnosis: `False`; trading "
        "authority: `none`.",
        f"- Viability hash: "
        f"`{support['portfolioStrategyViabilityHash']}`",
        "",
        "| Split / role | Factor rank IC | Gross Sharpe → net Sharpe | "
        "Annual turnover / cost | Break-even cost | Positive months / "
        "max underwater | Without best 5 days |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for split_name in ("validation", "test"):
        split = viability[split_name]
        friction = split["friction"]
        temporal = split["temporal"]
        break_even = friction["breakEvenCost"]
        break_even_label = (
            f"{break_even['bps']:.2f} bps"
            if break_even["bps"] is not None
            else break_even["status"]
        )
        lines.append(
            f"| {split_name} / `{split['role']}` | "
            f"`{split['factorRankIc']:.4f}` | "
            f"`{split['gross']['sharpe']:.4f}` → "
            f"`{split['net']['sharpe']:.4f}` | "
            f"`{friction['annualizedOneWayTurnover']:.4f}` / "
            f"`{friction['totalCostDrag']:.2%}` | "
            f"{break_even_label} | "
            f"`{temporal['positiveNetMonthRate']:.2%}` / "
            f"`{temporal['maximumUnderwaterBars']}` bars | "
            f"`{temporal['netTotalReturnWithoutBestDays']:.2%}` |"
        )
    validation = viability["validation"]
    stress = ", ".join(
        f"{item['costBps']:.0f} bps → Sharpe {item['netSharpe']:.4f}"
        for item in validation["costStress"]
    )
    delay = validation["extraDelay"]
    lines.extend(
        [
            "",
            f"- Validation cost curve: {stress}.",
            f"- Validation extra-delay Sharpe / delta: "
            f"`{delay['netSharpe']:.4f}` / "
            f"`{delay['netSharpeDelta']:+.4f}`.",
            "- Return-per-turnover is arithmetic return basis points per unit "
            "of one-way portfolio replacement. Break-even cost is charged per "
            "traded notional on the frozen gross path; neither is a fill or "
            "impact estimate.",
            "",
        ]
    )
    return lines


def signal_monetization_markdown_lines(
    support: dict[str, Any],
    *,
    heading: str,
    lane_name: str | None = None,
) -> list[str]:
    """Render the frozen additive signal-to-portfolio transmission bridge."""

    monetization = support.get("portfolioSignalMonetization")
    if not isinstance(monetization, dict):
        return []
    diagnosis = monetization["diagnosis"]
    prefix = f"{lane_name}: " if lane_name else ""
    lines = [
        heading,
        "",
        f"- {prefix}Validation outcome / next research focus: "
        f"`{diagnosis['outcome']}` / `{diagnosis['iterationFocus']}`",
        f"- Largest adverse transformation / annualized additive delta: "
        f"`{diagnosis['largestAdverseStage']}` / "
        f"`{diagnosis['largestAdverseAnnualizedDelta']}`",
        f"- Interpretation: {diagnosis['explanation']}",
        "- The equal-intent layer is a normalized Mandate-constrained "
        "diagnostic. Contributions are additive weight × next-bar return, "
        "not separately compounded counterfactual portfolios.",
        "- Diagnosis authority: `research-prioritization-only`; selection "
        "split: `validation`; test enters diagnosis: `False`; trading "
        "authority: `none`.",
        f"- Monetization hash: "
        f"`{support['portfolioSignalMonetizationHash']}`",
        "",
        "| Split / role | Equal intent | Sized raw | Governed target | "
        "Executed gross | Executed net | No-trade retention |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for split_name in ("validation", "test"):
        split = monetization[split_name]
        stages = {item["id"]: item for item in split["stages"]}
        coverage = split["coverage"]
        lines.append(
            f"| `{split_name}` / `{split['role']}` | "
            f"{_signed_percent(stages['equalIntent']['annualizedContribution'])} | "
            f"{_signed_percent(stages['preGovernorSizing']['annualizedContribution'])} | "
            f"{_signed_percent(stages['governedTarget']['annualizedContribution'])} | "
            f"{_signed_percent(stages['executedGross']['annualizedContribution'])} | "
            f"{_signed_percent(stages['executedNet']['annualizedContribution'])} | "
            f"`{coverage['noTradeRetentionDates']}` / "
            f"`{coverage['decisionDates']}` dates |"
        )
    lines.extend(
        [
            "",
            "| Validation transformation | Annualized additive delta |",
            "| --- | --- |",
        ]
    )
    for delta in monetization["validation"]["deltas"]:
        lines.append(
            f"| {delta['label']} | "
            f"{_signed_percent(delta['annualizedContributionDelta'])} |"
        )
    lines.append("")
    return lines


def rl_factor_fusion_diagnosis_markdown_lines(
    support: dict[str, Any],
    *,
    heading: str,
    lane_name: str | None = None,
) -> list[str]:
    """Render the frozen candidate-to-adaptive-value diagnosis."""

    fusion = support.get("rlFactorFusionDiagnosis")
    if not isinstance(fusion, dict) or not fusion.get("available"):
        return []
    diagnosis = fusion["diagnosis"]
    validation = fusion["validation"]
    candidate = validation["candidateFactor"]
    transmission = validation["adaptiveTransmission"]
    stability = validation["stability"]
    losses = validation["lossLocator"]
    prefix = f"{lane_name}: " if lane_name else ""
    lines = [
        heading,
        "",
        f"- {prefix}Validation diagnosis / next research focus: "
        f"`{diagnosis['stage']}` / `{diagnosis['iterationFocus']}`",
        f"- Interpretation: {diagnosis['explanation']}",
        f"- Candidate factor assessment: `{candidate['assessment']}`; "
        "fixed-sleeve Sharpe delta versus balanced "
        f"`{candidate['fixedSleeveSharpeDeltaVsBalanced']}`; same-pretrade "
        "one-step reward delta versus balanced "
        f"`{candidate['meanLocalRewardDeltaVsBalanced']}`.",
        "- Candidate selected / locally best / local-best capture: "
        f"`{candidate['selectedFrequency']}` / "
        f"`{candidate['localBestFrequency']}` / "
        f"`{candidate['oracleCaptureRate']}`.",
        "- Validation mean-trial full-path gross edge / incremental cost / "
        "net active return: "
        f"`{transmission['meanTrialGrossActiveReturn']}` / "
        f"`{transmission['meanTrialIncrementalCost']}` / "
        f"`{transmission['meanTrialNetActiveReturn']}`.",
        "- Validation net-Sharpe advantage / information ratio / positive net "
        "trial-path rate: "
        f"`{transmission['meanSharpeAdvantageVsSelectedBaseline']}` / "
        f"`{transmission['informationRatio']}` / "
        f"`{stability['positiveNetTrialRate']}`.",
        "- Worst causal regime / action pair / switch state / asset gross "
        "contributor: "
        f"`{losses['worstRegime']['key']}` / "
        f"`{losses['worstActionPair']['key']}` / "
        f"`{losses['worstSwitchState']['key']}` / "
        f"`{losses['worstAssetGrossContribution']['asset']}`.",
        f"- Fusion diagnosis hash: "
        f"`{support['rlFactorFusionDiagnosisHash']}`",
        "- Local opportunity is a same-pretrade, one-step, ex-post audit. "
        "Adaptive transmission uses independent complete policy paths. "
        "Neither enters training, policy selection, KEEP/REVERT, or trading.",
        "- Authority: `research-prioritization-only`; selection split: "
        "`validation`; test enters diagnosis: `False`; trading authority: "
        "`none`.",
        "",
        "| Split / role | Candidate fixed Δ Sharpe | Candidate local Δ reward "
        "| Gross edge → net active | Sharpe advantage | Positive net trials |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for split_name, key in (
        ("validation", "validation"),
        ("test", "testAudit"),
    ):
        split = fusion[key]
        split_candidate = split["candidateFactor"]
        split_transmission = split["adaptiveTransmission"]
        split_stability = split["stability"]
        lines.append(
            f"| `{split_name}` / `{split['role']}` | "
            f"{split_candidate['fixedSleeveSharpeDeltaVsBalanced']:+.4f} | "
            f"{split_candidate['meanLocalRewardDeltaVsBalanced']:+.6f} | "
            f"{_signed_percent(split_transmission['meanTrialGrossActiveReturn'])} "
            f"→ {_signed_percent(split_transmission['meanTrialNetActiveReturn'])} | "
            f"{split_transmission['meanSharpeAdvantageVsSelectedBaseline']:+.4f} | "
            f"{split_stability['positiveNetTrialRate']:.2%} |"
        )
    lines.append("")
    return lines
