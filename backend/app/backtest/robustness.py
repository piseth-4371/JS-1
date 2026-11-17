"""Robustness statistics for a list of trade results (in R). Pure functions, research only.

- monte_carlo(): shuffle the ORDER of the same trades many times. The total stays the same,
  but drawdown and losing streaks change - this shows what a bad-luck order could look like.
- bootstrap(): resample trades WITH replacement to see how uncertain the average R is.
  `p_no_edge` = share of resamples with average R <= 0. It is a resampling frequency, NOT the
  probability that the strategy has no edge (or that it is profitable). ci_low/ci_high = 5th/95th
  percentiles, i.e. a 90% range. Trades are treated as independent (iid), which understates
  uncertainty when trades cluster in time - see cluster_bootstrap().
- cluster_bootstrap(): resample whole groups (e.g. ISO weeks) instead of single trades, so trades
  from the same week stay together. Wider (more honest) range when trades are dependent.
- Multiple testing: when many strategy versions were tried, a 95% range for ONE of them is too narrow.
  bonferroni_z() gives the wider z for a family of tests.
- monte_carlo() reshuffles the order of the same trades, so it also assumes trades are exchangeable
  (no regimes); real drawdowns can be worse when losses cluster.
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
    p_no_edge: float          # share of resamples with average R <= 0 (a frequency, not a probability of no edge)


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


@dataclass
class ClusterBootstrap:
    runs: int
    groups: int
    avg_r: float
    ci_low: float             # 2.5th percentile of the average R (95% range)
    ci_high: float            # 97.5th percentile
    share_le0: float          # share of resamples with average R <= 0 (not a probability of no edge)


def cluster_means(rs, groups, runs: int = 5000, seed: int = 11) -> np.ndarray:
    """Averages of `runs` resamples that draw whole groups (e.g. weeks) with replacement."""
    rs = np.asarray(rs, dtype=float)
    _, inv = np.unique(np.asarray(groups), return_inverse=True)
    sums = np.bincount(inv, weights=rs)
    counts = np.bincount(inv).astype(float)
    g = len(sums)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, g, size=(runs, g))
    return sums[idx].sum(axis=1) / counts[idx].sum(axis=1)


def cluster_bootstrap(rs, groups, runs: int = 5000, seed: int = 11) -> ClusterBootstrap:
    """Resample whole groups (e.g. weeks) with replacement; the average is over all trades drawn."""
    rs = np.asarray(rs, dtype=float)
    if len(rs) == 0:
        return ClusterBootstrap(runs, 0, 0.0, 0.0, 0.0, 1.0)
    g = len(np.unique(np.asarray(groups)))
    means = cluster_means(rs, groups, runs, seed)
    return ClusterBootstrap(runs, g, float(rs.mean()), float(np.percentile(means, 2.5)),
                            float(np.percentile(means, 97.5)), float(np.mean(means <= 0)))


def bonferroni_z(tests: int, alpha: float = 0.05) -> float:
    """Two-sided z for a family-wise error rate `alpha` over `tests` tests (1.96 for one test)."""
    from statistics import NormalDist
    return NormalDist().inv_cdf(1 - alpha / (2 * max(1, tests)))


def bootstrap(rs, runs: int = 5000, seed: int = 11) -> Bootstrap:
    rs = np.asarray(rs, dtype=float)
    if len(rs) == 0:
        return Bootstrap(runs, 0.0, 0.0, 0.0, 1.0)
    rng = np.random.default_rng(seed)
    means = rng.choice(rs, size=(runs, len(rs)), replace=True).mean(axis=1)
    return Bootstrap(runs, float(rs.mean()), float(np.percentile(means, 5)), float(np.percentile(means, 95)),
                     float(np.mean(means <= 0)))
