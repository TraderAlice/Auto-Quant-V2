"""Narrow Freqtrade adaptations for offline and session-based research."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import math
from threading import RLock
from unittest.mock import patch

import pandas as pd
from ccxt.base.decimal_to_precision import TICK_SIZE

import freqtrade.data.dataprovider as dataprovider_module
from freqtrade.data import history
from freqtrade.enums import ExitType
from freqtrade.exchange import Exchange
from freqtrade.optimize import backtesting as backtesting_module
from freqtrade.optimize.backtesting import Backtesting

from .profiles import AssetProfile


_DATA_POLICY_LOCK = RLock()


def session_startup_candles(timeframe: str, requested: int) -> int:
    """Expand wall-clock warmup so row-based indicators see enough session bars.

    Freqtrade normally turns ``startup_candles`` into a wall-clock offset.  That
    is exact for 24/7 data, but 250 hourly candles only reaches about 48 regular
    US trading sessions after nights and weekends are removed.  The final
    indicator trim remains the original row count; this expansion only controls
    how much source history is loaded.
    """

    if requested <= 0:
        return requested
    normalized = timeframe.strip().lower()
    daily_or_slower = normalized.endswith(("d", "w", "mo"))
    factor = 2 if daily_or_slower else 6
    return math.ceil(requested * factor)


def retain_session_warmup(
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp,
    requested: int,
) -> pd.DataFrame:
    """Keep exactly ``requested`` real bars before a session backtest start."""

    if requested <= 0 or frame.empty:
        return frame
    before = frame.loc[frame["date"] < start].tail(requested)
    after = frame.loc[frame["date"] >= start]
    return pd.concat([before, after], ignore_index=True)


def _market_from_pair(pair: str, profile: AssetProfile) -> dict:
    base, quote = pair.split("/", 1)
    amount_step = profile.amount_step or 1.0
    price_tick = profile.price_tick or 0.01
    return {
        "id": base,
        "symbol": pair,
        "base": base,
        "quote": quote,
        "settle": None,
        "baseId": base,
        "quoteId": quote,
        "settleId": None,
        "type": "spot",
        "spot": True,
        "margin": False,
        "swap": False,
        "future": False,
        "option": False,
        "active": True,
        "contract": False,
        "contractSize": None,
        "linear": None,
        "inverse": None,
        "precision": {
            "amount": amount_step,
            "price": price_tick,
        },
        "limits": {
            "leverage": {"min": 1.0, "max": 1.0},
            "amount": {"min": amount_step, "max": None},
            "price": {"min": price_tick, "max": None},
            "cost": {"min": None, "max": None},
        },
        "maker": profile.fee,
        "taker": profile.fee,
        "percentage": True,
        "tierBased": False,
        "info": {
            "asset_class": profile.asset_class,
            "venue": profile.venue,
            "offline": True,
        },
    }


class OfflineMarketExchange(Exchange):
    """Freqtrade Exchange facade backed only by manifest market metadata.

    It intentionally implements no data download or live execution path.  The
    regular Freqtrade class still provides precision, stake-limit and pair
    helpers required by Backtesting.
    """

    def __init__(self, config: dict, profile: AssetProfile) -> None:
        # The base Exchange class wants a CCXT object for generic precision
        # helpers. Use a known local CCXT implementation as an internal detail;
        # the research profile is deliberately not a Broker/exchange adapter.
        runtime_config = deepcopy(config)
        runtime_config["exchange"]["name"] = "binance"
        super().__init__(runtime_config, validate=False)
        self._api.name = f"Offline {profile.venue}"
        self._api_async.name = f"Offline {profile.venue}"
        self._api.precisionMode = TICK_SIZE
        self._api_async.precisionMode = TICK_SIZE
        self._markets = {
            pair: _market_from_pair(pair, profile)
            for pair in profile.pairs
        }

    def reload_markets(self, force: bool = False, *, load_leverage_tiers: bool = True) -> None:
        """Keep the static manifest markets; never contact a remote venue."""

        return None


@contextmanager
def preserve_session_gaps():
    """Disable Freqtrade's crypto-oriented missing-candle forward fill.

    Freqtrade imports the two history helpers through different modules, so
    both symbols are patched for the duration of one serial backtest.  The
    Harness runs strategies serially; the lock makes the global patch explicit
    and prevents accidental overlap in future threaded callers.
    """

    with _DATA_POLICY_LOCK:
        original_load_data = history.load_data
        original_load_pair_history = dataprovider_module.load_pair_history

        def load_data_without_fill(*args, **kwargs):
            kwargs["fill_up_missing"] = False
            if "startup_candles" in kwargs:
                kwargs["startup_candles"] = session_startup_candles(
                    str(kwargs.get("timeframe", "")),
                    int(kwargs["startup_candles"]),
                )
            return original_load_data(*args, **kwargs)

        def load_pair_without_fill(*args, **kwargs):
            kwargs["fill_up_missing"] = False
            if "startup_candles" in kwargs:
                kwargs["startup_candles"] = session_startup_candles(
                    str(kwargs.get("timeframe", "")),
                    int(kwargs["startup_candles"]),
                )
            return original_load_pair_history(*args, **kwargs)

        with (
            patch.object(history, "load_data", load_data_without_fill),
            patch.object(
                dataprovider_module,
                "load_pair_history",
                load_pair_without_fill,
            ),
        ):
            yield


def gap_aware_stop_price(
    *,
    open_price: float,
    stop_price: float,
    is_short: bool,
) -> float | None:
    """Return the opening fill when a stop is already crossed at session open."""

    if is_short and open_price >= stop_price:
        return open_price
    if not is_short and open_price <= stop_price:
        return open_price
    return None


class SessionAwareBacktesting(Backtesting):
    """Freqtrade backtesting with session gaps preserved and gap-aware stops."""

    def start(self) -> None:
        with preserve_session_gaps():
            super().start()

    def load_bt_data(self):
        data, timerange = super().load_bt_data()
        if timerange.starttype == "date" and self.required_startup > 0:
            start = pd.Timestamp(timerange.startdt)
            data = {
                pair: retain_session_warmup(
                    frame,
                    start=start,
                    requested=self.required_startup,
                )
                for pair, frame in data.items()
            }
        return data, timerange

    def _get_close_rate_for_stoploss(self, row, trade, exit_, trade_dur):
        if exit_.exit_type in (
            ExitType.STOP_LOSS,
            ExitType.TRAILING_STOP_LOSS,
            ExitType.LIQUIDATION,
        ):
            stop_price = (
                trade.liquidation_price
                if exit_.exit_type == ExitType.LIQUIDATION and trade.liquidation_price
                else trade.stop_loss
            )
            gap_fill = gap_aware_stop_price(
                open_price=float(row[backtesting_module.OPEN_IDX]),
                stop_price=float(stop_price),
                is_short=bool(trade.is_short),
            )
            if gap_fill is not None:
                return gap_fill
        return super()._get_close_rate_for_stoploss(row, trade, exit_, trade_dur)


def build_backtester(config: dict, profile: AssetProfile) -> Backtesting:
    """Create the engine instance selected by one asset profile."""

    if not profile.offline_exchange and not profile.is_session_based:
        return Backtesting(config)

    exchange = OfflineMarketExchange(config, profile)
    if profile.is_session_based:
        return SessionAwareBacktesting(config, exchange=exchange)
    return Backtesting(config, exchange=exchange)
