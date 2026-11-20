"""Day 4: paper broker, engine cycle, duplicates, kill switch, restart, stale data."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import state
from app.core.engine import TradingEngine
from app.core.fills import Costs
from app.core.market_data import Bar
from app.core.paper_broker import PaperBroker
from app.core.risk import USTEC
from app.core.strategies import ALL
from app.core.strategies.base import BAR, Order, Strategy
from app.db import get_engine
from app.main import app
from app.models import OrderRow, PositionRow, SignalRow
from app.repository import save_bars

NY = ZoneInfo("America/New_York")
SRC, SYM = "test", "USTEC"


def ny(h, m, day=10):
    return int(datetime(2026, 11, day, h, m, tzinfo=NY).timestamp())


def flat_bars(start, n, price=28000.0):
    return [Bar(SRC, SYM, "M1", start + k * 60, price, price + 2, price - 2, price, 10) for k in range(n)]


class AlwaysLong(Strategy):
    """Test strategy: a buy-limit 5 points under the close on every bar."""
    name = "always_long"

    def on_bar(self, i, a):
        c = float(a["c"][i])
        return Order(self.name, 1, "limit", c - 5, c - 25, c + 35, 2.0,
                     placed_ts=int(a["close_ts"][i]), expiry_ts=int(a["close_ts"][i]) + 6 * BAR,
                     reason="test")


@pytest.fixture
def setup(temp_db, monkeypatch):
    monkeypatch.setitem(ALL, "always_long", AlwaysLong)
    save_bars(flat_bars(ny(8, 0), 120))          # 08:00-09:59 NY
    with Session(get_engine()) as s, s.begin():
        state.put(s, "active_strategy", "always_long")
    return ny(10, 0) + 5                         # "now": just after the 09:55 bar closed


def count(model, *where):
    with Session(get_engine()) as s:
        return s.scalar(select(func.count()).select_from(model).where(*where))


# ------------------------------------------------------------------ engine

def test_ten_dollar_account_signal_is_rejected_by_min_lot(setup):
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    res = TradingEngine(SRC, SYM, 10.0).cycle(setup)
    assert res.status == "REJECTED" and "Minimum lot" in res.detail
    assert count(OrderRow) == 0
    assert count(SignalRow, SignalRow.action == "LONG") == 1


def test_auto_trading_off_records_signal_only(setup):
    res = TradingEngine(SRC, SYM, 10_000.0).cycle(setup)
    assert res.status == "REJECTED" and "Auto-trading is OFF" in res.detail
    assert count(OrderRow) == 0


def test_order_placed_once_even_if_cycle_repeats_or_server_restarts(setup):
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    assert TradingEngine(SRC, SYM, 10_000.0).cycle(setup).status == "ORDER"
    assert TradingEngine(SRC, SYM, 10_000.0).cycle(setup).detail == "this 5m bar was already evaluated"
    restarted = TradingEngine(SRC, SYM, 10_000.0)        # "server restart": brand-new object
    restarted.startup(setup)
    restarted.cycle(setup + 10)
    assert count(OrderRow) == 1


def test_stale_data_means_wait(setup):
    res = TradingEngine(SRC, SYM, 10_000.0).cycle(setup + 3600)
    assert res.status == "WAIT" and "stale" in res.detail


def test_no_data_means_wait(temp_db):
    assert TradingEngine("nothing", SYM, 10.0).cycle(ny(10, 0)).status == "WAIT"


def test_kill_switch_cancels_closes_and_blocks(setup):
    client = TestClient(app)
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    eng = TradingEngine(SRC, SYM, 10_000.0)
    assert eng.cycle(setup).status == "ORDER"
    # let the order fill: next minute dips to the limit
    save_bars([Bar(SRC, SYM, "M1", ny(10, 0), 28000, 28001, 27990, 27998, 10)])
    eng.cycle(ny(10, 1) + 5)
    assert count(PositionRow, PositionRow.status == "open") == 1

    from app import config
    config.get_settings.cache_clear()
    import os
    os.environ["ENGINE_SOURCE"] = SRC
    try:
        r = client.post("/api/controls/kill").json()
    finally:
        os.environ.pop("ENGINE_SOURCE")
        config.get_settings.cache_clear()
    assert r == {"kill_switch": True, "auto_trading": False}
    assert count(PositionRow, PositionRow.status == "open") == 0
    assert count(PositionRow, PositionRow.exit_reason == "kill_switch") == 1
    assert eng.cycle(ny(10, 2) + 5).status == "KILLED"
    assert client.post("/api/controls/auto-trading", json={"enabled": True}).status_code == 409
    assert client.post("/api/controls/reset-kill").status_code == 400          # a reason is required
    assert client.post("/api/controls/reset-kill", json={"reason": "test misclick"}).status_code == 200  # undo window
    assert client.get("/api/overview").json()["kill_switch"] is False


# ------------------------------------------------------------------ broker

def make_order(placed, kind="limit", entry=100.0, stop=90.0, target=120.0):
    return Order("t", 1, kind, entry, stop, target, 2.0, placed_ts=placed, expiry_ts=placed + 1800)


def bar(ts, o, h, l, c):  # noqa: E741
    return Bar(SRC, SYM, "M1", ts, o, h, l, c, 1)


def test_broker_fill_target_and_pnl(temp_db):
    t = ny(10, 0)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000, Costs(0, 0))
        b.place(make_order(t), qty=2.0, signal_id=None, now_ts=t)
        b.process_minute(bar(t, 105, 106, 99, 101))       # fills at 100
        b.process_minute(bar(t + 60, 101, 121, 101, 120))  # target 120
        (p,) = s.scalars(select(PositionRow)).all()
        assert p.exit_reason == "target" and p.r == pytest.approx(2.0) and p.pnl_usd == pytest.approx(40.0)
        assert b.account_state(t + 120).equity == pytest.approx(10_040)


def test_same_minute_processed_twice_has_no_effect(temp_db):
    t = ny(10, 0)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000, Costs(0, 0))
        b.place(make_order(t), 1.0, None, t)
        b.process_minute(bar(t, 105, 106, 99, 101))
        b.process_minute(bar(t, 105, 106, 99, 101))
        assert len(s.scalars(select(PositionRow)).all()) == 1


def test_duplicate_order_ignored(temp_db):
    t = ny(10, 0)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000)
        assert b.place(make_order(t), 1.0, None, t) is not None
        assert b.place(make_order(t), 1.0, None, t) is None
        assert len(b.pending_orders()) == 1


def test_position_closed_at_1555(temp_db):
    t = ny(15, 50)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000, Costs(0, 0))
        b.place(make_order(t, kind="market", target=None), 1.0, None, t)
        b.process_minute(bar(t, 100, 101, 99.5, 100))
        for k in range(1, 6):
            b.process_minute(bar(t + k * 60, 101, 101.5, 100.5, 101))
        (p,) = s.scalars(select(PositionRow)).all()
        assert p.status == "closed" and p.exit_reason == "session_end"


def test_reconcile_cancels_orders_that_expired_while_off(temp_db):
    t = ny(10, 0)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000)
        b.place(make_order(t), 1.0, None, t)
        fixes = b.reconcile(t + 7200)
        assert fixes and not b.pending_orders()


def test_daily_loss_and_losing_streak_come_from_db(temp_db):
    t = ny(10, 0)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000, Costs(0, 0))
        for k in range(2):  # two losing trades of $100 each
            ts = t + k * 600
            b.place(make_order(ts), 10.0, None, ts)
            b.process_minute(bar(ts, 100, 100.5, 99.5, 100))   # fill at 100
            b.process_minute(bar(ts + 60, 95, 95, 85, 88))     # low 85 touches stop 90 -> exit at 90
        a = b.account_state(t + 3600)
        assert a.consecutive_losses == 2 and a.trades_today == 2
        assert a.equity == pytest.approx(10_000 - 2 * 100)      # 10 pts x 10 lots x $1 each
        assert a.day_start_equity == pytest.approx(10_000)


# ------------------------------------------------------------------ dashboard API

def test_market_analysis_reports_source_and_levels(setup, monkeypatch):
    import time as _t
    monkeypatch.setattr(_t, "time", lambda: setup)
    body = TestClient(app).get("/api/market/analysis", params={"source": SRC, "symbol": SYM, "hours": 2}).json()
    assert body["available"] and body["source"] == SRC
    assert body["candles"] and body["stale"] is False
    assert set(body["levels"]) == {"PDH", "PDL", "ONH", "ONL"}


def test_market_analysis_without_data(temp_db):
    body = TestClient(app).get("/api/market/analysis", params={"source": "nothing"}).json()
    assert body["available"] is False


def test_overview_defaults_are_safe(temp_db):
    body = TestClient(app).get("/api/overview").json()
    assert body["mode"] == "PAPER" and body["live_trading_available"] is False
    assert body["auto_trading"] is False and body["kill_switch"] is False


def test_unknown_strategy_rejected(temp_db):
    assert TestClient(app).post("/api/controls/strategy", json={"name": "magic"}).status_code == 400


def test_journal_metrics_small_sample_warning(temp_db):
    t = ny(10, 0)
    with Session(get_engine()) as s, s.begin():
        b = PaperBroker(s, USTEC, 10_000, Costs(0, 0))
        b.place(make_order(t), 1.0, None, t)
        b.process_minute(bar(t, 105, 106, 99, 101))
        b.process_minute(bar(t + 60, 101, 121, 101, 120))
    m = TestClient(app).get("/api/journal/metrics").json()
    assert m["closed_trades"] == 1 and m["total_r"] == pytest.approx(2.0)
    assert m["enough_data"] is False and "30" in m["verdict"]
