"""Buy-the-drop rule mechanics on made-up prices (no real data)."""
import numpy as np
import pandas as pd

from app.backtest import buy_the_drop as b


def test_signal_needs_strictly_lowest_of_last_n():
    p = np.array([10, 9, 8, 7.0])
    assert b.signals(p, 3).tolist() == [False, False, True, True]
    p = np.array([10, 9, 9.0])            # equal to an earlier close is not "strictly lower"
    assert b.signals(p, 3).tolist() == [False, False, False]
    p = np.array([5, 9, 8, 7.0])          # 7 is below 9 and 8 (last 2), even though 5 is lower further back
    assert b.signals(p, 3).tolist() == [False, False, False, True]


def test_no_look_ahead():
    p = np.array([10, 9, 8, 7, 100, 1.0])
    s1 = b.signals(p, 3)
    p2 = p.copy()
    p2[5] = 1000.0                        # changing a later price never changes an earlier signal
    assert b.signals(p2, 3)[:5].tolist() == s1[:5].tolist()


def test_one_position_and_exit_day_can_reenter():
    p = np.array([10, 9, 8, 7, 6, 5, 4, 3.0])     # falls every day: every day from index 2 signals
    assert b.trades(p, lookback=3, hold=2) == [(2, 4), (4, 6)]   # (6, 8) has no exit day -> not taken


def test_period_drops_trades_crossing_the_end():
    dates = pd.DatetimeIndex(["1999-12-28", "1999-12-29", "1999-12-30", "2000-01-03"])
    assert b.in_period([(0, 1), (2, 3)], dates, (1971, 1999)) == [(0, 1)]
    assert b.in_period([(0, 1), (2, 3)], dates, (2000, 2024)) == []


def test_costs_match_turn_of_month():
    from app.backtest import turn_of_month as t
    assert (b.SPREAD, b.FINANCING, b.STRESS) == (t.SPREAD, t.FINANCING, t.STRESS)
    assert (b.LOOKBACK, b.HOLD) == (10, 5) and b.NEARBY == {"lookback": (7, 13), "hold": (4, 6)}


def test_verdict_rules():
    def per(net, ok=True):
        return b.Period("x", 50 if ok else 5, net, net, 0.001 if ok else -0.1, 0.01, net, -1.0, 1.0, 0.6, -0.1, 0)
    good = per(0.005)
    assert b.verdict(good, good, (True, True), (True, True)) == b.PASS
    assert b.verdict(good, per(-0.001), (True, True), (True, True)) == b.NEGATIVE
    assert b.verdict(good, good, (True, False), (True, True)) == b.INCONCLUSIVE
    assert b.verdict(good, good, (True, True), (False, True)) == b.INCONCLUSIVE
    assert b.verdict(good, per(0.005, ok=False), (True, True), (True, True)) == b.INCONCLUSIVE
