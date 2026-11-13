"""Fill and exit rules for one 1-minute bar. Pure functions.

Used by BOTH the backtester and the live paper broker, so paper trading
behaves exactly like the backtest.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Costs:
    spread: float = 1.5     # index points per round trip [assumption: typical USTEC CFD spread]
    slippage: float = 0.5   # extra points on market/stop fills


def try_fill(kind: str, side: int, entry: float, o: float, h: float, l: float) -> float | None:  # noqa: E741
    """Price at which a pending order fills on this minute, or None."""
    if kind == "market":
        return o
    if kind == "limit":
        if (o - entry) * side <= 0:          # opened already at/through the limit: better price
            return o
        if (l if side == 1 else h) * side <= entry * side:
            return entry
        return None
    if kind == "stop":
        if (o - entry) * side >= 0:          # gapped through the trigger: worse price
            return o
        if (h if side == 1 else l) * side >= entry * side:
            return entry
        return None
    raise ValueError(f"unknown order kind {kind}")


def check_exit(side: int, stop: float, target: float, o: float, h: float, l: float,  # noqa: E741
               fill_bar: bool) -> tuple[float, str] | None:
    """(exit price, reason) if the stop or target is hit on this minute.

    Stop is checked first (pessimistic). On the minute the position opened
    (`fill_bar`), only the stop counts.
    """
    if side == 1:
        if not fill_bar and o <= stop:
            return o, "stop"
        if l <= stop:
            return stop, "stop"
        if not fill_bar and h >= target:
            return target, "target"
    else:
        if not fill_bar and o >= stop:
            return o, "stop"
        if h >= stop:
            return stop, "stop"
        if not fill_bar and l <= target:
            return target, "target"
    return None


def net_points(side: int, entry: float, exit_price: float, entry_kind: str, exit_reason: str, costs: Costs) -> float:
    """Profit in index points after spread and slippage."""
    pts = (exit_price - entry) * side - costs.spread
    if entry_kind in ("market", "stop"):
        pts -= costs.slippage
    if exit_reason in ("stop", "session_end", "kill_switch"):
        pts -= costs.slippage
    return pts
