"""Your own actions: a reason for each, and a cooling-off wait before the kill switch can be reset.

Idea from the finance-psychology skill: knowing about a bias does not stop it; a written reason and a waiting
period do. The engine never breaks its rules, but people can (stop it after a bad day, switch it back on in a
hurry). Rules, fixed 2026-11-20:
- KILL is never delayed and never needs a reason (it is the emergency stop). A reason is saved if given.
- Reset needs a reason of at least MIN_REASON characters, and is allowed only
  (a) within UNDO_SECONDS of pressing KILL (a misclick), or
  (b) once the New York date is later than the date KILL was pressed (sleep on it).
- Other manual changes (auto-trading, active strategy) save the reason if given.
Every manual action is an event of type "manual" so the monthly report can count them.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.core.news import NY

MIN_REASON = 5
UNDO_SECONDS = 120
TYPE = "manual"


def clean_reason(reason: str | None) -> str:
    return " ".join((reason or "").split())[:300]


def next_ny_day(ts: int) -> int:
    """Start (00:00 New York) of the day after the one `ts` falls on."""
    d = datetime.fromtimestamp(ts, NY).date() + timedelta(days=1)
    return int(datetime(d.year, d.month, d.day, tzinfo=NY).timestamp())


def reset_allowed(kill_ts: int, now: int) -> tuple[bool, int | None]:
    """(allowed, earliest reset time when not allowed). kill_ts 0 = unknown (older database): allowed."""
    if kill_ts <= 0 or now - kill_ts <= UNDO_SECONDS:
        return True, None
    after = next_ny_day(kill_ts)
    return (True, None) if now >= after else (False, after)


def message(action: str, reason: str) -> str:
    return f"{action} (by user). Reason: {reason or 'none given'}"
