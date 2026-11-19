"""Turn-of-the-month test on the Nasdaq Composite (docs/turn_of_month_preregistration.md).

    .venv\\Scripts\\python scripts\\turn_of_month_test.py

Measurement only: no strategy, risk limit or scanner.QUALIFIED is changed.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backtest import turn_of_month as t  # noqa: E402
from app.backtest.multimarket_trend import read_fred  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "external" / "fred" / "NASDAQCOM.csv"
OUT = ROOT.parent / "docs" / "turn_of_month_report.md"


def p(x: float, d: int = 3) -> str:
    return f"{x * 100:+.{d}f}%"


def main() -> int:
    s = read_fred(DATA)
    s = s[s.index.year <= 2024]
    dev = t.evaluate(s, t.DEV, "Development 1971-1999")
    val = t.evaluate(s, t.VAL, "Validation 2000-2024")
    v = t.verdict(dev, val)

    rows = []
    for x in (dev, val):
        rows.append(f"| {x.name} | {x.n} | {p(x.gross_avg)} | **{p(x.net_avg)}** | {p(x.low)} to {p(x.high)} | "
                    f"{p(x.stress_avg)} | {p(x.random_p95)} ({x.random_share_beaten:.1%} beaten) | {x.win_rate:.0%} | "
                    f"{'yes' if x.ok() else 'no'} |")
        print(f"{x.name}: n={x.n} gross={p(x.gross_avg)} net={p(x.net_avg)} range={p(x.low)}..{p(x.high)} "
              f"stress={p(x.stress_avg)} random95={p(x.random_p95)} beaten={x.random_share_beaten:.1%} "
              f"tom_daily={p(x.tom_daily)} all_daily={p(x.all_daily)} ok={x.ok()}")
    print("VERDICT:", v)

    # Information only: net average by decade (no decision uses this).
    prices, dates = s.to_numpy(float), s.index
    w = t.windows(dates)
    e = np.array([a for a, _ in w])
    x = np.array([b for _, b in w])
    net = t.net_return(prices, dates, e, x)
    dec = dates[e].year // 10 * 10
    decades = [f"| {d}s | {(dec == d).sum()} | {p(net[dec == d].mean())} |" for d in sorted(set(dec))]

    lines = [
        "# Turn of the month — results", "",
        f"Made by `scripts/turn_of_month_test.py` on {date.today().isoformat()}. Rules were committed before any "
        "result: `docs/turn_of_month_preregistration.md`. Measurement only: no strategy, risk limit or "
        "`scanner.QUALIFIED` changed.", "",
        f"## Verdict: **{v}**", "",
        "Rule: buy the Nasdaq Composite at the close of the second-to-last trading day of each month, sell at the "
        "close of the 3rd trading day of the next month. Costs: 0.02% spread + 7%/year financing per night "
        "(stress: doubled). Returns are per trade.", "",
        "| period | trades | before costs | after costs | 95% range (years resampled) | stress | random timing 95th pct | trades won | all checks |",
        "|---|---:|---:|---:|---|---:|---|---:|---|",
        *rows, "",
        "**Random timing** = the same number of 4-day holds started on random days, same costs, 5,000 runs. "
        "The rule must beat 95% of them.", "",
        "## Average daily price move (information only)", "",
        "| period | on the 4 turn-of-month days | on all days |", "|---|---:|---:|",
        f"| {dev.name} | {p(dev.tom_daily)} | {p(dev.all_daily)} |",
        f"| {val.name} | {p(val.tom_daily)} | {p(val.all_daily)} |", "",
        "## By decade (information only, not part of the verdict)", "",
        "| decade | trades | after costs |", "|---|---:|---:|", *decades, "",
        "## Limits",
        "- Nasdaq Composite, not the Nasdaq-100 CFD; close prices with no slippage; dividends ignored.",
        "- 0.02% spread and 7% financing are assumptions for today's Exness account; real older costs were higher.",
        "- About 12 trades a year, so single years are noisy. This is evaluation 53 in this project.",
        "- A pass would only justify a paper forward test, never real money.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
