"""Per-session data quality for 1-minute bars, and the session validity rule.

The rule was written down (docs/data_quality_rule.md) BEFORE any performance number was recomputed with it.
Do not change the thresholds to make a backtest look better.

A New York trading date is VALID when, inside the NAS100 holding window 03:00-15:55 New York time
(775 one-minute bars on a full day):
  - at least MIN_BARS (765) of the 775 minutes have a bar, and
  - no run of missing minutes is longer than MAX_GAP_MIN (5), counting missing minutes at the start
    and end of the window.

Missing prices are never filled in. Invalid dates are reported and can be excluded from backtests.
Pure functions: no database, no network.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

WINDOW_START_MIN = 3 * 60          # 03:00 New York
WINDOW_END_MIN = 15 * 60 + 55      # 15:55 New York (exclusive: the last bar starts at 15:54)
WINDOW_BARS = WINDOW_END_MIN - WINDOW_START_MIN   # 775
MIN_BARS = 765
MAX_GAP_MIN = 5


@dataclass(frozen=True)
class SessionQuality:
    ny_date: object
    bars: int                 # minutes with a bar inside 03:00-15:55
    expected: int             # 775
    longest_gap_min: int      # longest run of missing minutes (edges included)
    zero_volume_share: float  # share of those bars with volume 0 (VWAP then becomes a plain average)
    valid: bool
    reason: str               # "" when valid


def _longest_gap(minutes: np.ndarray) -> int:
    """minutes: sorted unique minute-of-day values inside the window. Longest run of missing minutes."""
    if minutes.size == 0:
        return WINDOW_BARS
    edges = np.concatenate(([WINDOW_START_MIN - 1], minutes, [WINDOW_END_MIN]))
    return int((np.diff(edges) - 1).max())


def judge(bars: int, longest_gap: int) -> tuple[bool, str]:
    reasons = []
    if bars < MIN_BARS:
        reasons.append(f"only {bars}/{WINDOW_BARS} bars")
    if longest_gap > MAX_GAP_MIN:
        reasons.append(f"gap of {longest_gap} min")
    return (not reasons, "; ".join(reasons))


def session_quality(m1: pd.DataFrame) -> list[SessionQuality]:
    """m1: columns ts (UTC seconds, bar open), v. One row per New York weekday that has at least one bar
    in the window. Dates with no bar at all (holidays, missing files) do not appear: nothing can trade there."""
    if m1.empty:
        return []
    ny = pd.to_datetime(m1["ts"], unit="s", utc=True).dt.tz_convert("America/New_York")
    mod = (ny.dt.hour * 60 + ny.dt.minute).to_numpy()
    keep = (mod >= WINDOW_START_MIN) & (mod < WINDOW_END_MIN) & (ny.dt.dayofweek.to_numpy() < 5)
    df = pd.DataFrame({"d": ny.dt.date.to_numpy()[keep], "mod": mod[keep],
                       "v": m1["v"].to_numpy()[keep] if "v" in m1 else np.zeros(int(keep.sum()))})
    out = []
    for d, g in df.groupby("d", sort=True):
        mins = np.unique(g["mod"].to_numpy())
        gap = _longest_gap(mins)
        ok, why = judge(int(mins.size), gap)
        out.append(SessionQuality(d, int(mins.size), WINDOW_BARS, gap, float((g["v"].to_numpy() <= 0).mean()), ok, why))
    return out


def valid_dates(quality: list[SessionQuality]) -> set:
    return {q.ny_date for q in quality if q.valid}


def max_gap_between(ts: np.ndarray, t0: int, t1: int) -> int:
    """Longest run of missing minutes between two bar-open times t0 <= t1 (inclusive), given sorted bar
    times `ts` (UTC seconds). Used to flag trades that were held through a hole in the data."""
    inside = ts[(ts >= t0) & (ts <= t1)]
    if inside.size == 0:
        return (t1 - t0) // 60 + 1
    edges = np.concatenate(([t0 - 60], inside, [t1 + 60]))
    return int((np.diff(edges) // 60 - 1).max())
