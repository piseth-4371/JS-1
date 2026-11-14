from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from app.backtest.intraday_momentum import (Day, build_days, early_close, random_direction_control, signal_side,
                                            trade_r)

NY = ZoneInfo("America/New_York")


def _day(entry=100.0, risk=10.0, closes=(101, 102, 103), lows=None, highs=None, opens=None):
    c = np.array(closes, float)
    return Day(date(2020, 1, 2), 0.01, entry, risk,
               np.array(opens if opens else c, float),
               np.array(highs if highs else c + 0.5, float),
               np.array(lows if lows else c - 0.5, float), c, len(c) - 1)


def test_early_close_days():
    assert early_close(date(2019, 7, 3)) and early_close(date(2019, 12, 24))
    assert early_close(date(2019, 11, 29))          # day after Thanksgiving 2019
    assert not early_close(date(2019, 11, 28)) and not early_close(date(2019, 7, 5))


def test_trade_r_exit_at_close_and_cost():
    x = _day()
    assert abs(trade_r(x, 1, cost_pts=2.0) - (3 - 2) / 10) < 1e-9
    assert abs(trade_r(x, -1, cost_pts=2.0) - (-3 - 2) / 10) < 1e-9


def test_trade_r_stop_gap_fills_at_open():
    x = _day(closes=(99, 85, 80), opens=[99, 85, 80], lows=[98.5, 84, 79], highs=[99.5, 86, 81])
    assert abs(trade_r(x, 1, cost_pts=0.0) - (85 - 100) / 10) < 1e-9    # stop at 90, bar opened at 85


def test_signal_and_control_reproducible():
    days = [_day(), _day(closes=(98, 97, 96))]
    assert signal_side(days[0]) == 1
    a, b = random_direction_control(days, runs=20, seed=3), random_direction_control(days, runs=20, seed=3)
    assert np.allclose(a, b)


def _bars(day, minutes_closes):
    rows = []
    for mod, c in minutes_closes:
        t = datetime(day.year, day.month, day.day, mod // 60, mod % 60, tzinfo=NY)
        rows.append((int(t.timestamp()), c, c + 1, c - 1, c))
    return pd.DataFrame(rows, columns=["ts", "o", "h", "l", "c"])


def test_build_days_uses_previous_close_and_10am():
    d1, d2 = date(2020, 1, 2), date(2020, 1, 3)
    prev = _bars(d1, [(959, 100.0)])
    today = _bars(d2, [(599, 101.0)] + [(m, 101.0) for m in range(860, 960)])
    days = build_days(pd.concat([prev, today], ignore_index=True))
    assert len(days) == 1 and days[0].day == d2
    assert abs(days[0].r1 - 0.01) < 1e-12 and days[0].entry == 101.0 and days[0].risk > 0
