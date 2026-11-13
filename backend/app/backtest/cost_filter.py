"""Research only: skip trades whose trading cost is too large compared with their risk.

Lesson from the BTC tests: when the stop is tiny, fixed costs eat most of the edge.
CostFiltered wraps any strategy and drops an order when
    cost_points / risk_points > max_share
The rule (2.0 points, 20%) was fixed BEFORE the validation run. It is NOT used by the
live engine: adding it there would change core strategy rules and needs owner approval.
"""
from __future__ import annotations

from app.core.strategies.base import Order, Strategy


class CostFiltered(Strategy):
    def __init__(self, inner: Strategy, cost_pts: float = 2.0, max_share: float = 0.20):
        self.inner, self.cost_pts, self.max_share = inner, cost_pts, max_share
        self.name = inner.name               # trades keep the original strategy name
        self.rr = inner.rr
        self.skipped = 0

    def new_day(self, day) -> None:
        self.inner.new_day(day)

    def on_bar(self, i: int, a: dict) -> Order | None:
        o = self.inner.on_bar(i, a)
        if o is None:
            return None
        risk = abs(o.entry - o.stop)
        if risk <= 0 or self.cost_pts / risk > self.max_share:
            self.skipped += 1
            return None
        return o
