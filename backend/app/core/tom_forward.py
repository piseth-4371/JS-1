"""Turn-of-the-month PAPER forward test (docs/turn_of_month_forward_preregistration.md).

Buy at the close of the second-to-last NYSE trading day of each month, sell at the close of the 3rd trading day of
the next month, on the MT5 USTEC bars the engine stores. Nothing is ever ordered: results are computed from closes.
"""
from __future__ import annotations

import calendar
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from app.core.news import NY

SPREAD = 0.0002
FINANCING = 0.07
FORWARD_FROM = date(2025, 12, 1)       # entries on/after this date count (data E19 never saw)
VERDICT_AFTER = 36
CLOSE_MINUTES = range(15 * 60 + 55, 16 * 60)   # 15:55-15:59 NY bars; the latest one is the day's close


# ---------- NYSE holiday rules (fixed in advance) ----------
def _nth_weekday(y: int, m: int, weekday: int, n: int) -> date:
    d = date(y, m, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last_weekday(y: int, m: int, weekday: int) -> date:
    d = date(y, m, calendar.monthrange(y, m)[1])
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _easter(y: int) -> date:
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    return date(y, month, (h + l - 7 * m + 114) % 31 + 1)


def _observed(d: date) -> date:
    return d - timedelta(days=1) if d.weekday() == 5 else d + timedelta(days=1) if d.weekday() == 6 else d


def nyse_holidays(y: int) -> set[date]:
    out = {_nth_weekday(y, 1, 0, 3), _nth_weekday(y, 2, 0, 3), _easter(y) - timedelta(days=2),
           _last_weekday(y, 5, 0), _observed(date(y, 7, 4)), _nth_weekday(y, 9, 0, 1),
           _nth_weekday(y, 11, 3, 4), _observed(date(y, 12, 25))}
    if y >= 2022:
        out.add(_observed(date(y, 6, 19)))
    ny = date(y, 1, 1)
    if ny.weekday() != 5:                      # Saturday New Year's Day is not moved back into December
        out.add(_observed(ny))
    return out


def trading_days(y: int, m: int) -> list[date]:
    hol = nyse_holidays(y)
    return [date(y, m, d) for d in range(1, calendar.monthrange(y, m)[1] + 1)
            if date(y, m, d).weekday() < 5 and date(y, m, d) not in hol]


def window(y: int, m: int) -> tuple[date, date]:
    """(entry day, exit day) for the turn from month (y, m) into the next month."""
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return trading_days(y, m)[-2], trading_days(ny, nm)[2]


# ---------- prices ----------
def daily_closes(m1: pd.DataFrame) -> dict[date, float]:
    """Close of each New York day = latest 15:55-15:59 bar's close."""
    if m1.empty:
        return {}
    ny = pd.to_datetime(m1["ts"], unit="s", utc=True).dt.tz_convert(NY)
    mod = (ny.dt.hour * 60 + ny.dt.minute).to_numpy()
    keep = np.isin(mod, list(CLOSE_MINUTES))
    sub = pd.DataFrame({"d": ny.dt.date.to_numpy()[keep], "ts": m1["ts"].to_numpy()[keep], "c": m1["c"].to_numpy()[keep]})
    last = sub.sort_values("ts").groupby("d").tail(1)
    return {d: float(c) for d, c in zip(last["d"], last["c"])}


@dataclass(frozen=True)
class Trade:
    month: str             # "2026-10" = turn from October into November
    entry_date: str
    exit_date: str
    status: str            # scheduled / open / done / void
    counted: bool          # part of the forward test (entry on/after FORWARD_FROM)
    entry: float | None = None
    exit: float | None = None
    points: float | None = None
    gross_pct: float | None = None
    net_pct: float | None = None
    note: str = ""


def build(closes: dict[date, float], today: date, first_month: tuple[int, int]) -> list[Trade]:
    """Every month turn from first_month up to the next one that has not finished."""
    out, (y, m) = [], first_month
    while True:
        entry_d, exit_d = window(y, m)
        if entry_d > today + timedelta(days=40):
            break
        e, x = closes.get(entry_d), closes.get(exit_d)
        base = dict(month=f"{y}-{m:02d}", entry_date=entry_d.isoformat(), exit_date=exit_d.isoformat(),
                    counted=entry_d >= FORWARD_FROM)
        if e is not None and x is not None:
            nights = (exit_d - entry_d).days
            gross = x / e - 1
            net = gross - SPREAD - FINANCING * nights / 365
            out.append(Trade(**base, status="done", entry=e, exit=x, points=round(x - e, 2),
                             gross_pct=round(gross * 100, 3), net_pct=round(net * 100, 3)))
        elif e is None and entry_d < today:
            out.append(Trade(**base, status="void", note="no close on the entry day (PC/MT5 off or no data)"))
        elif e is not None and x is None and exit_d < today:
            out.append(Trade(**base, status="void", entry=e, note="no close on the exit day (PC/MT5 off or no data)"))
        elif e is not None:
            out.append(Trade(**base, status="open", entry=e))
        else:
            out.append(Trade(**base, status="scheduled"))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def summary(trades: list[Trade]) -> dict:
    done = [t for t in trades if t.counted and t.status == "done"]
    net = np.array([t.net_pct for t in done], dtype=float)
    s = {"trades": len(done), "wins": int((net > 0).sum()), "losses": int((net <= 0).sum()),
         "total_net_pct": round(float(net.sum()), 3), "avg_net_pct": round(float(net.mean()), 3) if len(net) else None,
         "void": sum(t.counted and t.status == "void" for t in trades), "verdict_after": VERDICT_AFTER}
    if len(done) < VERDICT_AFTER:
        s["verdict"] = "collecting — no verdict"
    else:
        means = np.random.default_rng(11).choice(net, size=(5000, len(net))).mean(axis=1)
        low = float(np.percentile(means, 2.5))
        s["verdict"] = ("negative" if net.mean() <= 0 else "passes" if low > 0 else "inconclusive")
    return s


def as_dicts(trades: list[Trade]) -> list[dict]:
    return [asdict(t) for t in trades]


def ny_today(now_ts: int) -> date:
    return datetime.fromtimestamp(now_ts, NY).date()


# ---------- from the database (MT5 USTEC bars the engine stores) ----------
_CACHE: dict = {}


def report(now_ts: int) -> dict:
    """Trades + summary for the dashboard and Telegram. Cached for 5 minutes."""
    key = now_ts // 300
    if _CACHE.get("key") == key:
        return _CACHE["value"]
    from sqlalchemy import text

    from app.config import get_settings
    from app.db import get_engine
    st = get_settings()
    q = text("SELECT ts, close AS c FROM bars WHERE source=:s AND symbol=:y AND timeframe='M1' ORDER BY ts")
    with get_engine().connect() as conn:
        m1 = pd.DataFrame(conn.execute(q, {"s": st.engine_source, "y": st.mt5_symbol}).fetchall(), columns=["ts", "c"])
    value = report_from_bars(m1, now_ts, f"{st.engine_source} {st.mt5_symbol}")
    _CACHE.update(key=key, value=value)
    return value


def report_from_bars(m1: pd.DataFrame, now_ts: int, source: str) -> dict:
    today = ny_today(now_ts)
    if m1.empty:
        return {"source": source, "trades": [], "summary": summary([]), "next": None,
                "note": "No MT5 USTEC bars stored yet: start the engine with MT5 open."}
    first_day = ny_today(int(m1["ts"].iloc[0]))
    trades = [t for t in build(daily_closes(m1), today, (first_day.year, first_day.month))
              if date.fromisoformat(t.entry_date) >= first_day]
    nxt = next((t for t in trades if t.status in ("scheduled", "open")), None)
    return {"source": source, "trades": as_dicts(trades), "summary": summary(trades),
            "next": asdict(nxt) if nxt else None,
            "note": "Paper forward test — collecting, no verdict before 36 trades. Buy at the close of the "
                    "2nd-to-last trading day, sell at the close of the 3rd trading day. Never ordered."}
