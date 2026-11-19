"""High-impact US news blackout (part of the frozen strategy rules: "avoid ±30 min of high-impact news").

Calendar: app/calendar/us_high_impact_events.csv - every row has its official source:
- CPI and Employment Situation (NFP): release dates from the BLS release archives
  (bls.gov/bls/news-release/cpi.htm, .../empsit.htm) and BLS schedule pages; time 08:30 ET
  (the BLS schedule pages list 08:30 AM). The October 2025 reports were never published
  (2025 government shutdown), so they are correctly absent.
- FOMC: meeting dates from federalreserve.gov calendars; each past statement time was read
  from its press release ("For release at ..."), incl. the 2020 emergency statements.
- GDP and PCE (BEA "Personal Income and Outlays"): past releases from the BEA news archive
  (bea.gov/news/archive, each page's published time, mostly 08:30; some PCE at 10:00 ET);
  releases not yet archived from BEA's schedule file apps.bea.gov/API/signup/release_dates.json
  (both fetched 2026-11-13). Two posting-jitter times (08:29:59, 08:31) were set to the 08:30 schedule.
Not included: PPI, retail sales, jobless claims, ISM and other medium-impact releases.

Rules (the same in the backtester and the live engine):
- No NEW entry when the signal bar closes within ±30 min of an event.
- A pending (unfilled) order is cancelled at the first minute inside a blackout.
- Open positions keep their stop and target (no forced exit).
- Outside the calendar's coverage the engine does not trade: no calendar = unknown risk.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

NY = ZoneInfo("America/New_York")
CALENDAR = Path(__file__).resolve().parent.parent / "calendar" / "us_high_impact_events.csv"
# Usual 30-minute effect of each news type on NAS100 / gold / BTC, measured 2019-2024 (scripts/news_effect.py,
# docs/news_effect_report.md). Information only: the blackout rule does not use it.
EFFECTS = CALENDAR.parent / "news_effect.json"
EFFECT_MARKETS = ("nas100", "gold", "btc")
COVERED_FROM, COVERED_UNTIL = date(2019, 1, 1), date(2027, 1, 1)   # until = exclusive
WINDOW = 30 * 60                                                    # seconds before and after
EVENTS = ("CPI", "NFP", "FOMC", "GDP", "PCE")


@dataclass(frozen=True)
class Event:
    ts: int          # UTC epoch seconds of the release
    name: str
    source: str

    @property
    def label(self) -> str:
        return f"{self.name} {datetime.fromtimestamp(self.ts, NY):%Y-%m-%d %H:%M} ET"


@lru_cache
def load_events() -> tuple[Event, ...]:
    out = []
    with CALENDAR.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d, t = date.fromisoformat(r["date"]), r["time_et"]
            hh, mm = (int(x) for x in t.split(":"))
            ts = int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).timestamp())
            out.append(Event(ts, r["event"], r["source"]))
    return tuple(sorted(out, key=lambda e: e.ts))


@lru_cache
def load_effects() -> dict:
    """{news name: {market: summary}}; empty if the measurement file is missing."""
    try:
        return json.loads(EFFECTS.read_text(encoding="utf-8")).get("effects", {})
    except (OSError, ValueError):
        return {}


def effect(name: str) -> dict:
    """Short per-market effect for one news type: {market: {"x": times normal, "range_pct": usual 30-min range}}."""
    e = load_effects().get(name, {})
    return {m: {"x": v.get("effect_x"), "range_pct": v.get("news_range_pct")}
            for m in EFFECT_MARKETS if (v := e.get(m)) and v.get("n")}


@lru_cache
def _ts_array() -> np.ndarray:
    return np.array([e.ts for e in load_events()], dtype=np.int64)


def covered(ts: int) -> bool:
    return COVERED_FROM <= datetime.fromtimestamp(ts, NY).date() < COVERED_UNTIL


def blackout_event(ts: int) -> Event | None:
    """The event whose ±30 min window contains `ts`, or None."""
    arr = _ts_array()
    k = int(np.searchsorted(arr, ts - WINDOW, side="left"))
    if k < len(arr) and arr[k] <= ts + WINDOW:
        return load_events()[k]
    return None


def blackout_mask(ts: np.ndarray) -> np.ndarray:
    """Vectorised: True where a timestamp is within ±30 min of any event."""
    arr = _ts_array()
    ts = np.asarray(ts, dtype=np.int64)
    k = np.searchsorted(arr, ts - WINDOW, side="left")
    ok = k < len(arr)
    nxt = np.where(ok, arr[np.minimum(k, len(arr) - 1)], np.iinfo(np.int64).max)
    return ok & (nxt <= ts + WINDOW)


def covered_mask(ts: np.ndarray) -> np.ndarray:
    lo = int(datetime(COVERED_FROM.year, COVERED_FROM.month, COVERED_FROM.day, tzinfo=NY).timestamp())
    hi = int(datetime(COVERED_UNTIL.year, COVERED_UNTIL.month, COVERED_UNTIL.day, tzinfo=NY).timestamp())
    ts = np.asarray(ts, dtype=np.int64)
    return (ts >= lo) & (ts < hi)


def upcoming(now_ts: int, hours: int = 72) -> list[Event]:
    return [e for e in load_events() if now_ts - WINDOW <= e.ts <= now_ts + hours * 3600]


def entry_block_reason(close_ts: int) -> str | None:
    """Why a new entry at this 5m close is not allowed (None = allowed)."""
    if not covered(close_ts):
        return f"News calendar does not cover {datetime.fromtimestamp(close_ts, NY):%Y-%m-%d} - update app/calendar"
    ev = blackout_event(close_ts)
    if ev:
        return f"High-impact news blackout: {ev.label} (±30 min)"
    return None
