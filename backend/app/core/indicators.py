"""Technical indicators. All are CAUSAL: the value at row i uses only rows 0..i.

That is what prevents look-ahead bias. tests/test_indicators.py checks it by
computing on a shortened series and comparing with the full one.
"""
import numpy as np
import pandas as pd


def ema(close: pd.Series, n: int) -> pd.Series:
    """Exponential moving average (recent prices count more)."""
    return close.ewm(span=n, adjust=False, min_periods=n).mean()


def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    """Average True Range: the typical size of one candle, including gaps (Wilder smoothing)."""
    prev = close.shift(1)
    tr = pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def session_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, session_key: pd.Series) -> pd.Series:
    """Volume-weighted average price, restarting each session.

    If a session has no volume yet, falls back to the plain average of typical prices.
    """
    tp = (high + low + close) / 3
    g = session_key
    pv = (tp * volume).groupby(g).cumsum()
    vv = volume.groupby(g).cumsum()
    plain = tp.groupby(g).cumsum() / tp.groupby(g).cumcount().add(1)
    return pd.Series(np.where(vv > 0, pv / vv.where(vv > 0, 1), plain), index=close.index)
