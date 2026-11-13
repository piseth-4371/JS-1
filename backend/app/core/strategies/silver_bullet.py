"""Strategy 5 — ICT Silver Bullet (10:00-11:00 New York).

Rules:
- Liquidity levels: PDH/PDL, ONH/ONL, and (after 10:00) the 09:30-10:00 high/low
- Track the most recent sweep since 09:30 (trade beyond a level, close back inside):
    swept a high -> look for shorts; swept a low -> look for longs
- In bars closing 10:05-11:00: first displacement FVG in that direction
- Limit at FVG midpoint, valid 6 bars; stop = c1 extreme -/+ 0.10 ATR;
  stop distance 0.5-2.0 ATR; target 2R; one trade idea per day
"""
from app.core.strategies.base import BAR, Order, Strategy, btc_weekend, fvg, valid, window


class SilverBullet(Strategy):
    name = "silver_bullet"
    highs, lows = ("pdh", "onh"), ("pdl", "onl")

    def allowed(self, i, a) -> bool:
        return True

    def new_day(self, day):
        self.bias = 0
        self.r_hi = self.r_lo = None   # 09:30-10:00 range
        self.done = False

    def on_bar(self, i, a):
        mod = a["mod"][i]
        if mod < 570 or mod >= 660:
            return None
        h, l, c, atr = a["h"][i], a["l"][i], a["c"][i], a["atr"][i]

        highs = [a[k][i] for k in self.highs]
        lows = [a[k][i] for k in self.lows]
        if mod >= 600 and self.r_hi is not None:
            highs.append(self.r_hi)
            lows.append(self.r_lo)
        if any(valid(x) and h > x and c < x for x in highs):
            self.bias = -1
        if any(valid(x) and l < x and c > x for x in lows):
            self.bias = 1
        if mod < 600:  # build the 09:30-10:00 range
            self.r_hi = h if self.r_hi is None else max(self.r_hi, h)
            self.r_lo = l if self.r_lo is None else min(self.r_lo, l)
            return None

        if (self.done or self.bias == 0 or not window(a, i, 10 * 60 + 5, 11 * 60) or not valid(atr)
                or not self.allowed(i, a)):
            return None
        side = self.bias
        g = fvg(a, i, side)
        if g is None:
            return None
        lo, hi, extreme = g
        entry = (lo + hi) / 2
        stop = extreme - side * 0.10 * atr
        risk = (entry - stop) * side
        if not (0.5 * atr <= risk <= 2.0 * atr):
            return None
        self.done = True
        return Order(self.name, side, "limit", entry, stop, entry + side * self.rr * risk, self.rr,
                     placed_ts=a["close_ts"][i], expiry_ts=a["close_ts"][i] + 6 * BAR,
                     cancel_level=lo if side == 1 else hi,
                     reason="Silver Bullet: sweep then FVG in 10-11 window")


class BTCWeekendSilverBullet(SilverBullet):
    """Same rules and NY clock on BTCUSDT weekends (so Saturday and Sunday 10:00-11:00 NY).
    Liquidity = prior UTC-day high/low + the 09:30-10:00 NY range."""
    name = "btc_weekend_silver_bullet"
    highs, lows = ("pudh",), ("pudl",)

    def allowed(self, i, a) -> bool:
        return btc_weekend(a, i)
