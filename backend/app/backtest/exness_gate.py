"""Exness cost gate (docs/exness_cost_gate_preregistration.md): re-price NAS100 backtest trades with the spread
measured on Exness USTEC 2021-2023 and apply the same pass shape as the main test. Pure functions.

Measurement only: nothing here creates signals, changes a strategy or touches scanner.QUALIFIED.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from app.backtest.decompose import STOP_LIKE_EXITS, SLIP_ENTRIES, week_interval

NY = ZoneInfo("America/New_York")
BACKTEST_SPREAD = 1.5
BACKTEST_SLIPPAGE = 0.5
US_OPEN_MINUTE = 9 * 60 + 30
# Highest usable-year (2021-2023) Exness median / p90 per window, from docs/exness_spread_years_report.md.
EXNESS = {"pre_us": {"model": 2.94, "stress": 3.29}, "us": {"model": 2.94, "stress": 3.65}}
FAMILY_TESTS = 7
MIN_TRADES = 30
DEV_YEARS, VAL_YEARS = range(2019, 2023), range(2023, 2025)
REQUIRED = ("strategy", "side", "kind", "ny_date", "entry_ts", "entry", "exit", "exit_reason", "risk_pts", "r")

PASS, FAIL, NOT_ELIGIBLE, NO_VERDICT = ("passes the Exness gate", "fails the Exness gate",
                                        "not eligible — failed its main test",
                                        "input does not use the expected cost model — no verdict")


def window(entry_ts: int) -> str:
    d = datetime.fromtimestamp(int(entry_ts), NY)
    return "pre_us" if d.hour * 60 + d.minute < US_OPEN_MINUTE else "us"


def cost_model_error(t: pd.DataFrame) -> float:
    """Largest |r - (gross - (1.5 + 0.5*legs)/risk)|: 0 when the file uses the backtest's NAS100 cost model."""
    gross = (t["exit"] - t["entry"]) * t["side"] / t["risk_pts"]
    legs = t["kind"].isin(SLIP_ENTRIES).astype(int) + t["exit_reason"].isin(STOP_LIKE_EXITS).astype(int)
    expected = gross - (BACKTEST_SPREAD + BACKTEST_SLIPPAGE * legs) / t["risk_pts"]
    return float((expected - t["r"]).abs().max()) if len(t) else 0.0


def reprice(t: pd.DataFrame) -> pd.DataFrame:
    """Add window, r_exness (median spread) and r_stress (p90 spread)."""
    out = t.copy()
    out["window"] = [window(x) for x in out["entry_ts"]]
    for col, level in (("r_exness", "model"), ("r_stress", "stress")):
        spread = out["window"].map(lambda w: EXNESS[w][level])
        out[col] = out["r"] + (BACKTEST_SPREAD - spread) / out["risk_pts"]
    return out


@dataclass(frozen=True)
class Split:
    n: int
    avg_backtest: float
    avg_exness: float
    family_low: float
    family_high: float
    avg_stress: float

    def ok(self) -> bool:
        return self.n >= MIN_TRADES and self.avg_exness > 0 and self.family_low > 0 and self.avg_stress > 0


def split(t: pd.DataFrame, years: range) -> Split:
    dates = [date.fromisoformat(str(d)) for d in t["ny_date"]]
    mask = np.array([d.year in years for d in dates], dtype=bool)
    s = t[mask]
    if s.empty:
        nan = float("nan")
        return Split(0, nan, nan, nan, nan, nan)
    lo, hi = week_interval(s["r_exness"].to_numpy(), [d for d, m in zip(dates, mask) if m], tests=FAMILY_TESTS)
    return Split(len(s), float(s["r"].mean()), float(s["r_exness"].mean()), lo, hi, float(s["r_stress"].mean()))


def verdict(dev: Split, val: Split, main_passed: bool) -> str:
    if not main_passed:
        return NOT_ELIGIBLE
    return PASS if dev.ok() and val.ok() else FAIL
