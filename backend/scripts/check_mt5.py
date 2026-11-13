"""Day 1 check: can Python read USTEC from your MT5 terminal?

READ-ONLY. This script never places, changes or closes orders.

Before running:
  1. Open MetaTrader 5 and log in to your Exness **demo** account.
  2. Make sure USTEC is visible in Market Watch (right-click > Symbols).

Run (from the backend folder):
  .\\.venv\\Scripts\\python scripts\\check_mt5.py
"""
from datetime import datetime, timedelta, timezone
import os
import sys

import MetaTrader5 as mt5

SYMBOL = os.getenv("MT5_SYMBOL", "USTEC")
BALANCE = float(os.getenv("STARTING_BALANCE", "10"))
RISK_PCT = 0.5


def main() -> int:
    path = os.getenv("MT5_TERMINAL_PATH")
    ok = mt5.initialize(path) if path else mt5.initialize()
    if not ok:
        print("Could not connect to MT5:", mt5.last_error())
        print("Is the MetaTrader 5 terminal open and logged in?")
        return 1

    try:
        acc = mt5.account_info()
        if acc is None:
            print("Connected, but no account is logged in.")
            return 1
        is_demo = acc.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        print(f"Server: {acc.server}   Demo: {is_demo}   Currency: {acc.currency}")
        if not is_demo:
            print("WARNING: this is NOT a demo account. This project only supports demo/paper.")
            print("Please log in to a demo account and run again.")
            return 2

        if not mt5.symbol_select(SYMBOL, True):
            print(f"Symbol {SYMBOL} not found on this account. Error: {mt5.last_error()}")
            print("Cent accounts usually do not offer indices - use a Standard demo account.")
            return 1

        s = mt5.symbol_info(SYMBOL)
        print(f"\n--- {SYMBOL} contract specification (from the broker) ---")
        print(f"digits={s.digits}  point={s.point}  tick_size={s.trade_tick_size}  tick_value={s.trade_tick_value}")
        print(f"contract_size={s.trade_contract_size}  min_lot={s.volume_min}  lot_step={s.volume_step}  max_lot={s.volume_max}")
        print(f"current spread={s.spread} points  bid={s.bid}  ask={s.ask}")

        # Money per 1.0 index point for the minimum lot
        value_per_point = s.trade_tick_value / s.trade_tick_size * s.volume_min
        allowed = BALANCE * RISK_PCT / 100
        print(f"\n--- Risk check for a {BALANCE:g} {acc.currency} account at {RISK_PCT}% risk ---")
        print(f"Allowed risk per trade: {allowed:.4f} {acc.currency}")
        print(f"Min lot ({s.volume_min}) moves {value_per_point:.4f} {acc.currency} per index point")
        for stop_pts in (10, 20, 30, 40):
            risk = value_per_point * stop_pts
            verdict = "OK" if risk <= allowed else "REJECT"
            print(f"  stop {stop_pts:>3} pts -> risk {risk:.4f}  ({risk / BALANCE * 100:.2f}% of balance)  {verdict}")
        print(f"Largest stop allowed at min lot: {allowed / value_per_point:.1f} index points")

        # How much 1-minute history can we get?
        print("\n--- M1 history depth ---")
        now = datetime.now(timezone.utc)
        for days in (30, 180, 365, 365 * 3):
            rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M1, now - timedelta(days=days), now)
            n = 0 if rates is None else len(rates)
            first = datetime.fromtimestamp(rates[0]["time"], timezone.utc).date() if n else "-"
            print(f"  last {days:>4} days: {n:>8} bars, earliest {first}")
        print("\nSource: MT5 terminal (broker data). Timestamps are UTC.")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
