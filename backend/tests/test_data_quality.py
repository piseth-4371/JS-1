"""Session validity rule (docs/data_quality_rule.md) and data-hole detection."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from app.core import data_quality as dq
from app.repository import init_db

NY = ZoneInfo("America/New_York")


def day_bars(d: date, drop: set[int] = frozenset()):
    """1-minute bars for the 03:00-15:55 NY window of date d, minus the minute offsets in `drop`."""
    t0 = int(datetime(d.year, d.month, d.day, 3, 0, tzinfo=NY).timestamp())
    ts = [t0 + 60 * k for k in range(dq.WINDOW_BARS) if k not in drop]
    return pd.DataFrame({"ts": ts, "v": 0.0})


def test_full_day_is_valid_and_zero_volume_is_reported():
    (q,) = dq.session_quality(day_bars(date(2023, 3, 1)))
    assert q.valid and q.bars == 775 and q.longest_gap_min == 0 and q.zero_volume_share == 1.0


def test_five_minute_hole_ok_six_not():
    (q5,) = dq.session_quality(day_bars(date(2023, 3, 1), drop=set(range(100, 105))))
    (q6,) = dq.session_quality(day_bars(date(2023, 3, 1), drop=set(range(100, 106))))
    assert q5.valid and q5.longest_gap_min == 5
    assert not q6.valid and "gap of 6" in q6.reason


def test_missing_start_or_end_counts_as_gap_and_low_coverage_fails():
    (late,) = dq.session_quality(day_bars(date(2023, 3, 1), drop=set(range(0, 6))))
    assert not late.valid
    scattered = set(range(0, 775, 70)) | set(range(1, 775, 70))  # 2-min holes, 24 missing
    (low,) = dq.session_quality(day_bars(date(2023, 3, 1), drop=scattered))
    assert not low.valid and "bars" in low.reason and low.longest_gap_min == 2


def test_weekend_bars_ignored_and_dates_match_engine_dates():
    sat = day_bars(date(2023, 3, 4))
    assert dq.session_quality(sat) == []
    valid = dq.valid_dates(dq.session_quality(day_bars(date(2023, 3, 1))))
    assert date(2023, 3, 1) in valid       # plain datetime.date, same type as Frame ny_date


def test_max_gap_between_flags_holes_inside_a_trade():
    ts = np.array([0, 60, 120, 600, 660])
    assert dq.max_gap_between(ts, 0, 120) == 0
    assert dq.max_gap_between(ts, 0, 660) == 7       # 180..540 missing = 7 minutes


def test_init_db_adds_new_nullable_column_to_old_table(tmp_path, monkeypatch):
    import sqlite3
    from app import config, db
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE scanner_signals (id INTEGER PRIMARY KEY, market VARCHAR(10))")
    con.execute("INSERT INTO scanner_signals (id, market) VALUES (1, 'nas100')")
    con.commit()
    con.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()
    try:
        init_db()
        con = sqlite3.connect(path)
        cols = {r[1] for r in con.execute("PRAGMA table_info(scanner_signals)")}
        assert "cancel_level" in cols
        assert con.execute("SELECT market, cancel_level FROM scanner_signals").fetchall() == [("nas100", None)]
        con.close()
    finally:
        db.get_engine().dispose()
        config.get_settings.cache_clear()
        db.get_engine.cache_clear()
