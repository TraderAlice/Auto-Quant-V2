"""Shared request-bound prediction-population semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CROSS_SECTIONAL_MODE = "cross-sectional"
SINGLE_ASSET_TEMPORAL_MODE = "single-asset-temporal"
TWO_ASSET_RELATIVE_VALUE_MODE = "two-asset-relative-value"
TEMPORAL_EVALUATION_MODES = frozenset(
    {SINGLE_ASSET_TEMPORAL_MODE, TWO_ASSET_RELATIVE_VALUE_MODE}
)
MIN_CROSS_SECTIONAL_ASSETS = 4
TEMPORAL_SCORE_WINDOW = 60
TEMPORAL_SCORE_MINIMUM = 20
SIGNAL_TRANSLATION_METHOD = "prediction-mode-causal-percentile-v2"


class PredictionModeError(ValueError):
    """A fixed Factor claim and Portfolio Mandate do not define one mode."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class PredictionPopulation:
    research_assets: tuple[str, ...]
    prediction_assets: tuple[str, ...]
    context_assets: tuple[str, ...]
    authority: str
    evaluation_mode: str
    asset_position_roles: dict[str, str]

    @property
    def relative_value_pair(self) -> dict[str, Any] | None:
        if self.evaluation_mode != TWO_ASSET_RELATIVE_VALUE_MODE:
            return None
        left, right = self.prediction_assets
        return {
            "left_asset": left,
            "right_asset": right,
            "factor_contrast": "factor(left_asset)-factor(right_asset)",
            "target_contrast": (
                "forward_return(left_asset)-forward_return(right_asset)"
            ),
            "construction": "symmetric-dollar-neutral-equal-funded",
            "beta_neutral": False,
        }

    def as_metrics(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "evaluation_mode": self.evaluation_mode,
            "research_assets": list(self.research_assets),
            "prediction_assets": list(self.prediction_assets),
            "context_assets": list(self.context_assets),
            "asset_position_roles": dict(self.asset_position_roles),
            "trading_authority": "none",
            "relative_value_pair": self.relative_value_pair,
        }


def signal_translation_contract(
    population: dict[str, Any],
) -> dict[str, Any]:
    """Return the fixed Factor-to-decision-score semantics for one mode."""

    mode = population.get("evaluation_mode")
    if mode not in {
        CROSS_SECTIONAL_MODE,
        SINGLE_ASSET_TEMPORAL_MODE,
        TWO_ASSET_RELATIVE_VALUE_MODE,
    }:
        raise PredictionModeError(
            "prediction-universe.evaluation-mode",
            "Prediction population has no supported evaluation mode",
        )
    return {
        "method": SIGNAL_TRANSLATION_METHOD,
        "evaluation_mode": mode,
        "prediction_assets": population.get("prediction_assets"),
        "context_assets": population.get("context_assets"),
        "authority": population.get("authority"),
        "score_basis": (
            "same-timestamp-prediction-population"
            if mode == CROSS_SECTIONAL_MODE
            else "causal-own-factor-history"
            if mode == SINGLE_ASSET_TEMPORAL_MODE
            else "causal-ordered-factor-spread-history"
        ),
        "window_observations": (
            None if mode == CROSS_SECTIONAL_MODE else TEMPORAL_SCORE_WINDOW
        ),
        "minimum_observations": (
            MIN_CROSS_SECTIONAL_ASSETS
            if mode == CROSS_SECTIONAL_MODE
            else TEMPORAL_SCORE_MINIMUM
        ),
        "relative_value_pair": population.get("relative_value_pair"),
        "context_score": "unavailable-never-ranked",
        "selection_authority": "fixed-mechanical-translation",
        "trading_authority": "none",
    }

def resolve_prediction_population(
    research_universe: list[str],
    factor_claim: dict[str, Any],
    mandate: dict[str, Any],
) -> PredictionPopulation:
    """Resolve one strict population shared by Factor, Portfolio, and RL."""

    if (
        not research_universe
        or len(research_universe) != len(set(research_universe))
        or any(not isinstance(asset, str) or not asset for asset in research_universe)
    ):
        raise PredictionModeError(
            "prediction-universe.research-universe",
            "Research universe must contain unique non-empty asset symbols",
        )
    if mandate.get("researchUniverse") != research_universe:
        raise PredictionModeError(
            "prediction-universe.research-universe",
            "Portfolio Mandate researchUniverse must equal the Study universe",
        )
    claim = factor_claim.get("claim")
    if claim not in {
        "decision-signal",
        "novel-factor",
        "known-style-validation",
    }:
        raise PredictionModeError(
            "prediction-universe.claim",
            "Factor claim does not define a supported prediction population",
        )
    construction = mandate.get("construction")
    if not isinstance(construction, dict):
        raise PredictionModeError(
            "prediction-universe.mandate",
            "Portfolio Mandate construction is unavailable",
        )
    roles = construction.get("assetPositionRoles")
    if not isinstance(roles, dict) or set(roles) != set(research_universe):
        raise PredictionModeError(
            "prediction-universe.mandate",
            "Portfolio Mandate roles must cover the Study universe exactly",
        )
    tradable = mandate.get("tradableAssets")
    if (
        not isinstance(tradable, list)
        or not tradable
        or len(tradable) != len(set(tradable))
        or any(asset not in research_universe for asset in tradable)
    ):
        raise PredictionModeError(
            "prediction-universe.mandate",
            "Portfolio Mandate tradableAssets are invalid",
        )
    if claim == "decision-signal":
        prediction_assets = list(tradable)
        authority = "portfolio-mandate-tradable-assets"
    else:
        prediction_assets = list(research_universe)
        authority = "factor-claim-research-universe"
    context_assets = [
        asset for asset in research_universe if asset not in prediction_assets
    ]

    if len(prediction_assets) == 1:
        if claim != "decision-signal":
            raise PredictionModeError(
                "prediction-universe.claim",
                "Single-asset temporal evaluation is available only for a "
                "request-bound decision-signal claim",
            )
        evaluation_mode = SINGLE_ASSET_TEMPORAL_MODE
    elif len(prediction_assets) == 2:
        if claim != "decision-signal":
            raise PredictionModeError(
                "prediction-universe.claim",
                "Two-asset relative-value evaluation is available only for "
                "a request-bound decision-signal claim",
            )
        if (
            construction.get("family") != "dollar-neutral"
            or construction.get("netRule") != "zero"
            or any(roles.get(asset) != "two-sided" for asset in prediction_assets)
        ):
            raise PredictionModeError(
                "prediction-universe.relative-value-mandate",
                "Two-asset relative-value evaluation requires a symmetric "
                "two-sided dollar-neutral Portfolio Mandate",
            )
        evaluation_mode = TWO_ASSET_RELATIVE_VALUE_MODE
    elif len(prediction_assets) >= MIN_CROSS_SECTIONAL_ASSETS:
        evaluation_mode = CROSS_SECTIONAL_MODE
    else:
        raise PredictionModeError(
            "prediction-universe.population",
            "Prediction supports one request-bound temporal asset, exactly "
            "two symmetric dollar-neutral relative-value assets, or at least "
            f"{MIN_CROSS_SECTIONAL_ASSETS} cross-sectional prediction assets; "
            f"received {len(prediction_assets)}. A three-asset relative basket "
            "requires explicit caller-owned contrast weights.",
        )

    return PredictionPopulation(
        research_assets=tuple(research_universe),
        prediction_assets=tuple(prediction_assets),
        context_assets=tuple(context_assets),
        authority=authority,
        evaluation_mode=evaluation_mode,
        asset_position_roles={
            asset: str(roles[asset]) for asset in research_universe
        },
    )
