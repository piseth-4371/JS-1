"""Signals-only scanner snapshot and versioned simulated performance."""
from __future__ import annotations

import math
import statistics
import time
from dataclasses import asdict

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import news, scanner, tom_forward
from app.core.cost_observations import read_observations
from app.db import get_engine
from app.models import ScannerSignalRow

router = APIRouter()


def summary(group: list[ScannerSignalRow]) -> dict:
    rs = [x.r for x in group if x.r is not None]
    n = len(rs)
    wins = sum(r > 0 for r in rs)
    interval = None
    avg_interval = None
    if n:
        z = 1.96
        p = wins / n
        denominator = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denominator
        radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
        interval = [round(100 * (center - radius), 1), round(100 * (center + radius), 1)]
    if n >= 30:
        margin = 1.96 * statistics.stdev(rs) / math.sqrt(n)
        avg_interval = [round(statistics.mean(rs) - margin, 3), round(statistics.mean(rs) + margin, 3)]
    return {"resolved": n, "wins": wins, "win_rate": round(wins / n * 100, 1) if n else None,
            "win_rate_95_range": interval, "avg_r_95_range": avg_interval,
            "avg_r": round(statistics.mean(rs), 3) if n else None,
            "total_r": round(sum(rs), 2), "recorded": len(group),
            "expired": sum(x.status == "expired" for x in group),
            "invalid": sum(x.status == "invalid" for x in group),
            "cancelled": sum(x.status == "cancelled" for x in group),
            "pending": sum(x.status in ("open", "filled") for x in group)}


@router.get("/api/scanner")
def get_scanner(limit: int = Query(40, ge=1, le=200)) -> dict:
    with Session(get_engine()) as s:
        rows = list(s.scalars(select(ScannerSignalRow).order_by(ScannerSignalRow.bar_close_ts.desc()).limit(limit)))
        all_rows = list(s.scalars(select(ScannerSignalRow)))
    current = [x for x in all_rows if x.execution is not None and x.execution.version == 2]
    snapshot = dict(scanner.LATEST)
    now = int(time.time())
    signal = snapshot.get("signal")
    if signal and (now - (snapshot.get("scanned_ts") or 0) > 60
                   or now >= signal["expiry_ts"] or news.entry_block_reason(now)
                   or (signal["market"], signal["strategy"]) not in scanner.QUALIFIED
                   or not next(m for m in scanner.scan_markets() if m.key == signal["market"]).open_at(now)):
        snapshot.update(signal=None, note="WAIT: latest signal is stale, expired, or no longer eligible.")
    observations = read_observations()
    try:
        tom = tom_forward.report(now)
    except Exception as e:                       # never break the scanner card over this
        tom = {"error": type(e).__name__, "trades": [], "summary": None, "next": None}
    return {
        "turn_of_month": tom,
        **snapshot,
        "qualified_strategies": [{"market": m, "strategy": n, "validation_avg_r": v}
                                 for (m, n), v in scanner.QUALIFIED.items()],
        "costs": [{"market": m, "assumptions": asdict(c), "observation": observations.get(m),
                   "note": "Spread observations do not measure slippage or account-specific fees. Assumptions remain in use."}
                  for m, c in scanner.COSTS.items()],
        "track_record": {"shown": summary([x for x in current if x.shown]),
                         "practice": summary([x for x in current if not x.shown]),
                         "legacy_excluded": len(all_rows) - len(current),
                         "by_market": [{"market": m,
                                        "shown": summary([x for x in current if x.market == m and x.shown]),
                                        "practice": summary([x for x in current if x.market == m and not x.shown])}
                                       for m in scanner.COSTS],
                         "note": "Simulated fills from closed minute bars, with assumed costs; not actual trades. "
                                 "95% ranges assume independent trades; overlapping signals can understate uncertainty. "
                                 "Average-R ranges require 30 completed trades; this is not proof of an edge."},
        "recent": [{"market": x.market, "strategy": x.strategy, "bar_close_ts": x.bar_close_ts,
                    "side": "LONG" if x.side == 1 else "SHORT", "kind": x.kind, "entry": x.entry, "stop": x.stop,
                    "target": x.target if x.target is not None else x.entry + x.side * x.rr_target * abs(x.entry-x.stop),
                    "qualified": x.qualified, "shown": x.shown, "status": x.status, "r": x.r,
                    "fill_price": x.execution.fill_price if x.execution else None,
                    "exit_price": x.execution.exit_price if x.execution else None,
                    "legacy": x.execution is None, "data_source": x.data_source} for x in rows],
    }
