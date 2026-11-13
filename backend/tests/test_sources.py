import lzma
import struct
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.core.sources.dukascopy_source import day_url, parse_candles
from app.core.sources.mt5_source import server_to_utc


# ---------- Dukascopy ----------

def make_file(records):
    return lzma.compress(b"".join(struct.pack(">5if", *r) for r in records))


def test_dukascopy_month_is_zero_based():
    assert "/2026/00/05/" in day_url(date(2026, 1, 5))
    assert "/2026/10/13/" in day_url(date(2026, 11, 13))


def test_dukascopy_parse_scales_prices_and_time():
    raw = make_file([(60, 31_000_000, 31_002_000, 30_999_000, 31_003_500, 0.5)])
    (b,) = parse_candles(raw, date(2026, 11, 12))
    assert b.ts == int(datetime(2026, 11, 12, 0, 1, tzinfo=timezone.utc).timestamp())
    assert (b.open, b.high, b.low, b.close) == (31000.0, 31003.5, 30999.0, 31002.0)
    assert b.source == "dukascopy"


def test_dukascopy_drops_flat_zero_volume_fillers():
    raw = make_file([(0, 1000, 1000, 1000, 1000, 0.0), (60, 1000, 1001, 999, 1002, 1.0)])
    assert len(parse_candles(raw, date(2026, 11, 12))) == 1


def test_dukascopy_empty_file():
    assert parse_candles(b"", date(2026, 11, 12)) == []


# ---------- MT5 server time ----------

def fake_epoch(y, mo, d, h, mi):
    """What MT5 returns: server wall-clock written as if it were UTC."""
    return int(datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp())


def test_mt5_winter_offset_utc_plus_2():
    athens = ZoneInfo("Europe/Athens")
    # 16:30 server time in November = 14:30 UTC
    assert server_to_utc(fake_epoch(2026, 11, 12, 16, 30), athens) == fake_epoch(2026, 11, 12, 14, 30)


def test_mt5_summer_offset_utc_plus_3():
    athens = ZoneInfo("Europe/Athens")
    # 16:30 server time in July = 13:30 UTC
    assert server_to_utc(fake_epoch(2026, 7, 10, 16, 30), athens) == fake_epoch(2026, 7, 10, 13, 30)


# ---------------------------------------------------------------- polite downloading (Dukascopy 503s)
def test_rate_limit_stops_immediately_without_hammering(monkeypatch):
    from datetime import date as _date

    import pytest as _pytest

    from app.core.sources import dukascopy_source as dk
    calls = []

    def blocked(url, timeout):
        calls.append(url)
        raise dk.RateLimited("HTTP 503")

    monkeypatch.setattr(dk, "_get", blocked)
    monkeypatch.setattr(dk.time, "sleep", lambda s: None)
    with _pytest.raises(dk.RateLimited):
        dk.fetch_day(_date(2021, 3, 1))
    assert len(calls) == 1                     # one request, then the caller waits


def test_polite_schedule_backs_off_and_recovers():
    from app.core.sources.dukascopy_source import PoliteSchedule
    s = PoliteSchedule(base_pause=6)
    waits = [s.on_block() for _ in range(7)]
    assert [w / 60 for w in waits] == [2, 4, 8, 16, 30, 30, 30]   # minutes
    assert s.pause == 60                       # normal pause grew (capped at 60 s)
    for _ in range(500):
        s.on_success()
    assert 6 < s.pause < 7                     # slowly comes back (x0.8 every 50 good days)
    for _ in range(500):
        s.on_success()
    assert s.pause == 6                        # ... down to the base pause
