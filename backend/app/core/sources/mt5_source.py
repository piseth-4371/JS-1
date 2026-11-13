"""Read 1-minute bars from the MetaTrader 5 desktop terminal. READ-ONLY.

IMPORTANT time-zone fact (checked on 2026-11-13): MT5 bar times are in the
broker's SERVER time, not UTC. MetaQuotes-Demo was UTC+2 that day
(Eastern European Time, which becomes UTC+3 in summer). We convert using the
IANA zone in MT5_SERVER_TZ and double-check it against the live tick.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import wraps
from threading import Lock
from zoneinfo import ZoneInfo

from app.core.market_data import Bar


class MT5Error(RuntimeError):
    pass


_MT5_LOCK = Lock()


def _serialized_mt5(fn):
    """MT5's Python terminal connection is shared by the pull and preview threads."""
    @wraps(fn)
    def locked(*args, **kwargs):
        with _MT5_LOCK:
            return fn(*args, **kwargs)
    return locked


def server_to_utc(server_ts: int, server_tz: ZoneInfo) -> int:
    """MT5 'fake epoch' (server wall-clock written as if UTC) -> real UTC epoch."""
    wall = datetime.fromtimestamp(server_ts, timezone.utc).replace(tzinfo=None)
    return int(wall.replace(tzinfo=server_tz).timestamp())


def detect_server_offset_hours(mt5, symbol: str) -> float | None:
    """Offset (hours) between server clock and UTC, from the latest tick.

    Returns None if the last tick is old (market closed), because then we can't tell.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    now = datetime.now(timezone.utc).timestamp()
    diff = tick.time - now
    offset = round(diff / 3600 * 2) / 2  # nearest half hour
    if abs(diff - offset * 3600) > 600:  # tick older than 10 minutes
        return None
    return offset


def closed_m1(bars: list[Bar], observed_utc: datetime) -> list[Bar]:
    """Exclude the minute still forming at the time of the MT5 request."""
    cutoff = int(observed_utc.timestamp())
    return [bar for bar in bars if bar.ts + 60 <= cutoff]


def mt5_m5_preview(rate, tick, server_tz: ZoneInfo, now_ts: int, source: str, symbol: str) -> dict:
    """Convert the current MT5 M5 bar for display; never persist it for trading."""
    bar_ts = server_to_utc(int(rate["time"]), server_tz)
    tick_ts = server_to_utc(int(tick.time), server_tz)
    base = {"source": source, "symbol": symbol, "observed_ts": tick_ts,
            "stale": True, "available": False, "candle": None}
    if bar_ts != now_ts // 300 * 300:
        return {**base, "message": "No current five-minute candle from MT5."}
    age = now_ts - tick_ts
    return {
        **base,
        "available": True,
        "stale": age > 20 or age < -5,
        "candle": {"time": bar_ts, "open": float(rate["open"]), "high": float(rate["high"]),
                   "low": float(rate["low"]), "close": float(rate["close"])},
    }


@_serialized_mt5
def fetch_mt5_m1(symbol: str, start_utc: datetime, end_utc: datetime, server_tz_name: str, terminal_path: str | None = None) -> tuple[list[Bar], str]:
    """Return (bars, source_name). Raises MT5Error with a plain-English message on problems."""
    import MetaTrader5 as mt5  # imported here so tests/other code don't need MT5

    ok = mt5.initialize(terminal_path) if terminal_path else mt5.initialize()
    if not ok:
        raise MT5Error(f"Cannot connect to MT5 terminal: {mt5.last_error()}. Is it open and logged in?")
    try:
        acc = mt5.account_info()
        if acc is None:
            raise MT5Error("MT5 is open but no account is logged in.")
        if acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            raise MT5Error("MT5 is logged in to a REAL account. This project only reads from demo accounts.")
        if not mt5.symbol_select(symbol, True):
            raise MT5Error(f"Symbol {symbol} not available on {acc.server}.")

        server_tz = ZoneInfo(server_tz_name)
        live = detect_server_offset_hours(mt5, symbol)
        expected = datetime.now(server_tz).utcoffset().total_seconds() / 3600
        if live is not None and live != expected:
            raise MT5Error(
                f"MT5_SERVER_TZ={server_tz_name} means UTC{expected:+g}, but the live tick says UTC{live:+g}. "
                "Fix MT5_SERVER_TZ in .env before loading data."
            )

        # MT5 expects the range in server time too.
        def to_server(d: datetime) -> datetime:
            return d.astimezone(server_tz).replace(tzinfo=timezone.utc)

        bars: list[Bar] = []
        source = f"mt5:{acc.server}"
        # Ask in 30-day chunks: MT5 refuses ranges larger than its "Max bars in chart".
        cur = start_utc
        while cur < end_utc:
            nxt = min(cur + timedelta(days=30), end_utc)
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, to_server(cur), to_server(nxt))
            if rates is None:
                code, msg = mt5.last_error()
                raise MT5Error(f"copy_rates_range failed for {cur:%Y-%m-%d}..{nxt:%Y-%m-%d}: {code} {msg}")
            for r in rates:
                bars.append(
                    Bar(source, symbol, "M1", server_to_utc(int(r["time"]), server_tz),
                        float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]),
                        float(r["tick_volume"]))
                )
            cur = nxt
        # Drop any overlap between chunks and keep time order.
        uniq = {b.ts: b for b in bars}
        # MT5 also returns the current, unfinished M1 bar. Saving it with the
        # historical bars would freeze a partial OHLCV because inserts normally
        # ignore duplicate timestamps. Only finalized bars belong in the DB.
        return closed_m1([uniq[k] for k in sorted(uniq)], end_utc), source
    finally:
        mt5.shutdown()


@_serialized_mt5
def fetch_mt5_m5_preview(symbol: str, server_tz_name: str, terminal_path: str | None = None,
                         expected_source: str | None = None) -> dict:
    """Read the forming M5 candle from a demo terminal for display only."""
    import MetaTrader5 as mt5

    ok = mt5.initialize(terminal_path) if terminal_path else mt5.initialize()
    if not ok:
        raise MT5Error(f"Cannot connect to MT5 terminal: {mt5.last_error()}. Is it open and logged in?")
    try:
        acc = mt5.account_info()
        if acc is None:
            raise MT5Error("MT5 is open but no account is logged in.")
        if acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            raise MT5Error("MT5 is logged in to a REAL account. Preview requires a demo account.")
        source = f"mt5:{acc.server}"
        if expected_source and source != expected_source:
            raise MT5Error(f"MT5 source is {source}, but ENGINE_SOURCE is {expected_source}.")
        if not mt5.symbol_select(symbol, True):
            raise MT5Error(f"Symbol {symbol} not available on {acc.server}.")
        server_tz = ZoneInfo(server_tz_name)
        live = detect_server_offset_hours(mt5, symbol)
        expected = datetime.now(server_tz).utcoffset().total_seconds() / 3600
        if live is not None and live != expected:
            raise MT5Error(
                f"MT5_SERVER_TZ={server_tz_name} means UTC{expected:+g}, but the live tick says UTC{live:+g}. "
                "Fix MT5_SERVER_TZ in .env before loading data."
            )
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5Error(f"No tick for {symbol} from MT5.")
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1)
        if rates is None or len(rates) == 0:
            raise MT5Error(f"No M5 candle for {symbol} from MT5: {mt5.last_error()}")
        return mt5_m5_preview(rates[0], tick, server_tz, int(datetime.now(timezone.utc).timestamp()), source, symbol)
    finally:
        mt5.shutdown()
