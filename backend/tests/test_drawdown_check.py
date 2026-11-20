from app.core import drawdown_check as dc
from app.models import PositionRow

BT = [1, -1, -1, 2, -1, -1, -1, 3] * 5          # 40 trades with regular drops of 1-3R


def test_underwater():
    assert dc.underwater([1, -1, -2, 3, 1]) == [0, 1, 3, 0, 0]


def test_normal_drop():
    c = dc.compare([1, -1], BT)
    assert c["now_r"] == 1 and c["level"] == "normal" and c["share"] >= 0.2


def test_rare_and_deeper():
    assert dc.compare([-3], BT)["level"] in ("unusual", "rare")
    c = dc.compare([-10], BT)
    assert c["level"] == "deeper" and c["share"] == 0 and "bug" in c["text"]


def test_at_high_no_trades_and_thin_backtest():
    assert dc.compare([1, 2], BT)["level"] == "at high"
    assert dc.compare([], BT)["level"] == "no trades"
    assert dc.compare([-1], [1, -1])["level"] == "no backtest"


def test_report_uses_paper_positions(temp_db, monkeypatch):
    from sqlalchemy.orm import Session
    from app.db import get_engine
    from app.core import state
    monkeypatch.setattr(dc, "load_backtest", lambda: {"orb": [float(x) for x in BT]})
    with Session(get_engine()) as s:
        state.put(s, "active_strategy", "orb")
        for i, r in enumerate([1.0, -1.0]):
            s.add(PositionRow(order_id=i + 1, strategy="orb", side=1, kind="market", qty=0.1, entry=1, stop=0,
                              target=2, opened_ts=i, status="closed", closed_ts=i + 1, r=r, risk_pts=1))
        s.flush()
        rep = dc.report(s)
        assert [r["strategy"] for r in rep["rows"]] == ["orb"]
        assert rep["rows"][0]["level"] == "normal" and rep["rows"][0]["active"]
        assert dc.telegram_lines(s)[0].startswith("Is this drop normal? orb: now 1.00R below its high")
