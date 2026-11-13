"""Turn 1-minute bars into the 5-minute table every strategy reads.

Each 5-minute row i holds facts that were KNOWN when that bar closed:
OHLC, ATR, 15-minute EMA bias (from the last *completed* 15m bar), session
VWAP, prior-day high/low, overnight high/low, and ATR percentiles.

Times: `ts` = bar open (UTC epoch s). `mod` = minute-of-day in New York for
the bar OPEN (09:30 = 570). A 5m bar with mod 570 closes at 09:35.
`lmod` = the same in London time (08:00 = 480), for the London-session strategies.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.core.indicators import atr, ema, session_vwap
from app.db import get_engine

NY = "America/New_York"
LONDON = "Europe/London"
LONDON_OPEN = 480               # 08:00 London
HOLD_FROM = 180                 # 03:00 NY: positions may be open from here (London session) ...
RTH_OPEN, RTH_CLOSE = 570, 960   # 09:30, 16:00
FLAT_AT = 955                    # ... until 15:55 NY: every position closed
ATR_PCT_WINDOW = 20 * 276        # ~20 trading days of 5m bars


def load_m1(source: str, symbol: str, start_ts: int, end_ts: int) -> pd.DataFrame:
    q = text("SELECT ts, open AS o, high AS h, low AS l, close AS c, volume AS v FROM bars "
             "WHERE source=:s AND symbol=:y AND timeframe='M1' AND ts>=:a AND ts<:b ORDER BY ts")
    with get_engine().connect() as conn:
        return pd.read_sql(q, conn, params={"s": source, "y": symbol, "a": start_ts, "b": end_ts})


def _add_ny(df: pd.DataFrame) -> pd.DataFrame:
    ny = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(NY)
    df["ny_date"] = ny.dt.date
    df["mod"] = ny.dt.hour * 60 + ny.dt.minute
    df["weekday"] = ny.dt.weekday
    ldn = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(LONDON)
    df["lmod"] = ldn.dt.hour * 60 + ldn.dt.minute
    return df


def resample_complete(m1: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Clock-aligned bars built ONLY from complete buckets (same rule as market_data.resample)."""
    size = minutes * 60
    g = m1.groupby(m1["ts"] // size * size)
    out = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"), n=("ts", "size"))
    out = out[out["n"] == minutes].drop(columns="n")
    out.index.name = "ts"
    return out.reset_index()


@dataclass
class Frame:
    df5: pd.DataFrame
    a: dict            # numpy arrays of df5 columns (fast access in loops)
    m1: dict           # numpy arrays of the 1-minute bars (for fills)


def build_frame(m1: pd.DataFrame) -> Frame:
    m1 = _add_ny(m1.copy())
    df = resample_complete(m1, 5)
    df = _add_ny(df)
    df["close_ts"] = df["ts"] + 300
    df["consec"] = df["ts"].diff().eq(300)
    df["atr"] = atr(df["h"], df["l"], df["c"], 14)
    q = df["atr"].rolling(ATR_PCT_WINDOW, min_periods=ATR_PCT_WINDOW // 4)
    df["atr_q10"], df["atr_q95"] = q.quantile(0.10), q.quantile(0.95)

    # 15-minute bias: attach the last 15m bar that had CLOSED by this 5m bar's close.
    d15 = resample_complete(m1, 15)
    d15["ema20_15"], d15["ema50_15"] = ema(d15["c"], 20), ema(d15["c"], 50)
    d15["close_ts"] = d15["ts"] + 900
    d15 = d15.rename(columns={"c": "close_15"})[["close_ts", "close_15", "ema20_15", "ema50_15"]]
    df = pd.merge_asof(df.sort_values("close_ts"), d15.sort_values("close_ts"), on="close_ts", direction="backward")

    # Session VWAP (regular hours only).
    rth = (df["mod"] >= RTH_OPEN) & (df["mod"] < RTH_CLOSE)
    df["vwap"] = np.nan
    df.loc[rth, "vwap"] = session_vwap(df.loc[rth, "h"], df.loc[rth, "l"], df.loc[rth, "c"], df.loc[rth, "v"], df.loc[rth, "ny_date"])

    # Prior-day regular-hours high/low (known before today's open).
    # For every date (also weekends and pre-market), take the most recent EARLIER session.
    daily = df[rth].groupby("ny_date").agg(day_h=("h", "max"), day_l=("l", "min"))
    daily = daily.reindex(sorted(df["ny_date"].unique()))
    daily[["pdh", "pdl"]] = daily[["day_h", "day_l"]].ffill().shift(1)
    df = df.merge(daily[["pdh", "pdl"]], left_on="ny_date", right_index=True, how="left")

    # Overnight high/low: bars from 16:00 yesterday to 09:30 today (complete by the open).
    ny_dt = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(NY)
    df["sess_date"] = (ny_dt + pd.Timedelta(hours=8)).dt.date
    on = df[~rth].groupby("sess_date").agg(onh=("h", "max"), onl=("l", "min"))
    df = df.merge(on, left_on="ny_date", right_index=True, how="left")

    # London session VWAP: from 08:00 London until the NY cash open.
    ldn = (df["lmod"] >= LONDON_OPEN) & (df["mod"] < RTH_OPEN)
    df["lvwap"] = np.nan
    df.loc[ldn, "lvwap"] = session_vwap(df.loc[ldn, "h"], df.loc[ldn, "l"], df.loc[ldn, "c"], df.loc[ldn, "v"], df.loc[ldn, "ny_date"])

    # Asia range: 18:00 NY (evening before) until 08:00 London. Complete when London opens,
    # so strategies may use it only AFTER 08:00 London (same idea as ONH/ONL after 09:30).
    asia = (df["mod"] >= 18 * 60) | ((df["lmod"] < LONDON_OPEN) & (df["mod"] < 12 * 60))
    ar = df[asia].groupby("sess_date").agg(ash=("h", "max"), asl=("l", "min"))
    df = df.merge(ar, left_on="ny_date", right_index=True, how="left")
    df = df.sort_values("ts").reset_index(drop=True)

    cols = ["ts", "o", "h", "l", "c", "v", "mod", "close_ts", "consec", "atr", "atr_q10", "atr_q95",
            "close_15", "ema20_15", "ema50_15", "vwap", "pdh", "pdl", "onh", "onl",
            "lmod", "lvwap", "ash", "asl"]
    a = {k: df[k].to_numpy() for k in cols}
    a["ny_date"] = df["ny_date"].to_numpy()
    a["weekday"] = df["weekday"].to_numpy()
    m = {k: m1[k].to_numpy() for k in ["ts", "o", "h", "l", "c"]}
    m["can_hold"] = ((m1["mod"] >= HOLD_FROM) & (m1["mod"] < FLAT_AT) & (m1["weekday"] < 5)).to_numpy()
    m["ny_date"] = m1["ny_date"].to_numpy()
    return Frame(df, a, m)
