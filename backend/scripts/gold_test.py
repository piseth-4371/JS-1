"""Gold (XAUUSD) test of the 7 intraday strategies, rules unchanged (docs/gold_and_scanner_preregistration.md).

  .\\.venv\\Scripts\\python scripts\\gold_test.py
Writes docs/gold_report.md. 2025+ stays locked.
"""
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.robustness import bootstrap  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.markets import nas_hold_mask  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.repository import init_db  # noqa: E402
from app.core.strategies import ALL  # noqa: E402

GOLD_COSTS = Costs(spread=0.30, slippage=0.10)          # [assumption] US$ per ounce per trade
SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1))]
NAMES = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet",
         "london_trend_fvg", "london_sweep_mss_fvg"]


def ts(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def avg(x):
    return sum(x) / len(x) if x else float("nan")


def main() -> int:
    init_db()
    m1 = load_m1(hd.SOURCE, hd.GOLD, ts(date(2019, 1, 1)), ts(date(2025, 1, 1)))
    if m1.empty:
        print("No gold data. Run: scripts\\import_histdata.py --pair xauusd")
        return 1
    frame = build_frame(m1, hold_mask=nas_hold_mask)
    double = replace(GOLD_COSTS, spread=GOLD_COSTS.spread * 2, slippage=GOLD_COSTS.slippage * 2)
    settings = RiskSettings()
    md = [f"# Gold (XAUUSD) strategy test — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          "- Rules fixed before testing: docs/gold_and_scanner_preregistration.md (commit 6315eb8)",
          f"- Data: HistData {hd.GOLD} 1-minute bars, {len(m1):,} bars 2019-2024 (2025+ locked)",
          f"- Costs [assumption]: ${GOLD_COSTS.spread} spread + ${GOLD_COSTS.slippage} slippage per ounce; also doubled",
          "- Pass (BOTH splits): avg R > 0, avg R > 0 with double costs, P(no edge) ≤ 10%, ≥ 50 trades", "",
          "| strategy | split | trades | win% | avg R | avg R costs x2 | avg R 90% range | P(no edge) | result |",
          "|---|---|---:|---:|---:|---:|---|---:|---|"]
    passed = {}
    for name in NAMES:
        base = run(ALL[name](), frame, settings, GOLD_COSTS).trades
        dbl = run(ALL[name](), frame, settings, double).trades
        oks = []
        for split, s0, s1 in SPLITS:
            rs = [t.r for t in base if s0 <= t.ny_date < s1]
            r2 = [t.r for t in dbl if s0 <= t.ny_date < s1]
            if not rs:
                md.append(f"| {name} | {split} | 0 | | | | | | FAIL |")
                oks.append(False)
                continue
            b = bootstrap(rs)
            ok = avg(rs) > 0 and avg(r2) > 0 and b.p_no_edge <= 0.10 and len(rs) >= 50
            oks.append(ok)
            row = (f"| {name} | {split} | {len(rs)} | {sum(r > 0 for r in rs) / len(rs):.0%} | {avg(rs):+.2f} | "
                   f"{avg(r2):+.2f} | {b.ci_low:+.2f} to {b.ci_high:+.2f} | {b.p_no_edge:.0%} | {'pass' if ok else 'FAIL'} |")
            md.append(row)
            print(row)
        passed[name] = all(oks)
    winners = [n for n, ok in passed.items() if ok]
    md += ["", f"## Verdict: {'qualified for the scanner: ' + ', '.join(winners) if winners else '**no gold strategy qualifies**'}",
           "", "Past results do not guarantee future results. Research only."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "gold_report.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(md[-3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
