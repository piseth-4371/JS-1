"""Run all strategies on Dukascopy history and print a comparison.

Splits (decided BEFORE looking at results):
  development  2019-01-01 .. 2022-12-31
  validation   2023-01-01 .. 2024-12-31
  out-of-sample 2025-01-01 .. today   <- only with --oos, run ONCE at the very end

  .\\.venv\\Scripts\\python scripts\\run_backtest.py
  .\\.venv\\Scripts\\python scripts\\run_backtest.py --start 2026-10-19 --end 2026-11-13 --no-splits
  .\\.venv\\Scripts\\python scripts\\run_backtest.py --market btc      (Binance BTCUSDT, weekend book)
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
from app.core.markets import BTCUSD, NAS100  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import binance_source as bn  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
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
    p.add_argument("--market", choices=["nas100", "btc"], default="nas100")
    p.add_argument("--data", choices=["dukascopy", "histdata"], default="dukascopy", help="NAS100 history source")
    p.add_argument("--fee-pct", type=float, default=None, help="BTC: round-trip fee %% of price (default 0.10)")
    a = p.parse_args()
    mk = BTCUSD if a.market == "btc" else NAS100
    src, sym, data_label = ((bn.SOURCE, bn.SYMBOL, "Binance BTCUSDT 1-minute bars (trade prices)") if a.market == "btc"
                            else (hd.SOURCE, hd.INSTRUMENT, f"HistData.com {hd.INSTRUMENT} 1-minute BID bars") if a.data == "histdata"
                            else (dk.SOURCE, dk.INSTRUMENT, f"Dukascopy {dk.INSTRUMENT} 1-minute BID bars"))
    end = date.today() if a.oos else min(a.end, date(2025, 1, 1)) if not a.no_splits else a.end

    init_db()
    t0 = time.time()
    m1 = load_m1(src, sym, ts(a.start), ts(end))
    if m1.empty:
        print(f"No {src} data in that range. Run scripts\\backfill.py {src} first.")
        return 1
    print(f"Loaded {len(m1):,} one-minute bars {datetime.fromtimestamp(m1.ts.iloc[0], timezone.utc):%Y-%m-%d} -> "
          f"{datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc):%Y-%m-%d}  (source: {data_label})")
    frame = build_frame(m1, hold_mask=mk.hold_mask)
    print(f"Built {len(frame.df5):,} five-minute bars in {time.time() - t0:.0f}s")

    settings = RiskSettings()
    if mk is BTCUSD:
        costs = mk.costs if a.fee_pct is None else Costs(0.0, 0.0, a.fee_pct, mk.costs.slip_pct)
    else:
        costs = Costs(a.spread, a.slippage)
    print(f"Costs: spread {costs.spread} pts + slippage {costs.slippage} pts + fee {costs.fee_pct}% + slip {costs.slip_pct}% | risk {settings.risk_pct}%/trade, "
          f"min RR {settings.min_rr}, max {settings.max_trades_per_day} trades/day\n")

    splits = [("all", a.start, end)] if a.no_splits else [s for s in SPLITS if a.oos or s[0] != "out-of-sample"]
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    rows = []
    all_trades = []

    for name, cls in ALL.items():
        if not mk.owns(name):
            continue
        res = run(cls(), frame, settings, costs)
        all_trades += res.trades
        for split, s0, s1 in splits:
            tr = [t for t in res.trades if s0 <= t.ny_date < s1]
            months = max((min(s1, end) - max(s0, a.start)).days / 30.44, 0.1)
            st = compute(tr, months, settings.risk_pct)
            need = statistics.median(min_account_for(t, inst=mk.instrument) for t in tr) if tr else 0
            rows.append((name, split, st, need))
        top_rej = ", ".join(f"{k} x{v}" for k, v in res.rejections.most_common(3)) or "-"
        print(f"[{name}] signals {res.signals}, filled {len(res.trades)}, cancelled {dict(res.cancelled)}, "
              f"top risk rejections: {top_rej}")

    hdr = f"\n{'strategy':<28}{'split':<14}{'trades':>7}{'win%':>7}{'avgR':>7}{'PF':>6}{'totalR':>8}{'return%':>9}{'maxDD%':>8}{'/month':>7}  {'$ needed*':>9}  note"
    print(hdr)
    print("-" * len(hdr))
    for name, split, st, need in rows:
        pf = f"{st.profit_factor:.2f}" if st.profit_factor != float("inf") else "inf"
        print(f"{name:<28}{split:<14}{st.n:>7}{st.win_rate:>7.1f}{st.expectancy_r:>7.2f}{pf:>6}{st.total_r:>8.1f}"
              f"{st.return_pct:>9.1f}{st.max_dd_pct:>8.1f}{st.trades_per_month:>7.1f}  {need:>9.0f}  {st.note}")
    print(f"\n* $ needed = median account size at which {mk.instrument.symbol}'s minimum lot {mk.instrument.min_lot:g} fits the stop at 0.5% risk.")
    print("  Paper balance is $1,000 (owner approved 2026-11-13). Trades needing more than that are rejected.")

    with open(out_dir / f"backtest_trades{'_btc' if mk is BTCUSD else ''}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(asdict(all_trades[0]).keys()) if all_trades else ["none"])
        w.writeheader()
        for t in all_trades:
            w.writerow(asdict(t))
    print(f"\nAll trades saved to {out_dir / ('backtest_trades_btc.csv' if mk is BTCUSD else 'backtest_trades.csv')}  ({time.time() - t0:.0f}s total)")

    # Markdown report for the docs folder (kept in Git as a record of what was tested).
    first = datetime.fromtimestamp(m1.ts.iloc[0], timezone.utc).date()
    last = datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc).date()
    md = [f"# Backtest report — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          f"- Market: {mk.label}. Data: {data_label}, {first} → {last} ({len(m1):,} bars)",
          f"- Costs: spread {costs.spread} pts + fee {costs.fee_pct}% of price per round trip; slippage {costs.slippage} pts + "
          f"{costs.slip_pct}% of price on market/stop fills and stop exits",
          f"- Risk: {settings.risk_pct}% per trade, min RR {settings.min_rr}, max {settings.max_trades_per_day} trades/day, "
          f"1 position, daily −{settings.daily_loss_pct}%, weekly −{settings.weekly_loss_pct}%, stop after "
          f"{settings.max_consecutive_losses} losses",
          "- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat at the end of the book's window (NAS100 15:55 NY, BTC Sunday 17:00 NY)",
          f"- Out-of-sample (2025+) included: {'YES' if a.oos else 'no (locked)'}", "",
          "| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for name, split, st, need in rows:
        pf = f"{st.profit_factor:.2f}" if st.profit_factor != float("inf") else "inf"
        md.append(f"| {name} | {split} | {st.n} | {st.win_rate:.1f} | {st.expectancy_r:.2f} | {pf} | {st.total_r:.1f} | "
                  f"{st.return_pct:.1f} | {st.max_dd_pct:.1f} | {st.trades_per_month:.1f} | {need:.0f} | {st.note} |")
    md += ["", f"\\* median account size at which {mk.instrument.symbol}'s minimum lot fits the stop at 0.5% risk. "
           "The paper balance is $1,000; at $10 every trade would be rejected.", "",
           "**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs "
           "on BOTH development and validation is the minimum bar. Past results do not guarantee future results."]
    report = Path(__file__).resolve().parent.parent.parent / "docs" / (("backtest_report_oos" if a.oos else "backtest_report") + ("_btc" if mk is BTCUSD else "") + ".md")
    report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Report written to {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
