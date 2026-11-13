"""Download 1-minute bars and save them to the database.

Examples (from the backend folder):
  # Last 60 days from your MT5 demo terminal (must be open, demo account)
  .\\.venv\\Scripts\\python scripts\\backfill.py mt5 --days 60

  # Dukascopy history for backtesting (one file per day; takes a while)
  .\\.venv\\Scripts\\python scripts\\backfill.py dukascopy --start 2026-10-01 --end 2026-11-13

  # Bitcoin (BTCUSDT) from Binance public data, for the weekend book (fast, no account)
  .\\.venv\\Scripts\\python scripts\\backfill.py binance --start 2019-01-01

Running the same command twice is safe: duplicates are skipped.
"""
import argparse
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.core.market_data import validate_bars  # noqa: E402
from app.repository import count_bars, days_present, init_db, save_bars  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source", choices=["mt5", "dukascopy", "binance"])
    p.add_argument("--days", type=int, default=30, help="MT5: how many days back")
    p.add_argument("--start", type=date.fromisoformat, help="Dukascopy: first day (YYYY-MM-DD)")
    p.add_argument("--end", type=date.fromisoformat, help="Dukascopy: day after the last day")
    p.add_argument("--pause", type=float, default=6.0, help="Dukascopy: normal seconds between days (grows after blocks)")
    a = p.parse_args()

    settings = get_settings()
    init_db()

    if a.source == "mt5":
        from app.core.sources.mt5_source import MT5Error, fetch_mt5_m1

        end = datetime.now(timezone.utc)
        try:
            bars, source = fetch_mt5_m1(settings.mt5_symbol, end - timedelta(days=a.days), end,
                                        settings.mt5_server_tz, settings.mt5_terminal_path)
        except MT5Error as e:
            print("ERROR:", e)
            return 1
        symbol = settings.mt5_symbol
    elif a.source == "binance":
        from app.core.sources import binance_source as bn

        if not a.start:
            print("ERROR: --start is required for binance")
            return 1
        source, symbol = bn.SOURCE, bn.SYMBOL
        have = days_present(source, symbol)
        day = a.start
        end_day = a.end or date.today() + timedelta(days=1)
        while day < end_day:
            chunk_end = min(day + timedelta(days=7), end_day)
            days = [(day + timedelta(days=k) - date(1970, 1, 1)).days for k in range((chunk_end - day).days)]
            if all(d in have for d in days) and chunk_end < date.today():
                day = chunk_end
                continue
            s0 = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            s1 = datetime(chunk_end.year, chunk_end.month, chunk_end.day, tzinfo=timezone.utc)
            try:
                week = bn.fetch_m1(s0, min(s1, datetime.now(timezone.utc)))
            except bn.BinanceError as e:
                print("ERROR:", e, "- progress is saved; run the same command again later.")
                return 1
            report = validate_bars(week)
            if not report.ok:
                print(f"  {day}  validation failed, NOT saved: {report.errors[:3]}")
            else:
                save_bars(week)
                print(f"  {day} .. {chunk_end}  {len(week):>6} bars saved", flush=True)
            day = chunk_end
        n, first, last = count_bars(source, symbol)
        fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "-"  # noqa: E731
        print(f"Database now has {n} {symbol} M1 bars from {source}: {fmt(first)} -> {fmt(last)}")
        return 0
    else:
        from app.core.sources import dukascopy_source as dk

        if not a.start:
            print("ERROR: --start is required for dukascopy")
            return 1
        import random
        import time

        end_day = a.end or date.today()
        sched = dk.PoliteSchedule(a.pause)
        source, symbol = dk.SOURCE, dk.INSTRUMENT
        # Save day by day, so an interruption keeps everything downloaded so far.
        have = days_present(source, symbol)
        for d in dk.trading_days(a.start, end_day):
            if (date(d.year, d.month, d.day) - date(1970, 1, 1)).days in have:
                continue  # already downloaded earlier
            day_bars = None
            waited = 0.0
            while day_bars is None:
                try:
                    day_bars = dk.fetch_day(d)
                except dk.RateLimited as e:
                    wait = sched.on_block()
                    waited += wait
                    if waited > 6 * 3600:
                        print("ERROR: blocked for 6 hours. Progress is saved; run the same command later.")
                        return 1
                    print(f"  {d}  rate-limited ({e}); waiting {wait / 60:.0f} min, then pause {sched.pause:.0f}s "
                          f"between days  [{datetime.now():%H:%M}]", flush=True)
                    time.sleep(wait)
                except ConnectionError as e:
                    print(f"  {d}  network error ({e}); waiting 2 min  [{datetime.now():%H:%M}]", flush=True)
                    time.sleep(120)
            report = validate_bars(day_bars)
            if not report.ok:
                print(f"  {d}  validation failed, NOT saved: {report.errors[:3]}")
                continue
            save_bars(day_bars)
            print(f"  {d}  {len(day_bars):>5} bars saved", flush=True)
            time.sleep(sched.on_success() * random.uniform(0.8, 1.3))  # polite, slightly irregular
        n, first, last = count_bars(source, symbol)
        fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "-"  # noqa: E731
        print(f"Database now has {n} {symbol} M1 bars from {source}: {fmt(first)} -> {fmt(last)}")
        return 0

    report = validate_bars(bars)
    print(f"Downloaded {report.total} bars from {source}")
    if not report.ok:
        print("Validation problems (nothing saved):")
        for e in report.errors:
            print("  -", e)
        return 2

    save_bars(bars)
    n, first, last = count_bars(source, symbol)
    fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "-"  # noqa: E731
    print(f"Database now has {n} {symbol} M1 bars from {source}: {fmt(first)} -> {fmt(last)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
