"""Event-driven backtester.

How it avoids fooling itself:
- Strategies only see 5m bars AFTER they close; orders become active at that close.
- Fills and exits are simulated on the following 1-minute bars, in time order.
- If one minute touches BOTH stop and target, we assume the STOP happened first.
- On the minute an order fills, only the stop is checked (no same-minute profit).
- Price gaps: limit fills at the better open, stops exit at the worse open.
- Costs on every trade: spread, plus slippage on market/stop entries and on stop/forced exits.
- Every order goes through the real Risk Manager (risk.evaluate), with the same
  daily/weekly limits, 3 trades/day, 1 position, 2-loss stop as live.
- All positions are closed at the end of the book's window (NAS100 15:55 New York).
- High-impact news (app/core/news.py): no new entry within ±30 min of CPI/NFP/FOMC,
  pending orders are cancelled inside that window, no trading outside the calendar's coverage.

Results are measured in R (profit divided by the planned risk), so they don't
depend on account size. Separately we check what the $10 account would allow.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.core.features import Frame
from app.core.fills import Costs, check_exit, net_points, try_fill
from app.core.risk import FRACTIONAL, USTEC, AccountState, OrderRequest, RiskSettings, evaluate
from app.core.strategies.base import Order, Strategy

__all__ = ["Costs", "Result", "Trade", "run", "min_account_for"]


@dataclass
class Trade:
    strategy: str
    side: int
    kind: str
    ny_date: object
    entry_ts: int
    exit_ts: int
    entry: float
    stop: float
    target: float
    exit: float
    exit_reason: str
    risk_pts: float
    r: float
    risk_pct: float
    equity_after: float


@dataclass
class Result:
    strategy: str
    trades: list[Trade] = field(default_factory=list)
    signals: int = 0
    rejections: Counter = field(default_factory=Counter)
    cancelled: Counter = field(default_factory=Counter)


def _iso_week(d):
    y, w, _ = d.isocalendar()
    return y, w


def run(strategy: Strategy, f: Frame, settings: RiskSettings | None = None, costs: Costs | None = None,
        start_equity: float = 10.0) -> Result:
    settings = settings or RiskSettings()
    costs = costs or Costs()
    a, m = f.a, f.m1
    res = Result(strategy.name)
    acct = AccountState(start_equity, start_equity, start_equity)

    pending: dict | None = None     # {"order": Order, "risk_pct": float}
    pos: dict | None = None
    mi, n1 = 0, len(m["ts"])
    cur_day = cur_week = None

    def close_position(j, price, reason):
        nonlocal pos
        p = pos
        side = p["side"]
        r = net_points(side, p["entry"], price, p["kind"], reason, costs) / p["risk_pts"]
        acct.equity *= 1 + p["risk_pct"] / 100 * r
        acct.open_positions = 0
        acct.consecutive_losses = acct.consecutive_losses + 1 if r < 0 else 0
        res.trades.append(Trade(strategy.name, side, p["kind"], p["ny_date"], p["entry_ts"], int(m["ts"][j]),
                                p["entry"], p["stop"], p["target"], price, reason, p["risk_pts"], r,
                                p["risk_pct"], acct.equity))
        pos = None

    def exit_check(j, fill_bar: bool):
        hit = check_exit(pos["side"], pos["stop"], pos["target"], m["o"][j], m["h"][j], m["l"][j], fill_bar)
        if hit:
            close_position(j, *hit)

    def process_minute(j):
        nonlocal pending, pos
        if pos is not None:
            if not m["can_hold"][j]:
                close_position(j, m["o"][j], "session_end")
            else:
                exit_check(j, fill_bar=False)
        if pending is None or pos is not None:
            return
        od: Order = pending["order"]
        if m["news"][j]:
            res.cancelled["news blackout"] += 1
            pending = None
            return
        if m["ts"][j] >= od.expiry_ts or not m["can_hold"][j]:
            res.cancelled["expired"] += 1
            pending = None
            return
        s = od.side
        fill = try_fill(od.kind, s, od.entry, m["o"][j], m["h"][j], m["l"][j])
        if fill is None:
            return
        risk_pts = (fill - od.stop) * s
        if risk_pts <= 0:
            res.cancelled["gap through stop"] += 1
            pending = None
            return
        target = od.target if od.target is not None else fill + s * od.rr_target * risk_pts
        pos = dict(side=s, kind=od.kind, entry=fill, stop=od.stop, target=target, risk_pts=risk_pts,
                   risk_pct=pending["risk_pct"], entry_ts=int(m["ts"][j]), ny_date=m["ny_date"][j])
        pending = None
        acct.trades_today += 1
        acct.open_positions = 1
        exit_check(j, fill_bar=True)

    for i in range(len(a["ts"])):
        t_close = a["close_ts"][i]
        while mi < n1 and m["ts"][mi] < t_close:
            process_minute(mi)
            mi += 1

        day = a["ny_date"][i]
        if day != cur_day:
            cur_day = day
            strategy.new_day(day)
            acct.day_start_equity = acct.equity
            acct.trades_today = 0
            acct.consecutive_losses = 0
            wk = _iso_week(day)
            if wk != cur_week:
                cur_week = wk
                acct.week_start_equity = acct.equity

        if pending is not None:
            od = pending["order"]
            if od.cancel_level is not None and (a["c"][i] - od.cancel_level) * od.side < 0:
                res.cancelled["invalidated (closed beyond FVG)"] += 1
                pending = None

        order = strategy.on_bar(i, a)
        if order is None:
            continue
        res.signals += 1
        if not a["news_known"][i]:
            res.rejections["No news calendar for this date"] += 1
            continue
        if a["news"][i]:
            res.rejections["High-impact news blackout"] += 1
            continue
        if pos is not None or pending is not None:
            res.rejections["Busy: a position or order is already open"] += 1
            continue
        risk_pts = (order.entry - order.stop) * order.side
        target = order.target if order.target is not None else order.entry + order.side * order.rr_target * risk_pts
        dec = evaluate(OrderRequest(order.side, order.entry, order.stop, target), acct, FRACTIONAL, settings)
        if not dec.approved:
            for reason in dec.reasons:
                res.rejections[reason.split(" (")[0]] += 1
            continue
        pending = {"order": order, "risk_pct": dec.risk_pct}

    return res


def min_account_for(trade: Trade, settings: RiskSettings | None = None, inst=USTEC) -> float:
    """Smallest balance where the instrument's minimum lot fits this trade's stop within the risk %."""
    settings = settings or RiskSettings()
    return inst.min_lot * trade.risk_pts * inst.value_per_point_per_lot / (settings.risk_pct / 100)
