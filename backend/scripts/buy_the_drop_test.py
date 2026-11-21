"""Buy-the-drop test on the Nasdaq Composite (docs/buy_the_drop_preregistration.md, commit 6943a95).

    .venv\\Scripts\\python scripts\\buy_the_drop_test.py

Run ONCE. Measurement only: no strategy, risk limit or scanner.QUALIFIED is changed.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backtest import buy_the_drop as t  # noqa: E402
from app.backtest import nearby, yearly  # noqa: E402
from app.backtest.multimarket_trend import read_fred  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "external" / "fred" / "NASDAQCOM.csv"
OUT = ROOT.parent / "docs" / "buy_the_drop_report.md"


def p(x: float, d: int = 3) -> str:
    return f"{x * 100:+.{d}f}%"


def main() -> int:
    s = read_fred(DATA)
    s = s[s.index.year <= 2024]
    periods = [(t.DEV, "Development 1971-1999"), (t.VAL, "Validation 2000-2024")]
    res, year_rows, year_res, near_vals, near_res = [], [], [], [], []
    for years, name in periods:
        r = t.evaluate(s, years, name)
        res.append(r)
        net, yrs = t.period_net(s, years)
        rows = yearly.by_year(list(zip(yrs.tolist(), (net * 100).tolist())))      # in %
        year_rows.append(rows)
        year_res.append(yearly.year_check(rows))
        nb = {}
        for lb in t.NEARBY["lookback"]:
            n_, _ = t.period_net(s, years, lookback=lb)
            nb[f"lookback {lb} (chosen {t.LOOKBACK})"] = float(n_.mean() * 100)
        for h in t.NEARBY["hold"]:
            n_, _ = t.period_net(s, years, hold=h)
            nb[f"hold {h} days (chosen {t.HOLD})"] = float(n_.mean() * 100)
        near_vals.append(nb)
        near_res.append(nearby.nearby_check(r.net_avg * 100, nb))
    dev, val = res
    v = t.verdict(dev, val, tuple(y["passed"] for y in year_res), tuple(n["passed"] for n in near_res))

    rows = []
    for x, y, n in zip(res, year_res, near_res):
        ok = x.core_ok() and y["passed"] and n["passed"]
        rows.append(f"| {x.name} | {x.n} | {p(x.gross_avg)} | **{p(x.net_avg)}** | {p(x.low)} to {p(x.high)} | "
                    f"{p(x.stress_avg)} | {p(x.random_p95)} ({x.random_share_beaten:.1%} beaten) | {x.win_rate:.0%} | "
                    f"{p(x.worst, 1)} | {'yes' if ok else 'no'} |")
        print(f"{x.name}: n={x.n} gross={p(x.gross_avg)} net={p(x.net_avg)} range={p(x.low)}..{p(x.high)} "
              f"stress={p(x.stress_avg)} random95={p(x.random_p95)} beaten={x.random_share_beaten:.1%} "
              f"win={x.win_rate:.0%} worst={p(x.worst, 1)} all5d={p(x.all_avg)} core_ok={x.core_ok()} "
              f"year_ok={y['passed']} {y['reasons']} nearby_ok={n['passed']} {n['reasons']}")
    print("VERDICT:", v)

    detail = []
    for (years, name), rws, y, nb, n, x in zip(periods, year_rows, year_res, near_vals, near_res, res):
        detail += [f"### {name}", "",
                   f"Year-by-year: **{'passes' if y['passed'] else 'fails'}** "
                   f"({y['positive_years']} of {y['counting_years']} counting years positive"
                   + (f"; total without the best year {y['total_without_best']:+.2f}%" if y['total_without_best'] is not None else "")
                   + ")" + ("" if y["passed"] else " — " + "; ".join(y["reasons"])), "",
                   yearly.table(rws, unit="%"), "",
                   f"Nearby settings: **{'passes' if n['passed'] else 'fails'}**"
                   + ("" if n["passed"] else " — " + "; ".join(n["reasons"])), "",
                   nearby.table(f"lookback {t.LOOKBACK}, hold {t.HOLD}", x.net_avg * 100, nb, unit="%"), ""]

    lines = [
        "# Buy the drop — results", "",
        f"Made by `scripts/buy_the_drop_test.py` on {date.today().isoformat()}. Rules were committed before any "
        "result: `docs/buy_the_drop_preregistration.md` (commit 6943a95). Run once. Measurement only: no strategy, "
        "risk limit or `scanner.QUALIFIED` changed.", "",
        f"## Verdict: **{v}**", "",
        "Rule: buy the Nasdaq Composite at a close that is the lowest of the last 10 trading days, sell at the close "
        "5 trading days later, one trade at a time. Costs: 0.02% spread + 7%/year financing per night (stress: "
        "doubled). Returns are per trade.", "",
        "| period | trades | before costs | after costs | 95% range (years resampled) | stress | random timing 95th pct | trades won | worst trade | all checks |",
        "|---|---:|---:|---:|---|---:|---|---:|---:|---|",
        *rows, "",
        "**Random timing** = the same number of 5-day holds started on random days, same costs, 5,000 runs. "
        "The rule must beat 95% of them.", "",
        f"Information only — average 5-day hold after costs over every start day: development {p(dev.all_avg)}, "
        f"validation {p(val.all_avg)}.", "",
        "## Year-by-year and nearby settings", "", *detail,
        "## Pre-mortem check", "",
        "_Filled in by hand after reading the numbers above._", "",
        "## Limits",
        "- Nasdaq Composite, not the Nasdaq-100 CFD; signal and entry on the same close, no slippage; dividends ignored.",
        "- 0.02% spread and 7% financing are assumptions for today's Exness account; real older costs were higher.",
        "- No stop: single trades can lose a lot in a crash. This is evaluation 54 in this project.",
        "- A pass would only justify a paper forward test, never real money.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
