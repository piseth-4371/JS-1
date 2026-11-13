"""Database connection (SQLAlchemy).

SQLite for week 1. To switch to PostgreSQL later, only DATABASE_URL changes.
"""
import sqlite3
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if url.startswith("sqlite:///"):
        # Make sure the folder for the .db file exists.
        db_path = Path(url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Several processes share this file (server, downloads, backtests, backups).
        # WAL: long reads no longer block writes; timeout: wait up to 60 s for a lock
        # instead of failing with "database is locked" after 5 s.
        engine = create_engine(url, connect_args={"timeout": 60})

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA busy_timeout=60000")
            try:
                # Persistent once set. Switching needs a moment when no other process
                # holds the file; if busy, keep the current mode rather than fail.
                cur.execute("PRAGMA journal_mode=WAL")
            except sqlite3.OperationalError:
                pass
            cur.close()

        return engine
    return create_engine(url)


def check_database() -> bool:
    """Return True if we can run a trivial query, False otherwise."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
