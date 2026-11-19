"""Run the Exness cost gate (docs/exness_cost_gate_preregistration.md) on a NAS100 backtest trade file.

    .venv\\Scripts\\python scripts\\exness_cost_gate.py                       # bid-only backtest, information only
    .venv\\Scripts\\python scripts\\exness_cost_gate.py --trades data\\reports\\bidask_full_trades.csv \\
        --main-passed silver_bullet --out ..\\docs\\exness_cost_gate_bidask.md

--main-passed names strategies that PASSED their main pre-registered test; every other strategy is reported as
"not eligible". Measurement only: no strategy, risk limit or scanner.QUALIFIED is changed.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backtest import exness_gate as g  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def f(x, signed=True) -> str:
    if x != x:  # NaN
        return "—"
    return f"{x:+.3f}" if signed else f"{x:.3f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", default=str(ROOT / "data" / "backtest_trades.csv"))
    ap.add_argument("--main-passed", nargs="*", default=[])
    ap.add_argument("--out", default=str(ROOT.parent / "docs" / "exness_cost_gate_report.md"))
    a = ap.parse_args()

    t = pd.read_csv(a.trades)
    missing = [c for c in g.REQUIRED if c not in t.columns]
    if missing:
        print(f"Missing columns: {missing}")
        return 2
    t = t[~t["strategy"].str.startswith("btc_")]
    err = g.cost_model_error(t)
    lines = ["# Exness cost gate — results", "",
             f"Made by `scripts/exness_cost_gate.py` on {date.today().isoformat()} from `{Path(a.trades).name}` "
             f"({len(t):,} NAS100 trades). Rules were committed first: `docs/exness_cost_gate_preregistration.md`.",
             "Measurement only: no strategy, risk limit or `scanner.QUALIFIED` changed.", "",
             f"Input check: largest difference from the backtest cost model = {err:.2e} "
             f"({'PASS' if err < 1e-9 else 'FAIL'}).", ""]
    if err >= 1e-9:
        lines.append(f"**{g.NO_VERDICT}.**")
        Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(g.NO_VERDICT)
        return 1

    t = g.reprice(t)
    lines += ["**Backtest** = average R per trade with the 1.5-point spread. **Exness** = with 2.94 points "
              "(highest 2021-23 median). **Stress** = with the highest p90 (3.29 pre-US, 3.65 US). "
              "**Family range** = 95% range of the Exness average, widened for 7 strategies.", "",
              "| strategy | split | trades | backtest | Exness | family range | stress | verdict |",
              "|---|---|---:|---:|---:|---|---:|---|"]
    print(f"{'strategy':24} {'split':5} {'n':>5} {'backtest':>9} {'exness':>8} {'stress':>8}  verdict")
    for name in sorted(t["strategy"].unique()):
        s = t[t["strategy"] == name]
        dev, val = g.split(s, g.DEV_YEARS), g.split(s, g.VAL_YEARS)
        v = g.verdict(dev, val, name in a.main_passed)
        for label, x in (("2019-22", dev), ("2023-24", val)):
            lines.append(f"| {name} | {label} | {x.n} | {f(x.avg_backtest)} | {f(x.avg_exness)} | "
                         f"{f(x.family_low)} to {f(x.family_high)} | {f(x.avg_stress)} | {v if label == '2019-22' else ''} |")
            print(f"{name:24} {label:5} {x.n:5d} {f(x.avg_backtest):>9} {f(x.avg_exness):>8} {f(x.avg_stress):>8}  "
                  f"{v if label == '2019-22' else ''}")
    extra = (t["r"] - t["r_exness"]).mean()
    lines += ["", f"On average the wider Exness spread costs **{extra:.3f}R more per trade** than the backtest assumed "
              f"(median risk {t['risk_pts'].median():.1f} points).", "",
              "## Limits", "- Quoted spread only (last tick per minute); commission and account type not included.",
              "- One flat value per window; news spikes and the open are only covered by the p90 stress.",
              "- 2019, 2020 and 2024 trades use 2021-2023 Exness levels."]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
