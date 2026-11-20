""""Is this drop normal?" — the paper account's current drawdown compared with the same strategy's backtest.

Idea from the finance-psychology skill (recency bias): a bad week feels like a signal to change something. This
puts the drop next to how often the backtest (2019-2024, same strategy, same R units) was at least that far below
its high. Display only: no rule, limit, strategy or signal uses it. "Normal" means normal FOR THIS STRATEGY, and
every strategy here failed its test, so a normal drop is still a drop of a losing strategy.

Drawdown in R: equity starts at 0R, adds each closed trade's R, and the drop is the distance below the highest
value so far. Measured after each closed trade, in both the paper account and the backtest.
"""
from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.models import PositionRow

ROOT = Path(__file__).resolve().parents[2]
BACKTEST_FILES = [ROOT / "data" / "backtest_trades.csv", ROOT / "data" / "backtest_trades_btc.csv"]
MIN_BACKTEST_TRADES = 30
NORMAL_SHARE = 0.20      # at least this often in the backtest -> "normal"
SEEN_SHARE = 0.05        # at least this often -> "unusual, but seen before"; above 0 -> "rare"

_cache: dict = {"key": None, "data": {}}


def underwater(rs: list[float]) -> list[float]:
    """Distance below the running high (>= 0) after each trade, equity starting at 0R."""
    eq = peak = 0.0
    out = []
    for r in rs:
        eq += r
        peak = max(peak, eq)
        out.append(peak - eq)
    return out


def compare(paper_rs: list[float], backtest_rs: list[float]) -> dict:
    """Pure: paper R results (in order) vs backtest R results (in order) for the same strategy."""
    paper_dd = underwater(paper_rs)
    now = paper_dd[-1] if paper_dd else 0.0
    biggest = max(paper_dd, default=0.0)
    bt_dd = underwater(backtest_rs)
    out = {"paper_trades": len(paper_rs), "now_r": round(now, 2), "biggest_r": round(biggest, 2),
           "backtest_trades": len(backtest_rs), "backtest_total_r": round(sum(backtest_rs), 1),
           "backtest_biggest_r": round(max(bt_dd, default=0.0), 2), "share": None}
    if len(backtest_rs) < MIN_BACKTEST_TRADES:
        return {**out, "level": "no backtest", "text": f"Not enough backtest trades to compare (need {MIN_BACKTEST_TRADES})."}
    if not paper_rs:
        return {**out, "level": "no trades", "text": "No closed paper trades yet."}
    if round(now, 2) <= 0:
        return {**out, "level": "at high", "text": "At its high: no drop right now."}
    share = sum(d >= now for d in bt_dd) / len(bt_dd)
    out["share"] = round(share, 3)
    pct = f"{share * 100:.0f}%"
    if share >= NORMAL_SHARE:
        level, text = "normal", f"Normal for this strategy: the backtest was this far down or more after {pct} of its trades."
    elif share >= SEEN_SHARE:
        level, text = "unusual", f"Unusual, but seen before: the backtest was this far down after {pct} of its trades."
    elif share > 0:
        level, text = "rare", f"Rare: the backtest was this far down after only {pct} of its trades. Worth a check, not a rule change."
    else:
        level, text = "deeper", "Deeper than any drop in the backtest. Check for a bug or a data problem before anything else."
    return {**out, "level": level, "text": text}


def load_backtest() -> dict[str, list[float]]:
    """R per trade by strategy, in exit order, from the saved backtest CSVs (re-read when a file changes)."""
    key = tuple((str(p), p.stat().st_mtime) for p in BACKTEST_FILES if p.exists())
    if key != _cache["key"]:
        rows: dict[str, list[tuple[int, float]]] = {}
        for p in BACKTEST_FILES:
            if p.exists():
                with p.open(newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        rows.setdefault(row["strategy"], []).append((int(float(row["exit_ts"])), float(row["r"])))
        _cache.update(key=key, data={k: [r for _, r in sorted(v)] for k, v in rows.items()})
    return _cache["data"]


def report(s: Session) -> dict:
    """One row per strategy with closed paper trades, plus the active NAS100 strategy if it has none yet."""
    closed = list(s.scalars(select(PositionRow).where(PositionRow.status == "closed", PositionRow.r.is_not(None))
                            .order_by(PositionRow.closed_ts, PositionRow.id)))
    by: dict[str, list[float]] = {}
    for p in closed:
        by.setdefault(p.strategy, []).append(float(p.r))
    active = state.get(s, "active_strategy")
    names = list(by) + ([active] if active and active not in by else [])
    bt = load_backtest()
    rows = [{"strategy": n, "active": n == active, **compare(by.get(n, []), bt.get(n, []))} for n in names]
    return {"rows": rows, "backtest_found": bool(bt),
            "note": "Compared with the same strategy's 2019-2024 backtest in R. Display only: it never changes a rule. "
                    "Every strategy here failed its test, so 'normal' means normal for a losing strategy."}


def telegram_lines(s: Session) -> list[str]:
    out = []
    for r in report(s)["rows"]:
        if r["paper_trades"]:
            out.append(f"Is this drop normal? {r['strategy']}: now {r['now_r']:.2f}R below its high "
                       f"(biggest {r['biggest_r']:.2f}R, backtest biggest {r['backtest_biggest_r']:.2f}R). {r['text']}")
    return out
