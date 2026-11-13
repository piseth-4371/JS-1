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


def current_m5_preview(rows: list, now_ts: int) -> dict:
    """Use only the current, provisional five-minute kline for display."""
    base = {"available": False, "source": SOURCE, "symbol": SYMBOL,
            "candle": None, "observed_ts": now_ts, "stale": True}
    bucket = now_ts // 300 * 300
    if not rows or int(rows[0][0]) // 1000 != bucket:
        return {**base, "message": "No current five-minute candle from Binance."}
    row = rows[0]
    return {**base, "available": True, "stale": False,
            "candle": {"time": bucket, "open": float(row[1]), "high": float(row[2]),
                       "low": float(row[3]), "close": float(row[4])}}


def fetch_current_m5_preview() -> dict:
    """One bounded public market-data request; no account or trading endpoint."""
    now_ts = int(time.time())
    bucket = now_ts // 300 * 300
    params = f"symbol={SYMBOL}&interval=5m&startTime={bucket * 1000}&endTime={now_ts * 1000}&limit=1"
    try:
        with urllib.request.urlopen(f"{URL}?{params}", timeout=5) as resp:
            rows = json.loads(resp.read())
        return current_m5_preview(rows, int(time.time()))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, IndexError) as e:
        raise BinanceError(f"Binance preview unavailable: {e}") from e


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
