from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from app.core import scanner
from app.core.markets import nas_hold_mask
from app.core.scanner import ScanMarket, Setup, pick, resolve, scan_market
from app.models import ScannerSignalRow

NY = ZoneInfo("America/New_York")


def _setup(market="nas100", strategy="orb", qualified=True, cost=0.1, news=False):
    return Setup(market, strategy, 1, "limit", 100.0, 90.0, 120.0, 2.0, 0, 0, "", cost, qualified, news)


def test_nothing_shown_unless_qualified(monkeypatch):
    monkeypatch.setattr(scanner, "QUALIFIED", {})
    assert pick([_setup(qualified=False), _setup(strategy="trend_fvg", qualified=False)]) is None


def test_cost_and_news_checks_block_a_qualified_setup(monkeypatch):
    monkeypatch.setattr(scanner, "QUALIFIED", {("nas100", "orb"): 0.2})
    assert pick([_setup(cost=0.25)]) is None
    assert pick([_setup(news=True)]) is None
    assert pick([_setup()]) is not None


def test_pick_prefers_higher_validation_r_then_lower_cost(monkeypatch):
    monkeypatch.setattr(scanner, "QUALIFIED", {("nas100", "orb"): 0.1, ("gold", "orb"): 0.3})
    a, b = _setup("nas100"), _setup("gold")
    assert pick([a, b]) is b
    monkeypatch.setattr(scanner, "QUALIFIED", {("nas100", "orb"): 0.3, ("gold", "orb"): 0.3})
    a, b = _setup("nas100", cost=0.15), _setup("gold", cost=0.05)
    assert pick([a, b]) is b


def ts(h, m, day=12):
    return int(datetime(2026, 11, day, h, m, tzinfo=NY).timestamp())


def bars(rows):
    return pd.DataFrame(rows, columns=["ts", "o", "h", "l", "c"])


def _row(kind="limit", target=120.0):
    return ScannerSignalRow(market="nas100", strategy="orb", bar_close_ts=ts(10, 0), created_ts=ts(10, 0), side=1,
                            kind=kind, entry=100.0, stop=90.0, target=target, rr_target=2.0, expiry_ts=ts(10, 30),
                            cost_r=0.2, qualified=False, shown=False, reason="", data_source="t", status="open")


def test_resolve_fill_then_target():
    r = _row()
    resolve(r, bars([(ts(10, 0), 105, 106, 104, 105), (ts(10, 1), 104, 104, 99.5, 101),
                     (ts(10, 2), 101, 121, 100, 120)]), nas_hold_mask, ts(10, 5))
    assert r.status == "target" and abs(r.r - (2.0 - 0.2)) < 1e-9


def test_resolve_stop_wins_when_both_touched():
    r = _row(kind="market")
    resolve(r, bars([(ts(10, 0), 100, 100, 100, 100), (ts(10, 1), 100, 125, 85, 100)]), nas_hold_mask, ts(10, 5))
    assert r.status == "stop" and abs(r.r - (-1.2)) < 1e-9


def test_resolve_expired_when_never_filled():
    r = _row()
    resolve(r, bars([(ts(10, m), 110, 111, 109, 110) for m in range(0, 35)]), nas_hold_mask, ts(10, 40))
    assert r.status == "expired" and r.r is None


def test_scan_market_closed_on_saturday():
    m = ScanMarket("gold", "Gold", "x", "XAUUSD", nas_hold_mask, [], cost_points=0.4)
    st = scan_market(m, int(datetime(2026, 11, 14, 10, 0, tzinfo=NY).timestamp()))
    assert st.state == "closed" and st.setups == []
