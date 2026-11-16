import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.backup import backup, sqlite_path


def test_backup_copies_data_and_keeps_newest(tmp_path):
    db = tmp_path / "journal #1%.db"
    with sqlite3.connect(db) as c:
        c.execute("create table t (x int)")
        c.execute("insert into t values (42)")
    t0 = datetime(2026, 11, 13, tzinfo=timezone.utc)
    outs = [backup(db, tmp_path / "b", keep=3, now=t0 + timedelta(hours=i)) for i in range(5)]
    left = sorted(p.name for p in (tmp_path / "b").glob("*.db"))
    assert left == [p.name for p in outs[-3:]]
    with sqlite3.connect(outs[-1]) as c:
        assert c.execute("select x from t").fetchone() == (42,)


def test_sqlite_path_rules(tmp_path):
    assert sqlite_path("sqlite:///./data/app.db", tmp_path) == (tmp_path / "data" / "app.db").resolve()
    with pytest.raises(ValueError):
        sqlite_path("postgresql://x", tmp_path)
    with pytest.raises(FileNotFoundError):
        backup(tmp_path / "missing.db", tmp_path / "b")
