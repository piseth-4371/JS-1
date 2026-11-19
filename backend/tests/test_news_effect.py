from datetime import date, datetime

import numpy as np
import pytest

from app.backtest import news_effect as ne
from app.core.news import NY, Event


def bars(start, n, price=100.0, spikes=()):
    ts = np.arange(start, start + n * 60, 60)
    c = np.full(n, price)
    h, lo = c + 0.1, c - 0.1
    for s, size in spikes:
        k = (s - start) // 60
        h[k:k + 30] += size
    return ne.Bars(ts, h, lo, c)


def test_window_range_and_move_in_percent():
    start = 1_800_000_000
    b = bars(start - 3600, 7200)
    rng, move = ne.window(b, start)
    assert rng == pytest.approx(0.2)          # 0.2 / 100 * 100
    assert move == pytest.approx(0.0)


def test_window_needs_bars_and_a_recent_before_price():
    start = 1_800_000_000
    assert ne.window(bars(start, 60), start) is None                 # no bar before the release
    assert ne.window(bars(start - 3600, 70), start) is None          # only 10 bars in the window


def test_controls_skip_event_days_and_weekends_and_keep_clock_time():
    ev = int(datetime(2023, 3, 14, 8, 30, tzinfo=NY).timestamp())    # Tuesday
    days = {date(2023, 3, 10), date(2023, 3, 15)}
    c = ne.control_starts(ev, days, n_each_side=3)
    got = [datetime.fromtimestamp(t, NY) for t in c]
    assert [d.date().isoformat() for d in got] == ["2023-03-13", "2023-03-09", "2023-03-08",
                                                   "2023-03-16", "2023-03-17", "2023-03-20"]
    assert all((d.hour, d.minute) == (8, 30) for d in got)


def test_effect_is_news_range_over_normal_range():
    ev = int(datetime(2023, 3, 14, 8, 30, tzinfo=NY).timestamp())
    first = ev - 30 * 86400
    b = bars(first, 60 * 24 * 60, spikes=[(ev, 0.6)])                 # +0.6 high on the news window only
    ms, skipped = ne.measure(b, [Event(ev, "CPI", "x")], {date(2023, 3, 14)})
    assert skipped == 0 and len(ms) == 1
    s = ne.summarize(ms, skipped)
    assert s["news_range_pct"] == pytest.approx(0.8)
    assert s["normal_range_pct"] == pytest.approx(0.2)
    assert s["effect_x"] == pytest.approx(4.0)
    assert s["share_over_2x"] == 1.0
