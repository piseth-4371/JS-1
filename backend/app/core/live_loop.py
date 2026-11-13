"""Background loop: every 20 s, pull fresh bars from MT5 (demo) and run one engine cycle.

Only started when ENGINE_ENABLED=true in backend/.env, so tests and normal
development never touch MT5. Reading data only; no MT5 orders are ever sent.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.core.engine import TradingEngine
from app.core.sources.mt5_source import MT5Error, fetch_mt5_m1
from app.repository import save_bars

log = logging.getLogger("engine")
INTERVAL = 20


def _pull_bars() -> str:
    s = get_settings()
    end = datetime.now(timezone.utc)
    bars, source = fetch_mt5_m1(s.mt5_symbol, end - timedelta(hours=3), end, s.mt5_server_tz, s.mt5_terminal_path)
    save_bars(bars)
    return source


async def run_forever(engine: TradingEngine) -> None:
    await asyncio.to_thread(engine.startup)
    while True:
        try:
            await asyncio.to_thread(_pull_bars)
        except MT5Error as e:
            log.warning("MT5: %s", e)          # the engine will report stale data
        except Exception:
            log.exception("bar download failed")
        try:
            res = await asyncio.to_thread(engine.cycle)
            log.info("cycle: %s %s", res.status, res.detail)
        except Exception:
            log.exception("engine cycle failed")   # one bad cycle never stops the loop
        await asyncio.sleep(INTERVAL)
