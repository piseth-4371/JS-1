"""Agent 3 — Risk Manager. Deterministic Python with ABSOLUTE veto.

Every order must pass `evaluate()`. It returns ALL reasons for rejection,
so the dashboard can show exactly why a trade was blocked.

HARD_LIMITS are ceilings written in code. Settings may be stricter, never looser:
creating RiskSettings with a looser value raises an error.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

HARD_LIMITS = {
    "risk_pct": 1.0,               # max % of equity risked per trade
    "daily_loss_pct": 2.0,
    "weekly_loss_pct": 5.0,
    "max_trades_per_day": 3,
    "max_open_positions": 1,
    "max_consecutive_losses": 2,
    "max_leverage": 20.0,
}


@dataclass(frozen=True)
class RiskSettings:
    risk_pct: float = 0.5
    daily_loss_pct: float = 2.0
    weekly_loss_pct: float = 5.0
    max_trades_per_day: int = 3
    max_open_positions: int = 1
    max_consecutive_losses: int = 2
    max_leverage: float = 20.0
    min_rr: float = 2.0

    def __post_init__(self):
        for k, cap in HARD_LIMITS.items():
            v = getattr(self, k)
            if not 0 < v <= cap:
                raise ValueError(f"{k}={v} is outside the allowed range (0, {cap}]")
        if self.min_rr < 1.0:
            raise ValueError("min_rr must be at least 1.0")


@dataclass(frozen=True)
class Instrument:
    symbol: str
    value_per_point_per_lot: float   # $ gained/lost per 1.0 price move for 1 lot
    min_lot: float
    lot_step: float
    max_lot: float = 1e9


# From scripts/check_mt5.py on MetaQuotes-Demo, 2026-11-13: contract size 1, tick 0.01 = $0.01 per lot.
USTEC = Instrument("USTEC", value_per_point_per_lot=1.0, min_lot=0.1, lot_step=0.1, max_lot=250)
# Research-only: unlimited divisibility, to measure strategy quality in R independent of lot size.
FRACTIONAL = Instrument("FRACTIONAL", value_per_point_per_lot=1.0, min_lot=0.0, lot_step=1e-9)


@dataclass
class AccountState:
    equity: float
    day_start_equity: float
    week_start_equity: float
    trades_today: int = 0
    open_positions: int = 0
    consecutive_losses: int = 0
    kill_switch: bool = False


@dataclass(frozen=True)
class OrderRequest:
    side: int          # +1 long, -1 short
    entry: float
    stop: float | None
    target: float | None


@dataclass
class RiskDecision:
    approved: bool
    qty: float = 0.0
    risk_usd: float = 0.0
    risk_pct: float = 0.0
    reasons: list[str] = field(default_factory=list)


def evaluate(req: OrderRequest, acct: AccountState, inst: Instrument, s: RiskSettings) -> RiskDecision:
    reasons: list[str] = []

    # 1. Global switches and account limits
    if acct.kill_switch:
        reasons.append("Kill switch is ON")
    if acct.equity <= 0:
        reasons.append("Equity is zero or negative")
    if acct.day_start_equity > 0 and (acct.equity / acct.day_start_equity - 1) * 100 <= -s.daily_loss_pct:
        reasons.append(f"Daily loss limit {s.daily_loss_pct}% reached")
    if acct.week_start_equity > 0 and (acct.equity / acct.week_start_equity - 1) * 100 <= -s.weekly_loss_pct:
        reasons.append(f"Weekly loss limit {s.weekly_loss_pct}% reached")
    if acct.trades_today >= s.max_trades_per_day:
        reasons.append(f"Max {s.max_trades_per_day} trades per day reached")
    if acct.open_positions >= s.max_open_positions:
        reasons.append(f"Max {s.max_open_positions} open position(s) reached")
    if acct.consecutive_losses >= s.max_consecutive_losses:
        reasons.append(f"{acct.consecutive_losses} losses in a row today - stop trading (anti-revenge rule)")

    # 2. Order shape: stop-loss is mandatory and must be on the correct side
    if req.side not in (1, -1):
        reasons.append("Side must be LONG (+1) or SHORT (-1)")
    if req.stop is None or not math.isfinite(req.stop):
        reasons.append("Stop-loss is missing")
        return RiskDecision(False, reasons=reasons)
    risk_pts = (req.entry - req.stop) * req.side
    if risk_pts <= 0:
        reasons.append("Stop-loss is on the wrong side of the entry")
        return RiskDecision(False, reasons=reasons)
    if req.target is None or (req.target - req.entry) * req.side <= 0:
        reasons.append("Take-profit is missing or on the wrong side")
    else:
        rr = (req.target - req.entry) * req.side / risk_pts
        if rr < s.min_rr - 1e-9:
            reasons.append(f"Reward:risk {rr:.2f} is below minimum {s.min_rr}")

    # 3. Position size
    allowed_usd = acct.equity * s.risk_pct / 100
    per_lot_risk = risk_pts * inst.value_per_point_per_lot
    qty = allowed_usd / per_lot_risk
    max_by_leverage = acct.equity * s.max_leverage / (req.entry * inst.value_per_point_per_lot)
    qty = min(qty, max_by_leverage, inst.max_lot)
    qty = math.floor(qty / inst.lot_step + 1e-9) * inst.lot_step
    if qty <= 0 or qty < inst.min_lot:
        min_risk = inst.min_lot * per_lot_risk
        reasons.append(
            f"Minimum lot {inst.min_lot} would risk ${min_risk:.2f} "
            f"({min_risk / acct.equity * 100:.1f}% of equity) > allowed ${allowed_usd:.2f} ({s.risk_pct}%)"
        )
        qty = 0.0

    risk_usd = qty * per_lot_risk
    return RiskDecision(
        approved=not reasons,
        qty=qty if not reasons else 0.0,
        risk_usd=risk_usd if not reasons else 0.0,
        risk_pct=risk_usd / acct.equity * 100 if (not reasons and acct.equity > 0) else 0.0,
        reasons=reasons,
    )
