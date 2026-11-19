"""Telegram ALERTS for the signals-only scanner (one-way: this program -> your phone).

What it sends (all read-only information, never an order):
  - a new scanner setup (labelled PRACTICE ONLY unless the strategy passed its backtest)
  - what happened to that setup later (target / stop / expired / session end)
  - London and New York entry windows opening (Asia = range only, one message at 18:00 NY)
  - a market's price feed going stale / coming back (e.g. MT5 terminal closed)

Off unless TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set in backend/.env.
The bot cannot receive commands and cannot trade. Sending never raises: a failed
message is logged and the scanner keeps running.
"""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings

log = logging.getLogger("telegram")
# httpx logs every request URL at INFO, and the URL contains the bot token. Keep it out of the logs.
logging.getLogger("httpx").setLevel(logging.WARNING)

NY = ZoneInfo("America/New_York")
LONDON = ZoneInfo("Europe/London")
API = "https://api.telegram.org"
MARKETS = {"nas100": "NAS100", "gold": "Gold", "btc": "BTC"}
OUTCOMES = {"target": "🎯 TARGET hit", "stop": "🛑 STOP hit", "expired": "⌛ expired (never filled)",
            "session_end": "🔔 closed at session end", "filled": "✅ FILLED (entry reached)",
            "invalid": "⚠️ invalid (price jumped past stop/target)"}

# Entry windows, the same as the strategies and the dashboard Session panel (src/sessions.js).
# (name, clock, start minute, end minute). Asia is a range-building window, not an entry window.
SESSIONS = [("London", LONDON, 8 * 60 + 5, 10 * 60), ("New York", NY, 9 * 60 + 35, 15 * 60)]


def enabled() -> bool:
    s = get_settings()
    return bool(s.telegram_bot_token and s.telegram_chat_id)


def send(text: str) -> bool:
    """Send one message. Returns True on success; never raises and never logs the token."""
    s = get_settings()
    if not enabled():
        return False
    token = s.telegram_bot_token.get_secret_value()
    try:
        r = httpx.post(f"{API}/bot{token}/sendMessage", timeout=10,
                       json={"chat_id": s.telegram_chat_id, "text": text, "disable_web_page_preview": True})
        if r.status_code != 200:
            log.warning("telegram send failed: HTTP %s %s", r.status_code, r.text[:200].replace(token, "***"))
            return False
        return True
    except Exception as e:                       # network down etc.
        log.warning("telegram send failed: %s", type(e).__name__)
        return False


def _times(ts: int) -> str:
    ny = datetime.fromtimestamp(ts, NY)
    local = datetime.fromtimestamp(ts).astimezone()
    return f"{ny:%a %H:%M} New York · {local:%H:%M} your time"


def _px(x: float | None) -> str:
    return "-" if x is None else f"{x:,.2f}"


def setup_message(x: dict) -> str:
    """x = scanner._setup_dict(...)"""
    head = ("📢 SIGNAL (strategy passed its backtest)" if x["eligible"]
            else "🧪 PRACTICE ONLY — do not trade (strategy failed its backtest)")
    side = "🟢 LONG" if x["side"] == "LONG" else "🔴 SHORT"
    lines = [head, f"{MARKETS.get(x['market'], x['market'])} {side} · {x['strategy']}",
             f"Entry {_px(x['entry'])} ({x['kind']}) · Stop {_px(x['stop'])} · Target {_px(x['target'])} ({x['rr_target']:g}R)",
             f"Cost ≈ {x['cost_share'] * 100:.0f}% of risk", _times(x["bar_close_ts"])]
    if x.get("news_blackout"):
        lines.append("📰 inside a news blackout")
    if x.get("reason"):
        lines.append(x["reason"])
    lines.append("Paper/learning only. A signal is not a % chance of winning.")
    return "\n".join(lines)


def outcome_message(o: dict) -> str:
    """o = {market, strategy, side, status, r, ts, qualified}"""
    tag = "" if o["qualified"] else " (practice)"
    r = "" if o.get("r") is None else f" · {o['r']:+.2f}R after costs"
    return (f"{OUTCOMES.get(o['status'], o['status'])}{tag}\n"
            f"{MARKETS.get(o['market'], o['market'])} {o['side']} · {o['strategy']}{r}\n{_times(o['ts'])}")


def feed_message(market: str, state: str, detail: str, ts: int) -> str:
    name = MARKETS.get(market, market)
    if state == "open":
        return f"✅ {name} price feed is back.\n{_times(ts)}"
    hint = " Is the MT5 terminal open?" if market in ("nas100", "gold") else ""
    return f"⚠️ {name}: {state} — {detail}.{hint}\n{_times(ts)}"


def news_message(ev, now: int) -> str:
    """Heads-up before a high-impact release, with its usual 30-minute effect (measured 2019-2024)."""
    from app.core import news
    mins = max(1, round((ev.ts - now) / 60))
    lines = [f"📰 {ev.name} in {mins} min ({_times(ev.ts)})"]
    eff = news.effect(ev.name)
    for m in ("nas100", "gold", "btc"):
        if m in eff and eff[m]["x"]:
            lines.append(f"{MARKETS[m]}: usually {eff[m]['x']:.1f}× a normal move (≈{eff[m]['range_pct']:.2f}% in 30 min)")
    lines.append("No new entries from 30 min before to 30 min after. Direction is never predictable.")
    return "\n".join(lines)


NEWS_LEAD = 30 * 60


def sessions_open(ts: int) -> set[str]:
    """Which entry windows are open at ts (weekdays only), plus 'Asia' from 18:00 NY Sun-Thu."""
    ny = datetime.fromtimestamp(ts, NY)
    out = set()
    if ny.weekday() < 5:
        for name, zone, start, end in SESSIONS:
            t = datetime.fromtimestamp(ts, zone)
            if start <= t.hour * 60 + t.minute < end:
                out.add(name)
    if ny.hour >= 18 and ny.weekday() in (6, 0, 1, 2, 3):
        out.add("Asia")
    return out


def session_message(name: str, ts: int) -> str:
    if name == "Asia":
        return f"🌏 Asia session started — range building only (used by London setups).\n{_times(ts)}"
    rule = {"London": "until 10:00 London", "New York": "until 15:00 New York"}[name]
    return f"🕗 {name} entry window is OPEN ({rule}).\n{_times(ts)}"


class Notifier:
    """Remembers what it already told you, so each event is sent once."""

    def __init__(self) -> None:
        self.feed: dict[str, str] = {}
        self.sessions: set[str] | None = None     # None = first cycle: do not announce sessions already open
        self.news_sent: set[int] = set()

    def messages(self, scan: dict, alerts: list[dict], now: int) -> list[str]:
        s = get_settings()
        out: list[str] = []
        if s.telegram_session_alerts:
            current = sessions_open(now)
            if self.sessions is not None:
                out += [session_message(n, now) for n in ("Asia", "London", "New York") if n in current - self.sessions]
            self.sessions = current
        if s.telegram_news_alerts:
            from app.core import news
            for ev in news.load_events():
                if 0 < ev.ts - now <= NEWS_LEAD and ev.ts not in self.news_sent:
                    out.append(news_message(ev, now))
                    self.news_sent.add(ev.ts)
        for m in scan.get("markets", []):
            old, new = self.feed.get(m["key"]), m["state"]
            bad = ("stale", "no data")
            if old is not None and old != new and (new in bad or (old in bad and new == "open")):
                out.append(feed_message(m["key"], new, m["detail"], now))
            self.feed[m["key"]] = new
        for a in alerts:
            if a["type"] == "setup":
                x = a["setup"]
                if (x["eligible"] or s.telegram_practice_alerts) and not x["expired"]:
                    out.append(setup_message(x))
            elif a["type"] == "outcome" and (a["qualified"] or s.telegram_practice_alerts):
                out.append(outcome_message(a))
        return out

    def notify(self, scan: dict, alerts: list[dict], now: int) -> int:
        if not enabled():
            return 0
        return sum(send(t) for t in self.messages(scan, alerts, now))
