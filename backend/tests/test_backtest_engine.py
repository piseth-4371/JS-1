"""Fill rules of the backtester, with hand-made data so every number is checkable."""
import numpy as np
import pytest

from app.backtest.engine import Costs, run
from app.core.features import Frame
from app.core.strategies.base import Order, Strategy

T0 = 1_800_000_000
NO_COSTS = Costs(0, 0)


class OneShot(Strategy):
    """Emits a given order on 5m bar 0 only."""
    name = "oneshot"

    def __init__(self, **kw):
        self.kw = kw

    def on_bar(self, i, a):
        if i != 0:
            return None
        kw = dict(strategy="t", side=1, kind="limit", entry=100.0, stop=90.0, target=120.0, rr_target=2.0,
                  placed_ts=T0 + 300, expiry_ts=T0 + 300 + 1800)
        kw.update(self.kw)
        return Order(**kw)


def frame(minutes, can_hold=None, five_closes=None):
    """minutes: list of (o,h,l,c) 1-minute bars starting at T0. 5m bars are built from them."""
    n = len(minutes)
    m_o, m_h, m_l, m_c = (np.array(x, dtype=float) for x in zip(*minutes))
    m = {"ts": T0 + np.arange(n) * 60, "o": m_o, "h": m_h, "l": m_l, "c": m_c,
         "can_hold": np.array(can_hold if can_hold is not None else [True] * n),
         "ny_date": np.array(["d"] * n, dtype=object), "news": np.zeros(n, dtype=bool)}
    k = n // 5
    a = {"ts": T0 + np.arange(k) * 300, "close_ts": T0 + np.arange(k) * 300 + 300,
         "c": np.array(five_closes if five_closes else [m_c[i * 5 + 4] for i in range(k)], dtype=float),
         "ny_date": np.array([__import__("datetime").date(2026, 11, 9)] * k, dtype=object),
         "news": np.zeros(k, dtype=bool), "news_known": np.ones(k, dtype=bool)}
    return Frame(None, a, m)


FLAT = (100.0, 100.5, 99.5, 100.0)


def test_limit_fill_then_target():
    mins = [(105, 106, 104, 105)] * 5 + [(105, 105, 99, 101)] + [(101, 121, 101, 120)] + [FLAT] * 8
    res = run(OneShot(), frame(mins), costs=NO_COSTS)
    (t,) = res.trades
    assert t.entry == 100 and t.exit == 120 and t.exit_reason == "target"
    assert t.r == pytest.approx(2.0)


def test_both_stop_and_target_in_one_minute_counts_as_stop():
    mins = [(105, 106, 104, 105)] * 5 + [(100, 101, 99.5, 100)] + [(100, 125, 85, 100)] + [FLAT] * 8
    (t,) = run(OneShot(), frame(mins), costs=NO_COSTS).trades
    assert t.exit_reason == "stop" and t.r == pytest.approx(-1.0)


def test_gap_through_stop_exits_at_worse_open():
    mins = [(105, 106, 104, 105)] * 5 + [(100, 101, 99.5, 100)] + [(80, 82, 79, 81)] + [FLAT] * 8
    (t,) = run(OneShot(), frame(mins), costs=NO_COSTS).trades
    assert t.exit == 80 and t.r == pytest.approx(-2.0)


def test_limit_order_expires_unfilled():
    mins = [(105, 106, 104, 105)] * 50
    res = run(OneShot(), frame(mins), costs=NO_COSTS)
    assert res.trades == [] and res.cancelled["expired"] == 1


def test_costs_reduce_r():
    mins = [(105, 106, 104, 105)] * 5 + [(105, 105, 99, 101)] + [(101, 121, 101, 120)] + [FLAT] * 8
    (t,) = run(OneShot(), frame(mins), costs=Costs(spread=2.0, slippage=0.5)).trades
    assert t.r == pytest.approx((20 - 2.0) / 10)  # limit entry + target exit: spread only


def test_market_order_target_set_from_actual_fill():
    mins = [(105, 106, 104, 105)] * 5 + [(102, 103, 101, 102)] + [(102, 126, 101, 125)] + [FLAT] * 8
    (t,) = run(OneShot(kind="market", entry=105, target=None), frame(mins), costs=NO_COSTS).trades
    assert t.entry == 102 and t.target == pytest.approx(102 + 2 * 12)


def test_position_closed_at_session_end():
    mins = [(105, 106, 104, 105)] * 5 + [(100, 101, 99.5, 100)] + [(101, 102, 100, 101)] * 3 + [(103, 104, 102, 103)] * 6
    hold = [True] * 9 + [False] * 6
    (t,) = run(OneShot(), frame(mins, can_hold=hold), costs=NO_COSTS).trades
    assert t.exit_reason == "session_end" and t.exit == 103


def test_risk_manager_blocks_order_without_valid_stop():
    mins = [(105, 106, 104, 105)] * 15
    res = run(OneShot(stop=110.0), frame(mins), costs=NO_COSTS)  # stop above a long entry
    assert res.trades == [] and res.rejections


def test_fvg_invalidation_cancels_pending():
    mins = [(105, 106, 104, 105)] * 5 + [(103, 104, 102, 103)] * 5 + [(99, 100, 98, 99)] * 5
    # cancel if a 5m bar closes below 103.5 (before price reaches the 100 limit)
    res = run(OneShot(cancel_level=103.5), frame(mins), costs=NO_COSTS)
    assert res.trades == [] and res.cancelled["invalidated (closed beyond FVG)"] == 1
