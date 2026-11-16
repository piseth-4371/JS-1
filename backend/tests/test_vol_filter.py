from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from app.backtest import vol_filter as vf
from app.core.strategies.base import Order, Strategy

NY = ZoneInfo("America/New_York")


def _closes(values, start=date(2020, 1, 1)):
    days, d = [], start
    while len(days) < len(values):
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return pd.Series(values, index=days, dtype=float)


def test_daily_close_is_last_bar_before_16_ny():
    t = lambda h, m: int(datetime(2024, 6, 11, h, m, tzinfo=NY).timestamp())
    m1 = pd.DataFrame({"ts": [t(9, 30), t(15, 59), t(16, 5)], "c": [1.0, 2.0, 3.0]})
    assert vf.daily_closes(m1).to_dict() == {date(2024, 6, 11): 2.0}


def test_no_look_ahead_future_prices_do_not_change_past_percentiles():
    rng = np.random.default_rng(0)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400)))
    full = _closes(prices)
    cut = full.iloc[:300]
    day = full.index[299]
    a = vf.percentiles(full, [day])[day]
    b = vf.percentiles(cut, [day])[day]
    assert a is not None and a == b
    # a huge crash ON the trade date itself must not change that date's reading
    crashed = full.copy()
    crashed.iloc[299] = crashed.iloc[298] * 0.5
    assert vf.percentiles(crashed, [day])[day] == a


def test_not_enough_history_at_start():
    s = _closes(100 + np.arange(100.0))
    assert vf.percentiles(s, [s.index[50]])[s.index[50]] is None
    assert vf.regime(None) == "no_history"


def test_calm_and_wild_regimes():
    rng = np.random.default_rng(1)
    calm_then_wild = np.r_[rng.normal(0, 0.01, 300), rng.normal(0, 0.04, 30)]
    s = _closes(100 * np.exp(np.cumsum(calm_then_wild)))
    p = vf.percentiles(s, [s.index[-1]])[s.index[-1]]
    assert p > 80 and vf.regime(p) == "wild"
    wild_then_calm = np.r_[rng.normal(0, 0.03, 300), rng.normal(0, 0.003, 30)]
    s = _closes(100 * np.exp(np.cumsum(wild_then_calm)))
    p = vf.percentiles(s, [s.index[-1]])[s.index[-1]]
    assert p < 20 and vf.regime(p) == "calm"
    assert vf.regime(20.0) == vf.regime(80.0) == "normal"


class _Always(Strategy):
    name, rr = "always", 2.0

    def new_day(self, day):
        pass

    def on_bar(self, i, a):
        return Order("always", 1, "market", 100.0, 90.0, None, 2.0, 0, 0)


def test_wrapper_skips_non_normal_days_and_counts_them():
    d1, d2, d3 = date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)
    w = vf.VolFiltered(_Always(), {d1: 50.0, d2: 10.0, d3: None})
    a = {"ny_date": [d1, d2, d3]}
    assert w.on_bar(0, a) is not None
    assert w.on_bar(1, a) is None and w.on_bar(2, a) is None
    assert w.skipped == {"calm": 1, "wild": 0, "no_history": 1}


def test_random_skip_control():
    base = [1.0] * 50 + [-1.0] * 50
    assert vf.random_skip_beaten(base, 1.0, 50) == pytest.approx(1.0)   # keeping only winners beats random skips
    assert vf.random_skip_beaten(base, -1.0, 50) == 0.0
    assert vf.random_skip_beaten(base, 0.5, 0) == 0.0
