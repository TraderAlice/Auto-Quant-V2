from __future__ import annotations

import copy
import unittest

import jsonschema
import numpy as np
import pandas as pd

from autoquant.mandates import (
    PORTFOLIO_MANDATE_JSON_SCHEMA,
    build_portfolio_mandate,
    validate_portfolio_mandate,
)
from autoquant.project_templates.ohlcv_portfolio_lab.portfolio_core import (
    PortfolioFailure,
    constraint_audit,
    construct_signal_policy,
)
from autoquant.workspace import AutoQuantValidationError


UNIVERSE = ["A", "B", "C", "D", "E"]


def request(direction: str, assets: list[str]) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "autoquant-research-request",
        "title": "Mandate test",
        "question": "Which requested positions have governed evidence?",
        "decisionContext": "OpenAlice delegated a bounded research question.",
        "assets": [
            {"symbol": asset, "assetClass": "equity", "venue": "TEST"}
            for asset in assets
        ],
        "direction": direction,
        "horizon": "one month",
        "hypotheses": [],
        "constraints": [],
        "deliverables": ["portfolio evidence"],
        "source": {
            "system": "openalice",
            "workspaceId": "desk",
            "sessionId": "request",
            "artifactPath": None,
            "artifactRevision": None,
        },
    }


def panels() -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.bdate_range("2025-01-02", periods=60)
    factors = pd.DataFrame(
        np.tile([5.0, 4.0, 3.0, 2.0, 1.0], (len(index), 1)),
        index=index,
        columns=UNIVERSE,
    )
    closes = pd.DataFrame(
        {
            asset: 100.0
            * np.exp(np.cumsum(np.full(len(index), 0.001 + number * 0.0001)))
            for number, asset in enumerate(UNIVERSE)
        },
        index=index,
    )
    return factors, closes


class PortfolioMandateTests(unittest.TestCase):
    def test_request_mapping_is_strict_content_derived_and_schema_valid(self) -> None:
        mandate = build_portfolio_mandate(request("long", ["A", "B"]), UNIVERSE)

        self.assertEqual(mandate["source"]["direction"], "long")
        self.assertEqual(mandate["construction"]["family"], "long-cash")
        self.assertEqual(mandate["tradableAssets"], ["A", "B"])
        self.assertEqual(mandate["contextAssets"], ["C", "D", "E"])
        self.assertEqual(
            mandate["construction"]["benchmark"],
            "equal-weight-long-tradable",
        )
        self.assertEqual(validate_portfolio_mandate(mandate), mandate)
        jsonschema.Draft202012Validator(
            PORTFOLIO_MANDATE_JSON_SCHEMA,
            format_checker=jsonschema.FormatChecker(),
        ).validate(mandate)

        tampered = copy.deepcopy(mandate)
        tampered["tradableAssets"] = ["A", "C"]
        with self.assertRaisesRegex(
            AutoQuantValidationError,
            "Context assets|derived",
        ):
            validate_portfolio_mandate(tampered)

    def test_directional_policy_trades_only_requested_sign_and_retains_cash(self) -> None:
        factors, closes = panels()
        for direction, assets, sign in (
            ("long", ["A", "B"], 1),
            ("short", ["D", "E"], -1),
        ):
            with self.subTest(direction=direction):
                mandate = build_portfolio_mandate(
                    request(direction, assets),
                    UNIVERSE,
                )
                construction = construct_signal_policy(
                    factors,
                    closes,
                    mandate=mandate,
                )
                active = construction.targets[
                    construction.targets.abs().sum(axis=1) > 1e-12
                ]
                self.assertFalse(active.empty)
                self.assertTrue(
                    (active[mandate["contextAssets"]].abs() <= 1e-12)
                    .all()
                    .all()
                )
                self.assertTrue((active[assets] * sign >= -1e-12).all().all())
                self.assertLessEqual(
                    float(active.abs().sum(axis=1).max()),
                    0.60 + 1e-9,
                )
                audit = constraint_audit(
                    construction.targets,
                    mandate=mandate,
                )
                self.assertTrue(audit["passed"])
                self.assertEqual(audit["maximum_context_weight"], 0.0)
                self.assertEqual(audit["maximum_opposite_exposure"], 0.0)
                context_rows = construction.ledger[
                    construction.ledger["asset"].isin(
                        mandate["contextAssets"]
                    )
                ]
                self.assertTrue((~context_rows["tradable"]).all())
                self.assertTrue(
                    (context_rows["signal_event"] == "context_only").all()
                )
                self.assertTrue(
                    (context_rows["allocation_status"] == "context_only").all()
                )

    def test_underfunded_relative_value_stays_flat_instead_of_trading_peers(self) -> None:
        factors, closes = panels()
        mandate = build_portfolio_mandate(
            request("relative-value", ["A", "E"]),
            UNIVERSE,
        )
        construction = construct_signal_policy(
            factors,
            closes,
            mandate=mandate,
        )

        self.assertTrue(
            (construction.targets.abs().sum(axis=1) <= 1e-12).all()
        )
        with self.assertRaisesRegex(PortfolioFailure, "No active targets"):
            constraint_audit(construction.targets, mandate=mandate)
        tradable_rows = construction.ledger[
            construction.ledger["tradable"]
        ]
        self.assertIn(
            "insufficient_side_breadth",
            set(tradable_rows["allocation_status"]),
        )

    def test_directional_all_cash_book_is_a_valid_mandate_outcome(self) -> None:
        mandate = build_portfolio_mandate(
            request("long", ["A", "B"]),
            UNIVERSE,
        )
        targets = pd.DataFrame(
            0.0,
            index=pd.bdate_range("2025-01-02", periods=4),
            columns=UNIVERSE,
        )

        audit = constraint_audit(targets, mandate=mandate)

        self.assertTrue(audit["passed"])
        self.assertEqual(audit["active_dates"], 0)
        self.assertEqual(audit["maximum_gross_exposure"], 0.0)
        self.assertEqual(audit["maximum_context_weight"], 0.0)

    def test_template_default_explicitly_preserves_research_neutral_behavior(self) -> None:
        mandate = build_portfolio_mandate(None, UNIVERSE)

        self.assertEqual(mandate["source"]["kind"], "template-default")
        self.assertEqual(mandate["source"]["direction"], "research-only")
        self.assertEqual(mandate["tradableAssets"], UNIVERSE)
        self.assertEqual(mandate["contextAssets"], [])
        self.assertEqual(mandate["construction"]["family"], "dollar-neutral")
        self.assertEqual(
            mandate["construction"]["benchmark"],
            "equal-weight-long-research-universe",
        )


if __name__ == "__main__":
    unittest.main()
