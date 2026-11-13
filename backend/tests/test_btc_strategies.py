"""BTC weekend versions of the NAS100 strategies: windows, UTC-day levels, UTC opening range."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from app.core.features import build_frame
from app.core.markets import BTCUSD, NAS100
from app.core.strategies import ALL
from app.core.strategies.orb import BTCWeekendORB

BTC_NAMES = ["btc_weekend_trend_fvg", "btc_weekend_sweep_mss_fvg", "btc_weekend_orb",
             "btc_weekend_vwap_reversion", "btc_weekend_silver_bullet"]


def utc(y, mo, d, h=0, m=0):
    return int(datetime(y, mo, d, h, m, tzinfo=timezone.utc).timestamp())


def test_every_btc_strategy_belongs_to_the_btc_book_only():
    for n in BTC_NAMES:
        assert n in ALL and BTCUSD.owns(n) and not NAS100.owns(n)


def test_btc_versions_enter_on_weekends_only():
    # weekday / NY minute-of-day of the bar START (bar closes 5 minutes later)
    a = {"weekday": np.array([3, 4, 5, 6]), "mod": np.array([600, 17 * 60, 600, 15 * 60 + 25]),
         "lmod": np.zeros(4), "umod": np.zeros(4)}
    for n in ("btc_weekend_sweep_mss_fvg", "btc_weekend_vwap_reversion"):
        s = ALL[n]()
        assert [s.in_window(i, a) for i in range(4)] == [False, True, True, True], n
    sb = ALL["btc_weekend_silver_bullet"]()
    assert [sb.allowed(i, a) for i in range(4)] == [False, True, True, True]


def test_prior_utc_day_levels_and_clock():
    # Two full UTC days of 1-minute bars: day 1 trades 100-110, day 2 trades 200-210.
    t0 = utc(2026, 11, 14)                       # Saturday 00:00 UTC
    ts = np.arange(t0, t0 + 2 * 86400, 60)
    day2 = ts >= t0 + 86400
    base = np.where(day2, 200.0, 100.0)
    m1 = pd.DataFrame({"ts": ts, "o": base, "h": base + 10, "l": base, "c": base + 5, "v": 1.0})
    a = build_frame(m1, hold_mask=BTCUSD.hold_mask).a
    i1 = int(np.searchsorted(a["ts"], t0 + 3600))
    i2 = int(np.searchsorted(a["ts"], t0 + 86400 + 3600))
    assert np.isnan(a["pudh"][i1])                           # no earlier day yet: unknown, not invented
    assert (a["pudh"][i2], a["pudl"][i2]) == (110.0, 100.0)  # only the COMPLETED prior UTC day
    assert a["umod"][i2] == 60


def test_btc_orb_uses_the_utc_daily_open():
    s = BTCWeekendORB()
    day = utc(2026, 11, 14) // 86400              # Saturday (inside the weekend window)
    n = 8
    a = {"umod": np.array([0, 5, 10, 15, 20, 25, 30, 35]), "uday": np.full(n, day),
         "weekday": np.full(n, 5), "mod": np.full(n, 600),
         "h": np.array([101, 102, 101, 101, 101, 101, 106, 101.0]),
         "l": np.array([99, 98, 99, 99, 99, 99, 103, 99.0]),
         "c": np.array([100, 100, 100, 100, 100, 100, 105, 100.0]),
         "atr": np.full(n, 3.0), "close_ts": np.arange(n) * 300 + day * 86400 + 300}
    orders = [s.on_bar(i, a) for i in range(n)]
    hits = [(i, o) for i, o in enumerate(orders) if o]
    assert len(hits) == 1                         # one attempt per UTC day
    i, o = hits[0]
    assert i == 6 and o.side == 1 and o.stop == 100.0   # breakout above 102, stop at the range midpoint
