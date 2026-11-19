import pandas as pd

from app.api_market import resample_candles


def m1(start, closes):
    return pd.DataFrame({"ts": [start + 60 * i for i in range(len(closes))],
                         "o": closes, "h": [c + 1 for c in closes], "l": [c - 1 for c in closes], "c": closes})


def test_15_minute_candles_group_by_start_time():
    start = 1_800_000_000 - (1_800_000_000 % 900)       # a 15-minute boundary
    c = resample_candles(m1(start, list(range(100, 130))), 15)   # 30 minutes -> 2 candles
    assert [x["time"] for x in c] == [start, start + 900]
    assert c[0] == {"time": start, "open": 100.0, "high": 115.0, "low": 99.0, "close": 114.0}
    assert c[1]["open"] == 115.0 and c[1]["close"] == 129.0


def test_forming_candle_and_count_limit():
    start = 1_800_000_000 - (1_800_000_000 % 3600)
    c = resample_candles(m1(start, [1.0] * 130), 60)               # 2 full hours + 10 minutes
    assert len(c) == 3 and c[-1]["time"] == start + 7200          # newest holds only the 10 closed minutes
    assert len(resample_candles(m1(start, [1.0] * 130), 1, count=50)) == 50
    assert resample_candles(m1(start, []), 5) == []
