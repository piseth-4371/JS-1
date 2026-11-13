"""High-impact news blackout: calendar integrity, window maths, engine + backtester behaviour."""
import csv
from collections import Counter
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backtest.engine import run
from app.core import news, state
from app.core.engine import TradingEngine
from app.core.market_data import Bar
from app.db import get_engine
from app.models import OrderRow, SignalRow
from app.repository import save_bars
from tests.test_backtest_engine import FLAT, T0, OneShot, frame
from tests.test_paper_trading import SRC, SYM, flat_bars, setup  # noqa: F401

NY = ZoneInfo("America/New_York")


def ny(y, mo, d, h, m):
    return int(datetime(y, mo, d, h, m, tzinfo=NY).timestamp())


# ---------------------------------------------------------------- calendar file
def test_calendar_file_is_complete_and_sourced():
    with news.CALENDAR.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    official = ("https://www.bls.gov/", "https://www.federalreserve.gov/", "https://www.bea.gov/",
                "https://apps.bea.gov/")
    assert all(r["source"].startswith(official) for r in rows)
    assert {r["event"] for r in rows} == set(news.EVENTS)
    assert len({(r["date"], r["event"]) for r in rows}) == len(rows)          # no duplicates
    per_year = Counter((r["date"][:4], r["event"]) for r in rows)
    for y in range(2019, 2027):
        assert per_year[(str(y), "FOMC")] >= 8, y
        expected_bls = 11 if y == 2025 else 12           # Oct 2025 reports never published (shutdown)
        assert per_year[(str(y), "CPI")] == expected_bls and per_year[(str(y), "NFP")] == expected_bls, y
        # BEA: ~12 a year; shutdowns (Dec 2018-Jan 2019, Oct-Nov 2025) merged or moved some releases
        assert 10 <= per_year[(str(y), "GDP")] <= 13 and 11 <= per_year[(str(y), "PCE")] <= 13, y


def test_bea_events_and_10am_exceptions():
    labels = {e.label for e in news.load_events()}
    assert "GDP 2024-01-25 08:30 ET" in labels                      # Q4 2023 advance estimate
    assert "PCE 2019-03-29 08:30 ET" in labels                      # shutdown catch-up release
    assert "PCE 2024-11-27 10:00 ET" in labels and "PCE 2026-01-22 10:00 ET" in labels
    assert "GDP 2026-11-25 08:30 ET" in labels and "PCE 2026-12-23 08:30 ET" in labels   # scheduled
    # a 10:00 release blocks a 09:45 entry; the 08:30 window has ended by 09:01
    assert news.entry_block_reason(ny(2024, 11, 27, 9, 45)).startswith("High-impact news blackout: PCE")
    assert news.blackout_event(ny(2024, 1, 25, 9, 1)) is None


def test_known_events_and_times():
    labels = {e.label for e in news.load_events()}
    assert "FOMC 2020-03-03 10:00 ET" in labels and "FOMC 2020-03-15 17:00 ET" in labels   # emergency cuts
    assert "CPI 2024-05-15 08:30 ET" in labels and "NFP 2025-11-20 08:30 ET" in labels
    cpi = next(e for e in news.load_events() if e.label == "CPI 2024-03-12 08:30 ET")
    assert cpi.ts == int(datetime(2024, 3, 12, 12, 30, tzinfo=ZoneInfo("UTC")).timestamp())   # EDT = UTC-4


# ---------------------------------------------------------------- window maths
def test_blackout_is_30_minutes_each_side():
    cpi = ny(2024, 5, 15, 8, 30)
    assert news.blackout_event(cpi - 1800) is not None and news.blackout_event(cpi + 1800) is not None
    assert news.blackout_event(cpi - 1801) is None and news.blackout_event(cpi + 1801) is None
    ts = np.array([cpi - 1801, cpi - 1800, cpi, cpi + 1800, cpi + 1801])
    assert news.blackout_mask(ts).tolist() == [False, True, True, True, False]


def test_reasons_inside_outside_and_beyond_the_calendar():
    assert "CPI 2024-05-15 08:30 ET" in news.entry_block_reason(ny(2024, 5, 15, 8, 45))
    assert news.entry_block_reason(ny(2024, 5, 15, 10, 0)) is None
    assert "does not cover" in news.entry_block_reason(ny(2027, 1, 5, 10, 0))


# ---------------------------------------------------------------- backtester
def test_backtest_skips_signals_in_a_blackout_and_without_calendar():
    f = frame([FLAT] * 30)
    f.a["news"][0] = True
    res = run(OneShot(), f)
    assert res.trades == [] and res.rejections["High-impact news blackout"] == 1
    f = frame([FLAT] * 30)
    f.a["news_known"][0] = False
    res = run(OneShot(), f)
    assert res.trades == [] and res.rejections["No news calendar for this date"] == 1


def test_backtest_cancels_a_pending_order_when_news_starts():
    above = (105, 106, 104, 105)                                 # price above the 100 buy limit
    mins = [above] * 6 + [(105, 105, 99, 101)] + [FLAT] * 20     # minute 6 would fill the 100 limit
    f = frame(mins)
    f.m1["news"][6:] = True                                      # blackout starts at minute 6
    res = run(OneShot(), f)
    assert res.trades == [] and res.cancelled["news blackout"] == 1


# ---------------------------------------------------------------- live engine
def test_engine_rejects_a_signal_during_cpi(temp_db, monkeypatch):
    from app.core.strategies import ALL
    from tests.test_paper_trading import AlwaysLong
    monkeypatch.setitem(ALL, "always_long", AlwaysLong)
    day = ny(2026, 11, 10, 7, 0)                                 # CPI 2026-11-10 08:30 ET
    save_bars(flat_bars(day, 100))                               # 07:00-08:39
    with Session(get_engine()) as s, s.begin():
        state.put(s, "active_strategy", "always_long")
        state.put(s, "auto_trading", True)
    res = TradingEngine(SRC, SYM, 10_000.0).cycle(ny(2026, 11, 10, 8, 40) + 5)
    assert res.status == "REJECTED" and "High-impact news blackout: CPI 2026-11-10 08:30 ET" in res.detail
    with Session(get_engine()) as s:
        assert s.scalars(select(OrderRow)).all() == []
        sig = s.scalars(select(SignalRow)).one()
        assert sig.risk_approved is False and sig.risk_reasons[0].startswith("High-impact news blackout")


def test_broker_cancels_pending_order_when_news_window_opens(setup):
    # setup: an order is placed at 10:00 on 2026-11-10; pretend an event sits at 10:20 by checking the broker path
    eng = TradingEngine(SRC, SYM, 10_000.0)
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    assert eng.cycle(setup).status == "ORDER"
    real = news.blackout_event
    news.blackout_event = lambda ts: news.Event(ts, "TEST", "test") if ts >= ny(2026, 11, 10, 10, 0) else real(ts)
    try:
        save_bars([Bar(SRC, SYM, "M1", ny(2026, 11, 10, 10, 0), 28000, 28001, 27990, 27998, 10)])   # would fill
        eng.cycle(ny(2026, 11, 10, 10, 1) + 5)
    finally:
        news.blackout_event = real
    with Session(get_engine()) as s:
        o = s.scalars(select(OrderRow)).one()
        assert o.status == "cancelled" and o.status_reason.startswith("news blackout")
