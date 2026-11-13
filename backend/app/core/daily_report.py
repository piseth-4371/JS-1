"""Daily paper-trading report (read-only): what the engine saw, did and refused on one New York date.

Builds the journal needed for later performance reviews. Only facts stored in the
database are reported; nothing is estimated or invented.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import news
from app.models import EventRow, OrderRow, PositionRow, SignalRow

NY = ZoneInfo("America/New_York")


def _day_bounds(day: date) -> tuple[int, int]:
    a = datetime(day.year, day.month, day.day, tzinfo=NY)
    b = a + timedelta(days=1)
    return int(a.timestamp()), int(b.timestamp())


def _t(ts: int | None) -> str:
    return datetime.fromtimestamp(ts, NY).strftime("%H:%M") if ts else "-"


def build(s: Session, day: date, starting_balance: float) -> str:
    t0, t1 = _day_bounds(day)
    sigs = list(s.scalars(select(SignalRow).where(SignalRow.bar_close_ts >= t0, SignalRow.bar_close_ts < t1)))
    orders = list(s.scalars(select(OrderRow).where(OrderRow.created_ts >= t0, OrderRow.created_ts < t1)))
    closed = list(s.scalars(select(PositionRow).where(PositionRow.closed_ts >= t0, PositionRow.closed_ts < t1)
                            .order_by(PositionRow.closed_ts)))
    warn = list(s.scalars(select(EventRow).where(EventRow.ts >= t0, EventRow.ts < t1, EventRow.level != "INFO")
                          .order_by(EventRow.ts)))
    realized_before = sum(p.pnl_usd or 0 for p in s.scalars(
        select(PositionRow).where(PositionRow.status == "closed", PositionRow.closed_ts < t0)))
    day_pnl = sum(p.pnl_usd or 0 for p in closed)
    start_eq = starting_balance + realized_before

    out = [f"# Paper trading report — {day} (New York date)", "",
           f"Equity {start_eq:,.2f} → {start_eq + day_pnl:,.2f} USD (day {day_pnl:+,.2f}, "
           f"{(day_pnl / start_eq * 100 if start_eq else 0):+.2f}%). Paper money only.", ""]

    evs = [e for e in news.load_events() if t0 <= e.ts < t1]
    out.append("## High-impact news")
    out += [f"- {e.label} (±30 min blackout) — {e.source}" for e in evs] or ["- none scheduled"]
    if not news.covered(t0):
        out.append("- WARNING: the news calendar does not cover this date; the engine does not trade")
    out.append("")

    out.append("## Signals")
    if not sigs:
        out.append("- none recorded (engine off, market closed, or outside the strategy windows)")
    else:
        by = Counter((x.strategy, x.action) for x in sigs)
        out += [f"- {strat}: {act} × {n}" for (strat, act), n in sorted(by.items())]
        actionable = [x for x in sigs if x.action != "WAIT"]
        for x in actionable:
            verdict = "APPROVED" if x.risk_approved else "REJECTED: " + "; ".join(x.risk_reasons or [])
            out.append(f"  - {_t(x.bar_close_ts)} {x.strategy} {x.action} entry {x.entry:.2f} stop {x.stop:.2f} "
                       f"target {x.target:.2f} → {verdict}")
    out.append("")

    out.append("## Orders")
    out += [f"- {_t(o.created_ts)} {o.client_order_id}: {'BUY' if o.side == 1 else 'SELL'} {o.qty:g} {o.kind} "
            f"@ {o.entry:.2f} → {o.status}{(' (' + o.status_reason + ')') if o.status_reason else ''}"
            for o in orders] or ["- none"]
    out.append("")

    out.append("## Closed trades")
    if closed:
        rs = [p.r for p in closed if p.r is not None]
        out += [f"- {p.strategy} {'LONG' if p.side == 1 else 'SHORT'} {_t(p.opened_ts)}→{_t(p.closed_ts)} "
                f"entry {p.entry:.2f} exit {p.exit_price:.2f} ({p.exit_reason}) {p.r:+.2f}R {p.pnl_usd:+.2f} USD"
                for p in closed]
        out.append(f"- Total {sum(rs):+.2f}R over {len(rs)} trade(s). One day is far too few trades to judge a strategy.")
    else:
        out.append("- none")
    out.append("")

    out.append("## Warnings and errors")
    out += [f"- {_t(e.ts)} {e.level} {e.type}: {e.message}" for e in warn] or ["- none"]
    return "\n".join(out) + "\n"
