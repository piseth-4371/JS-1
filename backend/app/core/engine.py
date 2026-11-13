"""The trading engine: one `cycle()` connects all the agents.

    data (DB) -> checks -> PaperBroker fills/exits -> kill switch?
      -> Strategy (replayed over today's bars) -> Risk Manager -> PaperBroker.place

Each cycle is safe to repeat: a 5m bar that already has a signal is skipped,
and order ids are unique. The strategy is re-run from the start of the day,
so a restart loses no strategy memory.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import news, state
from app.core.features import build_frame, load_m1
from app.core.fills import Costs
from app.core.market_data import Bar, validate_bars
from app.core.markets import NAS100, Market
from app.core.paper_broker import PaperBroker
from app.core.risk import Instrument, OrderRequest, RiskSettings, evaluate
from app.core.strategies import ALL
from app.db import get_engine
from app.models import SignalRow

HISTORY_DAYS = 30          # enough for ATR percentiles and the 15m EMA50
STALE_AFTER = 120          # seconds after a minute bar closes before data counts as stale
MAX_SIGNAL_AGE = 600       # don't act on a 5m bar that closed more than 10 min ago


@dataclass
class CycleResult:
    status: str
    detail: str = ""
    signal: dict = field(default_factory=dict)


class TradingEngine:
    def __init__(self, source: str, symbol: str, starting_balance: float, instrument: Instrument | None = None,
                 settings: RiskSettings | None = None, costs: Costs | None = None, market: Market = NAS100):
        self.source, self.symbol, self.market = source, symbol, market
        self.inst, self.balance = instrument or market.instrument, starting_balance
        self.settings, self.costs = settings or RiskSettings(), costs or market.costs

    def _broker(self, s: Session) -> PaperBroker:
        return PaperBroker(s, self.inst, self.balance, self.costs, market=self.market)

    def startup(self, now_ts: int | None = None) -> list[str]:
        now_ts = now_ts or int(time.time())
        with Session(get_engine()) as s, s.begin():
            fixes = self._broker(s).reconcile(now_ts)
            state.log(s, "INFO", "engine_start", f"{self.market.label} engine started (paper only). Repairs: {fixes or 'none'}", now_ts)
            return fixes

    def cycle(self, now_ts: int | None = None) -> CycleResult:
        now_ts = now_ts or int(time.time())
        with Session(get_engine()) as s, s.begin():
            return self._cycle(s, now_ts)

    # ------------------------------------------------------------------
    def _cycle(self, s: Session, now: int) -> CycleResult:
        broker = self._broker(s)
        mk = self.market

        m1 = load_m1(self.source, self.symbol, now - HISTORY_DAYS * 86400, now - 59)
        m1 = m1[m1["ts"] + 60 <= now]                     # closed minutes only
        if m1.empty:
            return CycleResult("WAIT", "no market data in the database")
        bars = [Bar(self.source, self.symbol, "M1", int(r.ts), r.o, r.h, r.l, r.c, r.v) for r in m1.itertuples()]
        rep = validate_bars(bars[-2000:])
        if not rep.ok:
            state.log(s, "ERROR", "bad_data", "; ".join(rep.errors[:3]), now)
            return CycleResult("WAIT", "market data failed validation")

        last = bars[-1]
        if now - (last.ts + 60) > STALE_AFTER:
            if mk.can_hold(now):
                state.log(s, "WARN", "stale_data", f"{mk.label}: newest bar closed {(now - last.ts - 60) // 60} min ago", now)
            return CycleResult("WAIT", "data is stale (market closed or feed stopped)")

        # 1. Broker: process new closed minutes (fills, stops, targets, session end)
        cursor = int(state.get(s, mk.cursor_key))
        if cursor == 0:
            state.put(s, mk.cursor_key, last.ts)     # first run: start from now, not from history
            cursor = last.ts
        for b in bars:
            if b.ts > cursor:                             # only minutes not processed yet
                broker.process_minute(b)

        # 2. Kill switch overrides everything
        if state.get_bool(s, "kill_switch"):
            broker.kill(last.close, now)
            return CycleResult("KILLED", "kill switch is ON - nothing will trade")

        # This book only trades inside its own holding window (NAS100 weekdays, BTC weekends).
        if not mk.can_hold(now):
            return CycleResult("WAIT", f"{mk.label}: outside this book's trading hours")

        # 3. Strategy on the newest CLOSED 5m bar.
        # Cheap check first: if the newest finished 5m bar was already evaluated, skip the heavy work.
        name = state.get(s, mk.strategy_key)
        if name not in ALL or not mk.owns(name):
            name = mk.default_strategy
        newest_close = (last.ts + 60) // 300 * 300
        if s.scalar(select(SignalRow.id).where(SignalRow.strategy == name, SignalRow.bar_close_ts == newest_close)):
            return CycleResult("WAIT", "this 5m bar was already evaluated")
        f = build_frame(m1, hold_mask=mk.hold_mask)
        if f.df5.empty:
            return CycleResult("WAIT", "not enough data for 5m bars")
        a = f.a
        i = len(a["ts"]) - 1
        close_ts = int(a["close_ts"][i])
        if now - close_ts > MAX_SIGNAL_AGE:
            return CycleResult("WAIT", "no fresh 5m bar")
        if s.scalar(select(SignalRow.id).where(SignalRow.strategy == name, SignalRow.bar_close_ts == close_ts)):
            return CycleResult("WAIT", "this 5m bar was already evaluated")
        broker.on_5m_close(float(a["c"][i]), close_ts)

        strat = ALL[name]()
        day = a["ny_date"][i]
        strat.new_day(day)
        order = None
        for j in range(i + 1):
            if a["ny_date"][j] == day:
                o = strat.on_bar(j, a)
                if j == i:
                    order = o

        sig = SignalRow(strategy=name, bar_close_ts=close_ts, created_ts=now, action="WAIT",
                        data_source=self.source, data_ts=last.ts, risk_reasons=[])
        s.add(sig)
        if order is None:
            sig.reason = "No setup on this bar"
            s.flush()
            return CycleResult("WAIT", sig.reason, {"strategy": name, "bar_close_ts": close_ts})

        # 4. Risk Manager (absolute veto)
        risk_pts = (order.entry - order.stop) * order.side
        target = order.target if order.target is not None else order.entry + order.side * order.rr_target * risk_pts
        sig.action = "LONG" if order.side == 1 else "SHORT"
        sig.kind, sig.entry, sig.stop, sig.target = order.kind, order.entry, order.stop, target
        sig.expiry_ts, sig.reason = order.expiry_ts, order.reason
        acct = broker.account_state(now)
        dec = evaluate(OrderRequest(order.side, order.entry, order.stop, target), acct, self.inst, self.settings)
        reasons = list(dec.reasons)
        block = news.entry_block_reason(close_ts)
        if block:
            reasons.insert(0, block)
        if broker.pending_orders():
            reasons.append("An order is already pending")
        if not state.get_bool(s, "auto_trading"):
            reasons.append("Auto-trading is OFF (signal recorded only)")
        sig.risk_approved = not reasons
        sig.risk_reasons, sig.risk_qty = reasons, dec.qty
        s.flush()
        if reasons:
            state.log(s, "INFO", "signal_rejected", f"{sig.action} {name}: {'; '.join(reasons)}", now)
            return CycleResult("REJECTED", "; ".join(reasons), {"strategy": name, "action": sig.action})

        # 5. Execute on the paper broker
        broker.place(order, dec.qty, sig.id, now)
        return CycleResult("ORDER", f"{sig.action} {dec.qty:g} lots", {"strategy": name, "action": sig.action})
