from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.market_data import Bar
from app.main import app
from app.repository import count_bars, load_bars, save_bars


def bars(n, start=1_800_000_000):
    start -= start % 300
    return [Bar("test", "X", "M1", start + i * 60, 100, 101, 99, 100.5, 1) for i in range(n)]


def test_save_and_load_roundtrip(temp_db):
    b = bars(10)
    save_bars(b)
    assert load_bars("test", "X", "M1", b[0].ts, b[-1].ts + 1) == b


def test_saving_twice_does_not_duplicate(temp_db):
    b = bars(10)
    save_bars(b)
    save_bars(b)
    assert count_bars("test", "X")[0] == 10


def test_save_more_than_one_chunk(temp_db):
    save_bars(bars(1234))
    assert count_bars("test", "X")[0] == 1234


def test_bars_endpoint_resamples_and_reports_source(temp_db):
    now = int(datetime.now(timezone.utc).timestamp())
    save_bars(bars(30, start=now - 3600))
    body = TestClient(app).get("/api/market/bars", params={"source": "test", "symbol": "X", "tf": "M5", "hours": 2}).json()
    assert body["source"] == "test"
    assert body["count"] == 6
    assert body["stale"] is True  # newest bar is ~30 minutes old
