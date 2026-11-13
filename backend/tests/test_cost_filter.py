from app.backtest.cost_filter import CostFiltered
from app.core.strategies.base import Order, Strategy


class _Fixed(Strategy):
    name = "fixed"
    rr = 2.0

    def __init__(self, order):
        self.order, self.days = order, 0

    def new_day(self, day):
        self.days += 1

    def on_bar(self, i, a):
        return self.order


def _order(entry, stop):
    return Order(strategy="fixed", side=1, kind="limit", entry=entry, stop=stop,
                 target=entry + 2 * (entry - stop), rr_target=2.0, placed_ts=0, expiry_ts=1800)


def test_keeps_trade_when_cost_is_small_share_of_risk():
    f = CostFiltered(_Fixed(_order(100.0, 80.0)))      # risk 20, cost 2 = 10%
    assert f.on_bar(0, {}) is not None
    assert f.skipped == 0


def test_skips_trade_when_cost_is_large_share_of_risk():
    f = CostFiltered(_Fixed(_order(100.0, 95.0)))      # risk 5, cost 2 = 40%
    assert f.on_bar(0, {}) is None
    assert f.skipped == 1


def test_passes_through_wait_and_name_and_new_day():
    inner = _Fixed(None)
    f = CostFiltered(inner)
    assert f.on_bar(0, {}) is None and f.skipped == 0
    f.new_day(None)
    assert inner.days == 1 and f.name == "fixed" and f.rr == 2.0
