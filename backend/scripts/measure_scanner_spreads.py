"""Read-only spread observations for NAS100/gold demo bars and a public BTC quote.
Run from backend: .\\.venv\\Scripts\\python scripts/measure_scanner_spreads.py
No orders, credentials, or automatic changes to research assumptions.
"""
import json
import math
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from app.config import get_settings
from app.core.cost_observations import OBSERVATIONS, read_observations
from app.core.sources.mt5_source import server_to_utc
from zoneinfo import ZoneInfo


def main() -> int:
    values = read_observations()
    now = int(datetime.now(timezone.utc).timestamp())
    settings = get_settings()
    try:
        import MetaTrader5 as mt5
        try:
            ok = mt5.initialize(settings.mt5_terminal_path) if settings.mt5_terminal_path else mt5.initialize()
            if not ok:
                raise RuntimeError("MT5 terminal unavailable")
            acc = mt5.account_info()
            if acc is None or acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
                raise RuntimeError("A demo account is required")
            for market, symbol in (("nas100", settings.mt5_symbol), ("gold", settings.mt5_gold_symbol)):
                if not mt5.symbol_select(symbol, True):
                    print(f"{market}: symbol unavailable")
                    continue
                info = mt5.symbol_info(symbol)
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 1, 10000)
                if info is None or rates is None or len(rates) == 0:
                    print(f"{market}: no history available")
                    continue
                timestamps = np.array([server_to_utc(int(t), ZoneInfo(settings.mt5_server_tz)) for t in rates["time"]])
                dates = [datetime.fromtimestamp(int(t), ZoneInfo("America/New_York")) for t in timestamps]
                mask = np.array([d.weekday() < 5 and 180 <= d.hour * 60 + d.minute < 955 for d in dates])
                mask &= timestamps + 60 <= now
                spreads = rates["spread"].astype(float) * info.point
                mask &= np.isfinite(spreads) & (spreads >= 0)
                if not mask.any():
                    print(f"{market}: no closed bars in scanner hours")
                    continue
                values[market] = {"source": f"mt5:{acc.server}", "symbol": symbol,
                                  "observed_ts": now, "last_quote_ts": int(timestamps[mask].max()),
                                  "sample_count": int(mask.sum()), "kind": "minute spread history, scanner hours",
                                  "median_spread": float(np.median(spreads[mask])),
                                  "p90_spread": float(np.percentile(spreads[mask], 90)),
                                  "unit": "price points"}
                print(f"{market}: {int(mask.sum())} observations, median spread {np.median(spreads[mask]):.4f}")
        finally:
            mt5.shutdown()
    except Exception as exc:
        print(f"MT5 observation unavailable ({type(exc).__name__}); existing observations retained.")
    try:
        url = "https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=BTCUSDT"
        with urllib.request.urlopen(url, timeout=10) as response:
            quote = json.load(response)
        bid, ask = float(quote["bidPrice"]), float(quote["askPrice"])
        if not (math.isfinite(bid) and math.isfinite(ask) and 0 < bid <= ask):
            raise ValueError("Invalid quote")
        values["btc"] = {"source": "binance public bookTicker", "symbol": "BTCUSDT",
                         "observed_ts": now, "last_quote_ts": None, "sample_count": 1,
                         "kind": "single quote; exchange timestamp unavailable",
                         "median_spread": ask - bid, "p90_spread": None,
                         "spread_pct": (ask - bid) / ((ask + bid) / 2) * 100, "unit": "USDT"}
        print(f"btc: single observed spread {ask - bid:.4f} USDT; not a typical-cost estimate")
    except Exception as exc:
        print(f"BTC observation unavailable ({type(exc).__name__}); existing observations retained.")
    OBSERVATIONS.parent.mkdir(parents=True, exist_ok=True)
    temporary = OBSERVATIONS.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, indent=2), encoding="utf-8")
    temporary.replace(OBSERVATIONS)
    print("Slippage and fees remain assumptions. Spread observations do not change qualification or costs.")
    return 0 if any(x.get("observed_ts") == now for x in values.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
