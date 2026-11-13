"""Binance PUBLIC market data: BTCUSDT 1-minute candles (no account, no API key).

Endpoint: https://data-api.binance.vision/api/v3/klines (market data only).
Each kline: [open_ms, open, high, low, close, volume, close_ms, ...] in UTC.

Only CLOSED candles are returned: the still-forming minute is dropped, because a
saved bar is never overwritten (duplicates are skipped), so a half-finished
candle would stay wrong forever.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from app.core.market_data import Bar

SOURCE = "binance"
SYMBOL = "BTCUSDT"
URL = "https://data-api.binance.vision/api/v3/klines"
LIMIT = 1000          # max candles per request


class BinanceError(Exception):
    pass


def parse_klines(rows: list, now_ms: int, symbol: str = SYMBOL) -> list[Bar]:
    out = []
    for r in rows:
        if int(r[6]) >= now_ms:          # close time not reached yet: candle still forming
            continue
        out.append(Bar(SOURCE, symbol, "M1", int(r[0]) // 1000,
                       float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    return out


def _get(params: str, retries: int = 4) -> list:
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(f"{URL}?{params}", timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (418, 429):     # rate limited: wait as told
                time.sleep(int(e.headers.get("Retry-After", "30")))
                continue
            if e.code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            raise BinanceError(f"HTTP {e.code}: {e.reason}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(5 * (attempt + 1))
    raise BinanceError(f"Binance unreachable: {last}")


def fetch_m1(start: datetime, end: datetime, symbol: str = SYMBOL, pause: float = 0.2) -> list[Bar]:
    """All closed 1-minute candles with open time in [start, end)."""
    a = int(start.timestamp() * 1000)
    b = int(end.timestamp() * 1000)
    bars: list[Bar] = []
    while a < b:
        rows = _get(f"symbol={symbol}&interval=1m&startTime={a}&endTime={b - 1}&limit={LIMIT}")
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        bars += parse_klines(rows, now_ms, symbol)
        if len(rows) < LIMIT:
            break
        a = int(rows[-1][0]) + 60_000
        time.sleep(pause)
    return bars
