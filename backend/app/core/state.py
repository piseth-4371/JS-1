"""Persisted switches and the audit log. Stored in the DB, so they survive restarts."""
from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.models import ControlRow, EventRow

DEFAULTS = {
    "kill_switch": "false",
    "auto_trading": "false",          # OFF by default: the engine only records signals
    "active_strategy": "trend_fvg",
    "broker_cursor_ts": "0",          # last 1-minute bar the paper broker processed
}


def get(s: Session, key: str) -> str:
    row = s.get(ControlRow, key)
    return row.value if row else DEFAULTS[key]


def get_bool(s: Session, key: str) -> bool:
    return get(s, key) == "true"


def put(s: Session, key: str, value) -> None:
    if isinstance(value, bool):
        value = "true" if value else "false"
    row = s.get(ControlRow, key)
    if row:
        row.value, row.updated_ts = str(value), int(time.time())
    else:
        s.add(ControlRow(key=key, value=str(value), updated_ts=int(time.time())))


def log(s: Session, level: str, type_: str, message: str, ts: int | None = None) -> None:
    s.add(EventRow(ts=ts or int(time.time()), level=level, type=type_, message=message))
