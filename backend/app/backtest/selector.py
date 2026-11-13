"""Walk-forward STRATEGY SELECTOR ("auto-switch") - research only.

Question: does picking the strategy that did best RECENTLY beat simply
sticking with one strategy?

How it avoids cheating (look-ahead):
- Every Monday (New York) the selector looks ONLY at trades that already
  closed before that Monday 00:00 NY, inside a lookback window.
- It picks one strategy for the whole week (or none), then takes exactly the
  trades that strategy made that week. Those trades were simulated by the
  normal backtester with the same Risk Manager, fills and costs.

Rules (fixed BEFORE looking at results):
- criterion "avg_r":    pick the highest average R; pick NOTHING if the best is <= 0
- criterion "win_rate": pick the highest win rate (owner's idea), regardless of R
- a strategy needs at least `min_trades` trades in the lookback to be eligible

Approximation: each strategy's trades come from its own run, so daily/weekly
loss locks follow that strategy's own history. Only one strategy trades per
week, so this is close to - not identical with - one combined account.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


@dataclass
class Pick:
    week_start: date
    strategy: str | None
    score: float | None
    candidates: int          # strategies with enough trades in the lookback


@dataclass
class SelectorResult:
    name: str
    trades: list = field(default_factory=list)
    picks: list[Pick] = field(default_factory=list)

    def pick_counts(self) -> Counter:
        return Counter(p.strategy or "(no trade)" for p in self.picks)


def _ny_midnight(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=NY).timestamp())


def mondays(start: date, end: date) -> list[date]:
    d = start + timedelta(days=(7 - start.weekday()) % 7)
    out = []
    while d < end:
        out.append(d)
        d += timedelta(days=7)
    return out


def score(trades: list, criterion: str) -> float:
    rs = [t.r for t in trades]
    if criterion == "avg_r":
        return sum(rs) / len(rs)
    if criterion == "win_rate":
        return sum(r > 0 for r in rs) / len(rs) * 100
    raise ValueError(criterion)


def walk_forward(trades_by_strategy: dict[str, list], start: date, end: date, lookback_days: int,
                 criterion: str = "avg_r", min_trades: int = 10) -> SelectorResult:
    res = SelectorResult(f"auto-switch {criterion} {lookback_days // 30}m")
    for monday in mondays(start, end):
        t0 = _ny_midnight(monday)
        look_from = _ny_midnight(monday - timedelta(days=lookback_days))
        week_end = _ny_midnight(monday + timedelta(days=7))
        best, best_score, eligible = None, None, 0
        for name, trades in trades_by_strategy.items():
            past = [t for t in trades if look_from <= t.entry_ts and t.exit_ts < t0]   # only what was KNOWN
            if len(past) < min_trades:
                continue
            eligible += 1
            sc = score(past, criterion)
            if best_score is None or sc > best_score:
                best, best_score = name, sc
        if criterion == "avg_r" and best_score is not None and best_score <= 0:
            best = None                     # everything is losing recently: stay out
        res.picks.append(Pick(monday, best, best_score, eligible))
        if best:
            res.trades += [t for t in trades_by_strategy[best] if t0 <= t.entry_ts < week_end]
    res.trades.sort(key=lambda t: t.entry_ts)
    return res
