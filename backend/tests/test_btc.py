"""Weekend BTC book: Binance parsing, weekend hours, % costs, and keeping the two books apart."""
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import state
from app.core.engine import TradingEngine
from app.core.fills import Costs, net_points
from app.core.market_data import Bar
from app.core.markets import BTCUSD, NAS100
from app.core.paper_broker import PaperBroker
from app.core.sources.binance_source import parse_klines
from app.core.strategies import ALL
from app.core.strategies.base import BAR, Order, Strategy
from app.core.strategies.trend_fvg import BTCWeekendTrendFVG
from app.db import get_engine
from app.main import app
from app.models import OrderRow, PositionRow, SignalRow
from app.repository import save_bars

NY = ZoneInfo("America/New_York")
SRC, SYM = "test-binance", "BTCUSDT"


def ny(day, h, m):
    return int(datetime(2026, 11, day, h, m, tzinfo=NY).timestamp())   # 13 = Fri, 14 = Sat, 15 = Sun, 16 = Mon


def count(model, *where):
    with Session(get_engine()) as s:
        return s.scalar(select(func.count()).select_from(model).where(*where))


# ---------------------------------------------------------------- data + rules
def test_parse_klines_drops_the_candle_still_forming():
    rows = [[1_800_000_000_000, "100", "110", "95", "105", "2.5", 1_800_000_059_999],
            [1_800_000_060_000, "105", "106", "104", "105.5", "1", 1_800_000_119_999]]
    bars = parse_klines(rows, now_ms=1_800_000_100_000)
    assert len(bars) == 1
    b = bars[0]
    assert (b.ts, b.open, b.high, b.low, b.close, b.volume) == (1_800_000_000, 100, 110, 95, 105, 2.5)


def test_btc_trades_only_on_weekends():
    assert not BTCUSD.can_hold(ny(13, 16, 59)) and BTCUSD.can_hold(ny(13, 17, 0))      # Friday 17:00 NY
    assert BTCUSD.can_hold(ny(14, 3, 0)) and BTCUSD.can_hold(ny(15, 16, 59))           # Sat, Sun
    assert not BTCUSD.can_hold(ny(15, 17, 0)) and not BTCUSD.can_hold(ny(16, 10, 0))   # Sun 17:00, Mon


def test_the_two_books_never_overlap():
    start = ny(9, 0, 0)
    for k in range(7 * 24 * 60):
        t = start + k * 60
        assert not (NAS100.can_hold(t) and BTCUSD.can_hold(t))


def test_percentage_costs_for_crypto():
    c = Costs(spread=0, slippage=0, fee_pct=0.1, slip_pct=0.02)
    assert net_points(1, 50_000, 50_500, "limit", "target", c) == pytest.approx(500 - 50)
    assert net_points(1, 50_000, 49_800, "limit", "stop", c) == pytest.approx(-200 - 50 - 10)
    assert net_points(1, 100, 102, "limit", "target", Costs()) == pytest.approx(2 - 1.5)   # NAS100 unchanged


def test_btc_strategy_window_is_weekend_only():
    s = BTCWeekendTrendFVG()
    a = {"weekday": np.array([4, 4, 5, 6, 6, 0]), "mod": np.array([16 * 60, 17 * 60, 600, 15 * 60 + 25, 15 * 60 + 30, 600])}
    assert [s.in_window(i, a) for i in range(6)] == [False, True, True, True, False, False]


# ---------------------------------------------------------------- engine + broker
class BtcAlwaysLong(Strategy):
    name = "btc_always_long"

    def on_bar(self, i, a):
        c = float(a["c"][i])
        return Order(self.name, 1, "limit", c - 50, c - 250, c + 350, 2.0,
                     placed_ts=int(a["close_ts"][i]), expiry_ts=int(a["close_ts"][i]) + 6 * BAR, reason="test")


def flat(start, n, price=60_000.0):
    return [Bar(SRC, SYM, "M1", start + k * 60, price, price + 20, price - 20, price, 1) for k in range(n)]


@pytest.fixture
def btc_setup(temp_db, monkeypatch):
    monkeypatch.setitem(ALL, "btc_always_long", BtcAlwaysLong)
    save_bars(flat(ny(14, 8, 0), 120))                   # Saturday 08:00-09:59 NY
    with Session(get_engine()) as s, s.begin():
        state.put(s, "active_strategy_btc", "btc_always_long")
        state.put(s, "auto_trading", True)
    return ny(14, 10, 0) + 5


def btc_engine():
    return TradingEngine(SRC, SYM, 1_000.0, market=BTCUSD)


def test_btc_engine_trades_on_saturday_with_btc_sizing(btc_setup):
    res = btc_engine().cycle(btc_setup)
    assert res.status == "ORDER"
    with Session(get_engine()) as s:
        o = s.scalars(select(OrderRow)).one()
        assert o.strategy == "btc_always_long"
        assert o.qty == pytest.approx(0.025)             # $5 risk (0.5% of $1,000) / 200 pts stop
    save_bars([Bar(SRC, SYM, "M1", ny(14, 10, 0), 60_000, 60_001, 59_940, 59_990, 1)])   # fills at 59,950
    btc_engine().cycle(ny(14, 10, 1) + 5)
    assert count(PositionRow, PositionRow.status == "open") == 1


def test_nas_broker_never_touches_the_btc_position(btc_setup):
    eng = btc_engine()
    eng.cycle(btc_setup)
    save_bars([Bar(SRC, SYM, "M1", ny(14, 10, 0), 60_000, 60_001, 59_940, 59_990, 1)])
    eng.cycle(ny(14, 10, 1) + 5)
    with Session(get_engine()) as s, s.begin():
        nas = PaperBroker(s, NAS100.instrument, 1_000.0, market=NAS100)
        assert nas.open_positions() == []                # not its book
        assert nas.account_state(ny(14, 10, 2)).open_positions == 1   # but the shared limit counts it
        nas.process_minute(Bar("mt5", "USTEC", "M1", ny(14, 10, 2), 1, 1, 1, 1, 1))   # weekend NAS bar
    assert count(PositionRow, PositionRow.status == "open") == 1     # still open: NAS did not close it


def test_btc_engine_waits_on_weekdays(btc_setup):
    save_bars(flat(ny(16, 8, 0), 120))                   # Monday
    res = btc_engine().cycle(ny(16, 10, 0) + 5)
    assert res.status == "WAIT" and "outside" in res.detail
    assert count(SignalRow) == 0


def test_kill_switch_closes_the_btc_book_at_the_btc_price(btc_setup):
    eng = btc_engine()
    eng.cycle(btc_setup)
    save_bars([Bar(SRC, SYM, "M1", ny(14, 10, 0), 60_000, 60_001, 59_940, 59_990, 1)])
    eng.cycle(ny(14, 10, 1) + 5)
    with Session(get_engine()) as s, s.begin():
        state.put(s, "kill_switch", True)
    assert eng.cycle(ny(14, 10, 1) + 10).status == "KILLED"
    with Session(get_engine()) as s:
        p = s.scalars(select(PositionRow)).one()
        assert p.status == "closed" and p.exit_reason == "kill_switch" and p.exit_price == pytest.approx(59_990)


def test_choosing_a_btc_strategy_sets_the_btc_book(temp_db):
    c = TestClient(app)
    r = c.post("/api/controls/strategy", json={"name": "btc_weekend_trend_fvg"})
    assert r.status_code == 200 and r.json()["market"] == "btc"
    ov = c.get("/api/overview").json()
    books = {m["key"]: m for m in ov["markets"]}
    assert books["btc"]["active_strategy"] == "btc_weekend_trend_fvg"
    assert books["nas100"]["active_strategy"] == "trend_fvg"     # NAS100 book unchanged
