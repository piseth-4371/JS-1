"""Research only: multi-day trend strategies on daily bars (rules in docs/daily_trend_preregistration.md).

Pure functions. Signals use the day's CLOSE; orders fill at the NEXT day's open (no look-ahead).
Stops are fixed at entry (2 x ATR20) and checked on every later day: a gap through the stop fills at the open.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

NY = "America/New_York"


@dataclass
class DTrade:
    strategy: str
    side: int
    entry_day: date
    exit_day: date
    entry: float
    exit: float
    risk_pts: float
    days_held: int          # calendar days (for financing)
    bars_held: int          # trading days
    reason: str

    def r(self, cost_pts: float = 2.0, fin_rate: float = 0.05) -> float:
        gross = (self.exit - self.entry) * self.side / self.risk_pts
        financing = self.entry * fin_rate * self.days_held / 365
        return gross - (cost_pts + financing) / self.risk_pts


def daily_bars(m1: pd.DataFrame) -> pd.DataFrame:
    """M1 (ts UTC seconds, o h l c) -> daily OHLC; the day runs 18:00 -> 17:00 New York time."""
    t = pd.to_datetime(m1["ts"], unit="s", utc=True).dt.tz_convert(NY)
    day = (t + pd.Timedelta(hours=6)).dt.date          # 18:00 NY belongs to the next day
    df = m1.assign(day=day)
    d = df.groupby("day").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), n=("c", "size"))
    d = d[d["n"] >= 300]                                 # skip holiday stubs / near-empty days
    d.index = pd.Index(d.index, name="day")
    prev_c = d["c"].shift(1)
    tr = pd.concat([d["h"] - d["l"], (d["h"] - prev_c).abs(), (d["l"] - prev_c).abs()], axis=1).max(axis=1)
    d["atr20"] = tr.rolling(20).mean()
    d["sma100"] = d["c"].rolling(100).mean()
    d["hh55"] = d["h"].rolling(55).max().shift(1)       # previous 55 days, today excluded
    d["ll55"] = d["l"].rolling(55).min().shift(1)
    d["hh20"] = d["h"].rolling(20).max().shift(1)
    d["ll20"] = d["l"].rolling(20).min().shift(1)
    return d.drop(columns="n")


def _signals(d: pd.DataFrame, name: str) -> tuple[np.ndarray, np.ndarray]:
    """entry_side[i] (+1/-1/0) and exit_flag[i][side] decided on day i's close."""
    c = d["c"].to_numpy()
    if name == "sma100_long":
        s = d["sma100"].to_numpy()
        entry = np.where(c > s, 1, 0)
        exit_long = c < s
        exit_short = np.zeros(len(c), bool)
    elif name == "donchian_55_20":
        entry = np.where(c > d["hh55"].to_numpy(), 1, np.where(c < d["ll55"].to_numpy(), -1, 0))
        exit_long = c < d["ll20"].to_numpy()
        exit_short = c > d["hh20"].to_numpy()
    else:
        raise ValueError(name)
    return entry, np.vstack([exit_short, exit_long])     # row 0 = short, row 1 = long


def run_daily(d: pd.DataFrame, name: str, stop_atr: float = 2.0) -> list[DTrade]:
    entry_sig, exit_sig = _signals(d, name)
    o, h, lo = d["o"].to_numpy(), d["h"].to_numpy(), d["l"].to_numpy()
    atr = d["atr20"].to_numpy()
    days = list(d.index)
    trades: list[DTrade] = []
    i, n = 0, len(d)
    while i < n - 1:
        side = int(entry_sig[i])
        if side == 0 or np.isnan(atr[i]) or (name == "sma100_long" and np.isnan(d["sma100"].iat[i])):
            i += 1
            continue
        k = i + 1                                         # fill at next open
        entry = o[k]
        risk = stop_atr * atr[i]
        stop = entry - side * risk
        exit_px, reason, j = None, "", k
        while j < n:
            # stop first (pessimistic): a gap through the stop fills at the open
            if side == 1 and lo[j] <= stop:
                exit_px, reason = (o[j] if o[j] < stop else stop), "stop"
            elif side == -1 and h[j] >= stop:
                exit_px, reason = (o[j] if o[j] > stop else stop), "stop"
            elif exit_sig[1 if side == 1 else 0][j] and j + 1 < n:
                j += 1
                exit_px, reason = o[j], "signal"
            if exit_px is not None:
                break
            j += 1
        if exit_px is None:                               # still open at the end of the data
            j = n - 1
            exit_px, reason = d["c"].iat[j], "end of data"
        trades.append(DTrade(name, side, days[k], days[j], float(entry), float(exit_px), float(risk),
                             (days[j] - days[k]).days, j - k, reason))
        i = j if reason != "signal" else j - 1            # look for the next signal from the exit day's close
        i = max(i, k)
    return trades


def random_control(d: pd.DataFrame, trades: list[DTrade], runs: int = 500, stop_atr: float = 2.0,
                   seed: int = 7, cost_pts: float = 2.0, fin_rate: float = 0.05) -> np.ndarray:
    """Average R of 'same side, same holding length, same stop, random entry day' for each run."""
    rng = np.random.default_rng(seed)
    o, h, lo, c = (d[x].to_numpy() for x in ("o", "h", "l", "c"))
    atr = d["atr20"].to_numpy()
    days = list(d.index)
    valid = np.where(~np.isnan(atr))[0]
    out = np.empty(runs)
    for r_ in range(runs):
        rs = []
        for t in trades:
            hold = max(t.bars_held, 1)
            cand = valid[valid + 1 + hold < len(d)]
            i = int(rng.choice(cand))
            k = i + 1
            entry, risk = o[k], stop_atr * atr[i]
            stop = entry - t.side * risk
            exit_px, j = None, k
            for j in range(k, k + hold + 1):
                if t.side == 1 and lo[j] <= stop:
                    exit_px = o[j] if o[j] < stop else stop
                    break
                if t.side == -1 and h[j] >= stop:
                    exit_px = o[j] if o[j] > stop else stop
                    break
            if exit_px is None:
                j = k + hold
                exit_px = o[j]
            fake = DTrade("control", t.side, days[k], days[j], entry, exit_px, risk, (days[j] - days[k]).days, j - k, "")
            rs.append(fake.r(cost_pts, fin_rate))
        out[r_] = float(np.mean(rs)) if rs else 0.0
    return out
