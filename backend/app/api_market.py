"""Market analysis for the chart: 5m candles, EMA/VWAP lines, today's
liquidity levels, recent Fair Value Gaps and the 15m trend bias.

Every value comes from stored bars (source + timestamp included). Nothing is invented.
"""
from __future__ import annotations

import math
import time

from fastapi import APIRouter, Query

from app.config import get_settings
from app.core.engine import HISTORY_DAYS
from app.core.features import build_frame, load_m1
from app.core.strategies.base import fvg

router = APIRouter(prefix="/api/market")


def _num(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


@router.get("/analysis")
def analysis(hours: int = Query(12, ge=1, le=72), source: str | None = None, symbol: str | None = None) -> dict:
    st = get_settings()
    source = source or st.engine_source
    symbol = symbol or st.mt5_symbol
    now = int(time.time())
    m1 = load_m1(source, symbol, now - HISTORY_DAYS * 86400, now + 60)
    m1 = m1[m1["ts"] + 60 <= now]
    base = {"source": source, "symbol": symbol, "generated_ts": now}
    if m1.empty:
        return {**base, "available": False, "message": "No bars stored for this source yet."}

    f = build_frame(m1)
    a = f.a
    n = len(a["ts"])
    start = max(0, n - hours * 12)
    idx = range(start, n)

    candles = [{"time": int(a["ts"][i]), "open": float(a["o"][i]), "high": float(a["h"][i]),
                "low": float(a["l"][i]), "close": float(a["c"][i])} for i in idx]

    def line(col):
        return [{"time": int(a["ts"][i]), "value": float(a[col][i])} for i in idx if _num(a[col][i]) is not None]

    fvgs = []
    for i in idx:
        for side in (1, -1):
            g = fvg(a, i, side)
            if g:
                fvgs.append({"time": int(a["ts"][i - 2]), "end_time": int(a["ts"][i]), "side": "bullish" if side == 1 else "bearish",
                             "low": float(g[0]), "high": float(g[1])})

    last = n - 1
    c15, e20, e50 = _num(a["close_15"][last]), _num(a["ema20_15"][last]), _num(a["ema50_15"][last])
    if None in (c15, e20, e50):
        bias = "UNKNOWN"
    elif c15 > e50 and e20 > e50:
        bias = "BULLISH"
    elif c15 < e50 and e20 < e50:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    last_m1_ts = int(m1["ts"].iloc[-1])
    return {
        **base,
        "available": True,
        "last_bar_ts": last_m1_ts,
        "stale": now - (last_m1_ts + 60) > 120,
        "last_price": float(m1["c"].iloc[-1]),
        "candles": candles,
        "ema20_15": line("ema20_15"),
        "ema50_15": line("ema50_15"),
        "vwap": line("vwap"),
        "levels": {"PDH": _num(a["pdh"][last]), "PDL": _num(a["pdl"][last]),
                   "ONH": _num(a["onh"][last]), "ONL": _num(a["onl"][last])},
        "fvgs": fvgs[-15:],
        "bias_15m": bias,
        "atr_5m": _num(a["atr"][last]),
    }
