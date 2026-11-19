"""Telegram messages that need the database: the monthly results summary and the turn-of-month paper test.

Both are remembered in the `controls` table (state keys), so a restart never sends them twice.
Read-only information; nothing here can place an order.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state, tom_forward
from app.core.news import NY
from app.models import PositionRow, ScannerExecutionRow, ScannerSignalRow

MARKETS = {"nas100": "NAS100", "gold": "Gold", "btc": "BTC"}


def month_bounds(ym: str) -> tuple[int, int]:
    y, m = map(int, ym.split("-"))
    start = datetime(y, m, 1, tzinfo=NY)
    end = datetime(y + (m == 12), 1 if m == 12 else m + 1, 1, tzinfo=NY)
    return int(start.timestamp()), int(end.timestamp())


def previous_month(now_ts: int) -> str:
    d = datetime.fromtimestamp(now_ts, NY)
    y, m = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
    return f"{y}-{m:02d}"


def _line(label: str, rs: list[float]) -> str:
    if not rs:
        return f"{label}: none"
    wins = sum(r > 0 for r in rs)
    return f"{label}: {len(rs)} done · {wins} won · {len(rs) - wins} lost · total {sum(rs):+.2f}R"


def monthly_message(s: Session, ym: str, tom: dict) -> str:
    a, b = month_bounds(ym)
    sig = list(s.scalars(select(ScannerSignalRow).join(ScannerExecutionRow)
                         .where(ScannerExecutionRow.version == 2, ScannerSignalRow.resolved_ts >= a,
                                ScannerSignalRow.resolved_ts < b, ScannerSignalRow.r.is_not(None))))
    pos = list(s.scalars(select(PositionRow).where(PositionRow.status == "closed", PositionRow.closed_ts >= a,
                                                   PositionRow.closed_ts < b)))
    lines = [f"📅 Results for {datetime(*map(int, ym.split('-')), 1):%B %Y} (paper/learning)",
             _line("Real signals (passed strategies)", [x.r for x in sig if x.shown]),
             _line("Practice setups (failed strategies)", [x.r for x in sig if not x.shown])]
    usd = sum(p.pnl_usd or 0 for p in pos)
    lines.append(_line("Paper account trades", [p.r for p in pos if p.r is not None])
                 + (f" · {usd:+.2f} virtual $" if pos else ""))
    a_d, b_d = datetime.fromtimestamp(a, NY).date().isoformat(), datetime.fromtimestamp(b, NY).date().isoformat()
    tom_done = [t for t in tom["trades"] if t["status"] == "done" and a_d <= t["exit_date"] < b_d]
    if tom_done:
        lines += [f"Turn-of-month test: {t['net_pct']:+.2f}% after costs ({t['points']:+.1f} pts)" for t in tom_done]
    else:
        lines.append("Turn-of-month test: no trade finished this month")
    sm = tom["summary"]
    lines.append(f"Turn-of-month so far: {sm['trades']} of {sm['verdict_after']} trades needed — {sm['verdict']}")
    lines.append("No strategy has passed its test yet. Results are not a % chance of winning.")
    return "\n".join(lines)


def tom_message(t: dict) -> str:
    if t["status"] == "open":
        return (f"🗓️ Turn-of-month PAPER test: bought USTEC at the {t['entry_date']} close ({t['entry']:,.2f}).\n"
                f"Sells at the close on {t['exit_date']}. Paper test only — collecting, no verdict.")
    if t["status"] == "done":
        return (f"🗓️ Turn-of-month PAPER test finished: {t['entry']:,.2f} → {t['exit']:,.2f} "
                f"({t['points']:+.1f} pts, {t['net_pct']:+.2f}% after costs).\nPaper test only — collecting, no verdict.")
    return f"🗓️ Turn-of-month PAPER test {t['month']} is void: {t['note']}."


def messages(s: Session, now_ts: int, monthly: bool = True, tom_alerts: bool = True) -> list[str]:
    """Called once per scanner cycle. Writes the 'already sent' marks into the session (caller commits)."""
    out: list[str] = []
    tom = tom_forward.report(now_ts)
    if tom_alerts:
        recent = (datetime.fromtimestamp(now_ts, NY).date() - timedelta(days=14)).isoformat()
        sent = set(filter(None, state.get(s, "tg_tom_sent").split(",")))
        for t in tom["trades"]:
            if not t["counted"] or t["status"] == "scheduled" or t["exit_date"] < recent:
                continue                                   # only the last two weeks: no flood of old news
            mark = f"{t['month']}:{t['status']}"
            if mark not in sent:
                out.append(tom_message(t))
                sent.add(mark)
        state.put(s, "tg_tom_sent", ",".join(sorted(sent)[-12:]))
    ym = previous_month(now_ts)
    if monthly and state.get(s, "tg_monthly_sent") != ym:
        if state.get(s, "tg_monthly_sent") != "":          # first run ever: just remember, don't send an old month
            out.append(monthly_message(s, ym, tom))
        state.put(s, "tg_monthly_sent", ym)
    return out
