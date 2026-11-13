"""Agent 5 — Performance Analyst (statistics part). Read-only maths on finished trades."""
from __future__ import annotations

import statistics
from dataclasses import dataclass

MIN_TRADES_FOR_CONCLUSION = 30


@dataclass
class Stats:
    n: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    expectancy_r: float     # average R per trade = the "edge"
    total_r: float
    profit_factor: float
    return_pct: float       # compounded at the risk % used
    max_dd_pct: float
    longest_losing_streak: int
    trades_per_month: float
    note: str


def compute(trades, months: float, risk_pct: float = 0.5) -> Stats:
    rs = [t.r for t in trades]
    n = len(rs)
    if n == 0:
        return Stats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "no trades")
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    gross_win, gross_loss = sum(wins), -sum(losses)
    eq, peak, max_dd = 1.0, 1.0, 0.0
    streak = longest = 0
    for r in rs:
        eq *= 1 + risk_pct / 100 * r
        peak = max(peak, eq)
        max_dd = max(max_dd, 1 - eq / peak)
        streak = streak + 1 if r <= 0 else 0
        longest = max(longest, streak)
    note = "too few trades to conclude" if n < MIN_TRADES_FOR_CONCLUSION else ""
    return Stats(
        n=n,
        win_rate=len(wins) / n * 100,
        avg_win_r=statistics.mean(wins) if wins else 0.0,
        avg_loss_r=statistics.mean(losses) if losses else 0.0,
        expectancy_r=statistics.mean(rs),
        total_r=sum(rs),
        profit_factor=gross_win / gross_loss if gross_loss > 0 else float("inf"),
        return_pct=(eq - 1) * 100,
        max_dd_pct=max_dd * 100,
        longest_losing_streak=longest,
        trades_per_month=n / months if months else 0.0,
        note=note,
    )
