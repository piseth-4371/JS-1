"""The two "books" that share ONE paper account, ONE kill switch and ONE risk budget.

    NAS100  weekdays: positions may be open 03:00-15:55 New York (London open .. US close)
    BTC     weekends: Friday 17:00 .. Sunday 17:00 New York (while NAS100 CFDs are closed)

Each book has its own price feed, cost model, strategies (BTC strategies start
with "btc_"), broker cursor and active-strategy setting. Their holding windows
never overlap, and the Risk Manager still allows only 1 open position in total.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

import numpy as np

from app.core.fills import Costs
from app.core.risk import USTEC, Instrument

NY = ZoneInfo("America/New_York")

# Binance BTCUSDT: quantity in BTC, $1 per $1 move per 1 BTC; Binance minimum step 0.00001 BTC.
BTC = Instrument("BTCUSDT", value_per_point_per_lot=1.0, min_lot=0.00001, lot_step=0.00001, max_lot=1000)

# [ASSUMPTION] Crypto costs are a % of price, not fixed points: 0.10% round-trip fee
# (between Binance futures ~0.04-0.10% and spot ~0.2%) + 0.02% slippage on market/stop legs.
BTC_COSTS = Costs(spread=0.0, slippage=0.0, fee_pct=0.10, slip_pct=0.02)


def nas_hold_mask(mod: np.ndarray, weekday: np.ndarray) -> np.ndarray:
    return (weekday < 5) & (mod >= 180) & (mod < 955)


def btc_weekend_mask(mod: np.ndarray, weekday: np.ndarray) -> np.ndarray:
    return ((weekday == 4) & (mod >= 17 * 60)) | (weekday == 5) | ((weekday == 6) & (mod < 17 * 60))


@dataclass(frozen=True)
class Market:
    key: str
    label: str
    instrument: Instrument
    costs: Costs
    hold_mask: Callable[[np.ndarray, np.ndarray], np.ndarray]
    strategy_key: str            # control row holding the active strategy
    default_strategy: str
    cursor_key: str              # control row: last 1-minute bar processed by this book's broker

    def can_hold(self, ts: int) -> bool:
        d = datetime.fromtimestamp(ts, NY)
        return bool(self.hold_mask(np.array([d.hour * 60 + d.minute]), np.array([d.weekday()]))[0])

    def owns(self, strategy_name: str) -> bool:
        return strategy_name.startswith("btc_") == (self.key == "btc")


NAS100 = Market("nas100", "NAS100 (weekdays)", USTEC, Costs(), nas_hold_mask,
                "active_strategy", "trend_fvg", "broker_cursor_ts")
BTCUSD = Market("btc", "BTC (weekends)", BTC, BTC_COSTS, btc_weekend_mask,
                "active_strategy_btc", "btc_weekend_trend_fvg", "broker_cursor_ts_btc")
MARKETS = {m.key: m for m in (NAS100, BTCUSD)}


def market_for_strategy(name: str) -> Market:
    return BTCUSD if BTCUSD.owns(name) else NAS100
