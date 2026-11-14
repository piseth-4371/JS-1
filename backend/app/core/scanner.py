"""Signals-only scanner over NAS100, BTC and gold (rules: docs/gold_and_scanner_preregistration.md).

It NEVER places orders and never touches the paper account. Every closed 5-minute bar it:
  1. checks each open market (fresh data, trading window, news blackout),
  2. replays that market's strategies on today's bars and collects setups,
  3. shows ONE signal only from a strategy that PASSED development + validation on that market
     (QUALIFIED below) and whose cost is <= 20% of its risk; otherwise WAIT,
  4. stores every setup (qualified or practice-only) in `scanner_signals`, and later fills in
     what really happened (target / stop / expired) from real prices.
A rank is never a probability of winning.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.features import build_frame, load_m1
from app.core.markets import btc_weekend_mask, nas_hold_mask
from app.core.sources import binance_source as bn
from app.core.strategies import ALL
from app.models import ScannerSignalRow

NY = ZoneInfo("America/New_York")
HISTORY_DAYS = 30
STALE_AFTER = 120            # seconds: newest closed minute must be younger than this
MAX_COST_SHARE = 0.20
NAS_STRATEGIES = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet",
                  "london_trend_fvg", "london_sweep_mss_fvg"]
BTC_STRATEGIES = [n for n in ALL if n.startswith("btc_")]

# (market, strategy) -> validation avg R. ONLY strategies that passed development AND validation on that
# market under the pre-registered rules. As of 2026-11-14 nothing has passed (see docs/lessons.md).
QUALIFIED: dict[tuple[str, str], float] = {}


@dataclass(frozen=True)
class ScanMarket:
    key: str
    label: str
    source: str
    symbol: str
    window: Callable[[np.ndarray, np.ndarray], np.ndarray]
    strategies: list[str]
    cost_points: float = 0.0     # fixed cost per trade in price units
    cost_pct: float = 0.0        # cost as % of price (crypto)

    def open_at(self, ts: int) -> bool:
        d = datetime.fromtimestamp(ts, NY)
        return bool(self.window(np.array([d.hour * 60 + d.minute]), np.array([d.weekday()]))[0])

    def cost(self, price: float) -> float:
        return self.cost_points + price * self.cost_pct / 100


def scan_markets() -> list[ScanMarket]:
    s = get_settings()
    return [
        ScanMarket("nas100", "NAS100", s.engine_source, s.mt5_symbol, nas_hold_mask, NAS_STRATEGIES, cost_points=2.0),
        ScanMarket("btc", "BTC", bn.SOURCE, bn.SYMBOL, btc_weekend_mask, BTC_STRATEGIES, cost_pct=0.12),
        ScanMarket("gold", "Gold", s.engine_source, s.mt5_gold_symbol, nas_hold_mask, NAS_STRATEGIES, cost_points=0.40),
    ]


@dataclass
class Setup:
    market: str
    strategy: str
    side: int
    kind: str
    entry: float
    stop: float
    target: float | None
    rr_target: float
    expiry_ts: int
    bar_close_ts: int
    reason: str
    cost_share: float
    qualified: bool
    news_blackout: bool

    @property
    def eligible(self) -> bool:
        return self.qualified and not self.news_blackout and self.cost_share <= MAX_COST_SHARE


@dataclass
class MarketStatus:
    key: str
    label: str
    state: str                   # open / closed / stale / no data
    detail: str
    last_bar_ts: int | None = None
    setups: list[Setup] = field(default_factory=list)


def pick(setups: list[Setup]) -> Setup | None:
    """The ONE signal to show: eligible setups only; highest validation avg R, then lowest cost share."""
    ok = [x for x in setups if x.eligible]
    if not ok:
        return None
    return sorted(ok, key=lambda x: (-QUALIFIED.get((x.market, x.strategy), 0.0), x.cost_share))[0]


def scan_market(m: ScanMarket, now: int) -> MarketStatus:
    st = MarketStatus(m.key, m.label, "open", "")
    if not m.open_at(now):
        st.state, st.detail = "closed", "outside this market's trading window"
        return st
    m1 = load_m1(m.source, m.symbol, now - HISTORY_DAYS * 86400, now - 59)
    m1 = m1[m1["ts"] + 60 <= now]
    if m1.empty:
        st.state, st.detail = "no data", f"no {m.symbol} bars from {m.source}"
        return st
    st.last_bar_ts = int(m1["ts"].iloc[-1])
    if now - (st.last_bar_ts + 60) > STALE_AFTER:
        st.state, st.detail = "stale", f"newest bar closed {(now - st.last_bar_ts - 60) // 60} min ago"
        return st
    f = build_frame(m1, hold_mask=m.window)
    if f.df5.empty:
        st.state, st.detail = "no data", "not enough data for 5-minute bars"
        return st
    a = f.a
    i = len(a["ts"]) - 1
    day = a["ny_date"][i]
    for name in m.strategies:
        strat = ALL[name]()
        strat.new_day(day)
        order = None
        for j in range(i + 1):
            if a["ny_date"][j] == day:
                o = strat.on_bar(j, a)
                if j == i:
                    order = o
        if order is None:
            continue
        risk = abs(order.entry - order.stop)
        if risk <= 0:
            continue
        st.setups.append(Setup(m.key, name, order.side, order.kind, float(order.entry), float(order.stop),
                               None if order.target is None else float(order.target), float(order.rr_target),
                               int(order.expiry_ts), int(a["close_ts"][i]), order.reason,
                               m.cost(order.entry) / risk, (m.key, name) in QUALIFIED, bool(a["news"][i])))
    st.detail = f"{len(st.setups)} setup(s) on the {datetime.fromtimestamp(int(a['close_ts'][i]), NY):%H:%M} NY bar"
    return st


def record(s: Session, statuses: list[MarketStatus], chosen: Setup | None, now: int, sources: dict[str, str]) -> None:
    for st in statuses:
        for x in st.setups:
            exists = s.scalar(select(ScannerSignalRow.id).where(
                ScannerSignalRow.market == x.market, ScannerSignalRow.strategy == x.strategy,
                ScannerSignalRow.bar_close_ts == x.bar_close_ts))
            if exists:
                continue
            s.add(ScannerSignalRow(market=x.market, strategy=x.strategy, bar_close_ts=x.bar_close_ts, created_ts=now,
                                   side=x.side, kind=x.kind, entry=x.entry, stop=x.stop, target=x.target,
                                   rr_target=x.rr_target, expiry_ts=x.expiry_ts, cost_r=x.cost_share,
                                   qualified=x.qualified, shown=x is chosen, reason=x.reason,
                                   data_source=sources[x.market]))


def resolve(row: ScannerSignalRow, m1, window: Callable, now: int) -> None:
    """Fill in what really happened, from closed 1-minute bars after the signal. Pessimistic: if a bar touches
    both stop and target, the stop counts. Unfilled at expiry -> 'expired'. Window end -> 'session_end'."""
    side, entry, stop = row.side, row.entry, row.stop
    risk = abs(entry - stop)
    target = row.target if row.target is not None else entry + side * row.rr_target * risk
    filled = row.status == "filled"
    for b in m1.itertuples():
        t = int(b.ts)
        if t < row.bar_close_ts or (row.filled_ts and t < row.filled_ts):
            continue
        d = datetime.fromtimestamp(t, NY)
        if not window(np.array([d.hour * 60 + d.minute]), np.array([d.weekday()]))[0]:
            if filled:
                row.status, row.resolved_ts = "session_end", t
                row.r = (b.o - entry) * side / risk - row.cost_r
            else:
                row.status, row.resolved_ts = "expired", t
            return
        if not filled:
            if t >= row.expiry_ts:
                row.status, row.resolved_ts = "expired", t
                return
            hit = (row.kind == "market"
                   or (row.kind == "limit" and (b.l <= entry if side == 1 else b.h >= entry))
                   or (row.kind == "stop" and (b.h >= entry if side == 1 else b.l <= entry)))
            if not hit:
                continue
            filled, row.status, row.filled_ts = True, "filled", t
        if (b.l <= stop) if side == 1 else (b.h >= stop):
            row.status, row.resolved_ts, row.r = "stop", t, -1.0 - row.cost_r
            return
        if t > row.filled_ts and ((b.h >= target) if side == 1 else (b.l <= target)):
            row.status, row.resolved_ts = "target", t
            row.r = abs(target - entry) / risk - row.cost_r
            return


LATEST: dict = {"scanned_ts": None, "signal": None, "markets": [], "note": "scanner has not run yet"}


def run_scan(s: Session, now: int | None = None) -> dict:
    now = now or int(time.time())
    markets = scan_markets()
    statuses = [scan_market(m, now) for m in markets]
    setups = [x for st in statuses for x in st.setups]
    chosen = pick(setups)
    record(s, statuses, chosen, now, {m.key: m.source for m in markets})
    by_key = {m.key: m for m in markets}
    for row in s.scalars(select(ScannerSignalRow).where(ScannerSignalRow.status.in_(("open", "filled")))):
        m = by_key.get(row.market)
        if m is None:
            continue
        m1 = load_m1(m.source, m.symbol, row.bar_close_ts, now - 59)
        resolve(row, m1[m1["ts"] + 60 <= now], m.window, now)
    open_now = [st for st in statuses if st.state == "open"]
    if chosen:
        note = "Signal from a strategy that passed its backtest. Not a guarantee: past results can fail."
    elif not open_now:
        note = "WAIT: no market is open with fresh data."
    elif not QUALIFIED:
        note = "WAIT: no strategy has passed its backtest on any market, so the scanner shows no signal."
    else:
        note = "WAIT: no qualified setup right now (or it failed the news / cost check)."
    LATEST.update({"scanned_ts": now, "note": note,
                   "signal": None if chosen is None else _setup_dict(chosen),
                   "markets": [{"key": st.key, "label": st.label, "state": st.state, "detail": st.detail,
                                "last_bar_ts": st.last_bar_ts, "setups": [_setup_dict(x) for x in st.setups]}
                               for st in statuses]})
    return LATEST


def _setup_dict(x: Setup) -> dict:
    return {"market": x.market, "strategy": x.strategy, "side": "LONG" if x.side == 1 else "SHORT", "kind": x.kind,
            "entry": x.entry, "stop": x.stop, "target": x.target, "rr_target": x.rr_target, "expiry_ts": x.expiry_ts,
            "bar_close_ts": x.bar_close_ts, "reason": x.reason, "cost_share": round(x.cost_share, 3),
            "qualified": x.qualified, "news_blackout": x.news_blackout, "eligible": x.eligible}
