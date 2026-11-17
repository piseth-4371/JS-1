"""Paper engine versus backtester on the same minutes (rules: docs/paper_vs_backtest_plan.md).

  replay  (default): stored MT5 minutes -> REAL paper engine in a throwaway DB, and the backtester on the same minutes
  journal          : the real paper journal in data/app.db versus a backtest over the same minutes
  --report         : merge every result into docs/paper_vs_backtest_report.md

    .\\.venv\\Scripts\\python scripts\\paper_vs_backtest.py --strategy orb --start 2026-10-14 --end 2026-11-13
    .\\.venv\\Scripts\\python scripts\\paper_vs_backtest.py --strategy orb --mode journal
    .\\.venv\\Scripts\\python scripts\\paper_vs_backtest.py --report

Paper only: no orders are sent anywhere; the real paper account is never touched by replay mode.
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
NY = ZoneInfo("America/New_York")
OUT = ROOT / "data" / "reports" / "paper_compare"


def ny_midnight(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=NY).timestamp())


def window(strategy: str, d: date) -> tuple[int, int]:
    t = ny_midnight(d)
    start = (2 * 60 + 30) if strategy.startswith("london_") else (8 * 60 + 30)
    return t + start * 60, t + (16 * 60 + 10) * 60


def backtest_side(strategy, src, days, balance):
    from app.backtest import paper_compare as pc
    from app.backtest.engine import run
    from app.core.features import build_frame
    from app.core.markets import NAS100
    from app.core.risk import RiskSettings
    from app.core.strategies import ALL
    frame = build_frame(src.reset_index(drop=True), hold_mask=NAS100.hold_mask)
    wins = [window(strategy, d) for d in days]
    res = run(ALL[strategy](), frame, RiskSettings(), NAS100.costs, start_equity=balance, valid_dates=set(days))
    lo, hi = wins[0][0], wins[-1][1]
    trades = [pc.trade_from_backtest(t) for t in res.trades if lo <= t.entry_ts < hi]
    in_win = lambda ts: any(a <= ts <= b for a, b in wins)  # noqa: E731
    sigs = [s for s in pc.backtest_signals(ALL[strategy](), frame.a) if in_win(s.bar_close_ts)
            and datetime.fromtimestamp(s.bar_close_ts - 1, NY).date() in set(days)]
    return sigs, trades, dict(res.rejections), dict(res.cancelled)


def replay(a) -> dict:
    from app import config, db
    from app.core.engine import HISTORY_DAYS
    from app.core.features import load_m1
    from app.core.market_data import Bar

    days = [a.start + timedelta(days=k) for k in range((a.end - a.start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    t0, t1 = ny_midnight(days[0]), ny_midnight(days[-1]) + 86400
    src = load_m1(a.source, a.symbol, t0 - HISTORY_DAYS * 86400, t1)          # read from the real DB first
    have_days = {datetime.fromtimestamp(int(t), NY).date() for t in src["ts"]}
    days = [d for d in days if d in have_days]
    if not days:
        raise SystemExit("No stored minutes for those days.")
    hist_first = datetime.fromtimestamp(int(src["ts"].iloc[0]), NY).date()
    if (days[0] - hist_first).days < HISTORY_DAYS:
        print(f"WARNING: only {(days[0] - hist_first).days} days of history before {days[0]} (engine uses {HISTORY_DAYS}).")

    replay_db = ROOT / "data" / f"replay_compare_{a.strategy}.db"
    replay_db.unlink(missing_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{replay_db}"
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()

    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.backtest import paper_compare as pc
    from app.core import state
    from app.core.engine import TradingEngine
    from app.models import PositionRow, SignalRow
    from app.repository import init_db, save_bars

    init_db()
    with Session(db.get_engine()) as s, s.begin():
        state.put(s, "active_strategy", a.strategy)
        state.put(s, "auto_trading", True)
    rows = list(src.itertuples())
    bar = lambda r: Bar(a.source, a.symbol, "M1", int(r.ts), r.o, r.h, r.l, r.c, r.v)  # noqa: E731
    k = 0
    engine = TradingEngine(a.source, a.symbol, a.balance)
    cycles = Counter()
    for n, d in enumerate(days):
        w0, w1 = window(a.strategy, d)
        chunk = []
        while k < len(rows) and rows[k].ts < w0:
            chunk.append(bar(rows[k]))
            k += 1
        save_bars(chunk)
        if n == 0:
            engine.startup(w0)
        while k < len(rows) and rows[k].ts < w1:
            save_bars([bar(rows[k])])
            cycles[engine.cycle(int(rows[k].ts) + 65).status] += 1
            k += 1
        print(f"  {d}  cycles so far {dict(cycles)}", flush=True)

    with Session(db.get_engine()) as s:
        psig = [pc.signal_from_row(x) for x in s.scalars(select(SignalRow).where(SignalRow.action != "WAIT"))]
        ppos = [pc.trade_from_position(x) for x in s.scalars(select(PositionRow))]
    bsig, btr, brej, bcan = backtest_side(a.strategy, src, days, a.balance)
    return {"mode": "replay", "strategy": a.strategy, "first_day": str(days[0]), "last_day": str(days[-1]),
            "days": len(days), "minutes": len(rows), "cycles": dict(cycles), "paper_signals": psig, "paper_trades": ppos,
            "bt_signals": bsig, "bt_trades": btr, "bt_rejections": brej, "bt_cancelled": bcan}


def journal(a) -> dict:
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from app.backtest import paper_compare as pc
    from app.core.engine import HISTORY_DAYS
    from app.core.features import load_m1
    from app.db import get_engine
    from app.models import PositionRow, SignalRow
    from app.repository import init_db

    init_db()
    with Session(get_engine()) as s:
        lo, hi = s.execute(select(func.min(SignalRow.bar_close_ts), func.max(SignalRow.bar_close_ts))
                           .where(SignalRow.strategy == a.strategy)).one()
        if lo is None:
            raise SystemExit(f"The paper journal has no signals for {a.strategy}.")
        psig = [pc.signal_from_row(x) for x in s.scalars(select(SignalRow).where(SignalRow.strategy == a.strategy,
                                                                                  SignalRow.action != "WAIT"))]
        ppos = [pc.trade_from_position(x) for x in s.scalars(select(PositionRow).where(PositionRow.strategy == a.strategy))]
        evaluated = {int(x) for x in s.scalars(select(SignalRow.bar_close_ts).where(SignalRow.strategy == a.strategy))}
    first, last = datetime.fromtimestamp(lo - 1, NY).date(), datetime.fromtimestamp(hi - 1, NY).date()
    src = load_m1(a.source, a.symbol, ny_midnight(first) - HISTORY_DAYS * 86400, ny_midnight(last) + 86400)
    days = sorted({datetime.fromtimestamp(t - 1, NY).date() for t in evaluated})
    bsig, btr, brej, bcan = backtest_side(a.strategy, src, days, a.balance)
    # only what the live engine could have seen: signals on bars it evaluated, trades coming from those signals
    btr = [t for t in btr if (s := pc.signal_for_trade(t, bsig)) is not None and s.bar_close_ts in evaluated]
    bsig = [x for x in bsig if x.bar_close_ts in evaluated]
    return {"mode": "journal", "strategy": a.strategy, "first_day": str(first), "last_day": str(last), "days": len(days),
            "minutes": len(src), "cycles": {"5m bars evaluated live": len(evaluated)}, "paper_signals": psig,
            "paper_trades": ppos, "bt_signals": bsig, "bt_trades": btr, "bt_rejections": brej, "bt_cancelled": bcan}


def save(r: dict) -> Path:
    from app.backtest import paper_compare as pc
    sc = pc.compare_signals(r["paper_signals"], r["bt_signals"])
    tc = pc.compare_trades(r["paper_trades"], r["bt_trades"])
    out = {k: v for k, v in r.items() if not k.startswith(("paper_", "bt_s", "bt_t"))}
    out.update(paper_signal_count=len(r["paper_signals"]), bt_signal_count=len(r["bt_signals"]),
               paper_trade_count=len(r["paper_trades"]), bt_trade_count=len(r["bt_trades"]),
               paper_rejections=dict(Counter(s.note for s in r["paper_signals"])),
               signals=sc.as_dict(), trades=tc.as_dict(), made=str(date.today()))
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{r['mode']}_{r['strategy']}.json"
    p.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"signals: identical {sc.identical}, different {len(sc.different)}, paper-only {len(sc.paper_only)}, "
          f"backtest-only {len(sc.backtest_only)}")
    print(f"trades:  identical {tc.identical}, different {len(tc.different)}, paper-only {len(tc.paper_only)}, "
          f"backtest-only {len(tc.backtest_only)}  -> {p}")
    return p


def hm(ts) -> str:
    return datetime.fromtimestamp(int(ts), NY).strftime("%Y-%m-%d %H:%M")


def report() -> int:
    files = sorted(OUT.glob("*.json"))
    md = ["# Paper engine versus backtester — results", "",
          f"Made by `scripts/paper_vs_backtest.py --report` on {date.today()}. Rules: `docs/paper_vs_backtest_plan.md`. "
          "This checks the execution code (same data → same signal, fill, exit and cost?), not profitability.", "",
          "**How to read it:** *identical* = both systems agree exactly. *different* = matched, but a price, time, "
          "reason or R differs. *paper only / backtest only* = only one system had it; the paper side shows why it "
          "rejected or skipped. Expected design differences: minimum lot (paper only), 30-day indicator history, "
          "stale-data checks.", ""]
    if not files:
        md.append("No comparison has been run yet.")
    for f in files:
        r = json.loads(f.read_text(encoding="utf-8"))
        s, t = r["signals"], r["trades"]
        md += [f"## {r['strategy']} — {r['mode']} ({r['first_day']} .. {r['last_day']}, {r['days']} days, made {r['made']})", "",
               f"Cycles: {r['cycles']}", "",
               "| | identical | different | paper only | backtest only |", "|---|---:|---:|---:|---:|",
               f"| signals | {s['identical']} | {len(s['different'])} | {len(s['paper_only'])} | {len(s['backtest_only'])} |",
               f"| trades | {t['identical']} | {len(t['different'])} | {len(t['paper_only'])} | {len(t['backtest_only'])} |", "",
               f"Paper signal outcomes: {r['paper_rejections'] or 'none'}. Backtest rejections: {r['bt_rejections'] or 'none'}; "
               f"cancelled orders: {r['bt_cancelled'] or 'none'}.", ""]
        details = ([f"- signal {hm(k[0])} side {k[1]:+d}: " + ", ".join(f"{fl} paper {p} vs backtest {b}" for fl, (p, b) in d.items())
                    for k, d in s["different"]]
                   + [f"- signal {hm(x['bar_close_ts'])} side {x['side']:+d} PAPER ONLY ({x['note']})" for x in s["paper_only"]]
                   + [f"- signal {hm(x['bar_close_ts'])} side {x['side']:+d} BACKTEST ONLY" for x in s["backtest_only"]]
                   + [f"- trade {hm(k[0])} side {k[1]:+d}: " + ", ".join(f"{fl} paper {p} vs backtest {b}" for fl, (p, b) in d.items())
                      for k, d in t["different"]]
                   + [f"- trade {hm(x['entry_ts'])} side {x['side']:+d} PAPER ONLY (exit {x['reason']}, R {x['r']})" for x in t["paper_only"]]
                   + [f"- trade {hm(x['entry_ts'])} side {x['side']:+d} BACKTEST ONLY (exit {x['reason']}, R {x['r']:+.3f})"
                      for x in t["backtest_only"]])
        if details:
            md += ["Differences (first 25):", "", *details[:25], ""]
        else:
            md += ["No differences.", ""]
    (ROOT.parent / "docs" / "paper_vs_backtest_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("-> docs/paper_vs_backtest_report.md")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--strategy")
    p.add_argument("--mode", choices=["replay", "journal"], default="replay")
    p.add_argument("--start", type=date.fromisoformat)
    p.add_argument("--end", type=date.fromisoformat)
    p.add_argument("--balance", type=float, default=1000.0)
    p.add_argument("--source", default="mt5:MetaQuotes-Demo")
    p.add_argument("--symbol", default="USTEC")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    if a.report:
        return report()
    from app.core.strategies import ALL
    if a.strategy not in ALL:
        raise SystemExit(f"--strategy must be one of {sorted(ALL)}")
    if a.mode == "replay" and not (a.start and a.end):
        raise SystemExit("replay needs --start and --end (New York dates)")
    save(replay(a) if a.mode == "replay" else journal(a))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
