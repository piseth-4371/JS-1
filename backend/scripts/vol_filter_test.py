"""Research: volatility regime filter on the 7 NAS100 strategies (rules: docs/volatility_filter_preregistration.md).

Run ONCE. Development 2019-2022 and validation 2023-2024; 2025+ stays locked. Writes docs/volatility_filter_report.md.

  .\\.venv\\Scripts\\python scripts\\vol_filter_test.py
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.robustness import bootstrap  # noqa: E402
from app.backtest.vol_filter import VolFiltered, daily_closes, percentiles, random_skip_beaten, regime  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1), 100),
          ("validation", date(2023, 1, 1), date(2025, 1, 1), 50)]
NAMES = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet",
         "london_trend_fvg", "london_sweep_mss_fvg"]


def ts(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def avg(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def main() -> int:
    init_db()
    m1 = load_m1(hd.SOURCE, hd.INSTRUMENT, ts(date(2019, 1, 1)), ts(date(2025, 1, 1)))
    if m1.empty:
        print("No HistData NAS100 bars.")
        return 1
    frame = build_frame(m1)
    closes = daily_closes(m1)
    pct = percentiles(closes, sorted(set(frame.a["ny_date"])))
    regimes = {d: regime(p) for d, p in pct.items()}
    counts = {r: sum(1 for x in regimes.values() if x == r) for r in ("normal", "calm", "wild", "no_history")}
    print("day regimes:", counts)
    costs, settings = Costs(), RiskSettings()

    rows, verdicts, info = [], {}, []
    for name in NAMES:
        base = run(ALL[name](), frame, settings, costs).trades
        wrapper = VolFiltered(ALL[name](), pct)
        filt = run(wrapper, frame, settings, costs).trades
        ok_all = True
        for split, s0, s1, min_n in SPLITS:
            rb = [t.r for t in base if s0 <= t.ny_date < s1]
            rf = [t.r for t in filt if s0 <= t.ny_date < s1]
            ab, af = avg(rb), avg(rf)
            p_no_edge = bootstrap(rf).p_no_edge if rf else 1.0
            beat = random_skip_beaten(rb, af, len(rf)) if rf else 0.0
            checks = [af > 0, len(rf) >= min_n, p_no_edge <= 0.10, af > ab, beat >= 0.90]
            ok = all(checks)
            ok_all &= ok
            marks = "".join("✓" if c else "✗" for c in checks)
            row = (f"| {name} | {split} | {len(rb)} | {ab:+.3f} | {len(rf)} | {af:+.3f} | {p_no_edge:.0%} | "
                   f"{beat:.0%} | {marks} | {'PASS' if ok else 'fail'} |")
            rows.append(row)
            print(row)
            # information only: base trades on calm / wild days
            by = {"calm": [], "wild": []}
            for t in base:
                if s0 <= t.ny_date < s1 and regimes.get(t.ny_date) in by:
                    by[regimes[t.ny_date]].append(t.r)
            info.append(f"| {name} | {split} | {len(by['calm'])} | {avg(by['calm']):+.3f} | "
                        f"{len(by['wild'])} | {avg(by['wild']):+.3f} |")
        verdicts[name] = "PASS" if ok_all else "FAIL"

    passed = [n for n, v in verdicts.items() if v == "PASS"]
    md = [f"# Volatility regime filter — results ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC)", "",
          "Rules fixed and committed BEFORE this run: `volatility_filter_preregistration.md` (commit 67434a7).",
          f"Data: HistData {hd.INSTRUMENT} 2019-2024 (2025+ locked). Costs {costs.spread} spread + {costs.slippage} slippage.",
          f"Day regimes 2019-2024: normal {counts['normal']}, calm {counts['calm']}, wild {counts['wild']}, "
          f"not enough history {counts['no_history']} (start of 2019).", "",
          f"## Verdict: {'PASS — ' + ', '.join(passed) if passed else 'FAIL — no strategy passes in both periods'}", "",
          "Checks (all needed, both periods): 1 filtered avg R > 0 · 2 enough trades (100 dev / 50 val) · "
          "3 luck chance ≤ 10% · 4 better than unfiltered · 5 beats ≥ 90% of random-skip controls.", "",
          "| strategy | split | trades base | avg R base | trades filtered | avg R filtered | luck chance | beats random skip | checks 1-5 | result |",
          "|---|---|---:|---:|---:|---:|---:|---:|---|---|", *rows, "",
          "## Information only (not part of the verdict): trades on skipped days, unfiltered", "",
          "| strategy | split | calm trades | calm avg R | wild trades | wild avg R |", "|---|---|---:|---:|---:|---:|",
          *info, "",
          "No rule may be changed after this run (20/80 percentile, 20-day volatility, 250-day ranking). "
          "Past results do not guarantee future results."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "volatility_filter_report.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nVerdict: {verdicts}\nReport written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
