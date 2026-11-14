"""Research: market intraday momentum on NAS100 (rules: docs/intraday_momentum_preregistration.md).

  .\\.venv\\Scripts\\python scripts\\intraday_momentum_test.py
Writes docs/intraday_momentum_report.md. 2025+ stays locked.
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from app.backtest.intraday_momentum import (M_1554, M_1559, build_days, random_direction_control,  # noqa: E402
                                            signal_side, trade_r)
from app.backtest.robustness import bootstrap  # noqa: E402
from app.core.features import load_m1  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1))]


def ts(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def evaluate(days, cost=2.0):
    days = [x for x in days if signal_side(x) != 0]
    r = np.array([trade_r(x, signal_side(x), cost) for x in days])
    longs = np.array([trade_r(x, 1, cost) for x in days])
    ctrl = random_direction_control(days, runs=500, cost_pts=cost)
    return days, r, longs.mean(), ctrl


def main() -> int:
    init_db()
    m1 = load_m1(hd.SOURCE, hd.INSTRUMENT, ts(date(2019, 1, 1)), ts(date(2025, 1, 1)))
    main_days = build_days(m1, exit_minute=M_1554)
    info_days = build_days(m1, exit_minute=M_1559)
    print(f"{len(main_days)} tradable days (HistData {hd.INSTRUMENT})")
    md = [f"# Intraday momentum research (NAS100) — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          "- Rules fixed before testing: docs/intraday_momentum_preregistration.md (commit 406b7fb)",
          f"- Data: HistData {hd.INSTRUMENT} 1-minute bars 2019-2024 (2025+ locked); {len(main_days)} tradable days",
          "- Trade 15:30 → 15:55 NY in the direction of the first half-hour return (prev 16:00 → 10:00); "
          "stop 2×ATR14(5m); cost 2.0 points [assumption]", "",
          "| split | trades | long/short | win% | avg R | avg R costs x2 | avg R no cost | always-long avg R | "
          "random-direction avg R | beats random in | P(no edge) | PASS? |",
          "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    ok_all = []
    for split, s0, s1 in SPLITS:
        sd = [x for x in main_days if s0 <= x.day < s1]
        days, r, long_avg, ctrl = evaluate(sd)
        r2 = np.mean([trade_r(x, signal_side(x), 4.0) for x in days])
        r0 = np.mean([trade_r(x, signal_side(x), 0.0) for x in days])
        beat = float(np.mean(r.mean() > ctrl))
        p = bootstrap(list(r)).p_no_edge
        ok = r.mean() > 0 and len(r) >= 100 and beat >= 0.90 and r.mean() > long_avg
        ok_all.append(ok)
        nl = sum(signal_side(x) == 1 for x in days)
        row = (f"| {split} | {len(r)} | {nl}/{len(r) - nl} | {np.mean(r > 0):.0%} | {r.mean():+.3f} | {r2:+.3f} | "
               f"{r0:+.3f} | {long_avg:+.3f} | {ctrl.mean():+.3f} | {beat:.0%} | {p:.0%} | {'pass' if ok else 'FAIL'} |")
        md.append(row)
        print(row)
    md += ["", "Information only (does not count): the paper's full 15:30 → 16:00 window", "",
           "| split | trades | avg R | always-long avg R | beats random in |", "|---|---:|---:|---:|---:|"]
    for split, s0, s1 in SPLITS:
        days, r, long_avg, ctrl = evaluate([x for x in info_days if s0 <= x.day < s1])
        md.append(f"| {split} | {len(r)} | {r.mean():+.3f} | {long_avg:+.3f} | {np.mean(r.mean() > ctrl):.0%} |")
    verdict = "PASSES both splits" if all(ok_all) else "FAILS"
    md += ["", f"## Verdict: **{verdict}**", "",
           "Pass needs, in BOTH splits: avg R > 0 after costs, ≥100 trades, beat the random-direction control in ≥90% "
           "of 500 runs, and beat always-long. Past results do not guarantee future results. Research only."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "intraday_momentum_report.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-9:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
