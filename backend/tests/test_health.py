import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.fixture
def client(temp_db):
    return TestClient(app)


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_is_always_paper_mode(client):
    body = client.get("/api/health").json()
    assert body["trading_mode"] == "paper"
    assert body["live_trading_available"] is False


def test_settings_reject_live_mode(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "live")
    config.get_settings.cache_clear()
    with pytest.raises(Exception):
        config.get_settings()
    config.get_settings.cache_clear()
