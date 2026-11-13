import sys
from pathlib import Path

import pytest

# Let tests import the `app` package from the backend folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db  # noqa: E402


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """A throwaway SQLite file so tests never touch your real data."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()
    from app.repository import init_db

    init_db()
    yield
    db.get_engine().dispose()
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()
