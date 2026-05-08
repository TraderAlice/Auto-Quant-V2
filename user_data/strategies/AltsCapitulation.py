"""
AltsCapitulation — deep RSI capitulation MR on alts with 4h trend gate + DD-conviction sizing

Paradigm: mean-reversion (counter-trend)
Hypothesis: alts (SOL/BNB/AVAX) sell off harder than majors, producing deeper RSI extremes that mean-revert. Bake in v0.4.1's two confirmed wins from r0: (a) 4h trend gate as gold filter, (b) DD-conviction sizing where deeper RSI commands larger stake. v0.4.1 found RSI<25 MR is BNB-specific on full 5-pair basket; testing whether deeper threshold (RSI<22) on alts-only basket extracts the alpha at all three alt pairs simultaneously.
Parent: root
Created: TBD
Status: active
Uses MTF: yes
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class AltsCapitulation(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    pair_basket = ["SOL/USDT", "BNB/USDT", "AVAX/USDT"]

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

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rsi"] < 25)
            & (dataframe["ema50_4h"] > dataframe["ema200_4h"]),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["rsi"] > 60,
            "exit_long",
        ] = 1
        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_stake: float,
        min_stake,
        max_stake: float,
        leverage: float,
        entry_tag: str,
        side: str,
        **kwargs,
    ) -> float:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or len(df) == 0:
            return proposed_stake
        rsi = df["rsi"].iloc[-1]
        if rsi != rsi:
            return proposed_stake
        scale = min(2.0, max(0.5, 25.0 / max(rsi, 1.0)))
        scaled = proposed_stake * scale
        if min_stake is not None:
            scaled = max(min_stake, scaled)
        scaled = min(max_stake, scaled)
        return scaled
