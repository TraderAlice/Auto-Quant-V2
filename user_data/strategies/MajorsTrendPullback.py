"""
MajorsTrendPullback — pullback-to-EMA21 in 4h-confirmed 1d-bull trends, full 5-pair

Paradigm: trend-following
Hypothesis: in established uptrends (1d close > SMA200 AND 4h ema50 > ema200), short pullbacks to the 1h EMA21 are entry points; the trend continuation has positive expectancy across regimes if we silence trades when the higher-TF stack is broken. v0.4.1 found 4h trend gate is a paradigm-agnostic gold filter — bake it in from r0.
Parent: root
Created: TBD
Status: active
Uses MTF: yes
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class MajorsTrendPullback(IStrategy):
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

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] > dataframe["sma200_1d"])
            & (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["ema21"] > dataframe["ema50"])
            & (dataframe["close"] <= dataframe["ema21"] * 1.005)
            & (dataframe["close"] >= dataframe["ema21"] * 0.99)
            & (dataframe["rsi"] < 55)
            & (dataframe["rsi"] > 35),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rsi"] > 72)
            | (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            | (dataframe["close"] < dataframe["sma200_1d"]),
            "exit_long",
        ] = 1
        return dataframe
