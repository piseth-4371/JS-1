"""Strategy 3 — Opening Range Breakout (classic baseline).

Rules:
- Opening range (OR) = high/low of 09:30-09:45 New York (three 5m bars)
- OR size must be 0.5-3.0 ATR
- First 5m CLOSE above OR high (long) or below OR low (short) between 09:50 and 11:30
- Market order at the next minute; stop = OR midpoint; target 2R from the actual fill
- At most one breakout attempt per day
"""
from app.core.strategies.base import BAR, Order, Strategy, valid, window


class OpeningRangeBreakout(Strategy):
    name = "orb"

    def new_day(self, day):
        self.or_bars = []
        self.done = False

    def on_bar(self, i, a):
        mod = a["mod"][i]
        if 570 <= mod < 585:
            self.or_bars.append(i)
            return None
        if self.done or len(self.or_bars) != 3 or not window(a, i, 9 * 60 + 50, 11 * 60 + 30):
            return None
        atr = a["atr"][i]
        if not valid(atr) or atr <= 0:
            return None
        orh = max(a["h"][j] for j in self.or_bars)
        orl = min(a["l"][j] for j in self.or_bars)
        if not (0.5 * atr <= orh - orl <= 3.0 * atr):
            self.done = True
            return None
        c = a["c"][i]
        side = 1 if c > orh else -1 if c < orl else 0
        if side == 0:
            return None
        self.done = True
        stop = (orh + orl) / 2
        return Order(self.name, side, "market", c, stop, None, self.rr,
                     placed_ts=a["close_ts"][i], expiry_ts=a["close_ts"][i] + BAR,
                     reason=f"Close beyond opening range {orl:.1f}-{orh:.1f}")
