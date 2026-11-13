"""Strategy 1 — NY Trend-FVG v1 (ICT): trend + pullback into a Fair Value Gap.

Rules (frozen):
- Bias from the last completed 15m bar: close > EMA50 and EMA20 > EMA50 -> long (mirror short)
- Bar closes 09:45-11:30 New York
- FVG with displacement (c2 body >= 1.0 ATR), gap >= 0.15 ATR, close on the bias side of VWAP
- ATR between its 10th and 95th percentile of the last ~20 days
- Limit at the FVG midpoint (consequent encroachment), valid 6 bars, cancelled if a bar closes beyond the gap
- Stop = c1 extreme -/+ 0.10 ATR; stop distance must be 0.5-2.0 ATR; target 2R
"""
from app.core.strategies.base import BAR, Order, Strategy, fvg, valid, window


class TrendFVG(Strategy):
    name = "trend_fvg"
    clock, start, end, vwap_key = "mod", 9 * 60 + 45, 11 * 60 + 30, "vwap"   # NY 09:45-11:30, NY VWAP

    def in_window(self, i, a) -> bool:
        return window(a, i, self.start, self.end, self.clock)

    def on_bar(self, i, a):
        if not self.in_window(i, a):
            return None
        c, atr = a["c"][i], a["atr"][i]
        e20, e50, c15, vwap = a["ema20_15"][i], a["ema50_15"][i], a["close_15"][i], a[self.vwap_key][i]
        if not valid(atr, e20, e50, c15, vwap, a["atr_q10"][i], a["atr_q95"][i]):
            return None
        if not (a["atr_q10"][i] <= atr <= a["atr_q95"][i]):
            return None
        if c15 > e50 and e20 > e50:
            side = 1
        elif c15 < e50 and e20 < e50:
            side = -1
        else:
            return None
        if (c - vwap) * side <= 0:
            return None
        g = fvg(a, i, side)
        if g is None:
            return None
        lo, hi, extreme = g
        entry = (lo + hi) / 2
        stop = extreme - side * 0.10 * atr
        risk = (entry - stop) * side
        if not (0.5 * atr <= risk <= 2.0 * atr):
            return None
        return Order(self.name, side, "limit", entry, stop, entry + side * self.rr * risk, self.rr,
                     placed_ts=a["close_ts"][i], expiry_ts=a["close_ts"][i] + 6 * BAR,
                     cancel_level=lo if side == 1 else hi,
                     reason="Trend + pullback into displacement FVG")


class LondonTrendFVG(TrendFVG):
    """Same rules, London session: bars closing 08:15-10:00 London time, London VWAP (from 08:00 London)."""
    name = "london_trend_fvg"
    clock, start, end, vwap_key = "lmod", 8 * 60 + 15, 10 * 60, "lvwap"


class BTCWeekendTrendFVG(TrendFVG):
    """BTCUSDT weekend book (Binance data). Same trend + FVG rules on 5m/15m bars, but:
    - entries only on weekends: bars closing Fri 17:00 NY .. Sun 15:30 NY (flat at Sun 17:00)
    - VWAP = UTC-day VWAP (crypto trades 24/7; there is no cash session)
    """
    name = "btc_weekend_trend_fvg"
    vwap_key = "dvwap"

    def in_window(self, i, a) -> bool:
        wd, close_min = a["weekday"][i], a["mod"][i] + 5
        return (wd == 4 and close_min >= 17 * 60) or wd == 5 or (wd == 6 and close_min <= 15 * 60 + 30)
