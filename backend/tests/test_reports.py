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
    assert "Paper account trades: 1 done · 1 won · 0 lost · total +2.00R · worst drop 0.00R · +5.00 virtual $" in txt
    assert "Real signals (passed strategies): none" in txt
    assert "+1.94% after costs" in txt
    assert "win rate" not in txt.lower() and "chance of winning" in txt   # only the disclaimer, no win-chance figure


def test_drawdown_math():
    d = reports.drawdown(1000, [10, -30, 5, -20, 50])       # 1010 high, then 965 low -> 45 down, then 1015
    assert d["max"] == 45 and round(d["max_pct"], 3) == round(45 / 1010 * 100, 3)
    assert d["now"] == 0 and d["now_pct"] == 0
    assert reports.drawdown(0.0, [1, 1])["max"] == 0                            # never fell
    c = reports.drawdown(100, [10, -10], compound=True)                         # 110 -> 99
    assert round(c["max_pct"], 6) == 10 and round(c["now_pct"], 6) == 10
    assert reports._neg(0.0) == "0.00" and reports._neg(1.234) == "-1.23"


def test_monthly_message_shows_drawdowns(temp_db, monkeypatch):
    from app.core import drawdown_check
    monkeypatch.setattr(drawdown_check, "load_backtest", lambda: {"orb": [1.0, -1.0, -1.0, 2.0] * 10})
    def pos(i, day, pnl, r):
        return PositionRow(order_id=i, strategy="orb", side=1, kind="market", qty=0.1, entry=1, stop=0, target=2,
                           opened_ts=ts(2026, 11, day, 10), status="closed", closed_ts=ts(2026, 11, day, 11),
                           exit_price=2, exit_reason="x", pnl_usd=pnl, r=r, risk_pts=1)
    with Session(get_engine()) as s, s.begin():
        s.add_all([pos(1, 3, 20.0, 2.0), pos(2, 4, -10.0, -1.0), pos(3, 5, -5.0, -0.5), pos(4, 6, 8.0, 0.8)])
        s.flush()
        tom = {"trades": [DONE, {**DONE, "month": "2026-09", "exit_date": "2026-10-05", "net_pct": 2.33}],
               "summary": tom_forward.summary([])}
        txt = reports.monthly_message(s, "2026-11", tom)
    # 1000 -> 1020 high -> 1005 low: 15 $ = 1.5% (default $1,000 paper balance); now 7 $ below the high
    assert "Paper account trades: 4 done · 2 won · 2 lost · total +1.30R · worst drop -1.50R" in txt
    assert "Paper account drawdown: this month -15.00 virtual $ (-1.5%) · biggest ever -15.00 (-1.5%) · now 0.7% below its high" in txt
    assert "Turn-of-month drawdown: biggest 0.00% · now 0.00% below its high" in txt      # two gains in a row
    assert "Is this drop normal? orb: now 0.70R below its high (biggest 1.50R, backtest biggest 2.00R). Normal" in txt
    assert "Drawdown = the biggest fall from a previous high." in txt


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


def test_monthly_message_process_line(temp_db):
    from app.core import state
    from app.models import EventRow, SignalRow
    with Session(get_engine()) as s, s.begin():
        s.add(PositionRow(order_id=1, strategy="orb", side=1, kind="market", qty=0.1, entry=1, stop=0, target=2,
                          opened_ts=ts(2026, 11, 3, 10), status="closed", closed_ts=ts(2026, 11, 3, 11),
                          exit_price=2, exit_reason="target", pnl_usd=5.0, r=2.0, risk_pts=1))
        s.add(PositionRow(order_id=2, strategy="orb", side=1, kind="market", qty=0.1, entry=1, stop=0, target=2,
                          opened_ts=ts(2026, 11, 4, 10), status="closed", closed_ts=ts(2026, 11, 4, 11),
                          exit_price=1, exit_reason="kill_switch", pnl_usd=0.0, r=0.0, risk_pts=1))
        state.log(s, "WARN", "manual", "KILL SWITCH activated (by user). Reason: felt nervous", ts(2026, 11, 4, 11))
        state.log(s, "INFO", "manual", "Kill switch reset (auto-trading stays OFF) (by user). Reason: calm",
                  ts(2026, 11, 5, 9))
        state.log(s, "INFO", "manual", "KILL SWITCH activated (by user). Reason: old", ts(2026, 10, 30, 9))  # other month
        s.add(SignalRow(strategy="orb", bar_close_ts=ts(2026, 11, 6, 10), created_ts=0, action="LONG", data_source="x",
                        data_ts=0, risk_approved=False, risk_reasons=["busy"]))
        s.flush()
        txt = reports.monthly_message(s, "2026-11", EMPTY_TOM)
    assert ("Process: paper trades ended by the plan 1 of 2 · manual actions 2 (KILL 1, reset 1, other 0) · "
            "risk manager said no to 1 paper signals") in txt
    assert "11-04 11:00 KILL SWITCH activated (by user). Reason: felt nervous" in txt
    assert "Reason: old" not in txt
