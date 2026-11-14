"""Research: does skipping high-cost trades help? NAS100 strategies, with vs without the cost filter.

Rule fixed in advance: skip a trade when 2.0 points of cost > 20% of its risk (stop distance).
Development 2019-2022 and validation 2023-2024 only; 2025+ stays locked.
A real improvement must hold in BOTH splits. Writes docs/cost_filter_report.md.

  .\\.venv\\Scripts\\python scripts\\cost_filter_test.py [dukascopy]
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.cost_filter import CostFiltered  # noqa: E402
from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.robustness import bootstrap  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1))]
NAMES = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet",
         "london_trend_fvg", "london_sweep_mss_fvg"]


def ts(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def stats(rs):
    if not rs:
        return "0", "-", "-", "-"
    b = bootstrap(rs)
    return str(len(rs)), f"{sum(rs) / len(rs):+.2f}", f"{sum(rs):+.1f}", f"{b.p_no_edge:.0%}"


def main() -> int:
    src = dk if "dukascopy" in sys.argv[1:] else hd       # HistData (full 2019-2024) unless asked
    init_db()
    m1 = load_m1(src.SOURCE, src.INSTRUMENT, ts(date(2019, 1, 1)), ts(date(2025, 1, 1)))
    if m1.empty:
        print(f"No {src.SOURCE} data.")
        return 1
    last = datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc).date()
    frame = build_frame(m1)
    costs, settings = Costs(), RiskSettings()
    md = [f"# Cost filter research (NAS100) — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          f"- Data: {src.SOURCE} {src.INSTRUMENT} 2019-01-01 to {last} (2025+ locked)",
          f"- Costs {costs.spread} spread + {costs.slippage} slippage = {costs.spread + costs.slippage} points per trade [assumption; "
          "MetaQuotes-Demo measured ~0.9-1.0 point spread on 2026-11-13]",
          "- Filter (fixed in advance): skip the trade if cost > 20% of its risk", "",
          "| strategy | split | trades base | avg R base | trades filtered | avg R filtered | total R base | total R filtered | P(no edge) filtered |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name in NAMES:
        base = run(ALL[name](), frame, settings, costs).trades
        filt = run(CostFiltered(ALL[name]()), frame, settings, costs).trades
        for split, s0, s1 in SPLITS:
            if s0 >= last:
                md.append(f"| {name} | {split} | not downloaded yet | | | | | | |")
                continue
            rb = [t.r for t in base if s0 <= t.ny_date < s1]
            rf = [t.r for t in filt if s0 <= t.ny_date < s1]
            nb, ab, tb, _ = stats(rb)
            nf, af, tf, pf = stats(rf)
            row = f"| {name} | {split}{' (partial)' if (s1 - last).days > 7 else ''} | {nb} | {ab} | {nf} | {af} | {tb} | {tf} | {pf} |"
            md.append(row)
            print(row)
    md += ["", "**Reading this:** the filter only counts as an improvement if avg R improves in BOTH development and "
           "validation with enough trades (30+). Fewer trades also means more luck in the result. "
           "Past results do not guarantee future results."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "cost_filter_report.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nReport written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
