from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.core import volatility as v
from app.core.news import NY


def day_bars(day: datetime, width: float, start_h=9, end_h=11):
    """1-minute bars around 100 with a fixed high-low width, from start_h to end_h New York time."""
    rows, t = [], day.replace(hour=start_h, minute=0)
    while t.hour < end_h:
        rows.append({"ts": int(t.timestamp()), "h": 100 + width / 2, "l": 100 - width / 2})
        t += timedelta(minutes=1)
    return rows


def frame(days: int, today_width: float, normal_width: float = 1.0):
    today = datetime(2026, 11, 18, tzinfo=NY)
    rows = []
    for k in range(days, 0, -1):
        rows += day_bars(today - timedelta(days=k), normal_width)
    rows += day_bars(today, today_width)
    return pd.DataFrame(rows), int(today.replace(hour=11).timestamp())


def test_twice_the_normal_range_is_busy():
    m1, now = frame(25, today_width=2.0)
    r = v.measure("nas100", m1, now)
    assert r.state == "ok" and r.samples == v.LOOKBACK_DAYS
    assert r.x == pytest.approx(2.0, rel=0.02) and r.level == "busy"


def test_levels():
    assert [v.level(x) for x in (0.5, 1.0, 2.0, 3.0)] == ["calm", "normal", "busy", "very wild"]


def test_stale_data_and_short_history():
    m1, now = frame(25, today_width=1.0)
    assert v.measure("gold", m1, now + 3600).state == "no recent data"
    m1, now = frame(5, today_width=1.0)
    r = v.measure("gold", m1, now)
    assert r.state == "not enough history" and r.x is None and r.samples == 5
    assert v.measure("btc", pd.DataFrame(columns=["ts", "h", "l"]), now).state == "no recent data"


def test_same_new_york_hour_across_dst_change():
    # 2026-11-01 US clocks went back: a UTC-only 24 h shift would compare 10:00 with 09:00 NY.
    m1, now = frame(25, today_width=1.0)
    end_ny = datetime.fromtimestamp(now, NY)
    before = int((end_ny - timedelta(days=20)).timestamp())
    assert datetime.fromtimestamp(before, NY).hour == end_ny.hour
