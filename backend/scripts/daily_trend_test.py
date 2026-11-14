"""Research: daily trend strategies on NAS100 (rules fixed in docs/daily_trend_preregistration.md).

  .\\.venv\\Scripts\\python scripts\\daily_trend_test.py
Writes docs/daily_trend_report.md. 2025+ stays locked.
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from app.backtest.daily_trend import daily_bars, random_control, run_daily  # noqa: E402
from app.core.features import load_m1  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1))]
NAMES = ["sma100_long", "donchian_55_20"]


def ts(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def main() -> int:
    init_db()
    m1 = load_m1(hd.SOURCE, hd.INSTRUMENT, ts(date(2019, 1, 1)), ts(date(2025, 1, 1)))
    d = daily_bars(m1)
    print(f"{len(d)} daily bars {d.index[0]} -> {d.index[-1]} (HistData {hd.INSTRUMENT})")
    md = [f"# Daily trend research (NAS100) — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          f"- Rules fixed before testing: docs/daily_trend_preregistration.md (commit 923b5a6)",
          f"- Data: HistData {hd.INSTRUMENT} 1-minute → {len(d)} daily bars {d.index[0]} to {d.index[-1]}; 2025+ locked",
          "- Costs: 2.0 points per trade + overnight financing 5%/year of position value [assumptions]",
          "- Control: same side, same holding length, same stop, random entry day (500 runs)", "",
          "| strategy | split | trades | long/short | win% | avg R (fin 5%) | avg R fin 0% | avg R fin 10% | avg R costs x2 | control avg R | beats control in | avg days held | PASS? |",
          "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    verdicts = {}
    for name in NAMES:
        trades = run_daily(d, name)
        for split, s0, s1 in SPLITS:
            tr = [t for t in trades if s0 <= t.entry_day < s1]
            if not tr:
                md.append(f"| {name} | {split} | 0 | | | | | | | | | | FAIL |")
                verdicts.setdefault(name, []).append(False)
                continue
            r5 = np.array([t.r(2.0, 0.05) for t in tr])
            r0 = np.mean([t.r(2.0, 0.0) for t in tr])
            r10 = np.mean([t.r(2.0, 0.10) for t in tr])
            rc2 = np.mean([t.r(4.0, 0.10) for t in tr])
            ctrl = random_control(d, tr, runs=500)
            beat = float(np.mean(r5.mean() > ctrl))
            ok = r5.mean() > 0 and beat >= 0.90 and len(tr) >= 20
            verdicts.setdefault(name, []).append(ok)
            longs = sum(t.side == 1 for t in tr)
            row = (f"| {name} | {split} | {len(tr)} | {longs}/{len(tr) - longs} | {np.mean(r5 > 0):.0%} | {r5.mean():+.2f} | "
                   f"{r0:+.2f} | {r10:+.2f} | {rc2:+.2f} | {ctrl.mean():+.2f} | {beat:.0%} | "
                   f"{np.mean([t.days_held for t in tr]):.0f} | {'pass' if ok else 'FAIL'} |")
            md.append(row)
            print(row)
    md += ["", "## Verdict", ""]
    for name, v in verdicts.items():
        md.append(f"- **{name}: {'PASSES both splits' if all(v) else 'FAILS'}** (needs avg R > 0, beat the random-timing "
                  "control in ≥90% of runs, and ≥20 trades, in BOTH splits)")
    md += ["", "'costs x2' = 4 points per trade and 10% financing. Few trades per split means wide uncertainty. "
           "Past results do not guarantee future results. Research only: not connected to the live engine."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "daily_trend_report.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-6:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
