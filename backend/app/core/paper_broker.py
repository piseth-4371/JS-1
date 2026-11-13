"""Agent 4 — Execution & Order Manager: an internal PAPER broker.

No real orders are ever sent anywhere. Orders, positions and P&L live in the
database, so the state survives a server restart.

Safety features:
- Duplicate protection: client_order_id is unique (strategy + bar close time).
- Each 1-minute bar is processed once (a cursor is stored in the DB).
- Fill/exit rules are shared with the backtester (app/core/fills.py).
- kill(): cancels every pending order and closes every open position.
- reconcile(): run at startup to repair impossible states.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import state
from app.core.fills import Costs, check_exit, net_points, try_fill
from app.core.market_data import Bar
from app.core.markets import NAS100, Market
from app.core.risk import AccountState, Instrument
from app.core.strategies.base import Order
from app.models import OrderRow, PositionRow

NY = ZoneInfo("America/New_York")


def can_hold(ts: int) -> bool:
    """NAS100 book: positions may be open only 03:00-15:55 New York on weekdays."""
    return NAS100.can_hold(ts)


def ny_day_start(ts: int) -> int:
    d = datetime.fromtimestamp(ts, NY)
    return int(datetime(d.year, d.month, d.day, tzinfo=NY).timestamp())


def ny_week_start(ts: int) -> int:
    d = datetime.fromtimestamp(ts, NY)
    monday = (d - timedelta(days=d.weekday())).date()
    return int(datetime(monday.year, monday.month, monday.day, tzinfo=NY).timestamp())


class PaperBroker:
    """One book (NAS100 or BTC) of the shared paper account.

    Orders/positions are managed only for this book's strategies (`market.owns`),
    but account limits (equity, trades today, open positions) count BOTH books.
    """

    def __init__(self, s: Session, instrument: Instrument, starting_balance: float, costs: Costs | None = None,
                 market: Market = NAS100):
        self.s, self.inst, self.start, self.costs = s, instrument, starting_balance, costs or Costs()
        self.market = market

    # ------------------------------------------------------------- account
    def _realized_before(self, ts: int | None = None) -> float:
        q = select(func.coalesce(func.sum(PositionRow.pnl_usd), 0.0)).where(PositionRow.status == "closed")
        if ts is not None:
            q = q.where(PositionRow.closed_ts < ts)
        return float(self.s.scalar(q))

    def account_state(self, now_ts: int) -> AccountState:
        day0, week0 = ny_day_start(now_ts), ny_week_start(now_ts)
        today = self.s.scalars(select(PositionRow).where(PositionRow.opened_ts >= day0).order_by(PositionRow.opened_ts)).all()
        closed_today = [p for p in today if p.status == "closed"]
        streak = 0
        for p in reversed(closed_today):
            if p.r is not None and p.r < 0:
                streak += 1
            else:
                break
        return AccountState(
            equity=self.start + self._realized_before(),
            day_start_equity=self.start + self._realized_before(day0),
            week_start_equity=self.start + self._realized_before(week0),
            trades_today=len(today),
            open_positions=len(self.all_open_positions()),
            consecutive_losses=streak,
            kill_switch=state.get_bool(self.s, "kill_switch"),
        )

    def all_open_positions(self) -> list[PositionRow]:
        return list(self.s.scalars(select(PositionRow).where(PositionRow.status == "open")))

    def all_pending_orders(self) -> list[OrderRow]:
        return list(self.s.scalars(select(OrderRow).where(OrderRow.status == "pending")))

    def open_positions(self) -> list[PositionRow]:
        """This book only."""
        return [p for p in self.all_open_positions() if self.market.owns(p.strategy)]

    def pending_orders(self) -> list[OrderRow]:
        """This book only."""
        return [o for o in self.all_pending_orders() if self.market.owns(o.strategy)]

    # ------------------------------------------------------------- orders
    @staticmethod
    def client_order_id(order: Order) -> str:
        return f"{order.strategy}-{order.placed_ts}"

    def place(self, order: Order, qty: float, signal_id: int | None, now_ts: int) -> OrderRow | None:
        """Create a pending paper order. Returns None if this exact order already exists."""
        coid = self.client_order_id(order)
        if self.s.scalar(select(OrderRow).where(OrderRow.client_order_id == coid)):
            state.log(self.s, "WARN", "duplicate_order", f"Order {coid} already exists - ignored", now_ts)
            return None
        row = OrderRow(client_order_id=coid, signal_id=signal_id, strategy=order.strategy, side=order.side,
                       kind=order.kind, qty=qty, entry=order.entry, stop=order.stop, target=order.target,
                       rr_target=order.rr_target, cancel_level=order.cancel_level, created_ts=now_ts,
                       active_from_ts=order.placed_ts, expiry_ts=order.expiry_ts, status="pending")
        self.s.add(row)
        self.s.flush()
        state.log(self.s, "INFO", "order_placed",
                  f"{'BUY' if order.side == 1 else 'SELL'} {qty:g} {self.inst.symbol} {order.kind} @ {order.entry:.2f} "
                  f"SL {order.stop:.2f} ({coid})", now_ts)
        return row

    def _cancel(self, o: OrderRow, reason: str, ts: int) -> None:
        o.status, o.status_reason = "cancelled", reason
        state.log(self.s, "INFO", "order_cancelled", f"{o.client_order_id}: {reason}", ts)

    def _close(self, p: PositionRow, price: float, reason: str, ts: int) -> None:
        pts = net_points(p.side, p.entry, price, p.kind, reason, self.costs)
        p.status, p.closed_ts, p.exit_price, p.exit_reason = "closed", ts, price, reason
        p.pnl_usd = pts * p.qty * self.inst.value_per_point_per_lot
        p.r = pts / p.risk_pts
        state.log(self.s, "INFO", "position_closed",
                  f"{p.strategy} closed at {price:.2f} ({reason}): {p.r:+.2f}R, ${p.pnl_usd:+.2f}", ts)

    # ------------------------------------------------------------- per bar
    def on_5m_close(self, close: float, ts: int) -> None:
        """Cancel FVG orders whose zone was closed through before filling."""
        for o in self.pending_orders():
            if o.cancel_level is not None and o.active_from_ts <= ts and (close - o.cancel_level) * o.side < 0:
                self._cancel(o, "invalidated (5m close beyond FVG)", ts)

    def process_minute(self, b: Bar) -> None:
        cursor = int(state.get(self.s, self.market.cursor_key))
        if b.ts <= cursor:
            return  # already processed (e.g. after a restart)
        hold = self.market.can_hold(b.ts)
        for p in self.open_positions():
            if not hold:
                self._close(p, b.open, "session_end", b.ts)
                continue
            hit = check_exit(p.side, p.stop, p.target, b.open, b.high, b.low, fill_bar=False)
            if hit:
                self._close(p, hit[0], hit[1], b.ts)
        for o in self.pending_orders():
            if b.ts < o.active_from_ts:
                continue
            if b.ts >= o.expiry_ts or not hold:
                self._cancel(o, "expired", b.ts)
                continue
            if self.all_open_positions():
                continue                     # one position in total, across both books
            fill = try_fill(o.kind, o.side, o.entry, b.open, b.high, b.low)
            if fill is None:
                continue
            risk_pts = (fill - o.stop) * o.side
            if risk_pts <= 0:
                self._cancel(o, "price gapped through the stop", b.ts)
                continue
            target = o.target if o.target is not None else fill + o.side * o.rr_target * risk_pts
            o.status, o.fill_price, o.fill_ts = "filled", fill, b.ts
            p = PositionRow(order_id=o.id, strategy=o.strategy, side=o.side, kind=o.kind, qty=o.qty, entry=fill,
                            stop=o.stop, target=target, opened_ts=b.ts, status="open", risk_pts=risk_pts)
            self.s.add(p)
            self.s.flush()
            state.log(self.s, "INFO", "order_filled", f"{o.client_order_id} filled at {fill:.2f}", b.ts)
            hit = check_exit(p.side, p.stop, p.target, b.open, b.high, b.low, fill_bar=True)
            if hit:
                self._close(p, hit[0], hit[1], b.ts)
        state.put(self.s, self.market.cursor_key, b.ts)

    # ------------------------------------------------------------- safety
    def kill(self, last_price: float | None, ts: int) -> None:
        for o in self.pending_orders():
            self._cancel(o, "kill switch", ts)
        for p in self.open_positions():
            if last_price is None:
                state.log(self.s, "ERROR", "kill_switch", f"Position {p.id} open but no price to close it", ts)
                continue
            self._close(p, last_price, "kill_switch", ts)

    def reconcile(self, now_ts: int) -> list[str]:
        """Repair impossible states after a restart. Returns what was fixed."""
        fixes = []
        opens = self.all_open_positions()
        if len(opens) > self.inst_max_positions:
            state.put(self.s, "kill_switch", True)
            fixes.append(f"{len(opens)} open positions (max {self.inst_max_positions}) - kill switch turned ON")
        for o in self.pending_orders():
            if o.expiry_ts <= now_ts:
                self._cancel(o, "expired while the server was off", now_ts)
                fixes.append(f"cancelled stale order {o.client_order_id}")
        for f in fixes:
            state.log(self.s, "WARN", "reconcile", f, now_ts)
        return fixes

    inst_max_positions = 1
