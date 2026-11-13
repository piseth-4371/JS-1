"""Strategy 4 — VWAP mean reversion (counter-trend).

Rules:
- Bars closing 10:00-15:00 New York
- Price stretched: close at least 2.0 ATR away from session VWAP
- Turn candle: closes back toward VWAP (bullish candle below VWAP -> long; bearish above -> short)
- Market order next minute; stop = candle extreme -/+ 0.25 ATR (at least 0.5 ATR away); target 2R
- After a signal, wait 6 bars before the next one
"""
from app.core.strategies.base import BAR, Order, Strategy, btc_weekend, valid, window


class VWAPReversion(Strategy):
    name = "vwap_reversion"
    vwap_key = "vwap"

    def new_day(self, day):
        self.last_signal = -10**9

    def in_window(self, i, a) -> bool:
        return window(a, i, 10 * 60, 15 * 60)

    def on_bar(self, i, a):
        if i - self.last_signal < 6 or not self.in_window(i, a):
            return None
        o, h, l, c, atr, vwap = a["o"][i], a["h"][i], a["l"][i], a["c"][i], a["atr"][i], a[self.vwap_key][i]
        if not valid(atr, vwap) or atr <= 0:
            return None
        dev = (c - vwap) / atr
        if dev <= -2.0 and c > o:
            side, stop = 1, min(l - 0.25 * atr, c - 0.5 * atr)
        elif dev >= 2.0 and c < o:
            side, stop = -1, max(h + 0.25 * atr, c + 0.5 * atr)
        else:
            return None
        self.last_signal = i
        return Order(self.name, side, "market", c, stop, None, self.rr,
                     placed_ts=a["close_ts"][i], expiry_ts=a["close_ts"][i] + BAR,
                     reason=f"{abs(dev):.1f} ATR away from VWAP, turning back")


class BTCWeekendVWAPReversion(VWAPReversion):
    """Same rules on BTCUSDT weekends (Fri 17:00 - Sun 15:30 NY), UTC-day VWAP."""
    name = "btc_weekend_vwap_reversion"
    vwap_key = "dvwap"

    def in_window(self, i, a) -> bool:
        return btc_weekend(a, i)
