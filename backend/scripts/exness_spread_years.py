"""Exness USTEC spread by year (rules: docs/exness_spread_years_preregistration.md).

Measurement only: runs no strategy and writes nothing to the database. Writes docs/exness_spread_years_report.md.

    .\\.venv\\Scripts\\python scripts\\exness_spread_years.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import exness_spread_check as esc  # noqa: E402
from app.core import data_quality as dq  # noqa: E402
from app.core.features import load_m1  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.repository import init_db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT.parent / "docs" / "exness_spread_years_report.md"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
CONTROL_YEAR = 2023
WINDOWS = (("pre-US 03:00-09:29", 0, 570), ("US 09:30-15:54", 570, 10_000))


def scope(year: int) -> tuple[date, date]:
    return (date(2019, 8, 5) if year == 2019 else date(year, 1, 1)), date(year, 12, 31)


def min_days(year: int) -> int:
    return 80 if year == 2019 else esc.MIN_DAYS


def weekdays_in(first: date, last: date) -> list[date]:
    return [first + timedelta(n) for n in range((last - first).days + 1) if (first + timedelta(n)).weekday() < 5]


def nth_sunday(year: int, month: int, n: int) -> date:
    d = date(year, month, 1)
    return d + timedelta((6 - d.weekday()) % 7 + 7 * (n - 1))


def clock_periods(year: int) -> dict[str, tuple[int, int]]:
    """US DST changes at 02:00 local: second Sunday of March (07:00 UTC), first Sunday of November (06:00 UTC)."""
    s, e = nth_sunday(year, 3, 2), nth_sunday(year, 11, 1)
    t0, t1 = esc.utc(s.year, s.month, s.day, 7), esc.utc(e.year, e.month, e.day, 6)
    return {"before US DST": (esc.utc(year, 1, 1), t0), "US DST": (t0, t1), "after US DST": (t1, esc.utc(year + 1, 1, 1))}


def best_lag(c: dict[int, float]) -> int | None:
    good = {k: v for k, v in c.items() if not np.isnan(v)}
    return max(good, key=good.get) if good else None


def spread_verdicts(usable: bool, days: int, needed: int, median: float) -> str:
    if not usable:
        return "no verdict (file not usable)"
    return "not enough data" if days < needed else esc.assumption_verdict(median)


def check_year(year: int) -> dict:
    path = ROOT / "data" / "external" / f"exness_{year}" / f"Exness_USTEC_{year}.zip"
    first, last = scope(year)
    t0, t1 = esc.utc(year, 1, 1), esc.utc(year + 1, 1, 1)
    raw, ticks, bad = esc.read_exness(path)
    ex = esc.in_window(raw, year)
    ex = ex[(ex["ny_date"] >= first) & (ex["ny_date"] <= last)].reset_index(drop=True)
    ex["spread"] = ex["ask"] - ex["bid"]
    h = esc.in_window(load_m1(hd.SOURCE, hd.INSTRUMENT, t0, t1)[["ts", "c"]], year)
    h = h[(h["ny_date"] >= first) & (h["ny_date"] <= last)]

    valid = dq.valid_dates(dq.session_quality(ex[["ts"]]))
    days = weekdays_in(first, last)
    coverage = sum(d in valid for d in days) / len(days)
    dx = esc.minute_changes(ex["ts"].to_numpy(), ex["bid"].to_numpy())
    dh = esc.minute_changes(h["ts"].to_numpy(), h["c"].to_numpy())
    clocks = []
    for name, (a, b) in clock_periods(year).items():
        part = dx[(dx.index >= a) & (dx.index < b)]
        if part.empty:                     # 2019 scope starts after the March change
            continue
        c = esc.lag_correlations(part, dh[(dh.index >= a) & (dh.index < b)])
        clocks.append((name, c[0], best_lag(c)))
    gap = float((ex[["ts", "bid"]].merge(h[["ts", "c"]], on="ts").eval("bid - c")).abs().median())
    bad_share = bad / ticks if ticks else 1.0
    checks = {"coverage": coverage >= esc.MIN_COVERAGE, "clock": all(b == 0 for _, _, b in clocks),
              "price": gap <= esc.MAX_PRICE_GAP, "bad": bad_share <= esc.MAX_BAD_SHARE}
    usable = all(checks.values())

    bid = load_m1(dk.SOURCE, dk.INSTRUMENT, t0, t1)
    ask = load_m1(dk.SOURCE, dk.ASK_SYMBOL, t0, t1)
    du = bid[["ts", "c"]].merge(ask[["ts", "c"]], on="ts", suffixes=("_bid", "_ask"))
    du = esc.in_window(du.assign(spread=du["c_ask"] - du["c_bid"])[["ts", "spread"]], year)
    shared = ex[["ts", "ny_date", "mod", "spread"]].merge(du[["ts", "spread"]], on="ts", suffixes=("_ex", "_du"))

    windows = []
    for name, lo, hi in WINDOWS:
        w = ex[(ex["mod"] >= lo) & (ex["mod"] < hi)]
        s = shared[(shared["mod"] >= lo) & (shared["mod"] < hi)]
        n_days = w["ny_date"].nunique()
        med = float(w["spread"].median()) if len(w) else float("nan")
        p90 = float(w["spread"].quantile(.9)) if len(w) else float("nan")
        if s["ny_date"].nunique() >= esc.MIN_DAYS:
            me, md = float(s["spread_ex"].median()), float(s["spread_du"].median())
            ratio = me / md if md > 0 else float("nan")
            du_txt = f"{md:.2f} (ratio {ratio:.2f}): " + (esc.ratio_verdict(ratio) if usable else "no verdict")
        else:
            du_txt = "Dukascopy not available"
        windows.append((name, len(w), n_days, med, p90, spread_verdicts(usable, n_days, min_days(year), med), du_txt))
    return {"year": year, "ticks": ticks, "bad": bad, "bad_share": bad_share, "coverage": coverage, "weekdays": len(days),
            "valid": sum(d in valid for d in days), "clocks": clocks, "gap": gap, "checks": checks, "usable": usable,
            "windows": windows}


def label(year: int) -> str:
    return {2019: "2019 (Aug 5 on)", CONTROL_YEAR: "2023 (control)"}.get(year, str(year))


def write_report(res: list[dict]) -> None:
    md = ["# Exness USTEC spread by year — results", "",
          f"Made by `scripts/exness_spread_years.py` on {date.today()}. Rules were committed before these prices were read "
          "(`docs/exness_spread_years_preregistration.md`). Measurement only: no strategy was run and no cost, backtest or "
          "qualification setting changed. 2023 is a control run; the official 2023 result is `docs/exness_spread_check_report.md`.", "",
          "**Spread** is ask minus bid in index points. **Median** is the middle minute. **p90** means 90% of minutes were at "
          "or below that value.", "",
          "## File checks", "",
          "| year | usable | valid weekdays | clock | median price gap to HistData | bad ticks |", "|---|---|---:|---|---:|---:|"]
    for r in res:
        md.append(f"| {label(r['year'])} | {'YES' if r['usable'] else 'NO'} | {r['valid']}/{r['weekdays']} = {r['coverage']:.1%} "
                  f"{esc.pass_fail(r['checks']['coverage'])} | {esc.pass_fail(r['checks']['clock'])} | "
                  f"{r['gap']:.2f} {esc.pass_fail(r['checks']['price'])} | {r['bad']:,} of {r['ticks']:,} "
                  f"{esc.pass_fail(r['checks']['bad'])} |")
    md += ["", "## Spread", "",
           "| year | window | minutes | days | Exness median | Exness p90 | vs 1.5 | Dukascopy median |",
           "|---|---|---:|---:|---:|---:|---|---|"]
    for r in res:
        md += [f"| {label(r['year'])} | {n} | {m:,} | {d} | {med:.2f} | {p:.2f} | {v} | {du} |"
               for n, m, d, med, p, v, du in r["windows"]]
    md += ["", "## Clock check details", "", "| year | period | correlation at lag 0 | best lag (minutes) |", "|---|---|---:|---:|"]
    for r in res:
        md += [f"| {label(r['year'])} | {n} | {c:.3f} | {b:+d} |" for n, c, b in r["clocks"]]
    md += ["", "## Limits", "",
           "- This is the archive's `USTEC` instrument. Account types such as `USTECm` or `USTECc` can differ, and any "
           "commission is not in the spread.",
           "- It shows the spread at the last tick of each minute, not the price of any actual order.",
           "- It says nothing about whether a strategy makes money."]
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    init_db()
    res = []
    for y in YEARS:
        r = check_year(y)
        res.append(r)
        print(y, "usable" if r["usable"] else "NOT usable", f"coverage {r['coverage']:.1%} gap {r['gap']:.2f} bad {r['bad_share']:.4%}",
              r["checks"], [(n[:8], round(med, 2), v) for n, _, _, med, _, v, _ in r["windows"]], flush=True)
    write_report(res)
    print("->", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
