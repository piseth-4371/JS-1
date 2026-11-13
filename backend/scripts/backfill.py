"""Download 1-minute bars and save them to the database.

Examples (from the backend folder):
  # Last 60 days from your MT5 demo terminal (must be open, demo account)
  .\\.venv\\Scripts\\python scripts\\backfill.py mt5 --days 60

  # Dukascopy history for backtesting (one file per day; takes a while)
  .\\.venv\\Scripts\\python scripts\\backfill.py dukascopy --start 2026-10-01 --end 2026-11-13

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
    p.add_argument("source", choices=["mt5", "dukascopy"])
    p.add_argument("--days", type=int, default=30, help="MT5: how many days back")
    p.add_argument("--start", type=date.fromisoformat, help="Dukascopy: first day (YYYY-MM-DD)")
    p.add_argument("--end", type=date.fromisoformat, help="Dukascopy: day after the last day")
    p.add_argument("--pause", type=float, default=3.0, help="Dukascopy: seconds to wait between days")
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
    else:
        from app.core.sources import dukascopy_source as dk

        if not a.start:
            print("ERROR: --start is required for dukascopy")
            return 1
        import time

        end_day = a.end or date.today()
        source, symbol = dk.SOURCE, dk.INSTRUMENT
        # Save day by day, so an interruption keeps everything downloaded so far.
        have = days_present(source, symbol)
        for d in dk.trading_days(a.start, end_day):
            if (date(d.year, d.month, d.day) - date(1970, 1, 1)).days in have:
                continue  # already downloaded earlier
            day_bars = None
            for attempt in range(1, 13):           # up to ~2 hours of waiting per blocked day
                try:
                    day_bars = dk.fetch_day(d)
                    break
                except ConnectionError as e:
                    print(f"  {d}  server busy/blocked ({e}); waiting 10 min (attempt {attempt}/12)", flush=True)
                    time.sleep(600)
            if day_bars is None:
                print("ERROR: still blocked after 2 hours. Progress is saved; run the same command later.")
                return 1
            report = validate_bars(day_bars)
            if not report.ok:
                print(f"  {d}  validation failed, NOT saved: {report.errors[:3]}")
                continue
            save_bars(day_bars)
            print(f"  {d}  {len(day_bars):>5} bars saved", flush=True)
            time.sleep(a.pause)  # be polite to the free server
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
