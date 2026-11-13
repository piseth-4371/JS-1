import numpy as np

from app.core.strategies.base import fvg
from app.core.strategies.orb import OpeningRangeBreakout


def arrays(candles, mod_start=600, atr=10.0):
    """candles: list of (o, h, l, c) 5-minute bars, consecutive, starting at NY minute mod_start."""
    n = len(candles)
    o, h, l, c = (np.array(x, dtype=float) for x in zip(*candles))
    ts = np.arange(n) * 300 + 1_800_000_000
    return {
        "o": o, "h": h, "l": l, "c": c, "ts": ts, "close_ts": ts + 300,
        "mod": np.arange(n) * 5 + mod_start, "consec": np.array([False] + [True] * (n - 1)),
        "atr": np.full(n, atr),
    }


def test_bullish_fvg_detected():
    a = arrays([(100, 102, 99, 101),      # c1: high 102
                (101, 115, 100, 114),     # c2: displacement body 13 >= 1 ATR
                (114, 118, 105, 117)])    # c3: low 105 > 102 -> gap 102..105
    assert fvg(a, 2, 1) == (102, 105, 99)


def test_no_fvg_when_candles_overlap():
    a = arrays([(100, 106, 99, 101), (101, 115, 100, 114), (114, 118, 105, 117)])
    assert fvg(a, 2, 1) is None


def test_no_fvg_without_displacement():
    a = arrays([(100, 102, 99, 101), (101, 108, 100, 105), (105, 110, 104, 109)])  # body 4 < ATR 10
    assert fvg(a, 2, 1) is None


def test_bearish_fvg_detected():
    a = arrays([(120, 121, 118, 119), (119, 119, 104, 105), (105, 115, 100, 101)])
    assert fvg(a, 2, -1) == (115, 118, 121)


def test_orb_long_breakout():
    a = arrays([(100, 105, 98, 104), (104, 108, 101, 103), (103, 106, 100, 102),   # 09:30-09:45 range 98-108
                (102, 107, 101, 106),                                              # 09:45 bar: inside
                (106, 112, 105, 111)], mod_start=570)                              # closes 09:55 above 108
    s = OpeningRangeBreakout()
    s.new_day(None)
    orders = [s.on_bar(i, a) for i in range(5)]
    o = orders[4]
    assert o is not None and o.side == 1 and o.kind == "market" and o.stop == 103
    assert orders[:4] == [None] * 4
