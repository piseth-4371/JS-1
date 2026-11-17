"""Paper-versus-backtest matching rules (docs/paper_vs_backtest_plan.md)."""
from types import SimpleNamespace

import pytest

from app.backtest import paper_compare as pc
from app.backtest.engine import Costs, run
from tests.test_backtest_engine import FLAT, OneShot, frame


def sig(ts=300, side=1, entry=100.0, stop=90.0, target=120.0, kind="limit", note=""):
    return pc.SignalRec(ts, side, kind, entry, stop, target, note)


def tr(ts=60, side=1, entry=100.0, exit_=120.0, reason="target", r=2.0, exit_ts=120):
    return pc.TradeRec(ts, side, entry, 90.0, 120.0, exit_ts, exit_, reason, r)


def test_identical_signals_and_trades():
    assert pc.compare_signals([sig()], [sig()]).identical == 1
    c = pc.compare_trades([tr()], [tr()])
    assert (c.identical, c.different, c.paper_only, c.backtest_only) == (1, [], [], [])


def test_tiny_float_noise_is_not_a_difference_but_a_real_gap_is():
    assert pc.compare_trades([tr(r=2.0)], [tr(r=2.0 + 1e-12)]).identical == 1
    c = pc.compare_trades([tr(exit_=120.0)], [tr(exit_=119.5, r=1.95)])
    assert c.identical == 0 and c.different[0][1] == {"exit": (120.0, 119.5), "r": (2.0, 1.95)}


def test_exit_reason_and_time_differences_are_reported():
    c = pc.compare_trades([tr(reason="stop", exit_ts=180)], [tr(reason="target", exit_ts=120)])
    assert set(c.different[0][1]) == {"reason", "exit_ts"}


def test_one_side_only_items_keep_the_paper_reason():
    c = pc.compare_signals([sig(ts=300, note="Lot below broker minimum"), sig(ts=600)], [sig(ts=600), sig(ts=900)])
    assert c.identical == 1 and [x.note for x in c.paper_only] == ["Lot below broker minimum"]
    assert [x.bar_close_ts for x in c.backtest_only] == [900]


def test_same_time_other_side_does_not_match():
    c = pc.compare_signals([sig(side=1)], [sig(side=-1)])
    assert len(c.paper_only) == 1 and len(c.backtest_only) == 1


def test_open_paper_position_differs_from_a_closed_backtest_trade():
    open_pos = SimpleNamespace(opened_ts=60, side=1, entry=100.0, stop=90.0, target=120.0, status="open",
                               closed_ts=None, exit_price=None, exit_reason=None, r=None)
    c = pc.compare_trades([pc.trade_from_position(open_pos)], [tr()])
    assert set(c.different[0][1]) == {"exit_ts", "exit", "reason", "r"}


def test_backtest_signals_and_trades_come_from_the_same_run_rules():
    mins = [(105, 106, 104, 105)] * 5 + [(105, 105, 99, 101)] + [(101, 121, 101, 120)] + [FLAT] * 8
    f = frame(mins)
    (s,) = pc.backtest_signals(OneShot(), f.a)
    assert (s.side, s.kind, s.entry, s.stop, s.target) == (1, "limit", 100.0, 90.0, 120.0)
    (t,) = run(OneShot(), f, costs=Costs(1.5, 0.5)).trades
    rec = pc.trade_from_backtest(t)
    assert rec.entry == 100.0 and rec.reason == "target" and rec.r == pytest.approx((20 - 1.5) / 10)


def test_signal_for_trade_is_the_latest_same_side_signal_before_the_fill():
    sigs = [sig(ts=300, side=1), sig(ts=600, side=-1), sig(ts=900, side=1), sig(ts=1500, side=1)]
    assert pc.signal_for_trade(tr(ts=1200, side=1), sigs).bar_close_ts == 900
    assert pc.signal_for_trade(tr(ts=700, side=-1), sigs).bar_close_ts == 600
    assert pc.signal_for_trade(tr(ts=200, side=1), sigs) is None


def test_signal_from_paper_row_uses_the_rejection_reasons():
    row = SimpleNamespace(bar_close_ts=300, action="SHORT", kind="limit", entry=100.0, stop=110.0, target=80.0,
                          risk_approved=False, risk_reasons=["Lot below broker minimum", "News"])
    s = pc.signal_from_row(row)
    assert s.side == -1 and s.note == "Lot below broker minimum; News"
