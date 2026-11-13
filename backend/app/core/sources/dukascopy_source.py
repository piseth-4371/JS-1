"""Download free historical 1-minute candles from Dukascopy (for backtesting).

File format (decoded and checked on 2026-11-13):
  URL  .../datafeed/<INSTRUMENT>/<YYYY>/<MM-1>/<DD>/BID_candles_min_1.bi5
       NOTE: the month is 0-based (January = 00).
  Body LZMA-compressed; records of 24 bytes, big-endian:
       int32 seconds-from-midnight-UTC, int32 open, int32 close, int32 low, int32 high, float32 volume
  Prices are integers; divide by PRICE_SCALE.

Dukascopy fills closed-market minutes with flat zero-volume candles; we drop those.
HTTPS to the datafeed timed out from this PC, so we try HTTPS first then plain HTTP.
"""
from __future__ import annotations

import lzma
import struct
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

from app.core.market_data import Bar

INSTRUMENT = "USATECHIDXUSD"  # Dukascopy's Nasdaq-100 index CFD
PRICE_SCALE = 1000            # 31033675 -> 31033.675 (to be confirmed against MT5)
SOURCE = "dukascopy"
RECORD = struct.Struct(">5if")


def day_url(day: date, instrument: str = INSTRUMENT, scheme: str = "https") -> str:
    return (f"{scheme}://datafeed.dukascopy.com/datafeed/{instrument}/"
            f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5")


def parse_candles(raw_lzma: bytes, day: date, instrument: str = INSTRUMENT, scale: int = PRICE_SCALE) -> list[Bar]:
    """Turn one downloaded day file into Bars. Pure function (easy to test)."""
    if not raw_lzma:
        return []
    data = lzma.decompress(raw_lzma)
    if len(data) % RECORD.size:
        raise ValueError(f"{day}: file size {len(data)} is not a multiple of {RECORD.size}")
    midnight = int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())
    bars = []
    for secs, o, c, lo, hi, vol in RECORD.iter_unpack(data):
        if vol <= 0 and o == c == lo == hi:
            continue  # filler candle while the market is closed
        bars.append(Bar(SOURCE, instrument, "M1", midnight + secs, o / scale, hi / scale, lo / scale, c / scale, float(vol)))
    return bars


def _get(url: str, timeout: float) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "nas100-control-center/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # no data that day (weekend/holiday)
        raise


_preferred_scheme = "https"


def fetch_day(day: date, instrument: str = INSTRUMENT, timeout: float = 20, retries: int = 4) -> list[Bar]:
    """One day of bars. Retries with growing pauses (the server rate-limits with HTTP 503)."""
    global _preferred_scheme
    last_exc: Exception | None = None
    for attempt in range(retries):
        schemes = [_preferred_scheme] + [s for s in ("https", "http") if s != _preferred_scheme]
        for scheme in schemes:
            try:
                raw = _get(day_url(day, instrument, scheme), timeout)
                _preferred_scheme = scheme  # remember what worked
                return [] if raw is None else parse_candles(raw, day, instrument)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_exc = e
        time.sleep(5 * (attempt + 1) ** 2)  # 5s, 20s, 45s, 80s
    raise ConnectionError(f"Dukascopy download failed for {day}: {last_exc}")


def trading_days(start: date, end: date):
    """Days start..end-1, skipping Saturdays (no bars; Sunday evening does have bars)."""
    d = start
    while d < end:
        if d.weekday() != 5:
            yield d
        d += timedelta(days=1)
