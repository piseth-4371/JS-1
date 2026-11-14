from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.backtest.daily_trend import DTrade, random_control, run_daily


def make_days(closes):
    idx = [date(2019, 1, 1) + timedelta(days=i) for i in range(len(closes))]
    c = np.array(closes, float)
    d = pd.DataFrame({"o": c, "h": c + 1, "l": c - 1, "c": c}, index=pd.Index(idx, name="day"))
    d["atr20"] = 2.0
    d["sma100"] = 100.0
    d["hh55"] = d["h"].rolling(3).max().shift(1)
    d["ll55"] = d["l"].rolling(3).min().shift(1)
    d["hh20"] = d["h"].rolling(2).max().shift(1)
    d["ll20"] = d["l"].rolling(2).min().shift(1)
    return d


def test_r_includes_cost_and_financing():
    t = DTrade("x", 1, date(2020, 1, 1), date(2020, 1, 11), 1000.0, 1020.0, 10.0, 10, 7, "signal")
    assert abs(t.r(cost_pts=2.0, fin_rate=0.0) - 1.8) < 1e-9
    assert t.r(cost_pts=2.0, fin_rate=0.05) < 1.8          # financing makes it worse


def test_sma_long_enters_next_open_and_exits_on_signal():
    closes = [99, 101, 103, 105, 99, 98, 97]
    d = make_days(closes)
    tr = run_daily(d, "sma100_long")
    assert tr[0].entry_day == d.index[2]                     # signal day 1 close -> fill day 2 open
    assert tr[0].entry == 103 and tr[0].side == 1
    assert tr[0].reason in ("stop", "signal")


def test_stop_gap_fills_at_open_not_stop():
    closes = [99, 101, 102, 80, 80, 80]                      # gap far below the 2xATR stop
    d = make_days(closes)
    tr = run_daily(d, "sma100_long")
    assert tr[0].reason == "stop" and tr[0].exit == 80        # worse than the stop price, as in reality


def test_random_control_is_reproducible():
    d = make_days(list(range(100, 160)))
    tr = run_daily(d, "sma100_long")
    a = random_control(d, tr, runs=5, seed=1)
    b = random_control(d, tr, runs=5, seed=1)
    assert np.allclose(a, b)
