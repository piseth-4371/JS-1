import numpy as np
import pandas as pd

from app.core.features import build_frame
from app.core.indicators import atr, ema, session_vwap


def series(n=300, seed=1):
    rng = np.random.default_rng(seed)
    c = pd.Series(28000 + rng.normal(0, 5, n).cumsum())
    h = c + rng.uniform(0, 5, n)
    l = c - rng.uniform(0, 5, n)  # noqa: E741
    return h, l, c


def test_ema_and_atr_are_causal():
    """Values for the first 200 bars must not change when future bars are added."""
    h, l, c = series()
    full_e, short_e = ema(c, 20), ema(c[:200], 20)
    full_a, short_a = atr(h, l, c), atr(h[:200], l[:200], c[:200])
    pd.testing.assert_series_equal(full_e[:200], short_e)
    pd.testing.assert_series_equal(full_a[:200], short_a)


def test_vwap_resets_each_session():
    h = pd.Series([11.0, 11, 21, 21]); l = pd.Series([9.0, 9, 19, 19]); c = pd.Series([10.0, 10, 20, 20])  # noqa: E702,E741
    v = pd.Series([1.0, 3, 1, 1]); key = pd.Series(["d1", "d1", "d2", "d2"])  # noqa: E702
    out = session_vwap(h, l, c, v, key)
    assert list(out) == [10.0, 10.0, 20.0, 20.0]


def make_m1(days=3, seed=2):
    """Synthetic 1-minute bars covering full sessions (UTC 13:00-22:00 = NY 08:00/09:00-...)."""
    rng = np.random.default_rng(seed)
    start = int(pd.Timestamp("2026-11-09 13:00", tz="UTC").timestamp())
    rows, price = [], 28000.0
    for d in range(days):
        for k in range(9 * 60):
            ts = start + d * 86400 + k * 60
            o = price
            price += rng.normal(0, 3)
            rows.append((ts, o, max(o, price) + 1, min(o, price) - 1, price, 10.0))
    return pd.DataFrame(rows, columns=["ts", "o", "h", "l", "c", "v"])


def test_feature_frame_is_causal():
    """Every feature at a given 5m bar is identical whether or not later data exists."""
    m1 = make_m1()
    cut = len(m1) * 2 // 3
    full, part = build_frame(m1), build_frame(m1.iloc[:cut])
    n = len(part.df5) - 1  # last bar of the shorter run
    cols = ["o", "h", "l", "c", "atr", "close_15", "ema20_15", "ema50_15", "vwap", "pdh", "pdl"]
    a = full.df5[cols].iloc[:n].reset_index(drop=True)
    b = part.df5[cols].iloc[:n].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_15m_bias_uses_only_closed_bars():
    f = build_frame(make_m1())
    df = f.df5.dropna(subset=["close_15"])
    # the attached 15m close must be from a bar that closed at or before this 5m bar's close
    m1 = make_m1().set_index("ts")
    for _, row in df.sample(20, random_state=0).iterrows():
        last_15_close_ts = (row["close_ts"] // 900) * 900
        # the last 1-minute close before that moment (there may be an overnight gap)
        assert m1[m1.index < last_15_close_ts]["c"].iloc[-1] == row["close_15"]


def test_prior_day_levels_available_before_the_open():
    """At 08:00 NY (before 09:30) the prior-day high/low must already be known."""
    f = build_frame(make_m1(days=2))
    df = f.df5
    day1, day2 = sorted(df["ny_date"].unique())[:2]
    rth1 = df[(df["ny_date"] == day1) & (df["mod"] >= 570) & (df["mod"] < 960)]
    premarket2 = df[(df["ny_date"] == day2) & (df["mod"] < 570)]
    assert len(premarket2) > 0
    assert (premarket2["pdh"] == rth1["h"].max()).all()
    assert (premarket2["pdl"] == rth1["l"].min()).all()
