"""GET /api/scanner: the signals-only 3-market scanner (latest scan + its own track record)."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import scanner
from app.db import get_engine
from app.models import ScannerSignalRow

router = APIRouter()


@router.get("/api/scanner")
def get_scanner(limit: int = 40) -> dict:
    with Session(get_engine()) as s:
        rows = list(s.scalars(select(ScannerSignalRow).order_by(ScannerSignalRow.bar_close_ts.desc()).limit(limit)))
        done = list(s.scalars(select(ScannerSignalRow).where(ScannerSignalRow.r.is_not(None))))

    def summary(group: list[ScannerSignalRow]) -> dict:
        rs = [x.r for x in group]
        return {"resolved": len(rs), "wins": sum(r > 0 for r in rs),
                "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
                "total_r": round(sum(rs), 2) if rs else 0.0}

    return {
        **scanner.LATEST,
        "qualified_strategies": [{"market": m, "strategy": n, "validation_avg_r": v}
                                 for (m, n), v in scanner.QUALIFIED.items()],
        "track_record": {"shown": summary([x for x in done if x.shown]),
                         "practice": summary([x for x in done if not x.shown]),
                         "note": "Outcomes come from real prices after each signal; costs included. "
                                 "Needs 30+ resolved signals before it means anything."},
        "recent": [{"market": x.market, "strategy": x.strategy, "bar_close_ts": x.bar_close_ts,
                    "side": "LONG" if x.side == 1 else "SHORT", "kind": x.kind, "entry": x.entry, "stop": x.stop,
                    "target": x.target, "qualified": x.qualified, "shown": x.shown, "status": x.status, "r": x.r,
                    "data_source": x.data_source} for x in rows],
    }
