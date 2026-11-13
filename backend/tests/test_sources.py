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
