"""London-session features and strategy variants."""
import numpy as np
import pandas as pd

from app.core.features import build_frame
from app.core.paper_broker import can_hold
from app.core.strategies.sweep_mss_fvg import LondonSweepMSSFVG
from app.core.strategies.trend_fvg import LondonTrendFVG, TrendFVG
from tests.test_strategies import arrays


def m1_24h(start_utc="2026-11-09 00:00", days=2, seed=3):
    """Synthetic 1-minute bars around the clock (Mon-Tue by default)."""
    rng = np.random.default_rng(seed)
    start = int(pd.Timestamp(start_utc, tz="UTC").timestamp())
    rows, price = [], 28000.0
    for k in range(days * 1440):
        o = price
        price += rng.normal(0, 3)
        rows.append((start + k * 60, o, max(o, price) + 1, min(o, price) - 1, price, 10.0))
    return pd.DataFrame(rows, columns=["ts", "o", "h", "l", "c", "v"])


def row_at(df, utc):
    return df[df["ts"] == int(pd.Timestamp(utc, tz="UTC").timestamp())].iloc[0]


def test_london_clock_follows_both_daylight_saving_rules():
    winter = build_frame(m1_24h("2026-11-09 00:00", days=1)).df5
    r = row_at(winter, "2026-11-09 08:00")              # London GMT, NY EST
    assert r["lmod"] == 8 * 60 and r["mod"] == 3 * 60
    mismatch = build_frame(m1_24h("2026-03-16 00:00", days=1)).df5
    r = row_at(mismatch, "2026-03-16 08:00")            # NY already on EDT, London still GMT
    assert r["lmod"] == 8 * 60 and r["mod"] == 4 * 60


def test_asia_range_and_london_vwap():
    df = build_frame(m1_24h()).df5
    day2 = pd.Timestamp("2026-11-10").date()          # NY date (data starts Sunday evening NY)
    # Asia = 18:00 NY on day 1 (23:00 UTC) .. 08:00 London on day 2 (08:00 UTC)
    a = int(pd.Timestamp("2026-11-09 23:00", tz="UTC").timestamp())
    b = int(pd.Timestamp("2026-11-10 08:00", tz="UTC").timestamp())
    asia = df[(df["ts"] >= a) & (df["ts"] < b)]
    london = df[(df["ny_date"] == day2) & (df["lmod"] >= 8 * 60 + 5) & (df["mod"] < 570)]
    assert len(london) > 0
    assert (london["ash"] == asia["h"].max()).all() and (london["asl"] == asia["l"].min()).all()
    assert london["lvwap"].notna().all()
    assert df[(df["ny_date"] == day2) & (df["mod"] >= 600)]["lvwap"].isna().all()   # not used in NY


def test_asia_range_known_at_london_open_is_causal():
    m1 = m1_24h()
    cut = int(pd.Timestamp("2026-11-10 08:30", tz="UTC").timestamp())   # 30 min into London
    full, part = build_frame(m1).df5, build_frame(m1[m1["ts"] < cut]).df5
    p = part[part["lmod"] >= 8 * 60].tail(5)
    f = full.set_index("ts").loc[p["ts"]]
    for col in ["ash", "asl", "lvwap", "atr", "ema20_15"]:
        np.testing.assert_allclose(p[col].to_numpy(), f[col].to_numpy())


def test_positions_may_be_held_from_london_open_to_1555_ny_weekdays():
    ts = lambda s: int(pd.Timestamp(s, tz="America/New_York").timestamp())  # noqa: E731
    assert can_hold(ts("2026-11-10 03:00")) and can_hold(ts("2026-11-10 15:54"))
    assert not can_hold(ts("2026-11-10 02:59")) and not can_hold(ts("2026-11-10 15:55"))
    assert not can_hold(ts("2026-11-14 04:00"))         # Saturday


def london_fvg_arrays(lmod_start):
    a = arrays([(100, 102, 99, 101), (101, 115, 100, 114), (114, 118, 105, 117)], mod_start=200)
    n = 3
    a.update(lmod=np.arange(n) * 5 + lmod_start, atr_q10=np.full(n, 5.0), atr_q95=np.full(n, 20.0),
             ema20_15=np.full(n, 110.0), ema50_15=np.full(n, 100.0), close_15=np.full(n, 115.0),
             lvwap=np.full(n, 100.0), vwap=np.full(n, np.nan))
    return a


def test_london_trend_fvg_trades_only_in_london_window():
    a = london_fvg_arrays(lmod_start=8 * 60 + 5)        # bar 2 closes 08:20 London
    o = LondonTrendFVG().on_bar(2, a)
    assert o is not None and o.side == 1 and o.entry == 103.5 and o.stop == 98.0 and o.target == 114.5
    assert TrendFVG().on_bar(2, a) is None              # the NY version ignores London hours
    assert LondonTrendFVG().on_bar(2, london_fvg_arrays(lmod_start=11 * 60)) is None


def test_london_sweep_uses_asia_high():
    a = arrays([(100, 101, 99, 100)] * 4 + [(100, 112, 99, 105)], mod_start=200)   # last bar pokes above 110
    n = 5
    a.update(lmod=np.arange(n) * 5 + 8 * 60, ash=np.full(n, 110.0), asl=np.full(n, 90.0),
             pdh=np.full(n, np.nan), pdl=np.full(n, np.nan))
    s = LondonSweepMSSFVG()
    s.new_day(None)
    assert s.on_bar(4, a) is None
    assert len(s.setups) == 1 and s.setups[0]["side"] == -1 and s.setups[0]["extreme"] == 112
