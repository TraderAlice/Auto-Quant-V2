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
            "fetch-daum-ohlcv",
            "fetch-eastmoney-ohlcv",
            "fetch-euronext-ohlcv",
            "fetch-finmind-ohlcv",
            "fetch-nasdaq-ohlcv",
            "fetch-naver-ohlcv",
            "fetch-nikkei-ohlcv",
            "fetch-sina-ohlcv",
            "fetch-sohu-ohlcv",
            "fetch-tencent-ohlcv",
            "fetch-twse-ohlcv",
            "fetch-vndirect-ohlcv",
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
            self.assertEqual(len(verified["skills"]), 16)

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
            "split-and-dividend-adjusted",
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

    def test_yahoo_uses_exchange_timezone_for_session_date(self) -> None:
        yahoo = load_script(
            "autoquant_skill_yahoo_timezone",
            SKILLS
            / "fetch-yahoo-ohlcv"
            / "scripts"
            / "fetch_yahoo_daily.py",
        )
        timestamp = int(
            pd.Timestamp("2025-01-01T17:00:00Z").timestamp()
        )
        result = {
            "meta": {"exchangeTimezoneName": "Asia/Ho_Chi_Minh"},
            "timestamp": [timestamp],
            "indicators": {
                "quote": [
                    {
                        "open": [100.0],
                        "high": [101.0],
                        "low": [99.0],
                        "close": [100.0],
                        "volume": [1_000.0],
                    }
                ]
            },
        }
        frame, audit = yahoo.frame_for(
            "VNM.VN",
            result,
            "split-adjusted",
        )
        self.assertEqual(frame.loc[0, "date"], "2025-01-02")
        self.assertEqual(
            audit["sessionDateTimezone"],
            "Asia/Ho_Chi_Minh",
        )

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
                "日期",
                "成交股數",
                "成交金額",
                "開盤價",
                "最高價",
                "最低價",
                "收盤價",
                "漲跌價差",
                "成交筆數",
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
                ],
                [
                    "113/07/02",
                    "0",
                    "0",
                    "--",
                    "--",
                    "--",
                    "--",
                    "--",
                    "0",
                ],
            ],
        }
        frame, audit = twse.parse_month(
            "2330",
            json.dumps(payload).encode(),
        )
        self.assertEqual(str(frame.loc[0, "date"]), "2024-07-01")
        self.assertEqual(frame.loc[0, "volume"], 20_000_000.0)
        self.assertEqual(audit["rows"], 1)
        self.assertEqual(audit["providerRows"], 2)
        self.assertEqual(audit["unusableRowsDropped"], 1)
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

    def test_finmind_preserves_raw_twd_and_checks_traded_money(self) -> None:
        finmind = load_script(
            "autoquant_skill_finmind",
            SKILLS
            / "fetch-finmind-ohlcv"
            / "scripts"
            / "fetch_finmind_daily.py",
        )
        payload = {
            "msg": "success",
            "status": 200,
            "data": [
                {
                    "date": "2026-07-28",
                    "stock_id": "2330",
                    "Trading_Volume": 20_000_000,
                    "Trading_money": 19_300_000_000,
                    "open": 960.0,
                    "max": 980.0,
                    "min": 955.0,
                    "close": 970.0,
                    "spread": 10.0,
                    "Trading_turnover": 40_000,
                },
                {
                    "date": "2026-07-29",
                    "stock_id": "2330",
                    "Trading_Volume": 10_000_000,
                    "Trading_money": 9_850_000_000,
                    "open": 975.0,
                    "max": 995.0,
                    "min": 970.0,
                    "close": 990.0,
                    "spread": 20.0,
                    "Trading_turnover": 25_000,
                },
            ],
        }
        frame, audit = finmind.parse_payload(
            "2330",
            json.dumps(payload).encode(),
            finmind.date(2026, 7, 28),
            finmind.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 990.0)
        self.assertEqual(frame.loc[1, "volume"], 10_000_000)
        self.assertEqual(audit["valueVolumeRowsChecked"], 2)
        self.assertEqual(audit["valueVolumeAnomalyRows"], 0)

    def test_nasdaq_display_history_parses_prices_and_shares(self) -> None:
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

    def test_daum_page_preserves_raw_krw_and_checks_traded_value(self) -> None:
        daum = load_script(
            "autoquant_skill_daum",
            SKILLS
            / "fetch-daum-ohlcv"
            / "scripts"
            / "fetch_daum_daily.py",
        )
        payload = {
            "code": 200,
            "message": None,
            "currentPage": 1,
            "pageSize": 1000,
            "totalCount": 2,
            "totalPages": 1,
            "data": [
                {
                    "symbolCode": "A005930",
                    "date": "2026-07-29 00:00:00",
                    "openingPrice": 203000,
                    "highPrice": 208000,
                    "lowPrice": 201000,
                    "tradePrice": 207000,
                    "accTradeVolume": 13000000,
                    "accTradePrice": 2665000000000,
                },
                {
                    "symbolCode": "A005930",
                    "date": "2026-07-28 00:00:00",
                    "openingPrice": 200000,
                    "highPrice": 205000,
                    "lowPrice": 198000,
                    "tradePrice": 203000,
                    "accTradeVolume": 12000000,
                    "accTradePrice": 2418000000000,
                },
            ],
        }
        records, page_audit = daum.parse_page(
            "A005930", json.dumps(payload).encode(), 1
        )
        frame, audit = daum.frame_for(
            "A005930",
            records,
            daum.date(2026, 7, 28),
            daum.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 207_000)
        self.assertEqual(frame.loc[1, "volume"], 13_000_000)
        self.assertEqual(audit["valueVolumeRowsChecked"], 2)
        self.assertEqual(page_audit["totalCount"], 2)

    def test_vndirect_price_scale_and_invalid_bounds_are_audited(self) -> None:
        vndirect = load_script(
            "autoquant_skill_vndirect",
            SKILLS
            / "fetch-vndirect-ohlcv"
            / "scripts"
            / "fetch_vndirect_daily.py",
        )
        asset = {
            "symbol": "VCB",
            "providerSymbol": "VCB",
            "providerFloor": "HOSE",
            "venue": "HOSE",
            "currency": "VND",
            "assetClass": "equity",
        }
        records = [
            {
                "code": "VCB",
                "floor": "HOSE",
                "date": "2026-07-28",
                "open": 60.0,
                "high": 62.0,
                "low": 59.0,
                "close": 61.0,
                "adOpen": 30.0,
                "adHigh": 31.0,
                "adLow": 29.5,
                "adClose": 30.5,
                "nmVolume": 1_000,
                "nmValue": 60_500_000,
                "average": 60.5,
            },
            {
                "code": "VCB",
                "floor": "HOSE",
                "date": "2026-07-29",
                "open": 61.0,
                "high": 62.0,
                "low": 61.5,
                "close": 61.2,
                "adOpen": 30.5,
                "adHigh": 31.0,
                "adLow": 30.75,
                "adClose": 30.6,
                "nmVolume": 2_000,
                "nmValue": 122_400_000,
                "average": 61.2,
            },
        ]
        frame, audit = vndirect.frame_for(
            asset,
            records,
            "raw",
            vndirect.date(2026, 7, 28),
            vndirect.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28"])
        self.assertEqual(frame.loc[0, "close"], 61_000.0)
        self.assertEqual(frame.loc[0, "volume"], 1_000.0)
        self.assertEqual(audit["priceMultiplier"], 1_000)
        self.assertEqual(audit["normalValueChecks"], 2)
        self.assertEqual(audit["invalidBoundsRowsDropped"], 1)

    def test_euronext_official_csv_preserves_share_volume(self) -> None:
        euronext = load_script(
            "autoquant_skill_euronext",
            SKILLS
            / "fetch-euronext-ohlcv"
            / "scripts"
            / "fetch_euronext_daily.py",
        )
        raw = (
            "\ufeff\"Historical Data\"\n"
            "\"From 2026-07-28 to 2026-07-29\"\n"
            "FR0000121014\n"
            "Date;Open;High;Low;Last;Close;Number of Shares;"
            "Number of Trades;Turnover;vwap\n"
            "29/07/2026;477.00;486.40;465.25;467.95;467.95;"
            "684597;36414;322427655;470.9744\n"
            "28/07/2026;469.40;481.15;451.80;470.30;470.30;"
            "876705;44524;408412667;465.8496\n"
        ).encode()
        frame, audit = euronext.parse_payload(
            "FR0000121014-XPAR",
            raw,
            euronext.date(2026, 7, 28),
            euronext.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 467.95)
        self.assertEqual(frame.loc[1, "volume"], 684_597.0)
        self.assertEqual(audit["declaredIsin"], "FR0000121014")
        self.assertEqual(audit["lastCloseMismatchRows"], 0)

    def test_nikkei_recent_table_resolves_year_and_preserves_volume(self) -> None:
        nikkei = load_script(
            "autoquant_skill_nikkei",
            SKILLS
            / "fetch-nikkei-ohlcv"
            / "scripts"
            / "fetch_nikkei_daily.py",
        )
        raw = """
        <html><div class="l-miH02_date">2026年1月5日（月）</div>
        <table><thead><tr>
        <th>日付</th><th>始値</th><th>高値</th><th>安値</th>
        <th>終値</th><th>売買高</th><th>修正後終値</th>
        </tr></thead><tbody>
        <tr><th>1/5（月）</th><td>3,100</td><td>3,200</td>
        <td>3,050</td><td>3,180</td><td>12,345,600</td>
        <td>3,180.0</td></tr>
        <tr><th>12/30（火）</th><td>3,000</td><td>3,100</td>
        <td>2,980</td><td>3,050</td><td>10,000,000</td>
        <td>3,050.0</td></tr>
        </tbody></table></html>
        """.encode()
        frame, audit = nikkei.parse_payload(
            "7203",
            raw,
            nikkei.date(2025, 12, 30),
            nikkei.date(2026, 1, 6),
        )
        self.assertEqual(frame["date"].tolist(), ["2025-12-30", "2026-01-05"])
        self.assertEqual(frame.loc[1, "volume"], 12_345_600.0)
        self.assertEqual(audit["pageAsOf"], "2026-01-05")
        self.assertEqual(audit["adjustedCloseDifferenceRows"], 0)

    def test_sina_recent_kline_preserves_raw_prices_and_shares(self) -> None:
        sina = load_script(
            "autoquant_skill_sina",
            SKILLS
            / "fetch-sina-ohlcv"
            / "scripts"
            / "fetch_sina_daily.py",
        )
        payload = {
            "result": {
                "status": {"code": 0},
                "data": [
                    {
                        "day": "2026-07-28",
                        "open": "1300.000",
                        "high": "1320.000",
                        "low": "1290.000",
                        "close": "1310.000",
                        "volume": "3569892",
                    },
                    {
                        "day": "2026-07-29",
                        "open": "1310.000",
                        "high": "1330.000",
                        "low": "1300.000",
                        "close": "1325.000",
                        "volume": "7187261",
                    },
                ],
            }
        }
        frame, audit = sina.parse_payload(
            "sh600519",
            json.dumps(payload).encode(),
            sina.date(2026, 7, 28),
            sina.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 1325.0)
        self.assertEqual(frame.loc[1, "volume"], 7_187_261.0)
        self.assertEqual(audit["providerVolumeUnit"], "share")

    def test_sohu_jsonp_converts_lots_and_checks_traded_value(self) -> None:
        sohu = load_script(
            "autoquant_skill_sohu",
            SKILLS
            / "fetch-sohu-ohlcv"
            / "scripts"
            / "fetch_sohu_daily.py",
        )
        payload = [
            {
                "status": 0,
                "code": "cn_920019",
                "hq": [
                    [
                        "2026-07-29",
                        "13.690",
                        "14.030",
                        "0.300",
                        "2.18%",
                        "13.520",
                        "14.060",
                        "16975",
                        "2352.156",
                        "1.01%",
                    ],
                    [
                        "2026-07-28",
                        "13.450",
                        "13.730",
                        "0.130",
                        "0.96%",
                        "13.400",
                        "13.940",
                        "16448",
                        "2250.000",
                        "0.98%",
                    ],
                ],
                "stat": ["累计:", "2026-07-28至2026-07-29"],
            }
        ]
        raw = (
            "historySearchHandler("
            + json.dumps(payload, ensure_ascii=False)
            + ")\n"
        ).encode("gb18030")
        frame, audit = sohu.parse_payload(
            "cn_920019",
            raw,
            sohu.date(2026, 7, 28),
            sohu.date(2026, 7, 30),
        )
        self.assertEqual(frame["date"].tolist(), ["2026-07-28", "2026-07-29"])
        self.assertEqual(frame.loc[1, "close"], 14.03)
        self.assertEqual(frame.loc[1, "volume"], 1_697_500)
        self.assertEqual(audit["volumeMultiplier"], 100)
        self.assertEqual(audit["valueVolumeRowsChecked"], 2)

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
