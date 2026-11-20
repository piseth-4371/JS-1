"""Telegram messages that need the database: the monthly results summary and the turn-of-month paper test.

Both are remembered in the `controls` table (state keys), so a restart never sends them twice.
Read-only information; nothing here can place an order.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import drawdown_check, manual, state, tom_forward
from app.core.news import NY
from app.models import EventRow, PositionRow, ScannerExecutionRow, ScannerSignalRow, SignalRow

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


def drawdown(start: float, changes: list[float], compound: bool = False) -> dict:
    """Biggest fall from a previous high along start, start+c1, ... (or start*(1+c1/100)... when compound).

    Returns the biggest fall (`max`, same units as start) and as % of the high it fell from (`max_pct`),
    plus how far the last value is below its high (`now`, `now_pct`). All are >= 0.
    """
    eq = peak = start
    worst = worst_pct = 0.0
    for c in changes:
        eq = eq * (1 + c / 100) if compound else eq + c
        peak = max(peak, eq)
        if peak - eq > worst:
            worst = peak - eq
            worst_pct = (peak - eq) / peak * 100 if peak > 0 else 0.0
    now = peak - eq
    return {"max": worst, "max_pct": worst_pct, "now": now, "now_pct": now / peak * 100 if peak > 0 else 0.0}


def _neg(x: float, digits: int = 2) -> str:
    """A fall shown with a minus sign, or 0 when there was none (never '-0.00')."""
    return f"-{x:.{digits}f}" if round(x, digits) > 0 else f"{0:.{digits}f}"


def _line(label: str, rs: list[float]) -> str:
    if not rs:
        return f"{label}: none"
    wins = sum(r > 0 for r in rs)
    dd = drawdown(0.0, rs)["max"]
    return (f"{label}: {len(rs)} done · {wins} won · {len(rs) - wins} lost · total {sum(rs):+.2f}R"
            f" · worst drop {_neg(dd)}R")


def process_lines(s: Session, a: int, b: int, pos: list[PositionRow]) -> list[str]:
    """Process, not profit (finance-psychology skill: judge the process). Paper trades that ended by the plan,
    your own manual actions with their reasons, and paper signals the risk manager said no to."""
    events = list(s.scalars(select(EventRow).where(EventRow.type == manual.TYPE, EventRow.ts >= a, EventRow.ts < b)
                            .order_by(EventRow.ts, EventRow.id)))
    kills = sum(e.message.startswith("KILL SWITCH") for e in events)
    resets = sum(e.message.startswith("Kill switch reset") for e in events)
    blocked = len(list(s.scalars(select(SignalRow.id).where(SignalRow.risk_approved.is_(False),
                                                            SignalRow.bar_close_ts >= a, SignalRow.bar_close_ts < b))))
    by_plan = sum(p.exit_reason != "kill_switch" for p in pos)
    lines = [f"Process: paper trades ended by the plan {by_plan} of {len(pos)} · manual actions {len(events)} "
             f"(KILL {kills}, reset {resets}, other {len(events) - kills - resets}) · "
             f"risk manager said no to {blocked} paper signals"]
    for e in events[-5:]:
        lines.append(f"  {datetime.fromtimestamp(e.ts, NY):%m-%d %H:%M} {e.message}")
    if len(events) > 5:
        lines.append(f"  (+{len(events) - 5} earlier, see the event log)")
    return lines


def monthly_message(s: Session, ym: str, tom: dict) -> str:
    from app.config import get_settings
    a, b = month_bounds(ym)
    sig = list(s.scalars(select(ScannerSignalRow).join(ScannerExecutionRow)
                         .where(ScannerExecutionRow.version == 2, ScannerSignalRow.resolved_ts >= a,
                                ScannerSignalRow.resolved_ts < b, ScannerSignalRow.r.is_not(None))
                         .order_by(ScannerSignalRow.resolved_ts)))
    upto = list(s.scalars(select(PositionRow).where(PositionRow.status == "closed", PositionRow.closed_ts < b)
                          .order_by(PositionRow.closed_ts, PositionRow.id)))
    pos = [p for p in upto if p.closed_ts >= a]
    lines = [f"📅 Results for {datetime(*map(int, ym.split('-')), 1):%B %Y} (paper/learning)",
             _line("Real signals (passed strategies)", [x.r for x in sig if x.shown]),
             _line("Practice setups (failed strategies)", [x.r for x in sig if not x.shown])]
    usd = sum(p.pnl_usd or 0 for p in pos)
    lines.append(_line("Paper account trades", [p.r for p in pos if p.r is not None])
                 + (f" · {usd:+.2f} virtual $" if pos else ""))
    if upto:
        start = float(get_settings().starting_balance)
        before = start + sum(p.pnl_usd or 0 for p in upto if p.closed_ts < a)
        month = drawdown(before, [p.pnl_usd or 0 for p in pos])
        ever = drawdown(start, [p.pnl_usd or 0 for p in upto])
        lines.append(f"Paper account drawdown: this month {_neg(month['max'])} virtual $ ({_neg(month['max_pct'], 1)}%) · "
                     f"biggest ever {_neg(ever['max'])} ({_neg(ever['max_pct'], 1)}%) · "
                     f"now {ever['now_pct']:.1f}% below its high")
        try:
            lines += drawdown_check.telegram_lines(s)
        except Exception:                        # the summary still goes out without this line
            pass
    lines += process_lines(s, a, b, pos)
    a_d, b_d = datetime.fromtimestamp(a, NY).date().isoformat(), datetime.fromtimestamp(b, NY).date().isoformat()
    tom_done = [t for t in tom["trades"] if t["status"] == "done" and a_d <= t["exit_date"] < b_d]
    if tom_done:
        lines += [f"Turn-of-month test: {t['net_pct']:+.2f}% after costs ({t['points']:+.1f} pts)" for t in tom_done]
    else:
        lines.append("Turn-of-month test: no trade finished this month")
    tom_upto = [t["net_pct"] for t in tom["trades"] if t["counted"] and t["status"] == "done" and t["exit_date"] < b_d]
    if tom_upto:
        dd = drawdown(100.0, tom_upto, compound=True)
        lines.append(f"Turn-of-month drawdown: biggest {_neg(dd['max_pct'])}% · now {dd['now_pct']:.2f}% below its high")
    sm = tom["summary"]
    lines.append(f"Turn-of-month so far: {sm['trades']} of {sm['verdict_after']} trades needed — {sm['verdict']}")
    lines.append("Drawdown = the biggest fall from a previous high.")
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
