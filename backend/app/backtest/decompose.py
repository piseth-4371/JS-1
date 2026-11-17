"""Where profits and losses come from: cost breakdown, trade matching between fill models, summary
statistics and the pre-registered verdict (docs/bidask_full_preregistration.md). Pure functions.

Measurement only: nothing here creates signals or changes rules.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.backtest.robustness import cluster_means
from app.core.fills import Costs

STOP_LIKE_EXITS = ("stop", "session_end", "kill_switch")
SLIP_ENTRIES = ("market", "stop")


@dataclass(frozen=True)
class CostSplit:
    gross: float      # (exit - entry) * side / risk, before any cost
    spread: float     # spread / risk
    slippage: float   # slippage legs / risk
    fees: float       # fee / risk
    net: float        # gross - spread - slippage - fees


def cost_split(t, costs: Costs) -> CostSplit:
    """Split one trade's R into gross and the cost parts, using exactly the rule in fills.net_points."""
    risk = t.risk_pts
    gross = (t.exit - t.entry) * t.side / risk
    legs = (t.kind in SLIP_ENTRIES) + (t.exit_reason in STOP_LIKE_EXITS)
    slip = legs * (costs.slippage + t.entry * costs.slip_pct / 100) / risk
    fees = t.entry * costs.fee_pct / 100 / risk
    spread = costs.spread / risk
    return CostSplit(gross, spread, slip, fees, gross - spread - slip - fees)


def key(t) -> tuple[int, int]:
    return int(t.entry_ts), int(t.side)


@dataclass
class Matched:
    pairs: list          # [(a_trade, b_trade)] same entry minute and side
    only_a: list
    only_b: list


def match(a: list, b: list) -> Matched:
    bk = {key(t): t for t in b}
    pairs, only_a = [], []
    for t in a:
        u = bk.pop(key(t), None)
        if u is None:
            only_a.append(t)
        else:
            pairs.append((t, u))
    return Matched(pairs, only_a, sorted(bk.values(), key=key))


@dataclass(frozen=True)
class FillEffect:
    total_a: float
    total_b: float
    matched_diff: float    # sum over matched trades of (b.r - a.r)
    only_b: float          # sum R of trades only in b
    only_a: float          # sum R of trades only in a
    n_matched: int
    n_only_a: int
    n_only_b: int

    @property
    def residual(self) -> float:
        """total_b - total_a - (matched_diff + only_b - only_a); 0 when it reconciles."""
        return self.total_b - self.total_a - (self.matched_diff + self.only_b - self.only_a)


def fill_effect(a: list, b: list) -> FillEffect:
    m = match(a, b)
    return FillEffect(float(sum(t.r for t in a)), float(sum(t.r for t in b)),
                      float(sum(u.r - t.r for t, u in m.pairs)), float(sum(t.r for t in m.only_b)),
                      float(sum(t.r for t in m.only_a)), len(m.pairs), len(m.only_a), len(m.only_b))


def max_drawdown_pct(rs, risk_pct: float = 0.5) -> float:
    eq = np.concatenate(([1.0], np.cumprod(1 + risk_pct / 100 * np.asarray(rs, dtype=float))))
    peak = np.maximum.accumulate(eq)
    return float(((peak - eq) / peak).max() * 100)


@dataclass(frozen=True)
class Summary:
    n: int
    win_rate: float
    avg_win: float
    avg_loss: float
    avg: float
    profit_factor: float   # sum of winning R / |sum of losing R|; inf if no losers
    max_dd_pct: float


def summarize(rs) -> Summary:
    rs = np.asarray(rs, dtype=float)
    if rs.size == 0:
        nan = float("nan")
        return Summary(0, nan, nan, nan, nan, nan, 0.0)
    w, lo = rs[rs > 0], rs[rs <= 0]
    pf = float(w.sum() / -lo.sum()) if lo.sum() < 0 else float("inf")
    return Summary(int(rs.size), float(w.size / rs.size), float(w.mean()) if w.size else float("nan"),
                   float(lo.mean()) if lo.size else float("nan"), float(rs.mean()), pf, max_drawdown_pct(rs))


def week_of(d) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-{w:02d}"


def week_interval(rs, dates, tests: int = 1, runs: int = 5000, seed: int = 11) -> tuple[float, float]:
    """Two-sided interval for the average R from whole-week block resampling, Bonferroni-widened for `tests`."""
    rs = np.asarray(rs, dtype=float)
    if rs.size < 2:
        return float("nan"), float("nan")
    means = cluster_means(rs, [week_of(d) for d in dates], runs, seed)
    tail = 2.5 / max(1, tests)
    return float(np.percentile(means, tail)), float(np.percentile(means, 100 - tail))


PASS, NEGATIVE, INCONCLUSIVE, INCOMPLETE = ("passes the research criteria", "negative observed expectancy",
                                            "inconclusive", "incomplete data — no verdict")


@dataclass(frozen=True)
class SplitResult:
    n: int
    avg: float
    family_low: float
    stress_avg: float
    coverage_ok: bool


def verdict(dev: SplitResult, val: SplitResult, min_trades: int = 30) -> str:
    """Pre-registered rule (docs/bidask_full_preregistration.md)."""
    if not (dev.coverage_ok and val.coverage_ok):
        return INCOMPLETE
    if any(s.n > 0 and not s.avg > 0 for s in (dev, val)):
        return NEGATIVE                       # a split with no trades has no average: it cannot pass (n < 30)
    if all(s.n >= min_trades and s.family_low > 0 and s.stress_avg > 0 for s in (dev, val)):
        return PASS
    return INCONCLUSIVE
