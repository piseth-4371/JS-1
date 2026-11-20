from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import manual, state
from app.core.news import NY
from app.db import get_engine
from app.models import EventRow


def ny(*a):
    return int(datetime(*a, tzinfo=NY).timestamp())


def test_reset_rules():
    kill = ny(2026, 11, 20, 14, 0)
    assert manual.reset_allowed(kill, kill + 60) == (True, None)                 # misclick undo
    ok, after = manual.reset_allowed(kill, kill + 3600)
    assert not ok and after == ny(2026, 11, 21, 0, 0)                            # wait for the next NY day
    assert manual.reset_allowed(kill, ny(2026, 11, 21, 0, 0)) == (True, None)
    assert manual.reset_allowed(0, kill) == (True, None)                         # unknown kill time (old DB)


def test_next_day_across_dst():
    assert manual.next_ny_day(ny(2026, 11, 1, 0, 30)) == ny(2026, 11, 2, 0, 0)   # 25-hour day in New York


def test_clean_reason():
    assert manual.clean_reason("  felt   nervous \n") == "felt nervous"
    assert manual.clean_reason(None) == "" and len(manual.clean_reason("x" * 999)) == 300


def test_reset_needs_reason_and_waits(temp_db, monkeypatch):
    from app.main import app
    c = TestClient(app)
    assert c.post("/api/controls/kill", json={"reason": "bad day"}).status_code == 200
    with Session(get_engine()) as s, s.begin():
        state.put(s, "kill_switch_ts", int(datetime.now(NY).timestamp()) - 600)   # pressed 10 minutes ago
    assert c.post("/api/controls/reset-kill", json={"reason": "ok"}).status_code == 400
    r = c.post("/api/controls/reset-kill", json={"reason": "I feel calm now"})
    assert r.status_code == 409 and "Cooling-off" in r.json()["detail"]
    assert c.get("/api/overview").json()["kill_reset_after"] is not None
    with Session(get_engine()) as s, s.begin():
        state.put(s, "kill_switch_ts", int(datetime.now(NY).timestamp()) - 2 * 86400)   # two days ago
    assert c.post("/api/controls/reset-kill", json={"reason": "I feel calm now"}).status_code == 200
    with Session(get_engine()) as s:
        msgs = [e.message for e in s.scalars(select(EventRow).where(EventRow.type == "manual").order_by(EventRow.id))]
    assert msgs[0].startswith("KILL SWITCH activated (by user). Reason: bad day")
    assert msgs[-1].endswith("Reason: I feel calm now")
