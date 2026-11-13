"""Robustness statistics for a list of trade results (in R). Pure functions, research only.

- monte_carlo(): shuffle the ORDER of the same trades many times. The total stays the same,
  but drawdown and losing streaks change - this shows what a bad-luck order could look like.
- bootstrap(): resample trades WITH replacement to see how uncertain the average R is.
  `p_no_edge` = share of resamples with average R <= 0 (high = the edge may be luck).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MonteCarlo:
    runs: int
    max_dd_median: float      # % of equity
    max_dd_p95: float         # 1 in 20 orders is worse than this
    losing_streak_median: int
    losing_streak_p95: int


@dataclass
class Bootstrap:
    runs: int
    avg_r: float
    ci_low: float             # 5th percentile of the average R
    ci_high: float            # 95th percentile
    p_no_edge: float          # share of resamples with average R <= 0


def _path_stats(rs: np.ndarray, risk_pct: float) -> tuple[float, int]:
    eq = np.cumprod(1 + risk_pct / 100 * rs)
    peak = np.maximum.accumulate(np.concatenate(([1.0], eq)))[1:]
    max_dd = float(np.max(1 - eq / peak)) * 100 if len(eq) else 0.0
    longest = cur = 0
    for r in rs:
        cur = cur + 1 if r <= 0 else 0
        longest = max(longest, cur)
    return max_dd, longest


def monte_carlo(rs, risk_pct: float = 0.5, runs: int = 2000, seed: int = 7) -> MonteCarlo:
    rs = np.asarray(rs, dtype=float)
    rng = np.random.default_rng(seed)
    dds, streaks = [], []
    for _ in range(runs):
        dd, st = _path_stats(rng.permutation(rs), risk_pct)
        dds.append(dd)
        streaks.append(st)
    return MonteCarlo(runs, float(np.median(dds)), float(np.percentile(dds, 95)),
                      int(np.median(streaks)), int(np.percentile(streaks, 95)))


def bootstrap(rs, runs: int = 5000, seed: int = 11) -> Bootstrap:
    rs = np.asarray(rs, dtype=float)
    if len(rs) == 0:
        return Bootstrap(runs, 0.0, 0.0, 0.0, 1.0)
    rng = np.random.default_rng(seed)
    means = rng.choice(rs, size=(runs, len(rs)), replace=True).mean(axis=1)
    return Bootstrap(runs, float(rs.mean()), float(np.percentile(means, 5)), float(np.percentile(means, 95)),
                     float(np.mean(means <= 0)))
