"""Paper-versus-backtest comparison (rules: docs/paper_vs_backtest_plan.md). Pure functions.

Matches signals by (5m bar close time, side) and trades by (fill minute, side), then compares every field.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

PRICE_TOL, R_TOL = 1e-6, 1e-9


@dataclass(frozen=True)
class SignalRec:
    bar_close_ts: int
    side: int
    kind: str
    entry: float
    stop: float
    target: float | None
    note: str = ""            # paper: risk / rejection reasons; backtest: empty


@dataclass(frozen=True)
class TradeRec:
    entry_ts: int
    side: int
    entry: float
    stop: float
    target: float
    exit_ts: int | None
    exit: float | None
    reason: str | None
    r: float | None


SIGNAL_FIELDS = {"kind": None, "entry": PRICE_TOL, "stop": PRICE_TOL, "target": PRICE_TOL}
TRADE_FIELDS = {"entry": PRICE_TOL, "stop": PRICE_TOL, "target": PRICE_TOL, "exit_ts": None, "exit": PRICE_TOL,
                "reason": None, "r": R_TOL}


def _same(a, b, tol) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if tol is None:
        return a == b
    return abs(float(a) - float(b)) <= tol


@dataclass
class Comparison:
    identical: int = 0
    different: list = field(default_factory=list)   # [(key, {field: (paper, backtest)})]
    paper_only: list = field(default_factory=list)
    backtest_only: list = field(default_factory=list)

    @property
    def total_matched(self) -> int:
        return self.identical + len(self.different)

    def as_dict(self) -> dict:
        return {"identical": self.identical, "different": [[k, d] for k, d in self.different],
                "paper_only": [asdict(x) for x in self.paper_only], "backtest_only": [asdict(x) for x in self.backtest_only]}


def compare(paper: list, backtest: list, key, fields: dict) -> Comparison:
    out = Comparison()
    bt = {key(x): x for x in backtest}
    for p in sorted(paper, key=key):
        b = bt.pop(key(p), None)
        if b is None:
            out.paper_only.append(p)
            continue
        diff = {f: (getattr(p, f), getattr(b, f)) for f, tol in fields.items() if not _same(getattr(p, f), getattr(b, f), tol)}
        if diff:
            out.different.append((key(p), diff))
        else:
            out.identical += 1
    out.backtest_only = sorted(bt.values(), key=key)
    return out


def compare_signals(paper: list[SignalRec], backtest: list[SignalRec]) -> Comparison:
    return compare(paper, backtest, lambda s: (int(s.bar_close_ts), int(s.side)), SIGNAL_FIELDS)


def compare_trades(paper: list[TradeRec], backtest: list[TradeRec]) -> Comparison:
    return compare(paper, backtest, lambda t: (int(t.entry_ts), int(t.side)), TRADE_FIELDS)


def backtest_signals(strategy, a: dict, first_close_ts: int = 0, last_close_ts: int | None = None) -> list[SignalRec]:
    """Every order the strategy emits on the 5m table `a`, calling it exactly as backtest/engine.run does
    (new_day on a date change, then on_bar for every bar). Only bars closing in [first, last] are returned."""
    out, cur = [], None
    for i in range(len(a["ts"])):
        day = a["ny_date"][i]
        if day != cur:
            cur = day
            strategy.new_day(day)
        o = strategy.on_bar(i, a)
        ct = int(a["close_ts"][i])
        if o is None or ct < first_close_ts or (last_close_ts is not None and ct > last_close_ts):
            continue
        risk = (o.entry - o.stop) * o.side
        target = o.target if o.target is not None else o.entry + o.side * o.rr_target * risk
        out.append(SignalRec(ct, int(o.side), o.kind, float(o.entry), float(o.stop), float(target)))
    return out


def signal_for_trade(t, signals: list[SignalRec]) -> SignalRec | None:
    """The signal that produced a trade: the latest same-side signal whose 5m bar closed at or before the fill."""
    best = None
    for s in signals:
        if s.side == t.side and s.bar_close_ts <= t.entry_ts and (best is None or s.bar_close_ts > best.bar_close_ts):
            best = s
    return best


def trade_from_backtest(t) -> TradeRec:
    return TradeRec(int(t.entry_ts), int(t.side), float(t.entry), float(t.stop), float(t.target), int(t.exit_ts),
                    float(t.exit), t.exit_reason, float(t.r))


def trade_from_position(p) -> TradeRec:
    closed = p.status == "closed"
    return TradeRec(int(p.opened_ts), int(p.side), float(p.entry), float(p.stop), float(p.target),
                    int(p.closed_ts) if closed else None, float(p.exit_price) if closed else None,
                    p.exit_reason if closed else None, float(p.r) if closed and p.r is not None else None)


def signal_from_row(s) -> SignalRec:
    note = "approved" if s.risk_approved else "; ".join(s.risk_reasons or []) or "not evaluated"
    return SignalRec(int(s.bar_close_ts), 1 if s.action == "LONG" else -1, s.kind, float(s.entry), float(s.stop),
                     float(s.target) if s.target is not None else None, note)
