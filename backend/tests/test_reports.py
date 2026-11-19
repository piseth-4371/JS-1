from datetime import datetime

from sqlalchemy.orm import Session

from app.core import reports, tom_forward
from app.core.news import NY
from app.db import get_engine
from app.models import PositionRow


def ts(*a):
    return int(datetime(*a, tzinfo=NY).timestamp())


EMPTY_TOM = {"trades": [], "summary": tom_forward.summary([])}
DONE = {"month": "2026-10", "entry_date": "2026-10-29", "exit_date": "2026-11-04", "status": "done", "counted": True,
        "entry": 100.0, "exit": 102.0, "points": 2.0, "net_pct": 1.94, "gross_pct": 2.0, "note": ""}


def test_previous_month_and_bounds():
    assert reports.previous_month(ts(2027, 1, 1, 0, 5)) == "2026-12"
    a, b = reports.month_bounds("2026-12")
    assert (a, b) == (ts(2026, 12, 1), ts(2027, 1, 1))


def test_monthly_message_counts_paper_trades(temp_db):
    with Session(get_engine()) as s, s.begin():
        s.add(PositionRow(order_id=1, strategy="orb", side=1, kind="market", qty=0.1, entry=1, stop=0, target=2,
                          opened_ts=ts(2026, 11, 3, 10), status="closed", closed_ts=ts(2026, 11, 3, 11),
                          exit_price=2, exit_reason="target", pnl_usd=5.0, r=2.0, risk_pts=1))
        txt = reports.monthly_message(s, "2026-11", {"trades": [DONE], "summary": tom_forward.summary([])})
    assert "November 2026" in txt
    assert "Paper account trades: 1 done · 1 won · 0 lost · total +2.00R · +5.00 virtual $" in txt
    assert "Real signals (passed strategies): none" in txt
    assert "+1.94% after costs" in txt
    assert "win rate" not in txt.lower() and "chance of winning" in txt   # only the disclaimer, no win-chance figure


def test_monthly_sent_once_and_not_on_first_run(temp_db, monkeypatch):
    monkeypatch.setattr(tom_forward, "report", lambda now: EMPTY_TOM)
    with Session(get_engine()) as s, s.begin():
        assert reports.messages(s, ts(2026, 11, 19, 12)) == []          # first run: remember only
        assert reports.messages(s, ts(2026, 11, 30, 12)) == []
        out = reports.messages(s, ts(2026, 12, 1, 0, 1))
        assert len(out) == 1 and "November 2026" in out[0]
        assert reports.messages(s, ts(2026, 12, 1, 0, 2)) == []


def test_tom_messages_sent_once_per_status(temp_db, monkeypatch):
    open_t = {**DONE, "status": "open", "exit": None, "points": None, "net_pct": None}
    monkeypatch.setattr(tom_forward, "report", lambda now: {"trades": [open_t], "summary": tom_forward.summary([])})
    with Session(get_engine()) as s, s.begin():
        first = reports.messages(s, ts(2026, 10, 29, 17), monthly=False)
        assert len(first) == 1 and "bought USTEC" in first[0]
        assert reports.messages(s, ts(2026, 10, 30, 9), monthly=False) == []
        monkeypatch.setattr(tom_forward, "report", lambda now: {"trades": [DONE], "summary": tom_forward.summary([])})
        done = reports.messages(s, ts(2026, 11, 4, 17), monthly=False)
        assert len(done) == 1 and "finished" in done[0] and "+1.94%" in done[0]
        assert reports.messages(s, ts(2026, 11, 5, 9), monthly=False) == []
