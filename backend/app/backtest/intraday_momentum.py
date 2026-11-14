"""Research only: market intraday momentum (rules in docs/intraday_momentum_preregistration.md).

First half-hour return (prev 16:00 close -> 10:00) decides the direction of a 15:30 -> 15:55 trade.
Pure functions on a 1-minute DataFrame (ts UTC seconds, o h l c). New York time throughout.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

NY = "America/New_York"
M_0959, M_1529, M_1530, M_1554, M_1559 = 9 * 60 + 59, 15 * 60 + 29, 15 * 60 + 30, 15 * 60 + 54, 15 * 60 + 59


@dataclass
class Day:
    day: date
    r1: float                 # first half-hour return incl. overnight
    entry: float              # close of the 15:29 bar
    risk: float               # 2 x ATR14(5m) in points
    o: np.ndarray             # 1-minute bars of the trade window
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    exit_i: int               # index in the window of the exit bar (15:54, or 15:59 for the info variant)


def early_close(d: date) -> bool:
    """US cash market closes at 13:00 on these days (when they fall on weekdays)."""
    if (d.month, d.day) in ((7, 3), (12, 24)):
        return True
    # day after Thanksgiving = the Friday after the 4th Thursday of November
    if d.month == 11 and d.weekday() == 4:
        thursdays = [x for x in range(1, 31) if date(d.year, 11, x).weekday() == 3]
        return d - timedelta(days=1) == date(d.year, 11, thursdays[3])
    return False


def build_days(m1: pd.DataFrame, exit_minute: int = M_1554, stop_atr: float = 2.0) -> list[Day]:
    t = pd.to_datetime(m1["ts"], unit="s", utc=True).dt.tz_convert(NY)
    df = pd.DataFrame({"day": t.dt.date, "mod": t.dt.hour * 60 + t.dt.minute,
                       "o": m1["o"].to_numpy(), "h": m1["h"].to_numpy(), "l": m1["l"].to_numpy(), "c": m1["c"].to_numpy()})
    df = df[t.dt.day_of_week.to_numpy() < 5]
    close_1559 = df[df["mod"] == M_1559].set_index("day")["c"]
    out: list[Day] = []
    prev_close = None
    for d, g in df.groupby("day", sort=True):
        g = g.set_index("mod")
        pc = prev_close
        prev_close = close_1559.get(d, None)            # becomes "previous close" for the next day
        if pc is None or early_close(d):
            continue
        need = (M_0959, M_1529, exit_minute)
        if any(m not in g.index for m in need):
            continue
        # ATR14 of 5-minute bars ending at 15:30 (bins 14:20 ... 15:25)
        w = g.loc[(g.index >= 14 * 60 + 20) & (g.index < M_1530)]
        if w.empty:
            continue
        b = w.groupby(w.index // 5).agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
        if len(b) < 10:
            continue
        pcs = b["c"].shift(1)
        tr = pd.concat([b["h"] - b["l"], (b["h"] - pcs).abs(), (b["l"] - pcs).abs()], axis=1).max(axis=1)
        atr = float(tr.mean())
        win = g.loc[(g.index >= M_1530) & (g.index <= exit_minute)]
        if win.empty or atr <= 0:
            continue
        out.append(Day(d, float(g.at[M_0959, "c"] / pc - 1.0), float(g.at[M_1529, "c"]), stop_atr * atr,
                       win["o"].to_numpy(), win["h"].to_numpy(), win["l"].to_numpy(), win["c"].to_numpy(),
                       int(np.where(win.index.to_numpy() == exit_minute)[0][0])))
    return out


def trade_r(x: Day, side: int, cost_pts: float = 2.0) -> float:
    """R of one trade: enter at x.entry, exit at the exit bar's close or at the stop (gap -> the open)."""
    stop = x.entry - side * x.risk
    exit_px = x.c[x.exit_i]
    for j in range(x.exit_i + 1):
        if side == 1 and x.l[j] <= stop:
            exit_px = x.o[j] if x.o[j] < stop else stop
            break
        if side == -1 and x.h[j] >= stop:
            exit_px = x.o[j] if x.o[j] > stop else stop
            break
    return ((exit_px - x.entry) * side - cost_pts) / x.risk


def signal_side(x: Day) -> int:
    return 1 if x.r1 > 0 else -1 if x.r1 < 0 else 0


def random_direction_control(days: list[Day], runs: int = 500, seed: int = 11, cost_pts: float = 2.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    longs = np.array([trade_r(x, 1, cost_pts) for x in days])
    shorts = np.array([trade_r(x, -1, cost_pts) for x in days])
    pick = rng.integers(0, 2, size=(runs, len(days)))
    return np.where(pick == 1, longs, shorts).mean(axis=1)
