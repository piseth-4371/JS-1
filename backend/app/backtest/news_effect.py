"""How much NAS100, gold and BTC usually move around each high-impact US news type
(docs/news_effect_preregistration.md). Pure functions, measurement only: no trading rule comes from here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np

from app.core.news import NY, Event

WINDOW_MIN = 30
MIN_BARS = 20
BEFORE_MAX_GAP = 600      # the "before" bar must start within 10 minutes before the release
CONTROL_DAYS = 10         # weekdays on each side


@dataclass(frozen=True)
class Bars:
    ts: np.ndarray        # bar start, UTC seconds, sorted
    h: np.ndarray
    l: np.ndarray         # noqa: E741
    c: np.ndarray


def window(b: Bars, start: int, minutes: int = WINDOW_MIN, min_bars: int = MIN_BARS) -> tuple[float, float] | None:
    """(range %, |move| %) for the bars starting in [start, start + minutes), or None if data is missing."""
    k = int(np.searchsorted(b.ts, start, side="left"))
    if k == 0 or start - b.ts[k - 1] > BEFORE_MAX_GAP:
        return None
    before = float(b.c[k - 1])
    end = int(np.searchsorted(b.ts, start + minutes * 60, side="left"))
    if end - k < min_bars:
        return None
    hi, lo, last = float(b.h[k:end].max()), float(b.l[k:end].min()), float(b.c[end - 1])
    return (hi - lo) / before * 100, abs(last - before) / before * 100


def control_starts(ev_ts: int, event_days: set[date], n_each_side: int = CONTROL_DAYS) -> list[int]:
    """Same New York clock time on the nearest weekdays without any calendar event."""
    t = datetime.fromtimestamp(ev_ts, NY)
    out = []
    for step in (-1, 1):
        d, found = t.date(), 0
        while found < n_each_side:
            d += timedelta(days=step)
            if d.weekday() < 5 and d not in event_days:
                out.append(int(datetime(d.year, d.month, d.day, t.hour, t.minute, tzinfo=NY).timestamp()))
                found += 1
    return out


@dataclass(frozen=True)
class EventMeasure:
    name: str
    ts: int
    range_pct: float
    move_pct: float
    normal_pct: float      # median control range for this event


def measure(b: Bars, events: list[Event], event_days: set[date]) -> tuple[list[EventMeasure], int]:
    """Measures every event that has enough data; returns (measures, skipped)."""
    out, skipped = [], 0
    for e in events:
        w = window(b, e.ts)
        controls = [x for x in (window(b, s) for s in control_starts(e.ts, event_days)) if x is not None]
        if w is None or not controls:
            skipped += 1
            continue
        out.append(EventMeasure(e.name, e.ts, w[0], w[1], float(np.median([x[0] for x in controls]))))
    return out, skipped


def summarize(ms: list[EventMeasure], skipped: int) -> dict:
    if not ms:
        return {"n": 0, "skipped": skipped}
    r = np.array([m.range_pct for m in ms])
    nrm = np.array([m.normal_pct for m in ms])
    mv = np.array([m.move_pct for m in ms])
    news_med, normal_med = float(np.median(r)), float(np.median(nrm))
    return {"n": len(ms), "skipped": skipped,
            "news_range_pct": round(news_med, 3), "normal_range_pct": round(normal_med, 3),
            "effect_x": round(news_med / normal_med, 2) if normal_med > 0 else None,
            "news_move_pct": round(float(np.median(mv)), 3),
            "share_over_2x": round(float((r > 2 * nrm).mean()), 3)}
