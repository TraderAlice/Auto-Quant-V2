from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from autoquant.skill_bundle import (
    SKILL_DISCOVERY_ROOTS,
    WORKSPACE_SKILLS_MANIFEST,
    SkillBundleError,
    bundled_workspace_skills,
    materialize_workspace_skills,
    verify_materialized_workspace_skills,
)
from autoquant.workspace import (
    WORKSPACE_MANIFEST,
    AutoQuantValidationError,
    initialize_workspace,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "autoquant" / "workspace_skills"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkspaceSkillTests(unittest.TestCase):
    def test_canonical_bundle_materializes_and_detects_drift(self) -> None:
        expected_ids = {
            "acquire-market-ohlcv",
            "fetch-binance-ohlcv",
            "fetch-eastmoney-ohlcv",
            "fetch-nasdaq-ohlcv",
            "fetch-naver-ohlcv",
            "fetch-tencent-ohlcv",
            "fetch-twse-ohlcv",
            "fetch-yahoo-ohlcv",
            "package-autoquant-ohlcv",
        }
        self.assertEqual(
            {skill["id"] for skill in bundled_workspace_skills()},
            expected_ids,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = materialize_workspace_skills(root)
            self.assertEqual(
                {skill["id"] for skill in manifest["skills"]},
                expected_ids,
            )
            self.assertEqual(
                verify_materialized_workspace_skills(root),
                manifest,
            )
            for discovery_root in SKILL_DISCOVERY_ROOTS:
                self.assertEqual(
                    {
                        path.name
                        for path in (root / discovery_root).iterdir()
                    },
                    expected_ids,
                )

            drifted = (
                root
                / SKILL_DISCOVERY_ROOTS[0]
                / "acquire-market-ohlcv"
                / "SKILL.md"
            )
            drifted.write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(SkillBundleError, "drifted"):
                verify_materialized_workspace_skills(root)

    def test_workspace_init_materializes_skills_and_conflict_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = initialize_workspace(Path(directory) / "new")
            verified = verify_materialized_workspace_skills(
                workspace.root_dir
            )
            self.assertTrue((workspace.root_dir / WORKSPACE_SKILLS_MANIFEST).is_file())
            self.assertEqual(len(verified["skills"]), 9)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "adopted"
            conflict = (
                root
                / ".agents"
                / "skills"
                / "acquire-market-ohlcv"
            )
            conflict.mkdir(parents=True)
            marker = conflict / "caller.txt"
            marker.write_text("preserve\n", encoding="utf-8")
            with self.assertRaises(AutoQuantValidationError) as caught:
                initialize_workspace(root, adopt_existing=True)
            self.assertEqual(
                {issue.code for issue in caught.exception.issues},
                {"workspace.skill-bundle"},
            )
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve\n")
            self.assertFalse((root / WORKSPACE_MANIFEST).exists())
            self.assertFalse((root / "projects").exists())

    def test_yahoo_adjustment_applies_ratio_to_all_ohlc_only(self) -> None:
        yahoo = load_script(
            "autoquant_skill_yahoo",
            SKILLS
            / "fetch-yahoo-ohlcv"
            / "scripts"
            / "fetch_yahoo_daily.py",
        )
        result = {
            "timestamp": [1_704_153_600, 1_704_240_000],
            "indicators": {
                "quote": [
                    {
                        "open": [100.0, 110.0],
                        "high": [120.0, 115.0],
                        "low": [90.0, 100.0],
                        "close": [100.0, 110.0],
                        "volume": [1_000.0, 2_000.0],
                    }
                ],
                "adjclose": [{"adjclose": [50.0, 110.0]}],
            },
        }
        frame, audit = yahoo.frame_for(
            "SYNTH",
            result,
            "provider-adjusted",
        )
        self.assertEqual(frame.loc[0, "open"], 50.0)
        self.assertEqual(frame.loc[0, "high"], 60.0)
        self.assertEqual(frame.loc[0, "low"], 45.0)
        self.assertEqual(frame.loc[0, "close"], 50.0)
        self.assertEqual(frame.loc[0, "volume"], 1_000.0)
        self.assertEqual(audit["adjustedFactorRows"], 1)

    def test_yahoo_session_date_boundary_is_applied_after_parsing(self) -> None:
        yahoo = load_script(
            "autoquant_skill_yahoo_bounds",
            SKILLS
            / "fetch-yahoo-ohlcv"
            / "scripts"
            / "fetch_yahoo_daily.py",
        )
        frame = pd.DataFrame(
            {
                "date": ["2026-07-29", "2026-07-30"],
                "open": [1.0, 2.0],
                "high": [1.0, 2.0],
                "low": [1.0, 2.0],
                "close": [1.0, 2.0],
                "volume": [10.0, 20.0],
            }
        )
        bounded, dropped = yahoo.bound_session_dates(
            frame,
            yahoo.parse_date("2026-07-29"),
            yahoo.parse_date("2026-07-30"),
        )
        self.assertEqual(bounded["date"].tolist(), ["2026-07-29"])
        self.assertEqual(dropped, 1)

    def test_eastmoney_lots_become_shares_only_after_amount_check(self) -> None:
        eastmoney = load_script(
            "autoquant_skill_eastmoney",
            SKILLS
            / "fetch-eastmoney-ohlcv"
            / "scripts"
            / "fetch_eastmoney_daily.py",
        )
        payload = {
            "rc": 0,
            "data": {
                "code": "600519",
                "name": "fixture",
                "market": 1,
                "decimal": 2,
                "klines": [
                    (
                        "2026-07-28,1400.00,1410.00,1420.00,1390.00,"
                        "1000,140500000,2.13,0.71,10.00,0.01"
                    ),
                    (
                        "2026-07-29,1410.00,1400.00,1430.00,1395.00,"
                        "2000,281000000,2.48,-0.71,-10.00,0.02"
                    ),
                ],
            },
        }
        frame, audit = eastmoney.parse_payload(
            "1.600519",
            json.dumps(payload).encode(),
            eastmoney.date(2026, 7, 28),
            eastmoney.date(2026, 7, 30),
        )
        self.assertEqual(frame["volume"].tolist(), [100_000.0, 200_000.0])
        self.assertEqual(audit["providerVolumeUnit"], "lot")
        self.assertEqual(audit["outputVolumeUnit"], "share")
        self.assertEqual(audit["amountVwapRowsChecked"], 2)

        payload["data"]["klines"][0] = (
            "2026-07-28,1400.00,1410.00,1420.00,1390.00,"
            "1000,1405000,2.13,0.71,10.00,0.01"
        )
        with self.assertRaisesRegex(ValueError, "lot-to-share"):
            eastmoney.parse_payload(
                "1.600519",
                json.dumps(payload).encode(),
                eastmoney.date(2026, 7, 28),
                eastmoney.date(2026, 7, 30),
            )

    def test_tencent_lots_become_shares_and_prefix_matches_venue(self) -> None:
        tencent = load_script(
            "autoquant_skill_tencent",
            SKILLS
            / "fetch-tencent-ohlcv"
            / "scripts"
            / "fetch_tencent_daily.py",
        )
        payload = {
            "code": 0,
            "msg": "",
            "data": {
                "sh600519": {
                    "day": [
                        [
                            "2026-07-28",
                            "1400",
                            "1410",
                            "1420",
                            "1390",
                            "1000",
                        ],
                        [
                            "2026-07-29",
                            "1410",
                            "1400",
                            "1430",
                            "1395",
                            "2000",
                        ],
                    ],
                    "qt": {"sh600519": ["fixture"]},
                }
            },
        }
        frame, audit = tencent.parse_payload(
            "sh600519",
            json.dumps(payload).encode(),
            tencent.date(2026, 7, 28),
            tencent.date(2026, 7, 30),
        )
        self.assertEqual(frame["volume"].tolist(), [100_000.0, 200_000.0])
        self.assertEqual(audit["volumeMultiplier"], 100)
        with tempfile.TemporaryDirectory() as directory:
            assets = Path(directory) / "assets.json"
            assets.write_text(
                json.dumps(
                    [
                        {
                            "symbol": "600519",
                            "providerSymbol": "sz600519",
                            "venue": "XSHG",
                            "currency": "CNY",
                            "assetClass": "equity",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "prefix mismatches"):
                tencent.load_assets(assets)

    def test_twse_monthly_rows_preserve_official_share_volume(self) -> None:
        twse = load_script(
            "autoquant_skill_twse",
            SKILLS
            / "fetch-twse-ohlcv"
            / "scripts"
            / "fetch_twse_daily.py",
        )
        payload = {
            "stat": "OK",
            "title": "113/07 2330",
            "fields": [
                "Date",
                "Trade Volume",
                "Trade Value",
                "Opening Price",
                "Highest Price",
                "Lowest Price",
                "Closing Price",
                "Change",
                "Transaction",
            ],
            "data": [
                [
                    "113/07/01",
                    "20,000,000",
                    "19,300,000,000",
                    "960.00",
                    "980.00",
                    "955.00",
                    "970.00",
                    "+10.00",
                    "40,000",
                ]
            ],
        }
        frame, audit = twse.parse_month(
            "2330",
            json.dumps(payload).encode(),
        )
        self.assertEqual(str(frame.loc[0, "date"]), "2024-07-01")
        self.assertEqual(frame.loc[0, "volume"], 20_000_000.0)
        self.assertEqual(audit["rows"], 1)
        self.assertEqual(
            list(
                twse.months(
                    twse.date(2024, 7, 15),
                    twse.date(2024, 9, 1),
                )
            ),
            [twse.date(2024, 7, 1), twse.date(2024, 8, 1)],
        )
        self.assertEqual(
            list(
                twse.months(
                    twse.date(2024, 7, 15),
                    twse.date(2024, 9, 2),
                )
            ),
            [
                twse.date(2024, 7, 1),
                twse.date(2024, 8, 1),
                twse.date(2024, 9, 1),
            ],
        )

    def test_nasdaq_display_history_parses_raw_prices_and_shares(self) -> None:
        nasdaq = load_script(
            "autoquant_skill_nasdaq",
            SKILLS
            / "fetch-nasdaq-ohlcv"
            / "scripts"
            / "fetch_nasdaq_daily.py",
        )
        payload = {
            "data": {
                "symbol": "AAPL",
                "totalRecords": 3,
                "tradesTable": {
                    "rows": [
                        {
                            "date": "07/29/2026",
                            "close": "$338.19",
                            "volume": "56,090,840",
                            "open": "$339.73",
                            "high": "$344.5699",
                            "low": "$337.3501",
                        },
                        {
                            "date": "07/28/2026",
                            "close": "$340.08",
                            "volume": "51,859,040",
                            "open": "$340.03",
                            "high": "$342.89",
                            "low": "$335.60",
                        },
                        {
                            "date": "07/27/2026",
                            "close": "$340.00",
                            "volume": "N/A",
                            "open": "$339.00",
                            "high": "$341.00",
                            "low": "$338.00",
                        },
                    ]
                },
            },
            "status": {
                "rCode": 200,
                "bCodeMessage": None,
                "developerMessage": None,
            },
        }
        frame, audit = nasdaq.parse_payload(
            "AAPL",
            json.dumps(payload).encode(),
            nasdaq.date(2026, 7, 28),
            nasdaq.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 338.19)
        self.assertEqual(frame.loc[1, "volume"], 56_090_840.0)
        self.assertEqual(audit["declaredTotalRecords"], 3)
        self.assertEqual(audit["unusableRowsDropped"], 1)

    def test_naver_literal_table_preserves_raw_krw_and_share_volume(self) -> None:
        naver = load_script(
            "autoquant_skill_naver",
            SKILLS
            / "fetch-naver-ohlcv"
            / "scripts"
            / "fetch_naver_daily.py",
        )
        raw = (
            "[['날짜','시가','고가','저가','종가','거래량','외국인소진율'],"
            "['20260728',200000,205000,198000,203000,12000000,54.0],"
            "['20260729',203000,208000,201000,207000,13000000,54.1]]"
        ).encode()
        frame, audit = naver.parse_payload(
            "005930",
            raw,
            naver.date(2026, 7, 28),
            naver.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 207_000)
        self.assertEqual(frame.loc[1, "volume"], 13_000_000)
        self.assertEqual(audit["providerVolumeUnit"], "share")

    def test_package_audit_reconciles_a_confined_daily_panel(self) -> None:
        package_audit = load_script(
            "autoquant_skill_package",
            SKILLS
            / "package-autoquant-ohlcv"
            / "scripts"
            / "audit_ohlcv_package.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frame = pd.DataFrame(
                {
                    "date": ["2026-07-28", "2026-07-29"],
                    "open": [100.0, 101.0],
                    "high": [102.0, 103.0],
                    "low": [99.0, 100.0],
                    "close": [101.0, 102.0],
                    "volume": [1_000.0, 1_100.0],
                }
            )
            frame.to_csv(root / "AAPL.csv", index=False)
            package = {
                "schemaVersion": 1,
                "kind": "autoquant-ohlcv-dataset-package",
                "id": "skill-audit",
                "version": "2026-07-29",
                "assetClass": "equity",
                "frequency": "1d",
                "market": {
                    "clock": "session",
                    "calendar": "XNYS",
                    "timezone": "America/New_York",
                },
                "priceAdjustment": "raw",
                "provider": {
                    "name": "fixture",
                    "retrievedAt": None,
                    "sourceUri": None,
                    "terms": "deterministic fixture",
                },
                "assets": [
                    {
                        "symbol": "AAPL",
                        "venue": "XNAS",
                        "currency": "USD",
                        "path": "AAPL.csv",
                    }
                ],
            }
            package_path = root / "dataset-package.json"
            package_path.write_text(
                json.dumps(package),
                encoding="utf-8",
            )
            audit = package_audit.audit(package_path)
            self.assertEqual(audit["assets"]["AAPL"]["rows"], 2)
            self.assertTrue(audit["panel"]["fullyAligned"])
            self.assertEqual(audit["panel"]["unionTimestamps"], 2)

    def test_package_comparison_preserves_quantization_and_adjustment(self) -> None:
        comparison = load_script(
            "autoquant_skill_compare",
            SKILLS
            / "package-autoquant-ohlcv"
            / "scripts"
            / "compare_ohlcv_packages.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for side, close, volume in (
                ("left", 101.00, 1_000.0),
                ("right", 101.01, 1_050.0),
            ):
                side_root = root / side
                side_root.mkdir()
                pd.DataFrame(
                    {
                        "date": ["2026-07-29"],
                        "open": [100.0],
                        "high": [102.0],
                        "low": [99.0],
                        "close": [close],
                        "volume": [volume],
                    }
                ).to_csv(side_root / "AAPL.csv", index=False)
                package = {
                    "kind": "autoquant-ohlcv-dataset-package",
                    "id": side,
                    "priceAdjustment": "raw",
                    "provider": {"name": side},
                    "assets": [{"symbol": "AAPL", "path": "AAPL.csv"}],
                }
                path = side_root / "dataset-package.json"
                path.write_text(json.dumps(package), encoding="utf-8")
                paths.append(path)
            audit = comparison.compare(
                paths[0],
                paths[1],
                price_atol=0.011,
                price_rtol=0.0,
                volume_atol=100.0,
                volume_rtol=0.0,
            )
            self.assertEqual(audit["commonPanelDates"], 1)
            self.assertEqual(
                audit["assets"]["AAPL"]["prices"]["close"]["mismatchRows"],
                0,
            )
            self.assertEqual(
                audit["assets"]["AAPL"]["volume"]["mismatchRows"],
                0,
            )
            right = json.loads(paths[1].read_text(encoding="utf-8"))
            right["priceAdjustment"] = "provider-adjusted"
            paths[1].write_text(json.dumps(right), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different priceAdjustment"):
                comparison.compare(
                    paths[0],
                    paths[1],
                    price_atol=0.011,
                    price_rtol=0.0,
                    volume_atol=100.0,
                    volume_rtol=0.0,
                )
