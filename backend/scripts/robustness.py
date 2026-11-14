"""Stress-test strategies BEFORE trusting a backtest (development + validation only; 2025+ stays locked).

For each strategy and split it reports:
  base         normal costs, 2.0R target
  costs x2     double spread/slippage/fees            -> a real edge should survive
  2.5R / 3.0R  different targets (same entries)        -> if results flip, the edge may be luck
  bootstrap    90% range of the average R + chance the true edge is <= 0
  monte carlo  how deep the drawdown / losing streak could get with an unlucky trade order

  .\\.venv\\Scripts\\python scripts\\robustness.py --market btc
  .\\.venv\\Scripts\\python scripts\\robustness.py --strategies orb,sweep_mss_fvg
"""
import argparse
import sys
import time
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.robustness import bootstrap, monte_carlo  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.markets import BTCUSD, NAS100  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import binance_source as bn  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1))]


def ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def avg(rs):
    return sum(rs) / len(rs) if rs else float("nan")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--market", choices=["nas100", "btc"], default="nas100")
    p.add_argument("--data", choices=["dukascopy", "histdata"], default="histdata",
                   help="NAS100 history source (histdata = full 2019-2024; dukascopy = only 2019-01..2020-08)")
    p.add_argument("--strategies", default="", help="comma list; default = every strategy of the market")
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2025, 1, 1))
    a = p.parse_args()
    end = min(a.end, date(2025, 1, 1))                      # out-of-sample stays locked
    mk = BTCUSD if a.market == "btc" else NAS100
    src, sym = ((bn.SOURCE, bn.SYMBOL) if mk is BTCUSD else (hd.SOURCE, hd.INSTRUMENT) if a.data == "histdata"
                else (dk.SOURCE, dk.INSTRUMENT))
    names = [n for n in (a.strategies.split(",") if a.strategies else ALL) if n and mk.owns(n)]

    init_db()
    t0 = time.time()
    m1 = load_m1(src, sym, ts(a.start), ts(end))
    if m1.empty:
        print(f"No {src} data in that range.")
        return 1
    last = datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc).date()
    frame = build_frame(m1, hold_mask=mk.hold_mask)
    settings = RiskSettings()
    base_costs = mk.costs if mk is BTCUSD else Costs()
    double = replace(base_costs, spread=base_costs.spread * 2, slippage=base_costs.slippage * 2,
                     fee_pct=base_costs.fee_pct * 2, slip_pct=base_costs.slip_pct * 2)
    print(f"{mk.label}: data {src} {sym} -> {last}; base costs {base_costs}")

    md = [f"# Robustness report ({mk.label}) — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          f"- Data: {src} {sym} up to {last}; out-of-sample (2025+) locked",
          f"- Base costs: {base_costs}; 'costs x2' doubles every cost; targets 2.5R/3.0R use the same entries",
          "- Bootstrap: 5,000 resamples; Monte Carlo: 2,000 shuffles at 0.5% risk per trade", "",
          "| strategy | split | trades | base avg R | costs x2 | 2.5R | 3.0R | avg R 90% range | P(no edge) | max DD p95 % | losing streak p95 | verdict |",
          "|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for name in names:
        runs = {"base": run(ALL[name](), frame, settings, base_costs).trades,
                "x2": run(ALL[name](), frame, settings, double).trades}
        for rr in (2.5, 3.0):
            s = ALL[name]()
            s.rr = rr
            runs[rr] = run(s, frame, settings, base_costs).trades
        for split, s0, s1 in SPLITS:
            if s0 >= last:
                continue
            pick = {k: [t.r for t in v if s0 <= t.ny_date < s1] for k, v in runs.items()}
            rs = pick["base"]
            if len(rs) < 30:
                verdict = "too few trades"
            else:
                b = bootstrap(rs)
                ok = (avg(rs) > 0 and avg(pick["x2"]) > 0 and avg(pick[2.5]) > 0 and avg(pick[3.0]) > 0
                      and b.p_no_edge < 0.10)
                verdict = "robust in this split" if ok else "NOT robust"
            b, mc = bootstrap(rs), monte_carlo(rs)
            row = (f"| {name} | {split} | {len(rs)} | {avg(rs):.2f} | {avg(pick['x2']):.2f} | {avg(pick[2.5]):.2f} | "
                   f"{avg(pick[3.0]):.2f} | {b.ci_low:.2f} to {b.ci_high:.2f} | {b.p_no_edge:.0%} | "
                   f"{mc.max_dd_p95:.1f} | {mc.losing_streak_p95} | {verdict} |")
            md.append(row)
            print(row)
    md += ["", "**Reading this:** 'robust in this split' needs avg R > 0 at base, with double costs, at 2.5R and 3.0R, "
           "and less than a 10% bootstrap chance that the true edge is ≤ 0, with ≥ 30 trades. A strategy must be robust in "
           "BOTH development and validation. Max DD p95 = 1 in 20 trade orders would be worse. "
           "Past results do not guarantee future results."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / f"robustness_report{'_btc' if mk is BTCUSD else ''}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nReport written to {out}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
