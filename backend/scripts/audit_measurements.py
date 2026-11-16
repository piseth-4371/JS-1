"""Audit measurements (read-only research; no strategy, parameter or rule is changed).

Development 2019-2022 and validation 2023-2024 ONLY. 2025+ is never loaded.

What it measures, for the 7 NAS100 strategies on HistData NSXUSD M1 bars:
  1. Data quality per New York date with the rule fixed in docs/data_quality_rule.md -> docs/data_quality_report.md
  2. Reproducibility: the engine re-run is compared with the saved data/backtest_trades.csv
  3. All sessions vs VALID sessions only (a fresh engine run with valid_dates)
  4. Gross vs net expectancy, cost as a share of the initial risk, trades, drawdown
  5. Cost stress (scenarios fixed below BEFORE running; the same trades re-priced, entries/exits unchanged)
  6. Uncertainty: trade-level 95% range, week-clustered 95% range, and the lower end widened for the
     36 strategy versions tried so far (Bonferroni)
  7. Bid-only data checks: fills/exits that depended on the bid touching a level within one spread
     (with real bid/ask quotes those may not have happened) and trades held through a data hole

    .\\.venv\\Scripts\\python scripts\\audit_measurements.py
"""
import csv
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.report_card import max_drawdowns, report  # noqa: E402
from app.core import data_quality as dq  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.fills import net_points  # noqa: E402
from app.core.markets import NAS100  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT.parent / "docs"
START, END = date(2019, 1, 1), date(2025, 1, 1)          # END is exclusive; 2025+ never loaded
SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1), 4.0), ("validation", date(2023, 1, 1), date(2025, 1, 1), 2.0)]
BASE = Costs(spread=1.5, slippage=0.5)
# Fixed before running. Spread x2 = wide/fast market; slippage x3 = stop/market fills in fast moves;
# both = a plausible bad case. Measured (MetaQuotes-Demo, not Exness): median spread 0.9, p90 1.0 pts.
SCENARIOS = [("gross (no cost)", Costs(0, 0)), ("measured-like (1.0 / 0.5)", Costs(1.0, 0.5)), ("base (1.5 / 0.5)", BASE),
             ("spread x2 (3.0 / 0.5)", Costs(3.0, 0.5)), ("slippage x3 (1.5 / 1.5)", Costs(1.5, 1.5)),
             ("both (3.0 / 1.5)", Costs(3.0, 1.5))]
TESTS_SO_FAR = 36            # strategy versions tried (docs/decisions.md 2026-11-16)
RISK_PCT = 0.5


def ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def week_of(d) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-{w:02d}"


def dd_pct(rs: np.ndarray) -> float:
    if rs.size == 0:
        return 0.0
    eq = np.concatenate(([1.0], np.cumprod(1 + RISK_PCT / 100 * rs)))
    return float(max_drawdowns(eq[None, :])[0] * 100)


def data_report(q: list) -> list[str]:
    df = pd.DataFrame([x.__dict__ for x in q])
    df["year"] = [d.year for d in df["ny_date"]]
    out = ["# Data quality report (HistData NSXUSD M1, 2019-2024)", "",
           f"Made by `scripts/audit_measurements.py` on {date.today()}. Rule: `docs/data_quality_rule.md` "
           f"(03:00-15:55 New York, at least {dq.MIN_BARS}/{dq.WINDOW_BARS} bars, no hole longer than {dq.MAX_GAP_MIN} min). "
           "Missing prices are never filled in.", "",
           "| year | weekdays with data | valid | invalid | invalid: low coverage | invalid: hole > 5 min only | median bars | zero-volume bars |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for y, g in df.groupby("year"):
        inv = g[~g["valid"]]
        low = inv["reason"].str.contains("bars").sum()
        out.append(f"| {y} | {len(g)} | {int(g['valid'].sum())} | {len(inv)} | {low} | {len(inv) - low} | "
                   f"{int(g['bars'].median())} | {g['zero_volume_share'].mean():.0%} |")
    out += ["", "**Volume:** HistData bars carry no volume (0 on every bar). `session_vwap` then falls back to the plain "
            "average of 5-minute typical prices (a time-weighted average), while the live MT5 feed has tick volume, so the "
            "backtest 'VWAP' and the live VWAP are different lines. VWAP-based rules (trend_fvg filter, vwap_reversion, "
            "london variants) were backtested on the time-weighted version.", "",
            "## Invalid dates", "", "| date | bars | longest hole (min) | reason |", "|---|---:|---:|---|"]
    for x in q:
        if not x.valid:
            out.append(f"| {x.ny_date} | {x.bars} | {x.longest_gap_min} | {x.reason} |")
    return out


def priced(trades: list, costs: Costs, planned: bool = False) -> np.ndarray:
    return np.array([net_points(t.side, t.entry, t.exit, t.kind, t.exit_reason, costs)
                     / (t.planned_risk_pts if planned and t.planned_risk_pts > 0 else t.risk_pts) for t in trades])


def main() -> int:
    init_db()
    t0 = time.time()
    m1 = load_m1(hd.SOURCE, hd.INSTRUMENT, ts(START), ts(END))
    assert m1["ts"].max() < ts(END), "2025+ data must not be loaded"
    print(f"Loaded {len(m1):,} bars in {time.time() - t0:.0f}s")
    q = dq.session_quality(m1)
    valid = dq.valid_dates(q)
    (DOCS / "data_quality_report.md").write_text("\n".join(data_report(q)) + "\n", encoding="utf-8")
    print(f"{len(q)} weekdays with data, {len(valid)} valid -> docs/data_quality_report.md")

    frame = build_frame(m1, hold_mask=NAS100.hold_mask)
    bar_ts = frame.m1["ts"]
    lows, highs = frame.m1["l"], frame.m1["h"]
    idx = {int(t): i for i, t in enumerate(bar_ts)}
    settings = RiskSettings()
    saved = pd.read_csv(ROOT / "data" / "backtest_trades.csv") if (ROOT / "data" / "backtest_trades.csv").exists() else None

    rows, repro, checks, out_csv = [], [], [], []
    for name in ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet", "london_trend_fvg", "london_sweep_mss_fvg"]:
        runs = {"all sessions": run(ALL[name](), frame, settings, BASE),
                "valid sessions": run(ALL[name](), frame, settings, BASE, valid_dates=valid)}
        print(f"[{name}] all {len(runs['all sessions'].trades)} trades, valid-only {len(runs['valid sessions'].trades)} "
              f"({time.time() - t0:.0f}s)")
        if saved is not None:
            old = saved[saved["strategy"] == name]
            new = runs["all sessions"].trades
            same = len(old) == len(new) and np.allclose(old["r"].to_numpy(), [t.r for t in new], atol=1e-9)
            repro.append((name, len(old), len(new), old["r"].sum(), sum(t.r for t in new), same))
        tr_all = runs["all sessions"].trades
        holes = np.array([dq.max_gap_between(bar_ts, t.entry_ts, t.exit_ts) for t in tr_all])
        exits_ny = [pd.Timestamp(t.exit_ts, unit="s", tz="UTC").tz_convert("America/New_York") for t in tr_all]
        late = sum(1 for t, x in zip(tr_all, exits_ny) if x.date() > t.ny_date or x.hour * 60 + x.minute > 15 * 60 + 55)
        # Bid-only touch checks (HistData = BID bars; buys happen at the ask = bid + spread)
        long_lim, near_entry, near_exit = [], [], 0
        for t in tr_all:
            j = idx.get(int(t.entry_ts))
            is_ll = t.kind == "limit" and t.side == 1 and j is not None and frame.m1["o"][j] > t.entry
            long_lim.append(is_ll)
            near_entry.append(is_ll and lows[j] > t.entry - BASE.spread)
            if t.exit_reason == "target" and t.side == -1:
                k = idx.get(int(t.exit_ts))
                if k is not None and lows[k] > t.target - BASE.spread and frame.m1["o"][k] > t.target:
                    near_exit += 1
        long_lim, near_entry = np.array(long_lim, dtype=bool), np.array(near_entry, dtype=bool)
        other_ll = long_lim & ~near_entry
        rs_all = np.array([t.r for t in tr_all])
        checks.append((name, len(tr_all), int((holes > dq.MAX_GAP_MIN).sum()),
                       float(rs_all[holes > dq.MAX_GAP_MIN].mean()) if (holes > dq.MAX_GAP_MIN).any() else float("nan"),
                       late, int(near_entry.sum()), float(rs_all[near_entry].mean()) if near_entry.any() else float("nan"),
                       int(other_ll.sum()), float(rs_all[other_ll].mean()) if other_ll.any() else float("nan"), near_exit, int(sum(abs(t.risk_pts - t.planned_risk_pts) > 1e-9 for t in tr_all)),
                       float(np.mean(priced(tr_all, BASE, planned=True))) if tr_all else float("nan"),
                       float(rs_all.mean()) if tr_all else float("nan")))
        for label, res in runs.items():
            for t, h in zip(res.trades, holes if label == "all sessions" else [None] * len(res.trades)):
                out_csv.append({"sessions": label, **t.__dict__, "max_hole_min": h})
            for split, s0, s1, years in SPLITS:
                tr = [t for t in res.trades if s0 <= t.ny_date < s1]
                if len(tr) < 2:
                    rows.append((name, split, label, len(tr), None))
                    continue
                gross, net = priced(tr, Costs(0, 0)), np.array([t.r for t in tr])
                cost_r = gross - net
                card = report(net, years, RISK_PCT, groups=[week_of(t.ny_date) for t in tr], tests=TESTS_SO_FAR)
                stress = {lab: float(priced(tr, c).mean()) for lab, c in SCENARIOS}
                rows.append((name, split, label, len(tr), dict(
                    gross=float(gross.mean()), net=float(net.mean()), cost_mean=float(cost_r.mean()),
                    cost_med=float(np.median(cost_r)), dd=dd_pct(net), card=card, stress=stress,
                    stress_dd=dd_pct(priced(tr, SCENARIOS[-1][1])))))

    with open(ROOT / "data" / "reports" / "audit_trades.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_csv[0].keys()))
        w.writeheader()
        w.writerows(out_csv)

    md = ["# Audit measurements (2019-2024 only; 2025+ untouched)", "",
          f"Made by `scripts/audit_measurements.py` on {date.today()}. HistData NSXUSD 1-minute BID bars. "
          f"Risk {RISK_PCT}% per trade. R = net points / risk at the fill (engine convention). Every number below is "
          "after the audit fixes; earlier reports are kept unchanged for history.", "",
          "## 1. Reproducibility of the saved backtest", "",
          "| strategy | saved trades | re-run trades | saved total R | re-run total R | identical |", "|---|---:|---:|---:|---:|---|"]
    md += [f"| {n} | {a} | {b} | {x:+.2f} | {y:+.2f} | {'yes' if s else 'NO'} |" for n, a, b, x, y, s in repro]
    md += ["", "## 2. Gross vs net, all sessions vs valid sessions (base costs: spread 1.5 + slippage 0.5 pts)", "",
           "Cost/risk = cost of the trade in R (share of the initial risk). DD = max drawdown of the compounded "
           f"{RISK_PCT}% risk curve. 95% iid = avg ± 1.96·SE. Week 95% = bootstrap over ISO weeks. "
           f"Family low = avg − z·SE with Bonferroni z for {TESTS_SO_FAR} versions. Share ≤ 0 = share of bootstrap "
           "resamples whose average is ≤ 0 (a frequency, not a probability of no edge).", "",
           "| strategy | split | sessions | trades | gross avg R | net avg R | cost/risk mean | cost/risk median | max DD | 95% iid | 95% week | family low | share ≤ 0 |",
           "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|"]
    for name, split, label, n, d in rows:
        if d is None:
            md.append(f"| {name} | {split} | {label} | {n} | – | – | – | – | – | – | – | – | – |")
            continue
        c = d["card"]
        md.append(f"| {name} | {split} | {label} | {n} | {d['gross']:+.3f} | {d['net']:+.3f} | {d['cost_mean']:.3f} | "
                  f"{d['cost_med']:.3f} | {d['dd']:.1f}% | {c.ci95_low:+.3f} to {c.ci95_high:+.3f} | "
                  f"{c.ci95_week_low:+.3f} to {c.ci95_week_high:+.3f} | {c.ci_low_family:+.3f} | {c.p_no_edge:.0%} |")
    md += ["", "## 3. Cost stress (valid sessions; same trades re-priced; avg R per trade)", "",
           "Scenarios fixed before running. 'measured-like' uses the MetaQuotes-Demo median spread (~0.9-1.0 pts; not Exness, "
           "slippage not measured). Re-pricing keeps the same entries and exits, so it ignores that higher costs would also "
           "change which later trades the daily-loss rules allow.", "",
           "| strategy | split | trades | " + " | ".join(lab for lab, _ in SCENARIOS) + " | DD at worst case |",
           "|---|---|---:|" + "---:|" * len(SCENARIOS) + "---:|"]
    for name, split, label, n, d in rows:
        if label == "valid sessions" and d is not None:
            md.append(f"| {name} | {split} | {n} | " + " | ".join(f"{d['stress'][lab]:+.3f}" for lab, _ in SCENARIOS)
                      + f" | {d['stress_dd']:.1f}% |")
    md += ["", "## 4. Data and fill-model checks (all sessions, 2019-2024)", "",
           "| strategy | trades | held through hole > 5 min | avg R of those | exit after 15:55 NY or next day | "
           "long limit fills where the bid stayed within 1 spread* | avg R of those | other long limit fills | avg R of those | "
           "short target exits where the bid stayed within 1 spread* | fill risk ≠ planned risk | avg R on planned risk | avg R on fill risk |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, n, nh, rh, late, ne, rne, nl, rl, nx, diff, rp, rf in checks:
        md.append(f"| {name} | {n} | {nh} | {rh:+.2f} | {late} | {ne} | {rne:+.3f} | {nl} | {rl:+.3f} | {nx} | {diff} | {rp:+.3f} | {rf:+.3f} |")
    md += ["", "\\* The bars are BID prices. A buy (long entry, short exit) needs the ASK (about bid + spread) at the level. These "
           "fills/exits happened because the bid reached the level while staying within one spread of it, so with real "
           "quotes some would not have happened. Long limit fills are compared with the other long limit fills (a fair "
           "comparison: both groups are entries). Short target exits are only counted, because they are winners by "
           "construction; each one that would not have happened is an overstated result.", ""]
    (DOCS / "audit_measurements.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"done in {time.time() - t0:.0f}s -> docs/audit_measurements.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
