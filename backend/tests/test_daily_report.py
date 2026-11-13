from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.daily_report import build
from app.db import get_engine
from app.models import EventRow, OrderRow, PositionRow, SignalRow

NY = ZoneInfo("America/New_York")


def ny(h, m, d=date(2026, 3, 11)):
    return int(datetime(d.year, d.month, d.day, h, m, tzinfo=NY).timestamp())


def test_report_lists_facts_of_that_day_only(temp_db):
    with Session(get_engine()) as s, s.begin():
        s.add(SignalRow(strategy="orb", bar_close_ts=ny(9, 50), created_ts=ny(9, 50), action="WAIT",
                        data_source="test", data_ts=ny(9, 49)))
        s.add(SignalRow(strategy="orb", bar_close_ts=ny(10, 0), created_ts=ny(10, 0), action="LONG", kind="stop",
                        entry=100, stop=90, target=120, data_source="test", data_ts=ny(9, 59),
                        risk_approved=False, risk_reasons=["max trades reached"]))
        o = OrderRow(client_order_id="o1", strategy="orb", side=1, kind="limit", qty=1, entry=100, stop=90,
                     target=120, rr_target=2, created_ts=ny(10, 5), active_from_ts=ny(10, 5),
                     expiry_ts=ny(10, 35), status="filled")
        old = OrderRow(client_order_id="o0", strategy="orb", side=1, kind="limit", qty=1, entry=100, stop=90,
                       target=120, rr_target=2, created_ts=ny(10, 5, date(2026, 3, 10)),
                       active_from_ts=0, expiry_ts=0, status="filled")
        s.add_all([o, old])
        s.flush()
        # earlier day: +10 USD (counts in starting equity, not in the day)
        s.add(PositionRow(order_id=old.id, strategy="orb", side=1, kind="limit", qty=1, entry=100, stop=90,
                          target=120, opened_ts=ny(10, 6, date(2026, 3, 10)), status="closed",
                          closed_ts=ny(11, 0, date(2026, 3, 10)), exit_price=110, exit_reason="manual",
                          pnl_usd=10, r=1.0, risk_pts=10))
        s.add(PositionRow(order_id=o.id, strategy="orb", side=1, kind="limit", qty=1, entry=100, stop=90,
                          target=120, opened_ts=ny(10, 6), status="closed", closed_ts=ny(11, 0),
                          exit_price=90, exit_reason="stop", pnl_usd=-5, r=-1.0, risk_pts=10))
        s.add(EventRow(ts=ny(12, 0), level="ERROR", type="data", message="feed stale"))
        s.add(EventRow(ts=ny(12, 1), level="INFO", type="cycle", message="ok"))
    with Session(get_engine()) as s:
        text = build(s, date(2026, 3, 11), 1000.0)
    assert "Equity 1,010.00 → 1,005.00 USD (day -5.00" in text
    assert "orb: LONG × 1" in text and "orb: WAIT × 1" in text
    assert "REJECTED: max trades reached" in text
    assert "o1:" in text and "o0:" not in text
    assert "-1.00R -5.00 USD" in text
    assert "feed stale" in text and "cycle: ok" not in text


def test_report_shows_news_event(temp_db):
    with Session(get_engine()) as s:
        text = build(s, date(2026, 11, 10), 1000.0)   # CPI day in the sourced calendar
    assert "- CPI 2026-11-10 08:30 ET (±30 min blackout) — https://www.bls.gov/" in text
    assert "none recorded" in text
