"""Strategy report card: the ideas of "Quantitative Finance From Scratch" applied to our backtest trades.

Input: a list of trade results in R (after costs). 1R = the amount risked on that trade.
Pure functions, no files or network. Every number answers one plain question:

  expected value (ch 3)   avg_r         What does one trade make on average?
  standard error (ch 15)  se, ci95      How sure are we about that average?
  luck check (ch 4)       p_no_edge     How often would a strategy with NO edge look at least this good?
  volatility (ch 7)       std_r         How much do single trades swing?
  Sharpe ratio (ch 8)     sharpe_year   Return per unit of swing, per year (risk-free rate taken as 0).
  volatility drag (ch 9)  growth_year   What the account really keeps per year at the chosen risk %.
  Kelly (ch 14)           kelly_pct     Best % of the account to risk per trade. 0 = do not trade.
  fat tails / ES (16-17)  es5           Average of the worst 5 % of trades.
  Monte Carlo (ch 15)     mc_*          10,000 reshuffled years: typical, bad and worst cases.

None of this creates an edge. It only measures whether one exists.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

SEED = 7                 # fixed seed (ch 15): the same numbers every run
MC_PATHS = 10_000


@dataclass(frozen=True)
class Card:
    trades: int
    trades_per_year: float
    win_pct: float
    avg_r: float
    se: float
    ci95_low: float
    ci95_high: float
    p_no_edge: float          # bootstrap share of resamples with average <= 0
    std_r: float
    sharpe_trade: float
    sharpe_year: float
    growth_year_pct: float    # compounded yearly growth at `risk_pct` per trade
    kelly_pct: float          # % of account to risk per trade (0 if no edge)
    es5_r: float
    longest_losing_streak: int
    mc_median_pct: float      # one year of trades at `risk_pct`, 10,000 reshuffled paths
    mc_p10_pct: float
    mc_p90_pct: float
    mc_loss_chance_pct: float
    mc_median_max_dd_pct: float
    mc_worst5_max_dd_pct: float
    verdict: str

    def as_dict(self) -> dict:
        return asdict(self)


def longest_streak(r: np.ndarray) -> int:
    best = run = 0
    for x in r:
        run = run + 1 if x < 0 else 0
        best = max(best, run)
    return best


def kelly_fraction(r: np.ndarray) -> float:
    """Kelly share of the account to RISK per trade, for outcomes in R: maximise the average of
    ln(1 + f * R). Grid search (no formula needed for mixed outcomes). 0 when there is no edge."""
    if r.size == 0 or r.mean() <= 0:
        return 0.0
    worst = -r.min()
    f_max = 0.999 / worst if worst > 0 else 1.0       # never risk so much that one trade wipes the account
    grid = np.linspace(0, min(f_max, 1.0), 2001)
    growth = np.array([np.log1p(f * r).mean() for f in grid])
    return float(grid[int(growth.argmax())])


def max_drawdowns(paths: np.ndarray) -> np.ndarray:
    """paths: equity curves (rows). Returns the largest fall from a peak for each row, as a fraction."""
    peaks = np.maximum.accumulate(paths, axis=1)
    return ((peaks - paths) / peaks).max(axis=1)


def report(r_values, years: float, risk_pct: float = 0.5, seed: int = SEED) -> Card:
    r = np.asarray(r_values, dtype=float)
    n = r.size
    if n < 2 or years <= 0:
        raise ValueError("need at least 2 trades and a positive number of years")
    rng = np.random.default_rng(seed)
    per_year = n / years
    avg, std = float(r.mean()), float(r.std(ddof=1))
    se = std / math.sqrt(n)
    boot = rng.choice(r, size=(MC_PATHS, n)).mean(axis=1)
    p_no_edge = float((boot <= 0).mean())
    sharpe_trade = avg / std if std > 0 else 0.0
    f = risk_pct / 100
    g_trade = float(np.log1p(f * r).mean())
    tail = np.sort(r)[: max(1, int(math.ceil(0.05 * n)))]

    k = max(1, int(round(per_year)))                    # Monte Carlo: one year = k trades drawn from history
    draws = rng.choice(r, size=(MC_PATHS, k))
    equity = np.cumprod(1 + f * draws, axis=1)
    equity = np.hstack([np.ones((MC_PATHS, 1)), equity])
    final = (equity[:, -1] - 1) * 100
    dd = max_drawdowns(equity) * 100

    ci_low, ci_high = avg - 1.96 * se, avg + 1.96 * se
    if ci_low > 0:
        verdict = "EDGE LIKELY (still needs a pre-registered test)"
    elif ci_high < 0:
        verdict = "LOSES ON AVERAGE (do not trade)"
    else:
        verdict = "NO PROVEN EDGE (could be luck either way)"
    return Card(
        trades=n, trades_per_year=round(per_year, 1), win_pct=round(float((r > 0).mean() * 100), 1),
        avg_r=round(avg, 3), se=round(se, 3), ci95_low=round(ci_low, 3), ci95_high=round(ci_high, 3),
        p_no_edge=round(p_no_edge, 3), std_r=round(std, 3),
        sharpe_trade=round(sharpe_trade, 3), sharpe_year=round(sharpe_trade * math.sqrt(per_year), 2),
        growth_year_pct=round((math.exp(g_trade * per_year) - 1) * 100, 1),
        kelly_pct=round(kelly_fraction(r) * 100, 2), es5_r=round(float(tail.mean()), 2),
        longest_losing_streak=longest_streak(r),
        mc_median_pct=round(float(np.median(final)), 1), mc_p10_pct=round(float(np.percentile(final, 10)), 1),
        mc_p90_pct=round(float(np.percentile(final, 90)), 1),
        mc_loss_chance_pct=round(float((final < 0).mean() * 100), 1),
        mc_median_max_dd_pct=round(float(np.median(dd)), 1),
        mc_worst5_max_dd_pct=round(float(np.percentile(dd, 95)), 1),
        verdict=verdict)
