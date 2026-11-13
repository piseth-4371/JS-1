"""Strategy 2 — Liquidity Sweep + Market Structure Shift + FVG (ICT).

Rules:
- Liquidity levels: prior-day high/low (PDH/PDL) and overnight high/low (ONH/ONL)
- Window: bars closing 09:35-11:30 New York
- Sweep: a 5m bar trades beyond a level and CLOSES back inside it
    (above a high -> bearish idea; below a low -> bullish idea)
- Within the next 6 bars, Market Structure Shift: a close beyond the swing
  point formed just before the sweep (min low / max high of the 3 bars before it),
  AND a displacement FVG in the new direction completes on that bar or the one before
- Limit at FVG midpoint, valid 6 bars; stop beyond the sweep extreme + 0.10 ATR;
  stop distance 0.5-3.0 ATR; target 2R. One trade idea per sweep.
"""
from app.core.strategies.base import BAR, Order, Strategy, fvg, valid, window


class SweepMSSFVG(Strategy):
    name = "sweep_mss_fvg"

    def new_day(self, day):
        self.setups = []   # active sweeps: dict(side, bar, extreme, swing)

    def on_bar(self, i, a):
        if not window(a, i, 9 * 60 + 35, 11 * 60 + 30):
            return None
        h, l, c, atr = a["h"][i], a["l"][i], a["c"][i], a["atr"][i]
        if not valid(atr) or atr <= 0 or i < 4:
            return None

        # 1. New sweeps on this bar
        for lvl in (a["pdh"][i], a["onh"][i]):
            if valid(lvl) and h > lvl and c < lvl:
                self.setups.append(dict(side=-1, bar=i, extreme=h, swing=min(a["l"][i - 3:i])))
        for lvl in (a["pdl"][i], a["onl"][i]):
            if valid(lvl) and l < lvl and c > lvl:
                self.setups.append(dict(side=1, bar=i, extreme=l, swing=max(a["h"][i - 3:i])))

        # 2. Check active sweeps for MSS + FVG
        self.setups = [s for s in self.setups if i - s["bar"] <= 6]
        for s in list(self.setups):
            side = s["side"]
            if s["bar"] == i:
                continue
            # keep the most extreme price of the sweep leg
            s["extreme"] = max(s["extreme"], h) if side == -1 else min(s["extreme"], l)
            if (c - s["swing"]) * side <= 0:
                continue  # no structure shift yet
            g = fvg(a, i, side) or fvg(a, i - 1, side)
            if g is None:
                continue
            lo, hi, _ = g
            entry = (lo + hi) / 2
            stop = s["extreme"] - side * 0.10 * atr
            risk = (entry - stop) * side
            self.setups.remove(s)
            if not (0.5 * atr <= risk <= 3.0 * atr):
                continue
            return Order(self.name, side, "limit", entry, stop, entry + side * self.rr * risk, self.rr,
                         placed_ts=a["close_ts"][i], expiry_ts=a["close_ts"][i] + 6 * BAR,
                         cancel_level=lo if side == 1 else hi,
                         reason="Liquidity sweep -> structure shift -> FVG")
        return None
