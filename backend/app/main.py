"""FastAPI entry point.

Run (from the backend folder):
    .\\.venv\\Scripts\\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import FastAPI, Query

from app.api_market import router as market_router
from app.api_trading import router as trading_router
from app.config import get_settings
from app.core.market_data import is_stale, resample
from app.db import check_database
from app.repository import init_db, load_bars


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    task = None
    s = get_settings()
    if s.engine_enabled:
        from app.core.engine import TradingEngine
        from app.core.live_loop import run_forever

        engine = TradingEngine(s.engine_source, s.mt5_symbol, s.starting_balance)
        task = asyncio.create_task(run_forever(engine))
    yield
    if task:
        task.cancel()


app = FastAPI(title="NAS100 AI Trading Control Center", version="0.4.0", lifespan=lifespan)
app.include_router(trading_router)
app.include_router(market_router)


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    db_ok = check_database()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "trading_mode": settings.trading_mode,  # always "paper"
        "live_trading_available": False,
        "symbol": settings.mt5_symbol,
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
    }


@app.get("/api/market/bars")
def market_bars(
    source: str = Query(..., description='e.g. "mt5:MetaQuotes-Demo" or "dukascopy"'),
    symbol: str = Query(..., description='e.g. "USTEC" or "USATECHIDXUSD"'),
    tf: Literal["M1", "M5", "M15"] = "M5",
    hours: int = Query(24, ge=1, le=24 * 30),
) -> dict:
    """Stored candles for the chart. Every response says where the data came from."""
    now = datetime.now(timezone.utc)
    start = int((now - timedelta(hours=hours)).timestamp())
    m1 = load_bars(source, symbol, "M1", start, int(now.timestamp()) + 60)
    bars = m1 if tf == "M1" else resample(m1, int(tf[1:]))
    return {
        "source": source,
        "symbol": symbol,
        "timeframe": tf,
        "count": len(bars),
        "last_bar_utc": bars[-1].dt_utc.isoformat() if bars else None,
        "stale": is_stale(m1[-1].ts, now) if m1 else True,
        "bars": [{"t": b.ts, "o": b.open, "h": b.high, "l": b.low, "c": b.close, "v": b.volume} for b in bars],
    }
