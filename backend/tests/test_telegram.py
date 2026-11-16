from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.config import get_settings
from app.core import telegram

NY = ZoneInfo("America/New_York")
LDN = ZoneInfo("Europe/London")
TOKEN = "123456:SECRET-token-value"


@pytest.fixture
def tg(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setenv("TELEGRAM_PRACTICE_ALERTS", "true")
    monkeypatch.setenv("TELEGRAM_SESSION_ALERTS", "true")
    get_settings.cache_clear()
    sent = []

    def fake_post(url, json, timeout):
        sent.append((url, json))
        return httpx.Response(200, json={"ok": True})
    monkeypatch.setattr(telegram.httpx, "post", fake_post)
    yield sent
    get_settings.cache_clear()


def _setup(eligible=False, expired=False):
    return {"market": "nas100", "strategy": "orb", "side": "LONG", "kind": "stop", "entry": 21000.0, "stop": 20980.0,
            "target": 21040.0, "rr_target": 2.0, "expiry_ts": 0, "bar_close_ts": 1_700_000_000, "reason": "breakout",
            "cost_share": 0.1, "qualified": eligible, "news_blackout": False, "eligible": eligible, "expired": expired}


def ts(zone, y, mo, d, h, mi):
    return int(datetime(y, mo, d, h, mi, tzinfo=zone).timestamp())


def test_disabled_without_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    get_settings.cache_clear()
    assert not telegram.enabled()
    assert telegram.send("hi") is False
    get_settings.cache_clear()


def test_send_uses_chat_id_and_never_logs_token(tg, monkeypatch, caplog):
    assert telegram.send("hello")
    assert tg[0][1] == {"chat_id": "42", "text": "hello", "disable_web_page_preview": True}
    monkeypatch.setattr(telegram.httpx, "post", lambda *a, **k: httpx.Response(401, text=f"bad {TOKEN}"))
    assert telegram.send("x") is False
    assert TOKEN not in caplog.text


def test_send_never_raises_on_network_error(tg, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(telegram.httpx, "post", boom)
    assert telegram.send("x") is False


def test_practice_setup_is_labelled_and_can_be_turned_off(tg, monkeypatch):
    msgs = telegram.Notifier().messages({"markets": []}, [{"type": "setup", "setup": _setup()}], 0)
    assert len(msgs) == 1 and "PRACTICE ONLY" in msgs[0] and "do not trade" in msgs[0]
    assert "%" not in msgs[0].split("Cost")[0]           # no "% chance of winning" anywhere before the cost line
    monkeypatch.setenv("TELEGRAM_PRACTICE_ALERTS", "false")
    get_settings.cache_clear()
    assert telegram.Notifier().messages({"markets": []}, [{"type": "setup", "setup": _setup()}], 0) == []
    assert "SIGNAL" in telegram.Notifier().messages({"markets": []}, [{"type": "setup", "setup": _setup(True)}], 0)[0]


def test_expired_setup_not_sent(tg):
    assert telegram.Notifier().messages({"markets": []}, [{"type": "setup", "setup": _setup(expired=True)}], 0) == []


def test_outcome_message(tg):
    o = {"type": "outcome", "market": "gold", "strategy": "orb", "side": "SHORT", "status": "stop", "r": -1.12,
         "ts": 1_700_000_000, "qualified": False}
    (m,) = telegram.Notifier().messages({"markets": []}, [o], 0)
    assert "STOP" in m and "-1.12R" in m and "(practice)" in m


@pytest.mark.parametrize("now,expected", [
    (ts(LDN, 2024, 6, 11, 8, 10), {"London"}),
    (ts(LDN, 2024, 3, 12, 8, 10), {"London"}),          # US/UK clocks out of step
    (ts(NY, 2024, 6, 11, 10, 0), {"New York"}),
    (ts(NY, 2024, 6, 11, 15, 30), set()),
    (ts(NY, 2024, 6, 10, 18, 30), {"Asia"}),            # Monday evening
    (ts(NY, 2024, 6, 14, 18, 30), set()),               # Friday evening: no Asia session
    (ts(NY, 2024, 6, 16, 18, 30), {"Asia"}),            # Sunday evening
    (ts(LDN, 2024, 6, 15, 8, 30), set()),               # Saturday
])
def test_sessions_open(now, expected):
    assert telegram.sessions_open(now) == expected


def test_session_opening_sent_once_and_not_on_first_cycle(tg):
    n = telegram.Notifier()
    assert n.messages({"markets": []}, [], ts(LDN, 2024, 6, 11, 8, 30)) == []     # started mid-window: quiet
    n = telegram.Notifier()
    assert n.messages({"markets": []}, [], ts(LDN, 2024, 6, 11, 8, 0)) == []
    (m,) = n.messages({"markets": []}, [], ts(LDN, 2024, 6, 11, 8, 5))
    assert "London entry window is OPEN" in m
    assert n.messages({"markets": []}, [], ts(LDN, 2024, 6, 11, 8, 10)) == []
    n.messages({"markets": []}, [], ts(NY, 2024, 6, 11, 9, 30))
    (m,) = n.messages({"markets": []}, [], ts(NY, 2024, 6, 11, 9, 35))
    assert "New York" in m


def test_feed_warning_on_change_only(tg):
    n = telegram.Notifier()
    mk = lambda state: {"markets": [{"key": "nas100", "state": state, "detail": "newest bar closed 5 min ago"}]}
    t = ts(NY, 2024, 6, 15, 12, 0)                      # Saturday: no session messages mixed in
    assert n.messages(mk("open"), [], t) == []
    (m,) = n.messages(mk("stale"), [], t)
    assert "stale" in m and "MT5" in m
    assert n.messages(mk("stale"), [], t) == []
    (m,) = n.messages(mk("open"), [], t)
    assert "back" in m
    assert n.messages(mk("closed"), [], t) == []        # normal market close is not a warning


def test_notify_sends_nothing_when_disabled(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    get_settings.cache_clear()
    assert telegram.Notifier().notify({"markets": []}, [{"type": "setup", "setup": _setup(True)}], 0) == 0
    get_settings.cache_clear()
