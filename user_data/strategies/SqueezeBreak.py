"""
SqueezeBreak — Bollinger-band squeeze followed by upper-band breakout with volume confirm

Paradigm: volatility
Hypothesis: periods of low volatility (BB width compressed below its 50-bar median) precede directional expansions; entering on the first close above the upper band with volume > 1.3× 20-bar mean catches the expansion phase. Pure volatility paradigm — distinct from MR (mean) and trend (drift). Volatility paradigm has been under-explored across versions; testing cleanly here without confounders.
Parent: root
Created: TBD
Status: active
Uses MTF: no
"""

from pandas import DataFrame
import numpy as np
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class SqueezeBreak(IStrategy):
    # This research snapshot was designed for the crypto-majors arena.
    asset_classes = ["crypto"]

    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.99

    trailing_stop = False
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 250

    test_timeranges = [
        ("bull_2021",      "20210101-20211231"),
        ("winter_2022",    "20220101-20221231"),
        ("recovery_23_25", "20230101-20251231"),
        ("full_5y",        "20210101-20251231"),
    ]

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["bb_middle"] = bb["middleband"]
        dataframe["bb_lower"] = bb["lowerband"]
        dataframe["bb_width"] = (
            (dataframe["bb_upper"] - dataframe["bb_lower"])
            / dataframe["bb_middle"].replace(0, np.nan)
        )
        dataframe["bb_width_med50"] = dataframe["bb_width"].rolling(50).median()
        dataframe["vol_ma20"] = dataframe["volume"].rolling(20).mean()
        dataframe["squeeze"] = (
            dataframe["bb_width"].shift(1) < dataframe["bb_width_med50"].shift(1) * 0.85
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["squeeze"]
            & (dataframe["close"] > dataframe["bb_upper"])
            & (dataframe["close"].shift(1) <= dataframe["bb_upper"].shift(1))
            & (dataframe["volume"] > dataframe["vol_ma20"] * 1.3)
            & (dataframe["close"] > dataframe["sma200_1d"]),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["close"] < dataframe["bb_middle"],
            "exit_long",
        ] = 1
        return dataframe
