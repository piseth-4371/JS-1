"""Download Dukascopy USATECHIDXUSD 1-minute BID and ASK candles for the bid/ask re-test
(docs/bidask_retest_preregistration.md). Polite and resumable: days already stored are skipped, a rate
limit (HTTP 503) makes it wait, and every day is validated and saved as soon as it arrives.

    .\\.venv\\Scripts\\python scripts\\download_dukascopy_bidask.py                      (2022-12-01 .. 2023-12-31)
    .\\.venv\\Scripts\\python scripts\\download_dukascopy_bidask.py --start 2023-01-01 --end 2023-02-01

Never downloads 2025 or later.
"""
import argparse
import random
import sys
import time
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.market_data import validate_bars  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.repository import init_db, save_bars  # noqa: E402


def days_present(symbol: str) -> set[int]:
    q = text("SELECT DISTINCT ts / 86400 FROM bars WHERE source=:s AND symbol=:y AND timeframe='M1'")
    with get_engine().connect() as c:
        return {int(r[0]) for r in c.execute(q, {"s": dk.SOURCE, "y": symbol})}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=date.fromisoformat, default=date(2022, 12, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2024, 1, 1), help="day after the last day")
    p.add_argument("--pause", type=float, default=6.0)
    a = p.parse_args()
    if a.end > date(2025, 1, 1):
        print("Refusing: 2025+ is the locked out-of-sample period.")
        return 1
    init_db()
    sched = dk.PoliteSchedule(a.pause)
    have = {"BID": days_present(dk.INSTRUMENT), "ASK": days_present(dk.ASK_SYMBOL)}
    todo = [(d, side) for d in dk.trading_days(a.start, a.end) for side in ("BID", "ASK")
            if (d - date(1970, 1, 1)).days not in have[side]]
    print(f"{len(todo)} day files to download ({a.start} .. {a.end}, BID and ASK)", flush=True)
    blocked_total = 0.0
    for k, (d, side) in enumerate(todo, 1):
        bars = None
        while bars is None:
            try:
                bars = dk.fetch_day(d, side=side)
            except dk.RateLimited as e:
                wait = sched.on_block()
                blocked_total += wait
                if blocked_total > 8 * 3600:
                    print("Blocked for 8 hours in total. Progress is saved; run the same command later.", flush=True)
                    return 1
                print(f"  {d} {side} rate-limited ({e}); waiting {wait / 60:.0f} min [{datetime.now():%H:%M}]", flush=True)
                time.sleep(wait)
            except ConnectionError as e:
                print(f"  {d} {side} network error ({e}); waiting 2 min [{datetime.now():%H:%M}]", flush=True)
                time.sleep(120)
        rep = validate_bars(bars)
        if not rep.ok:
            print(f"  {d} {side} validation failed, NOT saved: {rep.errors[:3]}", flush=True)
        else:
            save_bars(bars)
        if k % 20 == 0 or k == len(todo):
            print(f"  [{k}/{len(todo)}] {d} {side} {len(bars)} bars  [{datetime.now():%H:%M}]", flush=True)
        time.sleep(sched.on_success() * random.uniform(0.8, 1.3))
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
