from datetime import date, datetime

import pandas as pd
import pytest

from app.core import tom_forward as t
from app.core.news import NY


def test_nyse_holidays_known_years():
    assert t.nyse_holidays(2026) == {date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3),
                                     date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7),
                                     date(2026, 11, 26), date(2026, 12, 25)}
    assert date(2027, 12, 31) not in t.nyse_holidays(2027)        # New Year 2028 is a Saturday: not moved back
    assert date(2023, 1, 2) in t.nyse_holidays(2023)              # Sunday New Year observed Monday


def test_windows_skip_weekends_and_holidays():
    assert t.window(2026, 10) == (date(2026, 10, 29), date(2026, 11, 4))
    assert t.window(2026, 8) == (date(2026, 8, 28), date(2026, 9, 3))        # Labor Day Sep 7 is after day 3
    assert t.window(2026, 12) == (date(2026, 12, 30), date(2027, 1, 6))      # Jan 1 holiday
    assert t.window(2027, 6) == (date(2027, 6, 29), date(2027, 7, 6))        # July 5 observed holiday


def bars(day_closes):
    rows = []
    for d, c in day_closes.items():
        for hh, mm, px in ((15, 54, c - 5), (15, 59, c)):
            rows.append({"ts": int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).timestamp()), "c": px})
    return pd.DataFrame(rows)


def test_daily_close_uses_the_last_bar_before_four():
    closes = t.daily_closes(bars({date(2026, 10, 29): 100.0}))
    assert closes == {date(2026, 10, 29): 100.0}


def test_trade_states_and_costs():
    closes = {date(2026, 10, 29): 100.0, date(2026, 11, 4): 102.0}
    tr = t.build(closes, today=date(2026, 12, 29), first_month=(2026, 10))
    done, void, nxt = tr[0], tr[1], tr[2]
    assert done.status == "done" and done.points == 2.0
    assert done.net_pct == pytest.approx((0.02 - 0.0002 - 0.07 * 6 / 365) * 100, abs=1e-3)
    assert void.status == "void" and "entry day" in void.note                 # Nov 27 had no close
    assert nxt.status == "scheduled" and nxt.entry_date == "2026-12-30"
    s = t.summary(tr)
    assert (s["trades"], s["wins"], s["void"], s["verdict"]) == (1, 1, 1, "collecting — no verdict")


def test_open_trade_and_forward_start():
    tr = t.build({date(2025, 10, 30): 100.0, date(2026, 10, 29): 100.0}, today=date(2026, 11, 2), first_month=(2025, 10))
    assert tr[0].counted is False                    # before 2025-12-01: shown, not counted
    assert tr[-2].status == "open" and tr[-2].counted
