from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from app.core import scanner
from app.core.markets import nas_hold_mask
from app.core.scanner import ScanMarket, Setup, pick, resolve, scan_market
from app.models import ScannerSignalRow, ScannerExecutionRow

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
                            cost_r=0.2, qualified=False, shown=False, reason="", data_source="t", status="open",
                            execution=ScannerExecutionRow(version=2, costs={"spread": 2.0, "slippage": 0.0}))


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


def test_unknown_news_and_expired_setups_blocked(monkeypatch):
    monkeypatch.setattr(scanner, "QUALIFIED", {("nas100", "orb"): 0.2})
    x = _setup()
    x.news_known = False
    assert pick([x]) is None
    x.news_known, x.expired = True, True
    assert pick([x]) is None


def test_stop_gap_and_both_slippage_legs():
    r = _row(kind="stop")
    r.execution.costs = {"spread": 1.5, "slippage": 0.5}
    resolve(r, bars([(ts(10, 0), 105, 106, 100, 105),
                     (ts(10, 1), 80, 85, 75, 82)]), nas_hold_mask, ts(10, 5))
    assert r.execution.fill_price == 105
    assert r.execution.exit_price == 80
    assert r.status == "stop"
    assert abs(r.r - (-2.75)) < 1e-9


def test_better_limit_fill_and_fixed_displayed_target():
    r = _row()
    resolve(r, bars([(ts(10, 0), 95, 101, 94, 100),
                     (ts(10, 1), 100, 121, 99, 120)]), nas_hold_mask, ts(10, 5))
    assert r.execution.fill_price == 95
    assert r.execution.exit_price == 120
    assert abs(r.r - 2.3) < 1e-9


def test_no_fill_before_publication_or_on_unclosed_bar():
    r = _row(kind="market")
    r.created_ts = ts(10, 0) + 20
    resolve(r, bars([(ts(10, 0), 100, 125, 80, 100),
                     (ts(10, 1), 105, 110, 100, 108)]), nas_hold_mask, ts(10, 1) + 30)
    assert r.status == "open"
    resolve(r, bars([(ts(10, 1), 105, 110, 100, 108)]), nas_hold_mask, ts(10, 2))
    assert r.execution.fill_price == 105
    assert r.status == "filled"


def test_repeated_resolution_and_restart_use_persisted_fill(temp_db):
    from sqlalchemy.orm import Session
    from app.db import get_engine
    r = _row(kind="market")
    with Session(get_engine()) as s, s.begin():
        s.add(r)
        resolve(r, bars([(ts(10, 0), 105, 110, 100, 108)]), nas_hold_mask, ts(10, 1))
    with Session(get_engine()) as s, s.begin():
        r = s.query(ScannerSignalRow).one()
        resolve(r, bars([(ts(10, 0), 105, 110, 100, 108),
                         (ts(10, 1), 80, 85, 75, 82)]), nas_hold_mask, ts(10, 2))
        assert r.execution.fill_price == 105
        assert abs(r.r + 2.7) < 1e-9


def test_legacy_is_not_rewritten():
    r = _row()
    r.execution = None
    resolve(r, bars([(ts(10, 0), 100, 120, 80, 100)]), nas_hold_mask, ts(10, 5))
    assert r.status == "open" and r.r is None


def test_cost_estimate_includes_entry_and_stop_exit():
    assert scanner.estimated_cost("nas100", 100, "market") == 2.5
    assert scanner.estimated_cost("nas100", 100, "limit") == 2.0
    assert abs(scanner.estimated_cost("btc", 50000, "stop") - 70) < 1e-9


def test_summary_excludes_unfilled_from_win_rate():
    from app.api_scanner import summary
    won, lost, expired = _row(), _row(), _row()
    won.r, won.status = 2.0, "target"
    lost.r, lost.status = -1.0, "stop"
    expired.status = "expired"
    stats = summary([won, lost, expired])
    assert stats["resolved"] == 2 and stats["recorded"] == 3
    assert stats["win_rate"] == 50 and stats["avg_r"] == 0.5
    assert stats["win_rate_95_range"][0] < 50 < stats["win_rate_95_range"][1]
    assert stats["avg_r_95_range"] is None


def test_api_hides_stale_signal_and_excludes_legacy(temp_db, monkeypatch):
    from app.api_scanner import get_scanner
    from sqlalchemy.orm import Session
    from app.db import get_engine
    old = _row()
    old.execution = None
    old.r, old.status = 9.0, "target"
    with Session(get_engine()) as s, s.begin():
        s.add(old)
    monkeypatch.setattr(scanner, "LATEST", {"scanned_ts": 1, "signal": {
        "market": "nas100", "strategy": "orb", "expiry_ts": 2}})
    result = get_scanner(limit=40)
    assert result["signal"] is None
    assert result["track_record"]["legacy_excluded"] == 1
    assert result["track_record"]["practice"]["resolved"] == 0


def test_run_scan_alerts_new_setups_once_and_outcomes(temp_db, monkeypatch):
    from sqlalchemy.orm import Session
    from app.db import get_engine
    x = _setup(qualified=False)
    x.bar_close_ts, x.expiry_ts = ts(10, 0), ts(10, 30)
    status = scanner.MarketStatus("nas100", "NAS100", "open", "", setups=[x])
    market = ScanMarket("nas100", "NAS100", "t", "SYM", nas_hold_mask, [])
    monkeypatch.setattr(scanner, "scan_markets", lambda: [market])
    monkeypatch.setattr(scanner, "scan_market", lambda m, now: status)
    prices = bars([(ts(10, 0), 95, 101, 94, 100), (ts(10, 1), 100, 101, 99, 100), (ts(10, 2), 100, 121, 99, 120)])
    monkeypatch.setattr(scanner, "load_m1", lambda *a: prices)
    first, second = [], []
    with Session(get_engine()) as s, s.begin():
        scanner.run_scan(s, now=ts(10, 0) + 1, alerts=first)
    assert [a["type"] for a in first] == ["setup"] and first[0]["setup"]["strategy"] == "orb"
    with Session(get_engine()) as s, s.begin():
        scanner.run_scan(s, now=ts(10, 4), alerts=second)
    assert all(a["type"] == "outcome" for a in second)            # same setup is not announced twice
    assert second[-1]["status"] == "target" and second[-1]["qualified"] is False
