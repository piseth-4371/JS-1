"""Shared pieces for all strategies (Agent 2 — Strategy Analyst).

A strategy sees row i of the 5-minute table AFTER that bar closed and either
returns an Order or None (= WAIT). It never sees the account or other orders.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

BAR = 300  # seconds in a 5-minute bar


@dataclass
class Order:
    strategy: str
    side: int                 # +1 long, -1 short
    kind: str                 # "limit" | "stop" | "market"
    entry: float              # planned entry (market: last close, the real fill comes later)
    stop: float
    target: float | None      # None for market orders: set to rr_target * risk at the fill
    rr_target: float
    placed_ts: int            # when the order becomes active (bar close)
    expiry_ts: int
    cancel_level: float | None = None   # cancel if a 5m bar CLOSES beyond this (side-aware)
    reason: str = ""
    conditions: dict = field(default_factory=dict)

    def __post_init__(self):
        # Strategies read NumPy arrays. NumPy numbers must become plain Python numbers,
        # otherwise SQLite stores them as raw bytes (bug found by the Day 7 replay).
        self.side = int(self.side)
        self.placed_ts, self.expiry_ts = int(self.placed_ts), int(self.expiry_ts)
        self.entry, self.stop, self.rr_target = float(self.entry), float(self.stop), float(self.rr_target)
        if self.target is not None:
            self.target = float(self.target)
        if self.cancel_level is not None:
            self.cancel_level = float(self.cancel_level)


class Strategy:
    name = "base"
    rr = 2.0

    def new_day(self, day) -> None:
        """Called once at the first bar of each New York date."""

    def on_bar(self, i: int, a: dict) -> Order | None:
        raise NotImplementedError


def window(a: dict, i: int, start_min: int, end_min: int, clock: str = "mod") -> bool:
    """True if bar i CLOSES inside [start_min, end_min] (minutes of day; clock "mod" = NY, "lmod" = London)."""
    close_min = a[clock][i] + 5
    return start_min <= close_min <= end_min


def valid(*xs) -> bool:
    return all(x is not None and np.isfinite(x) for x in xs)


def fvg(a: dict, i: int, side: int, disp_atr: float = 1.0, min_gap_atr: float = 0.15):
    """Fair Value Gap that completed at bar i (c1=i-2, c2=i-1, c3=i).

    Returns (zone_low, zone_high, c1_extreme) or None.
    Bullish: c3.low > c1.high, c2 is a strong bullish candle (displacement).
    """
    if i < 2 or not (a["consec"][i] and a["consec"][i - 1]):
        return None
    h, l, o, c, atr = a["h"], a["l"], a["o"], a["c"], a["atr"][i]
    if not valid(atr) or atr <= 0:
        return None
    body = (c[i - 1] - o[i - 1]) * side
    if body < disp_atr * a["atr"][i - 1]:
        return None
    if side == 1:
        lo, hi = h[i - 2], l[i]
        extreme = l[i - 2]
    else:
        lo, hi = h[i], l[i - 2]
        extreme = h[i - 2]
    if hi - lo < min_gap_atr * atr:
        return None
    return lo, hi, extreme
