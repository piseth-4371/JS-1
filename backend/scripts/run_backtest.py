"""Run all strategies on Dukascopy history and print a comparison.

Splits (decided BEFORE looking at results):
  development  2019-01-01 .. 2022-12-31
  validation   2023-01-01 .. 2024-12-31
  out-of-sample 2025-01-01 .. today   <- only with --oos, run ONCE at the very end

  .\\.venv\\Scripts\\python scripts\\run_backtest.py
  .\\.venv\\Scripts\\python scripts\\run_backtest.py --start 2026-10-19 --end 2026-11-13 --no-splits
"""
import argparse
import csv
import statistics
import sys
import time
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.engine import Costs, min_account_for, run  # noqa: E402
from app.backtest.metrics import compute  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1)),
          ("out-of-sample", date(2025, 1, 1), date(2100, 1, 1))]


def ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2025, 1, 1))
    p.add_argument("--oos", action="store_true", help="include 2025+ (the final exam - run once)")
    p.add_argument("--no-splits", action="store_true", help="one block for the whole range")
    p.add_argument("--spread", type=float, default=1.5)
    p.add_argument("--slippage", type=float, default=0.5)
    a = p.parse_args()
    end = date.today() if a.oos else min(a.end, date(2025, 1, 1)) if not a.no_splits else a.end

    init_db()
    t0 = time.time()
    m1 = load_m1(dk.SOURCE, dk.INSTRUMENT, ts(a.start), ts(end))
    if m1.empty:
        print("No Dukascopy data in that range. Run scripts\\backfill.py dukascopy first.")
        return 1
    print(f"Loaded {len(m1):,} one-minute bars {datetime.fromtimestamp(m1.ts.iloc[0], timezone.utc):%Y-%m-%d} -> "
          f"{datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc):%Y-%m-%d}  (source: dukascopy {dk.INSTRUMENT}, BID prices)")
    frame = build_frame(m1)
    print(f"Built {len(frame.df5):,} five-minute bars in {time.time() - t0:.0f}s")

    settings = RiskSettings()
    costs = Costs(a.spread, a.slippage)
    print(f"Costs: spread {costs.spread} pts + slippage {costs.slippage} pts | risk {settings.risk_pct}%/trade, "
          f"min RR {settings.min_rr}, max {settings.max_trades_per_day} trades/day\n")

    splits = [("all", a.start, end)] if a.no_splits else [s for s in SPLITS if a.oos or s[0] != "out-of-sample"]
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    rows = []
    all_trades = []

    for name, cls in ALL.items():
        res = run(cls(), frame, settings, costs)
        all_trades += res.trades
        for split, s0, s1 in splits:
            tr = [t for t in res.trades if s0 <= t.ny_date < s1]
            months = max((min(s1, end) - max(s0, a.start)).days / 30.44, 0.1)
            st = compute(tr, months, settings.risk_pct)
            need = statistics.median(min_account_for(t) for t in tr) if tr else 0
            rows.append((name, split, st, need))
        top_rej = ", ".join(f"{k} x{v}" for k, v in res.rejections.most_common(3)) or "-"
        print(f"[{name}] signals {res.signals}, filled {len(res.trades)}, cancelled {dict(res.cancelled)}, "
              f"top risk rejections: {top_rej}")

    hdr = f"\n{'strategy':<15}{'split':<14}{'trades':>7}{'win%':>7}{'avgR':>7}{'PF':>6}{'totalR':>8}{'return%':>9}{'maxDD%':>8}{'/month':>7}  {'$ needed*':>9}  note"
    print(hdr)
    print("-" * len(hdr))
    for name, split, st, need in rows:
        pf = f"{st.profit_factor:.2f}" if st.profit_factor != float("inf") else "inf"
        print(f"{name:<15}{split:<14}{st.n:>7}{st.win_rate:>7.1f}{st.expectancy_r:>7.2f}{pf:>6}{st.total_r:>8.1f}"
              f"{st.return_pct:>9.1f}{st.max_dd_pct:>8.1f}{st.trades_per_month:>7.1f}  {need:>9.0f}  {st.note}")
    print("\n* $ needed = median account size at which USTEC's 0.1 minimum lot fits the stop at 0.5% risk.")
    print("  Your $10 account: every one of these trades would be REJECTED by the Risk Manager.")

    with open(out_dir / "backtest_trades.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(asdict(all_trades[0]).keys()) if all_trades else ["none"])
        w.writeheader()
        for t in all_trades:
            w.writerow(asdict(t))
    print(f"\nAll trades saved to {out_dir / 'backtest_trades.csv'}  ({time.time() - t0:.0f}s total)")

    # Markdown report for the docs folder (kept in Git as a record of what was tested).
    first = datetime.fromtimestamp(m1.ts.iloc[0], timezone.utc).date()
    last = datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc).date()
    md = [f"# Backtest report — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          f"- Data: Dukascopy {dk.INSTRUMENT} 1-minute BID bars, {first} → {last} ({len(m1):,} bars)",
          f"- Costs: spread {costs.spread} pts + slippage {costs.slippage} pts on market/stop fills and stop exits",
          f"- Risk: {settings.risk_pct}% per trade, min RR {settings.min_rr}, max {settings.max_trades_per_day} trades/day, "
          f"1 position, daily −{settings.daily_loss_pct}%, weekly −{settings.weekly_loss_pct}%, stop after "
          f"{settings.max_consecutive_losses} losses",
          "- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat 15:55 NY",
          f"- Out-of-sample (2025+) included: {'YES' if a.oos else 'no (locked)'}", "",
          "| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for name, split, st, need in rows:
        pf = f"{st.profit_factor:.2f}" if st.profit_factor != float("inf") else "inf"
        md.append(f"| {name} | {split} | {st.n} | {st.win_rate:.1f} | {st.expectancy_r:.2f} | {pf} | {st.total_r:.1f} | "
                  f"{st.return_pct:.1f} | {st.max_dd_pct:.1f} | {st.trades_per_month:.1f} | {need:.0f} | {st.note} |")
    md += ["", "\\* median account size at which USTEC's 0.1 minimum lot fits the stop at 0.5% risk. "
           "At $10 every trade is rejected.", "",
           "**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs "
           "on BOTH development and validation is the minimum bar. Past results do not guarantee future results."]
    report = Path(__file__).resolve().parent.parent.parent / "docs" / ("backtest_report_oos.md" if a.oos else "backtest_report.md")
    report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Report written to {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
