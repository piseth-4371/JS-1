"""Database connection (SQLAlchemy).

SQLite for week 1. To switch to PostgreSQL later, only DATABASE_URL changes.
"""
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if url.startswith("sqlite:///"):
        # Make sure the folder for the .db file exists.
        db_path = Path(url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url)


def check_database() -> bool:
    """Return True if we can run a trivial query, False otherwise."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
