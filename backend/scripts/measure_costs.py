"""Measure the real USTEC spread from the MT5 demo terminal (READ-ONLY: never places orders).

MT5 stores a spread for every 1-minute bar. This script reads the last ~60 days of M1 bars,
converts the spread to index points and reports it by New York time window, so the
backtest's cost assumption (spread 1.5 + slippage 0.5 = 2.0 points) can be checked.

  .\\.venv\\Scripts\\python scripts\\measure_costs.py

Notes: the per-bar spread is what the terminal recorded for that minute; quick spikes inside a
minute may be higher. This measures the broker the terminal is logged in to (check the
"Server" line): another broker (e.g. Exness) can have different spreads.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.core.sources.mt5_source import server_to_utc  # noqa: E402

NY = ZoneInfo("America/New_York")
ASSUMED_SPREAD = 1.5
WINDOWS = [  # (label, NY minute-of-day from, to) - bar START times
    ("London 03:00-05:00 NY (London strategies)", 3 * 60, 5 * 60),
    ("Pre-open 08:00-09:30 NY", 8 * 60, 9 * 60 + 30),
    ("Open 09:30-09:45 NY (ORB range)", 9 * 60 + 30, 9 * 60 + 45),
    ("NY entries 09:45-11:30 NY", 9 * 60 + 45, 11 * 60 + 30),
    ("Midday 11:30-15:00 NY", 11 * 60 + 30, 15 * 60),
    ("All weekday hours 03:00-15:55 NY", 3 * 60, 15 * 60 + 55),
]


def main() -> int:
    import MetaTrader5 as mt5

    st = get_settings()
    ok = mt5.initialize(st.mt5_terminal_path) if st.mt5_terminal_path else mt5.initialize()
    if not ok:
        print("Could not connect to MT5:", mt5.last_error(), "- is the terminal open and logged in?")
        return 1
    try:
        acc = mt5.account_info()
        if acc is None or acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("Please log in to a DEMO account (this project never touches real accounts).")
            return 2
        sym = st.mt5_symbol
        info = mt5.symbol_info(sym)
        if info is None:
            print(f"Symbol {sym} not available on {acc.server}")
            return 1
        now = datetime.now(timezone.utc)
        rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M1, now - timedelta(days=60), now)
        if rates is None or len(rates) == 0:
            print("No M1 history:", mt5.last_error())
            return 1
        tz = ZoneInfo(st.mt5_server_tz)
        ts = np.array([server_to_utc(int(t), tz) for t in rates["time"]])
        spread_pts = rates["spread"].astype(float) * info.point          # MT5 points -> index points
        ny = [datetime.fromtimestamp(t, NY) for t in ts]
        mod = np.array([d.hour * 60 + d.minute for d in ny])
        wd = np.array([d.weekday() for d in ny])

        first, last = ny[0], ny[-1]
        print(f"Source: MT5 {acc.server} {sym} (demo), {len(ts):,} M1 bars "
              f"{first:%Y-%m-%d %H:%M} -> {last:%Y-%m-%d %H:%M} NY, measured {now:%Y-%m-%d %H:%M} UTC")
        print(f"Point size {info.point}; spread right now {info.spread * info.point:.2f} index points\n")
        print(f"{'window':<44}{'bars':>8}{'median':>8}{'mean':>8}{'p90':>8}{'p99':>8}")
        for label, a, b in WINDOWS:
            m = (wd < 5) & (mod >= a) & (mod < b)
            x = spread_pts[m]
            if len(x) == 0:
                print(f"{label:<44}{0:>8}")
                continue
            print(f"{label:<44}{len(x):>8}{np.median(x):>8.2f}{x.mean():>8.2f}"
                  f"{np.percentile(x, 90):>8.2f}{np.percentile(x, 99):>8.2f}")
        print(f"\nBacktest assumption: spread {ASSUMED_SPREAD} + slippage 0.5 = 2.0 index points per round trip.")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
