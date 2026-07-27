from __future__ import annotations

import unittest
from types import SimpleNamespace

import pandas as pd

from autoquant.factor_runtime import (
    FactorRuntimeError,
    build_factor_panel,
    evaluate_factor,
    values_to_wide,
)


def make_frames() -> dict[str, pd.DataFrame]:
    timestamps = pd.date_range("2026-01-01", periods=12, freq="1h", tz="UTC")
    frames: dict[str, pd.DataFrame] = {}
    for offset, asset in enumerate(("ALPHA", "BRAVO", "CHARLIE"), start=1):
        close = pd.Series(
            [100.0 + offset * step + (offset - 2) * step**2 / 20 for step in range(12)]
        )
        frames[asset] = pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": close - 0.2,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1_000.0 + offset * 10.0 + close.index * offset,
            }
        )
    return frames


class PanelFactorRuntimeTests(unittest.TestCase):
    def test_cross_asset_factor_uses_same_timestamp_market_context(self) -> None:
        panel = build_factor_panel(
            make_frames(),
            universe=["ALPHA", "BRAVO", "CHARLIE"],
        )

        def compute_factor(candidate_panel: pd.DataFrame) -> pd.Series:
            momentum = candidate_panel.groupby(
                "asset",
                sort=False,
            )["close"].pct_change(2, fill_method=None)
            market = momentum.groupby(
                candidate_panel["timestamp"],
                sort=False,
            ).transform("mean")
            return momentum - market

        evaluated = evaluate_factor(
            SimpleNamespace(compute_factor=compute_factor),
            panel,
        )
        wide = values_to_wide(
            panel,
            evaluated.values,
            universe=["ALPHA", "BRAVO", "CHARLIE"],
        )

        self.assertEqual(list(wide.columns), ["ALPHA", "BRAVO", "CHARLIE"])
        self.assertGreater(len(evaluated.causality_cuts), 0)
        self.assertTrue(
            (wide.dropna().sum(axis=1).abs() < 1e-12).all(),
        )
        self.assertGreater(
            float(wide["CHARLIE"].dropna().iloc[-1]),
            float(wide["ALPHA"].dropna().iloc[-1]),
        )

    def test_declared_components_share_the_panel_contract(self) -> None:
        panel = build_factor_panel(make_frames())

        def components(candidate_panel: pd.DataFrame) -> pd.DataFrame:
            momentum = candidate_panel.groupby(
                "asset",
                sort=False,
            )["close"].pct_change(2, fill_method=None)
            rank = momentum.groupby(
                candidate_panel["timestamp"],
                sort=False,
            ).rank(pct=True)
            return pd.DataFrame(
                {
                    "asset_momentum": momentum,
                    "cross_sectional_rank": rank,
                },
                index=candidate_panel.index,
            )

        module = SimpleNamespace(
            FACTOR_COMPONENTS={
                "asset_momentum": {
                    "label": "Two-bar asset momentum",
                    "intervals": ["base"],
                    "hypothesis": "Recent asset momentum persists.",
                },
                "cross_sectional_rank": {
                    "label": "Contemporaneous momentum rank",
                    "intervals": ["base"],
                    "hypothesis": "Relative strength persists cross-sectionally.",
                },
            },
            compute_factor_components=components,
            compute_factor=lambda candidate_panel: components(candidate_panel)[
                "cross_sectional_rank"
            ],
        )

        evaluated = evaluate_factor(module, panel)

        self.assertIsNotNone(evaluated.components)
        assert evaluated.components is not None
        self.assertEqual(
            list(evaluated.components.values.columns),
            ["asset_momentum", "cross_sectional_rank"],
        )

    def test_future_panel_access_is_rejected(self) -> None:
        panel = build_factor_panel(make_frames())

        def compute_factor(candidate_panel: pd.DataFrame) -> pd.Series:
            future = candidate_panel.groupby(
                "asset",
                sort=False,
            )["close"].shift(-1)
            return future / candidate_panel["close"] - 1.0

        with self.assertRaisesRegex(
            FactorRuntimeError,
            "future timestamps",
        ) as caught:
            evaluate_factor(
                SimpleNamespace(compute_factor=compute_factor),
                panel,
            )
        self.assertEqual(caught.exception.code, "factor.lookahead")

    def test_mutation_nondeterminism_and_alignment_are_rejected(self) -> None:
        panel = build_factor_panel(make_frames())

        def mutate(candidate_panel: pd.DataFrame) -> pd.Series:
            candidate_panel["bad"] = 1.0
            return candidate_panel["close"]

        calls = 0

        def nondeterministic(candidate_panel: pd.DataFrame) -> pd.Series:
            nonlocal calls
            calls += 1
            return candidate_panel["close"] + calls

        cases = (
            (
                "factor.mutation",
                SimpleNamespace(compute_factor=mutate),
            ),
            (
                "factor.nondeterministic",
                SimpleNamespace(compute_factor=nondeterministic),
            ),
            (
                "factor.alignment",
                SimpleNamespace(
                    compute_factor=lambda candidate_panel: candidate_panel[
                        "close"
                    ].iloc[:-1]
                ),
            ),
        )
        for expected, module in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(FactorRuntimeError) as caught:
                    evaluate_factor(module, panel)
                self.assertEqual(caught.exception.code, expected)

    def test_panel_builder_rejects_inconsistent_asset_columns(self) -> None:
        frames = make_frames()
        frames["BRAVO"] = frames["BRAVO"].drop(columns="volume")

        with self.assertRaises(FactorRuntimeError) as caught:
            build_factor_panel(frames)

        self.assertEqual(caught.exception.code, "factor.panel-columns")

    def test_evaluator_rejects_missing_identity_and_noncanonical_order(self) -> None:
        panel = build_factor_panel(make_frames())
        module = SimpleNamespace(
            compute_factor=lambda candidate_panel: candidate_panel["close"],
        )

        cases = (
            ("factor.panel-columns", panel.drop(columns="asset")),
            (
                "factor.panel-order",
                panel.sort_values(
                    ["asset", "timestamp"],
                    kind="stable",
                ).reset_index(drop=True),
            ),
        )
        for expected, invalid in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(FactorRuntimeError) as caught:
                    evaluate_factor(module, invalid)
                self.assertEqual(caught.exception.code, expected)


if __name__ == "__main__":
    unittest.main()
