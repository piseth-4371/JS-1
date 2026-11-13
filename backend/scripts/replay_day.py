"""REPLAY a past trading day through the REAL engine, minute by minute.

It copies the stored bars into a separate database (data/replay.db), so your
real paper account is never touched. Then it calls engine.cycle() once per
minute, exactly as the live loop would, and prints what happened.

  .\\.venv\\Scripts\\python scripts\\replay_day.py --day 2026-11-12
  .\\.venv\\Scripts\\python scripts\\replay_day.py --day 2026-11-12 --strategy orb --balance 1000

--balance only changes the replay account. With $10 every trade is rejected (min lot).
"""
import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
NY = ZoneInfo("America/New_York")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--day", type=date.fromisoformat, required=True, help="New York date to replay")
    p.add_argument("--strategy", default="trend_fvg")
    p.add_argument("--source", default="mt5:MetaQuotes-Demo")
    p.add_argument("--symbol", default="USTEC")
    p.add_argument("--balance", type=float, default=10.0)
    a = p.parse_args()

    from app import config, db
    from app.core.engine import HISTORY_DAYS
    from app.core.features import load_m1
    from app.core.market_data import Bar

    start = int(datetime(a.day.year, a.day.month, a.day.day, 0, 0, tzinfo=NY).timestamp())
    end = start + 86400
    src = load_m1(a.source, a.symbol, start - HISTORY_DAYS * 86400, end)
    if src[(src.ts >= start) & (src.ts < end)].empty:
        print(f"No {a.source} bars stored for {a.day}.")
        return 1

    # Switch to a throwaway database.
    replay_db = ROOT / "data" / "replay.db"
    replay_db.unlink(missing_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{replay_db}"
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()

    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.core import state
    from app.core.engine import TradingEngine
    from app.models import EventRow, PositionRow, SignalRow
    from app.repository import init_db, save_bars

    init_db()
    # Minutes before 08:30 NY are loaded as history; 08:30-16:10 is replayed minute by minute.
    replay_from = start + (8 * 60 + 30) * 60
    replay_to = start + (16 * 60 + 10) * 60
    hist = src[src.ts < replay_from]
    save_bars([Bar(a.source, a.symbol, "M1", int(r.ts), r.o, r.h, r.l, r.c, r.v) for r in hist.itertuples()])
    day = src[(src.ts >= replay_from) & (src.ts < replay_to)]
    with Session(db.get_engine()) as s, s.begin():
        state.put(s, "active_strategy", a.strategy)
        state.put(s, "auto_trading", True)

    engine = TradingEngine(a.source, a.symbol, a.balance)
    engine.startup(start)
    print(f"REPLAY {a.day} | strategy {a.strategy} | balance ${a.balance:g} | {len(day)} minutes | source {a.source}")
    counts = {}
    for r in day.itertuples():
        save_bars([Bar(a.source, a.symbol, "M1", int(r.ts), r.o, r.h, r.l, r.c, r.v)])
        res = engine.cycle(int(r.ts) + 65)        # 5 s after that minute closed
        counts[res.status] = counts.get(res.status, 0) + 1
        if res.status in ("ORDER", "REJECTED"):
            print(f"  {datetime.fromtimestamp(r.ts + 60, NY):%H:%M} NY  {res.status:<8} {res.detail}")

    with Session(db.get_engine()) as s:
        sigs = s.scalars(select(SignalRow)).all()
        pos = s.scalars(select(PositionRow)).all()
        errors = s.scalars(select(EventRow).where(EventRow.level == "ERROR")).all()
        print(f"\nCycles: {counts}")
        print(f"Signals: {len(sigs)} (actionable {sum(x.action != 'WAIT' for x in sigs)})")
        for x in pos:
            print(f"  trade {x.strategy} {'LONG' if x.side == 1 else 'SHORT'} entry {x.entry:.2f} exit {x.exit_price} "
                  f"({x.exit_reason}) {x.r if x.r is None else round(x.r, 2)} R, ${x.pnl_usd if x.pnl_usd is None else round(x.pnl_usd, 2)}")
        print(f"Open positions at end: {sum(x.status == 'open' for x in pos)}   ERROR events: {len(errors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
