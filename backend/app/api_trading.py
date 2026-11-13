"""API for the dashboard: status, signals, orders, positions, events, and controls.

The kill switch is enforced HERE on the backend: it cancels orders and closes
positions immediately, turns auto-trading off, and is stored in the database.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core import state
from app.core.markets import BTCUSD, MARKETS, NAS100, Market, market_for_strategy
from app.core.paper_broker import PaperBroker
from app.core.risk import RiskSettings
from app.core.sources import binance_source as bn
from app.core.strategies import ALL
from app.db import get_engine
from app.models import BarRow, EventRow, OrderRow, PositionRow, SignalRow

router = APIRouter(prefix="/api")


def _broker(s: Session, market: Market = NAS100) -> PaperBroker:
    return PaperBroker(s, market.instrument, get_settings().starting_balance, market.costs, market=market)


def _feed(market: Market) -> tuple[str, str]:
    st = get_settings()
    return (bn.SOURCE, bn.SYMBOL) if market is BTCUSD else (st.engine_source, st.mt5_symbol)


def _last_bar(s: Session, market: Market):
    src, sym = _feed(market)
    return s.scalar(select(BarRow).where(BarRow.source == src, BarRow.symbol == sym).order_by(desc(BarRow.ts)).limit(1))


def _row(r) -> dict:
    return {c.name: getattr(r, c.name) for c in r.__table__.columns}


@router.get("/overview")
def overview() -> dict:
    now = int(time.time())
    st = get_settings()
    with Session(get_engine()) as s:
        b = _broker(s)
        acct = b.account_state(now)
        last_bar = _last_bar(s, NAS100)
        rs = RiskSettings()
        books = []
        for m in MARKETS.values():
            lb = _last_bar(s, m)
            books.append({"key": m.key, "label": m.label, "symbol": _feed(m)[1], "source": _feed(m)[0],
                          "open_now": m.can_hold(now), "last_bar_ts": lb.ts if lb else None,
                          "last_price": lb.close if lb else None,
                          "stale": (now - lb.ts - 60 > 120) if lb else True,
                          "active_strategy": state.get(s, m.strategy_key),
                          "enabled": m is NAS100 or st.btc_weekend_enabled})
        return {
            "mode": "PAPER",
            "live_trading_available": False,
            "symbol": st.mt5_symbol,
            "starting_balance": st.starting_balance,
            "equity": acct.equity,
            "day_pnl": acct.equity - acct.day_start_equity,
            "day_pnl_pct": (acct.equity / acct.day_start_equity - 1) * 100 if acct.day_start_equity else 0,
            "week_pnl": acct.equity - acct.week_start_equity,
            "week_pnl_pct": (acct.equity / acct.week_start_equity - 1) * 100 if acct.week_start_equity else 0,
            "trades_today": acct.trades_today,
            "max_trades_per_day": rs.max_trades_per_day,
            "consecutive_losses_today": acct.consecutive_losses,
            "open_positions": [_row(p) for p in b.all_open_positions()],
            "pending_orders": [_row(o) for o in b.all_pending_orders()],
            "kill_switch": acct.kill_switch,
            "auto_trading": state.get_bool(s, "auto_trading"),
            "active_strategy": state.get(s, "active_strategy"),
            "engine_enabled": st.engine_enabled,
            "data_source": st.engine_source,
            "last_bar_ts": last_bar.ts if last_bar else None,
            "risk_settings": rs.__dict__,
            "markets": books,
            "trading_now": next((x["key"] for x in books if x["open_now"] and x["enabled"]), None),
        }


@router.get("/signals")
def signals(limit: int = 50) -> list[dict]:
    with Session(get_engine()) as s:
        return [_row(r) for r in s.scalars(select(SignalRow).order_by(desc(SignalRow.bar_close_ts)).limit(limit))]


@router.get("/orders")
def orders(limit: int = 50) -> list[dict]:
    with Session(get_engine()) as s:
        return [_row(r) for r in s.scalars(select(OrderRow).order_by(desc(OrderRow.id)).limit(limit))]


@router.get("/positions")
def positions(limit: int = 100) -> list[dict]:
    with Session(get_engine()) as s:
        return [_row(r) for r in s.scalars(select(PositionRow).order_by(desc(PositionRow.id)).limit(limit))]


@router.get("/events")
def events(limit: int = 100) -> list[dict]:
    with Session(get_engine()) as s:
        return [_row(r) for r in s.scalars(select(EventRow).order_by(desc(EventRow.id)).limit(limit))]


class Toggle(BaseModel):
    enabled: bool


class StrategyChoice(BaseModel):
    name: str


@router.post("/controls/auto-trading")
def set_auto_trading(body: Toggle) -> dict:
    with Session(get_engine()) as s, s.begin():
        if body.enabled and state.get_bool(s, "kill_switch"):
            raise HTTPException(409, "Kill switch is ON. Reset it first.")
        state.put(s, "auto_trading", body.enabled)
        state.log(s, "INFO", "control", f"Auto-trading {'ON' if body.enabled else 'OFF'} (by user)")
    return {"auto_trading": body.enabled}


@router.post("/controls/kill")
def kill() -> dict:
    now = int(time.time())
    st = get_settings()
    with Session(get_engine()) as s, s.begin():
        state.put(s, "kill_switch", True)
        state.put(s, "auto_trading", False)
        for m in MARKETS.values():                   # each book is closed at its OWN last price
            last = _last_bar(s, m)
            _broker(s, m).kill(last.close if last else None, now)
        state.log(s, "WARN", "kill_switch", "KILL SWITCH activated by user", now)
    return {"kill_switch": True, "auto_trading": False}


@router.post("/controls/reset-kill")
def reset_kill() -> dict:
    with Session(get_engine()) as s, s.begin():
        state.put(s, "kill_switch", False)
        state.log(s, "INFO", "kill_switch", "Kill switch reset by user (auto-trading stays OFF)")
    return {"kill_switch": False, "auto_trading": False}


@router.post("/controls/strategy")
def set_strategy(body: StrategyChoice) -> dict:
    if body.name not in ALL:
        raise HTTPException(400, f"Unknown strategy. Choose one of {list(ALL)}")
    with Session(get_engine()) as s, s.begin():
        m = market_for_strategy(body.name)
        state.put(s, m.strategy_key, body.name)
        state.log(s, "INFO", "control", f"{m.label}: active strategy set to {body.name}")
    return {"active_strategy": body.name, "market": m.key}


@router.get("/journal/metrics")
def journal_metrics() -> dict:
    """Agent 5 - Performance Analyst for PAPER trades. Says clearly when the sample is too small."""
    from app.backtest.metrics import MIN_TRADES_FOR_CONCLUSION, compute

    with Session(get_engine()) as s:
        closed = list(s.scalars(select(PositionRow).where(PositionRow.status == "closed").order_by(PositionRow.closed_ts)))
        sig = list(s.scalars(select(SignalRow)))
    if closed:
        months = max((closed[-1].closed_ts - closed[0].opened_ts) / 86400 / 30.44, 1 / 30)
    else:
        months = 0
    st = compute(closed, months, RiskSettings().risk_pct)
    rejected = [x for x in sig if x.action != "WAIT" and x.risk_approved is False]
    reasons: dict[str, int] = {}
    for x in rejected:
        for r in x.risk_reasons:
            key = r.split(" would risk")[0]
            reasons[key] = reasons.get(key, 0) + 1
    return {
        "closed_trades": st.n,
        "win_rate": st.win_rate,
        "avg_win_r": st.avg_win_r,
        "avg_loss_r": st.avg_loss_r,
        "expectancy_r": st.expectancy_r,
        "total_r": st.total_r,
        "profit_factor": None if st.profit_factor == float("inf") else st.profit_factor,
        "max_drawdown_pct": st.max_dd_pct,
        "longest_losing_streak": st.longest_losing_streak,
        "pnl_usd": sum(p.pnl_usd or 0 for p in closed),
        "signals_total": len(sig),
        "signals_actionable": sum(1 for x in sig if x.action != "WAIT"),
        "signals_rejected": len(rejected),
        "rejection_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "enough_data": st.n >= MIN_TRADES_FOR_CONCLUSION,
        "verdict": (f"Only {st.n} closed trades. At least {MIN_TRADES_FOR_CONCLUSION} are needed before "
                    "drawing any conclusion. Do not change the rules based on this.")
                   if st.n < MIN_TRADES_FOR_CONCLUSION else
                   "Sample is large enough to describe, but compare with the backtest before changing anything.",
    }
