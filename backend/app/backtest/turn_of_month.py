"""Turn-of-the-month test (docs/turn_of_month_preregistration.md). Pure functions, measurement only.

Buy at the close of the second-to-last trading day of a month, sell at the close of the 3rd trading day of the next
month. Net return = price return - spread - financing per calendar night.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.backtest.robustness import cluster_means

SPREAD = 0.0002          # 0.02% of price per round trip
FINANCING = 0.07         # 7% a year, per calendar night held
STRESS = 2.0             # stress = both costs doubled
HOLD_DAYS = 4            # trading-day returns earned (last day + first 3 days)
DEV, VAL = (1971, 1999), (2000, 2024)
MIN_TRADES = 30
RUNS, SEED = 5000, 11

PASS, NEGATIVE, INCONCLUSIVE = ("passes the research criteria", "negative observed result", "inconclusive")


def windows(dates: pd.DatetimeIndex) -> list[tuple[int, int]]:
    """(entry index, exit index) for every complete month turn."""
    months = dates.year * 12 + (dates.month - 1)
    idx_by_month: dict[int, list[int]] = {}
    for i, m in enumerate(months):
        idx_by_month.setdefault(int(m), []).append(i)
    out = []
    for m, days in idx_by_month.items():
        nxt = idx_by_month.get(m + 1)
        if len(days) >= 2 and nxt and len(nxt) >= 3:
            entry, exit_ = days[-2], nxt[2]
            assert exit_ - entry == HOLD_DAYS, "trading days must be consecutive"
            out.append((entry, exit_))
    return sorted(out)


def net_return(prices: np.ndarray, dates: pd.DatetimeIndex, entry: np.ndarray, exit_: np.ndarray,
               cost_mult: float = 1.0) -> np.ndarray:
    gross = prices[exit_] / prices[entry] - 1
    nights = (dates[exit_] - dates[entry]).days.to_numpy()
    return gross - cost_mult * (SPREAD + FINANCING * nights / 365)


@dataclass(frozen=True)
class Period:
    name: str
    n: int
    gross_avg: float
    net_avg: float
    low: float
    high: float
    stress_avg: float
    random_p95: float
    random_share_beaten: float     # share of random runs whose average is below the rule's
    win_rate: float
    tom_daily: float               # average daily price return on the 4 turn-of-month days
    all_daily: float               # average daily price return on all days

    def ok(self) -> bool:
        return (self.n >= MIN_TRADES and self.net_avg > 0 and self.low > 0 and self.net_avg > self.random_p95
                and self.stress_avg > 0)


def evaluate(s: pd.Series, years: tuple[int, int], name: str, runs: int = RUNS, seed: int = SEED) -> Period:
    prices, dates = s.to_numpy(dtype=float), s.index
    w = [(a, b) for a, b in windows(dates) if years[0] <= dates[a].year <= years[1]]
    entry = np.array([a for a, _ in w], dtype=int)
    exit_ = np.array([b for _, b in w], dtype=int)
    gross = prices[exit_] / prices[entry] - 1
    net = net_return(prices, dates, entry, exit_)
    stress = net_return(prices, dates, entry, exit_, STRESS)
    yrs = dates[entry].year.to_numpy()
    means = cluster_means(net, yrs, runs, seed)
    # Random timing: same number of 4-trading-day holds starting on random trading days of the same period.
    starts = np.flatnonzero((dates.year >= years[0]) & (dates.year <= years[1]))
    starts = starts[starts + HOLD_DAYS < len(prices)]
    every = net_return(prices, dates, starts, starts + HOLD_DAYS)
    rng = np.random.default_rng(seed)
    rand_means = every[rng.integers(0, len(every), size=(runs, len(net)))].mean(axis=1)
    daily = prices[1:] / prices[:-1] - 1
    in_period = (dates[1:].year >= years[0]) & (dates[1:].year <= years[1])
    tom_days = np.zeros(len(daily), dtype=bool)
    for a, b in w:
        tom_days[a:b] = True          # daily[i] is the return from day i to day i+1
    return Period(name, len(net), float(gross.mean()), float(net.mean()), float(np.percentile(means, 2.5)),
                  float(np.percentile(means, 97.5)), float(stress.mean()), float(np.percentile(rand_means, 95)),
                  float((rand_means < net.mean()).mean()), float((net > 0).mean()),
                  float(daily[tom_days & in_period].mean()), float(daily[in_period].mean()))


def verdict(dev: Period, val: Period) -> str:
    if dev.net_avg <= 0 or val.net_avg <= 0:
        return NEGATIVE
    return PASS if dev.ok() and val.ok() else INCONCLUSIVE
