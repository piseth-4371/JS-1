"""Turn 1-minute bars into the 5-minute table every strategy reads.

Each 5-minute row i holds facts that were KNOWN when that bar closed:
OHLC, ATR, 15-minute EMA bias (from the last *completed* 15m bar), session
VWAP, prior-day high/low, overnight high/low, and ATR percentiles.

Times: `ts` = bar open (UTC epoch s). `mod` = minute-of-day in New York for
the bar OPEN (09:30 = 570). A 5m bar with mod 570 closes at 09:35.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.core.indicators import atr, ema, session_vwap
from app.db import get_engine

NY = "America/New_York"
RTH_OPEN, RTH_CLOSE = 570, 960   # 09:30, 16:00
FLAT_AT = 955                    # 15:55: every position closed
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
    df = df.sort_values("ts").reset_index(drop=True)

    cols = ["ts", "o", "h", "l", "c", "v", "mod", "close_ts", "consec", "atr", "atr_q10", "atr_q95",
            "close_15", "ema20_15", "ema50_15", "vwap", "pdh", "pdl", "onh", "onl"]
    a = {k: df[k].to_numpy() for k in cols}
    a["ny_date"] = df["ny_date"].to_numpy()
    a["weekday"] = df["weekday"].to_numpy()
    m = {k: m1[k].to_numpy() for k in ["ts", "o", "h", "l", "c"]}
    m["can_hold"] = ((m1["mod"] >= RTH_OPEN) & (m1["mod"] < FLAT_AT)).to_numpy()
    m["ny_date"] = m1["ny_date"].to_numpy()
    return Frame(df, a, m)
