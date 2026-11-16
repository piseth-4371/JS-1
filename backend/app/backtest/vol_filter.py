"""Research only: volatility regime filter (rules: docs/volatility_filter_preregistration.md, fixed 2026-11-16).

For each trade date D:
  daily close  = close of the last 1-minute bar before 16:00 New York (weekdays)
  volatility   = std of the last 20 daily log returns BEFORE D (needs >= 15)
  percentile   = rank of that volatility among the previous 250 readings (needs >= 120)
Keep an order only if 20 <= percentile <= 80. Not connected to the live engine or the scanner.
"""
from __future__ import annotations

import bisect
import math
from datetime import date

import numpy as np
import pandas as pd

from app.core.strategies.base import Order, Strategy

NY = "America/New_York"
VOL_DAYS, VOL_MIN = 20, 15
RANK_DAYS, RANK_MIN = 250, 120
LOW, HIGH = 20.0, 80.0


def daily_closes(m1: pd.DataFrame) -> pd.Series:
    """m1 with columns ts (UTC seconds) and c -> Series {New York date: close of the last bar before 16:00}."""
    ny = pd.to_datetime(m1["ts"], unit="s", utc=True).dt.tz_convert(NY)
    keep = (ny.dt.day_of_week < 5) & (ny.dt.hour < 16)
    d = pd.DataFrame({"day": ny[keep].dt.date, "ts": m1["ts"][keep], "c": m1["c"][keep]}).sort_values("ts")
    return d.groupby("day")["c"].last().sort_index()


def _reading(rets: np.ndarray, k: int) -> float | None:
    """Volatility known before close number k: returns rets[1..k-1] (rets[j] = ln c[j]/c[j-1])."""
    window = rets[max(1, k - VOL_DAYS):k]
    return float(np.std(window, ddof=1)) if window.size >= VOL_MIN else None


def percentiles(closes: pd.Series, dates) -> dict[date, float | None]:
    """{date: volatility percentile 0-100, or None if not enough history}. Uses only closes BEFORE each date."""
    days = list(closes.index)
    c = closes.to_numpy(dtype=float)
    rets = np.concatenate([[np.nan], np.log(c[1:] / c[:-1])]) if c.size else np.array([])
    readings = [_reading(rets, k) for k in range(len(c) + 1)]   # readings[k]: known before close k
    out: dict[date, float | None] = {}
    for d in dates:
        k = bisect.bisect_left(days, d)                          # closes strictly before d
        v = readings[k]
        hist = [x for x in readings[max(0, k - RANK_DAYS):k] if x is not None]
        if v is None or len(hist) < RANK_MIN:
            out[d] = None
            continue
        h = np.asarray(hist)
        out[d] = float(100 * ((h < v).sum() + 0.5 * (h == v).sum()) / h.size)
    return out


def regime(p: float | None) -> str:
    if p is None:
        return "no_history"
    return "calm" if p < LOW else "wild" if p > HIGH else "normal"


class VolFiltered(Strategy):
    """Wraps a strategy; drops an order unless its New York date is a 'normal' volatility day."""

    def __init__(self, inner: Strategy, pct: dict):
        self.inner, self.pct = inner, pct
        self.name, self.rr = inner.name, inner.rr
        self.skipped = {"calm": 0, "wild": 0, "no_history": 0}

    def new_day(self, day) -> None:
        self.inner.new_day(day)

    def on_bar(self, i: int, a: dict) -> Order | None:
        o = self.inner.on_bar(i, a)
        if o is None:
            return None
        r = regime(self.pct.get(a["ny_date"][i]))
        if r != "normal":
            self.skipped[r] += 1
            return None
        return o


def random_skip_beaten(base_r, filtered_avg: float, n_keep: int, runs: int = 500, seed: int = 7) -> float:
    """Share of random-skip controls (keep n_keep of the base trades at random) that the filter BEATS."""
    base = np.asarray(base_r, dtype=float)
    if n_keep <= 0 or n_keep > base.size:
        return 0.0
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(base, size=n_keep, replace=False).mean() for _ in range(runs)])
    return float((filtered_avg > means).mean())


def is_finite(x) -> bool:
    return x is not None and math.isfinite(x)
