"""Download free historical 1-minute candles from Dukascopy (for backtesting).

File format (decoded and checked on 2026-11-13):
  URL  .../datafeed/<INSTRUMENT>/<YYYY>/<MM-1>/<DD>/BID_candles_min_1.bi5
       NOTE: the month is 0-based (January = 00).
  Body LZMA-compressed; records of 24 bytes, big-endian:
       int32 seconds-from-midnight-UTC, int32 open, int32 close, int32 low, int32 high, float32 volume
  Prices are integers; divide by PRICE_SCALE.

Dukascopy fills closed-market minutes with flat zero-volume candles; we drop those.
Rate limit: the server answers HTTP 503 when we ask too fast. On a 503 we STOP at once
(RateLimited) and let the caller wait - retrying straight away only prolongs the block.
Plain HTTP only redirects to HTTPS (checked 2026-11-13); it is kept as a fallback for
connection errors (HTTPS timed out from this PC once), never for 503s.
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


class RateLimited(ConnectionError):
    """HTTP 503/429: the server wants us to slow down. Wait before the next request."""


def _get(url: str, timeout: float) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "LITTLE/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # no data that day (weekend/holiday)
        if e.code in (429, 503):
            raise RateLimited(f"HTTP {e.code}") from e
        raise


_preferred_scheme = "https"


def fetch_day(day: date, instrument: str = INSTRUMENT, timeout: float = 20, retries: int = 3) -> list[Bar]:
    """One day of bars.

    RateLimited (503/429) is raised IMMEDIATELY - the caller must wait (see scripts/backfill.py).
    Network errors (timeouts, resets) are retried a few times, also trying the other scheme.
    """
    global _preferred_scheme
    last_exc: Exception | None = None
    for attempt in range(retries):
        schemes = [_preferred_scheme] + [s for s in ("https", "http") if s != _preferred_scheme]
        for scheme in schemes:
            try:
                raw = _get(day_url(day, instrument, scheme), timeout)
                _preferred_scheme = scheme  # remember what worked
                return [] if raw is None else parse_candles(raw, day, instrument)
            except RateLimited:
                raise
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_exc = e
        time.sleep(5 * (attempt + 1))
    raise ConnectionError(f"Dukascopy download failed for {day}: {last_exc}")


class PoliteSchedule:
    """How long to wait: a normal pause between days that grows after each block (and slowly
    shrinks back), plus an exponential wait while blocked: 2, 4, 8, 16, 30, 30 ... minutes."""

    def __init__(self, base_pause: float = 6.0, max_pause: float = 60.0):
        self.base, self.max = base_pause, max_pause
        self.pause = base_pause
        self.blocked_in_a_row = 0
        self.ok_in_a_row = 0

    def on_success(self) -> float:
        self.blocked_in_a_row = 0
        self.ok_in_a_row += 1
        if self.ok_in_a_row % 50 == 0:
            self.pause = max(self.base, self.pause * 0.8)
        return self.pause

    def on_block(self) -> float:
        self.ok_in_a_row = 0
        self.blocked_in_a_row += 1
        self.pause = min(self.max, self.pause * 1.5)
        return min(30 * 60, 120 * 2 ** (self.blocked_in_a_row - 1))


def trading_days(start: date, end: date):
    """Days start..end-1, skipping Saturdays (no bars; Sunday evening does have bars)."""
    d = start
    while d < end:
        if d.weekday() != 5:
            yield d
        d += timedelta(days=1)
