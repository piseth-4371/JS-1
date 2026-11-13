"""Background loops: every 20 s, pull fresh bars and run one engine cycle per book.

    NAS100 book: bars from MT5 (demo terminal must be open)
    BTC book:    bars from Binance PUBLIC market data (no account, no key)

Both loops run all the time; each engine only trades inside its own window
(NAS100 weekdays, BTC weekends), which is the weekend "auto-switch".
Only started when ENGINE_ENABLED=true. Reading data only; no orders are ever
sent to MT5 or Binance - all trading is internal paper trading.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.config import get_settings
from app.core.engine import HISTORY_DAYS, TradingEngine
from app.core.sources import binance_source as bn
from app.core.sources.mt5_source import MT5Error, fetch_mt5_m1
from app.repository import save_bars

log = logging.getLogger("engine")
INTERVAL = 20


def _pull_bars() -> str:
    s = get_settings()
    end = datetime.now(timezone.utc)
    bars, source = fetch_mt5_m1(s.mt5_symbol, end - timedelta(hours=3), end, s.mt5_server_tz, s.mt5_terminal_path)
    # Refresh the recent closed window as well as inserting new minutes. Older
    # versions could freeze an unfinished MT5 minute on first sight; upserting
    # its finalized value repairs those rows while the loop runs.
    save_bars(bars, update_existing=True)
    return source


def _pull_btc() -> str:
    end = datetime.now(timezone.utc)
    save_bars(bn.fetch_m1(end - timedelta(hours=3), end))
    return bn.SOURCE


def _btc_history() -> None:
    """Make sure the BTC engine has ~30 days of history (needed for ATR percentiles / EMA50)."""
    # ~45 small requests at startup; bars already stored are skipped, so gaps get filled.
    end = datetime.now(timezone.utc)
    save_bars(bn.fetch_m1(end - timedelta(days=HISTORY_DAYS + 1), end))


async def run_forever(engine: TradingEngine, pull: Callable[[], str] | None = None,
                      prepare: Callable[[], None] | None = None) -> None:
    pull = pull or _pull_bars                  # looked up at call time (tests replace it)
    key = getattr(getattr(engine, "market", None), "key", "engine")
    if prepare:
        try:
            await asyncio.to_thread(prepare)
        except Exception:
            log.exception("history download failed (will keep trying with recent bars)")
    await asyncio.to_thread(engine.startup)
    while True:
        try:
            await asyncio.to_thread(pull)
        except MT5Error as e:
            log.warning("MT5: %s", e)          # the engine will report stale data
        except Exception:
            log.exception("bar download failed")
        try:
            res = await asyncio.to_thread(engine.cycle)
            log.info("%s cycle: %s %s", key, res.status, res.detail)
        except Exception:
            log.exception("engine cycle failed")   # one bad cycle never stops the loop
        await asyncio.sleep(INTERVAL)
