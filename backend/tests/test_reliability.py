"""Day 7: failure injection. Things go wrong; the system must stay safe."""
import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import live_loop, state
from app.core.engine import CycleResult, TradingEngine
from app.core.market_data import Bar
from app.core.sources.mt5_source import MT5Error
from app.db import get_engine
from app.models import EventRow, OrderRow, PositionRow
from app.repository import save_bars
from tests.test_paper_trading import SRC, SYM, AlwaysLong, flat_bars, ny, setup  # noqa: F401


def count(model, *where):
    with Session(get_engine()) as s:
        return s.scalar(select(func.count()).select_from(model).where(*where))


def test_live_loop_survives_mt5_errors_and_crashing_cycles(monkeypatch):
    calls = {"pull": 0, "cycle": 0, "sleep": 0}

    def bad_pull():
        calls["pull"] += 1
        raise MT5Error("terminal closed") if calls["pull"] == 1 else RuntimeError("network down")

    class Eng:
        def startup(self):
            pass

        def cycle(self):
            calls["cycle"] += 1
            if calls["cycle"] == 1:
                raise ValueError("unexpected bug")
            return CycleResult("WAIT")

    async def fake_sleep(_):
        calls["sleep"] += 1
        if calls["sleep"] >= 3:
            raise asyncio.CancelledError

    monkeypatch.setattr(live_loop, "_pull_bars", bad_pull)
    monkeypatch.setattr(live_loop.asyncio, "sleep", fake_sleep)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(live_loop.run_forever(Eng()))
    assert calls["cycle"] == 3          # kept going after an MT5 error, a network error and a crash


def test_impossible_candle_means_wait_and_error_event(setup):
    save_bars([Bar(SRC, SYM, "M1", ny(10, 0), 28000, 27990, 28010, 28000, 1)])   # high < low
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    res = TradingEngine(SRC, SYM, 10_000.0).cycle(ny(10, 1) + 5)
    assert res.status == "WAIT" and "validation" in res.detail
    assert count(EventRow, EventRow.type == "bad_data") == 1
    assert count(OrderRow) == 0


def test_feed_stops_during_session_logs_warning(setup):
    res = TradingEngine(SRC, SYM, 10_000.0).cycle(ny(10, 30))   # last bar 09:59, now 10:30
    assert res.status == "WAIT"
    assert count(EventRow, EventRow.type == "stale_data") == 1


def test_kill_switch_survives_restart(setup):
    with Session(get_engine()) as s, s.begin():
        state.put(s, "kill_switch", True)
        state.put(s, "auto_trading", True)
    fresh = TradingEngine(SRC, SYM, 10_000.0)      # new process after a restart
    fresh.startup(setup)
    assert fresh.cycle(setup).status == "KILLED"
    assert count(OrderRow) == 0


def test_position_left_open_over_restart_is_closed_at_session_end(setup):
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    eng = TradingEngine(SRC, SYM, 10_000.0)
    assert eng.cycle(setup).status == "ORDER"
    save_bars([Bar(SRC, SYM, "M1", ny(10, 0), 28000, 28001, 27990, 27998, 10)])   # fills the limit
    eng.cycle(ny(10, 1) + 5)
    assert count(PositionRow, PositionRow.status == "open") == 1

    # server is "off" until 16:10; on restart the missed minutes are processed in order
    save_bars(flat_bars(ny(10, 1), 369, price=27999.0))        # 10:01 .. 16:09, between stop and target
    restarted = TradingEngine(SRC, SYM, 10_000.0)
    restarted.startup(ny(16, 10) + 5)
    restarted.cycle(ny(16, 10) + 5)
    with Session(get_engine()) as s:
        (p,) = s.scalars(select(PositionRow)).all()
        assert p.status == "closed" and p.exit_reason == "session_end"
        assert p.closed_ts == ny(15, 55)


def test_cycle_never_trades_without_a_stop(setup, monkeypatch):
    from app.core.strategies import ALL
    from app.core.strategies.base import Order

    class NoStop(AlwaysLong):
        def on_bar(self, i, a):
            o = super().on_bar(i, a)
            return Order(o.strategy, 1, "limit", o.entry, float("nan"), o.target, 2.0, o.placed_ts, o.expiry_ts)

    monkeypatch.setitem(ALL, "always_long", NoStop)
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    res = TradingEngine(SRC, SYM, 10_000.0).cycle(setup)
    assert res.status == "REJECTED" and "Stop-loss is missing" in res.detail
    assert count(OrderRow) == 0


def test_numpy_values_from_strategies_are_stored_as_numbers(setup, monkeypatch):
    """Regression (Day 7 replay): numpy.int64 timestamps were saved as bytes and crashed the broker."""
    import numpy as np

    from app.core.strategies import ALL
    from app.core.strategies.base import Order

    class NumpyLong(AlwaysLong):
        def on_bar(self, i, a):
            c = a["c"][i]
            return Order(self.name, np.int64(1), "limit", c - 5, c - 25, c + 35, 2.0,
                         placed_ts=a["close_ts"][i], expiry_ts=a["close_ts"][i] + np.int64(1800))

    monkeypatch.setitem(ALL, "always_long", NumpyLong)
    with Session(get_engine()) as s, s.begin():
        state.put(s, "auto_trading", True)
    eng = TradingEngine(SRC, SYM, 10_000.0)
    assert eng.cycle(setup).status == "ORDER"
    save_bars([Bar(SRC, SYM, "M1", ny(10, 0), 28000, 28001, 27990, 27998, 10)])
    eng.cycle(ny(10, 1) + 5)                       # used to raise TypeError: int < bytes
    with Session(get_engine()) as s:
        o = s.scalars(select(OrderRow)).one()
        assert isinstance(o.active_from_ts, int) and isinstance(o.expiry_ts, int)
        assert o.status == "filled"
