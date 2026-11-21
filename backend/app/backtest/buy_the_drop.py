"""Buy-the-drop test (docs/buy_the_drop_preregistration.md, commit 6943a95). Pure functions, measurement only.

Buy the Nasdaq Composite at a close that is the lowest of the last LOOKBACK trading days (strictly lower than each
of the previous LOOKBACK - 1 closes), sell at the close HOLD trading days later. One position at a time.
Net return = price return - spread - financing per calendar night (same costs as turn_of_month, E19).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.backtest.robustness import cluster_means
from app.backtest.turn_of_month import FINANCING, SPREAD, STRESS, net_return  # same costs as E19

LOOKBACK = 10            # today's close is the lowest of the last 10 trading days (today included)
HOLD = 5                 # sell at the close 5 trading days later
NEARBY = {"lookback": (7, 13), "hold": (4, 6)}   # fixed in the pre-registration
DEV, VAL = (1971, 1999), (2000, 2024)
MIN_TRADES = 30
RUNS, SEED = 5000, 11

PASS, NEGATIVE, INCONCLUSIVE = ("passes the research criteria", "negative observed result", "inconclusive")
__all__ = ["SPREAD", "FINANCING", "STRESS"]


def signals(prices: np.ndarray, lookback: int = LOOKBACK) -> np.ndarray:
    """True on day i if prices[i] is strictly below each of the previous lookback - 1 closes.
    The first lookback - 1 days cannot signal. Uses only closes up to and including day i (no look-ahead)."""
    n = len(prices)
    out = np.zeros(n, dtype=bool)
    k = lookback - 1
    for i in range(k, n):
        out[i] = prices[i] < prices[i - k:i].min()
    return out


def trades(prices: np.ndarray, lookback: int = LOOKBACK, hold: int = HOLD) -> list[tuple[int, int]]:
    """(entry index, exit index) pairs, one position at a time. Signals while a trade is open are ignored; the exit
    day can start a new trade if it is itself a signal. A trade without `hold` more days of data is not taken."""
    sig = signals(prices, lookback)
    out: list[tuple[int, int]] = []
    i, n = 0, len(prices)
    while i < n:
        if sig[i] and i + hold < n:
            out.append((i, i + hold))
            i += hold
        else:
            i += 1
    return out


def in_period(pairs: list[tuple[int, int]], dates: pd.DatetimeIndex, years: tuple[int, int]) -> list[tuple[int, int]]:
    """Trades whose entry year is in the period AND whose exit is still inside it (pre-registration: dropped otherwise)."""
    return [(a, b) for a, b in pairs if years[0] <= dates[a].year <= years[1] and dates[b].year <= years[1]]


def period_net(s: pd.Series, years: tuple[int, int], lookback: int = LOOKBACK, hold: int = HOLD,
               cost_mult: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """(net return per trade, entry year per trade) for one period."""
    prices, dates = s.to_numpy(dtype=float), s.index
    w = in_period(trades(prices, lookback, hold), dates, years)
    e = np.array([a for a, _ in w], dtype=int)
    x = np.array([b for _, b in w], dtype=int)
    if len(e) == 0:
        return np.array([]), np.array([], dtype=int)
    return net_return(prices, dates, e, x, cost_mult), dates[e].year.to_numpy()


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
    worst: float                   # worst single trade, net
    all_avg: float                 # information only: average net 5-day hold over every start day

    def core_ok(self) -> bool:
        """The checks in this module; the year-by-year and nearby checks are applied by the caller."""
        return (self.n >= MIN_TRADES and self.net_avg > 0 and self.stress_avg > 0 and self.low > 0
                and self.net_avg > self.random_p95)


def evaluate(s: pd.Series, years: tuple[int, int], name: str, runs: int = RUNS, seed: int = SEED) -> Period:
    prices, dates = s.to_numpy(dtype=float), s.index
    w = in_period(trades(prices), dates, years)
    e = np.array([a for a, _ in w], dtype=int)
    x = np.array([b for _, b in w], dtype=int)
    gross = prices[x] / prices[e] - 1
    net = net_return(prices, dates, e, x)
    stress = net_return(prices, dates, e, x, STRESS)
    means = cluster_means(net, dates[e].year.to_numpy(), runs, seed)
    # Random timing: same number of HOLD-day holds starting on random trading days, exit inside the period.
    starts = np.flatnonzero((dates.year >= years[0]) & (dates.year <= years[1]))
    starts = starts[starts + HOLD < len(prices)]
    starts = starts[dates[starts + HOLD].year <= years[1]]
    every = net_return(prices, dates, starts, starts + HOLD)
    rng = np.random.default_rng(seed)
    rand_means = every[rng.integers(0, len(every), size=(runs, len(net)))].mean(axis=1)
    return Period(name, len(net), float(gross.mean()), float(net.mean()), float(np.percentile(means, 2.5)),
                  float(np.percentile(means, 97.5)), float(stress.mean()), float(np.percentile(rand_means, 95)),
                  float((rand_means < net.mean()).mean()), float((net > 0).mean()), float(net.min()),
                  float(every.mean()))


def verdict(dev: Period, val: Period, year_ok: tuple[bool, bool], nearby_ok: tuple[bool, bool]) -> str:
    if dev.net_avg <= 0 or val.net_avg <= 0:
        return NEGATIVE
    if dev.core_ok() and val.core_ok() and all(year_ok) and all(nearby_ok):
        return PASS
    return INCONCLUSIVE
