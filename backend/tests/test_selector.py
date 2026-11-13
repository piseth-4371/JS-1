"""Auto-switch selector: it may only use the past, and it follows its declared rules."""
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.backtest.selector import mondays, walk_forward

NY = ZoneInfo("America/New_York")


@dataclass
class T:
    r: float
    entry_ts: int
    exit_ts: int
    ny_date: date


def tr(d: date, r: float, hour=10):
    ts = int(datetime(d.year, d.month, d.day, hour, tzinfo=NY).timestamp())
    return T(r, ts, ts + 1800, d)


def daily(start: date, days: int, r: float):
    from datetime import timedelta
    return [tr(start + timedelta(days=k), r) for k in range(days) if (start + timedelta(days=k)).weekday() < 5]


def test_mondays():
    assert mondays(date(2026, 11, 4), date(2026, 11, 24)) == [date(2026, 11, 9), date(2026, 11, 16), date(2026, 11, 23)]


def test_picks_the_strategy_that_did_best_before_the_week():
    data = {"good": daily(date(2026, 9, 1), 70, 0.5), "bad": daily(date(2026, 9, 1), 70, -0.5)}
    res = walk_forward(data, date(2026, 10, 5), date(2026, 10, 12), 30, "avg_r")
    assert [p.strategy for p in res.picks] == ["good"]
    assert all(t.r == 0.5 for t in res.trades) and len(res.trades) == 5    # Mon-Fri of that week


def test_never_uses_trades_from_the_week_it_is_choosing_for():
    """'future_star' only wins DURING the week; before it, it lost. A cheating selector would pick it."""
    week = date(2026, 10, 5)
    future_star = daily(date(2026, 9, 1), 34, -0.2) + daily(week, 7, 3.0)
    steady = daily(date(2026, 9, 1), 41, 0.1)
    res = walk_forward({"future_star": future_star, "steady": steady}, week, date(2026, 10, 12), 30, "avg_r")
    assert res.picks[0].strategy == "steady"


def test_stays_out_when_everything_is_losing_but_win_rate_still_picks():
    data = {"a": daily(date(2026, 9, 1), 40, -0.3), "b": daily(date(2026, 9, 1), 40, -0.1)}
    out = walk_forward(data, date(2026, 10, 5), date(2026, 10, 12), 30, "avg_r")
    assert out.picks[0].strategy is None and out.trades == []
    wr = walk_forward(data, date(2026, 10, 5), date(2026, 10, 12), 30, "win_rate")
    assert wr.picks[0].strategy is not None          # the win-rate rule has no "stay out" safety


def test_needs_enough_past_trades():
    data = {"few": daily(date(2026, 9, 28), 5, 1.0), "none": []}
    res = walk_forward(data, date(2026, 10, 5), date(2026, 10, 12), 30, "avg_r", min_trades=10)
    assert res.picks[0].strategy is None and res.picks[0].candidates == 0
