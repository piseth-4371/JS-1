"""'Volatility now' for the dashboard: how big the last hour's move is compared with normal (display only).

    range  = (high - low) of the last 60 minutes of 1-minute bars, as % of price
    normal = median of the same New York clock hour on up to 20 earlier days that have data
    x      = range / normal

Matching the clock hour matters: the US open is always busier than lunch, so "normal" means normal for
this hour. It measures SIZE only and never direction. It changes no trading rule, filter or limit
(a volatility filter was tested and failed: docs/volatility_filter_report.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.core.news import NY

WINDOW_MIN = 60
MIN_BARS = 40           # a window needs at least 40 of its 60 minutes
LOOKBACK_DAYS = 20      # earlier days with data used for "normal"
SEARCH_DAYS = 35        # calendar days searched to find them (weekends/holidays have none)
MIN_SAMPLES = 10        # fewer earlier days than this -> no comparison
STALE_SECONDS = 10 * 60
LEVELS = ((0.7, "calm"), (1.5, "normal"), (2.5, "busy"))   # x below each limit; above the last -> "very wild"


def level(x: float) -> str:
    for limit, name in LEVELS:
        if x < limit:
            return name
    return "very wild"


def window_range_pct(ts: np.ndarray, h: np.ndarray, l: np.ndarray, end: int,  # noqa: E741
                     minutes: int = WINDOW_MIN, min_bars: int = MIN_BARS) -> float | None:
    """(high - low) / low of the bars in [end - minutes, end), in %, or None if too few bars."""
    a, b = np.searchsorted(ts, end - minutes * 60, "left"), np.searchsorted(ts, end, "left")
    if b - a < min_bars:
        return None
    hi, lo = float(h[a:b].max()), float(l[a:b].min())
    return (hi - lo) / lo * 100 if lo > 0 else None


@dataclass(frozen=True)
class VolNow:
    market: str
    state: str                     # ok / no recent data / not enough history
    range_pct: float | None = None
    normal_pct: float | None = None
    x: float | None = None
    level: str | None = None
    samples: int = 0
    as_of: int | None = None       # end of the measured hour (last bar close)


def measure(market: str, m1: pd.DataFrame, now: int) -> VolNow:
    if m1.empty:
        return VolNow(market, "no recent data")
    ts = m1["ts"].to_numpy(np.int64)
    h, lo = m1["h"].to_numpy(float), m1["l"].to_numpy(float)
    end = int(ts[-1]) + 60                                   # close of the latest stored minute
    if now - end > STALE_SECONDS:
        return VolNow(market, "no recent data", as_of=end)
    cur = window_range_pct(ts, h, lo, end)
    if cur is None:
        return VolNow(market, "no recent data", as_of=end)
    end_ny = datetime.fromtimestamp(end, NY)
    past = []
    for k in range(1, SEARCH_DAYS + 1):
        if len(past) >= LOOKBACK_DAYS:
            break
        # Same wall-clock time k days earlier (zoneinfo keeps the New York clock across DST changes).
        e = int((end_ny - timedelta(days=k)).timestamp())
        r = window_range_pct(ts, h, lo, e)
        if r is not None:
            past.append(r)
    if len(past) < MIN_SAMPLES:
        return VolNow(market, "not enough history", range_pct=round(cur, 3), samples=len(past), as_of=end)
    normal = float(np.median(past))
    x = cur / normal if normal > 0 else None
    return VolNow(market, "ok", round(cur, 3), round(normal, 3), None if x is None else round(x, 2),
                  None if x is None else level(x), len(past), end)


# ---------- from the database ----------
_CACHE: dict = {}


def report(now: int) -> dict:
    """Volatility now for NAS100, gold and BTC from the bars the scanner uses. Cached for 60 s."""
    if _CACHE.get("key") == now // 60:
        return _CACHE["value"]
    from sqlalchemy import text

    from app.core.scanner import scan_markets
    from app.db import get_engine
    q = text("SELECT ts, high AS h, low AS l FROM bars WHERE source=:s AND symbol=:y AND timeframe='M1' "
             "AND ts>=:a AND ts<:b ORDER BY ts")
    start = now - (SEARCH_DAYS + 2) * 86400
    out = []
    with get_engine().connect() as conn:
        for m in scan_markets():
            rows = conn.execute(q, {"s": m.source, "y": m.symbol, "a": start, "b": now + 60}).fetchall()
            out.append(asdict(measure(m.key, pd.DataFrame(rows, columns=["ts", "h", "l"]), now)))
    value = {"markets": out, "window_minutes": WINDOW_MIN, "lookback_days": LOOKBACK_DAYS,
             "note": "Last hour's high-low range vs the median of the same New York hour on the previous "
                     "20 days with data. Size only, never direction. Display only: no rule uses it."}
    _CACHE.update(key=now // 60, value=value)
    return value
