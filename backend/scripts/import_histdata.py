"""Import HistData.com NSXUSD M1 zip files into the database (source "histdata").

Put the downloaded zips (e.g. HISTDATA_COM_ASCII_NSXUSD_M1_2019.zip) in backend\\data\\histdata\\ then:
  .\\.venv\\Scripts\\python scripts\\import_histdata.py

Bars from 2025 onward are NEVER imported: that period is the locked out-of-sample test.
Bad candles are reported and the whole file is skipped (nothing half-saved).
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.market_data import validate_bars  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.repository import count_bars, init_db, save_bars  # noqa: E402

OOS_START = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
DEFAULT_DIR = Path(__file__).resolve().parent.parent / "data" / "histdata"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("folder", nargs="?", type=Path, default=None)
    p.add_argument("--pair", default="nsxusd", help="nsxusd (Nasdaq-100) or xauusd (gold)")
    a = p.parse_args()
    inst = a.pair.upper()
    a.folder = a.folder or (DEFAULT_DIR if a.pair == "nsxusd" else DEFAULT_DIR / a.pair)
    zips = sorted(a.folder.glob("*.zip"))
    if not zips:
        print(f"No .zip files in {a.folder}")
        return 1
    init_db()
    for z in zips:
        bars = hd.read_zip(z, inst)
        dropped = sum(b.ts >= OOS_START for b in bars)
        bars = [b for b in bars if b.ts < OOS_START]
        rep = validate_bars(bars)
        if not rep.ok:
            print(f"{z.name}: validation failed, NOT saved: {rep.errors[:3]}")
            continue
        save_bars(bars)
        first = datetime.fromtimestamp(bars[0].ts, timezone.utc) if bars else None
        last = datetime.fromtimestamp(bars[-1].ts, timezone.utc) if bars else None
        print(f"{z.name}: {len(bars):,} bars saved ({first:%Y-%m-%d} -> {last:%Y-%m-%d} UTC)"
              + (f"; {dropped:,} bars from 2025+ skipped (locked)" if dropped else ""))
    n, first, last = count_bars(hd.SOURCE, inst)
    fmt = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if t else "-"  # noqa: E731
    print(f"Database now has {n:,} {inst} M1 bars from {hd.SOURCE}: {fmt(first)} -> {fmt(last)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
