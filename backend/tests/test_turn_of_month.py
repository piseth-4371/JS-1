import numpy as np
import pandas as pd
import pytest

from app.backtest import turn_of_month as t


def series(start="2000-01-03", end="2003-12-31", daily=None):
    dates = pd.bdate_range(start, end)
    rets = np.zeros(len(dates)) if daily is None else daily(dates)
    return pd.Series(100 * np.cumprod(1 + rets), index=dates)


def test_window_is_second_to_last_day_to_third_day():
    s = series("2001-01-01", "2001-03-31")
    w = t.windows(s.index)
    assert [(s.index[a].date().isoformat(), s.index[b].date().isoformat()) for a, b in w] == [
        ("2001-01-30", "2001-02-05"), ("2001-02-27", "2001-03-05")]   # March -> April missing: skipped


def test_costs_spread_and_nights():
    s = series("2001-01-01", "2001-02-28")
    (a, b), = t.windows(s.index)[:1]
    net = t.net_return(s.to_numpy(), s.index, np.array([a]), np.array([b]))
    nights = (s.index[b] - s.index[a]).days
    assert nights == 6
    assert net[0] == pytest.approx(-(0.0002 + 0.07 * 6 / 365))
    stress = t.net_return(s.to_numpy(), s.index, np.array([a]), np.array([b]), 2.0)
    assert stress[0] == pytest.approx(2 * net[0])


def tom_effect(size):
    def daily(dates):
        r = np.full(len(dates), -0.0001)
        months = dates.year * 12 + dates.month
        for i in range(1, len(dates) - 3):
            # days i+1..i+4 are the last day of a month and the first 3 of the next when months change at i+2
            if months[i + 2] != months[i + 1]:
                r[i + 1:i + 5] = size
        return r + np.where(np.arange(len(dates)) % 2, 0.001, -0.001)
    return daily


def test_a_real_effect_passes_and_beats_random_timing():
    s = series("1990-01-01", "2010-12-31", tom_effect(0.004))
    dev = t.evaluate(s, (1990, 1999), "dev", runs=500)
    val = t.evaluate(s, (2000, 2010), "val", runs=500)
    assert dev.n >= 100 and dev.net_avg > dev.random_p95
    assert dev.tom_daily > dev.all_daily
    assert t.verdict(dev, val) == t.PASS


def test_no_effect_is_negative_after_costs():
    s = series("1990-01-01", "2010-12-31", tom_effect(-0.0001))
    dev = t.evaluate(s, (1990, 1999), "dev", runs=500)
    val = t.evaluate(s, (2000, 2010), "val", runs=500)
    assert dev.net_avg < 0
    assert t.verdict(dev, val) == t.NEGATIVE
